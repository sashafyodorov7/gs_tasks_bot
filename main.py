import os
from datetime import datetime, timedelta
from telegram import Bot
from telegram.error import TelegramError
import gspread
from gspread.exceptions import APIError
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import asyncio

load_dotenv()

TOKEN = os.getenv('TOKEN')
GG_ID = os.getenv('GG_ID')
CHAT_ID = os.getenv('CHAT_ID')

# Устанавливаем параметры доступа к Google Sheets API
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
#creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/sashafyodorov/Projects/tasks_bot/credentials.json', scope)
creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(os.environ['HOME'], 'secrets', 'credentials.json'), scope)
client = gspread.authorize(creds)

# ID вашей Google таблицы
spreadsheet_id = GG_ID

# Функция для получения задач из Google таблицы
def get_tasks_from_sheet(sheet_name):
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    tasks = sheet.get_all_records()

    # Проходим по каждой задаче и определяем, нужно ли отправлять ее в сообщении
    task_flags = []
    for task in tasks:
        done_status = task.get('done', '').strip().upper()  # Получаем значение столбца "done" и преобразуем к верхнему регистру
        if done_status and done_status != 'TRUE':  # Если значение столбца "done" не пустое и не равно 'TRUE', значит задачу нужно отправить
            task_flags.append((task, True))

    return task_flags

# Функция для формирования сообщения
def format_message(tasks, task_type):
    message = f"{task_type} задачи на сегодня:\n"
    for i, task in enumerate(tasks, start=1):
        message += f"{i}. {task['task_name']}\n"
    return message

# Получаем текущую дату
today = datetime.now().strftime('%Y-%m-%d')

# Получаем рабочие и личные задачи на сегодня
# добавить если нужно отправлять задачи на сегодня if task[0]['dt'] == today
work_tasks = [task[0] for task in get_tasks_from_sheet('WorkTasks') if task[0]['dt'] == today]
personal_tasks = [task[0] for task in get_tasks_from_sheet('PersonalTasks') if task[0]['dt'] == today]


# Формируем сообщение
work_message = format_message(work_tasks, "Рабочие")
personal_message = format_message(personal_tasks, "Личные")

# Отправляем сообщение в Telegram
telegram_token = TOKEN
telegram_chat_id = CHAT_ID

bot = Bot(token=telegram_token)
async def send_messages():
    for li in range(5):  # Попробовать отправить сообщение не более 5 раз
        try:
            await bot.send_message(chat_id=telegram_chat_id, text=work_message)
            await bot.send_message(chat_id=telegram_chat_id, text=personal_message)
            break  # Если сообщения отправлены успешно, выйти из цикла
        except (TelegramError, APIError) as e:
            print("Ошибка отправки сообщения:", e)
            await asyncio.sleep(10)  # Подождать 1 секунду перед повторной попыткой
    else:
        print("Не удалось отправить сообщения после 5 попыток.")

bot = Bot(token=telegram_token)
asyncio.run(send_messages())
