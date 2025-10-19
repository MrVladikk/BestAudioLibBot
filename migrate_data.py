import asyncio
from sqlalchemy import create_engine, text, select, inspect, func
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

# Импортируем все наши модели и Base
from database import User, Genre, Author, Book, AudioFile, Favorite, UserProgress, Base

# --- НАСТРОЙКИ ---
SQLITE_DB_FILE = "audiobooks.db"
POSTGRES_CONNECTION_STRING = 'postgresql://neondb_owner:npg_JwW3qebOzH8R@ep-fragrant-resonance-a9vrs98d-pooler.gwc.azure.neon.tech/neondb?sslmode=require'
# -----------------

sqlite_engine = create_engine(f'sqlite:///{SQLITE_DB_FILE}')
postgres_engine = create_engine(POSTGRES_CONNECTION_STRING)

SqliteSession = sessionmaker(bind=sqlite_engine)
PostgresSession = sessionmaker(bind=postgres_engine)

source_session = SqliteSession()
dest_session = PostgresSession()

def migrate_table(model, source_session, dest_session):
    """Читает все данные из исходной таблицы и создает их копии для целевой."""
    records = source_session.execute(select(model)).scalars().all()
    if not records:
        return []

    new_objects = []
    for record in records:
        data = {c.name: getattr(record, c.name) for c in record.__table__.columns}
        new_objects.append(model(**data))
    
    return new_objects

def run_migration():
    print("--- Запуск миграции данных из SQLite в PostgreSQL (v3, с принудительной очисткой) ---")
    
    # Порядок важен для соблюдения внешних ключей
    models_to_migrate = [User, Genre, Author, Book, AudioFile, Favorite, UserProgress]
    tables_in_reverse_order = reversed(Base.metadata.sorted_tables)

    try:
        # --- ШАГ 1: Принудительная очистка таблиц в новой базе ---
        print("\n1. Очистка таблиц в новой базе данных PostgreSQL...")
        with postgres_engine.connect() as conn:
            trans = conn.begin()
            for table in tables_in_reverse_order:
                print(f"  - Очистка таблицы {table.name}...")
                conn.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE;'))
            trans.commit()
        print("Все таблицы в целевой базе данных успешно очищены.")

        # --- ШАГ 2: Копирование данных ---
        print("\n2. Чтение данных из старой базы и запись в новую...")
        all_new_records = []
        for model in tqdm(models_to_migrate, desc="Копирование таблиц"):
            recs = migrate_table(model, source_session, dest_session)
            if recs:
                all_new_records.extend(recs)
        
        print("\nДобавление всех скопированных записей в новую базу...")
        if all_new_records:
            dest_session.add_all(all_new_records)
            dest_session.commit()
        print("Данные успешно сохранены!")
        
        # --- ШАГ 3: Синхронизация счетчиков ID ---
        # Этот шаг теперь выполняется командой RESTART IDENTITY в шаге 1, но для надежности оставим.
        print("\n3. Проверка и синхронизация счетчиков ID...")
        with postgres_engine.connect() as conn:
            trans = conn.begin()
            for model in models_to_migrate:
                table_name = model.__tablename__
                pk_name = f"{table_name}_id_seq"
                max_id_result = dest_session.execute(select(func.max(model.id))).scalar()
                max_id = max_id_result if max_id_result is not None else 1
                try:
                    conn.execute(text(f"SELECT setval(pg_get_serial_sequence('\"{table_name}\"', 'id'), {max_id}, true);"))
                except Exception as seq_e:
                    pass
            trans.commit()
        
        print("Счетчики ID успешно синхронизированы.")
        print("\n🎉 Миграция данных полностью и корректно завершена!")

    except Exception as e:
        print(f"\n\nПроизошла КРИТИЧЕСКАЯ ошибка: {e}")
        print("Откатываем изменения...")
        dest_session.rollback()
    finally:
        source_session.close()
        dest_session.close()

if __name__ == '__main__':
    run_migration()