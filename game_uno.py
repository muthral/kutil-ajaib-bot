import random
import asyncio
import io
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from data import (
    add_score, get_nama, get_raw_name,
    init_wallet, format_rupiah, SLOT_INITIAL
)
from db import db_get_wallet, db_set_wallet

# =====================
# SESSIONS STORAGE
# =====================
uno_sessions = {}
uno_dm_pending = {}

# =====================
# CONSTANTS
# =====================
COLORS = ["red", "yellow", "green", "blue"]
COLOR_DISPLAY = {"red": "🔴", "yellow": "🟡", "green": "🟢", "blue": "🔵"}
COLOR_RGB = {
    "red":    (198, 47, 47),
    "yellow": (210, 175, 20),
    "green":  (39, 143, 72),
    "blue":   (35, 99, 180),
    "wild":   (30, 30, 30),
}
NUMBERS = list(range(0, 10))
SPECIAL = ["Skip", "Reverse", "Draw Two"]
WILDS = ["Wild", "Wild Draw Four"]

TARUHAN_PRESET = [500_000, 1_000_000, 2_000_000, 3_000_000, 7_000_000]

# =====================
# DECK CREATION
# =====================

def create_deck():
    deck = []
    for color in COLORS:
        deck.append({"color": color, "value": "0"})
        for val in range(1, 10):
            deck.append({"color": color, "value": str(val)})
            deck.append({"color": color, "value": str(val)})
        for sp in SPECIAL:
            deck.append({"color": color, "value": sp})
            deck.append({"color": color, "value": sp})
    for _ in range(4):
        deck.append({"color": "wild", "value": "Wild"})
        deck.append({"color": "wild", "value": "Wild Draw Four"})
    random.shuffle(deck)
    return deck

def card_label(card):
    if card["color"] == "wild":
        return card["value"]
    return f"{COLOR_DISPLAY[card['color']]} {card['value']}"

def card_label_plain(card):
    if card["color"] == "wild":
        return card["value"]
    return f"{card['color'].upper()} {card['value']}"

# =====================
# CARD IMAGE GENERATOR (Classic Style)
# =====================

def make_card_image(card):
    W, H = 140, 210
    color = card["color"]
    value = card["value"]

    bg_color = COLOR_RGB.get(color, (30, 30, 30))
    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    # Rounded corners via overlay
    inner_color = tuple(max(0, c - 40) for c in bg_color)
    oval_box = (10, 10, W - 10, H - 10)
    draw.rounded_rectangle([0, 0, W - 1, H - 1], radius=18, fill=bg_color)

    # White inner ellipse (classic UNO style)
    draw.ellipse([15, 25, W - 15, H - 25], fill=(255, 255, 255))

    # Text in ellipse
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_corner = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except Exception:
        font_big = ImageFont.load_default()
        font_small = font_big
        font_corner = font_big

    # Center label
    if value in ["Wild", "Wild Draw Four"]:
        # Colored segments
        seg_colors = [(198, 47, 47), (35, 99, 180), (210, 175, 20), (39, 143, 72)]
        seg_box = (20, 30, W - 20, H - 30)
        seg_w = (seg_box[2] - seg_box[0]) // 2
        seg_h = (seg_box[3] - seg_box[1]) // 2
        for i, sc in enumerate(seg_colors):
            sx = seg_box[0] + (i % 2) * seg_w
            sy = seg_box[1] + (i // 2) * seg_h
            draw.rectangle([sx, sy, sx + seg_w, sy + seg_h], fill=sc)
        # Oval clip
        draw.ellipse([20, 30, W - 20, H - 30], fill=None, outline=(255, 255, 255), width=3)

        short = "W" if value == "Wild" else "W+4"
        # Corner
        draw.text((6, 4), short, fill=(255, 255, 255), font=font_corner)
        draw.text((W - 28, H - 24), short, fill=(255, 255, 255), font=font_corner)

        # Center text
        bbox = draw.textbbox((0, 0), short, font=font_big)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(((W - tw) // 2, (H - th) // 2), short, fill=(255, 255, 255), font=font_big)
    else:
        # Number or Special
        if value in ["Skip", "Reverse", "Draw Two"]:
            short = {"Skip": "⊘", "Reverse": "⇌", "Draw Two": "+2"}[value]
        else:
            short = value

        # Center
        bbox = draw.textbbox((0, 0), short, font=font_big)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        cx = (W - tw) // 2
        cy = (H - th) // 2
        draw.text((cx, cy), short, fill=bg_color, font=font_big)

        # Corners
        draw.text((6, 4), short, fill=(255, 255, 255), font=font_corner)
        draw.text((W - 28, H - 24), short, fill=(255, 255, 255), font=font_corner)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def make_hand_image(hand):
    """Combine multiple card images horizontally."""
    cards_imgs = []
    for card in hand:
        buf = make_card_image(card)
        ci = Image.open(buf)
        cards_imgs.append(ci)

    if not cards_imgs:
        img = Image.new("RGB", (140, 210), (50, 50, 50))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf

    W_card, H_card = 140, 210
    overlap = 30
    total_w = W_card + (len(cards_imgs) - 1) * (W_card - overlap)
    img = Image.new("RGB", (total_w, H_card), (30, 30, 30))
    for i, ci in enumerate(cards_imgs):
        img.paste(ci, (i * (W_card - overlap), 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# =====================
# GAME LOGIC HELPERS
# =====================

def can_play(card, top_card, chosen_color=None):
    if card["color"] == "wild":
        return True
    if top_card["color"] == "wild":
        if chosen_color:
            return card["color"] == chosen_color
        return True
    return card["color"] == top_card["color"] or card["value"] == top_card["value"]

def playable_cards(hand, top_card, chosen_color=None):
    return [i for i, c in enumerate(hand) if can_play(c, top_card, chosen_color)]

# =====================
# TARUHAN FLOW
# =====================

async def unotaruhan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in uno_sessions:
        await update.message.reply_text("🃏 sudah ada game UNO taruhan, tunggu selesai dulu atau /stopuno")
        return

    uno_sessions[chat_id] = {
        "players": [],
        "player_objs": {},
        "bets": {},
        "bets_received": set(),
        "hands": {},
        "deck": [],
        "discard": [],
        "direction": 1,
        "current_turn": 0,
        "chosen_color": None,
        "pending_draw": 0,
        "started": False,
        "bet_amount": None,
        "draw_pending_uid": None,
        "finished": False,
        "finish_order": [],
    }

    await update.message.reply_text(
        "🃏 <b>UNO TARUHAN!</b>\n\n"
        "game UNO dengan taruhan saldo!\n\n"
        "ketik /joinuno untuk ikut (minimal 2 pemain, maks 10)\n"
        "setelah semua join, host ketik /startuno",
        parse_mode="HTML"
    )

async def joinuno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user = update.message.from_user

    if chat_id not in uno_sessions:
        await update.message.reply_text("belum ada game UNO. ketik /unotaruhan dulu")
        return

    session = uno_sessions[chat_id]

    if session["started"]:
        await update.message.reply_text("game sudah dimulai, tidak bisa join")
        return

    if user.id in session["player_objs"]:
        await update.message.reply_text("kamu sudah join!")
        return

    if len(session["players"]) >= 10:
        await update.message.reply_text("sudah penuh! maksimal 10 pemain")
        return

    session["players"].append(user.id)
    session["player_objs"][user.id] = user

    nama = await get_nama(user)
    jumlah = len(session["players"])

    player_list = "\n".join([f"• {await get_nama(session['player_objs'][uid])}" for uid in session["players"]])
    await update.message.reply_text(
        f"✅ {nama} join!\n\n"
        f"👥 <b>Pemain ({jumlah}):</b>\n{player_list}\n\n"
        f"{'host ketik /startuno untuk mulai' if jumlah >= 2 else 'menunggu pemain lain...'}",
        parse_mode="HTML"
    )

async def startuno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id not in uno_sessions:
        await update.message.reply_text("belum ada game UNO")
        return

    session = uno_sessions[chat_id]

    if session["started"]:
        await update.message.reply_text("game sudah dimulai")
        return

    if len(session["players"]) < 2:
        await update.message.reply_text("minimal 2 pemain!")
        return

    session["started"] = True

    await update.message.reply_text(
        f"💰 <b>UNO TARUHAN - INPUT TARUHAN</b>\n\n"
        f"bot akan DM setiap pemain untuk memasukkan jumlah taruhan.\n"
        f"<b>semua pemain harus memasukkan jumlah yang sama!</b>\n\n"
        f"⏳ menunggu semua pemain input taruhan...",
        parse_mode="HTML"
    )

    for uid in session["players"]:
        user_obj = session["player_objs"][uid]
        nama = await get_nama(user_obj)
        try:
            keyboard = [
                [
                    InlineKeyboardButton("Rp 500.000", callback_data=f"unobet_{chat_id}_500000"),
                    InlineKeyboardButton("Rp 1.000.000", callback_data=f"unobet_{chat_id}_1000000"),
                ],
                [
                    InlineKeyboardButton("Rp 2.000.000", callback_data=f"unobet_{chat_id}_2000000"),
                    InlineKeyboardButton("Rp 3.000.000", callback_data=f"unobet_{chat_id}_3000000"),
                ],
                [
                    InlineKeyboardButton("Rp 7.000.000", callback_data=f"unobet_{chat_id}_7000000"),
                ],
                [
                    InlineKeyboardButton("✏️ Masukkan angka sendiri", callback_data=f"unobet_{chat_id}_custom"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                uid,
                f"🃏 <b>UNO TARUHAN</b>\n\n"
                f"halo {nama}! 👋\n\n"
                f"pilih jumlah taruhan kamu:\n"
                f"<b>semua pemain harus pilih jumlah yang sama!</b>",
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            uno_dm_pending[uid] = {"chat_id": chat_id, "stage": "bet_choice"}
        except Exception:
            await context.bot.send_message(
                chat_id,
                f"⚠️ bot tidak bisa DM {nama}! pastikan sudah pernah chat dengan bot dulu."
            )

async def handle_uno_bet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    data = query.data

    if not data.startswith("unobet_"):
        return

    parts = data.split("_")
    if len(parts) < 3:
        return

    chat_id = int(parts[1])
    value = parts[2]

    if user_id not in uno_dm_pending:
        await query.edit_message_text("⚠️ sesi tidak ditemukan, mungkin sudah timeout.")
        return

    if chat_id not in uno_sessions:
        uno_dm_pending.pop(user_id, None)
        await query.edit_message_text("⚠️ sesi UNO sudah tidak ada.")
        return

    if uno_dm_pending[user_id].get("stage") != "bet_choice":
        return

    if value == "custom":
        uno_dm_pending[user_id]["stage"] = "bet_custom"
        await query.edit_message_text(
            "✏️ <b>Masukkan jumlah taruhan kamu:</b>\n\n"
            "ketik angka dalam Rupiah.\n"
            "contoh: ketik <code>500000</code> untuk Rp 500.000\n\n"
            "<b>semua pemain harus memasukkan jumlah yang sama!</b>",
            parse_mode="HTML"
        )
        return

    bet_amount = int(value)
    await _process_uno_bet(user_id, user, chat_id, bet_amount, context, query=query)

async def handle_uno_play_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    data = query.data

    if data.startswith("unoplay_"):
        parts = data.split("_")
        chat_id = int(parts[1])
        card_idx = int(parts[2])
        await _play_card_action(user_id, chat_id, card_idx, context, query)

    elif data.startswith("unodraw_"):
        parts = data.split("_")
        chat_id = int(parts[1])
        await _draw_card_action(user_id, chat_id, context, query)

    elif data.startswith("unocolor_"):
        parts = data.split("_")
        chat_id = int(parts[1])
        chosen_color = parts[2]
        await _choose_color_action(user_id, chat_id, chosen_color, context, query)

    elif data.startswith("unopass_"):
        parts = data.split("_")
        chat_id = int(parts[1])
        await _pass_turn_action(user_id, chat_id, context, query)

async def _process_uno_bet(user_id, user, chat_id, bet_amount, context, query=None):
    if chat_id not in uno_sessions:
        if query:
            await query.edit_message_text("⚠️ sesi UNO sudah tidak ada.")
        uno_dm_pending.pop(user_id, None)
        return

    session = uno_sessions[chat_id]
    session["bets"][user_id] = bet_amount
    session["bets_received"].add(user_id)
    uno_dm_pending.pop(user_id, None)

    msg = (
        f"✅ taruhan <b>{format_rupiah(bet_amount)}</b> tersimpan!\n\n"
        f"menunggu pemain lain selesai input..."
    )
    if query:
        await query.edit_message_text(msg, parse_mode="HTML")
    else:
        await context.bot.send_message(user_id, msg, parse_mode="HTML")

    if len(session["bets_received"]) == len(session["players"]):
        await _check_and_start_uno(chat_id, context)

async def _check_and_start_uno(chat_id, context):
    session = uno_sessions[chat_id]
    players = session["players"]
    player_objs = session["player_objs"]
    bets = session["bets"]

    # Check semua taruhan sama
    bet_values = [bets[uid] for uid in players]
    if len(set(bet_values)) > 1:
        bets_detail = "\n".join([
            f"• {await get_nama(player_objs[uid])}: {format_rupiah(bets[uid])}"
            for uid in players
        ])
        del uno_sessions[chat_id]
        await context.bot.send_message(
            chat_id,
            f"❌ <b>TARUHAN TIDAK SAMA!</b>\n\n"
            f"{bets_detail}\n\n"
            f"semua pemain harus memasukkan jumlah yang sama!\n"
            f"game dibatalkan. coba lagi dengan /unotaruhan",
            parse_mode="HTML"
        )
        return

    bet = bet_values[0]
    total_pot = bet * len(players)

    # Cek saldo semua pemain
    errors = []
    for uid in players:
        user_obj = player_objs[uid]
        await init_wallet(user_obj)
        wallet = await db_get_wallet(uid)
        saldo = wallet["saldo"] if wallet else SLOT_INITIAL
        if saldo < bet:
            errors.append(f"{await get_nama(user_obj)} (saldo: {format_rupiah(saldo)})")

    if errors:
        del uno_sessions[chat_id]
        await context.bot.send_message(
            chat_id,
            f"❌ <b>SALDO TIDAK CUKUP!</b>\n\n"
            f"taruhan: {format_rupiah(bet)}\n\n"
            f"saldo kurang:\n" + "\n".join(f"• {e}" for e in errors) + "\n\n"
            f"game dibatalkan. top up dulu ya!",
            parse_mode="HTML"
        )
        return

    # Potong saldo semua pemain
    for uid in players:
        user_obj = player_objs[uid]
        wallet = await db_get_wallet(uid)
        saldo = wallet["saldo"] if wallet else SLOT_INITIAL
        await db_set_wallet(uid, get_raw_name(user_obj), saldo - bet)

    session["bet_amount"] = bet
    session["total_pot"] = total_pot

    # Deal kartu
    deck = create_deck()
    hands = {uid: [] for uid in players}
    for _ in range(7):
        for uid in players:
            if deck:
                hands[uid].append(deck.pop())

    # Flip first card (bukan wild)
    top = None
    while deck:
        top = deck.pop()
        if top["color"] != "wild":
            break
        deck.insert(0, top)
        top = None

    if top is None:
        top = {"color": "red", "value": "0"}

    session["deck"] = deck
    session["hands"] = hands
    session["discard"] = [top]
    session["direction"] = 1
    session["current_turn"] = 0
    session["chosen_color"] = None
    session["pending_draw"] = 0
    session["draw_pending_uid"] = None

    player_names = "\n".join([f"• {await get_nama(player_objs[uid])}" for uid in players])
    await context.bot.send_message(
        chat_id,
        f"🃏 <b>UNO TARUHAN DIMULAI!</b>\n\n"
        f"💰 Taruhan: <b>{format_rupiah(bet)}</b> per orang\n"
        f"🏆 Total pot: <b>{format_rupiah(total_pot)}</b>\n\n"
        f"👥 Pemain:\n{player_names}\n\n"
        f"kartu sudah dibagikan!\n"
        f"bot akan DM kartu kamu — cek DM!",
        parse_mode="HTML"
    )

    # Kirim kartu ke setiap pemain
    for uid in players:
        await _send_hand(uid, chat_id, session, context)

    # Tampilkan kartu pertama
    await _announce_top_card(chat_id, session, context)
    await _send_turn(chat_id, session, context)

async def _send_hand(uid, chat_id, session, context):
    hand = session["hands"][uid]
    nama = await get_nama(session["player_objs"][uid])

    if not hand:
        try:
            await context.bot.send_message(uid, f"🃏 kartu kamu: (kosong!)")
        except Exception:
            pass
        return

    labels = "\n".join([f"{i+1}. {card_label(c)}" for i, c in enumerate(hand)])
    try:
        hand_img = make_hand_image(hand)
        await context.bot.send_photo(
            uid,
            photo=hand_img,
            caption=f"🃏 <b>Kartu kamu:</b>\n\n{labels}",
            parse_mode="HTML"
        )
    except Exception:
        try:
            await context.bot.send_message(
                uid,
                f"🃏 <b>Kartu kamu:</b>\n\n{labels}",
                parse_mode="HTML"
            )
        except Exception:
            pass

async def _announce_top_card(chat_id, session, context):
    top = session["discard"][-1]
    chosen = session.get("chosen_color")
    color_info = f" (warna dipilih: {COLOR_DISPLAY.get(chosen, chosen)})" if chosen and top["color"] == "wild" else ""
    try:
        top_img = make_card_image(top)
        await context.bot.send_photo(
            chat_id,
            photo=top_img,
            caption=f"🎴 <b>Kartu teratas:</b> {card_label(top)}{color_info}",
            parse_mode="HTML"
        )
    except Exception:
        await context.bot.send_message(
            chat_id,
            f"🎴 <b>Kartu teratas:</b> {card_label(top)}{color_info}",
            parse_mode="HTML"
        )

async def _send_turn(chat_id, session, context):
    players = session["players"]
    if not players:
        return
    current_uid = players[session["current_turn"] % len(players)]
    current_user = session["player_objs"][current_uid]
    nama = await get_nama(current_user)

    top = session["discard"][-1]
    chosen = session.get("chosen_color")

    hand = session["hands"].get(current_uid, [])
    playable = playable_cards(hand, top, chosen)

    keyboard = []
    for i in playable:
        c = hand[i]
        keyboard.append([InlineKeyboardButton(f"▶ {card_label(c)}", callback_data=f"unoplay_{chat_id}_{i}")])

    keyboard.append([InlineKeyboardButton("🃏 Ambil kartu", callback_data=f"unodraw_{chat_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    hand_labels = "\n".join([f"{i+1}. {card_label(c)}" for i, c in enumerate(hand)])

    try:
        await context.bot.send_message(
            current_uid,
            f"🎲 <b>Giliran kamu!</b>\n\n"
            f"🎴 Kartu teratas: {card_label(top)}"
            + (f" (warna: {COLOR_DISPLAY.get(chosen,chosen)})" if chosen and top["color"] == "wild" else "")
            + f"\n\n🃏 Kartumu:\n{hand_labels}\n\n"
            f"pilih kartu yang mau dimainkan:",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception:
        pass

    await context.bot.send_message(
        chat_id,
        f"🎲 giliran: <b>{nama}</b> ({len(hand)} kartu)",
        parse_mode="HTML"
    )

async def _play_card_action(user_id, chat_id, card_idx, context, query):
    if chat_id not in uno_sessions:
        await query.edit_message_text("⚠️ sesi sudah tidak ada.")
        return

    session = uno_sessions[chat_id]
    players = session["players"]
    current_uid = players[session["current_turn"] % len(players)]

    if user_id != current_uid:
        await query.answer("bukan giliran kamu!", show_alert=True)
        return

    hand = session["hands"].get(user_id, [])
    if card_idx >= len(hand):
        await query.answer("kartu tidak valid!", show_alert=True)
        return

    card = hand[card_idx]
    top = session["discard"][-1]
    chosen = session.get("chosen_color")

    if not can_play(card, top, chosen):
        await query.answer("kartu ini tidak bisa dimainkan!", show_alert=True)
        return

    hand.pop(card_idx)
    session["discard"].append(card)
    session["chosen_color"] = None
    nama = await get_nama(session["player_objs"][user_id])

    await query.edit_message_text(
        f"✅ kamu memainkan: <b>{card_label(card)}</b>",
        parse_mode="HTML"
    )
    await context.bot.send_message(
        chat_id,
        f"🃏 <b>{nama}</b> memainkan: <b>{card_label(card)}</b>\n({len(hand)} kartu tersisa)",
        parse_mode="HTML"
    )

    # Cek UNO
    if len(hand) == 1:
        await context.bot.send_message(chat_id, f"⚠️ <b>UNO!</b> {nama} tinggal 1 kartu!", parse_mode="HTML")

    # Cek menang
    if len(hand) == 0:
        await _player_finished(user_id, chat_id, session, context)
        return

    # Apply card effect
    await _apply_card_effect(card, user_id, chat_id, session, context)

async def _apply_card_effect(card, player_uid, chat_id, session, context):
    players = session["players"]
    n = len(players)
    direction = session["direction"]

    if card["value"] == "Reverse":
        session["direction"] *= -1
        direction = session["direction"]
        if n == 2:
            # Reverse in 2-player acts like Skip
            session["current_turn"] = (session["current_turn"] + direction * 2) % n
        else:
            session["current_turn"] = (session["current_turn"] + direction) % n
        await context.bot.send_message(chat_id, "🔄 arah dibalik!")

    elif card["value"] == "Skip":
        session["current_turn"] = (session["current_turn"] + direction * 2) % n
        skipped_uid = players[(session["current_turn"] - direction) % n]
        skipped_nama = await get_nama(session["player_objs"][skipped_uid])
        await context.bot.send_message(chat_id, f"🚫 giliran <b>{skipped_nama}</b> di-skip!", parse_mode="HTML")

    elif card["value"] == "Draw Two":
        next_idx = (session["current_turn"] + direction) % n
        next_uid = players[next_idx]
        drawn = _draw_from_deck(session, 2)
        session["hands"][next_uid].extend(drawn)
        next_nama = await get_nama(session["player_objs"][next_uid])
        await context.bot.send_message(
            chat_id,
            f"➕ <b>{next_nama}</b> harus ambil 2 kartu dan skip!",
            parse_mode="HTML"
        )
        await _send_hand(next_uid, chat_id, session, context)
        session["current_turn"] = (session["current_turn"] + direction * 2) % n

    elif card["value"] == "Wild":
        await _ask_color(player_uid, chat_id, session, context)
        return

    elif card["value"] == "Wild Draw Four":
        next_idx = (session["current_turn"] + direction) % n
        next_uid = players[next_idx]
        drawn = _draw_from_deck(session, 4)
        session["hands"][next_uid].extend(drawn)
        next_nama = await get_nama(session["player_objs"][next_uid])
        await context.bot.send_message(
            chat_id,
            f"➕ <b>{next_nama}</b> harus ambil 4 kartu dan skip!",
            parse_mode="HTML"
        )
        await _send_hand(next_uid, chat_id, session, context)
        session["current_turn"] = (session["current_turn"] + direction) % n
        await _ask_color(player_uid, chat_id, session, context)
        return

    else:
        session["current_turn"] = (session["current_turn"] + direction) % n

    # Skip players who have finished
    _skip_finished_players(session)
    await _announce_top_card(chat_id, session, context)
    await _send_turn(chat_id, session, context)

def _skip_finished_players(session):
    players = session["players"]
    direction = session["direction"]
    n = len(players)
    if n <= 1:
        return
    while session["hands"].get(players[session["current_turn"] % n]) is not None and \
            len(session["hands"].get(players[session["current_turn"] % n], [None])) == 0:
        session["current_turn"] = (session["current_turn"] + direction) % n

def _draw_from_deck(session, count):
    drawn = []
    for _ in range(count):
        if not session["deck"]:
            if len(session["discard"]) > 1:
                top = session["discard"].pop()
                random.shuffle(session["discard"])
                session["deck"] = session["discard"]
                session["discard"] = [top]
        if session["deck"]:
            drawn.append(session["deck"].pop())
    return drawn

async def _ask_color(player_uid, chat_id, session, context):
    keyboard = [
        [
            InlineKeyboardButton("🔴 Merah", callback_data=f"unocolor_{chat_id}_red"),
            InlineKeyboardButton("🟡 Kuning", callback_data=f"unocolor_{chat_id}_yellow"),
        ],
        [
            InlineKeyboardButton("🟢 Hijau", callback_data=f"unocolor_{chat_id}_green"),
            InlineKeyboardButton("🔵 Biru", callback_data=f"unocolor_{chat_id}_blue"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await context.bot.send_message(
            player_uid,
            "🌈 <b>pilih warna:</b>",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception:
        pass

async def _choose_color_action(user_id, chat_id, chosen_color, context, query):
    if chat_id not in uno_sessions:
        await query.edit_message_text("⚠️ sesi sudah tidak ada.")
        return

    session = uno_sessions[chat_id]
    players = session["players"]
    direction = session["direction"]
    n = len(players)

    # Verifikasi yang memilih adalah pemain yang main wild
    # (bisa saja bukan current turn kalau WD4 dan current sudah advance)
    session["chosen_color"] = chosen_color
    color_label = {"red": "Merah 🔴", "yellow": "Kuning 🟡", "green": "Hijau 🟢", "blue": "Biru 🔵"}.get(chosen_color, chosen_color)

    await query.edit_message_text(f"✅ kamu memilih warna: <b>{color_label}</b>", parse_mode="HTML")
    await context.bot.send_message(
        chat_id,
        f"🌈 warna dipilih: <b>{color_label}</b>",
        parse_mode="HTML"
    )

    session["current_turn"] = (session["current_turn"] + direction) % n
    _skip_finished_players(session)
    await _announce_top_card(chat_id, session, context)
    await _send_turn(chat_id, session, context)

async def _draw_card_action(user_id, chat_id, context, query):
    if chat_id not in uno_sessions:
        await query.edit_message_text("⚠️ sesi sudah tidak ada.")
        return

    session = uno_sessions[chat_id]
    players = session["players"]
    current_uid = players[session["current_turn"] % len(players)]

    if user_id != current_uid:
        await query.answer("bukan giliran kamu!", show_alert=True)
        return

    drawn = _draw_from_deck(session, 1)
    nama = await get_nama(session["player_objs"][user_id])

    if drawn:
        session["hands"][user_id].extend(drawn)
        card = drawn[0]
        await query.edit_message_text(
            f"🃏 kamu mengambil kartu: <b>{card_label(card)}</b>",
            parse_mode="HTML"
        )
        await context.bot.send_message(
            chat_id,
            f"🃏 <b>{nama}</b> mengambil 1 kartu",
            parse_mode="HTML"
        )

        top = session["discard"][-1]
        chosen = session.get("chosen_color")

        if can_play(card, top, chosen):
            keyboard = [
                [InlineKeyboardButton(f"▶ Mainkan {card_label(card)}", callback_data=f"unoplay_{chat_id}_{len(session['hands'][user_id])-1}")],
                [InlineKeyboardButton("⏭ Pass (skip giliran)", callback_data=f"unopass_{chat_id}")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            try:
                await context.bot.send_message(
                    user_id,
                    f"kartu yang kamu ambil bisa dimainkan!\n{card_label(card)}\n\nmainkan atau pass?",
                    reply_markup=reply_markup
                )
            except Exception:
                await _advance_turn(chat_id, session, context)
        else:
            await _advance_turn(chat_id, session, context)
    else:
        await query.edit_message_text("deck kosong dan tidak ada kartu untuk diambil!")
        await _advance_turn(chat_id, session, context)

async def _pass_turn_action(user_id, chat_id, context, query):
    if chat_id not in uno_sessions:
        await query.edit_message_text("⚠️ sesi sudah tidak ada.")
        return

    session = uno_sessions[chat_id]
    players = session["players"]
    current_uid = players[session["current_turn"] % len(players)]

    if user_id != current_uid:
        await query.answer("bukan giliran kamu!", show_alert=True)
        return

    await query.edit_message_text("⏭ kamu pass.")
    nama = await get_nama(session["player_objs"][user_id])
    await context.bot.send_message(chat_id, f"⏭ <b>{nama}</b> pass.", parse_mode="HTML")
    await _advance_turn(chat_id, session, context)

async def _advance_turn(chat_id, session, context):
    direction = session["direction"]
    players = session["players"]
    n = len(players)
    session["current_turn"] = (session["current_turn"] + direction) % n
    _skip_finished_players(session)
    await _announce_top_card(chat_id, session, context)
    await _send_turn(chat_id, session, context)

async def _player_finished(user_id, chat_id, session, context):
    if session.get("finished"):
        return

    session["finish_order"].append(user_id)
    players = session["players"]
    nama = await get_nama(session["player_objs"][user_id])
    rank = len(session["finish_order"])

    await context.bot.send_message(
        chat_id,
        f"🎉 <b>{nama}</b> habis kartu! (peringkat #{rank})",
        parse_mode="HTML"
    )

    # Cek remaining players yang masih punya kartu
    remaining = [uid for uid in players if uid not in session["finish_order"]]

    if len(remaining) <= 1:
        # Game selesai
        if remaining:
            session["finish_order"].append(remaining[0])
        session["finished"] = True
        await _end_uno_game(chat_id, session, context)
        return

    # Lanjutkan dengan player berikutnya
    direction = session["direction"]
    n = len(players)
    session["current_turn"] = (session["current_turn"] + direction) % n
    _skip_finished_players(session)
    await _announce_top_card(chat_id, session, context)
    await _send_turn(chat_id, session, context)

async def _end_uno_game(chat_id, session, context):
    finish_order = session["finish_order"]
    player_objs = session["player_objs"]
    bet = session["bet_amount"]
    total_pot = session["total_pot"]
    players = session["players"]

    # Pastikan finish_order lengkap
    for uid in players:
        if uid not in finish_order:
            finish_order.append(uid)

    winner_uid = finish_order[0]
    winner_user = player_objs[winner_uid]
    winner_nama = await get_nama(winner_user)

    # Transfer saldo: winner dapat total_pot (sudah dikurangi bet sendiri saat start)
    # winner mendapat semua taruhan player lain
    winnings = bet * (len(players) - 1)
    winner_wallet = await db_get_wallet(winner_uid)
    winner_saldo = (winner_wallet["saldo"] if winner_wallet else SLOT_INITIAL) + winnings
    await db_set_wallet(winner_uid, get_raw_name(winner_user), winner_saldo)

    # Skor
    chat_id_score = chat_id
    for rank, uid in enumerate(finish_order, 1):
        user_obj = player_objs[uid]
        if rank == 1:
            await add_score(chat_id_score, user_obj, 500)
        else:
            await add_score(chat_id_score, user_obj, 100)

    # Buat hasil
    result_text = f"🏆 <b>GAME UNO TARUHAN SELESAI!</b>\n\n"
    result_text += f"💰 Taruhan: {format_rupiah(bet)} per orang\n"
    result_text += f"🎯 Total pot: {format_rupiah(total_pot)}\n\n"
    result_text += f"🥇 <b>PEMENANG: {winner_nama}!</b>\n"
    result_text += f"   +{format_rupiah(winnings)} saldo\n"
    result_text += f"   +500 poin\n\n"
    result_text += f"📊 <b>Urutan selesai:</b>\n"

    for rank, uid in enumerate(finish_order, 1):
        user_obj = player_objs[uid]
        n = await get_nama(user_obj)
        if rank == 1:
            result_text += f"🥇 {n} — +{format_rupiah(winnings)} saldo, +500 poin\n"
        elif rank == 2:
            result_text += f"🥈 {n} — +100 poin\n"
        elif rank == 3:
            result_text += f"🥉 {n} — +100 poin\n"
        else:
            result_text += f"#{rank} {n} — +100 poin\n"

    result_text += f"\n💳 saldo {winner_nama}: {format_rupiah(winner_saldo)}"

    await context.bot.send_message(chat_id, result_text, parse_mode="HTML")

    del uno_sessions[chat_id]

async def stopuno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in uno_sessions:
        session = uno_sessions[chat_id]
        # Kembalikan saldo jika taruhan sudah dibayar
        if session.get("bet_amount") is not None:
            bet = session["bet_amount"]
            player_objs = session["player_objs"]
            for uid in session["players"]:
                user_obj = player_objs[uid]
                wallet = await db_get_wallet(uid)
                saldo = (wallet["saldo"] if wallet else SLOT_INITIAL) + bet
                await db_set_wallet(uid, get_raw_name(user_obj), saldo)

            await update.message.reply_text(
                f"game UNO dihentikan.\n"
                f"taruhan {format_rupiah(bet)} dikembalikan ke semua pemain."
            )
        else:
            await update.message.reply_text("game UNO dihentikan.")

        for uid in list(uno_dm_pending.keys()):
            if uno_dm_pending[uid].get("chat_id") == chat_id:
                del uno_dm_pending[uid]

        del uno_sessions[chat_id]
    else:
        await update.message.reply_text("tidak ada game UNO yang berjalan")

async def proses_uno_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in uno_dm_pending:
        return

    pending = uno_dm_pending[user_id]
    stage = pending.get("stage")
    chat_id = pending.get("chat_id")

    if stage == "bet_custom":
        text = update.message.text.strip().replace(".", "").replace(",", "")
        if not text.isdigit():
            await update.message.reply_text("tolong masukkan angka saja. contoh: 500000")
            return
        bet_amount = int(text)
        if bet_amount <= 0:
            await update.message.reply_text("❌ taruhan harus lebih dari 0!")
            return
        await _process_uno_bet(user_id, update.message.from_user, chat_id, bet_amount, context)
