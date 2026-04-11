import random
from telegram import Update
from telegram.ext import ContextTypes

from data import (
    SLOT_EMOJIS, DIAMOND, SUPER_JACKPOT_EMOJI,
    SLOT_COST, SLOT_WIN_NORMAL, SLOT_WIN_DIAMOND, SLOT_WIN_SUPER, SLOT_INITIAL,
    init_wallet, format_rupiah, get_nama, get_raw_name,
)
from db import db_get_all_wallets, db_get_badges, db_update_saldo

async def slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    uid = user.id
    nama = await get_nama(user)

    await init_wallet(user)

    reel = [random.choice(SLOT_EMOJIS) for _ in range(3)]
    tampilan = " | ".join(reel)
    semua_sama = reel[0] == reel[1] == reel[2]

    delta = -SLOT_COST

    if semua_sama and reel[0] == SUPER_JACKPOT_EMOJI:
        delta += SLOT_WIN_SUPER
        hasil_teks = (
            f"🪽🪽🪽 <b>SUPER JACKPOT!!</b> 🪽🪽🪽\n\n"
            f"WOOWWW KAMU LUAR BIASA BERUNTUNG!!! 🎉🎉🎉\n\n"
            f"menang <b>{format_rupiah(SLOT_WIN_SUPER)}</b>!"
        )
    elif semua_sama and reel[0] == DIAMOND:
        delta += SLOT_WIN_DIAMOND
        hasil_teks = (
            f"💎💎💎 <b>JACKPOT DIAMOND!!</b> 💎💎💎\n\n"
            f"kamu beruntung!!! 🤑\n\n"
            f"menang <b>{format_rupiah(SLOT_WIN_DIAMOND)}</b>!"
        )
    elif semua_sama:
        delta += SLOT_WIN_NORMAL
        hasil_teks = (
            f"🎊 <b>MENANG!</b> kamu beruntung! 🎊\n\n"
            f"menang <b>{format_rupiah(SLOT_WIN_NORMAL)}</b>!"
        )
    else:
        hasil_teks = "😢 tidak ada yang cocok, coba lagi!"

    saldo = await db_update_saldo(uid, delta)
    if saldo is None:
        saldo = SLOT_INITIAL + delta

    await update.message.reply_text(
        f"🎰 <b>SLOT MACHINE</b>\n\n"
        f"┌─────────────────┐\n"
        f"│  {tampilan}  │\n"
        f"└─────────────────┘\n\n"
        f"{hasil_teks}\n\n"
        f"💳 saldo: <b>{format_rupiah(saldo)}</b>",
        parse_mode="HTML"
    )

async def kekayaan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await db_get_all_wallets()
    wallets = [r for r in rows if r["user_id"] > 0]

    if not wallets:
        await update.message.reply_text("belum ada yang main slot!")
        return

    text = "💰 <b>DAFTAR KEKAYAAN PEMAIN</b>\n\n"
    for i, info in enumerate(wallets, 1):
        saldo = info["saldo"]
        uid = info["user_id"]
        raw_name = info["name"]
        badges = await db_get_badges(uid)
        display_name = f"{raw_name} {''.join(badges)}" if badges else raw_name
        emoji = "🤑" if saldo > SLOT_INITIAL else ("😢" if saldo < 0 else "😐")
        text += f"{i}. {display_name} — {format_rupiah(saldo)} {emoji}\n"

    text += f"\n💡 saldo awal: {format_rupiah(SLOT_INITIAL)}\n🎰 bayar per spin: {format_rupiah(SLOT_COST)}"
    await update.message.reply_text(text, parse_mode="HTML")
