import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv("config/.env")
TOKEN=os.getenv("BOT_TOKEN")
WEBAPP_URL=os.getenv("WEBAPP_URL","")

async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    kb=[
      [InlineKeyboardButton("🌐 Web App",web_app=WebAppInfo(url=WEBAPP_URL))],
      [InlineKeyboardButton("💰 Balansim",callback_data="balance"),
       InlineKeyboardButton("📦 Faol buyurtmam",callback_data="active")],
      [InlineKeyboardButton("📜 Xaridlarim",callback_data="history"),
       InlineKeyboardButton("💬 Support",callback_data="support")]
    ]
    await update.message.reply_text("🎮 Game Top-Up\n\nBarcha xaridlar Web App orqali amalga oshiriladi.",reply_markup=InlineKeyboardMarkup(kb))

if __name__=="__main__":
    if not TOKEN: raise SystemExit("BOT_TOKEN config/.env da kiritilmagan")
    Application.builder().token(TOKEN).build().add_handler(CommandHandler("start",start))
    app=Application.builder().token(TOKEN).build(); app.add_handler(CommandHandler("start",start)); app.run_polling()
