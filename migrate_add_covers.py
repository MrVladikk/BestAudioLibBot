from sqlalchemy import create_engine, text

# Убедитесь, что имя файла базы данных совпадает с вашим
DB_FILE = "audiobooks.db"
engine = create_engine(f'sqlite:///{DB_FILE}')

def add_cover_column():
    """
    Добавляет колонку cover_file_id в таблицу books, если она еще не существует.
    """
    print("Проверка и обновление структуры базы данных...")
    
    # SQL-команда для добавления новой колонки
    # VARCHAR - это стандартный тип для текстовых строк, как и String в SQLAlchemy
    add_column_sql = text("ALTER TABLE books ADD COLUMN cover_file_id VARCHAR")

    try:
        # Пытаемся выполнить команду
        with engine.connect() as connection:
            connection.execute(add_column_sql)
        print("Успех! Колонка 'cover_file_id' была успешно добавлена в таблицу 'books'.")
    except Exception as e:
        # Если команда не удалась, скорее всего, колонка уже существует
        if "duplicate column name" in str(e):
            print("Колонка 'cover_file_id' уже существует. Никаких изменений не требуется.")
        else:
            # Если произошла другая ошибка, выводим ее
            print(f"Произошла непредвиденная ошибка: {e}")

if __name__ == '__main__':
    add_cover_column()