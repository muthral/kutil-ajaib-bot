import random
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InlineQueryResultCachedSticker, InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import ContextTypes

from data import add_score, get_nama, get_raw_name, init_wallet, format_rupiah, SLOT_INITIAL
from db import db_get_wallet, db_set_wallet

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

STICKER_TO_CARD = {}
for _key, _fid in STICKERS.items():
    if _key == "draw_four":
        STICKER_TO_CARD[_fid] = ("x", "draw_four")
    elif _key == "colorchooser":
        STICKER_TO_CARD[_fid] = ("x", "colorchooser")
    else:
        _c, _v = _key.split("_", 1)
        STICKER_TO_CARD[_fid] = (_c, _v)

COLORS = ["r", "g", "b", "y"]
COLOR_LABEL = {"r": "🔴Merah", "g": "🟢Hijau", "b": "🔵Biru", "y": "🟡Kuning"}
COLOR_FULL = {"r": "red", "g": "green", "b": "blue", "y": "yellow"}
COLOR_EMOJI_INFO = {"r": "❤️", "g": "💚", "b": "💙", "y": "💛"}

DRAW_INLINE_TEXT = "🃏 Mengambil kartu..."

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

def _label_info(card, chosen_color=None):
    c, v = card
    name_map = {
        "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
        "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
        "draw": "Draw Two", "skip": "Skip", "reverse": "Reverse",
        "colorchooser": "Color Chooser", "draw_four": "Draw Four",
    }
    name = name_map.get(v, v)
    if c == "x":
        chosen_emoji = COLOR_EMOJI_INFO.get(chosen_color, "") if chosen_color else ""
        return f"{chosen_emoji}⬛️{name}"
    return f"{COLOR_EMOJI_INFO.get(c, '')}{name}"

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

uno_sessions = {}

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
        f"gunakan tombol <b>Lihat Kartu</b> untuk melihat & memainkan kartu.",
        parse_mode="HTML"
    )

    stk = _sticker(top)
    if stk:
        await context.bot.send_sticker(cid, stk)
    await context.bot.send_message(cid, f"🎴 kartu awal: <b>{_label(top)}</b>", parse_mode="HTML")
    await _send_turn(cid, s, context)

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
        [InlineKeyboardButton("🃏 Lihat Kartu", switch_inline_query_current_chat="")]
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

async def handle_uno_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    uid = query.from_user.id

    cid = None
    for c, sess in uno_sessions.items():
        if uid in sess.get("hands", {}) and uid not in sess.get("eliminated", set()):
            cid = c
            break

    if cid is None:
        await query.answer([], cache_time=0, is_personal=True)
        return

    s = uno_sessions[cid]
    hand = s["hands"].get(uid, [])
    top = s["discard"][-1]
    chosen = s.get("chosen_color")
    current_uid = s["players"][s["turn_idx"] % len(s["players"])]

    results = []

    results.append(InlineQueryResultArticle(
        id="draw",
        title="🃏 Ambil Kartu",
        description="Ambil 1 kartu dari deck",
        input_message_content=InputTextMessageContent(message_text=DRAW_INLINE_TEXT),
    ))

    active_players = [p for p in s["players"]
                      if p not in s.get("finish_order", []) and p not in s.get("eliminated", set())]
    player_info_parts = []
    for p in active_players:
        pobj = s["objs"][p]
        pname = pobj.first_name
        pcards = len(s["hands"].get(p, []))
        player_info_parts.append(f"{pname} ({pcards} cards)")

    cur_obj = s["objs"][current_uid]
    cur_display = cur_obj.first_name
    cur_username = f"(@{cur_obj.username})" if cur_obj.username else ""

    info_text = (
        f"Current player: {cur_display} {cur_username}\n"
        f"Last card: {_label_info(top, chosen)}\n"
        f"Players: {' -> '.join(player_info_parts)}"
    )

    results.append(InlineQueryResultArticle(
        id="info",
        title="❓ Info Permainan",
        description=f"Giliran: {cur_display}",
        input_message_content=InputTextMessageContent(message_text=info_text),
    ))

    for i, card in enumerate(hand):
        stk = _sticker(card)
        if stk:
            can = _can_play(card, top, chosen)
            results.append(InlineQueryResultCachedSticker(
                id=f"card_{i}",
                sticker_file_id=stk,
            ))

    try:
        await query.answer(results, cache_time=0, is_personal=True)
    except Exception:
        pass

async def handle_uno_sticker_in_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.sticker:
        return
    if not msg.via_bot:
        return
    if msg.via_bot.id != context.bot.id:
        return
    if msg.chat.type == "private":
        return

    cid = msg.chat_id
    uid = msg.from_user.id

    if cid not in uno_sessions:
        return
    s = uno_sessions[cid]
    if uid not in s.get("hands", {}):
        return
    if uid in s.get("eliminated", set()):
        return

    fid = msg.sticker.file_id
    card = STICKER_TO_CARD.get(fid)
    if not card:
        return

    players = s["players"]
    cur = players[s["turn_idx"] % len(players)]
    if uid != cur:
        await msg.reply_text("⚠️ bukan giliran kamu!")
        return

    if s.get("color_pending"):
        await msg.reply_text("⚠️ pilih warna dulu!")
        return

    hand = s["hands"][uid]
    card_idx = None
    for i, h in enumerate(hand):
        if h == card:
            card_idx = i
            break
    if card_idx is None:
        await msg.reply_text("⚠️ kamu tidak punya kartu ini!")
        return

    top = s["discard"][-1]
    if not _can_play(card, top, s.get("chosen_color")):
        await msg.reply_text("⚠️ kartu ini tidak bisa dimainkan!")
        return

    hand.pop(card_idx)
    s["discard"].append(card)
    s["chosen_color"] = None
    nama = await get_nama(s["objs"][uid])

    await context.bot.send_message(cid,
        f"🃏 <b>{nama}</b> memainkan: <b>{_label(card)}</b> ({len(hand)} kartu tersisa)",
        parse_mode="HTML"
    )
    if len(hand) == 1:
        await context.bot.send_message(cid, f"⚠️ <b>UNO!</b> {nama} tinggal 1 kartu!", parse_mode="HTML")
    if len(hand) == 0:
        await _player_done(uid, cid, s, context)
        return

    await _apply_effect(card, uid, cid, s, context)

async def proses_uno_inline_draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.via_bot:
        return
    if msg.via_bot.id != context.bot.id:
        return
    if msg.chat.type == "private":
        return
    if msg.text != DRAW_INLINE_TEXT:
        return

    cid = msg.chat_id
    uid = msg.from_user.id

    if cid not in uno_sessions:
        return
    s = uno_sessions[cid]
    if uid not in s.get("hands", {}):
        return
    if uid in s.get("eliminated", set()):
        return

    players = s["players"]
    cur = players[s["turn_idx"] % len(players)]
    if uid != cur:
        await msg.reply_text("⚠️ bukan giliran kamu!")
        return

    if s.get("color_pending"):
        await msg.reply_text("⚠️ pilih warna dulu!")
        return

    drawn = _draw_cards(s, 1)
    nama = await get_nama(s["objs"][uid])
    if not drawn:
        await context.bot.send_message(cid,
            f"🃏 <b>{nama}</b> tidak bisa ambil kartu (deck kosong)", parse_mode="HTML")
        await _advance(cid, s, context)
        return

    card = drawn[0]
    s["hands"][uid].extend(drawn)
    await context.bot.send_message(cid,
        f"🃏 <b>{nama}</b> ambil 1 kartu ({len(s['hands'][uid])} kartu)", parse_mode="HTML")

    top = s["discard"][-1]
    if _can_play(card, top, s.get("chosen_color")):
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶ Mainkan", callback_data=f"unoplay_{cid}_{len(s['hands'][uid])-1}")],
            [InlineKeyboardButton("⏭ Pass", callback_data=f"unopass_{cid}")],
        ])
        await context.bot.send_message(cid,
            f"kartu yang diambil <b>{nama}</b> bisa dimainkan!",
            reply_markup=kb, parse_mode="HTML"
        )
    else:
        await _advance(cid, s, context)

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
    done = set(s.get("finish_order", []))
    done.update(s.get("eliminated", set()))
    visited = 0
    while visited < n:
        uid = players[s["turn_idx"] % n]
        if uid not in done:
            break
        s["turn_idx"] = (s["turn_idx"] + s["dir"]) % n
        visited += 1

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
            [InlineKeyboardButton("▶ Mainkan", callback_data=f"unoplay_{cid}_{len(s['hands'][uid])-1}")],
            [InlineKeyboardButton("⏭ Pass", callback_data=f"unopass_{cid}")],
        ])
        await context.bot.send_message(cid,
            f"kartu yang diambil <b>{nama}</b> bisa dimainkan!",
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
