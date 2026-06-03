from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import json
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")

DATA_FILE = "kassa_ru.json"
HISTORY_FILE = "history_ru.json"

DEFAULT_DATA = {
    "дол": 0,
    "руб": 0,
    "евро": 0,
    "долбелый": 0,
    "лир": 0,
    "лирвакыф": 0,
    "лиртуркфин": 0,
    "лирзират": 0,
    "парибу": 0,
    "байбит": 0
}

CASH = ["дол", "руб", "евро", "долбелый", "лир"]
BANKS = ["лирвакыф", "лиртуркфин", "лирзират"]
CRYPTO = ["парибу", "байбит"]

keyboard = ReplyKeyboardMarkup(
    [
        ["📊 Дай", "💵 Касса"],
        ["🏦 Банки", "₿ Крипта"],
        ["📜 История", "↩️ Отмена"],
        ["➕ Добавить", "➖ Удалить"]
    ],
    resize_keyboard=True
)


def load_json(file, default):
    if not os.path.exists(file):
        save_json(file, default)
        return default.copy()

    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_data():
    return load_json(DATA_FILE, DEFAULT_DATA.copy())


def save_data(data):
    save_json(DATA_FILE, data)


def load_history():
    return load_json(HISTORY_FILE, [])


def save_history(history):
    save_json(HISTORY_FILE, history)


def money(amount):
    if amount == int(amount):
        return f"{int(amount):,}".replace(",", " ")
    return f"{amount:,.2f}".replace(",", " ")


def report(data, title="📊 КАССА", keys=None):
    if keys is None:
        keys = list(data.keys())

    text = title + ":\n\n"
    for key in keys:
        if key in data:
            text += f"{key}: {money(data[key])}\n"
    return text


def add_operation(position, amount, comment):
    data = load_data()
    history = load_history()

    if position not in data:
        return "Такой позиции нет. Добавь так: добавь фунты 0"

    before = data[position]
    after = before + amount
    data[position] = after

    history.append({
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "position": position,
        "amount": amount,
        "comment": comment,
        "before": before,
        "after": after
    })

    save_data(data)
    save_history(history)

    return (
        f"✅ Записал: {money(amount)} {position}\n"
        f"Итого: {money(after)}\n"
        f"Комментарий: {comment}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Бот кассы работает.\n\n"
        "Можно нажимать кнопки или писать вручную:\n\n"
        "лир +1000 обмен\n"
        "дол -100 клиенту\n"
        "парибу +500 перевод\n\n"
        "Добавить позицию:\n"
        "добавь фунты 0\n\n"
        "Удалить позицию:\n"
        "удали фунты",
        reply_markup=keyboard
    )


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    data = load_data()

    if text in ["📊 дай", "дай", "отчет", "отчёт"]:
        await update.message.reply_text(report(data), reply_markup=keyboard)
        return

    if text in ["💵 касса", "касса"]:
        await update.message.reply_text(report(data, "💵 НАЛИЧКА", CASH), reply_markup=keyboard)
        return

    if text in ["🏦 банки", "банки"]:
        await update.message.reply_text(report(data, "🏦 БАНКИ", BANKS), reply_markup=keyboard)
        return

    if text in ["₿ крипта", "крипта"]:
        await update.message.reply_text(report(data, "₿ КРИПТА", CRYPTO), reply_markup=keyboard)
        return

    if text in ["📜 история", "история"]:
        history = load_history()
        if not history:
            await update.message.reply_text("Истории пока нет.", reply_markup=keyboard)
            return

        msg = "📜 Последние операции:\n\n"
        for h in history[-10:]:
            msg += (
                f"{h['date']} | {h['position']} "
                f"{money(h['amount'])} | {h['comment']} | итог {money(h['after'])}\n"
            )

        await update.message.reply_text(msg, reply_markup=keyboard)
        return

    if text in ["↩️ отмена", "отмена"]:
        history = load_history()

        if not history:
            await update.message.reply_text("Нечего отменять.", reply_markup=keyboard)
            return

        last = history.pop()
        data = load_data()

        position = last["position"]
        data[position] = last["before"]

        save_data(data)
        save_history(history)

        await update.message.reply_text(
            f"↩️ Отменил:\n"
            f"{position} {money(last['amount'])}\n"
            f"Вернул итог: {money(last['before'])}",
            reply_markup=keyboard
        )
        return

    if text in ["➕ добавить", "добавить"]:
        await update.message.reply_text(
            "Напиши так:\n\nдобавь фунты 0",
            reply_markup=keyboard
        )
        return

    if text in ["➖ удалить", "удалить"]:
        await update.message.reply_text(
            "Напиши так:\n\nудали фунты",
            reply_markup=keyboard
        )
        return

    if text.startswith("добавь "):
        parts = text.split()
        if len(parts) < 3:
            await update.message.reply_text("Пример: добавь фунты 0", reply_markup=keyboard)
            return

        name = parts[1]
        try:
            amount = float(parts[2].replace(",", "."))
        except:
            await update.message.reply_text("Сумма должна быть числом. Пример: добавь фунты 0", reply_markup=keyboard)
            return

        data[name] = amount
        save_data(data)

        await update.message.reply_text(
            f"✅ Добавил позицию: {name} = {money(amount)}",
            reply_markup=keyboard
        )
        return

    if text.startswith("удали "):
        parts = text.split()
        if len(parts) < 2:
            await update.message.reply_text("Пример: удали фунты", reply_markup=keyboard)
            return

        name = parts[1]

        if name not in data:
            await update.message.reply_text("Такой позиции нет.", reply_markup=keyboard)
            return

        del data[name]
        save_data(data)

        await update.message.reply_text(f"✅ Удалил позицию: {name}", reply_markup=keyboard)
        return

    parts = text.split()

    if len(parts) >= 2:
        position = parts[0]

        try:
            amount = float(parts[1].replace(",", "."))
        except:
            await update.message.reply_text("Не понял сумму. Пример: лир +1000 обмен", reply_markup=keyboard)
            return

        comment = " ".join(parts[2:])
        msg = add_operation(position, amount, comment)

        await update.message.reply_text(msg, reply_markup=keyboard)
        return

    await update.message.reply_text(
        "Не понял.\n\n"
        "Примеры:\n"
        "дай\n"
        "лир +1000 обмен\n"
        "дол -100 клиенту\n"
        "добавь фунты 0",
        reply_markup=keyboard
    )


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()
