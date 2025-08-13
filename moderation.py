import asyncio
from telethon import TelegramClient, events, Button

# --- ОБЯЗАТЕЛЬНЫЕ НАСТРОЙКИ ---
# 1. Ваши учетные данные с my.telegram.org
API_ID = 123456  # Замените на ваш API ID
API_HASH = ''  # Замените на ваш API Hash

# 2. Данные вашего бота
BOT_TOKEN = ''  # Замените на токен вашего бота

# 3. ID
# ID канала должен быть числом (например, -1001234567890)
CHANNEL_ID = -1001234567890
ADMIN_ID = 1234567890  # Замените на ваш личный Telegram ID

# --- КОНЕЦ НАСТРОЕК ---

# Создаем клиент Telethon, но НЕ ЗАПУСКАЕМ его здесь
bot = TelegramClient('bot_session', API_ID, API_HASH)

# Глобальные переменные для хранения очереди модерации
MESSAGES_TO_MODERATE = []
CURRENT_MESSAGE_INDEX = 0
MODERATION_IN_PROGRESS = False

async def send_next_for_moderation():
    """Отправляет следующий пост на модерацию администратору."""
    global CURRENT_MESSAGE_INDEX, MODERATION_IN_PROGRESS

    if CURRENT_MESSAGE_INDEX < len(MESSAGES_TO_MODERATE):
        message_obj = MESSAGES_TO_MODERATE[CURRENT_MESSAGE_INDEX]
        message_id = message_obj.id
        
        keyboard = [
            [Button.inline("Заблокировать", data=f'block_{message_id}')],
            [Button.inline("Самостоятельная модерация", data=f'manual_{message_id}')],
            [Button.inline("Пропустить", data=f'skip_{message_id}')]
        ]

        try:
            await bot.forward_messages(ADMIN_ID, message_id, from_peer=CHANNEL_ID)
            
            total = len(MESSAGES_TO_MODERATE)
            await bot.send_message(
                ADMIN_ID,
                f'Пост {CURRENT_MESSAGE_INDEX + 1}/{total}. Выберите действие:',
                buttons=keyboard
            )
        except Exception as e:
            print(f"Ошибка при обработке сообщения {message_id}: {e}")
            CURRENT_MESSAGE_INDEX += 1
            await send_next_for_moderation()

    else:
        await bot.send_message(ADMIN_ID, '🎉 Модерация всех постов завершена!')
        MODERATION_IN_PROGRESS = False

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Обработчик команды /start."""
    if event.sender_id != ADMIN_ID:
        return
    await event.reply(
        'Привет! Я помогу смодерировать твой канал с самого первого поста.\n'
        'Используй команду /moderate, чтобы начать.'
    )

@bot.on(events.NewMessage(pattern='/moderate'))
async def moderate_handler(event):
    """Загружает всю историю канала и начинает модерацию."""
    global MESSAGES_TO_MODERATE, CURRENT_MESSAGE_INDEX, MODERATION_IN_PROGRESS
    
    if event.sender_id != ADMIN_ID:
        return
    if MODERATION_IN_PROGRESS:
        await event.reply("Модерация уже запущена.")
        return

    await event.reply('Начинаю загрузку всей истории сообщений канала... Это может занять некоторое время.')
    
    MESSAGES_TO_MODERATE = []
    CURRENT_MESSAGE_INDEX = 0
    MODERATION_IN_PROGRESS = True
    
    async with TelegramClient('user_session', API_ID, API_HASH) as client:
        async for message in client.iter_messages(CHANNEL_ID, reverse=True):
            if message and (message.text or message.media):
                MESSAGES_TO_MODERATE.append(message)

    if not MESSAGES_TO_MODERATE:
        await event.reply('В канале не найдено сообщений для модерации.')
        MODERATION_IN_PROGRESS = False
        return

    await event.reply(f'✅ История загружена. Всего постов на модерацию: {len(MESSAGES_TO_MODERATE)}.\nНачинаем!')
    await send_next_for_moderation()

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    """Обработчик нажатий на инлайн-кнопки."""
    global CURRENT_MESSAGE_INDEX

    if event.sender_id != ADMIN_ID:
        await event.answer("Это не для вас.", alert=True)
        return

    await event.answer()

    query_data = event.data.decode('utf-8')
    action, message_id_str = query_data.split('_')
    message_id = int(message_id_str)
    
    try:
        channel_username = (await bot.get_entity(CHANNEL_ID)).username
        message_link = f'https://t.me/{channel_username}/{message_id}'
    except Exception:
        message_link = f"Не удалось создать ссылку для сообщения {message_id}"


    if action == 'block':
        try:
            await bot.edit_message(
                CHANNEL_ID,
                message_id,
                text="(Контент не доступен из-за местного законодательства)"
            )
            await event.edit(f'✅ Пост #{message_id} заблокирован.')
        except Exception as e:
            await event.edit(f'❌ Не удалось заблокировать пост #{message_id}. Ошибка: {e}')
    
    elif action == 'manual':
        await event.edit(f'👉 Ссылка для ручной модерации поста #{message_id}:\n{message_link}')

    elif action == 'skip':
        await event.edit(f'➡️ Пост #{message_id} пропущен.')
    
    CURRENT_MESSAGE_INDEX += 1
    await asyncio.sleep(1) 
    await send_next_for_moderation()

async def main():
    """Основная функция для запуска и работы бота."""
    # Запускаем бота ИМЕННО ЗДЕСЬ, внутри основной функции
    await bot.start(bot_token=BOT_TOKEN)
    print("Бот запущен...")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    # Эта часть запускает основную функцию и управляет циклом
    asyncio.run(main())
