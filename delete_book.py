from database import session, Book

def delete_book_by_title():
    """
    Скрипт для удаления книги из базы данных по ее точному названию.
    """
    print("--- Удаление книги из базы данных ---")
    
    # Запрашиваем у пользователя точное название книги
    book_title_to_delete = input("Введите точное название книги, которую хотите удалить: ")

    # Ищем книгу в базе данных
    book = session.query(Book).filter(Book.title == book_title_to_delete).first()

    # Если книга найдена, запрашиваем подтверждение и удаляем
    if book:
        print(f"\nНайдена книга: '{book.title}' автора '{book.author.name}'.")
        # Запрашиваем подтверждение
        confirm = input("Вы уверены, что хотите удалить эту книгу и все ее главы? (y/n): ")
        
        if confirm.lower() == 'y':
            session.delete(book)
            session.commit()
            print(f"Книга '{book.title}' была успешно удалена.")
        else:
            print("Удаление отменено.")
    else:
        # Если книга не найдена
        print(f"Книга с названием '{book_title_to_delete}' не найдена в базе данных.")

if __name__ == '__main__':
    delete_book_by_title()