from database import session, Author, Book, AudioFile, Genre

def add_mysterious_island_chapters():
    """
    Скрипт для ПОЛНОГО ОБНОВЛЕНИЯ аудио-глав 
    для книги 'Таинственный остров'.
    """
    
    book_title = "Таинственный остров"
    author_name = "Жюль Верн"
    
    # --- ВАЖНО: Убедитесь, что здесь исправлен ID для Главы 13 ---
    chapters = [
        {"title": "Глава 1", "file_id": "CQACAgIAAxkBAAIBbWhRnbK1FMr4-rZqUT8ggqQ1W_AAA3R4AALoO5BKgSyqigX4WCA2BA"},
        {"title": "Глава 2", "file_id": "CQACAgIAAxkBAAIBb2hRncuGINr40PmFLMADL8WstbI8AAJ2eAAC6DuQSn-om1ncFpqlNgQ"},
        {"title": "Глава 3", "file_id": "CQACAgIAAxkBAAIBcWhRneKT_ucn9OFjOBTbuV4DowuhAAJ4eAAC6DuQSs-peFc7ieoCNgQ"},
        {"title": "Глава 4", "file_id": "CQACAgIAAxkBAAIBc2hRnfX3PUWHD335PG2ICNVAO7NVAAJ7eAAC6DuQSlQiAV7C7tzONgQ"},
        {"title": "Глава 5", "file_id": "CQACAgIAAxkBAAIBdWhRngoad-oH-iTjcFZTnwIq5HtvAAJ8eAAC6DuQSrDztREJrEaJNgQ"},
        {"title": "Глава 6", "file_id": "CQACAgIAAxkBAAIBd2hRnhykuqcm7IDvy_Ro1JqIZQABfQACgHgAAug7kEoaQBSJqciPBjYE"},
        {"title": "Глава 7", "file_id": "CQACAgIAAxkBAAIBeWhRnjVTdPvFtknA-pGNs604dHxmAAKCeAAC6DuQSoj-qwABZuJfWTYE"},
        {"title": "Глава 8", "file_id": "CQACAgIAAxkBAAIBe2hRnkqc_VhSoTaVQebo3ObZe8QNAAKDeAAC6DuQStRDpmmJjaBzNgQ"},
        {"title": "Глава 9", "file_id": "CQACAgIAAxkBAAIBfWhRnlxZp2-VvpCZVbojGapIP9ZcAAKFeAAC6DuQSnAhr1--wR-YNgQ"},
        {"title": "Глава 10", "file_id": "CQACAgIAAxkBAAIBf2hRnm8Pd8VCIlKPAxBsJuQfOandAAKGeAAC6DuQSmDhD_3sEuopNgQ"},
        {"title": "Глава 11", "file_id": "CQACAgIAAxkBAAIBgWhRnoWADw35r0Tb5NkNMeI6TP9tAAKKeAAC6DuQShlI8lj3jZa1NgQ"},
        {"title": "Глава 12", "file_id": "CQACAgIAAxkBAAIBg2hRnqW8V5qmbBfsvgti5VK7Sd6KAAKLeAAC6DuQSkI-fwZ5hxe0NgQ"},
        {"title": "Глава 13", "file_id": "CQACAgIAAxkBAAIBhWhRnrhHxrG8i3Tw7vtECkDfK9g2AAKNeAAC6DuQSjkDlGWbhH95NgQ"},
        {"title": "Глава 14", "file_id": "CQACAgIAAxkBAAIBh2hRnsrXyGnPHnhvQPbikmRWs6SsAAKPeAAC6DuQShVYXeZHAnFUNgQ"},
        {"title": "Глава 15", "file_id": "CQACAgIAAxkBAAIBiWhRnt-QTHLygTSYBmKpt0A9xrHDAAKReAAC6DuQSnIagjmVMJmINgQ"},
        {"title": "Глава 16", "file_id": "CQACAgIAAxkBAAIBi2hRnvAy1SIbbmLLeshZXolTvosGAAKSeAAC6DuQSl6WwvkvuseINgQ"},
        {"title": "Глава 17", "file_id": "CQACAgIAAxkBAAIBjWhRnwPc7yF65TVV94O45-M7CM5nAAKVeAAC6DuQSvopDrm-3XrqNgQ"},
        {"title": "Глава 18", "file_id": "CQACAgIAAxkBAAIBj2hRnxd_eyn8fBjD6dZr3kdL1_LxAAKWeAAC6DuQSvE7u85ys_MiNgQ"},
        {"title": "Глава 19", "file_id": "CQACAgIAAxkBAAIBkWhRnylNtiBTMxpBJ6Aq_XygKRq3AAL1cwACcBqQSl-LF1FQuNjeNgQ"},
        {"title": "Глава 20", "file_id": "CQACAgIAAxkBAAIBk2hRnz2xO78M62WGdQLarY06esvtAAKXeAAC6DuQSj_Sn9-EakbSNgQ"},
        {"title": "Глава 21", "file_id": "CQACAgIAAxkBAAIBlWhRn0xmo9QNiSTgPz5Jyet6lLjVAAKZeAAC6DuQSrUZejvTTfw-NgQ"},
        {"title": "Глава 22", "file_id": "CQACAgIAAxkBAAIBl2hRn195C_6L399OvbVTE5y7wDcnAAKaeAAC6DuQSscQ4OpoXI74NgQ"},
        {"title": "Глава 23", "file_id": "CQACAgIAAxkBAAIBmWhRn3JkC2_aOymbpQS36E7ecevTAAKceAAC6DuQSl9plyrWQ7CWNgQ"},
        {"title": "Глава 24", "file_id": "CQACAgIAAxkBAAIBm2hRn4ESuVKGMPeAvZ69O_2c6qlHAAKeeAAC6DuQSqGajg2SL8oTNgQ"},
        {"title": "Глава 25", "file_id": "CQACAgIAAxkBAAIBnWhRn5Ff0JiqN0bbWqTLy6R6CXidAAKieAAC6DuQSgEr-af8_L1HNgQ"},
        {"title": "Глава 26", "file_id": "CQACAgIAAxkBAAIBn2hRn6zR8evtYC6R9gV6preSMPUYAAKjeAAC6DuQSs8zjJC3sLjqNgQ"},
        {"title": "Глава 27", "file_id": "CQACAgIAAxkBAAIBoWhRn7wBQ1p6YC5Y356VVNXQTY_mAAKmeAAC6DuQStrfdrnjqFKoNgQ"},
        {"title": "Глава 28", "file_id": "CQACAgIAAxkBAAIBo2hRn83cTidML1E_-vy3Apebcs3hAAKneAAC6DuQShNThKIJK8hRNgQ"},
    ]
    # --------------------------------------------------------------------

    # --- УЛУЧШЕНИЕ: Сначала удаляем старую книгу, если она есть, чтобы избежать дублей ---
    old_book = session.query(Book).join(Author).filter(
        Book.title == book_title,
        Author.name == author_name
    ).first()
    
    if old_book:
        print(f"Найдена и удаляется старая версия книги '{book_title}'...")
        session.delete(old_book)
        session.commit()
    # --------------------------------------------------------------------------------

    # Находим автора и жанр (или создаем, если их нет)
    author = session.query(Author).filter_by(name=author_name).first()
    if not author:
        author = Author(name=author_name)
        session.add(author)

    genre = session.query(Genre).filter_by(name="Приключения").first()
    if not genre:
        genre = Genre(name="Приключения")
        session.add(genre)

    # Создаем новую запись для книги
    new_book = Book(title=book_title, author=author, genre=genre)
    session.add(new_book)
    print(f"Добавлена новая, исправленная версия книги: '{book_title}'")
    
    # Привязываем к ней аудиофайлы
    for chapter_data in chapters:
        # Проверяем, что ID был вставлен
        if "СЮДА_ВСТАВИТЬ" in chapter_data["file_id"]:
            print(f"КРИТИЧЕСКАЯ ОШИБКА: Вы не вставили исправленный ID для главы '{chapter_data['title']}'.")
            print("Пожалуйста, исправьте ID в скрипте и запустите его снова.")
            return # Прерываем выполнение скрипта

        audio = AudioFile(book=new_book, title=chapter_data["title"], file_id=chapter_data["file_id"])
        session.add(audio)
    
    session.commit()
    print(f"Аудио-главы для книги '{book_title}' успешно обновлены в базе данных!")


if __name__ == '__main__':
    add_mysterious_island_chapters()