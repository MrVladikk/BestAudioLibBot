from database import session, Author, Genre, Book, AudioFile

def add_world_order_book():
    """
    Скрипт для добавления книги 'Мировой порядок' Генри Киссинджера.
    """
    
    # --- Данные о книге ---
    book_title = "Мировой порядок"
    author_name = "Генри Киссинджер"
    genre_name = "Политика"  # Новый жанр
    
    # --- Список глав, сформированный из вашего файла ---
    chapters = [
        {"title": "Глава 00 (Введение)", "file_id": "CQACAgIAAxkBAAICpWhSZX_mlpaHe5ZVDUhivPaPl2R7AAKcaAAC6DuYSjCr0R3-xOf2NgQ"},
        {"title": "Глава 01", "file_id": "CQACAgIAAxkBAAICp2hSZaCZmuSVfA2nvqPM6xXNN5LRAAKgaAAC6DuYSri5MvTjJh-ANgQ"},
        {"title": "Глава 02", "file_id": "CQACAgIAAxkBAAICqWhSZbmDbDxd9Zybf2ddMMkdrTmFAAKjaAAC6DuYSq1y4WFVwsYQNgQ"},
        {"title": "Глава 03", "file_id": "CQACAgIAAxkBAAICq2hSZcqWJO6jd98Mu1o4SNs9G8MhAAKkaAAC6DuYSgABgM1LpLhAKTYE"},
        {"title": "Глава 04", "file_id": "CQACAgIAAxkBAAICrWhSZd-X6C3uZnaPZqq4k_SCU6DhAAKlaAAC6DuYSlb6s2ediAL_NgQ"},
        {"title": "Глава 05", "file_id": "CQACAgIAAxkBAAICr2hSZg_ivH6CxZCbldL57Vy3Ds1qAAKnaAAC6DuYSoFqvGpbmvwcNgQ"},
        {"title": "Глава 06", "file_id": "CQACAgIAAxkBAAICsWhSZjRU5xBk11pQGVd3viDqGkkZAAKsaAAC6DuYSnH0odCHxSVbNgQ"},
        {"title": "Глава 07", "file_id": "CQACAgIAAxkBAAICs2hSZkFGlvsw3PqPKfxNQ_wXMxcjAAKtaAAC6DuYSpAB60N7endaNgQ"},
        {"title": "Глава 08", "file_id": "CQACAgIAAxkBAAICtWhSZlO2bhtPgqEAAau34-u0NhVJOgACsWgAAug7mEqa2l_QIwgjVjYE"},
        {"title": "Глава 09", "file_id": "CQACAgIAAxkBAAICt2hSZmzhK8Saz53aL_G4Le7SlZE0AAKzaAAC6DuYSm4NvrppDPLYNgQ"},
        {"title": "Глава 10", "file_id": "CQACAgIAAxkBAAICuWhSZnx4dbAO2u5Az788XiKtuoaHAAK1aAAC6DuYSvmho4EOO3mWNgQ"},
        {"title": "Глава 11", "file_id": "CQACAgIAAxkBAAICu2hSZorFyerjsv6Qpd-YeSYL5A-DAAK2aAAC6DuYSpUVxR9QR_mdNgQ"},
        {"title": "Глава 12", "file_id": "CQACAgIAAxkBAAICvWhSZpWfth8D5m9OF8RMnMPDkA0wAAK5aAAC6DuYSpuUede30Q1RNgQ"},
        {"title": "Глава 13", "file_id": "CQACAgIAAxkBAAICv2hSZqIxgdU8KI8GrpAEpvtEStCNAAK6aAAC6DuYSu2TtrrdxmcLNgQ"},
        {"title": "Глава 14", "file_id": "CQACAgIAAxkBAAICwWhSZrC0NlBnXqVuj2b83-GhxbROAAK8aAAC6DuYSuWva-J5h5DCNgQ"},
        {"title": "Глава 15", "file_id": "CQACAgIAAxkBAAICw2hSZrwF3J3Ox3COKt-fToQBOA8aAAK-aAAC6DuYSiFo3qW9_ppjNgQ"},
        {"title": "Глава 16", "file_id": "CQACAgIAAxkBAAICxWhSZs28IlXV1H27QuKr4fk9jS_OAALAaAAC6DuYSnB6grQZ-yAYNgQ"},
        {"title": "Глава 17", "file_id": "CQACAgIAAxkBAAICx2hSZtrbhyLUYfoCnLXU7niJ47YcAALBaAAC6DuYSpT-EhnkLb36NgQ"},
        {"title": "Глава 18", "file_id": "CQACAgIAAxkBAAICyWhSZuUPMyC5FpHgn-EdOifYtvGpAAKwbwACcBqYSsnmbpSCeliZNgQ"},
        {"title": "Глава 19", "file_id": "CQACAgIAAxkBAAICy2hSZvkUJVWEX_VlYJtTyK9qASbaAALEaAAC6DuYSs67F6h9imRwNgQ"},
        {"title": "Глава 20", "file_id": "CQACAgIAAxkBAAICzWhSZwa-WuQcv0xpeAd56OD-RKmyAALFaAAC6DuYSvNlWNmKS7TlNgQ"},
        {"title": "Глава 21", "file_id": "CQACAgIAAxkBAAICz2hSZxmiKlHGFdG548twV1aWHL9eAALJaAAC6DuYSpwEEBTz9HJHNgQ"},
        {"title": "Глава 22", "file_id": "CQACAgIAAxkBAAIC0WhSZyfEeUMfirlKEpL0n87WFmjFAALKaAAC6DuYSsp8ZBq-c7yqNgQ"},
        {"title": "Глава 23", "file_id": "CQACAgIAAxkBAAIC02hSZzOUcAw7liFduXIM7a-seuhvAALMaAAC6DuYSs03FEodiGa_NgQ"},
        {"title": "Глава 24", "file_id": "CQACAgIAAxkBAAIC1WhSZ0C4FDoIODI0QOQTRV_lWB_RAALOaAAC6DuYSukOCq_uvZojNgQ"},
        {"title": "Глава 25", "file_id": "CQACAgIAAxkBAAIC12hSZ1DfbWau4oQGHxrZv8Mbf9RnAALPaAAC6DuYSlBNe8nqAAGA1jYE"},
        {"title": "Глава 26", "file_id": "CQACAgIAAxkBAAIC2WhSZ17RtC0xaWaKmPKzIvfOjEEAA9FoAALoO5hK1y2tlgMT_ts2BA"},
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
    print(f"Книга '{book_title}' со всеми главами успешно добавлена в базу данных!")


if __name__ == '__main__':
    add_world_order_book()