import os
import asyncio
import aiosqlite
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

DB_NAME = "videos.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                file_id TEXT
            )
        """)
        await db.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات فعال است. یک ویدیو بفرست!")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video
    file_id = video.file_id

    await update.message.reply_text("اسم ویدیو را بفرست:")

    context.user_data["waiting_for_name"] = file_id

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "waiting_for_name" in context.user_data:
        name = update.message.text.strip()
        file_id = context.user_data["waiting_for_name"]

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO videos (name, file_id) VALUES (?, ?)", (name, file_id))
            await db.commit()

        await update.message.reply_text("ذخیره شد.")
        del context.user_data["waiting_for_name"]

    else:
        await update.message.reply_text("برای دیدن لیست، بزن: /list")

async def list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, name FROM videos")
        rows = await cursor.fetchall()

    if not rows:
        await update.message.reply_text("هیچ ویدیویی ذخیره نشده.")
        return

    keyboard = []
    for row in rows:
        vid_id, name = row
        keyboard.append([InlineKeyboardButton(name, callback_data=str(vid_id))])

    await update.message.reply_text("انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    video_id = int(query.data)

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT file_id FROM videos WHERE id = ?", (video_id,))
        row = await cursor.fetchone()

    if not row:
        await query.edit_message_text("پیدا نشد.")
        return

    sent_msg = await query.message.reply_video(video=row[0])

    await asyncio.sleep(55)
    try:
        await sent_msg.delete()
    except:
        pass

async def main():
    await init_db()

        app = ApplicationBuilder().token(os.environ['8598664221:AAGcvlMYKZ9UIic8YNhsWlueJyW0hg1Td6I']).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_videos))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT, handle_text))
    app.add_handler(CallbackQueryHandler(send_video))

    print("Bot is running on Render...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
