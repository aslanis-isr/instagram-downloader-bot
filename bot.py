import asyncio
import os
import re
from pathlib import Path

import yt_dlp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile


TOKEN = os.getenv("BOT_TOKEN")

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

dp = Dispatcher()


def is_instagram_url(text):
    pattern = r"https?://(www\.)?instagram\.com/(reel|reels|p|tv)/[^\s]+"
    return bool(re.search(pattern, text))


def download_video(url):
    output = str(DOWNLOAD_DIR / "%(id)s.%(ext)s")

    options = {
        "outtmpl": output,
        "format": "best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])

    files = list(DOWNLOAD_DIR.iterdir())

    if not files:
        raise Exception("Видео не найдено")

    return files[0]


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🎬 Добро пожаловать!\n\n"
        "Я бесплатный бот для скачивания "
        "публичных видео из Instagram.\n\n"
        "📥 Просто отправьте мне ссылку на Reel."
    )


@dp.message(F.text)
async def get_video(message: Message):

    url = message.text.strip()

    if not is_instagram_url(url):
        await message.answer(
            "❌ Отправьте корректную ссылку Instagram.\n\n"
            "Например:\n"
            "https://www.instagram.com/reel/XXXXXXXX/"
        )
        return

    status = await message.answer("⏳ Скачиваю видео...")

    try:

        file_path = await asyncio.to_thread(
            download_video,
            url
        )

        if not file_path.exists():
            raise Exception("Файл не найден")

        if file_path.stat().st_size > 50 * 1024 * 1024:
            await status.edit_text(
                "❌ Видео слишком большое для отправки."
            )
            file_path.unlink(missing_ok=True)
            return

        await status.edit_text("📤 Отправляю видео...")

        video = FSInputFile(file_path)

        await message.answer_video(
            video=video,
            caption="✅ Готово!"
        )

        file_path.unlink(missing_ok=True)

        await status.delete()

    except Exception as error:

        print("ERROR:", error)

        await status.edit_text(
            "❌ Не удалось скачать видео.\n\n"
            "Проверьте ссылку и убедитесь, "
            "что публикация открытая."
        )


async def main():

    if not TOKEN:
        raise RuntimeError(
            "Не найден BOT_TOKEN"
        )

    bot = Bot(TOKEN)

    print("🤖 Бот запущен!")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
