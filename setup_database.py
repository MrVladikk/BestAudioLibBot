from database import Base, engine, session, Genre, Author, Book

def setup_db():
    # Удаляем все старые таблицы (если они были) и создаем новые по чертежам из database.py
    print("Удаление старых таблиц и создание новых...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Таблицы успешно созданы.")

    # Создаем и добавляем тестовые данные
    print("Добавление тестовых данных...")
    
    # Жанры
    genre_prose = Genre(name="Классическая проза")
    genre_adventure = Genre(name="Приключения")

    # Авторы
    author_pushkin = Author(name="Александр Пушкин")
    author_verne = Author(name="Жюль Верн")

    # Книги
    book_captain = Book(title="Капитанская дочка", author=author_pushkin, genre=genre_prose)
    book_island = Book(title="Таинственный остров", author=author_verne, genre=genre_adventure)

    session.add_all([genre_prose, genre_adventure, author_pushkin, author_verne, book_captain, book_island])
    
    # Сохраняем все изменения в базе
    session.commit()
    print("Тестовые данные успешно добавлены.")
    print("База данных готова к работе!")

if __name__ == '__main__':
    setup_db()