import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("BOT_TOKEN", "")
DATA_FILE = "data.json"

OBJECTS = {
    "obj1": "777 Xovli",
    "obj2": "Mingdonobod Kotej",
    "obj3": "London 38kv"
}

CHOOSE_OBJ, ENTER_AMOUNT, ENTER_DESC = range(3)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"obj1": [], "obj2": [], "obj3": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fmt(amount):
    return "{:,.0f} so'm".format(amount).replace(",", " ")

def menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Xarajat qoshish", callback_data="add")],
        [InlineKeyboardButton("Hisobot korish", callback_data="report")],
        [InlineKeyboardButton("Oxirgi ochirish", callback_data="delete_last")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "PRORAB HISOBOT\n\nXarajatlarni boshqarish\n\nNima qilmoqchisiz?",
        reply_markup=menu_kb()
    )

async def add_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "Qaysi obyekt?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("777 Xovli", callback_data="add_obj1")],
            [InlineKeyboardButton("Mingdonobod Kotej", callback_data="add_obj2")],
            [InlineKeyboardButton("London 38kv", callback_data="add_obj3")],
            [InlineKeyboardButton("Orqaga", callback_data="menu")],
        ])
    )
    return CHOOSE_OBJ

async def choose_obj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    obj_key = q.data.replace("add_", "")
    context.user_data["current_obj"] = obj_key
    await q.edit_message_text(
        f"{OBJECTS[obj_key]}\n\nSummani kiriting (faqat raqam):\nMasalan: 500000"
    )
    return ENTER_AMOUNT

async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace(" ", "").replace(",", "")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
        context.user_data["amount"] = amount
        await update.message.reply_text(
            f"Summa: {fmt(amount)}\n\nNima uchun yozing:\nMasalan: g'isht, ish haqi, qum"
        )
        return ENTER_DESC
    except Exception:
        await update.message.reply_text("Xato! Faqat raqam kiriting:\nMasalan: 500000")
        return ENTER_AMOUNT

async def enter_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    if not desc:
        await update.message.reply_text("Bosh bolmasin!")
        return ENTER_DESC
    obj_key = context.user_data["current_obj"]
    amount = context.user_data["amount"]
    expenses = load_data()
    expenses[obj_key].append({
        "amount": amount,
        "desc": desc,
        "date": datetime.now().strftime("%d.%m.%Y"),
        "timestamp": datetime.now().isoformat()
    })
    save_data(expenses)
    total = sum(e["amount"] for e in expenses[obj_key])
    await update.message.reply_text(
        f"Qoshildi!\n\n{OBJECTS[obj_key]}\n{fmt(amount)}\n{desc}\n\nJami: {fmt(total)}",
        reply_markup=menu_kb()
    )
    return ConversationHandler.END

async def report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "Qaysi hisobot?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Hammasi", callback_data="rep_all")],
            [InlineKeyboardButton("777 Xovli", callback_data="rep_obj1")],
            [InlineKeyboardButton("Mingdonobod Kotej", callback_data="rep_obj2")],
            [InlineKeyboardButton("London 38kv", callback_data="rep_obj3")],
            [InlineKeyboardButton("Orqaga", callback_data="menu")],
        ])
    )

async def show_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    obj_key = q.data.replace("rep_", "")
    expenses = load_data()
    text = "HISOBOT\n\n"
    if obj_key == "all":
        grand = 0
        for key, name in OBJECTS.items():
            items = expenses.get(key, [])
            total = sum(e["amount"] for e in items)
            grand += total
            text += f"{name}\nJami: {fmt(total)} ({len(items)} ta)\n\n"
        text += f"UMUMIY: {fmt(grand)}"
    else:
        name = OBJECTS[obj_key]
        items = expenses.get(obj_key, [])
        total = sum(e["amount"] for e in items)
        text += f"{name}\n"
        if not items:
            text += "Xarajatlar yoq\n"
        else:
            for e in items[-10:]:
                text += f"{e['date']} - {fmt(e['amount'])}\n{e['desc']}\n\n"
        text += f"Jami: {fmt(total)}"
    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Orqaga", callback_data="menu")]])
    )

async def delete_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    expenses = load_data()
    last_obj, last_time = None, ""
    for key in OBJECTS:
        items = expenses.get(key, [])
        if items:
            t = items[-1].get("timestamp", "")
            if t > last_time:
                last_time, last_obj = t, key
    if not last_obj:
        await q.edit_message_text(
            "Ochiriladigan narsa yoq!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Orqaga", callback_data="menu")]]))
        return
    last = expenses[last_obj][-1]
    await q.edit_message_text(
        f"Ochirilsinmi?\n\n{OBJECTS[last_obj]}\n{fmt(last['amount'])}\n{last['desc']}\n{last['date']}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Ha, ochir", callback_data=f"del_{last_obj}")],
            [InlineKeyboardButton("Yoq", callback_data="menu")],
        ])
    )

async def confirm_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    obj_key = q.data.replace("del_", "")
    expenses = load_data()
    if expenses.get(obj_key):
        d = expenses[obj_key].pop()
        save_data(expenses)
        await q.edit_message_text(
            f"Ochirildi!\n{fmt(d['amount'])}\n{d['desc']}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Orqaga", callback_data="menu")]]))
    else:
        await q.edit_message_text(
            "Topilmadi!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Orqaga", callback_data="menu")]]))

async def go_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "PRORAB HISOBOT\n\nNima qilmoqchisiz?",
        reply_markup=menu_kb()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bekor qilindi", reply_markup=menu_kb())
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_entry, pattern="^add$")],
        states={
            CHOOSE_OBJ: [CallbackQueryHandler(choose_obj, pattern="^add_obj")],
            ENTER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)],
            ENTER_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_desc)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(go_menu, pattern="^menu$"),
        ],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(report_menu, pattern="^report$"))
    app.add_handler(CallbackQueryHandler(show_report, pattern="^rep_"))
    app.add_handler(CallbackQueryHandler(delete_last, pattern="^delete_last$"))
    app.add_handler(CallbackQueryHandler(confirm_del, pattern="^del_"))
    app.add_handler(CallbackQueryHandler(go_menu, pattern="^menu$"))
    print("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
