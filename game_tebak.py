import random
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from data import (
    game_sessions, chaos_sessions, duel_sessions, duel_dm_pending,
    taruhan_sessions, taruhan_dm_pending,
    add_score, hitung_poin, get_nama, get_raw_name,
    init_wallet, format_rupiah, SLOT_INITIAL
)
from db import db_get_wallet, db_set_wallet

# =====================
# /angka (SOLO)
# =====================

async def angka(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    key = (chat_id, user_id)

    if key in game_sessions:
        await update.message.reply_text("kamu masih bermain! selesaikan dulu atau /stoptebak")
        return

    target = random.randint(0, 100)
    game_sessions[key] = {"angka": target, "tebakan": 0}

    await update.message.reply_text(
        "🎯 <b>TEBAK ANGKA DIMULAI!</b>\n\n"
        "tebak angka antara 0 - 100\n"
        "langsung ketik angkanya!",
        parse_mode="HTML"
    )

async def stoptebak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    key = (chat_id, user_id)

    if key in game_sessions:
        target = game_sessions[key]["angka"]
        del game_sessions[key]
        await update.message.reply_text(f"game dihentikan. angkanya adalah {target}")
    else:
        await update.message.reply_text("kamu tidak sedang bermain")

async def proses_tebakan_internal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    key = (chat_id, user_id)

    if key not in game_sessions:
        return

    text = update.message.text
    if not text or not text.strip().lstrip("-").isdigit():
        return

    tebakan = int(text.strip())
    session = game_sessions[key]
    target = session["angka"]
    session["tebakan"] += 1

    if tebakan > target:
        await update.message.reply_text("⬇️ terlalu besar")
        return
    if tebakan < target:
        await update.message.reply_text("⬆️ terlalu kecil")
        return

    jumlah = session["tebakan"]
    poin = hitung_poin(jumlah)
    del game_sessions[key]
    await add_score(chat_id, update.message.from_user, poin)

    if jumlah == 1:
        pesan = "🤯🤯🤯 OMAIGOT?! SEKALI TEBAK LANGSUNG BENER!!"
    elif jumlah == 2:
        pesan = "🔥 WOW DUA KALI! LUAR BIASA!"
    elif jumlah == 3:
        pesan = "🔥 KEREN SEKALI, KAMU LEGEND!"
    elif jumlah <= 5:
        pesan = "😎 woww keren banget"
    elif jumlah <= 8:
        pesan = "👍 lumayan keren"
    elif jumlah <= 12:
        pesan = "😅 lama banget nebaknya"
    else:
        pesan = "💀 nyawit ni orang"

    await update.message.reply_text(
        f"{pesan}\n\n"
        f"kamu berhasil menebak dalam <b>{jumlah}x</b> tebakan!\n\n"
        f"🏅 +{poin} poin!",
        parse_mode="HTML"
    )

# =====================
# /angkachaos
# =====================

async def angkachaos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in chaos_sessions:
        await update.message.reply_text("🌀 game chaos sudah berjalan!")
        return

    target = random.randint(0, 100)
    chaos_sessions[chat_id] = {"angka": target, "tebakan_per_user": {}, "participants": {}}

    await update.message.reply_text(
        "🌀 <b>ANGKA CHAOS DIMULAI!</b>\n\n"
        "siapapun boleh nebak!\n"
        "tebak angka 0 - 100\n\n"
        "langsung ketik angkanya aja!",
        parse_mode="HTML"
    )

async def stopchaos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in chaos_sessions:
        target = chaos_sessions[chat_id]["angka"]
        del chaos_sessions[chat_id]
        await update.message.reply_text(f"game chaos dihentikan. angkanya adalah {target}")
    else:
        await update.message.reply_text("tidak ada game chaos yang berjalan")

async def proses_chaos_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id not in chaos_sessions:
        return

    text = update.message.text
    if not text or not text.strip().lstrip("-").isdigit():
        return

    tebakan = int(text.strip())
    session = chaos_sessions[chat_id]
    target = session["angka"]
    user = update.message.from_user
    uid = user.id
    nama = await get_nama(user)

    session["tebakan_per_user"][uid] = session["tebakan_per_user"].get(uid, 0) + 1
    session["participants"][uid] = user

    if tebakan > target:
        await update.message.reply_text(f"⬇️ {nama}: terlalu besar")
        return
    if tebakan < target:
        await update.message.reply_text(f"⬆️ {nama}: terlalu kecil")
        return

    jumlah = session["tebakan_per_user"][uid]
    poin = hitung_poin(jumlah)
    participants = dict(session["participants"])
    del chaos_sessions[chat_id]

    await add_score(chat_id, user, poin)

    for other_uid, other_user in participants.items():
        if other_uid != uid:
            await add_score(chat_id, other_user, 5)

    await update.message.reply_text(
        f"🎉 <b>{nama}</b> berhasil menebak angka <b>{target}</b>!\n\n"
        f"ditebak dalam <b>{jumlah}x</b> tebakan\n\n"
        f"🏅 +{poin} poin!\n"
        f"👾 pemain lain masing-masing +5 poin",
        parse_mode="HTML"
    )

# =====================
# /angkaduel
# =====================

async def angkaduel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in duel_sessions:
        await update.message.reply_text("⚔️ sudah ada game duel, tunggu selesai dulu atau /stopduel")
        return

    duel_sessions[chat_id] = {
        "players": [],
        "player_objs": {},
        "numbers": {},
        "numbers_received": set(),
        "tebakan_per_player": {},
        "turn": 0,
        "started": False
    }

    await update.message.reply_text(
        "⚔️ <b>ANGKA DUEL!</b>\n\n"
        "game untuk 2 pemain saja!\n"
        "ketik /joinduel untuk ikut\n\n"
        "setelah 2 orang join, host ketik /startduel",
        parse_mode="HTML"
    )

async def joinduel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user = update.message.from_user

    if chat_id not in duel_sessions:
        await update.message.reply_text("belum ada game duel. ketik /angkaduel dulu")
        return

    session = duel_sessions[chat_id]

    if session["started"]:
        await update.message.reply_text("game sudah dimulai, tidak bisa join")
        return

    if user.id in session["player_objs"]:
        await update.message.reply_text("kamu sudah join!")
        return

    if len(session["players"]) >= 2:
        await update.message.reply_text("duel hanya untuk 2 pemain, sudah penuh!")
        return

    session["players"].append(user.id)
    session["player_objs"][user.id] = user
    session["tebakan_per_player"][user.id] = 0

    nama = await get_nama(user)
    jumlah = len(session["players"])

    if jumlah == 1:
        await update.message.reply_text(f"✅ {nama} join! menunggu 1 pemain lagi...")
    else:
        await update.message.reply_text(
            f"✅ {nama} join!\n\n"
            f"👥 sudah 2 pemain! host ketik /startduel untuk mulai"
        )

async def startduel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id not in duel_sessions:
        await update.message.reply_text("belum ada game duel")
        return

    session = duel_sessions[chat_id]

    if session["started"]:
        await update.message.reply_text("game sudah dimulai")
        return

    if len(session["players"]) < 2:
        await update.message.reply_text("⚔️ duel butuh tepat 2 pemain!")
        return

    session["started"] = True
    session["turn"] = 0

    player_a = session["player_objs"][session["players"][0]]
    player_b = session["player_objs"][session["players"][1]]
    nama_a = await get_nama(player_a)
    nama_b = await get_nama(player_b)

    await update.message.reply_text(
        f"⚔️ <b>DUEL DIMULAI!</b>\n\n"
        f"👤 <b>{nama_a}</b>  VS  👤 <b>{nama_b}</b>\n\n"
        f"📨 bot sudah DM kalian berdua!\n"
        f"silakan masukkan angka rahasiamu via DM bot.\n\n"
        f"game akan mulai setelah keduanya memasukkan angka 🎯",
        parse_mode="HTML"
    )

    for uid in session["players"]:
        user_obj = session["player_objs"][uid]
        nama = await get_nama(user_obj)
        try:
            await context.bot.send_message(
                uid,
                f"⚔️ <b>ANGKA DUEL</b>\n\n"
                f"halo {nama}! 👋\n\n"
                f"masukkan angka rahasiamu:\n"
                f"🔢 <b>range: 1 - 100</b>\n\n"
                f"angkamu akan ditebak oleh lawanmu!\n"
                f"pilih dengan bijak 😏",
                parse_mode="HTML"
            )
            duel_dm_pending[uid] = chat_id
        except Exception:
            await context.bot.send_message(
                chat_id,
                f"⚠️ bot tidak bisa DM {nama}!\n"
                f"pastikan kamu sudah pernah chat dengan bot dulu ya."
            )

async def stopduel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in duel_sessions:
        for uid in duel_sessions[chat_id].get("players", []):
            duel_dm_pending.pop(uid, None)
        del duel_sessions[chat_id]
        await update.message.reply_text("game duel dihentikan")
    else:
        await update.message.reply_text("tidak ada game duel yang berjalan")

async def proses_duel_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in duel_dm_pending:
        return

    text = update.message.text
    if not text or not text.strip().lstrip("-").isdigit():
        await update.message.reply_text("tolong masukkan angka saja (1-100)")
        return

    angka_input = int(text.strip())

    if not (1 <= angka_input <= 100):
        await update.message.reply_text("⚠️ angka harus antara 1 - 100!")
        return

    chat_id = duel_dm_pending.pop(user_id)

    if chat_id not in duel_sessions:
        await update.message.reply_text("sesi duel sudah tidak ada")
        return

    session = duel_sessions[chat_id]
    session["numbers"][user_id] = angka_input

    await update.message.reply_text(
        f"✅ angkamu (<b>{angka_input}</b>) sudah tersimpan!\n\n"
        f"kembali ke grup dan tunggu giliran ya 😊",
        parse_mode="HTML"
    )

    session["numbers_received"].add(user_id)

    if len(session["numbers_received"]) == 2:
        player_a_id = session["players"][0]
        player_b_id = session["players"][1]
        nama_a = await get_nama(session["player_objs"][player_a_id])
        nama_b = await get_nama(session["player_objs"][player_b_id])

        await context.bot.send_message(
            chat_id,
            f"🎯 <b>KEDUA PEMAIN SUDAH SIAP!</b>\n\n"
            f"⚔️ <b>{nama_a}</b> VS <b>{nama_b}</b>\n\n"
            f"📌 aturan:\n"
            f"• {nama_a} menebak angka {nama_b}\n"
            f"• {nama_b} menebak angka {nama_a}\n"
            f"• siapa duluan yang benar, menang!\n\n"
            f"giliran pertama: <b>{nama_a}</b> 🎲",
            parse_mode="HTML"
        )

async def proses_duel_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id not in duel_sessions:
        return

    session = duel_sessions[chat_id]

    if not session["started"]:
        return

    if len(session["numbers_received"]) < 2:
        return

    text = update.message.text
    if not text or not text.strip().lstrip("-").isdigit():
        return

    user = update.message.from_user
    user_id = user.id
    players = session["players"]

    current_turn_id = players[session["turn"] % 2]
    if user_id != current_turn_id:
        return

    tebakan = int(text.strip())
    lawan_id = players[(session["turn"] + 1) % 2]
    target = session["numbers"][lawan_id]
    nama = await get_nama(user)
    nama_lawan = await get_nama(session["player_objs"][lawan_id])

    session["tebakan_per_player"][user_id] = session["tebakan_per_player"].get(user_id, 0) + 1

    if tebakan > target:
        await update.message.reply_text(f"⬇️ terlalu besar, {nama}!", reply_to_message_id=update.message.message_id)
    elif tebakan < target:
        await update.message.reply_text(f"⬆️ terlalu kecil, {nama}!", reply_to_message_id=update.message.message_id)
    else:
        jumlah_tebak = session["tebakan_per_player"][user_id]
        loser_obj = session["player_objs"][lawan_id]
        del duel_sessions[chat_id]

        await add_score(chat_id, user, 100)
        await add_score(chat_id, loser_obj, 10)

        await update.message.reply_text(
            f"🏆 <b>{nama} MENANG DUEL!</b>\n\n"
            f"angka rahasia {nama_lawan} memang <b>{target}</b>!\n\n"
            f"ditebak dalam <b>{jumlah_tebak}x</b> giliran\n\n"
            f"🏅 {nama} +100 poin!\n"
            f"🏅 {nama_lawan} +10 poin",
            parse_mode="HTML"
        )
        return

    session["turn"] += 1
    next_id = players[session["turn"] % 2]
    next_player = session["player_objs"][next_id]
    next_nama = await get_nama(next_player)

    await context.bot.send_message(
        chat_id,
        f"🎲 giliran: <b>{next_nama}</b>",
        parse_mode="HTML"
    )

# =====================
# /angkataruhan
# =====================

async def angkataruhan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in taruhan_sessions:
        await update.message.reply_text("💰 sudah ada game taruhan, tunggu selesai dulu atau /stoptaruhan")
        return

    taruhan_sessions[chat_id] = {
        "players": [],
        "player_objs": {},
        "numbers": {},
        "bets": {},
        "numbers_received": set(),
        "bets_received": set(),
        "guesses": {},
        "turn": 0,
        "started": False
    }

    await update.message.reply_text(
        "💰 <b>ANGKA TARUHAN!</b>\n\n"
        "duel angka dengan taruhan saldo!\n"
        "diskusikan dulu jumlah taruhan dengan lawanmu.\n\n"
        "/jointaruhan untuk ikut\n"
        "butuh tepat 2 pemain\n\n"
        "setelah 2 orang join, host ketik /starttaruhan",
        parse_mode="HTML"
    )

async def jointaruhan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user = update.message.from_user

    if chat_id not in taruhan_sessions:
        await update.message.reply_text("belum ada game taruhan. ketik /angkataruhan dulu")
        return

    session = taruhan_sessions[chat_id]

    if session["started"]:
        await update.message.reply_text("game sudah dimulai, tidak bisa join")
        return

    if user.id in session["player_objs"]:
        await update.message.reply_text("kamu sudah join!")
        return

    if len(session["players"]) >= 2:
        await update.message.reply_text("sudah penuh! hanya untuk 2 pemain")
        return

    session["players"].append(user.id)
    session["player_objs"][user.id] = user

    nama = await get_nama(user)
    jumlah = len(session["players"])

    if jumlah == 1:
        await update.message.reply_text(f"✅ {nama} join! menunggu 1 pemain lagi...")
    else:
        await update.message.reply_text(
            f"✅ {nama} join!\n\n"
            f"👥 sudah 2 pemain! host ketik /starttaruhan"
        )

async def starttaruhan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id not in taruhan_sessions:
        await update.message.reply_text("belum ada game taruhan")
        return

    session = taruhan_sessions[chat_id]

    if session["started"]:
        await update.message.reply_text("game sudah dimulai")
        return

    if len(session["players"]) < 2:
        await update.message.reply_text("butuh tepat 2 pemain!")
        return

    session["started"] = True

    player_a = session["player_objs"][session["players"][0]]
    player_b = session["player_objs"][session["players"][1]]
    nama_a = await get_nama(player_a)
    nama_b = await get_nama(player_b)

    await update.message.reply_text(
        f"💰 <b>TARUHAN DIMULAI!</b>\n\n"
        f"👤 <b>{nama_a}</b>  VS  👤 <b>{nama_b}</b>\n\n"
        f"📨 bot sudah DM kalian berdua!\n"
        f"masukkan angka rahasia dan jumlah taruhan via DM.",
        parse_mode="HTML"
    )

    for uid in session["players"]:
        user_obj = session["player_objs"][uid]
        nama = await get_nama(user_obj)
        try:
            await context.bot.send_message(
                uid,
                f"💰 <b>ANGKA TARUHAN</b>\n\n"
                f"halo {nama}! 👋\n\n"
                f"<b>langkah 1:</b> masukkan angka rahasiamu\n"
                f"🔢 range: 1 - 100\n\n"
                f"angkamu akan ditebak lawan, pilih dengan bijak!",
                parse_mode="HTML"
            )
            taruhan_dm_pending[uid] = {"chat_id": chat_id, "stage": "angka"}
        except Exception:
            await context.bot.send_message(
                chat_id,
                f"⚠️ bot tidak bisa DM {nama}! pastikan sudah pernah chat dengan bot."
            )

async def stoptaruhan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in taruhan_sessions:
        for uid in taruhan_sessions[chat_id].get("players", []):
            taruhan_dm_pending.pop(uid, None)
        del taruhan_sessions[chat_id]
        await update.message.reply_text("game taruhan dihentikan")
    else:
        await update.message.reply_text("tidak ada game taruhan yang berjalan")

async def _start_taruhan_game(chat_id, context):
    session = taruhan_sessions[chat_id]
    player_a_id = session["players"][0]
    player_b_id = session["players"][1]
    player_a = session["player_objs"][player_a_id]
    player_b = session["player_objs"][player_b_id]

    bet_a = session["bets"].get(player_a_id, 0)
    bet_b = session["bets"].get(player_b_id, 0)

    nama_a = await get_nama(player_a)
    nama_b = await get_nama(player_b)

    if bet_a != bet_b:
        del taruhan_sessions[chat_id]
        await context.bot.send_message(
            chat_id,
            f"❌ <b>TARUHAN TIDAK SAMA!</b>\n\n"
            f"{nama_a}: {format_rupiah(bet_a)}\n"
            f"{nama_b}: {format_rupiah(bet_b)}\n\n"
            f"game dibatalkan. diskusikan dulu jumlahnya, lalu /angkataruhan lagi.",
            parse_mode="HTML"
        )
        return

    bet = bet_a

    await init_wallet(player_a)
    await init_wallet(player_b)
    wallet_a = await db_get_wallet(player_a_id)
    wallet_b = await db_get_wallet(player_b_id)

    saldo_a = wallet_a["saldo"] if wallet_a else SLOT_INITIAL
    saldo_b = wallet_b["saldo"] if wallet_b else SLOT_INITIAL

    errors = []
    if saldo_a < bet:
        errors.append(f"{nama_a} (saldo: {format_rupiah(saldo_a)})")
    if saldo_b < bet:
        errors.append(f"{nama_b} (saldo: {format_rupiah(saldo_b)})")

    if errors:
        del taruhan_sessions[chat_id]
        await context.bot.send_message(
            chat_id,
            f"❌ <b>SALDO TIDAK CUKUP!</b>\n\n"
            f"taruhan: {format_rupiah(bet)}\n\n"
            f"saldo kurang milik: {', '.join(errors)}\n\n"
            f"game dibatalkan.",
            parse_mode="HTML"
        )
        return

    session["bet_amount"] = bet
    session["guesses"] = {player_a_id: 0, player_b_id: 0}
    session["turn"] = 0

    await context.bot.send_message(
        chat_id,
        f"🎰 <b>SEMUA SIAP! TARUHAN DIMULAI!</b>\n\n"
        f"⚔️ <b>{nama_a}</b> VS <b>{nama_b}</b>\n"
        f"💰 taruhan: <b>{format_rupiah(bet)}</b> masing-masing\n\n"
        f"📌 aturan:\n"
        f"• {nama_a} menebak angka {nama_b}\n"
        f"• {nama_b} menebak angka {nama_a}\n"
        f"• siapa duluan yang benar, menang dan dapat {format_rupiah(bet)}!\n\n"
        f"giliran pertama: <b>{nama_a}</b> 🎲",
        parse_mode="HTML"
    )

async def proses_taruhan_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in taruhan_dm_pending:
        return

    pending = taruhan_dm_pending[user_id]
    chat_id = pending["chat_id"]
    stage = pending["stage"]

    text = update.message.text
    if not text or not text.strip().lstrip("-").isdigit():
        if stage == "angka":
            await update.message.reply_text("tolong masukkan angka saja (1-100)")
        else:
            await update.message.reply_text("tolong masukkan jumlah taruhan dalam angka. contoh: 50000")
        return

    nilai = int(text.strip())

    if stage == "angka":
        if not (1 <= nilai <= 100):
            await update.message.reply_text("⚠️ angka harus antara 1 - 100!")
            return

        if chat_id not in taruhan_sessions:
            taruhan_dm_pending.pop(user_id, None)
            await update.message.reply_text("sesi taruhan sudah tidak ada")
            return

        taruhan_sessions[chat_id]["numbers"][user_id] = nilai
        taruhan_sessions[chat_id]["numbers_received"].add(user_id)
        taruhan_dm_pending[user_id]["stage"] = "taruhan"

        await update.message.reply_text(
            f"✅ angkamu (<b>{nilai}</b>) tersimpan!\n\n"
            f"<b>langkah 2:</b> masukkan jumlah taruhan (Rp)\n"
            f"contoh: ketik <code>50000</code> untuk taruhan Rp 50.000\n\n"
            f"pastikan jumlahnya sama dengan lawanmu!",
            parse_mode="HTML"
        )

    elif stage == "taruhan":
        if nilai <= 0:
            await update.message.reply_text("❌ jumlah taruhan harus lebih dari 0!")
            return

        if chat_id not in taruhan_sessions:
            taruhan_dm_pending.pop(user_id, None)
            await update.message.reply_text("sesi taruhan sudah tidak ada")
            return

        taruhan_sessions[chat_id]["bets"][user_id] = nilai
        taruhan_sessions[chat_id]["bets_received"].add(user_id)
        del taruhan_dm_pending[user_id]

        await update.message.reply_text(
            f"✅ taruhan <b>{format_rupiah(nilai)}</b> tersimpan!\n\n"
            f"menunggu lawan selesai input...",
            parse_mode="HTML"
        )

        if len(taruhan_sessions[chat_id]["bets_received"]) == 2:
            await _start_taruhan_game(chat_id, context)

async def proses_taruhan_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id not in taruhan_sessions:
        return

    session = taruhan_sessions[chat_id]

    if not session["started"]:
        return

    if "bet_amount" not in session:
        return

    text = update.message.text
    if not text or not text.strip().lstrip("-").isdigit():
        return

    user = update.message.from_user
    user_id = user.id
    players = session["players"]

    current_turn_id = players[session["turn"] % 2]
    if user_id != current_turn_id:
        return

    tebakan = int(text.strip())
    lawan_id = players[(session["turn"] + 1) % 2]
    target = session["numbers"][lawan_id]
    nama = await get_nama(user)
    nama_lawan = await get_nama(session["player_objs"][lawan_id])

    session["guesses"][user_id] = session["guesses"].get(user_id, 0) + 1

    if tebakan > target:
        await update.message.reply_text(f"⬇️ terlalu besar, {nama}!")
    elif tebakan < target:
        await update.message.reply_text(f"⬆️ terlalu kecil, {nama}!")
    else:
        bet = session["bet_amount"]
        jumlah_tebak = session["guesses"][user_id]
        loser_obj = session["player_objs"][lawan_id]

        del taruhan_sessions[chat_id]

        wallet_winner = await db_get_wallet(user_id)
        wallet_loser = await db_get_wallet(lawan_id)

        saldo_winner = (wallet_winner["saldo"] if wallet_winner else SLOT_INITIAL) + bet
        saldo_loser = (wallet_loser["saldo"] if wallet_loser else SLOT_INITIAL) - bet

        await db_set_wallet(user_id, get_raw_name(user), saldo_winner)
        await db_set_wallet(lawan_id, get_raw_name(loser_obj), saldo_loser)

        await add_score(chat_id, user, 100)
        await add_score(chat_id, loser_obj, 10)

        await update.message.reply_text(
            f"🏆 <b>{nama} MENANG TARUHAN!</b>\n\n"
            f"angka rahasia {nama_lawan} memang <b>{target}</b>!\n"
            f"ditebak dalam <b>{jumlah_tebak}x</b> giliran\n\n"
            f"💰 {nama} dapat: <b>+{format_rupiah(bet)}</b>\n"
            f"💸 {nama_lawan} kehilangan: <b>-{format_rupiah(bet)}</b>\n\n"
            f"💳 saldo {nama}: <b>{format_rupiah(saldo_winner)}</b>",
            parse_mode="HTML"
        )
        return

    session["turn"] += 1
    next_id = players[session["turn"] % 2]
    next_player = session["player_objs"][next_id]
    next_nama = await get_nama(next_player)

    await context.bot.send_message(
        chat_id,
        f"🎲 giliran: <b>{next_nama}</b>",
        parse_mode="HTML"
    )
