Ferrari Dice — bot.py

import asyncio
import logging
import random
import sqlite3
import uuid
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiocryptopay import AioCryptoPay, Networks
# ==========================================
# CONFIG
# ==========================================
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")
bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
crypto = AioCryptoPay(token=CRYPTOBOT_TOKEN, network=Networks.MAIN_NET)
logging.basicConfig(level=logging.INFO)
FAKE_ONLINE = random.randint(120, 450)
PVP_ROOMS = {}
# ==========================================
# DATABASE
# ==========================================
conn = sqlite3.connect("casino.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance REAL DEFAULT 0,
    total_deposit REAL DEFAULT 0,
    total_withdraw REAL DEFAULT 0
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS withdraws (
    id TEXT,
    user_id INTEGER,
    amount REAL,
    status TEXT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS checks (
    code TEXT,
    amount REAL,
    activations INTEGER,
    activated_by TEXT,
    required_deposit REAL DEFAULT 0
)
''')
conn.commit()
# ==========================================
# STATES
# ==========================================
class DepositState(StatesGroup):
    waiting_amount = State()
class WithdrawState(StatesGroup):
    waiting_amount = State()
class SupportState(StatesGroup):
    waiting_question = State()
class DiceState(StatesGroup):
    waiting_bet = State()
class MultiDiceState(StatesGroup):
    waiting_bet = State()
class AdminBalanceAdd(StatesGroup):
    waiting_user = State()
    waiting_amount = State()
class AdminBalanceRemove(StatesGroup):
    waiting_user = State()
    waiting_amount = State()
class CreateCheck(StatesGroup):
    waiting_activations = State()
    waiting_amount = State()
class CreateDepositCheck(StatesGroup):
    waiting_activations = State()
    waiting_amount = State()
    waiting_deposit = State()
# ==========================================
# HELPERS
# ==========================================
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()
def create_user(user_id, username):
    if not get_user(user_id):
        cursor.execute(
            "INSERT INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )
        conn.commit()
def get_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else 0
def add_balance(user_id, amount):
    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id=?",
        (amount, user_id),
    )
    conn.commit()
def remove_balance(user_id, amount):
    cursor.execute(
        "UPDATE users SET balance = balance - ? WHERE user_id=?",
        (amount, user_id),
    )
    conn.commit()
def add_deposit(user_id, amount):
    cursor.execute(
        "UPDATE users SET total_deposit = total_deposit + ? WHERE user_id=?",
        (amount, user_id),
    )
    conn.commit()
def add_withdraw(user_id, amount):
    cursor.execute(
        "UPDATE users SET total_withdraw = total_withdraw + ? WHERE user_id=?",
        (amount, user_id),
    )
    conn.commit()
def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🎮 Играть", callback_data="games")
    kb.button(text="👤 Профиль", callback_data="profile")
    kb.button(text="🛠 Поддержка", callback_data="support")
    kb.adjust(1)
    return kb.as_markup()
def games_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🎲 Dice x0-x4", callback_data="dice_game")
    kb.button(text="🎲 Произведение >18", callback_data="multi_game")
    kb.button(text="⚔️ PvP Dice", callback_data="pvp_game")
    kb.button(text="🔙 Назад", callback_data="back")
    kb.adjust(1)
    return kb.as_markup()
def profile_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Пополнить", callback_data="deposit")
    kb.button(text="💸 Вывод", callback_data="withdraw")
    kb.button(text="🎁 Активировать чек", callback_data="activate_check")
    kb.button(text="🔙 Назад", callback_data="back")
    kb.adjust(1)
    return kb.as_markup()
def admin_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🎁 Создать чек", callback_data="create_check")
    kb.button(text="💎 Депозитный чек", callback_data="create_dep_check")
    kb.button(text="➕ Пополнить баланс", callback_data="admin_add")
    kb.button(text="➖ Снять баланс", callback_data="admin_remove")
    kb.adjust(1)
    return kb.as_markup()
# ==========================================
# START
# ==========================================
@dp.message(Command("start"))
async def start(message: Message):
    create_user(message.from_user.id, message.from_user.username)
    text = f"""
🎲 <b>Добро пожаловать в Ferrari Dice</b>
⚡️ Моментальные пополнения
💸 Моментальные выводы
🔥 Красивые игры и быстрые выплаты
👥 Онлайн: <b>{FAKE_ONLINE}</b>
💎 Желаем удачи!
    """
    await message.answer(text, reply_markup=main_menu())
# ==========================================
# CALLBACKS
# ==========================================
@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 Главное меню",
        reply_markup=main_menu(),
    )
@dp.callback_query(F.data == "games")
async def games(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎮 Выберите игру",
        reply_markup=games_menu(),
    )
@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    text = f"""
👤 <b>Профиль</b>
🆔 ID: <code>{callback.from_user.id}</code>
👤 Username: @{callback.from_user.username}
💰 Баланс: <b>{user[2]:.2f}$</b>
💳 Депозитов: <b>{user[3]:.2f}$</b>
💸 Выведено: <b>{user[4]:.2f}$</b>
    """
    await callback.message.edit_text(text, reply_markup=profile_menu())
# ==========================================
# DEPOSIT
# ==========================================
@dp.callback_query(F.data == "deposit")
async def deposit(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DepositState.waiting_amount)
    await callback.message.answer("💳 Введите сумму пополнения:")
@dp.message(DepositState.waiting_amount)
async def deposit_amount(message: Message, state: FSMContext):
    amount = float(message.text)
    invoice = await crypto.create_invoice(
        asset="USDT",
        amount=amount,
        description="Ferrari Dice Deposit"
    )
    await message.answer(
        f"💳 Счёт создан\n\n💰 Сумма: {amount}$\n\n🔗 Оплатить: {invoice.bot_invoice_url}"
    )
    while True:
        invoices = await crypto.get_invoices(invoice_ids=invoice.invoice_id)
        if invoices.items[0].status == "paid":
            add_balance(message.from_user.id, amount)
            add_deposit(message.from_user.id, amount)
            await message.answer(f"✅ Баланс пополнен на {amount}$")
            break
        await asyncio.sleep(5)
    await state.clear()
# ==========================================
# WITHDRAW
# ==========================================
@dp.callback_query(F.data == "withdraw")
async def withdraw(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WithdrawState.waiting_amount)
    await callback.message.answer("💸 Введите сумму вывода:")
@dp.message(WithdrawState.waiting_amount)
async def withdraw_amount(message: Message, state: FSMContext):
    amount = float(message.text)
    balance = get_balance(message.from_user.id)
    if amount > balance:
        return await message.answer("❌ Недостаточно средств")
    remove_balance(message.from_user.id, amount)
    withdraw_id = str(uuid.uuid4())[:8]
    cursor.execute(
        "INSERT INTO withdraws VALUES (?, ?, ?, ?)",
        (withdraw_id, message.from_user.id, amount, "pending")
    )
    conn.commit()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"accept_{withdraw_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"decline_{withdraw_id}"
                )
            ]
        ]
    )
    await bot.send_message(
        ADMIN_ID,
        f"💸 Новый вывод\n\n👤 @{message.from_user.username}\n💰 {amount}$",
        reply_markup=kb
    )
    await message.answer("⏳ Заявка отправлена администрации")
    await state.clear()
@dp.callback_query(F.data.startswith("accept_"))
async def accept_withdraw(callback: CallbackQuery):
    withdraw_id = callback.data.split("_")[1]
    cursor.execute("SELECT * FROM withdraws WHERE id=?", (withdraw_id,))
    data = cursor.fetchone()
    if not data:
        return
    add_withdraw(data[1], data[2])
    cursor.execute(
        "UPDATE withdraws SET status='accepted' WHERE id=?",
        (withdraw_id,)
    )
    conn.commit()
    await bot.send_message(
        data[1],
        f"✅ Ваш вывод {data[2]}$ подтверждён"
    )
    await callback.message.edit_text("✅ Вывод подтвержден")
@dp.callback_query(F.data.startswith("decline_"))
async def decline_withdraw(callback: CallbackQuery):
    withdraw_id = callback.data.split("_")[1]
    cursor.execute("SELECT * FROM withdraws WHERE id=?", (withdraw_id,))
    data = cursor.fetchone()
    if not data:
        return
    add_balance(data[1], data[2])
    cursor.execute(
        "UPDATE withdraws SET status='declined' WHERE id=?",
        (withdraw_id,)
    )
    conn.commit()
    await bot.send_message(
        data[1],
        f"❌ Ваш вывод {data[2]}$ отклонён"
    )
    await callback.message.edit_text("❌ Вывод отклонён")
# ==========================================
# SUPPORT
# ==========================================
@dp.callback_query(F.data == "support")
async def support(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportState.waiting_question)
    await callback.message.answer(
        "🛠 Введите вопрос администрации"
    )
@dp.message(SupportState.waiting_question)
async def support_question(message: Message, state: FSMContext):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Ответить",
                    callback_data=f"reply_{message.from_user.id}"
                )
            ]
        ]
    )
    await bot.send_message(
        ADMIN_ID,
        f"📩 Пользователь @{message.from_user.username} пишет:\n\n{message.text}",
        reply_markup=kb
    )
    await message.answer("✅ Сообщение отправлено")
    await state.clear()
# ==========================================
# GAME 1
# ==========================================
@dp.callback_query(F.data == "dice_game")
async def dice_game(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DiceState.waiting_bet)
    await callback.message.answer("🎲 Введите ставку:")
@dp.message(DiceState.waiting_bet)
async def dice_play(message: Message, state: FSMContext):
    bet = float(message.text)
    balance = get_balance(message.from_user.id)
    if bet > balance:
        return await message.answer("❌ Недостаточно средств")
    remove_balance(message.from_user.id, bet)
    dice = random.randint(1, 6)
    if dice in [1, 2]:
        text = f"🎲 Выпало {dice}\n\n❌ Проигрыш"
    elif dice in [3, 4]:
        win = bet * 2
        add_balance(message.from_user.id, win)
        text = f"🎲 Выпало {dice}\n\n✅ Победа x2\n💰 Вы выиграли {win}$"
    else:
        win = bet * 4
        add_balance(message.from_user.id, win)
        text = f"🎲 Выпало {dice}\n\n🔥 JACKPOT x4\n💰 Вы выиграли {win}$"
    await message.answer(text)
    await state.clear()
# ==========================================
# GAME 2
# ==========================================
@dp.callback_query(F.data == "multi_game")
async def multi_game(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MultiDiceState.waiting_bet)
    await callback.message.answer("🎲 Введите ставку:")
@dp.message(MultiDiceState.waiting_bet)
async def multi_play(message: Message, state: FSMContext):
    bet = float(message.text)
    balance = get_balance(message.from_user.id)
    if bet > balance:
        return await message.answer("❌ Недостаточно средств")
    remove_balance(message.from_user.id, bet)
    d1 = random.randint(1, 6)
    d2 = random.randint(1, 6)
    result = d1 * d2
    if result > 18:
        win = bet * 5
        add_balance(message.from_user.id, win)
        text = f"""
🎲 Первый кубик: {d1}
🎲 Второй кубик: {d2}
🧮 Произведение: {result}
🔥 Победа x5
💰 Выигрыш: {win}$
        """
    else:
        text = f"""
🎲 Первый кубик: {d1}
🎲 Второй кубик: {d2}
🧮 Произведение: {result}
❌ Проигрыш
        """
    await message.answer(text)
    await state.clear()
# ==========================================
# ADMIN PANEL
# ==========================================
@dp.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "👑 Админ панель",
        reply_markup=admin_menu()
    )
# ==========================================
# CREATE CHECK
# ==========================================
@dp.callback_query(F.data == "create_check")
async def create_check(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(CreateCheck.waiting_activations)
    await callback.message.answer("Введите количество активаций")
@dp.message(CreateCheck.waiting_activations)
async def check_activations(message: Message, state: FSMContext):
    await state.update_data(activations=int(message.text))
    await state.set_state(CreateCheck.waiting_amount)
    await message.answer("Введите сумму")
@dp.message(CreateCheck.waiting_amount)
async def check_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    code = str(uuid.uuid4())[:10]
    cursor.execute(
        "INSERT INTO checks VALUES (?, ?, ?, ?, ?)",
        (code, float(message.text), data['activations'], "", 0)
    )
    conn.commit()
    await message.answer(
        f"🎁 Чек создан\n\n/start check_{code}"
    )
    await state.clear()
# ==========================================
# ACTIVATE CHECK
# ==========================================
@dp.message(F.text.startswith("/start check_"))
async def activate_check(message: Message):
    code = message.text.split("check_")[1]
    cursor.execute("SELECT * FROM checks WHERE code=?", (code,))
    check = cursor.fetchone()
    if not check:
        return await message.answer("❌ Чек не найден")
    activated = check[3].split(",") if check[3] else []
    if str(message.from_user.id) in activated:
        return await message.answer("❌ Вы уже активировали чек")
    if check[2] <= 0:
        return await message.answer("❌ Активации закончились")
    if get_user(message.from_user.id)[3] < check[4]:
        return await message.answer(
            f"❌ Нужно депозитов минимум {check[4]}$"
        )
    activated.append(str(message.from_user.id))
    cursor.execute(
        "UPDATE checks SET activations=?, activated_by=? WHERE code=?",
        (check[2] - 1, ",".join(activated), code)
    )
    conn.commit()
    add_balance(message.from_user.id, check[1])
    await message.answer(
        f"🎉 Вы получили {check[1]}$"
    )
# ==========================================
# PVP GAME
# ==========================================
@dp.callback_query(F.data == "pvp_game")
async def pvp_game(callback: CallbackQuery):
    room_id = str(uuid.uuid4())[:6]
    PVP_ROOMS[room_id] = {
        "creator": callback.from_user.id,
        "creator_name": callback.from_user.username,
    }
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚔️ Присоединиться",
                    callback_data=f"joinpvp_{room_id}"
                )
            ]
        ]
    )
    await callback.message.answer(
        f"⚔️ PvP комната создана\n\n👤 Создатель: @{callback.from_user.username}\n🆔 Комната: {room_id}",
        reply_markup=kb
    )
@dp.callback_query(F.data.startswith("joinpvp_"))
async def join_pvp(callback: CallbackQuery):
    room_id = callback.data.split("_")[1]
    if room_id not in PVP_ROOMS:
        return await callback.answer("Комната не найдена", show_alert=True)
    room = PVP_ROOMS[room_id]
    if callback.from_user.id == room['creator']:
        return await callback.answer("Нельзя играть против себя", show_alert=True)
    p1 = random.randint(1, 6)
    p2 = random.randint(1, 6)
    if p1 > p2:
        winner = room['creator_name']
    elif p2 > p1:
        winner = callback.from_user.username
    else:
        winner = "Ничья"
    text = f"""
⚔️ PvP Dice
🎲 @{room['creator_name']} выбил: {p1}
🎲 @{callback.from_user.username} выбил: {p2}
🏆 Победитель: {winner}
    """
    await callback.message.edit_text(text)
    del PVP_ROOMS[room_id]
# ==========================================
# BONUS FEATURES
# ==========================================
@dp.message(Command("balance"))
async def balance_cmd(message: Message):
    bal = get_balance(message.from_user.id)
    await message.answer(f"💰 Ваш баланс: {bal}$")
@dp.message(Command("top"))
async def top_players(message: Message):
    cursor.execute(
        "SELECT username, total_deposit FROM users ORDER BY total_deposit DESC LIMIT 10"
    )
    users = cursor.fetchall()
    text = "🏆 ТОП ИГРОКОВ\n\n"
    for i, user in enumerate(users, start=1):
        text += f"{i}. @{user[0]} — {user[1]}$\n"
    await message.answer(text)
# ==========================================
# RUN
# ==========================================
async def main():
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())

Установка

pip install aiogram aiocryptopay

Переменные окружения (Bothost.ru)

Создай переменные:

BOT_TOKEN=токен_бота
ADMIN_ID=твой_telegram_id
CRYPTOBOT_TOKEN=токен_cryptobot

Установка

pip install aiogram aiocryptopay

Запуск

python bot.py

Что уже есть

✅ PvP Dice игры
✅ Fake Online
✅ Красивое меню ✅ Профиль ✅ Пополнение через CryptoBot ✅ Вывод заявками ✅ Поддержка ✅ Dice x0-x4 ✅ Произведение >18 ✅ Чеки ✅ Депозитные чеки ✅ Админка ✅ Топ игроков ✅ SQLite база ✅ Анти-двойная активация чеков

Что можно потом добавить

* Рефералка
* PvP игры
* Джекпот комната
* Crash game
* Рулетка
* Fake online
* Логи в канал
* Web admin panel
* Postgres
* Docker
