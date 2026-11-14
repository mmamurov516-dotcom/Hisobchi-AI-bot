import asyncio
import logging
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from config import BOT_TOKEN
from database import init_db
from handlers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def handle_ping(request):
    """Render va cron-job.org uchun health-check endpoint"""
    return web.Response(
        text="Hisobchi AI Bot is running! Status: 200 OK",
        status=200
    )

async def start_web_server():
    """Render Web Service talab qiladigan HTTP serverni ishga tushirish"""
    port = int(os.getenv("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    app.router.add_get("/ping", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Render HTTP Web Server {port}-portda muvaffaqiyatli ishga tushdi!")
    return runner

async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="balans", description="Mening hisobim va qolgan pul"),
        BotCommand(command="xarajatlar", description="Nimaga qancha sarflandi"),
        BotCommand(command="bekor", description="Oxirgi yozuvni bekor qilish"),
        BotCommand(command="tozalash", description="Hisobni tozalash"),
        BotCommand(command="yordam", description="Botdan foydalanish qo'llanmasi"),
    ]
    await bot.set_my_commands(commands)

async def main():
    logger.info("Ma'lumotlar bazasi ishga tushirilmoqda...")
    await init_db()

    # Render va cron-job.org uchun HTTP serverni fonda ishga tushiramiz
    web_runner = await start_web_server()

    bot = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot_instance = Bot(token=BOT_TOKEN, default=bot)
    dp = Dispatcher()
    dp.include_router(router)

    await setup_bot_commands(bot_instance)
    
    bot_info = await bot_instance.get_me()
    logger.info(f"Hisobchi bot (@{bot_info.username}) muvaffaqiyatli ishga tushdi!")

    try:
        await bot_instance.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot_instance)
    finally:
        await bot_instance.session.close()
        await web_runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
