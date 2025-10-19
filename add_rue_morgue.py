from database import session, Author, Genre, Book, AudioFile

def add_rue_morgue_story():
    """
    Скрипт для добавления книги 'Убийство на улице Морг' с тремя главами.
    """
    
    # --- Данные о книге ---
    book_title = "Убийство на улице Морг"
    author_name = "Эдгар Аллан По"
    genre_name = "Детектив"
    
    # --- Список глав, сформированный из вашего файла ---
    chapters = [
        {"title": "Часть 1", "file_id": "CQACAgIAAxkBAAIDFmhSd-sHPFCeKQGUvCguaS3Vo_8gAALuaQAC6DuYSnnWRvQwdAaoNgQ"},
        {"title": "Часть 2", "file_id": "CQACAgIAAxkBAAIDGGhSeAKwIrL7iSD2cQOTXk4CNzRxAALwaQAC6DuYSmBKVGAVHZu-NgQ"},
        {"title": "Часть 3", "file_id": "CQACAgIAAxkBAAIDGmhSeBeDxU3jAZUlJ5c8URdOE8ScAALyaQAC6DuYSiJBJhoRdRhoNgQ"}
    ]
    # --------------------------------------------------------------------

    # Проверяем, существует ли уже такая книга
    existing_book = session.query(Book).join(Author).filter(
        Book.title == book_title,
        Author.name == author_name
    ).first()
    if existing_book:
        print(f"Книга '{book_title}' уже существует в базе. Добавление отменено.")
        return

    # Находим автора или создаем нового
    author = session.query(Author).filter_by(name=author_name).first()
    if not author:
        author = Author(name=author_name)
        session.add(author)
        print(f"Добавлен новый автор: {author_name}")

    # Находим жанр или создаем новый
    genre = session.query(Genre).filter_by(name=genre_name).first()
    if not genre:
        genre = Genre(name=genre_name)
        session.add(genre)
        print(f"Добавлен новый жанр: {genre_name}")
    
    # Создаем новую книгу
    new_book = Book(title=book_title, author=author, genre=genre)
    session.add(new_book)
    print(f"Добавлена новая книга: '{book_title}'")
    
    # Добавляем аудиофайлы к новой книге
    for chapter_data in chapters:
        audio = AudioFile(book=new_book, title=chapter_data["title"], file_id=chapter_data["file_id"])
        session.add(audio)
    
    session.commit()
    print(f"Книга '{book_title}' с тремя главами успешно добавлена в базу данных!")


if __name__ == '__main__':
    add_rue_morgue_story()