from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from uno_game import UnoGame, get_card_label, get_card_sticker, COLOR_LABEL
import random

async def send_turn_message(bot: Bot, chat_id: int, game: UnoGame, player_names: dict):
    """Kirim pesan giliran ke grup."""
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
        count = len(game.players[uid].hand)
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

async def process_play_card(bot: Bot, chat_id: int, game: UnoGame, player_uid: int, card: tuple, context):
    """Memproses aksi main kartu."""
    success, msg = game.play_card(player_uid, card)
    if not success:
        return False, msg

    player = game.players[player_uid]
    label = get_card_label(card)

    # Kirim sticker (opsional)
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
        player.uno_called = True  # Tandai sudah disebut

    if player.card_count() == 0:
        # Pemain habis kartu
        game.player_done(player_uid)
        rank = len(game.finished_players)
        await bot.send_message(chat_id, f"🎉 <b>{player.name}</b> habis kartu! (#{rank})", parse_mode="HTML")
        if game.is_game_over():
            return True, "game_over"
        # Lanjutkan ke giliran berikutnya
        game.advance_turn()
        await send_turn_message(bot, chat_id, game, {uid: p.name for uid, p in game.players.items()})
        return True, "player_finished"

    # Terapkan efek kartu
    effect = game.apply_effect(card)

    if effect == "choose_color":
        # Minta pemain memilih warna
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
        # Jangan kirim turn message dulu
    else:
        game.advance_turn()
        await send_turn_message(bot, chat_id, game, {uid: p.name for uid, p in game.players.items()})

    return True, "success"

async def process_draw_card(bot: Bot, chat_id: int, game: UnoGame, player_uid: int, context):
    """Memproses aksi ambil kartu."""
    player = game.players.get(player_uid)
    if not player:
        return False, "Pemain tidak ditemukan"

    card = game.draw_card(player_uid)
    if not card:
        await bot.send_message(chat_id, "🃏 Deck kosong, tidak bisa ambil kartu.")
        game.advance_turn()
        await send_turn_message(bot, chat_id, game, {uid: p.name for uid, p in game.players.items()})
        return True, "no_card"

    await bot.send_message(chat_id, f"🃏 <b>{player.name}</b> ambil 1 kartu ({player.card_count()} kartu)", parse_mode="HTML")

    # Cek apakah kartu yang diambil bisa langsung dimainkan
    if game.can_play(card):
        # Tampilkan tombol Mainkan / Pass
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
        # Jangan maju giliran, tunggu keputusan pemain
        return True, "can_play"
    else:
        game.advance_turn()
        await send_turn_message(bot, chat_id, game, {uid: p.name for uid, p in game.players.items()})
        return True, "success"

async def process_pass(bot: Bot, chat_id: int, game: UnoGame, player_uid: int, context):
    """Pemain memilih pass setelah ambil kartu."""
    player = game.players.get(player_uid)
    if not player:
        return False, "Pemain tidak ditemukan"

    await bot.send_message(chat_id, f"⏭ <b>{player.name}</b> pass.", parse_mode="HTML")
    game.advance_turn()
    await send_turn_message(bot, chat_id, game, {uid: p.name for uid, p in game.players.items()})
    return True, "success"

async def process_color_choice(bot: Bot, chat_id: int, game: UnoGame, player_uid: int, color: str, context):
    """Pemain memilih warna setelah Wild."""
    if game.pending_color_chooser != player_uid:
        return False, "Bukan giliranmu memilih warna"

    game.set_color(color)
    label = {"r":"Merah 🔴","g":"Hijau 🟢","b":"Biru 🔵","y":"Kuning 🟡"}.get(color, color)
    await bot.send_message(chat_id, f"🌈 warna dipilih: <b>{label}</b>", parse_mode="HTML")

    game.advance_turn()
    await send_turn_message(bot, chat_id, game, {uid: p.name for uid, p in game.players.items()})
    return True, "success"
