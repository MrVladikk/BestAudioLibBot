import asyncio
import os
from tqdm import tqdm
from aiogram import Bot
from aiogram.types import FSInputFile

from database import session, Book, AudioFile

# --- НАСТРОЙКИ ---
API_TOKEN = '7743716366:AAFyNE4FCaSWvRfo65pDjOOoC_doWH7jBls'
ADMIN_ID = 705446667 # <<< ЗАМЕНИТЕ НА ВАШ ID
UPLOADS_FOLDER = "uploads"
# -----------------

bot = Bot(token=API_TOKEN)

async def add_chapters():
    """
    Находит существующую книгу и добавляет к ней все главы из папки 'uploads'.
    """
    print("--- Утилита добавления глав к существующей книге ---")
    
    book_title = input("Введите точное название книги, в которую нужно добавить главы: ")

    # Находим книгу в базе данных
    book_to_update = session.query(Book).filter(Book.title == book_title).first()

    if not book_to_update:
        print(f"ОШИБКА: Книга с названием '{book_title}' не найдена в базе.")
        return

    print(f"Найдена книга: '{book_to_update.title}'. Начинаем добавление глав...")

    try:
        files_to_upload = sorted(os.listdir(UPLOADS_FOLDER))
    except FileNotFoundError:
        print(f"ОШИБКА: Папка '{UPLOADS_FOLDER}' не найдена.")
        return

    if not files_to_upload:
        print(f"ОШИБКА: Папка '{UPLOADS_FOLDER}' пуста.")
        return
    
    print(f"Найдено {len(files_to_upload)} глав для добавления...")

    for filename in tqdm(files_to_upload, desc="Добавление глав"):
        await process_file(filename, book_to_update)
        await asyncio.sleep(1) # Делаем паузу в 1 секунду между загрузками

    print("\nВсе главы из папки успешно добавлены к книге!")


async def process_file(filename, book_obj):
    """Отправляет один файл, получает его ID и сохраняет в базу."""
    file_path = os.path.join(UPLOADS_FOLDER, filename)
    try:
        audio_to_upload = FSInputFile(file_path, filename=filename)
        sent_message = await bot.send_audio(ADMIN_ID, audio_to_upload)
        file_id = sent_message.audio.file_id
        chapter_title = os.path.splitext(filename)[0]
        new_chapter = AudioFile(book_id=book_obj.id, title=chapter_title, file_id=file_id)
        session.add(new_chapter)
        session.commit()
    except Exception as e:
        print(f"\nОШИБКА при обработке файла {filename}: {e}")


async def main():
    await add_chapters()
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())