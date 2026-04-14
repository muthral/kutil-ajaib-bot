import os
from telegram import Update
from telegram.ext import ContextTypes
from data import get_nama, format_rupiah, init_wallet, get_raw_name
from db import db_get_wallet, db_set_wallet, db_get_scores, db_set_score, db_get_wallet_by_any_name

ADMIN_IDS_STR = os.environ.get("BOT_ADMIN_IDS", "")
ADMIN_IDS = set()
for part in ADMIN_IDS_STR.split(","):
    part = part.strip()
    if part.isdigit():
        ADMIN_IDS.add(int(part))

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def setsaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ kamu bukan admin bot.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("gunakan: /setsaldo @username jumlah\natau reply ke pesan user lalu /setsaldo _ jumlah")
        return

    jumlah_str = context.args[1]
    if not jumlah_str.lstrip("-").isdigit():
        await update.message.reply_text("jumlah harus angka.")
        return

    jumlah = int(jumlah_str)

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        await init_wallet(target_user)
        await db_set_wallet(target_user.id, get_raw_name(target_user), jumlah)
        nama = await get_nama(target_user)
    else:
        username = context.args[0].lstrip("@")
        wallet = await db_get_wallet_by_any_name(f"@{username}")
        if not wallet:
            await update.message.reply_text(
                f"❌ @{username} tidak ditemukan.\n"
                f"coba reply ke pesan mereka langsung."
            )
            return
        await db_set_wallet(wallet["user_id"], wallet["name"], jumlah)
        nama = wallet["name"]

    await update.message.reply_text(
        f"✅ saldo {nama} diubah menjadi {format_rupiah(jumlah)}"
    )

async def addsaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ kamu bukan admin bot.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("gunakan: /addsaldo @username jumlah")
        return

    jumlah_str = context.args[1]
    if not jumlah_str.lstrip("-").isdigit():
        await update.message.reply_text("jumlah harus angka.")
        return

    tambahan = int(jumlah_str)

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        await init_wallet(target_user)
        wallet_data = await db_get_wallet(target_user.id)
        saldo = (wallet_data["saldo"] if wallet_data else 0) + tambahan
        await db_set_wallet(target_user.id, get_raw_name(target_user), saldo)
        nama = await get_nama(target_user)
    else:
        username = context.args[0].lstrip("@")
        wallet = await db_get_wallet_by_any_name(f"@{username}")
        if not wallet:
            await update.message.reply_text(
                f"❌ @{username} tidak ditemukan.\n"
                f"coba reply ke pesan mereka langsung."
            )
            return
        saldo = wallet["saldo"] + tambahan
        await db_set_wallet(wallet["user_id"], wallet["name"], saldo)
        nama = wallet["name"]

    await update.message.reply_text(
        f"✅ saldo {nama} ditambah {format_rupiah(tambahan)}.\n"
        f"saldo sekarang: {format_rupiah(saldo)}"
    )

async def setscore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ kamu bukan admin bot.")
        return

    if update.message.chat.type == "private":
        await update.message.reply_text("command ini hanya untuk grup.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("gunakan: /setscore @username jumlah")
        return

    jumlah_str = context.args[1]
    if not jumlah_str.lstrip("-").isdigit():
        await update.message.reply_text("jumlah harus angka.")
        return

    jumlah = int(jumlah_str)
    chat_id = update.message.chat_id

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        await db_set_score(chat_id, target_user.id, get_raw_name(target_user), jumlah)
        nama = await get_nama(target_user)
    else:
        username = context.args[0].lstrip("@")
        scores_dict = await db_get_scores(chat_id)
        found_uid = None
        found_name = None
        for uid, info in scores_dict.items():
            if info["name"].lower() == f"@{username.lower()}":
                found_uid = uid
                found_name = info["name"]
                break
        if not found_uid:
            await update.message.reply_text("user tidak ditemukan di papan skor grup ini.")
            return
        await db_set_score(chat_id, found_uid, found_name, jumlah)
        nama = found_name

    await update.message.reply_text(
        f"✅ skor {nama} di grup ini diubah menjadi {jumlah} poin."
    )

async def addscore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ kamu bukan admin bot.")
        return

    if update.message.chat.type == "private":
        await update.message.reply_text("command ini hanya untuk grup.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("gunakan: /addscore @username jumlah")
        return

    jumlah_str = context.args[1]
    if not jumlah_str.lstrip("-").isdigit():
        await update.message.reply_text("jumlah harus angka.")
        return

    tambahan = int(jumlah_str)
    chat_id = update.message.chat_id

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        scores_dict = await db_get_scores(chat_id)
        current = scores_dict.get(target_user.id, {}).get("score", 0)
        new_score = current + tambahan
        await db_set_score(chat_id, target_user.id, get_raw_name(target_user), new_score)
        nama = await get_nama(target_user)
    else:
        username = context.args[0].lstrip("@")
        scores_dict = await db_get_scores(chat_id)
        found_uid = None
        found_name = None
        for uid, info in scores_dict.items():
            if info["name"].lower() == f"@{username.lower()}":
                found_uid = uid
                found_name = info["name"]
                break
        if not found_uid:
            await update.message.reply_text("user tidak ditemukan di papan skor grup ini.")
            return
        current = scores_dict[found_uid]["score"]
        new_score = current + tambahan
        await db_set_score(chat_id, found_uid, found_name, new_score)
        nama = found_name

    await update.message.reply_text(
        f"✅ skor {nama} ditambah {tambahan} poin.\n"
        f"skor sekarang: {new_score}"
    )

