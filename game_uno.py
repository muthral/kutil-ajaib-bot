import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from data import add_score, get_nama, get_raw_name, init_wallet, format_rupiah, SLOT_INITIAL
from db import db_get_wallet, db_set_wallet

# ============================================================
# STICKER IDs (Classic mode, from kierankihn/telegram-uno-bot)
# ============================================================
STICKERS = {
    "b_0": "BQADBAAD2QEAAl9XmQAB--inQsYcLTsC", "b_1": "BQADBAAD2wEAAl9XmQABBzh4U-rFicEC",
    "b_2": "BQADBAAD3QEAAl9XmQABo3l6TT0MzKwC", "b_3": "BQADBAAD3wEAAl9XmQAB2y-3TSapRtIC",
    "b_4": "BQADBAAD4QEAAl9XmQABT6nhOuolqKYC", "b_5": "BQADBAAD4wEAAl9XmQABwRfmekGnpn0C",
    "b_6": "BQADBAAD5QEAAl9XmQABQITgUsEsqxsC", "b_7": "BQADBAAD5wEAAl9XmQABVhPF6EcfWjEC",
    "b_8": "BQADBAAD6QEAAl9XmQABP6baig0pIvYC", "b_9": "BQADBAAD6wEAAl9XmQAB0CQdsQs_pXIC",
    "b_draw": "BQADBAAD7QEAAl9XmQAB00Wii7R3gDUC", "b_skip": "BQADBAAD8QEAAl9XmQAB_RJHYKqlc-wC",
    "b_reverse": "BQADBAAD7wEAAl9XmQABo7D0B9NUPmYC",
    "g_0": "BQADBAAD9wEAAl9XmQABb8CaxxsQ-Y8C", "g_1": "BQADBAAD-QEAAl9XmQAB9B6ti_j6UB0C",
    "g_2": "BQADBAAD-wEAAl9XmQABYpLjOzbRz8EC", "g_3": "BQADBAAD_QEAAl9XmQABKvc2ZCiY-D8C",
    "g_4": "BQADBAAD_wEAAl9XmQABJB52wzPdHssC", "g_5": "BQADBAADAQIAAl9XmQABp_Ep1I4GA2cC",
    "g_6": "BQADBAADAwIAAl9XmQABaaMxxa4MihwC", "g_7": "BQADBAADBQIAAl9XmQABv5Q264Crz8gC",
    "g_8": "BQADBAADBwIAAl9XmQABjMH-X9UHh8sC", "g_9": "BQADBAADCQIAAl9XmQAB26fZ2fW7vM0C",
    "g_draw": "BQADBAADCwIAAl9XmQAB64jIZrgXrQUC", "g_skip": "BQADBAADDwIAAl9XmQAB17yhhnh46VQC",
    "g_reverse": "BQADBAADDQIAAl9XmQAB_xcaab0DkegC",
    "r_0": "BQADBAADEQIAAl9XmQABiUfr1hz-zT8C", "r_1": "BQADBAADEwIAAl9XmQAB5bWfwJGs6Q0C",
    "r_2": "BQADBAADFQIAAl9XmQABHR4mg9Ifjw0C", "r_3": "BQADBAADFwIAAl9XmQABYBx5O_PG2QIC",
    "r_4": "BQADBAADGQIAAl9XmQABTQpGrlvet3cC", "r_5": "BQADBAADGwIAAl9XmQABbdLt4gdntBQC",
    "r_6": "BQADBAADHQIAAl9XmQABqEI274p3lSoC", "r_7": "BQADBAADHwIAAl9XmQABCw8u67Q4EK4C",
    "r_8": "BQADBAADIQIAAl9XmQAB8iDJmLxp8ogC", "r_9": "BQADBAADIwIAAl9XmQAB_HCAww1kNGYC",
    "r_draw": "BQADBAADJQIAAl9XmQABuz0OZ4l3k6MC", "r_skip": "BQADBAADKQIAAl9XmQAC2AL5Ok_ULwI",
    "r_reverse": "BQADBAADJwIAAl9XmQABu2tIeQTpDvUC",
    "y_0": "BQADBAADKwIAAl9XmQAB_nWoNKe8DOQC", "y_1": "BQADBAADLQIAAl9XmQABVprAGUDKgOQC",
    "y_2": "BQADBAADLwIAAl9XmQABqyT4_YTm54EC", "y_3": "BQADBAADMQIAAl9XmQABGC-Xxg_N6fIC",
    "y_4": "BQADBAADMwIAAl9XmQABbc-ZGL8kApAC", "y_5": "BQADBAADNQIAAl9XmQAB67QJZIF6XAcC",
    "y_6": "BQADBAADNwIAAl9XmQABJg_7XXoITsoC", "y_7": "BQADBAADOQIAAl9XmQABVrd7OcS2k34C",
    "y_8": "BQADBAADOwIAAl9XmQABRpJSahBWk3EC", "y_9": "BQADBAADPQIAAl9XmQAB9MwJWKLJogYC",
    "y_draw": "BQADBAADPwIAAl9XmQABaPYK8oYg84cC", "y_skip": "BQADBAADQwIAAl9XmQABO_AZKtxY6IMC",
    "y_reverse": "BQADBAADQQIAAl9XmQABZdQFahGG6UQC",
    "draw_four": "BQADBAAD9QEAAl9XmQABVlkSNfhn76cC",
    "colorchooser": "BQADBAAD8wEAAl9XmQABl9rUOPqx4E4C",
}

# ============================================================
# CARD HELPERS
# ============================================================
COLORS = ["r", "g", "b", "y"]
COLOR_LABEL = {"r": "🔴Merah", "g": "🟢Hijau", "b": "🔵Biru", "y": "🟡Kuning"}
COLOR_FULL = {"r": "red", "g": "green", "b": "blue", "y": "yellow"}

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

def _sticker(card, playable=True):
    c, v = card
    if v in ("colorchooser", "draw_four"):
        return STICKERS.get(v)
    key = f"{c}_{v}"
    return STICKERS.get(key)

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

def _playable(hand, top, chosen_color=None):
    return [i for i, card in enumerate(hand) if _can_play(card, top, chosen_color)]

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

# ============================================================
# SESSION STORAGE
# ============================================================
uno_sessions = {}
uno_dm_pending = {}

# ============================================================
# COMMANDS: /unotaruhan /joinuno /startuno /stopuno
# ============================================================

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
    await update.message.reply_text(
        "💰 bot akan DM setiap pemain untuk memilih taruhan.\n"
        "<b>semua pemain harus memilih jumlah yang sama!</b>",
        parse_mode="HTML"
    )
    for uid in s["players"]:
        uobj = s["objs"][uid]
        nama = await get_nama(uobj)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Rp 500.000", callback_data=f"unobet_{cid}_500000"),
             InlineKeyboardButton("Rp 1.000.000", callback_data=f"unobet_{cid}_1000000")],
            [InlineKeyboardButton("Rp 2.000.000", callback_data=f"unobet_{cid}_2000000"),
             InlineKeyboardButton("Rp 3.000.000", callback_data=f"unobet_{cid}_3000000")],
            [InlineKeyboardButton("Rp 7.000.000", callback_data=f"unobet_{cid}_7000000")],
            [InlineKeyboardButton("✏️ Masukkan angka sendiri", callback_data=f"unobet_{cid}_custom")],
        ])
        try:
            await context.bot.send_message(
                uid,
                f"🃏 <b>UNO TARUHAN</b> — halo {nama}!\n\npilih jumlah taruhan:\n"
                "<i>semua pemain harus pilih jumlah yang sama!</i>",
                reply_markup=kb, parse_mode="HTML"
            )
            uno_dm_pending[uid] = {"cid": cid, "stage": "bet"}
        except Exception:
            await context.bot.send_message(cid, f"⚠️ tidak bisa DM {nama}! pastikan sudah chat bot dulu.")

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
        await update.message.reply_text(f"game UNO dihentikan. taruhan {format_rupiah(s['bet'])} dikembalikan.")
    else:
        await update.message.reply_text("game UNO dihentikan.")
    for uid in list(uno_dm_pending):
        if uno_dm_pending[uid].get("cid") == cid:
            del uno_dm_pending[uid]
    del uno_sessions[cid]

# ============================================================
# CALLBACK: TARUHAN
# ============================================================

async def handle_uno_bet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    _, cid_str, val = q.data.split("_", 2)
    cid = int(cid_str)

    if uid not in uno_dm_pending or uno_dm_pending[uid].get("cid") != cid:
        await q.edit_message_text("⚠️ sesi tidak ditemukan."); return
    if cid not in uno_sessions:
        uno_dm_pending.pop(uid, None)
        await q.edit_message_text("⚠️ sesi UNO sudah tidak ada."); return

    if val == "custom":
        uno_dm_pending[uid]["stage"] = "bet_custom"
        await q.edit_message_text(
            "✏️ ketik jumlah taruhan (angka saja, contoh: <code>500000</code>)\n"
            "<i>semua pemain harus sama!</i>", parse_mode="HTML"
        )
        return

    await _record_bet(uid, q.from_user, cid, int(val), context, q)

async def _record_bet(uid, user, cid, amount, context, q=None):
    if cid not in uno_sessions:
        uno_dm_pending.pop(uid, None)
        if q: await q.edit_message_text("⚠️ sesi UNO sudah tidak ada.")
        return
    s = uno_sessions[cid]
    s["bets"][uid] = amount
    s["bets_received"].add(uid)
    uno_dm_pending.pop(uid, None)
    msg = f"✅ taruhan <b>{format_rupiah(amount)}</b> tersimpan! menunggu pemain lain..."
    if q:
        await q.edit_message_text(msg, parse_mode="HTML")
    else:
        await context.bot.send_message(uid, msg, parse_mode="HTML")
    if len(s["bets_received"]) == len(s["players"]):
        await _validate_and_start(cid, context)

async def _validate_and_start(cid, context):
    s = uno_sessions[cid]
    bets = [s["bets"][u] for u in s["players"]]
    objs = s["objs"]

    # Cek semua taruhan sama
    if len(set(bets)) > 1:
        detail = "\n".join([f"• {await get_nama(objs[u])}: {format_rupiah(s['bets'][u])}" for u in s["players"]])
        del uno_sessions[cid]
        await context.bot.send_message(cid,
            f"❌ <b>TARUHAN TIDAK SAMA!</b>\n\n{detail}\n\ngame dibatalkan. coba lagi dengan /unotaruhan",
            parse_mode="HTML"); return

    bet = bets[0]
    pot = bet * len(s["players"])

    # Cek saldo
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

    # Potong saldo
    for uid in s["players"]:
        w = await db_get_wallet(uid)
        await db_set_wallet(uid, get_raw_name(objs[uid]), (w["saldo"] if w else SLOT_INITIAL) - bet)

    s["bet"] = bet
    s["pot"] = pot

    # Deal kartu
    deck = _new_deck()
    hands = {uid: [] for uid in s["players"]}
    for _ in range(7):
        for uid in s["players"]:
            if deck: hands[uid].append(deck.pop())

    # Kartu pertama (bukan wild)
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
        f"7 kartu sudah dibagikan!",
        parse_mode="HTML"
    )

    # Kirim sticker kartu pertama
    stk = _sticker(top)
    if stk:
        await context.bot.send_sticker(cid, stk)
    await context.bot.send_message(cid, f"🎴 kartu awal: <b>{_label(top)}</b>", parse_mode="HTML")
    await _send_turn(cid, s, context)

# ============================================================
# TURN MANAGEMENT
# ============================================================

async def _send_turn(cid, s, context):
    players = s["players"]
    if not players: return
    uid = players[s["turn_idx"] % len(players)]
    uobj = s["objs"][uid]
    nama = await get_nama(uobj)
    hand = s["hands"].get(uid, [])
    top = s["discard"][-1]
    chosen = s.get("chosen_color")
    playable_idx = _playable(hand, top, chosen)

    # Buat tombol kartu yang bisa dimainkan
    rows = []
    for i in playable_idx:
        rows.append([InlineKeyboardButton(f"▶ {_label(hand[i])}", callback_data=f"unoplay_{cid}_{i}")])
    rows.append([InlineKeyboardButton("🃏 Ambil kartu", callback_data=f"unodraw_{cid}")])

    hand_txt = " | ".join([_label(c) for c in hand]) if hand else "(kosong)"
    color_hint = f" (warna: {COLOR_LABEL.get(chosen,'?')})" if chosen and top[0]=="x" else ""

    msg = await context.bot.send_message(
        cid,
        f"🎲 giliran: <b>{nama}</b> ({len(hand)} kartu)\n"
        f"🎴 Kartu teratas: <b>{_label(top)}</b>{color_hint}\n\n"
        f"<i>kartu {nama}:</i> {hand_txt}",
        reply_markup=InlineKeyboardMarkup(rows),
        parse_mode="HTML"
    )
    s["turn_msg_id"] = msg.message_id

# ============================================================
# CALLBACK: PLAY / DRAW / COLOR / PASS
# ============================================================

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

    await q.edit_message_reply_markup(None)

    # Kirim sticker kartu yang dimainkan
    stk = _sticker(card)
    if stk:
        try: await context.bot.send_sticker(cid, stk)
        except Exception: pass

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

def _skip_done_players(s):
    players = s["players"]
    n = len(players)
    if n <= 1: return
    visited = 0
    while visited < n:
        uid = players[s["turn_idx"] % n]
        if uid not in s.get("finish_order", []):
            break
        s["turn_idx"] = (s["turn_idx"] + s["dir"]) % n
        visited += 1

async def _ask_color(uid, cid, s, context):
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
    s["chosen_color"] = color
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
        await q.edit_message_reply_markup(None)
        await context.bot.send_message(cid, f"🃏 <b>{nama}</b> tidak bisa ambil kartu (deck kosong)", parse_mode="HTML")
        await _advance(cid, s, context); return

    card = drawn[0]
    s["hands"][uid].extend(drawn)
    await q.edit_message_reply_markup(None)
    await context.bot.send_message(cid, f"🃏 <b>{nama}</b> ambil 1 kartu", parse_mode="HTML")

    top = s["discard"][-1]
    if _can_play(card, top, s.get("chosen_color")):
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"▶ Mainkan {_label(card)}", callback_data=f"unoplay_{cid}_{len(s['hands'][uid])-1}")],
            [InlineKeyboardButton("⏭ Pass", callback_data=f"unopass_{cid}")],
        ])
        await context.bot.send_message(cid,
            f"kartu yang diambil <b>{nama}</b> bisa dimainkan!\n<b>{_label(card)}</b>\nmainkan atau pass?",
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
    await q.edit_message_reply_markup(None)
    nama = await get_nama(s["objs"][uid])
    await context.bot.send_message(cid, f"⏭ <b>{nama}</b> pass.", parse_mode="HTML")
    await _advance(cid, s, context)

async def _advance(cid, s, context):
    s["turn_idx"] = (s["turn_idx"] + s["dir"]) % len(s["players"])
    _skip_done_players(s)
    top = s["discard"][-1]
    stk = _sticker(top)
    if stk:
        try: await context.bot.send_sticker(cid, stk)
        except Exception: pass
    await _send_turn(cid, s, context)

# ============================================================
# PLAYER DONE / GAME OVER
# ============================================================

async def _player_done(uid, cid, s, context):
    if uid in s["finish_order"]: return
    s["finish_order"].append(uid)
    nama = await get_nama(s["objs"][uid])
    rank = len(s["finish_order"])
    await context.bot.send_message(cid, f"🎉 <b>{nama}</b> habis kartu! (#{rank})", parse_mode="HTML")

    remaining = [u for u in s["players"] if u not in s["finish_order"]]
    if len(remaining) <= 1:
        if remaining: s["finish_order"].append(remaining[0])
        await _end_game(cid, s, context); return

    s["turn_idx"] = (s["turn_idx"] + s["dir"]) % len(s["players"])
    _skip_done_players(s)
    top = s["discard"][-1]
    stk = _sticker(top)
    if stk:
        try: await context.bot.send_sticker(cid, stk)
        except Exception: pass
    await _send_turn(cid, s, context)

async def _end_game(cid, s, context):
    order = s["finish_order"]
    objs = s["objs"]
    bet = s["bet"]
    n = len(s["players"])

    # Lengkapi urutan
    for uid in s["players"]:
        if uid not in order: order.append(uid)

    winner = order[0]
    winnings = bet * (n - 1)
    w = await db_get_wallet(winner)
    await db_set_wallet(winner, get_raw_name(objs[winner]), (w["saldo"] if w else SLOT_INITIAL) + winnings)

    for rank, uid in enumerate(order, 1):
        await add_score(cid, objs[uid], 500 if rank == 1 else 100)

    lines = []
    for rank, uid in enumerate(order, 1):
        nama = await get_nama(objs[uid])
        medal = {1:"🥇",2:"🥈",3:"🥉"}.get(rank, f"#{rank}")
        extra = f" +{format_rupiah(winnings)} saldo, +500 poin" if rank == 1 else " +100 poin"
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

# ============================================================
# DM HANDLER (untuk input angka custom taruhan)
# ============================================================

async def proses_uno_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    if uid not in uno_dm_pending: return
    p = uno_dm_pending[uid]
    if p.get("stage") != "bet_custom": return
    cid = p["cid"]
    text = update.message.text.strip().replace(".", "").replace(",", "")
    if not text.isdigit():
        await update.message.reply_text("tolong masukkan angka saja. contoh: 500000"); return
    amount = int(text)
    if amount <= 0:
        await update.message.reply_text("❌ jumlah harus lebih dari 0!"); return
    await _record_bet(uid, update.message.from_user, cid, amount, context)

