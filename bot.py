import asyncio
import json
import os
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import BaseFilter

# Ваші дані
TOKEN = "8609045969:AAE9iBwu5tDNJEtuFY6_5Bn36ExnevaE-kQ"
GROUP_ID = -5144682306
TARGET_BOT_USERNAME = "sanitaclinicfrombot"

DATA_FILE = "leads.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Фільтр для перевірки, що повідомлення від потрібного бота і в потрібній групі
class FromSpecificBotFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        if message.chat.id != GROUP_ID:
            return False
        if message.from_user and message.from_user.username == TARGET_BOT_USERNAME:
            return True
        return False

def parse_lead_text(text: str) -> dict:
    """Парсить текст повідомлення від WPForms, витягуючи назву форми, ім'я, телефон та імейл"""
    lines = text.strip().split("\n")
    
    # Перший рядок зазвичай є назвою форми (наприклад, "Online Consultation")
    form_name = lines[0].strip() if lines else "Невідома форма"
    
    name = None
    phone = None
    email = None

    # Регулярні вирази для пошуку полів (гнучкі до регістру та пробілів)
    for line in lines:
        # Шукаємо ім'я (підтримує "Ім'я та Прізвище", "Ім’я" тощо)
        if "ім" in line.lower() and ":" in line:
            name = line.split(":", 1)[1].strip()
        # Шукаємо телефон
        elif " телефон" in line.lower() and ":" in line:
            phone = line.split(":", 1)[1].strip()
        # Шукаємо імейл
        elif "email" in line.lower() or "пошт" in line.lower():
            if ":" in line:
                email = line.split(":", 1)[1].strip()

    return {
        "form_name": form_name,
        "name": name,
        "phone": phone,
        "email": email
    }

@dp.message(FromSpecificBotFilter())
async def save_lead_handler(message: types.Message):
    lead_text = message.text or message.caption
    if not lead_text:
        return

    # Витягуємо структуровані дані
    parsed_data = parse_lead_text(lead_text)

    lead_entry = {
        "date": str(message.date),
        "form_name": parsed_data["form_name"],
        "name": parsed_data["name"],
        "phone": parsed_data["phone"],
        "email": parsed_data["email"],
        "raw_message": lead_text  # зберігаємо також оригінал на всякий випадок
    }

    # Читаємо існуючі дані з файлу
    data = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []

    # Додаємо новий запис
    data.append(lead_entry)

    # Зберігаємо назад у JSON-файл
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"Збережено нову заявку з форми: {parsed_data['form_name']}")

async def main():
    print("Бот-слухач запущено і чекає на заявки...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())