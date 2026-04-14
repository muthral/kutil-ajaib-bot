import random
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from data import add_score, get_nama, get_raw_name, init_wallet, format_rupiah, SLOT_INITIAL
from db import db_get_wallet, db_set_wallet

# -------------------- DECK & CARD HELPERS --------------------
COLORS = ["r", "g", "b", "y"]
COLOR_LABEL = {"r": "🔴Merah", "g": "🟢Hijau", "b": "🔵Biru", "y": "🟡Kuning"}
COLOR_EMOJI_INFO = {"r": "❤️", "g": "💚", "b": "💙", "y": "💛"}

def _new_deck():
    deck = []
    for c in COLORS:
        for v in ["0","1","2","3","4","5","6","7","8","9","draw","skip","reverse"]:
            deck.append((c, v))
            if v != "0":
                deck.append((c, v))
    for _ in range(4):
        deck.append(("x", "colorchooser"))
        deck.append(("x", "draw_four"))
    random.shuffle(deck)
    return deck

def _label(card):
    c, v = card
    col = COLOR_LABEL.get(c, "")
    lbl = {"draw": "+2", "skip": "⊘", "reverse": "⇌", "colorchooser": "Wild", "draw_four": "Wild+4"}
    return f"{col} {lbl.get(v, v)}" if col else lbl.get(v, v)

def _can_play(card, top, chosen_color=None):
    c, v = card
    tc, tv = top
    if v in ("colorchooser", "draw_four"):
        return True
    if tc == "x":
        return c == chosen_color if chosen_color else True
    return c == tc or v == tv

def _draw_cards(session, n):
    drawn = []
    for _ in range(n):
        if not session["deck"]:
            if len(session["discard"]) > 1:
                top = session["discard"].pop()
                random.shuffle(session["discard"])
                session["deck"] = session["discard"]
                session["discard"] = [top]
        if session["deck"]:
            drawn.append(session["deck"].pop())
    return drawn

# -------------------- UNO SESSION STORAGE --------------------
uno_sessions = {}

# -------------------- COMMAND HANDLERS --------------------
async def unotaruhan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    if cid in uno_sessions:
        await update.message.reply_text("🃏 sudah ada game UNO taruhan. /stopuno untuk hentikan.")
        return
    uno_sessions[cid] = {
        "players": [], "objs": {}, "bets": {}, "bets_received": set(),
        "hands": {}, "deck": [], "discard": [], "dir": 1, "turn_idx": 0,
        "chosen_color": None, "started": False, "bet": None, "pot": 0,
        "finish_order": [], "turn_msg_id": None,
        "color_pending": False, "color_pending_uid": None,
        "bet_custom_pending": None, "eliminated": set(),
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
    if cid not in uno_sessions:
        await update.message.reply_text("belum ada game UNO. ketik /unotaruhan dulu")
        return
    s = uno_sessions[cid]
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
    if cid not in uno_sessions:
        await update.message.reply_text("belum ada game UNO"); return
    s = uno_sessions[cid]
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
    if cid not in uno_sessions:
        await update.message.reply_text("tidak ada game UNO"); return
    s = uno_sessions[cid]
    if s.get("bet") is not None:
        for uid in s["players"]:
            w = await db_get_wallet(uid)
            if w:
                await db_set_wallet(uid, get_raw_name(s["objs"][uid]), w["saldo"] + s["bet"])
        await update.message.reply_text(
            f"🚫 game UNO dibatalkan.\n"
            f"taruhan {format_rupiah(s['bet'])} dikembalikan ke semua pemain. saldo utuh."
        )
    else:
        await update.message.reply_text("🚫 game UNO dibatalkan.")
    del uno_sessions[cid]

async def leaveuno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    uid = update.message.from_user.id

    if cid not in uno_sessions:
        return
    s = uno_sessions[cid]
    if uid not in s["objs"]:
        return

    nama = await get_nama(s["objs"][uid])

    if s.get("bet") is None:
        s["players"].remove(uid)
        del s["objs"][uid]
        s["bets"].pop(uid, None)
        s["bets_received"].discard(uid)
        await update.message.reply_text(f"🚪 {nama} keluar dari game UNO.")
        if len(s["players"]) < 2:
            del uno_sessions[cid]
            await update.message.reply_text("❌ pemain kurang, game UNO dibatalkan.")
        return

    if uid in s.get("finish_order", []) or uid in s.get("eliminated", set()):
        await update.message.reply_text("kamu sudah tidak aktif di game ini.")
        return

    s.setdefault("eliminated", set()).add(uid)
    await context.bot.send_message(cid, f"🚪 <b>{nama}</b> keluar dari permainan!", parse_mode="HTML")

    remaining = [u for u in s["players"]
                 if u not in s.get("finish_order", []) and u not in s.get("eliminated", set())]

    if len(remaining) <= 1:
        if remaining:
            winner_uid = remaining[0]
            if winner_uid not in s["finish_order"]:
                s["finish_order"].insert(0, winner_uid)
        await context.bot.send_message(cid, "🏁 <b>Permainan Selesai!</b>", parse_mode="HTML")
        await _end_game(cid, s, context)
        return

    current_uid = s["players"][s["turn_idx"] % len(s["players"])]
    if s.get("color_pending") and s.get("color_pending_uid") == uid:
        s["color_pending"] = False
        s["color_pending_uid"] = None
        auto_color = random.choice(COLORS)
        s["chosen_color"] = auto_color
        label = {"r":"Merah 🔴","g":"Hijau 🟢","b":"Biru 🔵","y":"Kuning 🟡"}.get(auto_color, auto_color)
        await context.bot.send_message(cid, f"🌈 warna otomatis dipilih: <b>{label}</b>", parse_mode="HTML")

    if current_uid == uid:
        s["turn_idx"] = (s["turn_idx"] + s["dir"]) % len(s["players"])
        _skip_done_players(s)
        await _send_turn(cid, s, context)

# -------------------- BETTING & GAME START --------------------
async def handle_uno_bet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    parts = q.data.split("_", 2)
    cid = int(parts[1])
    val = parts[2]

    if cid not in uno_sessions:
        await q.answer("sesi UNO sudah tidak ada.", show_alert=True); return
    s = uno_sessions[cid]
    if uid not in s["players"]:
        await q.answer("kamu bukan pemain!", show_alert=True); return
    if s.get("bet") is not None:
        await q.answer("taruhan sudah dipilih!", show_alert=True); return

    await q.answer()

    if val == "custom":
        s["bet_custom_pending"] = uid
        nama = await get_nama(s["objs"][uid])
        await q.edit_message_text(
            f"✏️ <b>{nama}</b>, ketik jumlah taruhan di chat ini (angka saja)\n"
            f"contoh: <code>500000</code>",
            parse_mode="HTML"
        )
        return

    amount = int(val)
    await _process_group_bet(cid, amount, context, q=q)

async def proses_uno_group_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or update.message.chat.type == "private":
        return
    cid = update.message.chat_id
    if cid not in uno_sessions:
        return
    s = uno_sessions[cid]
    uid = update.message.from_user.id
    if s.get("bet_custom_pending") != uid:
        return
    text = update.message.text.strip().replace(".", "").replace(",", "")
    if not text.isdigit():
        return
    amount = int(text)
    if amount <= 0:
        await update.message.reply_text("❌ jumlah harus lebih dari 0!")
        return
    s["bet_custom_pending"] = None
    await _process_group_bet(cid, amount, context, update=update)

async def _process_group_bet(cid, amount, context, q=None, update=None):
    if cid not in uno_sessions:
        return
    s = uno_sessions[cid]
    for uid in s["players"]:
        s["bets"][uid] = amount
    s["bets_received"] = set(s["players"])
    msg_text = f"💰 Taruhan dipilih: <b>{format_rupiah(amount)}</b>/orang\n⏳ memproses..."
    if q:
        await q.edit_message_text(msg_text, parse_mode="HTML")
    elif update:
        await update.message.reply_text(msg_text, parse_mode="HTML")
    await _validate_and_start(cid, context)

async def _validate_and_start(cid, context):
    s = uno_sessions[cid]
    bet = s["bets"][s["players"][0]]
    pot = bet * len(s["players"])
    objs = s["objs"]

    short = []
    for uid in s["players"]:
        await init_wallet(objs[uid])
        w = await db_get_wallet(uid)
        if (w["saldo"] if w else SLOT_INITIAL) < bet:
            short.append(f"• {await get_nama(objs[uid])} (saldo: {format_rupiah(w['saldo'] if w else 0)})")
    if short:
        del uno_sessions[cid]
        await context.bot.send_message(cid,
            f"❌ <b>SALDO TIDAK CUKUP!</b>\n\ntaruhan: {format_rupiah(bet)}\n\n" + "\n".join(short) + "\n\ngame dibatalkan.",
            parse_mode="HTML"); return

    for uid in s["players"]:
        w = await db_get_wallet(uid)
        await db_set_wallet(uid, get_raw_name(objs[uid]), (w["saldo"] if w else SLOT_INITIAL) - bet)

    s["bet"] = bet
    s["pot"] = pot

    deck = _new_deck()
    hands = {uid: [] for uid in s["players"]}
    for _ in range(7):
        for uid in s["players"]:
            if deck: hands[uid].append(deck.pop())

    top = None
    while deck:
        top = deck.pop()
        if top[0] != "x": break
        deck.insert(0, top); top = None
    if not top: top = ("r", "0")

    s["deck"] = deck
    s["hands"] = hands
    s["discard"] = [top]
    s["chosen_color"] = None
    s["turn_idx"] = 0
    s["dir"] = 1

    names = "\n".join([f"• {await get_nama(objs[u])}" for u in s["players"]])
    await context.bot.send_message(cid,
        f"🃏 <b>UNO TARUHAN DIMULAI!</b>\n\n"
        f"💰 Taruhan: <b>{format_rupiah(bet)}</b>/orang\n"
        f"🏆 Total pot: <b>{format_rupiah(pot)}</b>\n\n"
        f"👥 Pemain:\n{names}\n\n"
        f"7 kartu sudah dibagikan!\n"
        f"klik tombol <b>Lihat Kartu</b> untuk melihat & memainkan kartu.",
        parse_mode="HTML"
    )

    await context.bot.send_message(cid, f"🎴 kartu awal: <b>{_label(top)}</b>", parse_mode="HTML")
    await _send_turn(cid, s, context)

# -------------------- TURN MANAGEMENT --------------------
async def _send_turn(cid, s, context):
    players = s["players"]
    if not players: return
    uid = players[s["turn_idx"] % len(players)]
    uobj = s["objs"][uid]
    nama = await get_nama(uobj)
    hand = s["hands"].get(uid, [])
    top = s["discard"][-1]
    chosen = s.get("chosen_color")

    color_hint = f"\n🌈 Warna: {COLOR_LABEL.get(chosen, '?')}" if chosen and top[0] == "x" else ""

    player_parts = []
    for p in players:
        if p in s.get("finish_order", []) or p in s.get("eliminated", set()):
            continue
        pname = await get_nama(s["objs"][p])
        pcards = len(s["hands"].get(p, []))
        player_parts.append(f"{pname} ({pcards} kartu)")

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🃏 Lihat Kartu", callback_data=f"unoview_{cid}")]
    ])

    msg = await context.bot.send_message(
        cid,
        f"🎲 giliran: <b>{nama}</b> ({len(hand)} kartu)\n"
        f"🎴 Kartu teratas: <b>{_label(top)}</b>{color_hint}\n\n"
        f"👥 {' → '.join(player_parts)}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    s["turn_msg_id"] = msg.message_id

def _skip_done_players(s):
    players = s["players"]
    n = len(players)
    if n <= 1: return
    done = set(s.get("finish_order", []))
    done.update(s.get("eliminated", set()))
    visited = 0
    while visited < n:
        uid = players[s["turn_idx"] % n]
        if uid not in done:
            break
        s["turn_idx"] = (s["turn_idx"] + s["dir"]) % n
        visited += 1

# -------------------- VIEW CARDS (PRIVATE MESSAGE) --------------------
async def handle_uno_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tombol 'Lihat Kartu' ditekan di grup."""
    q = update.callback_query
    uid = q.from_user.id
    cid = int(q.data.split("_")[1])

    if cid not in uno_sessions:
        await q.answer("Sesi sudah tidak ada.", show_alert=True)
        return
    s = uno_sessions[cid]
    if uid not in s.get("hands", {}):
        await q.answer("Kamu bukan pemain.", show_alert=True)
        return
    if uid in s.get("eliminated", set()):
        await q.answer("Kamu sudah keluar dari game.", show_alert=True)
        return

    # Cek apakah giliran user
    players = s["players"]
    cur = players[s["turn_idx"] % len(players)]
    if uid != cur:
        await q.answer("Bukan giliran kamu!", show_alert=True)
        return

    await q.answer()

    hand = s["hands"][uid]
    top = s["discard"][-1]
    chosen = s.get("chosen_color")

    # Kirim pesan pribadi dengan daftar kartu
    try:
        # Buat tombol untuk setiap kartu
        buttons = []
        row = []
        for idx, card in enumerate(hand):
            playable = _can_play(card, top, chosen)
            label = _label(card)
            if not playable:
                label = f"❌ {label}"
            row.append(InlineKeyboardButton(label, callback_data=f"unoplay_{cid}_{idx}"))
            if len(row) == 2:  # 2 tombol per baris biar rapi
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        # Tambah tombol aksi
        buttons.append([InlineKeyboardButton("🃏 Ambil Kartu", callback_data=f"unodraw_{cid}")])
        buttons.append([InlineKeyboardButton("ℹ️ Info Permainan", callback_data=f"unoinfo_{cid}")])

        await context.bot.send_message(
            uid,
            f"🃏 <b>KARTU MILIKMU</b> ({len(hand)} kartu)\n"
            f"🎴 Kartu teratas: {_label(top)}\n\n"
            f"Klik kartu untuk memainkannya. Kartu yang ❌ tidak bisa dimainkan.",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
        )
    except Exception as e:
        await context.bot.send_message(
            cid,
            f"⚠️ Tidak bisa mengirim pesan pribadi ke {await get_nama(s['objs'][uid])}. "
            f"Pastikan kamu sudah pernah chat dengan bot.",
            parse_mode="HTML"
        )

async def handle_uno_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tombol info di pesan pribadi."""
    q = update.callback_query
    uid = q.from_user.id
    cid = int(q.data.split("_")[1])

    if cid not in uno_sessions:
        await q.answer("Sesi sudah tidak ada.", show_alert=True)
        return
    s = uno_sessions[cid]
    if uid not in s.get("hands", {}):
        await q.answer("Kamu bukan pemain.", show_alert=True)
        return

    players = s["players"]
    cur = players[s["turn_idx"] % len(players)]
    cur_obj = s["objs"][cur]
    top = s["discard"][-1]
    chosen = s.get("chosen_color")

    active = [p for p in players if p not in s.get("finish_order", []) and p not in s.get("eliminated", set())]
    info = f"🎲 Giliran: {await get_nama(cur_obj)}\n"
    info += f"🎴 Kartu teratas: {_label(top)}"
    if chosen:
        info += f" (warna {COLOR_LABEL.get(chosen, chosen)})"
    info += "\n\n👥 Pemain:\n"
    for p in active:
        pname = await get_nama(s["objs"][p])
        info += f"• {pname} ({len(s['hands'][p])} kartu)\n"

    await q.edit_message_text(info, parse_mode="HTML")

# -------------------- PLAY CARD (via private message callback) --------------------
async def handle_uno_play_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    data = q.data

    if data.startswith("unoplay_"):
        _, cid_s, idx_s = data.split("_")
        await _action_play(uid, int(cid_s), int(idx_s), q, context)
    elif data.startswith("unodraw_"):
        cid = int(data.split("_")[1])
        await _action_draw(uid, cid, q, context)
    elif data.startswith("unocolor_"):
        _, cid_s, color = data.split("_")
        await _action_color(uid, int(cid_s), color, q, context)
    elif data.startswith("unopass_"):
        cid = int(data.split("_")[1])
        await _action_pass(uid, cid, q, context)
    elif data.startswith("unoinfo_"):
        await handle_uno_info_callback(update, context)

async def _action_play(uid, cid, idx, q, context):
    await q.answer()
    if cid not in uno_sessions:
        await q.edit_message_text("⚠️ sesi sudah tidak ada."); return
    s = uno_sessions[cid]
    players = s["players"]
    cur = players[s["turn_idx"] % len(players)]
    if uid != cur:
        await q.answer("bukan giliran kamu!", show_alert=True); return
    hand = s["hands"].get(uid, [])
    if idx >= len(hand):
        await q.answer("kartu tidak valid!", show_alert=True); return
    card = hand[idx]
    top = s["discard"][-1]
    if not _can_play(card, top, s.get("chosen_color")):
        await q.answer("kartu ini tidak bisa dimainkan!", show_alert=True); return

    hand.pop(idx)
    s["discard"].append(card)
    s["chosen_color"] = None
    nama = await get_nama(s["objs"][uid])

    await q.edit_message_text(f"✅ Kamu memainkan: {_label(card)}", parse_mode="HTML")

    await context.bot.send_message(cid,
        f"🃏 <b>{nama}</b> memainkan: <b>{_label(card)}</b> ({len(hand)} kartu tersisa)",
        parse_mode="HTML"
    )
    if len(hand) == 1:
        await context.bot.send_message(cid, f"⚠️ <b>UNO!</b> {nama} tinggal 1 kartu!", parse_mode="HTML")
    if len(hand) == 0:
        await _player_done(uid, cid, s, context); return

    await _apply_effect(card, uid, cid, s, context)

async def _apply_effect(card, uid, cid, s, context):
    c, v = card
    players = s["players"]
    n = len(players)
    d = s["dir"]
    nxt = lambda: players[(s["turn_idx"] + d) % n]

    if v == "reverse":
        s["dir"] *= -1
        d = s["dir"]
        if n == 2:
            s["turn_idx"] = (s["turn_idx"] + d * 2) % n
        else:
            s["turn_idx"] = (s["turn_idx"] + d) % n
        await context.bot.send_message(cid, "🔄 arah dibalik!")

    elif v == "skip":
        skipped = nxt()
        s_name = await get_nama(s["objs"][skipped])
        s["turn_idx"] = (s["turn_idx"] + d * 2) % n
        await context.bot.send_message(cid, f"🚫 giliran <b>{s_name}</b> di-skip!", parse_mode="HTML")

    elif v == "draw":
        next_uid = nxt()
        drawn = _draw_cards(s, 2)
        s["hands"][next_uid].extend(drawn)
        nn = await get_nama(s["objs"][next_uid])
        await context.bot.send_message(cid, f"➕ <b>{nn}</b> ambil 2 kartu dan skip!", parse_mode="HTML")
        s["turn_idx"] = (s["turn_idx"] + d * 2) % n

    elif v == "colorchooser":
        await _ask_color(uid, cid, s, context); return

    elif v == "draw_four":
        next_uid = nxt()
        drawn = _draw_cards(s, 4)
        s["hands"][next_uid].extend(drawn)
        nn = await get_nama(s["objs"][next_uid])
        await context.bot.send_message(cid, f"➕ <b>{nn}</b> ambil 4 kartu dan skip!", parse_mode="HTML")
        s["turn_idx"] = (s["turn_idx"] + d) % n
        await _ask_color(uid, cid, s, context); return

    else:
        s["turn_idx"] = (s["turn_idx"] + d) % n

    _skip_done_players(s)
    await _send_turn(cid, s, context)

async def _ask_color(uid, cid, s, context):
    s["color_pending"] = True
    s["color_pending_uid"] = uid
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔴 Merah", callback_data=f"unocolor_{cid}_r"),
         InlineKeyboardButton("🟡 Kuning", callback_data=f"unocolor_{cid}_y")],
        [InlineKeyboardButton("🟢 Hijau", callback_data=f"unocolor_{cid}_g"),
         InlineKeyboardButton("🔵 Biru", callback_data=f"unocolor_{cid}_b")],
    ])
    nama = await get_nama(s["objs"][uid])
    await context.bot.send_message(cid,
        f"🌈 <b>{nama}</b>, pilih warna:", reply_markup=kb, parse_mode="HTML"
    )

async def _action_color(uid, cid, color, q, context):
    await q.answer()
    if cid not in uno_sessions:
        await q.edit_message_text("⚠️ sesi sudah tidak ada."); return
    s = uno_sessions[cid]
    if s.get("color_pending_uid") and s["color_pending_uid"] != uid:
        await q.answer("bukan kamu yang memilih warna!", show_alert=True); return
    s["chosen_color"] = color
    s["color_pending"] = False
    s["color_pending_uid"] = None
    label = {"r":"Merah 🔴","g":"Hijau 🟢","b":"Biru 🔵","y":"Kuning 🟡"}.get(color, color)
    await q.edit_message_text(f"🌈 warna dipilih: <b>{label}</b>", parse_mode="HTML")
    s["turn_idx"] = (s["turn_idx"] + s["dir"]) % len(s["players"])
    _skip_done_players(s)
    await _send_turn(cid, s, context)

async def _action_draw(uid, cid, q, context):
    await q.answer()
    if cid not in uno_sessions:
        await q.edit_message_text("⚠️ sesi sudah tidak ada."); return
    s = uno_sessions[cid]
    players = s["players"]
    cur = players[s["turn_idx"] % len(players)]
    if uid != cur:
        await q.answer("bukan giliran kamu!", show_alert=True); return
    drawn = _draw_cards(s, 1)
    nama = await get_nama(s["objs"][uid])
    if not drawn:
        await q.edit_message_text("🃏 Deck kosong, tidak bisa ambil kartu.")
        await context.bot.send_message(cid, f"🃏 <b>{nama}</b> tidak bisa ambil kartu (deck kosong)", parse_mode="HTML")
        await _advance(cid, s, context); return

    card = drawn[0]
    s["hands"][uid].extend(drawn)
    await q.edit_message_text(f"🃏 Kamu ambil 1 kartu. ({len(s['hands'][uid])} kartu)")
    await context.bot.send_message(cid, f"🃏 <b>{nama}</b> ambil 1 kartu", parse_mode="HTML")

    top = s["discard"][-1]
    if _can_play(card, top, s.get("chosen_color")):
        # Kirim pesan baru dengan pilihan mainkan/pass
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶ Mainkan kartu yang diambil", callback_data=f"unoplay_{cid}_{len(s['hands'][uid])-1}")],
            [InlineKeyboardButton("⏭ Pass", callback_data=f"unopass_{cid}")],
        ])
        await context.bot.send_message(uid,
            f"Kartu yang kamu ambil: {_label(card)}\nKartu ini bisa dimainkan!",
            reply_markup=kb, parse_mode="HTML"
        )
    else:
        await _advance(cid, s, context)

async def _action_pass(uid, cid, q, context):
    await q.answer()
    if cid not in uno_sessions: return
    s = uno_sessions[cid]
    players = s["players"]
    cur = players[s["turn_idx"] % len(players)]
    if uid != cur:
        await q.answer("bukan giliran kamu!", show_alert=True); return
    await q.edit_message_text("⏭ Kamu pass.")
    nama = await get_nama(s["objs"][uid])
    await context.bot.send_message(cid, f"⏭ <b>{nama}</b> pass.", parse_mode="HTML")
    await _advance(cid, s, context)

async def _advance(cid, s, context):
    s["turn_idx"] = (s["turn_idx"] + s["dir"]) % len(s["players"])
    _skip_done_players(s)
    await _send_turn(cid, s, context)

async def _player_done(uid, cid, s, context):
    if uid in s["finish_order"]: return
    s["finish_order"].append(uid)
    nama = await get_nama(s["objs"][uid])
    rank = len(s["finish_order"])
    await context.bot.send_message(cid, f"🎉 <b>{nama}</b> habis kartu! (#{rank})", parse_mode="HTML")

    remaining = [u for u in s["players"]
                 if u not in s["finish_order"] and u not in s.get("eliminated", set())]
    if len(remaining) <= 1:
        if remaining: s["finish_order"].append(remaining[0])
        await _end_game(cid, s, context); return

    s["turn_idx"] = (s["turn_idx"] + s["dir"]) % len(s["players"])
    _skip_done_players(s)
    await _send_turn(cid, s, context)

async def _end_game(cid, s, context):
    order = list(s["finish_order"])
    objs = s["objs"]
    bet = s["bet"]
    n = len(s["players"])

    for uid in s["players"]:
        if uid not in order and uid not in s.get("eliminated", set()):
            order.append(uid)
    for uid in s.get("eliminated", set()):
        if uid not in order:
            order.append(uid)

    winner = order[0]
    winnings = s["pot"]
    w = await db_get_wallet(winner)
    await db_set_wallet(winner, get_raw_name(objs[winner]), (w["saldo"] if w else SLOT_INITIAL) + winnings)

    for rank, uid in enumerate(order, 1):
        await add_score(cid, objs[uid], 500 if rank == 1 else 100)

    lines = []
    for rank, uid in enumerate(order, 1):
        nama = await get_nama(objs[uid])
        medal = {1:"🥇",2:"🥈",3:"🥉"}.get(rank, f"#{rank}")
        if rank == 1:
            extra = f" +{format_rupiah(winnings)} saldo, +500 poin"
        elif uid in s.get("eliminated", set()):
            extra = " (keluar) +100 poin"
        else:
            extra = " +100 poin"
        lines.append(f"{medal} {nama}{extra}")

    w2 = await db_get_wallet(winner)
    winner_nama = await get_nama(objs[winner])
    await context.bot.send_message(cid,
        f"🏆 <b>GAME UNO TARUHAN SELESAI!</b>\n\n"
        f"💰 Taruhan: {format_rupiah(bet)}/orang | Pot: {format_rupiah(s['pot'])}\n\n"
        + "\n".join(lines) +
        f"\n\n💳 saldo {winner_nama}: {format_rupiah(w2['saldo'] if w2 else 0)}",
        parse_mode="HTML"
    )
    del uno_sessions[cid]

# -------------------- OBSOLETE (dibersihkan) --------------------
# Fungsi inline query dan sticker tidak digunakan lagi.
async def handle_uno_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Tidak digunakan, biarkan kosong agar tidak error.
    pass

async def handle_uno_sticker_in_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Tidak digunakan.
    pass

async def proses_uno_inline_draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Tidak digunakan.
    pass
