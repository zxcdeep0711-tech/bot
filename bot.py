import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "8565167626:AAFp0SOX5AQS80GBg78Gufb9Y0AUbn5wyzY"  # Получите у @BotFather
ADMIN_ID = 8837634730  # Ваш Telegram ID (узнать можно у @userinfobot)
# =============================================

applications_enabled = True

class Form(StatesGroup):
    nick = State()
    age = State()
    hours = State()
    experience = State()
    cheats_mods = State()
    role = State()
    why_you = State()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def get_main_keyboard(user_id: int):
    buttons = [[KeyboardButton(text="📝 Заполнить анкету")]]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="⚙️ Настройки")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_admin_settings_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Включить анкеты", callback_data="enable_apps")],
            [InlineKeyboardButton(text="🔴 Отключить анкеты", callback_data="disable_apps")]
        ]
    )

def get_decision_keyboard(applicant_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"accept_{applicant_id}"),
                InlineKeyboardButton(text="❌ Отказать", callback_data=f"reject_{applicant_id}")
            ]
        ]
    )

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}! Выберите действие:",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@dp.message(F.text == "⚙️ Настройки")
async def admin_settings(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    status_str = "включен" if applications_enabled else "отключен"
    await message.answer(
        f"⚙️ **Панель управления настройками**\nТекущий статус приема анкет: **{status_str}**",
        reply_markup=get_admin_settings_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.in_({"enable_apps", "disable_apps"}))
async def toggle_applications(callback: types.CallbackQuery):
    global applications_enabled
    if callback.from_user.id != ADMIN_ID:
        return
    if callback.data == "enable_apps":
        applications_enabled = True
        await callback.message.edit_text("✅ Прием анкет успешно **ВКЛЮЧЕН**.", parse_mode="Markdown")
    else:
        applications_enabled = False
        await callback.message.edit_text("🔴 Прием анкет успешно **ОТКЛЮЧЕН**.", parse_mode="Markdown")
    await callback.answer()

# --- СТАРТ ЗАПОЛНЕНИЯ АНКЕТЫ ---
@dp.message(F.text == "📝 Заполнить анкету")
async def start_form(message: types.Message, state: FSMContext):
    if not applications_enabled:
        await message.answer(
            "Здравствуйте! Набор на пост Администратора закрыт временно, в скором времени откроют. "
            "Все вопросы в чате канала."
        )
        return

    await state.set_state(Form.nick)
    msg = await message.answer("1. Ваш ник:")
    # Сохраняем ID сообщения с вопросом, чтобы потом удалить
    await state.update_data(last_bot_msg=msg.message_id)

# Функция для обработки шагов с очисткой сообщений
async def process_next_step(message: types.Message, state: FSMContext, next_state: State, next_text: str, data_key: str):
    data = await state.get_data()
    
    # Сохраняем ответ пользователя
    await state.update_data({data_key: message.text})
    
    # Удаляем сообщение пользователя и предыдущий вопрос бота для чистоты чата
    try:
        await message.delete()
        await bot.delete_message(chat_id=message.chat.id, message_id=data.get('last_bot_msg'))
    except Exception:
        pass

    # Отправляем новый вопрос и сохраняем его ID
    msg = await message.answer(next_text)
    await state.set_state(next_state)
    await state.update_data(last_bot_msg=msg.message_id)

@dp.message(Form.nick)
async def process_nick(message: types.Message, state: FSMContext):
    await process_next_step(message, state, Form.age, "2. Ваш возраст:", "nick")

@dp.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
    await process_next_step(message, state, Form.hours, "3. Сколько часов в день готовы уделять проекту?", "age")

@dp.message(Form.hours)
async def process_hours(message: types.Message, state: FSMContext):
    await process_next_step(message, state, Form.experience, "4. Был ли опыт администрирования? (Да/Нет, если да — где)", "hours")

@dp.message(Form.experience)
async def process_experience(message: types.Message, state: FSMContext):
    await process_next_step(message, state, Form.cheats_mods, "5. Разбираетесь ли в читах/модах (Fabric 1.21.x) и их настройке?", "experience")

@dp.message(Form.cheats_mods)
async def process_cheats_mods(message: types.Message, state: FSMContext):
    await process_next_step(message, state, Form.role, "6. Кем хотите быть? (Модератор чата / Хелпер по багам / Тестер сборок)", "cheats_mods")

@dp.message(Form.role)
async def process_role(message: types.Message, state: FSNContext if False else FSMContext):
    await process_next_step(message, state, Form.why_you, "7. Почему именно вы?", "role")

@dp.message(Form.why_you)
async def process_why_you(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # Удаляем последнее сообщение с ответом и последний вопрос бота
    try:
        await message.delete()
        await bot.delete_message(chat_id=message.chat.id, message_id=data.get('last_bot_msg'))
    except Exception:
        pass

    await state.clear()

    # Уведомляем пользователя
    await message.answer("Анкета Была Отправлена Владельцу. В скором времени анкету примут либо откажут.")

    # Красивое отображение юзернейма или имени (без надписи "без_юзернейма")
    user_identifier = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

    # Формируем сообщение для админа
    applicant_info = (
        f"📌 **Новая анкета!** (От: {user_identifier}, ID: `{message.from_user.id}`)\n\n"
        f"1. Ваш ник: {data['nick']}\n"
        f"2. Ваш возраст: {data['age']}\n"
        f"3. Сколько часов в день готовы уделять проекту? {data['hours']}\n"
        f"4. Был ли опыт администрирования?: {data['experience']}\n"
        f"5. Разбираетесь ли в читах/модах (Fabric 1.21.x)?: {data['cheats_mods']}\n"
        f"6. Кем хотите быть?: {data['role']}\n"
        f"7. Почему именно вы?: {message.text}"
    )

    # Отправляем владельцу
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=applicant_info,
        reply_markup=get_decision_keyboard(message.from_user.id)
    )

# --- РЕШЕНИЕ АДМИНА (ОДОБРИТЬ / ОТКАЗАТЬ) ---
@dp.callback_query(F.data.startswith(("accept_", "reject_")))
async def handle_decision(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    action, applicant_id = callback.data.split("_")
    applicant_id = int(applicant_id)

    if action == "accept":
        text_to_applicant = "Здравствуйте! Ваша Анкета Принята, в скором вам отпишет Владелец."
    else:
        text_to_applicant = "Здравствуйте! Ваша Анкета Отклонена. Удачи!"

    # Отправляем ответ кандидату
    try:
        await bot.send_message(chat_id=applicant_id, text=text_to_applicant)
    except Exception:
        pass

    # Удаляем анкету у администратора после принятия/отказа
    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.answer("Готово!")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())