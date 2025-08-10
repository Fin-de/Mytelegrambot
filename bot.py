import logging
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Вставьте сюда токен вашего бота, полученный от BotFather
TOKEN = "8258447539:AAGhBEBFQMsuUBsrWH0jFYIxYhjo7FF-NIU" 

# ID группы, куда будут отправляться сообщения операторам
OPERATOR_GROUP_ID = -1002790545860 # Замените на реальный ID вашей группы

# !!! ДОБАВЛЕНО: Список ID операторов !!!
# Замените на реальные ID ваших операторов.
# Пример: OPERATOR_IDS = [123456789, 987654321]
# !!! ВАЖНО: Убедитесь, что ID оператора, который будет вводить команду, здесь указан.
# Если вы тестируете сами, добавьте свой ID.
OPERATOR_IDS = [7018522414 , 5295863860] # !!! ЗАМЕНИТЕ НА РЕАЛЬНЫЙ ID ВАШЕГО ОПЕРАТОРА !!!

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__) # Исправлено: должно быть __name__

# --- Хранилище для связи пользователя и оператора ---
# user_interactions = {
#     user_id: {
#         "user_id_to_reply": user_id,       # ID пользователя, которому оператор отвечает
#         "user_name": user_name
#     }
# }
user_interactions = {}

# --- Вспомогательная функция для проверки, является ли пользователь оператором ---
def is_operator(user_id: int) -> bool:
    """Проверяет, является ли пользователь оператором по его ID."""
    return user_id in OPERATOR_IDS

# --- Команды ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение."""
    user = update.effective_user
    user_id = user.id

    # Если это оператор, отвечаем иначе
    if is_operator(user_id):
        logger.info(f"Оператор ({user_id}) вызвал команду /start.")
        await update.message.reply_text("Привет, Оператор! Здесь отображаются ваши команды.")
        return

    # Обычный пользователь
    logger.info(f"Пользователь ({user_id}) вызвал команду /start.")
    await update.message.reply_html(
        rf"Привет, {user.mention_html()}! Я бот для заказа товаров. Пожалуйста, опишите ваши пожелания к товару, и мы свяжемся с вами.",
        reply_markup=ForceReply(selective=True),
    )

async def reply_to_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /reply от оператора."""

    user_id = update.effective_user.id

    # !!! ПРОДОЛЖАЕМ КОНТРОЛИРОВАТЬ: команда должна быть от оператора !!!
    if not is_operator(user_id):
        logger.warning(f"Команда /reply получена от не-оператора. User ID: {user_id}. Сообщение: '{update.message.text}'")
        await update.message.reply_text("У вас нет прав для использования этой команды.")
        return

    # !!! ИСПРАВЛЕНИЕ: Команда /reply должна вводиться в ЛИЧНОМ ЧАТЕ с ботом, а не в группе !!!
    if update.effective_chat.type != "private":
        logger.warning(f"Команда /reply получена не в личном чате. Тип чата: {update.effective_chat.type}. Отправитель: {user_id}. Сообщение: '{update.message.text}'")
        await update.message.reply_text("Эта команда предназначена для использования в личном чате с ботом.")
        return

    # !!! ВСЕ ЕЩЕ ВАЖНО: Логируем получение команды !!!
    logger.info(f"ПОЛУЧЕНА КОМАНДА /reply. Сообщение: '{update.message.text}'. Отправитель: {user_id}")

    # Парсим команду: /reply <user_id> <сообщение>
    args = update.message.text.split(maxsplit=2)
    if len(args) < 3:
        await update.message.reply_text("Неверный формат команды. Используйте: `/reply <user_id> <сообщение>`")
        logger.error(f"Неверный формат команды /reply. Сообщение: '{update.message.text}'")
        return

    try:
        user_id_to_reply = int(args[1])
        message_to_user = args[2]
        logger.info(f"Парсинг команды: user_id_to_reply = {user_id_to_reply}, message_to_user = '{message_to_user}'")
    except ValueError:
        await update.message.reply_text("Неверный ID пользователя. Пожалуйста, укажите числовой ID.")
        logger.error(f"Ошибка парсинга user_id в команде /reply. Сообщение: '{update.message.text}'")
        return

    # Проверяем, есть ли информация о пользователе, которому хотим ответить
    if user_id_to_reply not in user_interactions:
        await update.message.reply_text(f"Не найдена информация о пользователе с ID {user_id_to_reply}. Убедитесь, что пользователь сначала написал боту.")
        logger.warning(f"Попытка ответа пользователю {user_id_to_reply}, но он отсутствует в user_interactions.")
        return

    logger.info(f"Информация о пользователе {user_id_to_reply} найдена в user_interactions.")

    # Отправляем сообщение пользователю
    try:
        await context.bot.send_message(
            chat_id=user_id_to_reply,
            text=f"Оператор ответил вам:\n\n{message_to_user}"
        )
        # Отвечаем оператору, что его сообщение отправлено
        await update.message.reply_text(f"Ваш ответ успешно отправлен пользователю с ID {user_id_to_reply}.")
        logger.info(f"Сообщение от оператора успешно отправлено пользователю {user_id_to_reply}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения пользователю {user_id_to_reply}: {e}")
        await update.message.reply_text(f"Не удалось отправить сообщение пользователю с ID {user_id_to_reply}. Убедитесь, что ID верный и пользователь взаимодействует с ботом.")

# --- Обработка сообщений от пользователей ---

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пересылает сообщения пользователей в группу операторам и сохраняет информацию."""

    user_id = update.effective_user.id

    # Игнорируем сообщения от операторов в этом обработчике.
    # Если это оператор, он может отправлять команды, которые обрабатываются CommandHandler.
    if is_operator(user_id):
        logger.info(f"Сообщение от оператора ({user_id}) проигнорировано в handle_user_message.")
        return

    # !!! ИСПРАВЛЕНО: Этот обработчик реагирует ТОЛЬКО на не-командные сообщения !!!
    # Команды будут обрабатываться CommandHandler.
    if update.message.text.startswith('/'):
        logger.debug(f"Сообщение '{update.message.text}' от пользователя {user_id} проигнорировано, т.к. это команда.")
        return

    user_message = update.message.text
    # Пытаемся получить имя пользователя, если оно недоступно, используем ID
    user_name = update.effective_user.full_name if update.effective_user.full_name else f"User_{user_id}"

    logger.info(f"ПОЛУЧЕНО СООБЩЕНИЕ ОТ ПОЛЬЗОВАТЕЛЯ. '{user_name}' (ID: {user_id}): '{user_message}'")

    # Обрабатываем только личные сообщения (от обычных пользователей к боту)
    if update.effective_chat.type == "private": 
        logger.info(f"Сообщение от пользователя {user_id} пересылается в группу операторов ({OPERATOR_GROUP_ID}).")

        try:
            # Отправляем сообщение в группу операторов
            sent_message_to_operators = await context.bot.send_message(
                chat_id=OPERATOR_GROUP_ID,
                text=f"Новое сообщение от пользователя:\n\n"
                     f"ID пользователя: {user_id}\n"
                     f"Имя пользователя: {user_name}\n"
                     f"Пожелания: {user_message}",
            )
            logger.info(f"Сообщение успешно отправлено в группу операторов. ID сообщения в группе: {sent_message_to_operators.message_id}")

            # Сохраняем данные пользователя для возможности ответа
            user_interactions[user_id] = {
                "user_id_to_reply": user_id, 
                "user_name": user_name,
            }
            logger.info(f"Данные для пользователя {user_id} сохранены в user_interactions: {user_interactions[user_id]}")

        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в группу операторов ({OPERATOR_GROUP_ID}): {e}")
            # Отвечаем пользователю, что его сообщение не удалось переслать операторам
            await update.message.reply_text("Произошла ошибка при отправке вашего сообщения операторам. Попробуйте позже.")
            return # Выходим, если не удалось отправить в группу

        # Отвечаем пользователю, что его сообщение отправлено
        await update.message.reply_text(
            "Ваши пожелания отправлены нашим операторам. Мы свяжемся с вами в ближайшее время!"
        )

# --- Определение главной функции ---
def main() -> None:
    """Запускает бота."""
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    # CommandHandler для "reply" будет обрабатывать команды.
    # Внутри reply_to_user_command есть проверки на ID оператора и тип чата.
    application.add_handler(CommandHandler("reply", reply_to_user_command)) 

    # Обработчик сообщений от пользователей
    # Этот обработчик будет обрабатывать ТОЛЬКО сообщения, которые НЕ являются командами
    # и приходят в личные чаты ОТ ОБЫЧНЫХ ПОЛЬЗОВАТЕЛЕЙ.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_user_message))

    logger.info("Бот запущен. Ожидание команд...")
    application.run_polling()

# --- Точка входа в программу ---
if __name__ == "__main__":
    main()
