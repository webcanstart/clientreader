import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import BaseFilter
from aiohttp import web

TOKEN = "8609045969:AAE9iBwu5tDNJEtuFY6_5Bn36ExnevaE-kQ"
GROUP_ID = -5144682306
TARGET_BOT_USERNAME = "sanitaclinicfrombot"
DATA_FILE = "leads.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()

class FromSpecificBotFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        if message.chat.id != GROUP_ID:
            return False
        if message.from_user and message.from_user.username == TARGET_BOT_USERNAME:
            return True
        return False

def parse_lead_text(text: str) -> dict:
    lines = text.strip().split("\n")
    form_name = lines[0].strip() if lines else "Невідома форма"
    name, phone, email = None, None, None

    for line in lines:
        if "ім" in line.lower() and ":" in line:
            name = line.split(":", 1)[1].strip()
        elif " телефон" in line.lower() and ":" in line:
            phone = line.split(":", 1)[1].strip()
        elif "email" in line.lower() or "пошт" in line.lower():
            if ":" in line:
                email = line.split(":", 1)[1].strip()

    return {"form_name": form_name, "name": name, "phone": phone, "email": email}

@dp.message(FromSpecificBotFilter())
async def save_lead_handler(message: types.Message):
    lead_text = message.text or message.caption
    if not lead_text:
        return

    parsed_data = parse_lead_text(lead_text)
    lead_entry = {
        "date": str(message.date),
        "form_name": parsed_data["form_name"],
        "name": parsed_data["name"],
        "phone": parsed_data["phone"],
        "email": parsed_data["email"],
        "raw_message": lead_text
    }

    data = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []

    data.append(lead_entry)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Заглушка вебсервера для безкоштовного тарифу Render
async def handle(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    # Запускаємо вебсервер і телеграм-бота паралельно
    await web_server()
    print("Бот-слухач та вебсервер запущені...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())