import random
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InlineQueryResultCachedSticker, InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import ContextTypes

from data import add_score, get_nama, get_raw_name, init_wallet, format_rupiah, SLOT_INITIAL
from db import db_get_wallet, db_set_wallet

# -------------------- CONSTANTS & STICKER MAPPING --------------------
COLORS = ["r", "g", "b", "y"]
COLOR_LABEL = {"r": "🔴Merah", "g": "🟢Hijau", "b": "🔵Biru", "y": "🟡Kuning"}
CARD_VALUES = ["0","1","2","3","4","5","6","7","8","9","draw","skip","reverse"]
WILD_VALUES = ["colorchooser", "draw_four"]

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
for key, fid in STICKERS.items():
    if key == "draw_four":
        STICKER_TO_CARD[fid] = ("x", "draw_four")
    elif key == "colorchooser":
        STICKER_TO_CARD[fid] = ("x", "colorchooser")
    else:
        c, v = key.split("_", 1)
        STICKER_TO_CARD[fid] = (c, v)

def get_card_label(card):
    c, v = card
    col = COLOR_LABEL.get(c, "")
    lbl = {"draw": "+2", "skip": "⊘", "reverse": "⇌", "colorchooser": "Wild", "draw_four": "Wild+4"}
    return f"{col} {lbl.get(v, v)}" if col else lbl.get(v, v)

def get_card_sticker(card):
    c, v = card
    if v in ("colorchooser", "draw_four"):
        return STICKERS.get(v)
    key = f"{c}_{v}"
    return STICKERS.get(key)

# -------------------- CLASS DEFINITIONS --------------------
class UnoPlayer:
    def __init__(self, user_id: int, name: str):
        self.user_id = user_id
        self.name = name
        self.hand = []  # list of (color, value)
        self.eliminated = False
        self.finished = False
        self.uno_called = False

    def has_card(self, card):
        return card in self.hand

    def remove_card(self, card):
        if card in self.hand:
            self.hand.remove(card)
            return True
        return False

    def card_count(self):
        return len(self.hand)

class UnoGame:
    def __init__(self, chat_id: int, players: list, player_names: dict, bet: int):
        self.chat_id = chat_id
        self.players = {}
        for uid in players:
            self.players[uid] = UnoPlayer(uid, player_names[uid])
        self.player_order = players[:]
        self.bet = bet
        self.pot = bet * len(players)
        self.deck = []
        self.discard = []
        self.direction = 1
        self.turn_index = 0
        self.chosen_color = None
        self.started = False
        self.finished_players = []
        self.pending_color_chooser = None
        self.pending_draw_four = False
        self._init_deck()
        self._deal_cards()

    def _init_deck(self):
        deck = []
        for c in COLORS:
            for v in CARD_VALUES:
                deck.append((c, v))
                if v != "0":
                    deck.append((c, v))
        for _ in range(4):
            deck.append(("x", "colorchooser"))
            deck.append(("x", "draw_four"))
        random.shuffle(deck)
        self.deck = deck

    def _deal_cards(self):
        for _ in range(7):
            for uid in self.player_order:
                if self.deck:
                    self.players[uid].hand.append(self.deck.pop())
        while self.deck:
            top = self.deck.pop()
            if top[0] != "x":
                self.discard.append(top)
                break
            self.deck.insert(0, top)
        if not self.discard:
            self.discard.append(("r", "0"))

    def _draw_cards(self, n):
        drawn = []
        for _ in range(n):
            if not self.deck:
                if len(self.discard) > 1:
                    top = self.discard.pop()
                    random.shuffle(self.discard)
                    self.deck = self.discard
                    self.discard = [top]
            if self.deck:
                drawn.append(self.deck.pop())
        return drawn

    def get_active_players(self):
        return [uid for uid in self.player_order if not self.players[uid].eliminated and not self.players[uid].finished]

    def get_current_player(self):
        active = self.get_active_players()
        if not active:
            return None
        idx = self.turn_index % len(self.player_order)
        uid = self.player_order[idx]
        if uid not in active:
            for i in range(len(self.player_order)):
                next_idx = (idx + i) % len(self.player_order)
                next_uid = self.player_order[next_idx]
                if next_uid in active:
                    self.turn_index = next_idx
                    return self.players[next_uid]
        return self.players.get(uid)

    def can_play(self, card):
        top = self.discard[-1]
        c, v = card
        tc, tv = top
        if v in ("colorchooser", "draw_four"):
            return True
        if tc == "x":
            return c == self.chosen_color if self.chosen_color else True
        return c == tc or v == tv

    def play_card(self, player_uid, card):
        player = self.players.get(player_uid)
        if not player or not player.has_card(card) or not self.can_play(card):
            return False, "invalid"
        player.remove_card(card)
        self.discard.append(card)
        self.chosen_color = None
        if len(player.hand) == 1 and not player.uno_called:
            penalty = self._draw_cards(2)
            player.hand.extend(penalty)
            return True, "penalty_uno"
        return True, "success"

    def apply_effect(self, card):
        c, v = card
        active = self.get_active_players()
        if not active:
            return "game_end"
        if v == "reverse":
            self.direction *= -1
            if len(active) == 2:
                self.turn_index = (self.turn_index + self.direction * 2) % len(self.player_order)
            else:
                self.turn_index = (self.turn_index + self.direction) % len(self.player_order)
            return "reverse"
        elif v == "skip":
            self.turn_index = (self.turn_index + self.direction * 2) % len(self.player_order)
            return "skip"
        elif v == "draw":
            next_uid = self._get_next_player_uid()
            if next_uid:
                drawn = self._draw_cards(2)
                self.players[next_uid].hand.extend(drawn)
            self.turn_index = (self.turn_index + self.direction * 2) % len(self.player_order)
            return "draw"
        elif v == "colorchooser":
            self.pending_color_chooser = self.get_current_player().user_id if self.get_current_player() else None
            return "choose_color"
        elif v == "draw_four":
            next_uid = self._get_next_player_uid()
            if next_uid:
                drawn = self._draw_cards(4)
                self.players[next_uid].hand.extend(drawn)
            self.turn_index = (self.turn_index + self.direction) % len(self.player_order)
            self.pending_color_chooser = self.get_current_player().user_id if self.get_current_player() else None
            self.pending_draw_four = True
            return "choose_color"
        else:
            self.turn_index = (self.turn_index + self.direction) % len(self.player_order)
            return "normal"

    def _get_next_player_uid(self):
        active = self.get_active_players()
        if not active:
            return None
        idx = self.turn_index % len(self.player_order)
        for _ in range(len(self.player_order)):
            idx = (idx + self.direction) % len(self.player_order)
            uid = self.player_order[idx]
            if uid in active:
                return uid
        return None

    def advance_turn(self):
        active = self.get_active_players()
        if not active:
            return
        for _ in range(len(self.player_order)):
            idx = self.turn_index % len(self.player_order)
            if self.player_order[idx] in active:
                break
            self.turn_index = (self.turn_index + self.direction) % len(self.player_order)

    def draw_card(self, player_uid):
        drawn = self._draw_cards(1)
        if drawn:
            card = drawn[0]
            self.players[player_uid].hand.append(card)
            return card
        return None

    def player_done(self, player_uid):
        player = self.players.get(player_uid)
        if player and not player.finished:
            player.finished = True
            self.finished_players.append(player_uid)
        active = self.get_active_players()
        if len(active) <= 1:
            if active and active[0] not in self.finished_players:
                self.finished_players.append(active[0])
            return True
        return False

    def set_color(self, color):
        self.chosen_color = color
        self.pending_color_chooser = None
        self.pending_draw_four = False

    def is_game_over(self):
        return len(self.get_active_players()) <= 1

    def get_top_card(self):
        return self.discard[-1]

    def get_winner(self):
        if self.finished_players:
            return self.finished_players[0]
        active = self.get_active_players()
        if len(active) == 1:
            return active[0]
        return None

# -------------------- HELPER FUNCTIONS --------------------
async def send_turn_message(bot, chat_id, game, player_names):
    current = game.get_current_player()
    if not current:
        await bot.send_message(chat_id, "Permainan berakhir.")
        return
    top = game.get_top_card()
    chosen = game.chosen_color
    color_hint = f"\n🌈 Warna: {COLOR_LABEL.get(chosen, '?')}" if chosen and top[0] == "x" else ""
    active = game.get_active_players()
    player_parts = []
    for uid in active:
        name = player_names.get(uid, str(uid))
        count = game.players[uid].card_count()
        player_parts.append(f"{name} ({count} kartu)")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🃏 Lihat Kartu", switch_inline_query_current_chat="")]
    ])
    await bot.send_message(
        chat_id,
        f"🎲 giliran: <b>{current.name}</b> ({current.card_count()} kartu)\n"
        f"🎴 Kartu teratas: <b>{get_card_label(top)}</b>{color_hint}\n\n"
        f"👥 {' → '.join(player_parts)}",
        reply_markup=kb,
        parse_mode="HTML"
    )

async def process_play_card(bot, chat_id, game, player_uid, card, context):
    success, msg = game.play_card(player_uid, card)
    if not success:
        return False, msg
    player = game.players[player_uid]
    label = get_card_label(card)
    sticker_id = get_card_sticker(card)
    if sticker_id:
        try:
            await bot.send_sticker(chat_id, sticker_id)
        except:
            pass
    await bot.send_message(
        chat_id,
        f"🃏 <b>{player.name}</b> memainkan: <b>{label}</b> ({player.card_count()} kartu tersisa)",
        parse_mode="HTML"
    )
    if msg == "penalty_uno":
        await bot.send_message(chat_id, f"⚠️ <b>{player.name}</b> lupa bilang UNO! Ambil 2 kartu penalti.", parse_mode="HTML")
    if player.card_count() == 1 and not player.uno_called:
        player.uno_called = True
    if player.card_count() == 0:
        game_over = game.player_done(player_uid)
        rank = len(game.finished_players)
        await bot.send_message(chat_id, f"🎉 <b>{player.name}</b> habis kartu! (#{rank})", parse_mode="HTML")
        if game_over:
            return True, "game_over"
        game.advance_turn()
        await send_turn_message(bot, chat_id, game, {uid: p.name for uid, p in game.players.items()})
        return True, "player_finished"
    effect = game.apply_effect(card)
    if effect == "choose_color":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔴 Merah", callback_data=f"unocolor_{chat_id}_r"),
             InlineKeyboardButton("🟡 Kuning", callback_data=f"unocolor_{chat_id}_y")],
            [InlineKeyboardButton("🟢 Hijau", callback_data=f"unocolor_{chat_id}_g"),
             InlineKeyboardButton("🔵 Biru", callback_data=f"unocolor_{chat_id}_b")],
        ])
        await bot.send_message(
            chat_id,
            f"🌈 <b>{player.name}</b>, pilih warna:",
            reply_markup=kb,
            parse_mode="HTML"
        )
    else:
        game.advance_turn()
        await send_turn_message(bot, chat_id, game, {uid: p.name for uid, p in game.players.items()})
    return True, "success"

async def process_draw_card(bot, chat_id, game, player_uid, context):
    player = game.players.get(player_uid)
    if not player:
        return False, "invalid"
    card = game.draw_card(player_uid)
    if not card:
        await bot.send_message(chat_id, "🃏 Deck kosong, tidak bisa ambil kartu.")
        game.advance_turn()
        await send_turn_message(bot, chat_id, game, {uid: p.name for uid, p in game.players.items()})
        return True, "no_card"
    await bot.send_message(chat_id, f"🃏 <b>{player.name}</b> ambil 1 kartu ({player.card_count()} kartu)", parse_mode="HTML")
    if game.can_play(card):
        hand_index = len(player.hand) - 1
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶ Mainkan", callback_data=f"unoplay_{chat_id}_{hand_index}")],
            [InlineKeyboardButton("⏭ Pass", callback_data=f"unopass_{chat_id}")],
        ])
        await bot.send_message(
            chat_id,
            f"Kartu yang diambil <b>{player.name}</b> bisa dimainkan!",
            reply_markup=kb,
            parse_mode="HTML"
        )
        return True, "can_play"
    else:
        game.advance_turn()
        await send_turn_message(bot, chat_id, game, {uid: p.name for uid, p in game.players.items()})
        return True, "success"

async def process_pass(bot, chat_id, game, player_uid, context):
    player = game.players.get(player_uid)
    if not player:
        return False
    await bot.send_message(chat_id, f"⏭ <b>{player.name}</b> pass.", parse_mode="HTML")
    game.advance_turn()
    await send_turn_message(bot, chat_id, game, {uid: p.name for uid, p in game.players.items()})
    return True

async def process_color_choice(bot, chat_id, game, player_uid, color, context):
    if game.pending_color_chooser != player_uid:
        return False
    game.set_color(color)
    label = {"r":"Merah 🔴","g":"Hijau 🟢","b":"Biru 🔵","y":"Kuning 🟡"}.get(color, color)
    await bot.send_message(chat_id, f"🌈 warna dipilih: <b>{label}</b>", parse_mode="HTML")
    game.advance_turn()
    await send_turn_message(bot, chat_id, game, {uid: p.name for uid, p in game.players.items()})
    return True

# -------------------- SESSION STORAGE --------------------
uno_sessions = {}  # chat_id -> UnoGame
uno_bet_pending = {}

# -------------------- COMMAND HANDLERS --------------------
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

# -------------------- BETTING CALLBACKS --------------------
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
    for uid in players:
        w = await db_get_wallet(uid)
        await db_set_wallet(uid, get_raw_name(objs[uid]), (w["saldo"] if w else SLOT_INITIAL) - bet)
    player_names = {uid: await get_nama(objs[uid]) for uid in players}
    game = UnoGame(cid, players, player_names, bet)
    uno_sessions[cid] = game
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
    top = game.get_top_card()
    stk = get_card_sticker(top)
    if stk:
        await context.bot.send_sticker(cid, stk)
    await context.bot.send_message(cid, f"🎴 kartu awal: <b>{get_card_label(top)}</b>", parse_mode="HTML")
    await send_turn_message(context.bot, cid, game, player_names)

# -------------------- INLINE QUERY HANDLER --------------------
async def handle_uno_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    uid = query.from_user.id
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

# -------------------- CHOSEN INLINE RESULT HANDLER --------------------
async def handle_uno_chosen_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chosen_inline_result
    uid = result.from_user.id
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
    current = game.get_current_player()
    if current.user_id != uid:
        return
    res_id = result.result_id
    if res_id == "info":
        return
    elif res_id.startswith("card_"):
        idx = int(res_id.split("_")[1])
        if idx < len(player.hand):
            card = player.hand[idx]
            if game.can_play(card):
                success, status = await process_play_card(
                    context.bot, cid, game, uid, card, context
                )
                if status == "game_over":
                    await end_game(cid, game, context)

# -------------------- CALLBACK HANDLER (warna, main setelah draw, pass) --------------------
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

# -------------------- END GAME --------------------
async def end_game(cid, game: UnoGame, context):
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
        for rank, uid in enumerate(order, 1):
            user_obj = await context.bot.get_chat(uid)
            await add_score(cid, user_obj, 500 if rank == 1 else 100)
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

# Placeholder untuk kompatibilitas (tidak digunakan)
async def handle_uno_sticker_in_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def proses_uno_inline_draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass
