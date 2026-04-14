import random
from typing import List, Dict, Optional, Tuple, Set

# -------------------- CONSTANTS --------------------
COLORS = ["r", "g", "b", "y"]
COLOR_LABEL = {"r": "🔴Merah", "g": "🟢Hijau", "b": "🔵Biru", "y": "🟡Kuning"}
CARD_VALUES = ["0","1","2","3","4","5","6","7","8","9","draw","skip","reverse"]
WILD_VALUES = ["colorchooser", "draw_four"]

# STICKER MAPPING (akan digunakan di inline query)
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

# Reverse mapping untuk chosen result
STICKER_TO_CARD = {}
for key, fid in STICKERS.items():
    if key == "draw_four":
        STICKER_TO_CARD[fid] = ("x", "draw_four")
    elif key == "colorchooser":
        STICKER_TO_CARD[fid] = ("x", "colorchooser")
    else:
        c, v = key.split("_", 1)
        STICKER_TO_CARD[fid] = (c, v)


class UnoPlayer:
    def __init__(self, user_id: int, name: str):
        self.user_id = user_id
        self.name = name
        self.hand: List[Tuple[str, str]] = []
        self.eliminated = False
        self.finished = False
        self.uno_called = False

    def has_card(self, card: Tuple[str, str]) -> bool:
        return card in self.hand

    def remove_card(self, card: Tuple[str, str]) -> bool:
        if card in self.hand:
            self.hand.remove(card)
            return True
        return False

    def card_count(self) -> int:
        return len(self.hand)


class UnoGame:
    def __init__(self, chat_id: int, players: List[int], player_names: Dict[int, str], bet: int):
        self.chat_id = chat_id
        self.players: Dict[int, UnoPlayer] = {}
        for uid in players:
            self.players[uid] = UnoPlayer(uid, player_names[uid])
        self.player_order = players[:]  # urutan tetap
        self.bet = bet
        self.pot = bet * len(players)
        self.deck: List[Tuple[str, str]] = []
        self.discard: List[Tuple[str, str]] = []
        self.direction = 1
        self.turn_index = 0
        self.chosen_color: Optional[str] = None
        self.started = False
        self.finished_players: List[int] = []
        self.pending_color_chooser: Optional[int] = None
        self.pending_draw_four: bool = False

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
        # Setup initial discard
        while self.deck:
            top = self.deck.pop()
            if top[0] != "x":
                self.discard.append(top)
                break
            self.deck.insert(0, top)
        if not self.discard:
            self.discard.append(("r", "0"))

    def _draw_cards(self, n: int) -> List[Tuple[str, str]]:
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

    def get_current_player(self) -> Optional[UnoPlayer]:
        active = self.get_active_players()
        if not active:
            return None
        idx = self.turn_index % len(self.player_order)
        uid = self.player_order[idx]
        if uid not in active:
            # cari pemain berikutnya
            for i in range(len(self.player_order)):
                next_idx = (idx + i) % len(self.player_order)
                next_uid = self.player_order[next_idx]
                if next_uid in active:
                    self.turn_index = next_idx
                    return self.players[next_uid]
        return self.players.get(uid)

    def get_active_players(self) -> List[int]:
        return [uid for uid in self.player_order if not self.players[uid].eliminated and not self.players[uid].finished]

    def can_play(self, card: Tuple[str, str]) -> bool:
        top = self.discard[-1]
        c, v = card
        tc, tv = top
        if v in ("colorchooser", "draw_four"):
            return True
        if tc == "x":
            return c == self.chosen_color if self.chosen_color else True
        return c == tc or v == tv

    def play_card(self, player_uid: int, card: Tuple[str, str]) -> Tuple[bool, str]:
        player = self.players.get(player_uid)
        if not player:
            return False, "Pemain tidak ditemukan"
        if not player.has_card(card):
            return False, "Kartu tidak dimiliki"
        if not self.can_play(card):
            return False, "Kartu tidak bisa dimainkan"

        player.remove_card(card)
        self.discard.append(card)
        self.chosen_color = None

        # Cek UNO
        if len(player.hand) == 1 and not player.uno_called:
            # Pemain lupa bilang UNO -> penalti 2 kartu
            penalty = self._draw_cards(2)
            player.hand.extend(penalty)
            return True, "penalty_uno"

        return True, "success"

    def apply_effect(self, card: Tuple[str, str]) -> str:
        """Apply card effect and return next action hint."""
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

        else:  # normal card
            self.turn_index = (self.turn_index + self.direction) % len(self.player_order)
            return "normal"

    def _get_next_player_uid(self) -> Optional[int]:
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
        """Make sure turn_index points to an active player."""
        active = self.get_active_players()
        if not active:
            return
        # Cari indeks yang valid
        for _ in range(len(self.player_order)):
            idx = self.turn_index % len(self.player_order)
            if self.player_order[idx] in active:
                break
            self.turn_index = (self.turn_index + self.direction) % len(self.player_order)

    def draw_card(self, player_uid: int) -> Optional[Tuple[str, str]]:
        drawn = self._draw_cards(1)
        if drawn:
            card = drawn[0]
            self.players[player_uid].hand.append(card)
            return card
        return None

    def player_done(self, player_uid: int):
        player = self.players.get(player_uid)
        if player and not player.finished:
            player.finished = True
            self.finished_players.append(player_uid)
        # Cek apakah game selesai
        active = self.get_active_players()
        if len(active) <= 1:
            if active:
                winner = active[0]
                if winner not in self.finished_players:
                    self.finished_players.append(winner)
            return True
        return False

    def set_color(self, color: str):
        self.chosen_color = color
        self.pending_color_chooser = None
        self.pending_draw_four = False

    def is_game_over(self) -> bool:
        return len(self.get_active_players()) <= 1

    def get_top_card(self) -> Tuple[str, str]:
        return self.discard[-1]

    def get_winner(self) -> Optional[int]:
        if len(self.finished_players) > 0:
            return self.finished_players[0]
        active = self.get_active_players()
        if len(active) == 1:
            return active[0]
        return None


# Helper functions for label and sticker
def get_card_label(card: Tuple[str, str]) -> str:
    c, v = card
    col = COLOR_LABEL.get(c, "")
    lbl = {"draw": "+2", "skip": "⊘", "reverse": "⇌", "colorchooser": "Wild", "draw_four": "Wild+4"}
    return f"{col} {lbl.get(v, v)}" if col else lbl.get(v, v)

def get_card_sticker(card: Tuple[str, str]) -> Optional[str]:
    c, v = card
    if v in ("colorchooser", "draw_four"):
        return STICKERS.get(v)
    key = f"{c}_{v}"
    return STICKERS.get(key)
