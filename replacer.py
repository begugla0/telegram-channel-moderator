import asyncio
from telethon import TelegramClient

# --- НАСТРОЙКИ ---
# 1. Ваши учетные данные с my.telegram.org
API_ID = 123456      # Вставьте ваш API ID
API_HASH = ''  # Вставьте ваш API Hash

# 2. Название вашего канала
CHANNEL_USERNAME = ''

# 3. ТЕКСТ, КОТОРЫЙ НУЖНО НАЙТИ И ЗАМЕНИТЬ
TEXT_TO_FIND = ''

# 4. ТЕКСТ, НА КОТОРЫЙ НУЖНО ЗАМЕНИТЬ
# Например, '@new_copyright' или 'Источник: Мой канал'
REPLACEMENT_TEXT = '' # <--- ЗАМЕНИТЕ ЭТО НА ВАШ НОВЫЙ ТЕКСТ

# 5. Задержка между изменениями в секундах (рекомендуется 2-3 секунды)
DELAY_SECONDS = 2
# --- КОНЕЦ НАСТРОЕК ---


async def main():
    """
    Основная функция для подключения и обработки сообщений.
    """
    print("--- Скрипт для замены текста в постах ---")
    if TEXT_TO_FIND == REPLACEMENT_TEXT:
        print("ОШИБКА: Текст для поиска и текст для замены одинаковы. Выход.")
        return
        
    async with TelegramClient('user_session', API_ID, API_HASH) as client:
        print("Клиент успешно запущен от вашего имени.")
        
        try:
            channel = await client.get_entity(CHANNEL_USERNAME)
            print(f"Канал '{channel.title}' найден. Начинаю обработку...")
            print(f"Буду искать '{TEXT_TO_FIND}' и заменять на '{REPLACEMENT_TEXT}'")
        except Exception as e:
            print(f"Не удалось найти канал {CHANNEL_USERNAME}. Ошибка: {e}")
            print("Убедитесь, что вы являетесь администратором этого канала.")
            return

        total_messages_scanned = 0
        total_messages_edited = 0

        # Получаем все сообщения из канала
        async for message in client.iter_messages(channel):
            total_messages_scanned += 1

            if total_messages_scanned % 50 == 0:
                print(f"Просканировано сообщений: {total_messages_scanned}...")

            # Проверяем, что у сообщения есть текст и он содержит искомую фразу
            if message.text and TEXT_TO_FIND in message.text:
                
                # Создаем новый текст, заменяя старый на новый
                new_text = message.text.replace(TEXT_TO_FIND, REPLACEMENT_TEXT)

                # Проверяем, изменился ли текст
                if new_text != message.text:
                    try:
                        # Редактируем сообщение
                        await message.edit(new_text)
                        total_messages_edited += 1
                        print(f"  [УСПЕХ] Сообщение {message.id} отредактировано.")
                        
                        # Ждем, чтобы не получить бан
                        print(f"  ...пауза на {DELAY_SECONDS} сек.")
                        await asyncio.sleep(DELAY_SECONDS)

                    except Exception as e:
                        print(f"  [ОШИБКА] Не удалось отредактировать сообщение {message.id}: {e}")
                        if 'wait' in str(e): 
                            print("  !!! Словили лимит от Telegram. Увеличиваю паузу до 60 секунд.")
                            await asyncio.sleep(60)
        
        print("\n--- ГОТОВО! ---")
        print(f"Всего просканировано сообщений: {total_messages_scanned}")
        print(f"Всего отредактировано сообщений: {total_messages_edited}")


if __name__ == "__main__":
    asyncio.run(main())
