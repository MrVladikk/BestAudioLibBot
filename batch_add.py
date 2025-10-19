import asyncio
import os
from tqdm import tqdm
from aiogram import Bot
from aiogram.types import FSInputFile

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_factory, Author, Genre, Book, AudioFile

# --- НАСТРОЙКИ ---
# Вставьте сюда ваш токен бота (тот же, что и в main.py)
API_TOKEN = '7743716366:AAFyNE4FCaSWvRfo65pDjOOoC_doWH7jBls'

# Вставьте сюда ВАШ User ID, который вы получили от @userinfobot
# Скрипт будет отправлять аудиофайлы в ваш личный чат с ботом.
ADMIN_ID = 705446667  # <<< ЗАМЕНИТЕ НА ВАШ ID

# Название папки, куда вы складываете аудиофайлы и обложку
UPLOADS_FOLDER = "Uploads"
# -----------------

bot = Bot(token=API_TOKEN)

async def batch_add_book():
    """
    Автоматически добавляет книгу и все ее главы из папки 'Uploads',
    находя и загружая обложку (cover.jpg/png).
    """
    print("--- Автоматический загрузчик книг v2.1 (с паузой) ---")
    
    # --- ШАГ 1: Поиск обложки и аудиофайлов ---
    try:
        all_files_in_folder = os.listdir(UPLOADS_FOLDER)
    except FileNotFoundError:
        print(f"ОШИБКА: Папка '{UPLOADS_FOLDER}' не найдена. Создайте ее и положите туда файлы книги.")
        return

    cover_path = None
    cover_file_id = None
    possible_cover_names = ['cover.jpg', 'cover.jpeg', 'cover.png']
    
    audio_filenames = []

    for file in all_files_in_folder:
        if file.lower() in possible_cover_names:
            cover_path = os.path.join(UPLOADS_FOLDER, file)
        elif file.lower().endswith(('.mp3', '.m4a')):
            audio_filenames.append(file)
        else:
            print(f"Предупреждение: Неизвестный файл '{file}' будет проигнорирован.")

    # Сортируем аудиофайлы, чтобы главы шли по порядку
    audio_filenames.sort()

    if not audio_filenames:
        print(f"ОШИБКА: В папке '{UPLOADS_FOLDER}' не найдено аудиофайлов (.mp3).")
        return

    # --- ШАГ 2: Запрос информации о книге ---
    book_title = input("Введите название книги: ")
    author_name = input("Введите имя автора: ")
    genre_name = input("Введите жанр: ")

    # --- ШАГ 3: Загрузка обложки (если найдена) ---
    if cover_path:
        print(f"Найдена обложка: {os.path.basename(cover_path)}. Загружаем ее для получения file_id...")
        try:
            cover_to_upload = FSInputFile(cover_path)
            sent_message = await bot.send_photo(ADMIN_ID, cover_to_upload)
            cover_file_id = sent_message.photo[-1].file_id
            print("Обложка успешно загружена. file_id получен.")
        except Exception as e:
            print(f"Не удалось загрузить обложку. Ошибка: {e}. Книга будет добавлена без нее.")
            cover_file_id = None
    else:
        print("Обложка не найдена. Книга будет добавлена без нее.")

    # --- ШАГ 4: Сохранение книги в БД ---
    async with async_session_factory() as session:
        try:
            # Поиск или создание автора
            result = await session.execute(select(Author).filter_by(name=author_name))
            author = result.scalars().first()
            if not author:
                author = Author(name=author_name)
                session.add(author)
                await session.flush()  # Сохраняем автора, чтобы получить его ID

            # Поиск или создание жанра
            result = await session.execute(select(Genre).filter_by(name=genre_name))
            genre = result.scalars().first()
            if not genre:
                genre = Genre(name=genre_name)
                session.add(genre)
                await session.flush()  # Сохраняем жанр, чтобы получить его ID

            # Проверка существующей книги
            result = await session.execute(
                select(Book).filter_by(title=book_title, author_id=author.id)
            )
            existing_book = result.scalars().first()
            if existing_book:
                print(f"Книга '{book_title}' уже существует. Удаляем старую версию для полного обновления...")
                await session.delete(existing_book)
                await session.commit()

            # Создание новой книги
            new_book = Book(
                title=book_title,
                author_id=author.id,
                genre_id=genre.id,
                cover_file_id=cover_file_id
            )
            session.add(new_book)
            await session.commit()
            print(f"Книга '{book_title}' создана. Начинаем загрузку глав...")

            # --- ШАГ 5: Последовательная загрузка аудио-глав ---
            print("Отправка аудиофайлов в Telegram для получения ID (это может занять время)...")
            for filename in tqdm(audio_filenames, desc="Загрузка глав"):
                await process_audio_file(filename, new_book, session)
                # Делаем паузу в 1 секунду после каждой главы, чтобы избежать бана от Telegram
                await asyncio.sleep(1)

            print("\nВсе главы успешно добавлены в базу данных!")
        except Exception as e:
            print(f"ОШИБКА при сохранении в базу данных: {e}")
            await session.rollback()

async def process_audio_file(filename, book_obj, session: AsyncSession):
    """Отправляет один аудиофайл, получает его ID и сохраняет в базу."""
    file_path = os.path.join(UPLOADS_FOLDER, filename)
    try:
        audio_to_upload = FSInputFile(file_path, filename=filename)
        sent_message = await bot.send_audio(ADMIN_ID, audio_to_upload)
        file_id = sent_message.audio.file_id
        chapter_title = os.path.splitext(filename)[0]
        new_chapter = AudioFile(book_id=book_obj.id, title=chapter_title, file_id=file_id)
        session.add(new_chapter)
        await session.commit()
    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА при обработке файла {filename}: {e}")
        # Прерываем все, если один файл не удалось загрузить
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()

async def main():
    try:
        await batch_add_book()
    except asyncio.CancelledError:
        print("\nВыполнение было прервано из-за ошибки в одном из файлов.")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())