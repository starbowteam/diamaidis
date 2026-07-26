# -*- coding: utf-8 -*-
import os
import asyncio
import logging
import json
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import aiohttp
from supabase import create_client, Client
import disnake
from disnake.ext import commands, tasks

# ----------------------------
# CONFIG
# ----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ Ошибка: переменная окружения BOT_TOKEN не установлена.")
    exit(1)

ALLOWED_CHANNEL_ID = 1462064375862005845  # Канал для обычного общения
LOG_CHANNEL_ID = 1530453871581855744
SUPABASE_URL = "https://pqgwrokpizeelfrjmgoc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxZ3dyb2twaXplZWxmcmptZ29jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcxNTAyMDksImV4cCI6MjA5MjcyNjIwOX0.qtFCGBnpwdQbtmpwSZxI_hH3arq4HBAw62vs5h8WmAk"

TRIGGER_WORDS = [
    "даймонд аи", "даймонд ии", "ии диамонд", "diamond ai", "dm ai",
    "диамонд аи", "диамонд ии", "ai diamond", "даймонд бот", "diamond bot"
]

# ----------------------------
# СИСТЕМНЫЙ ПРОМТ (с датами)
# ----------------------------
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

# ----------------------------
# Logging
# ----------------------------
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

# ----------------------------
# Supabase Client
# ----------------------------
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

# ----------------------------
# BOT INIT
# ----------------------------
intents = disnake.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

MISTRAL_API_KEY = ""
SYSTEM_PROMPT = BASE_SYSTEM_PROMPT
last_dm_time = {}

conversation_memory: Dict[int, List[Dict[str, str]]] = {}
MAX_HISTORY = 10

def get_user_history(user_id: int) -> List[Dict[str, str]]:
    if user_id not in conversation_memory:
        conversation_memory[user_id] = []
    return conversation_memory[user_id]

def add_to_history(user_id: int, role: str, content: str):
    history = get_user_history(user_id)
    history.append({"role": role, "content": content})
    if len(history) > MAX_HISTORY * 2:
        conversation_memory[user_id] = history[-MAX_HISTORY*2:]

def clear_user_history(user_id: int):
    if user_id in conversation_memory:
        conversation_memory[user_id] = []

# ----------------------------
# LOGGING HELPER
# ----------------------------
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

# ----------------------------
# MISTRAL API CALL (с историей и датой)
# ----------------------------
async def get_mistral_response(user_id: int, user_message: str, username: str) -> str:
    global MISTRAL_API_KEY, SYSTEM_PROMPT
    if not MISTRAL_API_KEY:
        return "эй, ключ не подгрузился, напиши админу."

    lower_msg = user_message.lower()
    if any(phrase in lower_msg for phrase in ["забудь", "очисти память", "забудь о разговоре", "сбрось контекст"]):
        clear_user_history(user_id)
        return "окей, забыл всё, о чём мы говорили. давай начнём сначала, если хочешь."

    # Подставляем текущую дату в промт
    current_date = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    system_prompt_with_date = SYSTEM_PROMPT.format(current_date=current_date)

    history = get_user_history(user_id)
    messages = [
        {"role": "system", "content": system_prompt_with_date},
        *history,
        {"role": "user", "content": f"сообщение от {username}: {user_message}"}
    ]

    if len(messages) > 12:
        messages = [messages[0]] + messages[-10:]

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral-small-latest",
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 500
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    reply = data["choices"][0]["message"]["content"].strip()
                    add_to_history(user_id, "user", f"сообщение от {username}: {user_message}")
                    add_to_history(user_id, "assistant", reply)
                    return reply
                else:
                    error_text = await resp.text()
                    logger.error(f"Mistral API error {resp.status}: {error_text}")
                    return "ой, что-то сломалось, попробуй позже."
    except Exception as e:
        logger.exception(f"Ошибка вызова Mistral: {e}")
        return "не вышло связаться с моим мозгом, давай попозже."

# ----------------------------
# AUTO MESSAGES (интервал 2 часа)
# ----------------------------
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

async def send_auto_message():
    channel = bot.get_channel(ALLOWED_CHANNEL_ID)
    if not channel:
        logger.warning("Канал для общения не найден")
        return
    last_user_msg_time = None
    async for msg in channel.history(limit=20):
        if not msg.author.bot:
            last_user_msg_time = msg.created_at
            break
    if last_user_msg_time:
        seconds_since = (datetime.now(timezone.utc) - last_user_msg_time).total_seconds()
        if seconds_since < 7200:
            return
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

# ----------------------------
# TASKS
# ----------------------------
@tasks.loop(minutes=120)
async def auto_message_task():
    await bot.wait_until_ready()
    await send_auto_message()

@tasks.loop(minutes=10)
async def dm_task():
    await bot.wait_until_ready()
    await send_random_dm()

# ----------------------------
# EVENTS
# ----------------------------
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

    if not auto_message_task.is_running():
        auto_message_task.start()
    if not dm_task.is_running():
        dm_task.start()

@bot.event
async def on_message(message: disnake.Message):
    if message.author.bot:
        return

    is_ping = bot.user in message.mentions

    # Если сообщение не в разрешённом канале и не пинг – игнорируем
    if message.channel.id != ALLOWED_CHANNEL_ID and not is_ping:
        return

    should_respond = False
    trigger = ""

    if is_ping:
        should_respond = True
        trigger = "пинг (вне канала)" if message.channel.id != ALLOWED_CHANNEL_ID else "пинг"

    # Триггер-слова только в целевом канале
    if message.channel.id == ALLOWED_CHANNEL_ID:
        content_lower = message.content.lower()
        for word in TRIGGER_WORDS:
            if word in content_lower:
                should_respond = True
                trigger = f"триггер: {word}"
                break

    # Реплай на бота – только если целевой канал или пинг
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

        final_reply = reply

        if is_reply:
            await message.reply(final_reply)
        else:
            if is_ping:
                await message.channel.send(f"{message.author.mention}, {final_reply}")
            else:
                await message.channel.send(final_reply)

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

# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        logger.exception(f"Ошибка запуска бота: {e}")
