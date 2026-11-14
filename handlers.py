import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

from database import (
    register_user,
    add_transactions,
    get_financial_summary,
    get_detailed_expenses,
    get_category_summary,
    delete_last_transaction,
    clear_user_data
)
from ai_service import analyze_message_with_ai
from formatters import (
    format_money,
    format_transaction_saved,
    format_balance_report,
    format_detailed_expenses_report
)

router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    await register_user(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username or ""
    )
    
    welcome_text = (
        f"Assalomu alaykum, <b>{user.first_name}</b>! 👋\n\n"
        "Men <b>Gemini AI</b> bilan ishlaydigan aqlli shaxsiy hisobchi botman 🤖📊\n\n"
        "Menga daromadlaringiz va harajatlaringizni <b>oddiy matn (text)</b> shaklida yozsangiz kifoya. "
        "Men barchasini eslab qolaman va doimiy hisob-kitob qilib boraman:\n"
        "• Qancha pul sarflandi\n"
        "• Aynan nimaga qancha pul ketdi\n"
        "• Qancha pulingiz qoldi (balans)\n\n"
        "💡 <b>Misollar:</b>\n"
        "▫️ <i>«Oylik maoshim 6 000 000 so'm»</i>\n"
        "▫️ <i>«1 kg olma uchun 10 ming som, 2 kg banan uchun 20 ming»</i>\n"
        "▫️ <i>«Tushlikka 35 000 va taksiga 12 000 ketdi»</i>\n"
        "▫️ <i>«Qancha pulim qoldi?»</i> yoki <i>«Nimaga qancha sarfladim?»</i>\n\n"
        "📌 <b>Asosiy buyruqlar:</b>\n"
        "/balans — Qolgan pul va umumiy holat\n"
        "/xarajatlar — Nimaga qancha sarflanganining ro'yxati\n"
        "/bekor — Oxirgi yozuvni bekor qilish\n"
        "/tozalash — Barcha hisob-kitoblarni o'chirib, noldan boshlash\n"
        "/yordam — Qo'llanma"
    )
    await message.answer(welcome_text, parse_mode="HTML")

@router.message(Command("yordam"))
@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📖 <b>Hisobchi botdan foydalanish bo'yicha qo'llanma:</b>\n\n"
        "Siz istalgan vaqtda botga shunchaki erkin matn yozishingiz mumkin:\n\n"
        "1️⃣ <b>Daromad kiritish:</b>\n"
        "• <i>«Oyligim 5 million so'm»</i>\n"
        "• <i>«Menga 400 ming qarz qaytarishdi»</i>\n\n"
        "2️⃣ <b>Xarajatlarni kiritish:</b>\n"
        "• <i>«1 kg olma uchun 10 ming som, 2 kg banan uchun 20 ming»</i>\n"
        "• <i>«Benzinga 150000 som to'ladim»</i>\n"
        "• <i>«Kommunal to'lov 250 ming»</i>\n\n"
        "3️⃣ <b>Hisobot so'rash:</b>\n"
        "• Shunchaki: <i>«Qancha pulim qoldi?»</i> yoki /balans\n"
        "• <i>«Nimaga qancha sarfladim?»</i> yoki /xarajatlar\n\n"
        "4️⃣ <b>Tuzatish:</b>\n"
        "• <i>«Oxirgisini o'chir»</i> yoki /bekor"
    )
    await message.answer(help_text, parse_mode="HTML")

@router.message(Command("balans"))
@router.message(Command("hisob"))
async def cmd_balance(message: Message):
    summary = await get_financial_summary(message.from_user.id)
    categories = await get_category_summary(message.from_user.id)
    text = format_balance_report(summary, categories)
    await message.answer(text, parse_mode="HTML")

@router.message(Command("xarajatlar"))
async def cmd_expenses(message: Message):
    summary = await get_financial_summary(message.from_user.id)
    expenses = await get_detailed_expenses(message.from_user.id, limit=40)
    text = format_detailed_expenses_report(expenses, summary)
    await message.answer(text, parse_mode="HTML")

@router.message(Command("bekor"))
@router.message(Command("undo"))
async def cmd_undo(message: Message):
    user_id = message.from_user.id
    deleted = await delete_last_transaction(user_id)
    if not deleted:
        await message.answer("ℹ️ O'chirish uchun oxirgi operatsiya topilmadi.", parse_mode="HTML")
        return
        
    summary = await get_financial_summary(user_id)
    t_name = "Daromad" if deleted["type"] == "income" else "Xarajat"
    amt_str = format_money(deleted["amount"])
    
    reply = (
        f"🗑 <b>Oxirgi yozuv bekor qilindi:</b>\n"
        f"• Tur: {t_name}\n"
        f"• Nomi: <b>{deleted['description']}</b>\n"
        f"• Miqdori: <b>{amt_str}</b>\n\n"
        f"📊 <b>Yangilangan balans:</b> <b>{format_money(summary['balance'])}</b>"
    )
    await message.answer(reply, parse_mode="HTML")

@router.message(Command("tozalash"))
async def cmd_clear(message: Message):
    user_id = message.from_user.id
    await clear_user_data(user_id)
    await message.answer(
        "🧹 <b>Barcha hisob-kitoblaringiz muvaffaqiyatli tozalandi!</b>\n\n"
        "Hisobingiz 0 so'mga tenglashtirildi. Yangi daromad yoki harajatlaringizni yozishingiz mumkin.",
        parse_mode="HTML"
    )

@router.message(F.text)
async def handle_user_text(message: Message):
    user_id = message.from_user.id
    user_text = message.text.strip()
    
    await register_user(
        user_id=user_id,
        full_name=message.from_user.full_name,
        username=message.from_user.username or ""
    )

    # Foydalanuvchining hozirgi hisoboti
    summary = await get_financial_summary(user_id)
    
    # Gemini AI bilan tahlil qilish
    analysis = await analyze_message_with_ai(user_text, summary)
    intent = analysis.get("intent", "general_chat")
    items = analysis.get("items", [])
    ai_reply = analysis.get("ai_reply", "")

    if intent == "add_transaction" and items:
        # DB ga saqlash
        saved_items = await add_transactions(user_id, items, raw_message=user_text)
        new_summary = await get_financial_summary(user_id)
        
        reply_text = format_transaction_saved(saved_items, new_summary)
        if ai_reply and len(ai_reply) < 200:
            reply_text += f"\n\n💬 <i>{ai_reply}</i>"
            
        await message.answer(reply_text, parse_mode="HTML")

    elif intent == "query_balance":
        categories = await get_category_summary(user_id)
        text = format_balance_report(summary, categories)
        if ai_reply:
            text += f"\n\n💬 <i>{ai_reply}</i>"
        await message.answer(text, parse_mode="HTML")

    elif intent == "query_expenses":
        expenses = await get_detailed_expenses(user_id, limit=40)
        text = format_detailed_expenses_report(expenses, summary)
        if ai_reply:
            text += f"\n\n💬 <i>{ai_reply}</i>"
        await message.answer(text, parse_mode="HTML")

    elif intent == "delete_last":
        deleted = await delete_last_transaction(user_id)
        if deleted:
            new_summary = await get_financial_summary(user_id)
            reply = (
                f"🗑 <b>Oxirgi yozuv o'chirildi:</b> {deleted['description']} ({format_money(deleted['amount'])})\n"
                f"📊 <b>Qolgan balans:</b> <b>{format_money(new_summary['balance'])}</b>"
            )
        else:
            reply = "ℹ️ O'chirish uchun yozuv topilmadi."
        await message.answer(reply, parse_mode="HTML")

    elif intent == "clear_all":
        await clear_user_data(user_id)
        await message.answer(
            "🧹 <b>Barcha hisob-kitoblar tozalandi!</b>\n"
            "Yangi ma'lumotlarni yuborishingiz mumkin.",
            parse_mode="HTML"
        )

    else:
        # Umumiy suhbat yoki javob
        if ai_reply:
            # Agar foydalanuvchida daromad yoki xarajat kiritilgan bo'lsa, balansni eslatib o'tamiz
            if summary["total_income"] > 0 or summary["total_expense"] > 0:
                ai_reply += f"\n\n💳 <i>Hozirgi balansingiz: {format_money(summary['balance'])}</i>"
            await message.answer(ai_reply, parse_mode="HTML")
        else:
            await message.answer(
                "Xabaringizni tushundim. Agar harajat yoki daromad kiritmoqchi bo'lsangiz, masalan:\n"
                "<i>1 kg olma uchun 10 ming som, 2 kg banan uchun 20 ming</i> deb yozing.",
                parse_mode="HTML"
            )
