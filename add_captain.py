from database import session, Author, Book, AudioFile

def add_captains_daughter_chapters():
    """
    Скрипт для добавления аудио-глав к уже существующей
    книге 'Капитанская дочка'.
    """
    
    # --- Данные о книге (должны совпадать с тем, что в базе) ---
    book_title = "Капитанская дочка"
    author_name = "Александр Пушкин"
    
    # --- Список глав, сформированный из вашего файла ---
    chapters = [
        {"title": "Глава 1: Сержант гвардии", "file_id": "CQACAgIAAxkBAAIBPmhRl-iwaqkt8F96_ql3zxLr23ByAALxdwAC6DuQSp_Pazi64e-vNgQ"},
        {"title": "Глава 2: Вожатый", "file_id": "CQACAgIAAxkBAAIBQGhRmHdx3cMk2DpH3m_MxqIj0FZYAAIDeAAC6DuQSuaFqNE8SavONgQ"},
        {"title": "Глава 3: Крепость", "file_id": "CQACAgIAAxkBAAIBQmhRmJXPKZZ8veTxqrERjdWmh8XxAAIJeAAC6DuQSlOgeEmuiBZvNgQ"},
        {"title": "Глава 4: Поединок", "file_id": "CQACAgIAAxkBAAIBRGhRmLCIHw8BiOA80sHrzU8BIlUiAAINeAAC6DuQSq_hoe6nXjJ_NgQ"},
        {"title": "Глава 5: Любовь", "file_id": "CQACAgIAAxkBAAIBRmhRmMiYNi6TafmPNLYVgHIT3nqkAAIOeAAC6DuQSvjHs2SNVV_bNgQ"},
        {"title": "Глава 6: Пугачёвщина", "file_id": "CQACAgIAAxkBAAIBSGhRmN7ZgQb9H8LP9GuoqK8e9RAwAAIQeAAC6DuQSuh5nBTnn16bNgQ"},
        {"title": "Глава 7: Приступ", "file_id": "CQACAgIAAxkBAAIBSmhRmPK1lZpeNKRaPOqhAxzkdsgiAAIUeAAC6DuQSr5i8eeFSlHENgQ"},
        {"title": "Глава 8: Незваный гость", "file_id": "CQACAgIAAxkBAAIBTGhRmQ1hr8-zqbuv46doIBHO71jlAAIYeAAC6DuQShSxoIcAAaUW3zYE"},
        {"title": "Глава 9: Разлука", "file_id": "CQACAgIAAxkBAAIBTmhRmSoQ_j-vXIJyTLligLEBGweNAAIaeAAC6DuQSnPpr91qSs_-NgQ"},
        {"title": "Глава 10: Осада города", "file_id": "CQACAgIAAxkBAAIBUGhRmT7SRw3zySq6ifVPj1vsJqm9AAIfeAAC6DuQSsW_A--ucSW0NgQ"},
        {"title": "Глава 11: Мятежная слобода", "file_id": "CQACAgIAAxkBAAIBUmhRmVkeitWlfsDboQ3RD4jsTbh_AAIjeAAC6DuQSqzteTCBQvRsNgQ"},
        {"title": "Глава 12: Сирота", "file_id": "CQACAgIAAxkBAAIBVGhRmW1nFejDg4ZESdAfPAf_9aWkAAIleAAC6DuQStFcNViVkppNNgQ"},
        {"title": "Глава 13: Арест", "file_id": "CQACAgIAAxkBAAIBVmhRmYAMeYi444Sr6pRpcSbG7gXJAAIneAAC6DuQSonFRSDNZtsvNgQ"},
        {"title": "Глава 14: Суд", "file_id": "CQACAgIAAxkBAAIBWGhRmZUbp9Dd7FuRr7GyideDQsTlAAIreAAC6DuQSoxdMmw7kBghNgQ"},
        {"title": "Пропущенная глава", "file_id": "CQACAgIAAxkBAAIBWmhRmaoVUbr-FPZ3cbPuS-OiqOKBAAIveAAC6DuQSmh4fmDyH_xyNgQ"},
    ]
    # --------------------------------------------------------------------

    # Находим книгу в базе данных
    book_to_update = session.query(Book).join(Author).filter(
        Book.title == book_title,
        Author.name == author_name
    ).first()

    # Если книга не найдена, выводим ошибку и выходим
    if not book_to_update:
        print(f"ОШИБКА: Книга '{book_title}' автора '{author_name}' не найдена в базе.")
        print("Сначала запустите 'setup_database.py', чтобы создать ее.")
        return
        
    # Проверяем, нет ли у книги уже добавленных глав, чтобы не дублировать
    if book_to_update.audio_files:
        print(f"У книги '{book_title}' уже есть аудиофайлы. Добавление отменено, чтобы избежать дублей.")
        return

    print(f"Найдена книга: '{book_to_update.title}'. Добавляем аудиофайлы...")

    # Привязываем к найденной книге аудиофайлы
    for chapter_data in chapters:
        audio = AudioFile(
            book=book_to_update, 
            title=chapter_data["title"], 
            file_id=chapter_data["file_id"]
        )
        session.add(audio)
    
    # Сохраняем изменения
    session.commit()
    print(f"Аудио-главы для книги '{book_title}' успешно добавлены в базу данных!")


if __name__ == '__main__':
    add_captains_daughter_chapters()