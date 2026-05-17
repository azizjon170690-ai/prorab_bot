import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
DATA_FILE = "data.json"

OBJECTS = {
    "obj1": "777 Xovli",
    "obj2": "Mingdonobod Kotej",
    "obj3": "London 38kv"
}

# States
CHOOSE_OBJ, ENTER_AMOUNT, ENTER_DESC = range(3)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"obj1": [], "obj2": [], "obj3": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def format_sum(amount):
    return f"{amount:,.0f} so'm".replace(",", " ")

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Xarajat qo'shish", callback_data="add")],
        [InlineKeyboardButton("📊 Hisobot ko'rish", callback_data="report")],
        [InlineKeyboardButton("🗑 Oxirgi o'chirish", callback_data="delete_last")],
    ])

def objects_keyboard(prefix="obj_"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 777 Xovli", callback_data=f"{prefix}obj1")],
        [InlineKeyboardButton("🏡 Mingdonobod Kotej", callback_data=f"{prefix}obj2")],
        [InlineKeyboardButton("🏢 London 38kv", callback_data=f"{prefix}obj3")],
        [InlineKeyboardButton("↩️ Orqaga", callback_data="back")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚒ *PRORAB HISOBOT*\n\nXarajatlarni boshqarish tizimi\n\nNima qilmoqchisiz?",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back" or data == "menu":
        await query.edit_message_text(
            "⚒ *PRORAB HISOBOT*\n\nNima qilmoqchisiz?",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END

    elif data == "add":
        await query.edit_message_text(
            "➕ *Qaysi obyektga xarajat qo'shmoqchisiz?*",
            parse_mode="Markdown",
            reply_markup=objects_keyboard("add_")
        )
        return CHOOSE_OBJ

    elif data.startswith("add_"):
        obj_key = data.replace("add_", "")
        context.user_data["current_obj"] = obj_key
        obj_name = OBJECTS[obj_key]
        await query.edit_message_text(
            f"🏗 *{obj_name}*\n\n💰 Summani kiriting (faqat raqam):\nMasalan: 500000",
            parse_mode="Markdown"
        )
        return ENTER_AMOUNT

    elif data == "report":
        await query.edit_message_text(
            "📊 *Qaysi obyekt hisoboti?*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Hammasi", callback_data="rep_all")],
                [InlineKeyboardButton("🏠 777 Xovli", callback_data="rep_obj1")],
                [InlineKeyboardButton("🏡 Mingdonobod Kotej", callback_data="rep_obj2")],
                [InlineKeyboardButton("🏢 London 38kv", callback_data="rep_obj3")],
                [InlineKeyboardButton("↩️ Orqaga", callback_data="back")],
            ])
        )
        return ConversationHandler.END

    elif data.startswith("rep_"):
        obj_key = data.replace("rep_", "")
        expenses = load_data()
        text = "📊 *HISOBOT*\n\n"

        if obj_key == "all":
            grand_total = 0
            for key, name in OBJECTS.items():
                items = expenses.get(key, [])
                total = sum(e["amount"] for e in items)
                grand_total += total
                text += f"━━━━━━━━━━━━━━━\n"
                text += f"🏗 *{name}*\n"
                text += f"💰 Jami: *{format_sum(total)}*\n"
                text += f"📝 {len(items)} ta xarajat\n"
            text += f"━━━━━━━━━━━━━━━\n"
            text += f"🔢 *UMUMIY: {format_sum(grand_total)}*"
        else:
            name = OBJECTS[obj_key]
            items = expenses.get(obj_key, [])
            total = sum(e["amount"] for e in items)
            text += f"🏗 *{name}*\n"
            text += f"━━━━━━━━━━━━━━━\n"
            if not items:
                text += "Xarajatlar yo'q\n"
            else:
                for e in items[-10:]:
                    text += f"📅 {e['date']}\n"
                    text += f"💰 {format_sum(e['amount'])}\n"
                    text += f"📝 {e['desc']}\n\n"
                if len(items) > 10:
                    text += f"_(oxirgi 10 ta ko'rsatildi)_\n\n"
            text += f"━━━━━━━━━━━━━━━\n"
            text += f"💰 *Jami: {format_sum(total)}*"

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Orqaga", callback_data="menu")]])
        )

    elif data == "delete_last":
        expenses = load_data()
        # Find last expense across all objects
        last_obj = None
        last_time = None
        for key in OBJECTS:
            items = expenses.get(key, [])
            if items:
                item_time = items[-1].get("timestamp", "")
                if last_time is None or item_time > last_time:
                    last_time = item_time
                    last_obj = key

        if last_obj is None:
            await query.edit_message_text(
                "❌ O'chiriladigan xarajat yo'q!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Orqaga", callback_data="menu")]])
            )
            return

        last = expenses[last_obj][-1]
        text = f"🗑 *Oxirgi xarajatni o'chirish?*\n\n"
        text += f"🏗 {OBJECTS[last_obj]}\n"
        text += f"💰 {format_sum(last['amount'])}\n"
        text += f"📝 {last['desc']}\n"
        text += f"📅 {last['date']}"

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Ha, o'chir", callback_data=f"confirm_del_{last_obj}")],
                [InlineKeyboardButton("❌ Yo'q", callback_data="menu")],
            ])
        )

    elif data.startswith("confirm_del_"):
        obj_key = data.replace("confirm_del_", "")
        expenses = load_data()
        if expenses.get(obj_key):
            deleted = expenses[obj_key].pop()
            save_data(expenses)
            await query.edit_message_text(
                f"✅ O'chirildi!\n\n💰 {format_sum(deleted['amount'])}\n📝 {deleted['desc']}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Orqaga", callback_data="menu")]])
            )
        else:
            await query.edit_message_text(
                "❌ Xarajat topilmadi!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Orqaga", callback_data="menu")]])
            )

async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace(" ", "").replace(",", "")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
        context.user_data["amount"] = amount
        await update.message.reply_text(
            f"✅ Summa: *{format_sum(amount)}*\n\n📝 Nima uchun? (qisqacha yozing)\nMasalan: g'isht, ish haqi, qum...",
            parse_mode="Markdown"
        )
        return ENTER_DESC
    except:
        await update.message.reply_text("❌ Noto'g'ri summa! Faqat raqam kiriting:\nMasalan: 500000")
        return ENTER_AMOUNT

async def enter_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    if not desc:
        await update.message.reply_text("❌ Tavsif bo'sh bo'lmasin!")
        return ENTER_DESC

    obj_key = context.user_data["current_obj"]
    amount = context.user_data["amount"]
    obj_name = OBJECTS[obj_key]

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
        f"✅ *Xarajat qo'shildi!*\n\n"
        f"🏗 {obj_name}\n"
        f"💰 {format_sum(amount)}\n"
        f"📝 {desc}\n\n"
        f"📊 {obj_name} jami: *{format_sum(total)}*",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(button_handler, pattern="^add$"),
        ],
        states={
            CHOOSE_OBJ: [CallbackQueryHandler(button_handler)],
            ENTER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)],
            ENTER_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_desc)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("start", start))

    print("Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
