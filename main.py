import requests
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

API_KEY = '860230fe5d3b8ba07645e976d1746ccc'  # Ваш ключ OpenWeatherMap
EXCHANGE_RATE_API_KEY = 'f859da0d4e8c7dd76865f71a'  # Ваш ключ Exchange Rate API
NEWS_API_KEY = 'd667922810c746c6886a0ce64e757781'  # Ваш ключ NewsAPI
BOT_TOKEN = '7505400129:AAH0vuXtjpQbCxjDc55KcPlyo5ukvajnwHw'

# Логин и пароль администратора
ADMIN_LOGIN = "admin"  # Меняйте логин здесь
ADMIN_PASSWORD = "password123"  # Меняйте пароль здесь

# Фиктивные данные об оружии Украины
WEAPONS_DATA = {
    'tank': {
        'name': 'Танк Т-84',
        'description': (
            "Танк Т-84 — современный основной боевой танк Украины. Разработан на базе советского танка Т-80УД. "
            "Обладает улучшенной бронезащитой, современными системами управления огнём и мощным двигателем."
        ),
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Strong_Europe_Tank_Challenge_2018_%2842054365704%29.jpg/1024px-Strong_Europe_Tank_Challenge_2018_%2842054365704%29.jpg'
    },
    'rifle': {
        'name': 'Винтовка Zbroyar Z-10',
        'description': (
            "Первые винтовки Z-10 были изготовлены в мае 2012 года. К началу весны 2014 года компания "
            "полностью обеспечивала себя ствольными коробками, затворными рамами и газовыми системами, "
            "но стволы к выпускаемому оружию являлись импортными. В связи с девальвацией гривны в 2014—2015 гг. "
            "стволы покупали небольшими партиями. После начала боевых действий на востоке Украины весной 2014 года "
            "компания активизировала сотрудничество с руководством государственных силовых структур Украины для участия в военных заказах."
        ),
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Zbroyar_Z-10_07.jpg/270px-Zbroyar_Z-10_07.jpg'
    },
    'missile': {
        'name': 'Ракетный комплекс «Стугна-П»',
        'description': (
            "«Скиф» — украинский противотанковый ракетный комплекс, разработанный украинской ОДКБ «Луч» в сотрудничестве с минской компанией ОАО «Пеленг». "
            "Ракета производится в Киеве на ГАХК «Артём», прибор наведения «ПН-С» — в Минске в ОАО «Пеленг». "
            "В ПТРК «Скиф» применена полуавтоматическая система наведения по лучу лазера. "
            "Обнаружение цели и наведение обеспечивается с помощью оптического и инфракрасного прицелов, "
            "что позволяет вести стрельбу в сложных погодных условиях. Особенностью ПТРК является возможность наведения ракеты на цель с закрытых позиций и укрытий. "
            "Другой отличительной чертой комплекса является траектория полёта ракеты: после пуска она летит над линией визирования (на высоте около 10 м) и снижается на уровень цели на конечном участке полёта. "
            "Лазерный луч при этом светит в хвост ракеты и только за долю секунды перед ударом переводится на цель."
        ),
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Skif_ATGM.jpg/274px-Skif_ATGM.jpg'
    },
    'drone': {
        'name': 'БПЛА «Фурия»',
        'description': (
            'Украинский беспилотный летательный аппарат, используемый для разведки. '
            'Фурія (БпАК А1-СМ «Фурія» UAS A1-CM “Furia”) — український безпілотний авіаційний комплекс розвідки та корегування вогню артилерії. '
            'Розроблений у 2014 році київським підприємством «Атлон Авіа». Станом на 2021 рік було вироблено понад 100 комплексів у різних модифікаціях '
            'для потреб Збройних Сил України, Національної гвардії України, Служби безпеки України. З 2014 року безпілотний авіаційний комплекс активно '
            'застосовувався в ході проведення Операції об’єднаних сил на сході України для ведення повітряної розвідки і корегування вогню артилерії. '
            'З 2015 року прийнятий на озброєння Національної гвардії. У 2019-2020 роках БпАК пройшов повний перелік Державних випробувань. '
            'Офіційно прийнятий на озброєння Збройних Сил України у 2020 році за наслідками успішних державних випробувань.'
        ),
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/ff/%D0%A4%D1%83%D1%80%D1%96%D1%8F_%D0%90%D0%A1%D0%9C130103.jpg/230px-%D0%A4%D1%83%D1%80%D1%96%D1%8F_%D0%90%D0%A1%D0%9C130103.jpg'
    }
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
url = f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook'

response = requests.get(url)
print(response.json())

class Registration(StatesGroup):
    name = State()
    password = State()

class AdminLogin(StatesGroup):
    login = State()
    password = State()

class ManageUsers(StatesGroup):
    select_user = State()
    confirm_action = State()

class CurrencyConversion(StatesGroup):
    waiting_for_currency_pair = State()
    waiting_for_amount = State()

@dp.message(Command("start"))
async def send_welcome(message: Message, state: FSMContext):
    conn = sqlite3.connect('basa.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   name TEXT, 
                   pass TEXT,
                   is_admin INTEGER DEFAULT 0,
                   chat_id INTEGER)''')
    conn.commit()
    cur.close()
    conn.close()

    await message.answer('Привет! Давайте зарегистрируем вас. Введите ваше имя:')
    await state.set_state(Registration.name)

@dp.message(Registration.name)
async def user_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer('Введите пароль:')
    await state.set_state(Registration.password)

@dp.message(Registration.password)
async def user_pass(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data['name']
    password = message.text.strip()

    conn = sqlite3.connect('basa.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, pass, chat_id) VALUES (?, ?, ?)", (name, password, message.chat.id))
    conn.commit()
    cur.close()
    conn.close()

    await state.clear()
    await show_main_menu(message.chat.id, 'Регистрация завершена! Выберите функцию:')

async def show_main_menu(chat_id, text):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Погода', callback_data='weather'), InlineKeyboardButton(text='Список пользователей', callback_data='users')],
        [InlineKeyboardButton(text='Конвертация валют', callback_data='currency_conversion'), InlineKeyboardButton(text='Новости', callback_data='news')],
        [InlineKeyboardButton(text='Изучение оружия', callback_data='weapons'), InlineKeyboardButton(text='Канал автора бота', callback_data='channel')],
        [InlineKeyboardButton(text='Админ панель', callback_data='admin_panel')],
        [InlineKeyboardButton(text='Помощь', callback_data='help')]
    ])
    await bot.send_message(chat_id, text, reply_markup=keyboard)

async def show_admin_menu(chat_id, text):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Управление пользователями', callback_data='manage_users')],
        [InlineKeyboardButton(text='В главное меню', callback_data='main_menu')]
    ])
    await bot.send_message(chat_id, text, reply_markup=keyboard)

async def get_back_to_menu_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='В главное меню', callback_data='main_menu')]
    ])

@dp.callback_query(lambda call: call.data == 'main_menu')
async def back_to_main_menu(call: types.CallbackQuery):
    await call.message.delete()
    await show_main_menu(call.message.chat.id, 'Выберите функцию:')

@dp.callback_query(lambda call: call.data == 'admin_panel')
async def admin_panel(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer('Введите логин администратора:')
    await state.set_state(AdminLogin.login)

@dp.message(AdminLogin.login)
async def admin_login(message: Message, state: FSMContext):
    if message.text.strip() == ADMIN_LOGIN:
        await state.update_data(admin_login=True)
        await message.answer('Введите пароль администратора:')
        await state.set_state(AdminLogin.password)
    else:
        await message.answer('Неверный логин. Попробуйте снова.')

@dp.message(AdminLogin.password)
async def admin_password(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get('admin_login') and message.text.strip() == ADMIN_PASSWORD:
        await message.answer('Добро пожаловать в админ панель!')
        await show_admin_menu(message.chat.id, 'Админ панель:')
        await state.clear()
    else:
        await message.answer('Неверный пароль. Попробуйте снова.')
        await state.set_state(AdminLogin.login)

@dp.callback_query(lambda call: call.data == 'manage_users')
async def manage_users(call: types.CallbackQuery, state: FSMContext):
    conn = sqlite3.connect('basa.db')
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()

    if users:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=user[1], callback_data=f'user_{user[0]}')] for user in users
        ] + [[InlineKeyboardButton(text='В главное меню', callback_data='main_menu')]])
        await call.message.answer('Выберите пользователя для управления:', reply_markup=keyboard)
        await state.set_state(ManageUsers.select_user)
    else:
        await call.message.answer('Нет зарегистрированных пользователей.', reply_markup=await get_back_to_menu_button())

@dp.callback_query(lambda call: call.data.startswith('user_'))
async def select_user(call: types.CallbackQuery, state: FSMContext):
    user_id = int(call.data.split('_')[1])
    await state.update_data(selected_user_id=user_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Удалить пользователя', callback_data='delete_user')],
        [InlineKeyboardButton(text='Забанить пользователя', callback_data='ban_user')],
        [InlineKeyboardButton(text='Назад', callback_data='manage_users')]
    ])
    await call.message.answer('Выберите действие с пользователем:', reply_markup=keyboard)
    await state.set_state(ManageUsers.confirm_action)

@dp.callback_query(lambda call: call.data in ['delete_user', 'ban_user'])
async def confirm_user_action(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['selected_user_id']

    if call.data == 'delete_user':
        conn = sqlite3.connect('basa.db')
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        await call.message.answer('Пользователь удален.', reply_markup=await get_back_to_menu_button())
    elif call.data == 'ban_user':
        await call.message.answer('Пользователь забанен.', reply_markup=await get_back_to_menu_button())

    await state.clear()

@dp.callback_query(lambda call: call.data == 'weather')
async def get_weather(call: types.CallbackQuery):
    await call.message.answer('Введите название города:', reply_markup=await get_back_to_menu_button())
    dp.message.register(fetch_weather)

async def fetch_weather(message: Message):
    city = message.text.strip()
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru'

    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверяем наличие ошибок HTTP
        data = response.json()

        # Проверяем наличие данных о погоде в ответе
        if 'main' in data and 'weather' in data:
            temp = data['main']['temp']
            description = data['weather'][0]['description']
            await message.answer(f"Погода в {city}:\nТемпература: {temp}°C\nОписание: {description.capitalize()}")
        else:
            await message.answer(f"Не удалось получить данные о погоде для города {city}. Пожалуйста, проверьте название города и попробуйте снова.")
    except requests.exceptions.HTTPError as http_err:
        await message.answer(f"Ошибка HTTP: {http_err}. Пожалуйста, попробуйте снова.")
    except Exception as err:
        await message.answer(f"Произошла ошибка: {err}. Пожалуйста, попробуйте снова.")

@dp.callback_query(lambda call: call.data == 'users')
async def show_users(call: types.CallbackQuery):
    conn = sqlite3.connect('basa.db')
    cur = conn.cursor()
    cur.execute("SELECT name FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()

    if users:
        user_list = "\n".join([user[0] for user in users])
        await call.message.answer(f"Список пользователей:\n{user_list}", reply_markup=await get_back_to_menu_button())
    else:
        await call.message.answer("Нет зарегистрированных пользователей.", reply_markup=await get_back_to_menu_button())

@dp.callback_query(lambda call: call.data == 'currency_conversion')
async def convert_currency(call: types.CallbackQuery, state: FSMContext):
    await show_currency_pairs(call.message.chat.id, 'Выберите валютную пару:')
    await state.set_state(CurrencyConversion.waiting_for_currency_pair)

async def show_currency_pairs(chat_id, text):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='USD/EUR', callback_data='USD/EUR'), InlineKeyboardButton(text='EUR/USD', callback_data='EUR/USD')],
        [InlineKeyboardButton(text='USD/UAH', callback_data='USD/UAH'), InlineKeyboardButton(text='UAH/USD', callback_data='UAH/USD')],
        [InlineKeyboardButton(text='RUB/UAH', callback_data='RUB/UAH'), InlineKeyboardButton(text='UAH/RUB', callback_data='UAH/RUB')],
        [InlineKeyboardButton(text='В главное меню', callback_data='main_menu')]
    ])
    await bot.send_message(chat_id, text, reply_markup=keyboard)

@dp.callback_query(lambda call: call.data in ['USD/EUR', 'EUR/USD', 'USD/UAH', 'UAH/USD', 'RUB/UAH', 'UAH/RUB'])
async def process_currency_pair(call: types.CallbackQuery, state: FSMContext):
    currency_pair = call.data
    from_currency, to_currency = currency_pair.split('/')
    await state.update_data(from_currency=from_currency, to_currency=to_currency)
    await call.message.answer(f'Вы выбрали {from_currency}/{to_currency}. Введите сумму для конвертации:', reply_markup=await get_back_to_menu_button())
    await state.set_state(CurrencyConversion.waiting_for_amount)

@dp.message(CurrencyConversion.waiting_for_amount)
async def process_conversion(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        data = await state.get_data()
        from_currency = data['from_currency']
        to_currency = data['to_currency']

        url = f'https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/pair/{from_currency}/{to_currency}/{amount}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            conversion_result = data.get('conversion_result')
            if conversion_result:
                await message.answer(f'{amount} {from_currency} = {conversion_result:.2f} {to_currency}')
            else:
                await message.answer('Не удалось выполнить конвертацию. Проверьте введенные данные.')
        else:
            await message.answer('Ошибка при запросе к API. Попробуйте позже.')
    except ValueError:
        await message.answer('Ошибка: введите корректное числовое значение для суммы.')
    except Exception as e:
        await message.answer(f'Ошибка: {str(e)}')

    await state.clear()
    await show_main_menu(message.chat.id, 'Конвертация завершена!')

@dp.callback_query(lambda call: call.data == 'news')
async def get_news(call: types.CallbackQuery):
    url = f'https://newsapi.org/v2/top-headlines?country=ru&apiKey={NEWS_API_KEY}'
    try:
        response = requests.get(url)
        data = response.json()

        if data['status'] == 'ok' and data['totalResults'] > 0:
            news_list = data['articles'][:5]
            news_message = "Последние новости:\n"
            for news in news_list:
                news_message += f"\n- {news['title']} ({news['source']['name']})\n{news['url']}\n"
            await call.message.answer(news_message, reply_markup=await get_back_to_menu_button())
        else:
            await call.message.answer("Не удалось получить новости. Попробуйте позже.", reply_markup=await get_back_to_menu_button())
    except Exception as e:
        await call.message.answer(f"Произошла ошибка при получении новостей: {str(e)}", reply_markup=await get_back_to_menu_button())

@dp.callback_query(lambda call: call.data == 'weapons')
async def show_weapons_menu(call: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Танк', callback_data='weapon_tank')],
        [InlineKeyboardButton(text='Винтовка', callback_data='weapon_rifle')],
        [InlineKeyboardButton(text='Ракетный комплекс', callback_data='weapon_missile')],
        [InlineKeyboardButton(text='БПЛА', callback_data='weapon_drone')],
        [InlineKeyboardButton(text='В главное меню', callback_data='main_menu')]
    ])
    await call.message.answer('Выберите оружие для изучения:', reply_markup=keyboard)

@dp.callback_query(lambda call: call.data.startswith('weapon_'))
async def show_weapon_info(call: types.CallbackQuery):
    weapon_key = call.data.split('_')[1]
    weapon = WEAPONS_DATA.get(weapon_key)

    if weapon:
        name = weapon['name']
        description = weapon['description']
        image_url = weapon['image_url']

        message_text = f"**{name}**\n\n{description}"

        await call.message.answer_photo(photo=image_url, caption=message_text, reply_markup=await get_back_to_menu_button())
    else:
        await call.message.answer("Информация об этом оружии недоступна.", reply_markup=await get_back_to_menu_button())

@dp.callback_query(lambda call: call.data == 'channel')
async def send_channel_link(call: types.CallbackQuery):
    await call.message.answer('Переходите на канал автора бота: https://www.tiktok.com/@game.ps.5?_t=8oyNFkAjw1e&_r=1',
                              reply_markup=await get_back_to_menu_button())

@dp.callback_query(lambda call: call.data == 'help')
async def show_help(call: types.CallbackQuery):
    await call.message.answer("Бот предоставляет информацию о погоде, новостях, конвертации валют и изучении оружия Украины.\n\n"
        "🛠️ **Технологии**: Бот написан на Python с использованием библиотеки Aiogram для взаимодействия с Telegram API. "
        "Для хранения данных используется SQLite, а для получения данных о погоде и новостей — OpenWeatherMap и NewsAPI.\n\n"
        "👨‍💻 **Создатель**: Виталий Поворознюк. Вы можете найти его канал на TikTok: https://www.tiktok.com/@game.ps.5.\n\n"
        "Если у вас есть вопросы или предложения, обращайтесь на канал автора или используйте другие доступные способы связи.", reply_markup=await get_back_to_menu_button())

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
