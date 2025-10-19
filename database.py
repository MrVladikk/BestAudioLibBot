import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, UniqueConstraint, DateTime
from datetime import datetime, timezone

# Настройка логирования для диагностики
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Строка подключения к PostgreSQL
DB_CONNECTION_STRING = 'postgresql+asyncpg://neondb_owner:npg_JwW3qebOzH8R@ep-fragrant-resonance-a9vrs98d-pooler.gwc.azure.neon.tech/neondb'

# Создание асинхронного движка с настройками для стабильности
async_engine = create_async_engine(
    DB_CONNECTION_STRING,
    pool_pre_ping=True,        # Проверка соединения перед использованием
    pool_recycle=3600,         # Переработка соединений каждые 3600 секунд
    pool_size=10,              # Размер пула соединений
    max_overflow=20,           # Максимальное количество дополнительных соединений
    connect_args={'ssl': 'require'},  # Требование SSL для подключения
    echo=False                 # Отключено логирование SQL-запросов (включите для отладки: echo=True)
)

# Создание фабрики асинхронных сессий
async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

Base = declarative_base()

# Функция для инициализации таблиц в базе данных
async def init_db():
    logger.debug("Начало инициализации базы данных...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.debug("База данных успешно инициализирована.")

# --- Модели таблиц ---
class Genre(Base):
    __tablename__ = 'genres'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    books = relationship("Book", back_populates="genre")

class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    books = relationship("Book", back_populates="author")

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    cover_file_id = Column(String, nullable=True)
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=False)
    genre_id = Column(Integer, ForeignKey('genres.id'), nullable=False)
    author = relationship("Author", back_populates="books")
    genre = relationship("Genre", back_populates="books")
    audio_files = relationship("AudioFile", back_populates="book", cascade="all, delete-orphan")
    user_progress = relationship("UserProgress", back_populates="book", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="book", cascade="all, delete-orphan")

class AudioFile(Base):
    __tablename__ = 'audio_files'
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    title = Column(String, nullable=False)
    file_id = Column(String, nullable=False, unique=True)
    book = relationship("Book", back_populates="audio_files")

class UserProgress(Base):
    __tablename__ = 'user_progress'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    last_chapter_id = Column(Integer, ForeignKey('audio_files.id'), nullable=False)
    __table_args__ = (UniqueConstraint('user_id', 'book_id', name='_user_book_progress_uc'),)
    book = relationship("Book", back_populates="user_progress")

class Favorite(Base):
    __tablename__ = 'favorites'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    book = relationship("Book", back_populates="favorites")
    __table_args__ = (UniqueConstraint('user_id', 'book_id', name='_user_book_favorite_uc'),)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    first_name = Column(String)
    username = Column(String, nullable=True)
    date_joined = Column(DateTime, default=lambda: datetime.now(timezone.utc))