import random
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InlineQueryResultCachedSticker, InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import ContextTypes

from data import add_score, get_nama, get_raw_name, init_wallet, format_rupiah, SLOT_INITIAL
from db import db_get_wallet, db_set_wallet

from uno_game import UnoGame, STICKERS, STICKER_TO_CARD, get_card_label, get_card_sticker, COLOR_LABEL
from uno_actions import (
    send_turn_message, process_play_card, process_draw_card,
    process_pass, process_color_choice
)

# Session storage
uno_sessions = {}  # chat_id -> UnoGame instance
uno_bet_pending = {}  # chat_id -> {"players": [], "objs": {}, "bets": {}}

async def unotaruhan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    if cid in uno_sessions or cid in uno_bet_pending:
        await update.message.reply_text("🃏 sudah ada game UNO. /stopuno untuk hentikan.")
        return
    uno_bet_pending[cid] = {
        "players": [], "objs": {}, "bets": {}, "bets_received": set(),
        "started": False
    }
    await update.message.reply_text(
        "🃏 <b>UNO TARUHAN!</b>\n\n"
        "ketik /joinuno untuk ikut (min. 2, maks. 10)\n"
        "setelah semua siap, host ketik /startuno",
        parse_mode="HTML"
    )

async def joinuno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    user = update.message.from_user
    if cid not in uno_bet_pending:
        await update.message.reply_text("belum ada game UNO. ketik /unotaruhan dulu")
        return
    s = uno_bet_pending[cid]
    if s["started"]:
        await update.message.reply_text("game sudah mulai"); return
    if user.id in s["objs"]:
        await update.message.reply_text("kamu sudah join!"); return
    if len(s["players"]) >= 10:
        await update.message.reply_text("sudah penuh (maks. 10)"); return
    s["players"].append(user.id)
    s["objs"][user.id] = user
    nama = await get_nama(user)
    daftar = "\n".join([f"• {await get_nama(s['objs'][u])}" for u in s["players"]])
    await update.message.reply_text(
        f"✅ {nama} join!\n\n👥 <b>Pemain ({len(s['players'])}):</b>\n{daftar}",
        parse_mode="HTML"
    )

async def startuno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    if cid not in uno_bet_pending:
        await update.message.reply_text("belum ada game UNO"); return
    s = uno_bet_pending[cid]
    if s["started"]:
        await update.message.reply_text("game sudah mulai"); return
    if len(s["players"]) < 2:
        await update.message.reply_text("minimal 2 pemain!"); return
    s["started"] = True
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Rp 500.000", callback_data=f"unobet_{cid}_500000"),
         InlineKeyboardButton("Rp 1.000.000", callback_data=f"unobet_{cid}_1000000")],
        [InlineKeyboardButton("Rp 2.000.000", callback_data=f"unobet_{cid}_2000000"),
         InlineKeyboardButton("Rp 3.000.000", callback_data=f"unobet_{cid}_3000000")],
        [InlineKeyboardButton("Rp 7.000.000", callback_data=f"unobet_{cid}_7000000")],
        [InlineKeyboardButton("✏️ Masukkan angka sendiri", callback_data=f"unobet_{cid}_custom")],
    ])
    await update.message.reply_text(
        "💰 <b>PILIH TARUHAN</b>\n\n"
        "salah satu pemain klik jumlah taruhan:\n"
        "<i>jumlah ini berlaku untuk semua pemain!</i>",
        reply_markup=kb, parse_mode="HTML"
    )

async def stopuno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    if cid in uno_sessions:
        game = uno_sessions[cid]
        # Kembalikan saldo
        for uid in game.players:
            w = await db_get_wallet(uid)
            if w:
                await db_set_wallet(uid, get_raw_name(await context.bot.get_chat(uid)), w["saldo"] + game.bet)
        del uno_sessions[cid]
        await update.message.reply_text("🚫 game UNO dihentikan. Taruhan dikembalikan.")
    elif cid in uno_bet_pending:
        del uno_bet_pending[cid]
        await update.message.reply_text("🚫 game UNO dibatalkan.")
    else:
        await update.message.reply_text("tidak ada game UNO")

async def leaveuno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    uid = update.message.from_user.id
    if cid in uno_sessions:
        game = uno_sessions[cid]
        if uid in game.players:
            player = game.players[uid]
            player.eliminated = True
            await update.message.reply_text(f"🚪 {player.name} keluar dari permainan.")
            if game.is_game_over():
                await end_game(cid, game, context)
            else:
                if game.get_current_player() and game.get_current_player().user_id == uid:
                    game.advance_turn()
                    await send_turn_message(context.bot, cid, game, {u: p.name for u, p in game.players.items()})
        else:
            await update.message.reply_text("kamu bukan pemain.")
    else:
        await update.message.reply_text("tidak ada game UNO aktif.")

# ---------- BETTING ----------
async def handle_uno_bet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    parts = q.data.split("_", 2)
    cid = int(parts[1])
    val = parts[2]

    if cid not in uno_bet_pending:
        await q.answer("sesi tidak ditemukan", show_alert=True); return
    s = uno_bet_pending[cid]
    if uid not in s["players"]:
        await q.answer("kamu bukan pemain", show_alert=True); return

    await q.answer()
    if val == "custom":
        # Simpan state untuk input manual
        context.user_data["uno_custom_bet_chat"] = cid
        await q.edit_message_text("✏️ Ketik jumlah taruhan di chat ini (angka saja)")
        return

    amount = int(val)
    await process_bet(cid, amount, context, q)

async def proses_uno_group_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or update.message.chat.type == "private":
        return
    cid = context.user_data.pop("uno_custom_bet_chat", None)
    if not cid or cid not in uno_bet_pending:
        return
    text = update.message.text.strip().replace(".", "").replace(",", "")
    if not text.isdigit():
        return
    amount = int(text)
    if amount <= 0:
        await update.message.reply_text("jumlah harus > 0")
        return
    await process_bet(cid, amount, context, update=update)

async def process_bet(cid, amount, context, q=None, update=None):
    s = uno_bet_pending[cid]
    for uid in s["players"]:
        s["bets"][uid] = amount
    s["bets_received"] = set(s["players"])
    msg = f"💰 Taruhan dipilih: <b>{format_rupiah(amount)}</b>/orang\n⏳ memproses..."
    if q:
        await q.edit_message_text(msg, parse_mode="HTML")
    elif update:
        await update.message.reply_text(msg, parse_mode="HTML")
    await validate_and_start(cid, context)

async def validate_and_start(cid, context):
    s = uno_bet_pending.pop(cid)
    bet = s["bets"][s["players"][0]]
    objs = s["objs"]
    players = s["players"]

    # Cek saldo
    short = []
    for uid in players:
        await init_wallet(objs[uid])
        w = await db_get_wallet(uid)
        saldo = w["saldo"] if w else SLOT_INITIAL
        if saldo < bet:
            short.append(f"• {await get_nama(objs[uid])} (saldo: {format_rupiah(saldo)})")
    if short:
        await context.bot.send_message(cid,
            f"❌ <b>SALDO TIDAK CUKUP!</b>\n\ntaruhan: {format_rupiah(bet)}\n\n" + "\n".join(short) + "\n\ngame dibatalkan.",
            parse_mode="HTML")
        return

    # Potong saldo
    for uid in players:
        w = await db_get_wallet(uid)
        await db_set_wallet(uid, get_raw_name(objs[uid]), (w["saldo"] if w else SLOT_INITIAL) - bet)

    # Buat game instance
    player_names = {uid: await get_nama(objs[uid]) for uid in players}
    game = UnoGame(cid, players, player_names, bet)
    uno_sessions[cid] = game

    # Kirim pesan mulai
    names = "\n".join([f"• {player_names[uid]}" for uid in players])
    await context.bot.send_message(cid,
        f"🃏 <b>UNO TARUHAN DIMULAI!</b>\n\n"
        f"💰 Taruhan: <b>{format_rupiah(bet)}</b>/orang\n"
        f"🏆 Total pot: <b>{format_rupiah(game.pot)}</b>\n\n"
        f"👥 Pemain:\n{names}\n\n"
        f"7 kartu sudah dibagikan!\n"
        f"gunakan tombol <b>Lihat Kartu</b> untuk melihat & memainkan kartu.",
        parse_mode="HTML"
    )

    # Kirim sticker kartu awal
    top = game.get_top_card()
    stk = get_card_sticker(top)
    if stk:
        await context.bot.send_sticker(cid, stk)
    await context.bot.send_message(cid, f"🎴 kartu awal: <b>{get_card_label(top)}</b>", parse_mode="HTML")

    await send_turn_message(context.bot, cid, game, player_names)

# ---------- INLINE QUERY ----------
async def handle_uno_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    uid = query.from_user.id

    # Cari game yang diikuti user
    game = None
    cid = None
    for chat_id, g in uno_sessions.items():
        if uid in g.players and not g.players[uid].eliminated and not g.players[uid].finished:
            game = g
            cid = chat_id
            break
    if not game:
        await query.answer([], cache_time=0, is_personal=True)
        return

    player = game.players[uid]
    results = []

    # Tampilkan semua kartu di tangan
    for i, card in enumerate(player.hand):
        stk = get_card_sticker(card)
        if stk:
            results.append(InlineQueryResultCachedSticker(
                id=f"card_{i}",
                sticker_file_id=stk,
            ))
        else:
            label = get_card_label(card)
            results.append(InlineQueryResultArticle(
                id=f"card_{i}",
                title=label,
                input_message_content=InputTextMessageContent(f"🃏 {label}")
            ))

    # Info permainan
    top = game.get_top_card()
    active = game.get_active_players()
    info = f"🎴 Kartu teratas: {get_card_label(top)}\n"
    info += f"👥 Pemain: {', '.join([game.players[u].name for u in active])}"
    results.append(InlineQueryResultArticle(
        id="info",
        title="ℹ️ Info Permainan",
        input_message_content=InputTextMessageContent(info)
    ))

    try:
        await query.answer(results, cache_time=0, is_personal=True)
    except Exception as e:
        print(f"Inline error: {e}")

# ---------- CHOSEN INLINE RESULT ----------
async def handle_uno_chosen_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dipanggil saat user memilih salah satu hasil inline query."""
    result = update.chosen_inline_result
    uid = result.from_user.id
    # Cari game
    game = None
    cid = None
    for chat_id, g in uno_sessions.items():
        if uid in g.players:
            game = g
            cid = chat_id
            break
    if not game:
        return

    player = game.players.get(uid)
    if not player or player.eliminated or player.finished:
        return

    # Periksa apakah ini giliran pemain
    current = game.get_current_player()
    if current.user_id != uid:
        # Bukan giliran, abaikan
        return

    # Parse result_id
    res_id = result.result_id
    if res_id == "info":
        # Tidak ada aksi
        return
    elif res_id.startswith("card_"):
        idx = int(res_id.split("_")[1])
        if idx < len(player.hand):
            card = player.hand[idx]
            # Cek apakah kartu bisa dimainkan
            if game.can_play(card):
                success, status = await process_play_card(
                    context.bot, cid, game, uid, card, context
                )
                if status == "game_over":
                    await end_game(cid, game, context)
            else:
                # Kartu tidak bisa dimainkan -> beri tahu via pesan sementara? Skip.
                pass

# ---------- CALLBACK QUERY (untuk warna, main setelah draw, pass) ----------
async def handle_uno_play_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    data = q.data

    if data.startswith("unoplay_"):
        _, cid_s, idx_s = data.split("_")
        cid = int(cid_s)
        idx = int(idx_s)
        game = uno_sessions.get(cid)
        if not game:
            await q.answer("Sesi tidak ada", show_alert=True); return
        player = game.players.get(uid)
        if not player:
            await q.answer("Bukan pemain", show_alert=True); return
        if game.get_current_player().user_id != uid:
            await q.answer("Bukan giliranmu", show_alert=True); return
        if idx >= len(player.hand):
            await q.answer("Kartu tidak valid"); return
        card = player.hand[idx]
        if not game.can_play(card):
            await q.answer("Kartu tidak bisa dimainkan"); return

        await q.edit_message_reply_markup(None)
        success, status = await process_play_card(context.bot, cid, game, uid, card, context)
        if status == "game_over":
            await end_game(cid, game, context)

    elif data.startswith("unodraw_"):
        cid = int(data.split("_")[1])
        game = uno_sessions.get(cid)
        if not game: return
        if game.get_current_player().user_id != uid:
            await q.answer("Bukan giliranmu", show_alert=True); return
        await q.edit_message_reply_markup(None)
        await process_draw_card(context.bot, cid, game, uid, context)

    elif data.startswith("unopass_"):
        cid = int(data.split("_")[1])
        game = uno_sessions.get(cid)
        if not game: return
        if game.get_current_player().user_id != uid:
            await q.answer("Bukan giliranmu", show_alert=True); return
        await q.edit_message_reply_markup(None)
        await process_pass(context.bot, cid, game, uid, context)

    elif data.startswith("unocolor_"):
        _, cid_s, color = data.split("_")
        cid = int(cid_s)
        game = uno_sessions.get(cid)
        if not game: return
        if game.pending_color_chooser != uid:
            await q.answer("Bukan kamu yang memilih warna", show_alert=True); return
        await q.edit_message_reply_markup(None)
        await process_color_choice(context.bot, cid, game, uid, color, context)
        if game.is_game_over():
            await end_game(cid, game, context)

# ---------- END GAME ----------
async def end_game(cid, game: UnoGame, context):
    # Tentukan urutan pemenang
    order = game.finished_players.copy()
    for uid in game.player_order:
        if uid not in order and not game.players[uid].eliminated:
            order.append(uid)
    for uid in game.player_order:
        if uid not in order:
            order.append(uid)

    winner = order[0] if order else None
    if winner:
        winnings = game.pot
        w = await db_get_wallet(winner)
        await db_set_wallet(winner, get_raw_name(await context.bot.get_chat(winner)), (w["saldo"] if w else SLOT_INITIAL) + winnings)

        # Tambah skor
        for rank, uid in enumerate(order, 1):
            user_obj = await context.bot.get_chat(uid)
            await add_score(cid, user_obj, 500 if rank == 1 else 100)

    # Buat pesan hasil
    lines = []
    for rank, uid in enumerate(order, 1):
        name = game.players[uid].name
        medal = {1:"🥇",2:"🥈",3:"🥉"}.get(rank, f"#{rank}")
        if rank == 1:
            extra = f" +{format_rupiah(game.pot)} saldo, +500 poin"
        elif game.players[uid].eliminated:
            extra = " (keluar) +100 poin"
        else:
            extra = " +100 poin"
        lines.append(f"{medal} {name}{extra}")

    await context.bot.send_message(cid,
        f"🏆 <b>GAME UNO TARUHAN SELESAI!</b>\n\n"
        f"💰 Taruhan: {format_rupiah(game.bet)}/orang | Pot: {format_rupiah(game.pot)}\n\n"
        + "\n".join(lines),
        parse_mode="HTML"
    )
    del uno_sessions[cid]

# Placeholder untuk kompatibilitas
async def handle_uno_sticker_in_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def proses_uno_inline_draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass
