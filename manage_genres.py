import asyncio
import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database import async_session_factory, Genre, Book

# Настройка логирования для диагностики
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def list_genres(session: AsyncSession):
    """Возвращает список всех жанров с количеством книг."""
    try:
        result = await session.execute(select(Genre).order_by(Genre.name))
        genres = result.scalars().all()
        if not genres:
            print("Жанры не найдены.")
            return []
        print("\nСписок жанров:")
        for genre in genres:
            book_count = (await session.execute(
                select(func.count(Book.id)).filter(Book.genre_id == genre.id)
            )).scalar()
            print(f"- {genre.name} (ID: {genre.id}, книг: {book_count})")
        return genres
    except Exception as e:
        logger.error(f"Ошибка при получении списка жанров: {e}")
        return []

async def transfer_books(session: AsyncSession, source_genre_name: str, target_genre_name: str):
    """Переносит все книги из одного жанра в другой."""
    try:
        # Поиск исходного жанра
        source_genre = (await session.execute(
            select(Genre).filter_by(name=source_genre_name)
        )).scalars().first()
        if not source_genre:
            print(f"Жанр '{source_genre_name}' не найден.")
            return False

        # Поиск целевого жанра
        target_genre = (await session.execute(
            select(Genre).filter_by(name=target_genre_name)
        )).scalars().first()
        if not target_genre:
            print(f"Жанр '{target_genre_name}' не найден. Создаём новый жанр...")
            target_genre = Genre(name=target_genre_name)
            session.add(target_genre)
            await session.flush()  # Сохраняем, чтобы получить ID

        # Поиск книг в исходном жанре
        books = (await session.execute(
            select(Book).filter_by(genre_id=source_genre.id)
        )).scalars().all()
        if not books:
            print(f"В жанре '{source_genre_name}' нет книг для переноса.")
            return True

        # Перенос книг
        for book in books:
            book.genre_id = target_genre.id
        await session.commit()
        print(f"Успешно перенесено {len(books)} книг из '{source_genre_name}' в '{target_genre_name}'.")
        return True
    except Exception as e:
        logger.error(f"Ошибка при переносе книг: {e}")
        await session.rollback()
        return False

async def delete_genre(session: AsyncSession, genre_name: str, target_genre_name: str = None):
    """Удаляет жанр, при необходимости перенеся книги в другой жанр."""
    try:
        # Поиск жанра для удаления
        genre = (await session.execute(
            select(Genre).filter_by(name=genre_name)
        )).scalars().first()
        if not genre:
            print(f"Жанр '{genre_name}' не найден.")
            return False

        # Проверка наличия книг в жанре
        book_count = (await session.execute(
            select(func.count(Book.id)).filter(Book.genre_id == genre.id)
        )).scalar()
        if book_count > 0:
            if not target_genre_name:
                print(f"Жанр '{genre_name}' содержит {book_count} книг. Укажите жанр для переноса книг перед удалением.")
                return False
            # Перенос книг перед удалением
            success = await transfer_books(session, genre_name, target_genre_name)
            if not success:
                return False

        # Удаление жанра
        await session.delete(genre)
        await session.commit()
        print(f"Жанр '{genre_name}' успешно удалён.")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении жанра: {e}")
        await session.rollback()
        return False

async def main():
    """Основная функция для управления жанрами."""
    print("--- Управление жанрами ---")
    async with async_session_factory() as session:
        while True:
            print("\nВыберите действие:")
            print("1. Перенести книги из одного жанра в другой")
            print("2. Удалить жанр")
            print("3. Показать список жанров")
            print("4. Выход")
            choice = input("Введите номер действия (1-4): ")

            if choice == "1":
                await list_genres(session)
                source_genre = input("Введите название жанра, из которого перенести книги: ")
                target_genre = input("Введите название жанра, в который перенести книги: ")
                await transfer_books(session, source_genre, target_genre)
            elif choice == "2":
                await list_genres(session)
                genre_name = input("Введите название жанра для удаления: ")
                book_count = (await session.execute(
                    select(func.count(Book.id)).join(Genre).filter(Genre.name == genre_name)
                )).scalar()
                if book_count > 0:
                    target_genre = input("Жанр содержит книги. Введите жанр для переноса книг (или оставьте пустым для отмены): ")
                    if not target_genre:
                        print("Удаление отменено.")
                        continue
                else:
                    target_genre = None
                await delete_genre(session, genre_name, target_genre)
            elif choice == "3":
                await list_genres(session)
            elif choice == "4":
                print("Выход из программы.")
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    asyncio.run(main())