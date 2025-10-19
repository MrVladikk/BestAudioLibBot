from database import session, Genre, Book

def manage_genres():
    """
    Утилита для просмотра и безопасного удаления жанров.
    """
    print("--- Управление жанрами ---")
    
    # Получаем и выводим все жанры с их ID
    all_genres = session.query(Genre).order_by(Genre.name).all()
    
    if not all_genres:
        print("В базе данных пока нет ни одного жанра.")
        return

    print("\nСписок существующих жанров:")
    for genre in all_genres:
        print(f"  ID: {genre.id}  |  Название: {genre.name}")
        
    print("-" * 30)

    try:
        # Запрашиваем ID жанра для удаления
        genre_id_to_delete = int(input("Введите ID жанра, который хотите удалить (или любую букву для отмены): "))
    except ValueError:
        print("Отмена операции.")
        return

    # Ищем выбранный жанр в базе
    genre_to_delete = session.query(Genre).filter_by(id=genre_id_to_delete).first()

    if not genre_to_delete:
        print(f"ОШИБКА: Жанр с ID {genre_id_to_delete} не найден.")
        return

    # Проверяем, привязаны ли к этому жанру какие-либо книги
    books_in_genre = session.query(Book).filter_by(genre_id=genre_to_delete.id).count()

    if books_in_genre > 0:
        print(f"\nОШИБКА: Нельзя удалить жанр '{genre_to_delete.name}', так как он используется в {books_in_genre} книге(ах).")
        print("Сначала измените жанр у этих книг через админ-панель в боте.")
        return

    # Если жанр "свободен", запрашиваем подтверждение
    print(f"\nНайден жанр '{genre_to_delete.name}', который не используется ни в одной книге.")
    confirm = input("Вы уверены, что хотите удалить этот жанр? (y/n): ")

    if confirm.lower() == 'y':
        session.delete(genre_to_delete)
        session.commit()
        print(f"✅ Жанр '{genre_to_delete.name}' был успешно удален.")
    else:
        print("Удаление отменено.")


if __name__ == '__main__':
    manage_genres()