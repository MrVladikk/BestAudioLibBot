import asyncio
import logging
import os
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import BotCommand
from aiogram.filters.command import Command
from aiogram.filters import StateFilter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Chat
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.exc import OperationalError

from database import async_session_factory, Genre, Book, AudioFile, Author, UserProgress, Favorite, User

# Настройка логирования для диагностики
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Конфигурация бота
API_TOKEN = '7743716366:AAFyNE4FCaSWvRfo65pDjOOoC_doWH7jBls'
ADMIN_ID = 705446667
CHAPTERS_PER_PAGE = 10
FAVORITES_PER_PAGE = 10
BOOKS_PER_PAGE = 5

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Состояния для FSM
class SearchState(StatesGroup):
    waiting_for_query = State()

class AdminState(StatesGroup):
    waiting_for_chapter_audio = State()
    waiting_for_broadcast_message = State()
    confirm_broadcast = State()
    editing_book_waiting_for_new_value = State()

# Клавиатуры
main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📚 Жанры", callback_data="browse_genres"), InlineKeyboardButton(text="👤 Авторы", callback_data="browse_authors")],
    [InlineKeyboardButton(text="⭐️ Мое избранное", callback_data="my_favorites:0")],
    [InlineKeyboardButton(text="🔍 Поиск", callback_data="start_search")],
    [InlineKeyboardButton(text="🎲 Случайная книга", callback_data="random_book")]
])
button_to_main_menu = InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main_menu")

admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
    [InlineKeyboardButton(text="✍️ Редактировать книгу", callback_data="admin_edit_book_page:0")],
    [InlineKeyboardButton(text="🗑️ Удалить книгу", callback_data="admin_delete_book_page:0")],
    [InlineKeyboardButton(text="➕ Добавить главу к книге", callback_data="admin_add_chapter_page:0")],
    [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="admin_broadcast")]
])
button_to_admin_panel = InlineKeyboardButton(text="⬅️ Назад в админ-панель", callback_data="to_admin_panel")

# Асинхронная функция для выполнения запросов с повторными попытками
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(OperationalError)
)
async def execute_query(session: AsyncSession, query):
    logger.debug("Выполнение запроса: %s", query)
    result = await session.execute(query)
    logger.debug("Запрос выполнен успешно")
    return result

# Отправляет или редактирует сообщение с карточкой книги
async def show_book_card(target_chat: Chat, book_id: int, is_new_message: bool = False):
    logger.debug("Вызов show_book_card для book_id=%d, is_new_message=%s", book_id, is_new_message)
    async with async_session_factory() as session:
        try:
            # Используем joinedload для предзагрузки author и genre
            query = select(Book).filter(Book.id == book_id).options(joinedload(Book.author), joinedload(Book.genre))
            book = (await execute_query(session, query)).scalars().first()
            if not book:
                logger.warning("Книга с id=%d не найдена", book_id)
                return

            card_text = f"<b>{book.title}</b>\n\n<b>Автор:</b> {book.author.name}\n<b>Жанр:</b> {book.genre.name}"
            builder = InlineKeyboardBuilder()
            is_favorite = (await execute_query(session, select(Favorite).filter_by(user_id=target_chat.id, book_id=book_id))).scalars().first()
            if is_favorite:
                builder.add(InlineKeyboardButton(text="🌟 Убрать из избранного", callback_data=f"rm_fav:{book_id}"))
            else:
                builder.add(InlineKeyboardButton(text="⭐️ Добавить в избранное", callback_data=f"add_fav:{book_id}"))
            progress = (await execute_query(session, select(UserProgress).filter_by(user_id=target_chat.id, book_id=book_id))).scalars().first()
            if progress:
                last_chapter = (await execute_query(session, select(AudioFile).filter_by(id=progress.last_chapter_id))).scalars().first()
                if last_chapter:
                    builder.add(InlineKeyboardButton(
                        text=f"▶️ Продолжить с '{last_chapter.title}'",
                        callback_data=f"chapter:{last_chapter.id}"
                    ))
            builder.add(InlineKeyboardButton(text="📖 Смотреть все главы", callback_data=f"ch_page:{book.id}:0"))
            builder.row(button_to_main_menu)
            builder.adjust(1)
            logger.debug("Отправка карточки книги: %s", card_text)
            if book.cover_file_id:
                await bot.send_photo(
                    chat_id=target_chat.id,
                    photo=book.cover_file_id,
                    caption=card_text,
                    reply_markup=builder.as_markup()
                )
            elif is_new_message:
                await bot.send_message(
                    chat_id=target_chat.id,
                    text=card_text,
                    reply_markup=builder.as_markup()
                )
            else:
                await target_chat.edit_text(card_text, reply_markup=builder.as_markup())
        except Exception as e:
            logger.error("Ошибка в show_book_card: %s", e)
            await session.rollback()
            raise

# Создаёт клавиатуру для выбора глав книги
async def create_chapters_keyboard(book_id: int, page: int = 0) -> InlineKeyboardBuilder:
    async with async_session_factory() as session:
        try:
            chapters_count = (await execute_query(session, select(func.count(AudioFile.id)).filter(AudioFile.book_id == book_id))).scalar()
            chapters_on_page = (await execute_query(
                session,
                select(AudioFile).filter(AudioFile.book_id == book_id).order_by(AudioFile.id).limit(CHAPTERS_PER_PAGE).offset(page * CHAPTERS_PER_PAGE)
            )).scalars().all()
            builder = InlineKeyboardBuilder()
            for chapter in chapters_on_page:
                builder.add(InlineKeyboardButton(text=chapter.title, callback_data=f"chapter:{chapter.id}"))
            builder.adjust(1)
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"ch_page:{book_id}:{page-1}"))
            if (page + 1) * CHAPTERS_PER_PAGE < chapters_count:
                nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"ch_page:{book_id}:{page+1}"))
            if nav_buttons:
                builder.row(*nav_buttons)
            builder.row(InlineKeyboardButton(text="⬅️ Назад к книге", callback_data=f"book:{book_id}"))
            return builder
        except Exception as e:
            logger.error("Ошибка в create_chapters_keyboard: %s", e)
            await session.rollback()
            return InlineKeyboardBuilder()

# Создаёт клавиатуру для админских действий с книгами
async def create_admin_books_keyboard(page: int = 0, callback_prefix: str = "del_confirm") -> InlineKeyboardBuilder:
    async with async_session_factory() as session:
        try:
            books_count = (await execute_query(session, select(func.count(Book.id)))).scalar()
            books_on_page = (await execute_query(
                session,
                select(Book).order_by(Book.title).limit(BOOKS_PER_PAGE).offset(page * BOOKS_PER_PAGE)
            )).scalars().all()
            builder = InlineKeyboardBuilder()
            for book in books_on_page:
                builder.add(InlineKeyboardButton(text=book.title, callback_data=f"{callback_prefix}:{book.id}"))
            builder.adjust(1)
            page_callback_prefix = "admin_delete_book_page"
            if callback_prefix == "add_chapter_to":
                page_callback_prefix = "admin_add_chapter_page"
            elif callback_prefix == "edit_book":
                page_callback_prefix = "admin_edit_book_page"
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{page_callback_prefix}:{page-1}"))
            if (page + 1) * BOOKS_PER_PAGE < books_count:
                nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"{page_callback_prefix}:{page+1}"))
            if nav_buttons:
                builder.row(*nav_buttons)
            builder.row(button_to_admin_panel)
            return builder
        except Exception as e:
            logger.error("Ошибка в create_admin_books_keyboard: %s", e)
            await session.rollback()
            return InlineKeyboardBuilder()

# Устанавливает команды главного меню бота
async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="/start", description="Перезапустить бота"),
        BotCommand(command="/menu", description="Показать главное меню"),
        BotCommand(command="/clear", description="Очистить экран и показать меню"),
        BotCommand(command="/admin", description="Панель администратора")
    ]
    await bot.set_my_commands(main_menu_commands)

# Обновляет карточку книги после изменения статуса избранного
async def refresh_book_card(callback: types.CallbackQuery):
    book_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    async with async_session_factory() as session:
        try:
            # Используем joinedload для предзагрузки author и genre
            query = select(Book).filter_by(id=book_id).options(joinedload(Book.author), joinedload(Book.genre))
            book = (await execute_query(session, query)).scalars().first()
            if not book:
                logger.warning("Книга с id=%d не найдена", book_id)
                return
            card_text = f"<b>{book.title}</b>\n\n<b>Автор:</b> {book.author.name}\n<b>Жанр:</b> {book.genre.name}"
            builder = InlineKeyboardBuilder()
            is_favorite = (await execute_query(session, select(Favorite).filter_by(user_id=user_id, book_id=book_id))).scalars().first()
            if is_favorite:
                builder.add(InlineKeyboardButton(text="🌟 Убрать из избранного", callback_data=f"rm_fav:{book_id}"))
            else:
                builder.add(InlineKeyboardButton(text="⭐️ Добавить в избранное", callback_data=f"add_fav:{book_id}"))
            progress = (await execute_query(session, select(UserProgress).filter_by(user_id=user_id, book_id=book_id))).scalars().first()
            if progress:
                last_chapter = (await execute_query(session, select(AudioFile).filter_by(id=progress.last_chapter_id))).scalars().first()
                if last_chapter:
                    builder.add(InlineKeyboardButton(
                        text=f"▶️ Продолжить с '{last_chapter.title}'",
                        callback_data=f"chapter:{last_chapter.id}"
                    ))
            builder.add(InlineKeyboardButton(text="📖 Смотреть все главы", callback_data=f"ch_page:{book.id}:0"))
            builder.row(button_to_main_menu)
            builder.adjust(1)
            try:
                if callback.message.photo:
                    await callback.message.edit_caption(caption=card_text, reply_markup=builder.as_markup())
                else:
                    await callback.message.edit_text(card_text, reply_markup=builder.as_markup())
            except TelegramBadRequest as e:
                logger.error("Не удалось обновить карточку: %s", e)
        except Exception as e:
            logger.error("Ошибка в refresh_book_card: %s", e)
            await session.rollback()

# Обработчик команды /admin для входа в панель администратора
@dp.message(Command("admin"))
async def admin_panel(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("Добро пожаловать в панель администратора!", reply_markup=admin_keyboard)

# Начало процесса рассылки
@dp.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Доступ запрещён.", show_alert=True)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Да, начать рассылку", callback_data="broadcast:start"))
    builder.add(InlineKeyboardButton(text="Нет, отменить", callback_data="to_admin_panel"))
    await callback.message.edit_text(
        "Вы уверены, что хотите создать сообщение для рассылки?\n"
        "Его получат ВСЕ пользователи бота.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# Отмена рассылки на начальном этапе
@dp.callback_query(F.data == "broadcast:cancel")
async def broadcast_cancel_initial(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Рассылка отменена.")
    await callback.answer()

# Запрос сообщения для рассылки
@dp.callback_query(F.data == "broadcast:start")
async def broadcast_get_message(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.waiting_for_broadcast_message)
    await callback.message.edit_text(
        "Хорошо. Теперь пришлите сообщение, которое вы хотите разослать пользователям. "
        "Это может быть текст, фото с подписью, стикер и т.д."
    )
    await callback.answer()

# Предварительный просмотр сообщения рассылки
@dp.message(AdminState.waiting_for_broadcast_message, F.content_type.in_({'text', 'photo', 'sticker', 'video', 'document'}))
async def broadcast_preview(message: types.Message, state: FSMContext):
    await state.update_data(
        broadcast_chat_id=message.chat.id,
        broadcast_message_id=message.message_id
    )
    await state.set_state(AdminState.confirm_broadcast)
    await message.answer("Вот так будет выглядеть ваше сообщение для пользователей. Всё верно?")
    await bot.copy_message(
        chat_id=message.chat.id,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Отправить всем", callback_data="broadcast:send"))
    builder.add(InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast:cancel"))
    await message.answer("Отправляем?", reply_markup=builder.as_markup())

# Выполнение рассылки всем пользователям
@dp.callback_query(AdminState.confirm_broadcast, F.data == "broadcast:send")
async def broadcast_run(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    from_chat_id = data.get('broadcast_chat_id')
    message_id = data.get('broadcast_message_id')
    await state.clear()
    if not from_chat_id or not message_id:
        await callback.message.edit_text("Ошибка: данные для рассылки не найдены. Попробуйте снова.")
        return await callback.answer()
    async with async_session_factory() as session:
        try:
            users = (await execute_query(session, select(User.user_id))).scalars().all()
            await callback.message.edit_text(f"Начало рассылки... Всего пользователей: {len(users)}")
            await callback.answer()
            success_count = 0
            fail_count = 0
            for user_id in users:
                try:
                    await bot.copy_message(
                        chat_id=user_id,
                        from_chat_id=from_chat_id,
                        message_id=message_id
                    )
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    logger.error("Не удалось отправить сообщение пользователю %d: %s", user_id, e)
                await asyncio.sleep(0.1)
            await callback.message.answer(
                f"✅ Рассылка завершена!\n\n"
                f"Успешно отправлено: {success_count}\n"
                f"Не удалось доставить: {fail_count} (пользователи заблокировали бота)"
            )
        except Exception as e:
            logger.error("Ошибка в broadcast_run: %s", e)
            await session.rollback()
            await callback.message.answer("Ошибка во время рассылки. Попробуйте позже.")

# Окончательная отмена рассылки
@dp.callback_query(AdminState.confirm_broadcast, F.data == "broadcast:cancel")
async def broadcast_cancel_final(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Рассылка отменена.")
    await callback.answer()

# Переход в админ-панель
@dp.callback_query(F.data == "to_admin_panel")
async def process_to_admin_panel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Добро пожаловать в панель администратора!", reply_markup=admin_keyboard)
    await callback.answer()

# Получение статистики бота
@dp.callback_query(F.data == "admin_stats")
async def get_admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Доступ запрещён.", show_alert=True)
    async with async_session_factory() as session:
        try:
            book_count = (await execute_query(session, select(func.count(Book.id)))).scalar()
            author_count = (await execute_query(session, select(func.count(Author.id)))).scalar()
            genre_count = (await execute_query(session, select(func.count(Genre.id)))).scalar()
            chapters_count = (await execute_query(session, select(func.count(AudioFile.id)))).scalar()
            total_users = (await execute_query(session, select(func.count(User.id)))).scalar()
            stats_text = (
                f"📊 **Статистика бота**:\n\n"
                f"👥 Всего пользователей: {total_users}\n"
                f"📚 Книг: {book_count}\n"
                f"👤 Авторов: {author_count}\n"
                f"🎨 Жанров: {genre_count}\n"
                f"🎧 Всего глав: {chapters_count}"
            )
            await callback.message.answer(stats_text)
            await callback.answer()
        except Exception as e:
            logger.error("Ошибка в get_admin_stats: %s", e)
            await session.rollback()
            await callback.message.answer("Ошибка подключения к базе данных. Попробуйте позже.")

# Список книг для удаления
@dp.callback_query(F.data.startswith("admin_delete_book_page:"))
async def admin_delete_book_list(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Доступ запрещён.", show_alert=True)
    page = int(callback.data.split(":")[1])
    builder = await create_admin_books_keyboard(page, callback_prefix="del_confirm")
    await callback.message.edit_text("Какую книгу вы хотите удалить?", reply_markup=builder.as_markup())
    await callback.answer()

# Подтверждение удаления книги
@dp.callback_query(F.data.startswith("del_confirm:"))
async def admin_delete_confirm(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Доступ запрещён.", show_alert=True)
    book_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        try:
            # Используем joinedload для предзагрузки данных книги
            query = select(Book).filter_by(id=book_id).options(joinedload(Book.author), joinedload(Book.genre))
            book = (await execute_query(session, query)).scalars().first()
            if not book:
                await callback.answer("Книга уже удалена.", show_alert=True)
                await process_to_admin_panel(callback, None)
                return
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="❗️ Да, удалить", callback_data=f"del_execute:{book.id}"))
            builder.add(InlineKeyboardButton(text="Отменить", callback_data="to_admin_panel"))
            await callback.message.edit_text(
                f"Вы уверены, что хотите безвозвратно удалить книгу '<b>{book.title}</b>' и все её главы?",
                reply_markup=builder.as_markup()
            )
            await callback.answer()
        except Exception as e:
            logger.error("Ошибка в admin_delete_confirm: %s", e)
            await session.rollback()
            await callback.message.answer("Ошибка при загрузке книги. Попробуйте позже.")

# Выполнение удаления книги
@dp.callback_query(F.data.startswith("del_execute:"))
async def admin_delete_execute(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Доступ запрещён.", show_alert=True)
    book_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        try:
            # Используем joinedload для предзагрузки данных книги
            query = select(Book).filter_by(id=book_id).options(joinedload(Book.author), joinedload(Book.genre))
            book = (await execute_query(session, query)).scalars().first()
            if book:
                book_title = book.title
                await session.delete(book)
                await session.commit()
                await callback.answer(f"Книга '{book_title}' удалена.", show_alert=True)
            else:
                await callback.answer("Книга уже была удалена.", show_alert=True)
            await process_to_admin_panel(callback, None)
        except Exception as e:
            logger.error("Ошибка в admin_delete_execute: %s", e)
            await session.rollback()
            await callback.answer("Ошибка при удалении книги. Попробуйте позже.", show_alert=True)

# Список книг для добавления главы
@dp.callback_query(F.data.startswith("admin_add_chapter_page:"))
async def admin_add_chapter_list(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Доступ запрещён.", show_alert=True)
    page = int(callback.data.split(":")[1])
    builder = await create_admin_books_keyboard(page, callback_prefix="add_chapter_to")
    await callback.message.edit_text("К какой книге вы хотите добавить главу?", reply_markup=builder.as_markup())
    await callback.answer()

# Выбор книги для добавления главы
@dp.callback_query(F.data.startswith("add_chapter_to:"))
async def admin_add_chapter_select_book(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Доступ запрещён.", show_alert=True)
    book_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        try:
            # Используем joinedload для предзагрузки данных книги
            query = select(Book).filter_by(id=book_id).options(joinedload(Book.author), joinedload(Book.genre))
            book = (await execute_query(session, query)).scalars().first()
            if not book:
                await callback.answer("Книга не найдена.", show_alert=True)
                return
            await state.set_state(AdminState.waiting_for_chapter_audio)
            await state.update_data(book_id=book_id)
            builder = InlineKeyboardBuilder()
            builder.add(button_to_admin_panel)
            await callback.message.edit_text(
                f"Вы добавляете главу к '<b>{book.title}</b>'.\n\n"
                f"Теперь отправьте аудиофайл для новой главы.",
                reply_markup=builder.as_markup()
            )
            await callback.answer()
        except Exception as e:
            logger.error("Ошибка в admin_add_chapter_select_book: %s", e)
            await session.rollback()
            await callback.answer("Ошибка при выборе книги. Попробуйте позже.", show_alert=True)

# Приём аудиофайла для новой главы
@dp.message(AdminState.waiting_for_chapter_audio, F.audio)
async def admin_add_chapter_receive_audio(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    book_id = state_data.get('book_id')
    if not book_id:
        await message.reply("Ошибка: ID книги не найден. Попробуйте снова.")
        await state.clear()
        return
    async with async_session_factory() as session:
        try:
            chapter_title = os.path.splitext(message.audio.file_name)[0] if message.audio.file_name else "Новая глава"
            new_chapter = AudioFile(book_id=book_id, title=chapter_title, file_id=message.audio.file_id)
            session.add(new_chapter)
            await session.commit()
            await message.reply(f"✅ Глава '{chapter_title}' успешно добавлена!")
            await admin_panel(message, state)
        except Exception as e:
            logger.error("Ошибка в admin_add_chapter_receive_audio: %s", e)
            await session.rollback()
            await message.reply("Ошибка при добавлении главы. Попробуйте позже.")

# Список книг для редактирования
@dp.callback_query(F.data.startswith("admin_edit_book_page:"))
async def admin_edit_book_list(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Доступ запрещён.", show_alert=True)
    page = int(callback.data.split(":")[1])
    builder = await create_admin_books_keyboard(page, callback_prefix="edit_book")
    await callback.message.edit_text("Какую книгу вы хотите отредактировать?", reply_markup=builder.as_markup())
    await callback.answer()

# Выбор книги для редактирования
@dp.callback_query(F.data.startswith("edit_book:"))
async def admin_edit_book_select(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Доступ запрещён.", show_alert=True)
    await state.clear()
    book_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        try:
            # Используем joinedload для предзагрузки данных книги
            query = select(Book).filter_by(id=book_id).options(joinedload(Book.author), joinedload(Book.genre))
            book = (await execute_query(session, query)).scalars().first()
            if not book:
                return await callback.answer("Книга не найдена.", show_alert=True)
            await state.update_data(edit_book_id=book_id)
            text = f"Редактирование книги: <b>{book.title}</b>\nЧто вы хотите изменить?"
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Название", callback_data="edit_field:title"))
            builder.add(InlineKeyboardButton(text="Автора", callback_data="edit_field:author"))
            builder.add(InlineKeyboardButton(text="Жанр", callback_data="edit_field:genre"))
            builder.add(InlineKeyboardButton(text="Обложку", callback_data="edit_field:cover"))
            builder.adjust(2)
            builder.row(button_to_admin_panel)
            await callback.message.edit_text(text, reply_markup=builder.as_markup())
            await callback.answer()
        except Exception as e:
            logger.error("Ошибка в admin_edit_book_select: %s", e)
            await session.rollback()
            await callback.answer("Ошибка при выборе книги. Попробуйте позже.", show_alert=True)

# Выбор поля для редактирования
@dp.callback_query(StateFilter(None), F.data.startswith("edit_field:"))
async def admin_edit_field_select(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Доступ запрещён.", show_alert=True)
    field_to_edit = callback.data.split(":")[1]
    await state.update_data(field_to_edit=field_to_edit)
    await state.set_state(AdminState.editing_book_waiting_for_new_value)
    prompt_text = {
        "title": "Введите новое название книги:",
        "author": "Введите новое имя автора:",
        "genre": "Введите новое название жанра:",
        "cover": "Пришлите новую картинку для обложки:"
    }
    cancel_button = InlineKeyboardMarkup(inline_keyboard=[[button_to_admin_panel]])
    await callback.message.edit_text(prompt_text.get(field_to_edit, "Неизвестное поле."), reply_markup=cancel_button)
    await callback.answer()

# Приём текстового значения для редактирования
@dp.message(AdminState.editing_book_waiting_for_new_value, F.text)
async def admin_edit_receive_text(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    book_id = state_data.get('edit_book_id')
    field_to_edit = state_data.get('field_to_edit')
    if not all([book_id, field_to_edit]):
        await message.answer("Ошибка состояния. Нажмите /admin и попробуйте снова.", reply_markup=admin_keyboard)
        return await state.clear()
    async with async_session_factory() as session:
        try:
            # Используем joinedload для предзагрузки данных книги
            query = select(Book).filter_by(id=book_id).options(joinedload(Book.author), joinedload(Book.genre))
            book = (await execute_query(session, query)).scalars().first()
            if not book:
                await message.answer("Ошибка: не удалось найти книгу для обновления.")
                return await state.clear()
            new_value = message.text
            if field_to_edit == 'title':
                book.title = new_value
            elif field_to_edit == 'author':
                author = (await execute_query(session, select(Author).filter_by(name=new_value))).scalars().first()
                if not author:
                    author = Author(name=new_value)
                    session.add(author)
                book.author = author
            elif field_to_edit == 'genre':
                genre = (await execute_query(session, select(Genre).filter_by(name=new_value))).scalars().first()
                if not genre:
                    genre = Genre(name=new_value)
                    session.add(genre)
                book.genre = genre
            await session.commit()
            await state.clear()
            await message.answer("✅ Информация о книге успешно обновлена!", reply_markup=admin_keyboard)
        except Exception as e:
            logger.error("Ошибка в admin_edit_receive_text: %s", e)
            await session.rollback()
            await message.answer("Ошибка при обновлении книги. Попробуйте позже.")

# Приём новой обложки для книги
@dp.message(AdminState.editing_book_waiting_for_new_value, F.photo)
async def admin_edit_receive_cover(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    book_id = state_data.get('edit_book_id')
    field_to_edit = state_data.get('field_to_edit')
    if field_to_edit != 'cover':
        return await message.reply("Ожидался текст, а не фото. Пожалуйста, отправьте текст или отмените действие.")
    async with async_session_factory() as session:
        try:
            # Используем joinedload для предзагрузки данных книги
            query = select(Book).filter_by(id=book_id).options(joinedload(Book.author), joinedload(Book.genre))
            book = (await execute_query(session, query)).scalars().first()
            if not book:
                await message.answer("Ошибка: не удалось найти книгу для обновления.")
                return await state.clear()
            book.cover_file_id = message.photo[-1].file_id
            await session.commit()
            await state.clear()
            await message.answer("✅ Обложка книги успешно обновлена!", reply_markup=admin_keyboard)
        except Exception as e:
            logger.error("Ошибка в admin_edit_receive_cover: %s", e)
            await session.rollback()
            await message.answer("Ошибка при обновлении обложки. Попробуйте позже.")

# Обработчик команд /start, /menu, /clear
@dp.message(Command("start", "menu", "clear"))
async def send_welcome(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    async with async_session_factory() as session:
        try:
            logger.debug("Обработка /start для user_id=%d", user_id)
            existing_user = (await execute_query(session, select(User).filter_by(user_id=user_id))).scalars().first()
            if not existing_user:
                new_user = User(
                    user_id=user_id,
                    first_name=message.from_user.first_name,
                    username=message.from_user.username,
                    date_joined=datetime.now(timezone.utc).replace(tzinfo=None)  # Удаляем временную зону
                )
                session.add(new_user)
                await session.commit()
                logger.debug("Добавлен новый пользователь: %d", user_id)
            await message.answer(
                "Привет! Я бот для прослушивания аудиокниг.\n"
                "Выбери, что тебя интересует:",
                reply_markup=main_keyboard
            )
        except Exception as e:
            logger.error("Ошибка в send_welcome: %s", e)
            await session.rollback()
            await message.answer("Ошибка при загрузке данных. Попробуйте позже.")

# Переход в главное меню
@dp.callback_query(F.data == "to_main_menu")
async def process_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_text("Главное меню:", reply_markup=main_keyboard)
    except TelegramBadRequest:
        try:
            await callback.message.delete()
        except:
            pass
        await callback.message.answer("Главное меню:", reply_markup=main_keyboard)
    await callback.answer()

# Выбор случайной книги
@dp.callback_query(F.data == "random_book")
async def process_random_book(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    async with async_session_factory() as session:
        try:
            # Используем joinedload для предзагрузки author и genre
            query = select(Book).order_by(func.random()).options(joinedload(Book.author), joinedload(Book.genre))
            random_book = (await execute_query(session, query)).scalars().first()
            if random_book:
                await show_book_card(callback.message.chat, random_book.id, is_new_message=True)
            else:
                await callback.message.answer("В библиотеке пока нет книг.")
            await callback.answer()
        except Exception as e:
            logger.error("Ошибка в process_random_book: %s", e)
            await session.rollback()
            await callback.message.answer("Ошибка при загрузке книги. Попробуйте позже.")

# Просмотр жанров
@dp.callback_query(F.data == "browse_genres")
async def process_genres_press(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    async with async_session_factory() as session:
        try:
            genres = (await execute_query(session, select(Genre).order_by(Genre.name))).scalars().all()
            builder = InlineKeyboardBuilder()
            for genre in genres:
                builder.add(InlineKeyboardButton(text=genre.name, callback_data=f"genre:{genre.id}"))
            builder.adjust(2)
            builder.row(button_to_main_menu)
            await callback.message.edit_text("Выберите жанр:", reply_markup=builder.as_markup())
            await callback.answer()
        except Exception as e:
            logger.error("Ошибка в process_genres_press: %s", e)
            await session.rollback()
            await callback.message.answer("Ошибка при загрузке жанров. Попробуйте позже.")

# Просмотр книг определённого жанра
@dp.callback_query(F.data.startswith("genre:"))
async def process_genre_books(callback: types.CallbackQuery):
    genre_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        try:
            # Используем joinedload для предзагрузки author и genre
            query = select(Book).filter(Book.genre_id == genre_id).order_by(Book.title).options(joinedload(Book.author), joinedload(Book.genre))
            books = (await execute_query(session, query)).scalars().all()
            genre = (await execute_query(session, select(Genre).filter(Genre.id == genre_id))).scalars().first()
            builder = InlineKeyboardBuilder()
            for book in books:
                builder.add(InlineKeyboardButton(text=book.title, callback_data=f"book:{book.id}"))
            builder.adjust(1)
            builder.row(InlineKeyboardButton(text="⬅️ Назад к жанрам", callback_data="browse_genres"), button_to_main_menu)
            await callback.message.edit_text(f"Книги в жанре '<b>{genre.name}</b>':", reply_markup=builder.as_markup())
            await callback.answer()
        except Exception as e:
            logger.error("Ошибка в process_genre_books: %s", e)
            await session.rollback()
            await callback.message.answer("Ошибка при загрузке книг. Попробуйте позже.")

# Просмотр авторов
@dp.callback_query(F.data == "browse_authors")
async def process_authors_press(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    async with async_session_factory() as session:
        try:
            authors = (await execute_query(session, select(Author).order_by(Author.name))).scalars().all()
            builder = InlineKeyboardBuilder()
            for author in authors:
                builder.add(InlineKeyboardButton(text=author.name, callback_data=f"author:{author.id}"))
            builder.adjust(2)
            builder.row(button_to_main_menu)
            await callback.message.edit_text("Выберите автора:", reply_markup=builder.as_markup())
            await callback.answer()
        except Exception as e:
            logger.error("Ошибка в process_authors_press: %s", e)
            await session.rollback()
            await callback.message.answer("Ошибка при загрузке авторов. Попробуйте позже.")

# Просмотр книг определённого автора
@dp.callback_query(F.data.startswith("author:"))
async def process_author_books(callback: types.CallbackQuery):
    author_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        try:
            # Используем joinedload для предзагрузки author и genre
            query = select(Book).filter(Book.author_id == author_id).order_by(Book.title).options(joinedload(Book.author), joinedload(Book.genre))
            books = (await execute_query(session, query)).scalars().all()
            author = (await execute_query(session, select(Author).filter(Author.id == author_id))).scalars().first()
            builder = InlineKeyboardBuilder()
            for book in books:
                builder.add(InlineKeyboardButton(text=book.title, callback_data=f"book:{book.id}"))
            builder.adjust(1)
            builder.row(InlineKeyboardButton(text="⬅️ Назад к авторам", callback_data="browse_authors"), button_to_main_menu)
            await callback.message.edit_text(f"Книги автора '<b>{author.name}</b>':", reply_markup=builder.as_markup())
            await callback.answer()
        except Exception as e:
            logger.error("Ошибка в process_author_books: %s", e)
            await session.rollback()
            await callback.message.answer("Ошибка при загрузке книг. Попробуйте позже.")

# Начало поиска
@dp.callback_query(F.data == "start_search")
async def process_search_press(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.waiting_for_query)
    await callback.message.edit_text("Введите название книги или имя автора для поиска:")
    await callback.answer()

# Обработка поискового запроса
@dp.message(SearchState.waiting_for_query)
async def process_search_query(message: types.Message, state: FSMContext):
    await state.clear()
    user_query = message.text.lower()
    async with async_session_factory() as session:
        try:
            # Используем joinedload для предзагрузки author
            query = select(Book).join(Author).options(joinedload(Book.author))
            all_books = (await execute_query(session, query)).scalars().all()
            search_results = [
                book for book in all_books
                if user_query in book.title.lower() or user_query in book.author.name.lower()
            ]
            builder = InlineKeyboardBuilder()
            if not search_results:
                builder.add(button_to_main_menu)
                await message.answer("По вашему запросу ничего не найдено.", reply_markup=builder.as_markup())
                return
            for book in search_results:
                builder.add(InlineKeyboardButton(text=f"{book.title} ({book.author.name})", callback_data=f"book:{book.id}"))
            builder.adjust(1)
            builder.row(button_to_main_menu)
            await message.answer(f"Результаты поиска по запросу '<b>{message.text}</b>':", reply_markup=builder.as_markup())
        except Exception as e:
            logger.error("Ошибка в process_search_query: %s", e)
            await session.rollback()
            await message.answer("Ошибка при поиске. Попробуйте позже.")

# Выбор книги
@dp.callback_query(F.data.startswith("book:"))
async def process_book_selection(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    book_id = int(callback.data.split(":")[1])
    await show_book_card(callback.message.chat, book_id, is_new_message=True)
    await callback.answer()

# Добавление книги в избранное
@dp.callback_query(F.data.startswith("add_fav:"))
async def process_add_favorite(callback: types.CallbackQuery):
    book_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    async with async_session_factory() as session:
        try:
            existing = (await execute_query(session, select(Favorite).filter_by(user_id=user_id, book_id=book_id))).scalars().first()
            if not existing:
                session.add(Favorite(user_id=user_id, book_id=book_id))
                await session.commit()
                await callback.answer("Добавлено в избранное!")
            await refresh_book_card(callback)
        except Exception as e:
            logger.error("Ошибка в process_add_favorite: %s", e)
            await session.rollback()
            await callback.answer("Ошибка при добавлении в избранное. Попробуйте позже.", show_alert=True)

# Удаление книги из избранного
@dp.callback_query(F.data.startswith("rm_fav:"))
async def process_remove_favorite(callback: types.CallbackQuery):
    book_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    async with async_session_factory() as session:
        try:
            favorite_to_delete = (await execute_query(session, select(Favorite).filter_by(user_id=user_id, book_id=book_id))).scalars().first()
            if favorite_to_delete:
                await session.delete(favorite_to_delete)
                await session.commit()
                await callback.answer("Удалено из избранного!")
            await refresh_book_card(callback)
        except Exception as e:
            logger.error("Ошибка в process_remove_favorite: %s", e)
            await session.rollback()
            await callback.answer("Ошибка при удалении из избранного. Попробуйте позже.", show_alert=True)

# Просмотр списка избранного
@dp.callback_query(F.data.startswith("my_favorites:"))
async def process_my_favorites(callback: types.CallbackQuery):
    page = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    async with async_session_factory() as session:
        try:
            # Используем joinedload для предзагрузки author и genre
            favorite_books_query = select(Book).join(Favorite).filter(Favorite.user_id == user_id).order_by(Favorite.id.desc()).options(joinedload(Book.author), joinedload(Book.genre))
            total_favorites = (await execute_query(session, select(func.count()).select_from(favorite_books_query.subquery()))).scalar()
            paginated_books = (await execute_query(
                session,
                favorite_books_query.limit(FAVORITES_PER_PAGE).offset(page * FAVORITES_PER_PAGE)
            )).scalars().all()
            if not paginated_books:
                await callback.answer("Ваш список избранного пуст.", show_alert=True)
                return
            builder = InlineKeyboardBuilder()
            for book in paginated_books:
                builder.add(InlineKeyboardButton(text=f"{book.title} - {book.author.name}", callback_data=f"book:{book.id}"))
            builder.adjust(1)
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"my_favorites:{page-1}"))
            if (page + 1) * FAVORITES_PER_PAGE < total_favorites:
                nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"my_favorites:{page+1}"))
            if nav_buttons:
                builder.row(*nav_buttons)
            builder.row(button_to_main_menu)
            try:
                await callback.message.edit_text("⭐️ Ваше избранное:", reply_markup=builder.as_markup())
            except TelegramBadRequest:
                await callback.message.delete()
                await bot.send_message(
                    chat_id=callback.from_user.id,
                    text="⭐️ Ваше избранное:",
                    reply_markup=builder.as_markup()
                )
            await callback.answer()
        except Exception as e:
            logger.error("Ошибка в process_my_favorites: %s", e)
            await session.rollback()
            await callback.message.answer("Ошибка при загрузке избранного. Попробуйте позже.")

# Переключение страниц с главами
@dp.callback_query(F.data.startswith("ch_page:"))
async def process_chapter_page_press(callback: types.CallbackQuery):
    data_parts = callback.data.split(":")
    book_id = int(data_parts[1])
    page = int(data_parts[2])
    builder = await create_chapters_keyboard(book_id, page)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await bot.send_message(
        chat_id=callback.from_user.id,
        text="Выберите главу:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# Выбор и воспроизведение главы
@dp.callback_query(F.data.startswith("chapter:"))
async def process_chapter_selection(callback: types.CallbackQuery):
    chapter_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    async with async_session_factory() as session:
        try:
            # Используем joinedload для предзагрузки book
            query = select(AudioFile).filter(AudioFile.id == chapter_id).options(joinedload(AudioFile.book))
            current_chapter = (await execute_query(session, query)).scalars().first()
            if not current_chapter:
                return await callback.answer("Глава не найдена!", show_alert=True)
            progress = (await execute_query(session, select(UserProgress).filter_by(user_id=user_id, book_id=current_chapter.book_id))).scalars().first()
            if progress:
                progress.last_chapter_id = chapter_id
            else:
                session.add(UserProgress(user_id=user_id, book_id=current_chapter.book_id, last_chapter_id=chapter_id))
            await session.commit()
            await callback.answer(f"Отправляю: {current_chapter.title}")
            await bot.send_audio(
                chat_id=user_id,
                audio=current_chapter.file_id.strip(),
                title=current_chapter.title
            )
            # Используем joinedload для предзагрузки book в next_chapter
            query = select(AudioFile).filter(
                AudioFile.book_id == current_chapter.book_id,
                AudioFile.id > current_chapter.id
            ).order_by(AudioFile.id).options(joinedload(AudioFile.book))
            next_chapter = (await execute_query(session, query)).scalars().first()
            if next_chapter:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(
                    text=f"▶️ Следующая глава: {next_chapter.title}",
                    callback_data=f"chapter:{next_chapter.id}"
                ))
                await bot.send_message(
                    chat_id=user_id,
                    text="Продолжить прослушивание?",
                    reply_markup=builder.as_markup()
                )
        except Exception as e:
            logger.error("Ошибка в process_chapter_selection: %s", e)
            await session.rollback()
            await callback.answer("Ошибка при загрузке главы. Попробуйте позже.", show_alert=True)

# Получение ID загруженного фото
@dp.message(F.photo)
async def get_photo_file_id(message: types.Message):
    file_id = message.photo[-1].file_id
    await message.reply(f"ID этого фото (для обложки):\n<code>{file_id}</code>")

# Получение ID загруженного аудио
@dp.message(F.audio)
async def get_audio_file_id(message: types.Message):
    file_id = message.audio.file_id
    await message.reply(f"ID этого аудио (для главы):\n<code>{file_id}</code>")

# Главная функция для запуска бота
async def main():
    await set_main_menu(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())