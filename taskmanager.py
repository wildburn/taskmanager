import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Объект бота
bot = Bot(token="TOKEN")

# Диспетчер
dp = Dispatcher()

# Хранилище задач и напоминаний
tasks = {}
reminders = {}

# Инициализация планировщика
scheduler = AsyncIOScheduler()


# Хэндлер на команду /start
@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я TaskManagerBot. Используй команды /add, /list, /delete и /remind для управления задачами."
    )


# Хэндлер на команду /add
@dp.message(Command(commands=["add"]))
async def cmd_add(message: Message):
    args = message.text[5:].strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Пожалуйста, укажите приоритет (low, medium, high) и текст задачи после команды /add."
        )
        return

    priority = args[0].lower()
    task_text = args[1]

    if priority not in ["low", "medium", "high"]:
        await message.answer("Приоритет должен быть одним из: low, medium, high.")
        return

    user_id = message.from_user.id
    if user_id not in tasks:
        tasks[user_id] = []

    tasks[user_id].append((priority, task_text))
    await message.answer(f"Задача '{task_text}' с приоритетом '{priority}' добавлена.")


# Хэндлер на команду /list
@dp.message(Command(commands=["list"]))
async def cmd_list(message: Message):
    user_id = message.from_user.id
    if user_id not in tasks or not tasks[user_id]:
        await message.answer("У вас нет задач.")
        return

    sorted_tasks = sorted(
        tasks[user_id], key=lambda x: ["low", "medium", "high"].index(x[0])
    )
    task_list = "\n".join(
        [
            f"{idx + 1}. [{priority}] {task}"
            for idx, (priority, task) in enumerate(sorted_tasks)
        ]
    )
    await message.answer(f"Ваши задачи:\n{task_list}")


# Хэндлер на команду /delete
@dp.message(Command(commands=["delete"]))
async def cmd_delete(message: Message):
    task_number = message.text[8:].strip()
    if not task_number.isdigit():
        await message.answer("Пожалуйста, укажите номер задачи после команды /delete.")
        return

    user_id = message.from_user.id
    task_idx = int(task_number) - 1

    if user_id not in tasks or task_idx < 0 or task_idx >= len(tasks[user_id]):
        await message.answer("Неверный номер задачи.")
        return

    deleted_task = tasks[user_id].pop(task_idx)
    await message.answer(
        f"Задача '{deleted_task[1]}' с приоритетом '{deleted_task[0]}' удалена."
    )


# Хэндлер на команду /remind
@dp.message(Command(commands=["remind"]))
async def cmd_remind(message: Message):
    args = message.text[8:].strip().split()
    if len(args) < 2:
        await message.answer("Использование: /remind HH:MM текст напоминания")
        return

    time_str = args[0]
    reminder_text = " ".join(args[1:])

    try:
        reminder_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        await message.answer("Неверный формат времени. Используйте HH:MM.")
        return

    user_id = message.from_user.id
    if user_id not in reminders:
        reminders[user_id] = []

    reminders[user_id].append((reminder_time, reminder_text))
    scheduler.add_job(
        send_reminder,
        trigger="cron",
        hour=reminder_time.hour,
        minute=reminder_time.minute,
        args=[user_id, reminder_text],
        id=f"{user_id}_{reminder_time}_{reminder_text}",
        replace_existing=True,
    )

    await message.answer(f"Напоминание '{reminder_text}' установлено на {time_str}.")


async def send_reminder(user_id, text):
    await bot.send_message(user_id, f"Напоминание: {text}")


# Запуск процесса поллинга новых апдейтов и планировщика
async def main():
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
