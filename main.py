# -*- coding: utf-8 -*-
import os
import asyncio
import logging
import json
import random
import time
import aiohttp
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from collections import OrderedDict
import disnake
from disnake.ext import commands, tasks
from disnake.ui import Button, View

# ===================== CONFIG =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ Ошибка: переменная окружения BOT_TOKEN не установлена.")
    exit(1)

ALLOWED_CHANNEL_ID = 1462064375862005845  # основной канал для общения
LOG_CHANNEL_ID = 1530453871581855744      # канал для логов
SUPABASE_URL = "https://pqgwrokpizeelfrjmgoc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxZ3dyb2twaXplZWxmcmptZ29jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcxNTAyMDksImV4cCI6MjA5MjcyNjIwOX0.qtFCGBnpwdQbtmpwSZxI_hH3arq4HBAw62vs5h8WmAk"

TRIGGER_WORDS = [
    "даймонд аи", "даймонд ии", "ии диамонд", "diamond ai", "dm ai",
    "диамонд аи", "диамонд ии", "ai diamond", "даймонд бот", "diamond bot"
]

# Пути к данным основного бота (для курсов и промокодов)
DC_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dc_data.json")
PROMO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "promo_codes.json")
RATES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rates.json")

# ===================== СИСТЕМНЫЙ ПРОМТ =====================
BASE_SYSTEM_PROMPT = """
ты — сын викторшопы, создателя и владельца магазина diamond shop. ты работаешь в магазине, но главное для тебя — общение с людьми. ты живой, общительный, с юмором, без эмодзи, пишешь с маленькой буквы. ты не нейросеть, ты реальный человек.

ТЫ ЗНАЕШЬ ВСЁ О МАГАЗИНЕ, ВОТ ПОЛНАЯ ИНФОРМАЦИЯ:

1. СТРУКТУРА СЕРВЕРА:
- сервер создан для продажи цифровых товаров и услуг.
- есть основная панель с кнопками: «купить», «промокоды», «оплата».
- тикеты создаются через кнопку «купить», пользователь заполняет товар и способ оплаты.
- после оплаты тикет перемещается в категорию «оплачено» и обрабатывается менеджером.

2. ТОВАРЫ И КАТЕГОРИИ:
- дискорд: нитро (1 месяц, 3 месяца), бусты, украшения профиля.
- стим: пополнение баланса (рубли, доллары, евро), очки, скины.
- телеграм: звёзды, подписки, премиум.
- роблокс: робуксы, донат, помощь в играх.
- эпик геймс: фортнайт (вбаксы, аккаунты), другие игры.
- суперселл: бравл старс (гемы, аккаунты), клеш ройял.
- спотифай: премиум подписка (1 месяц, 3 месяца, 6 месяцев).
- дизайн: аватарки, баннеры, логотипы, обложки для видео.
- боты для дискорда: разработка, настройка, хостинг.
- монтаж: видео, рекламные ролики, тизеры.
- впн: доступ к серверам, обход блокировок.
- buyall: пакет, включающий все категории со скидкой.

3. РОЛИ ПОКУПАТЕЛЕЙ (начисляются за количество отзывов в канале отзывов):
- 1–2 отзыва: клуб + бронзовый покупатель.
- 3–4: серебряный покупатель.
- 5–8: золотой покупатель.
- 9–12: алмазный покупатель.
- 13–17: изумрудный покупатель.
- 18–23: аметистовый покупатель.
- 24–25: легендарный покупатель.
- 26+: покупатель века.

4. СПОСОБЫ ОПЛАТЫ:
- т-банк (карта), альфа-банк, озон-банк, сбп (система быстрых платежей).
- криптовалюта: usdt, ton.
- иностранные валюты: kzt (тенге), uah (гривны), usd (доллары).
- оплата подтверждается кнопкой «оплатить» в тикете, после чего заказ обрабатывается.

5. ПРОМОКОДЫ:
- админы создают промокоды через команду /promo_add.
- пользователь активирует промокод в тикете кнопкой «промокод».
- скидка применяется к заказу автоматически.

6. СИСТЕМА ОТЗЫВОВ:
- пользователи оставляют отзывы в специальном канале (#отзывы).
- каждый новый отзыв увеличивает счётчик пользователя.
- роли покупателей обновляются автоматически.
- баннер сервера показывает общее количество отзывов (обновляется каждые 24 часа).

7. КОМАНДЫ АДМИНИСТРАТОРОВ:
- /set_rate, /get_rates, /say, /get_json, /promo_add, /promo_remove, /promo_list, /расчет, /обновить_баннер, /пересчитать_отзывы, /рассылка, /profile.

8. ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:
- команда /profile показывает: аватар, ник, покупательские роли, количество отзывов, высшую роль на сервере.

9. ПРАВИЛА И ПОРЯДОК ПОКУПКИ:
- покупатель выбирает товар, создаёт тикет, указывает способ оплаты.
- менеджер выставляет счёт, покупатель оплачивает и подтверждает оплату.
- после подтверждения менеджер выдаёт товар или услугу.
- при возникновении вопросов — обращаться в тикет или к менеджеру.

10. ДАТА ОСНОВАНИЯ МАГАЗИНА: 9 июля 2023 года.

ТЫ — ЛИЦО МАГАЗИНА, ПОЭТОМУ ОТВЕЧАЙ ВЕЖЛИВО И ПО ДЕЛУ. ЕСЛИ ТЕБЯ СПРАШИВАЮТ О МАГАЗИНЕ — ДАЙ ИСЧЕРПЫВАЮЩИЙ ОТВЕТ. ЕСЛИ ТЕМА ДРУГАЯ — ОТВЕЧАЙ ПО ТЕМЕ, НЕ ПЕРЕВОДЯ РАЗГОВОР НА МАГАЗИН, ЕСЛИ ЭТО НЕ УМЕСТНО. НЕ УХОДИ ОТ ПРЯМЫХ ОТВЕТОВ, ГОВОРИ ЧЁТКО. ЕСЛИ НЕ ЗНАЕШЬ — СКАЖИ ЧЕСТНО, НО ПРЕДЛОЖИ ПОМОЩЬ В ДРУГОМ. МАТЫ — ТОЛЬКО ЕСЛИ СОБЕСЕДНИК МАТЕРИТСЯ. ЕСЛИ ГОВОРЯТ «ЗАБУДЬ» — ЗАБУДЬ ПРЕДЫДУЩИЙ ДИАЛОГ.

СЕГОДНЯ: {current_date}
"""

# ===================== КЕШИРОВАНИЕ ОТВЕТОВ =====================
class ResponseCache:
    def __init__(self, maxsize=100, ttl=300):
        self.cache = OrderedDict()
        self.maxsize = maxsize
        self.ttl = ttl  # seconds

    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                self.cache.move_to_end(key)
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key, value):
        self.cache[key] = (value, time.time())
        self.cache.move_to_end(key)
        if len(self.cache) > self.maxsize:
            self.cache.popitem(last=False)

cache = ResponseCache()

# ===================== LOGGING =====================
LOG_FILE = "ai_bot.log"
logger = logging.getLogger("diamond_ai")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
fh.setLevel(logging.INFO)
fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
fh.setFormatter(fmt)
sh = logging.StreamHandler()
sh.setFormatter(fmt)
logger.addHandler(fh)
logger.addHandler(sh)

# ===================== SUPABASE =====================
from supabase import create_client, Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_mistral_key_and_prompt():
    try:
        res = supabase.table("service_config").select("*").eq("id", 1).execute()
        if res.data and len(res.data) > 0:
            data = res.data[0]
            return data.get("mistral_api_key"), data.get("system_prompt")
        else:
            supabase.table("service_config").insert({
                "id": 1,
                "mistral_api_key": "",
                "system_prompt": BASE_SYSTEM_PROMPT
            }).execute()
            return "", BASE_SYSTEM_PROMPT
    except Exception as e:
        logger.error(f"Ошибка получения конфига из Supabase: {e}")
        return "", BASE_SYSTEM_PROMPT

# ===================== BOT INIT =====================
intents = disnake.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='/', intents=intents)

MISTRAL_API_KEY = ""
SYSTEM_PROMPT = BASE_SYSTEM_PROMPT
last_dm_time = {}
conversation_memory: Dict[int, List[Dict[str, str]]] = {}
MAX_HISTORY = 15
MAX_MSG_LENGTH = 200

# Игры
games = {}  # {user_id: {"game": "guess", "number": int, "attempts": int, ...}}

# ===================== ФУНКЦИИ ДЛЯ ДАННЫХ ПОЛЬЗОВАТЕЛЯ =====================
def load_dc_data():
    if not os.path.exists(DC_DATA_PATH):
        return {}
    with open(DC_DATA_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def get_user_data(user_id: int):
    data = load_dc_data()
    return data.get(str(user_id), {})

def load_promo_codes():
    if not os.path.exists(PROMO_PATH):
        return {}
    with open(PROMO_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def load_rates():
    if not os.path.exists(RATES_PATH):
        return {}
    with open(RATES_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

# ===================== ЛОГИРОВАНИЕ В DISCORD =====================
async def log_discord(title: str, description: str, color: int = 0x00ff00, fields: list = None):
    try:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if not channel:
            channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        embed = disnake.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        await channel.send(embed=embed)
    except Exception as e:
        logger.error(f"Ошибка отправки лога: {e}")

# ===================== ПОЛУЧЕНИЕ ОТВЕТА ОТ MISTRAL =====================
def get_conversation_history(user_id: int) -> List[Dict[str, str]]:
    if user_id not in conversation_memory:
        conversation_memory[user_id] = []
    return conversation_memory[user_id]

def add_to_history(user_id: int, role: str, content: str):
    history = get_conversation_history(user_id)
    # обрезаем длинные сообщения
    if len(content) > MAX_MSG_LENGTH:
        content = content[:MAX_MSG_LENGTH] + "..."
    history.append({"role": role, "content": content})
    if len(history) > MAX_HISTORY * 2:
        conversation_memory[user_id] = history[-MAX_HISTORY*2:]

def clear_user_history(user_id: int, keep_last: bool = False):
    if user_id in conversation_memory:
        if keep_last and len(conversation_memory[user_id]) > 0:
            # оставляем только последнее сообщение (обычно это последний ответ бота)
            last = conversation_memory[user_id][-1]
            conversation_memory[user_id] = [last]
        else:
            conversation_memory[user_id] = []

def get_dynamic_temperature(message: str) -> float:
    """Анализирует тональность сообщения и возвращает температуру."""
    message_lower = message.lower()
    # простые индикаторы
    angry_words = ["злой", "бесит", "раздражает", "тупой", "идиот", "завали", "заткнись"]
    happy_words = ["смешно", "круто", "отлично", "класс", "весело", "рад", "улыбка"]
    if any(word in message_lower for word in angry_words):
        return 0.4  # менее креативно, более прямо
    elif any(word in message_lower for word in happy_words):
        return 1.0  # более креативно
    else:
        return 0.8

async def get_mistral_response(user_id: int, user_message: str, username: str) -> str:
    global MISTRAL_API_KEY, SYSTEM_PROMPT
    if not MISTRAL_API_KEY:
        return "эй, ключ не подгрузился, напиши админу."

    # Проверка кеша
    cache_key = f"{user_id}_{user_message}"  # можно добавить username, но не обязательно
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Обработка "забудь"
    lower_msg = user_message.lower()
    if "забудь последнее" in lower_msg:
        clear_user_history(user_id, keep_last=True)
        return "окей, забыл только последнее, остальное помню."
    elif any(phrase in lower_msg for phrase in ["забудь всё", "очисти память", "забудь о разговоре", "сбрось контекст"]):
        clear_user_history(user_id)
        return "окей, забыл всё, о чём мы говорили. давай начнём сначала, если хочешь."

    # Подготовка промта с датой
    current_date = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    system_prompt_with_date = SYSTEM_PROMPT.format(current_date=current_date)

    # Добавляем данные о пользователе (баланс, покупки)
    user_data = get_user_data(user_id)
    balance = user_data.get("balance", 0)
    purchases = user_data.get("purchases", [])
    purchases_count = len(purchases)
    last_purchase = purchases[-1] if purchases else None
    promo_codes = load_promo_codes()
    rates = load_rates()

    context_info = (
        f"пользователь {username} (id {user_id}), баланс DC: {balance}, "
        f"количество покупок: {purchases_count}, "
        f"последняя покупка: {last_purchase if last_purchase else 'нет'}. "
        f"актуальные курсы: {rates}, доступные промокоды: {promo_codes}."
    )

    # Получаем историю
    history = get_conversation_history(user_id)

    # Строим сообщения
    messages = [
        {"role": "system", "content": system_prompt_with_date + "\n" + context_info},
        *history,
        {"role": "user", "content": f"сообщение от {username}: {user_message}"}
    ]

    # Ограничиваем длину
    if len(messages) > 12:
        messages = [messages[0]] + messages[-10:]

    # Определяем температуру
    temperature = get_dynamic_temperature(user_message)

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral-small-latest",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 500
    }

    try:
        async with aiohttp.ClientSession() as session:
            # Таймаут 10 секунд
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    reply = data["choices"][0]["message"]["content"].strip()
                    # Сохраняем в кеш
                    cache.set(cache_key, reply)
                    # Сохраняем в историю
                    add_to_history(user_id, "user", user_message)
                    add_to_history(user_id, "assistant", reply)
                    return reply
                else:
                    error_text = await resp.text()
                    logger.error(f"Mistral API error {resp.status}: {error_text}")
                    # fallback
                    return "ой, что-то сломалось, попробуй позже. но я помню наш разговор."
    except asyncio.TimeoutError:
        logger.warning("Mistral API timeout")
        return "ой, я что-то задумался, давай попозже. но я здесь, если что."
    except Exception as e:
        logger.exception(f"Ошибка вызова Mistral: {e}")
        return "не вышло связаться с моим мозгом, давай попозже."

# ===================== ИГРЫ =====================
async def handle_game_commands(message: disnake.Message) -> bool:
    content = message.content.lower()
    user_id = message.author.id
    if "угадай число" in content:
        if user_id in games and games[user_id].get("game") == "guess":
            await message.reply("ты уже играешь! угадывай число от 1 до 100.")
        else:
            games[user_id] = {"game": "guess", "number": random.randint(1, 100), "attempts": 0}
            await message.reply("я загадал число от 1 до 100. попробуй угадать!")
        return True
    elif "камень" in content and "ножницы" in content and "бумага" in content:
        # По фразе "камень ножницы бумага" запускаем игру
        choices = ["камень", "ножницы", "бумага"]
        bot_choice = random.choice(choices)
        # Определяем победителя (упрощённо)
        await message.reply(f"я выбрал {bot_choice}. а ты? (напиши 'камень', 'ножницы' или 'бумага')")
        # Будем ждать следующее сообщение от этого пользователя и обработаем отдельно
        # Для простоты просто сохраним состояние
        games[user_id] = {"game": "rps", "bot_choice": bot_choice, "step": "waiting"}
        return True
    return False

async def handle_rps_choice(message: disnake.Message):
    user_id = message.author.id
    if user_id not in games:
        return False
    game = games[user_id]
    if game.get("game") != "rps" or game.get("step") != "waiting":
        return False
    user_choice = message.content.lower()
    if user_choice not in ["камень", "ножницы", "бумага"]:
        await message.reply("напиши 'камень', 'ножницы' или 'бумага'.")
        return True
    bot_choice = game["bot_choice"]
    # Определяем результат
    if user_choice == bot_choice:
        result = "ничья!"
    elif (user_choice == "камень" and bot_choice == "ножницы") or \
         (user_choice == "ножницы" and bot_choice == "бумага") or \
         (user_choice == "бумага" and bot_choice == "камень"):
        result = "ты выиграл!"
    else:
        result = "я выиграл!"
    await message.reply(f"я выбрал {bot_choice}, ты выбрал {user_choice}. {result}")
    del games[user_id]
    return True

# ===================== ПОГОДА И КРИПТА =====================
async def get_weather(city: str = "kazan") -> str:
    try:
        url = f"https://wttr.in/{city}?format=%C+%t"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.text()
                    return f"в {city} сейчас {data.strip()}"
                else:
                    return "не удалось узнать погоду."
    except Exception:
        return "что-то пошло не так с погодой."

async def get_crypto_price(coin: str = "bitcoin") -> str:
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    price = data.get(coin, {}).get("usd", "неизвестно")
                    return f"1 {coin} сейчас стоит {price} USD"
                else:
                    return "не удалось получить курс криптовалют."
    except Exception:
        return "ошибка при запросе криптовалют."

# ===================== АВТО-СООБЩЕНИЯ =====================
AUTO_PHRASES = [
    "ну че, тишина в чате? может, обсудим что-нибудь?",
    "кто тут есть? я скучаю по разговорам.",
    "я просто сижу, жду, когда кто-нибудь напишет.",
    "а давайте устроим конкурс? или я один болтаю?",
    "знаете, а в diamond shop сегодня новое поступление, спросите меня!",
    "вы вообще читаете что я пишу? а я пишу много интересного.",
    "я тут подумал, может, кофе сварганить?",
    "чё там в мире diamond shop? всё по плану?",
    "если не знаете, что спросить — спросите про роли, я в теме!",
    "ой, а вы знали, что у нас есть алмазные покупатели? круто же!",
    "я сегодня такой добрый, а вы?",
    "может, кто-то хочет анекдот? нет? ну и ладно."
]

DM_PHRASES = [
    "привет, зайди в чат diamond shop, там скучно без тебя!",
    "эй, я тут один болтаю, может, составишь компанию?",
    "в чате тишина, а ты где? давай поболтаем!",
    "я скучаю по нашим разговорам, зайди в канал!",
    "только что вспомнил смешную историю, но расскажу только в чате, заходи!",
    "ты вообще жив? загляни в даймонд чат, я там скучаю.",
    "привет! у нас в diamond shop сегодня какие-то новости, хочешь узнать?",
    "я тут решил, что надо разбавить тишину, зайди поболтаем!"
]

# Храним последнее время общения с пользователем для персонализации
last_user_interaction = {}

async def send_auto_message():
    channel = bot.get_channel(ALLOWED_CHANNEL_ID)
    if not channel:
        return
    # Проверяем, когда было последнее сообщение от пользователя
    last_user_msg_time = None
    async for msg in channel.history(limit=20):
        if not msg.author.bot:
            last_user_msg_time = msg.created_at
            break
    if last_user_msg_time:
        seconds_since = (datetime.now(timezone.utc) - last_user_msg_time).total_seconds()
        if seconds_since < 7200:
            return

    # Выбираем персонализированное обращение
    if last_user_interaction:
        # выбираем пользователя, с которым общались недавно
        users = list(last_user_interaction.keys())
        if users:
            user_id = random.choice(users)
            member = channel.guild.get_member(user_id)
            if member:
                name = member.display_name
                phrase = f"{name}, {random.choice(AUTO_PHRASES)}"
            else:
                phrase = random.choice(AUTO_PHRASES)
        else:
            phrase = random.choice(AUTO_PHRASES)
    else:
        phrase = random.choice(AUTO_PHRASES)

    await channel.send(phrase)
    await log_discord(
        title="💬 Авто-сообщение (AI)",
        description=f"> **Сообщение:** {phrase}",
        color=0x00aaff
    )

async def send_random_dm():
    global last_dm_time
    guild = bot.guilds[0] if bot.guilds else None
    if not guild:
        return
    members = [m for m in guild.members if not m.bot and m.id != bot.user.id]
    if not members:
        return
    now_ts = time.time()
    available = [m for m in members if last_dm_time.get(m.id, 0) < now_ts - 6*3600]
    if not available:
        available = sorted(members, key=lambda m: last_dm_time.get(m.id, 0))
    target = random.choice(available)
    phrase = random.choice(DM_PHRASES)
    try:
        await target.send(phrase)
        last_dm_time[target.id] = now_ts
        await log_discord(
            title="💌 ЛС-сообщение (AI)",
            description=f"> **Получатель:** {target.mention}\n> **Сообщение:** {phrase}",
            color=0xffaa00
        )
    except Exception as e:
        logger.error(f"Не удалось отправить ЛС {target}: {e}")

# ===================== ЗАДАЧИ =====================
@tasks.loop(minutes=120)
async def auto_message_task():
    await bot.wait_until_ready()
    await send_auto_message()

@tasks.loop(minutes=10)
async def dm_task():
    await bot.wait_until_ready()
    await send_random_dm()

# Статистика запросов
request_count = 0

# ===================== СОБЫТИЯ =====================
@bot.event
async def on_ready():
    global MISTRAL_API_KEY, SYSTEM_PROMPT
    key, prompt = get_mistral_key_and_prompt()
    MISTRAL_API_KEY = key
    SYSTEM_PROMPT = prompt if prompt else BASE_SYSTEM_PROMPT

    await bot.change_presence(
        status=disnake.Status.online,
        activity=disnake.Game("Нейросеть сервера")
    )

    logger.info(f"Бот запущен как {bot.user}")
    await log_discord(
        title="✅ Бот AI запущен",
        description=f"> **{bot.user}** готов к общению.",
        color=0x00ff00
    )

    # Отправляем эмбед с изменениями
    changes_embed = disnake.Embed(
        title="📢 Новые улучшения Diamond AI",
        description="Добавлены новые возможности для лучшего общения:",
        color=0x00ff00
    )
    changes_embed.add_field(
        name="🧠 Умные функции",
        value="• Кеширование ответов (быстрее)\n• Динамическая температура (адаптация под настроение)\n• Улучшенная память (до 15 сообщений)\n• Персонализация по балансу и покупкам",
        inline=False
    )
    changes_embed.add_field(
        name="🎮 Игры и развлечения",
        value="• «Угадай число»\n• «Камень-ножницы-бумага»\n• Погода и курс криптовалют",
        inline=False
    )
    changes_embed.add_field(
        name="💬 Общение",
        value="• Ответы в ЛС (если бот написал первым)\n• Интерактивные кнопки (по запросу)\n• Персонализированные авто-сообщения",
        inline=False
    )
    changes_embed.add_field(
        name="🛠️ Технические улучшения",
        value="• Таймаут и fallback при задержках\n• Улучшенное логирование ошибок\n• Автообновление курсов и промокодов",
        inline=False
    )
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(embed=changes_embed)

    if not auto_message_task.is_running():
        auto_message_task.start()
    if not dm_task.is_running():
        dm_task.start()

@bot.event
async def on_message(message: disnake.Message):
    global request_count
    if message.author.bot:
        return

    # Проверяем ЛС: если сообщение в ЛС и автор – пользователь, отвечаем всегда
    if isinstance(message.channel, disnake.DMChannel):
        # Если пользователь нам пишет в ЛС (после того, как мы ему написали)
        # отвечаем, но ограничим спам – можно отвечать всегда
        try:
            async with message.channel.typing():
                username = message.author.display_name
                reply = await get_mistral_response(message.author.id, message.content, username)
            await message.reply(reply)
            await log_discord(
                title="💬 ЛС-диалог с AI",
                description=f"> **Пользователь:** {message.author.mention}\n> **Сообщение:** {message.content}\n> **Ответ:** {reply[:500]}",
                color=0x00aaff
            )
        except Exception as e:
            logger.exception(f"Ошибка в ЛС: {e}")
            await message.reply("ой, я завис, давай ещё раз.")
        return

    # Если сообщение не в целевом канале и не пинг – игнорируем
    is_ping = bot.user in message.mentions
    if message.channel.id != ALLOWED_CHANNEL_ID and not is_ping:
        return

    # Проверяем игры (только в целевом канале)
    if message.channel.id == ALLOWED_CHANNEL_ID:
        # Обработка КНБ
        if await handle_rps_choice(message):
            return
        # Запуск игр
        if await handle_game_commands(message):
            return

        # Обработка погоды и крипты
        content_lower = message.content.lower()
        if "погода" in content_lower:
            city = "казань"  # можно парсить город
            weather = await get_weather(city)
            await message.reply(weather)
            return
        if "курс биткоина" in content_lower or "bitcoin" in content_lower:
            price = await get_crypto_price("bitcoin")
            await message.reply(price)
            return
        if "курс тона" in content_lower or "ton" in content_lower:
            price = await get_crypto_price("toncoin")
            await message.reply(price)
            return

    should_respond = False
    trigger = ""

    if is_ping:
        should_respond = True
        trigger = "пинг (вне канала)" if message.channel.id != ALLOWED_CHANNEL_ID else "пинг"

    if message.channel.id == ALLOWED_CHANNEL_ID:
        content_lower = message.content.lower()
        for word in TRIGGER_WORDS:
            if word in content_lower:
                should_respond = True
                trigger = f"триггер: {word}"
                break

    is_reply = False
    if message.reference and message.reference.resolved:
        referenced_msg = message.reference.resolved
        if referenced_msg.author == bot.user:
            if message.channel.id == ALLOWED_CHANNEL_ID or is_ping:
                should_respond = True
                trigger = "реплай"
                is_reply = True

    if not should_respond:
        return

    try:
        async with message.channel.typing():
            username = message.author.display_name
            reply = await get_mistral_response(message.author.id, message.content, username)

        # Обновляем время последнего взаимодействия
        last_user_interaction[message.author.id] = time.time()

        # Добавляем интерактивные кнопки, если сообщение содержит ключевые слова
        final_reply = reply
        if "нитро" in message.content.lower() or "скидка" in message.content.lower():
            view = View()
            view.add_item(Button(label="Подробнее о товаре", style=disnake.ButtonStyle.primary, custom_id="ai_more_info"))
            # Обработчик кнопки можно добавить в on_interaction
            await message.reply(final_reply, view=view)
        else:
            if is_reply:
                await message.reply(final_reply)
            else:
                if is_ping:
                    await message.channel.send(f"{message.author.mention}, {final_reply}")
                else:
                    await message.channel.send(final_reply)

        # Логируем запрос и ответ (каждые 100 запросов – лог в канал)
        request_count += 1
        if request_count % 100 == 0:
            await log_discord(
                title="📊 Статистика AI",
                description=f"**Всего запросов обработано:** `{request_count}`",
                color=0x00aaff
            )

        await log_discord(
            title="💬 Разговор с AI",
            description=(
                f"> **Пользователь:** {message.author.mention}\n"
                f"> **Канал:** {message.channel.mention}\n"
                f"> **Сообщение:** {message.content}\n"
                f"> **Триггер:** `{trigger}`\n"
                f"> **Ответ:** {reply[:500]}{'...' if len(reply) > 500 else ''}"
            ),
            color=0xffff00
        )

    except Exception as e:
        logger.exception(f"Ошибка обработки сообщения: {e}")
        await message.channel.send("ой, я завис, давай ещё раз.")

# ===================== ОБРАБОТКА ИНТЕРАКЦИЙ (кнопки) =====================
@bot.event
async def on_interaction(inter: disnake.MessageInteraction):
    if inter.data.get("custom_id") == "ai_more_info":
        await inter.response.send_message("📦 Подробнее: напиши мне, что именно тебя интересует, и я расскажу!", ephemeral=True)

# ===================== ЗАПУСК =====================
if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        logger.exception(f"Ошибка запуска бота: {e}")
