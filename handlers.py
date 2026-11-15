import logging
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
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
from ai_service import analyze_message_with_ai, analyze_audio_with_ai
from formatters import (
    format_money,
    format_transaction_saved,
    format_balance_report,
    format_detailed_expenses_report
)

router = Router()
logger = logging.getLogger(__name__)

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Asosiy pastki menyu tugmalari"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💳 Balans"),
                KeyboardButton(text="📝 Xarajatlar")
            ],
            [
                KeyboardButton(text="↩️ Bekor qilish"),
                KeyboardButton(text="🗑 Xotirani tozalash")
            ]
        ],
        resize_keyboard=True,
        persistent=True
    )

def get_clear_confirm_keyboard() -> InlineKeyboardMarkup:
    """Xotirani tozalashni tasdiqlash uchun tugmalar"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, tozalansin", callback_data="confirm_clear_memory"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_clear_memory")
            ]
        ]
    )

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
        "Menga daromadlaringiz va harajatlaringizni <b>matn (text)</b> yoki <b>ovozli xabar (audio) 🎙</b> shaklida yuborsangiz kifoya. "
        "Men barchasini eslab qolaman va doimiy hisob-kitob qilib boraman:\n"
        "• Qancha pul sarflandi\n"
        "• Aynan nimaga qancha pul ketdi\n"
        "• Qancha pulingiz qoldi (balans)\n\n"
        "💡 <b>Misollar:</b>\n"
        "▫️ <i>«Oylik maoshim 6 000 000 so'm»</i>\n"
        "▫️ <i>«1 kg olma uchun 10 ming som, 2 kg banan uchun 20 ming»</i>\n"
        "▫️ <i>«Tushlikka 35 000 va taksiga 12 000 ketdi»</i>\n"
        "▫️ <i>«Qancha pulim qoldi?»</i> yoki <i>«Nimaga qancha sarfladim?»</i>\n\n"
        "Pastdagi tugmalar orqali ham tezkor buyruqlarni berishingiz mumkin! 👇"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_keyboard())

@router.message(Command("yordam"))
@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📖 <b>Hisobchi botdan foydalanish bo'yicha qo'llanma:</b>\n\n"
        "Siz istalgan vaqtda botga <b>matn yozishingiz</b> yoki <b>ovozli xabar yuborishingiz</b> mumkin:\n\n"
        "1️⃣ <b>Daromad kiritish:</b>\n"
        "• <i>«Oyligim 5 million so'm»</i>\n"
        "• <i>«Menga 400 ming qarz qaytarishdi»</i>\n\n"
        "2️⃣ <b>Xarajatlarni kiritish:</b>\n"
        "• <i>«1 kg olma uchun 10 ming som, 2 kg banan uchun 20 ming»</i>\n"
        "• <i>«Benzinga 150000 som to'ladim»</i>\n"
        "• <i>«Kommunal to'lov 250 ming»</i>\n\n"
        "🎙 <b>Ovozli xabar:</b> Mikrofon tugmasini bosib xarajat yoki daromadingizni gapirib yuborsangiz, bot uni tinglab darhol hisobga oladi.\n\n"
        "3️⃣ <b>Tugmalar va boshqaruv:</b>\n"
        "• <b>💳 Balans</b> — Qolgan mablag' va holat\n"
        "• <b>📝 Xarajatlar</b> — Nimaga qancha ketgani ro'yxati\n"
        "• <b>↩️ Bekor qilish</b> — Oxirgi yozuvni o'chirish\n"
        "• <b>🗑 Xotirani tozalash</b> — Barcha yozuvlarni noldan tozalash"
    )
    await message.answer(help_text, parse_mode="HTML", reply_markup=get_main_keyboard())

@router.message(Command("balans"))
@router.message(Command("hisob"))
async def cmd_balance(message: Message):
    summary = await get_financial_summary(message.from_user.id)
    categories = await get_category_summary(message.from_user.id)
    text = format_balance_report(summary, categories)
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())

@router.message(Command("xarajatlar"))
async def cmd_expenses(message: Message):
    summary = await get_financial_summary(message.from_user.id)
    expenses = await get_detailed_expenses(message.from_user.id, limit=40)
    text = format_detailed_expenses_report(expenses, summary)
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())

@router.message(Command("bekor"))
@router.message(Command("undo"))
async def cmd_undo(message: Message):
    user_id = message.from_user.id
    deleted = await delete_last_transaction(user_id)
    if not deleted:
        await message.answer("ℹ️ O'chirish uchun oxirgi operatsiya topilmadi.", parse_mode="HTML", reply_markup=get_main_keyboard())
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
    await message.answer(reply, parse_mode="HTML", reply_markup=get_main_keyboard())

async def ask_clear_memory(message: Message):
    """Xotirani tozalashdan oldin tasdiqlash so'rash"""
    text = (
        "⚠️ <b>Xotirani tozalashni tasdiqlang:</b>\n\n"
        "Barcha kiritilgan daromad va xarajatlar tarixi butunlay o'chiriladi hamda balansingiz 0 so'mga tenglashtiriladi.\n\n"
        "Haqiqatan ham barcha ma'lumotlarni o'chirib tashlamoqchimisiz?"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_clear_confirm_keyboard())

@router.message(Command("tozalash"))
async def cmd_clear(message: Message):
    await ask_clear_memory(message)

@router.callback_query(F.data == "confirm_clear_memory")
async def on_confirm_clear(callback: CallbackQuery):
    await clear_user_data(callback.from_user.id)
    await callback.message.edit_text(
        "🧹 <b>Barcha xotira va hisob-kitoblar muvaffaqiyatli tozalandi!</b>\n\n"
        "Balansingiz 0 so'mga tenglashtirildi. Yangi ma'lumotlaringizni yozishingiz yoki ovozli xabar orqali yuborishingiz mumkin.",
        parse_mode="HTML"
    )
    await callback.answer("Xotira tozalandi! ✅")

@router.callback_query(F.data == "cancel_clear_memory")
async def on_cancel_clear(callback: CallbackQuery):
    await callback.message.edit_text(
        "❌ <b>Xotirani tozalash bekor qilindi.</b>\n"
        "Barcha hisob-kitoblaringiz va balansingiz o'zgarishsiz saqlab qolindi.",
        parse_mode="HTML"
    )
    await callback.answer("Bekor qilindi ❌")

@router.message(F.voice | F.audio)
async def handle_user_audio(message: Message):
    """Ovozli xabar (voice) va audio fayllarni qabul qilib qayta ishlash"""
    user_id = message.from_user.id
    
    await register_user(
        user_id=user_id,
        full_name=message.from_user.full_name,
        username=message.from_user.username or ""
    )

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    voice = message.voice or message.audio
    mime_type = getattr(voice, "mime_type", None) or "audio/ogg"

    try:
        file = await message.bot.download(voice)
        audio_bytes = file.read()
    except Exception as e:
        logger.error(f"Audio yuklab olishda xatolik: {e}")
        await message.answer(
            "Kechirasiz, ovozli xabarni yuklab olishda xatolik yuz berdi. Iltimos qaytadan yuboring.",
            reply_markup=get_main_keyboard()
        )
        return

    summary = await get_financial_summary(user_id)
    analysis = await analyze_audio_with_ai(audio_bytes, mime_type=mime_type, context_summary=summary)

    transcription = analysis.get("transcription", "").strip()
    intent = analysis.get("intent", "general_chat")
    items = analysis.get("items", [])
    ai_reply = analysis.get("ai_reply", "")

    header = ""
    if transcription:
        header = f"🎙 <b>Eshitilgan matn:</b> <i>«{transcription}»</i>\n\n"

    if intent == "add_transaction" and items:
        saved_items = await add_transactions(user_id, items, raw_message=transcription or "Ovozli xabar")
        new_summary = await get_financial_summary(user_id)
        
        reply_text = header + format_transaction_saved(saved_items, new_summary)
        if ai_reply and len(ai_reply) < 200:
            reply_text += f"\n\n💬 <i>{ai_reply}</i>"
            
        await message.answer(reply_text, parse_mode="HTML", reply_markup=get_main_keyboard())

    elif intent == "query_balance":
        categories = await get_category_summary(user_id)
        text = header + format_balance_report(summary, categories)
        if ai_reply:
            text += f"\n\n💬 <i>{ai_reply}</i>"
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())

    elif intent == "query_expenses":
        expenses = await get_detailed_expenses(user_id, limit=40)
        text = header + format_detailed_expenses_report(expenses, summary)
        if ai_reply:
            text += f"\n\n💬 <i>{ai_reply}</i>"
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())

    elif intent == "delete_last":
        deleted = await delete_last_transaction(user_id)
        if deleted:
            new_summary = await get_financial_summary(user_id)
            reply = (
                header +
                f"🗑 <b>Oxirgi yozuv o'chirildi:</b> {deleted['description']} ({format_money(deleted['amount'])})\n"
                f"📊 <b>Qolgan balans:</b> <b>{format_money(new_summary['balance'])}</b>"
            )
        else:
            reply = header + "ℹ️ O'chirish uchun yozuv topilmadi."
        await message.answer(reply, parse_mode="HTML", reply_markup=get_main_keyboard())

    elif intent == "clear_all":
        await ask_clear_memory(message)

    else:
        if ai_reply:
            reply = header + ai_reply
            if summary["total_income"] > 0 or summary["total_expense"] > 0:
                reply += f"\n\n💳 <i>Hozirgi balansingiz: {format_money(summary['balance'])}</i>"
            await message.answer(reply, parse_mode="HTML", reply_markup=get_main_keyboard())
        else:
            await message.answer(
                header + "Ovozingizni eshitdim, lekin undan daromad yoki xarajatni aniqlay olmadim. Iltimos qaytadan yozib yuboring.",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )

@router.message(F.text)
async def handle_user_text(message: Message):
    user_id = message.from_user.id
    user_text = message.text.strip()
    user_lower = user_text.lower()
    
    # Tezkor menyu tugmalari va oddiy so'zlarni 0.01 soniyada AI siz bajarish
    if user_lower in ["💳 balans", "balans", "balansim", "hisob", "hisobim", "/balans"]:
        await cmd_balance(message)
        return
    if user_lower in ["📝 xarajatlar", "xarajatlar", "harajatlar", "xarajatlarim", "harajatlarim", "/xarajatlar"]:
        await cmd_expenses(message)
        return
    if user_lower in ["↩️ bekor qilish", "bekor", "bekor qilish", "undo", "/bekor"]:
        await cmd_undo(message)
        return
    if user_lower in ["🗑 xotirani tozalash", "xotirani tozalash", "tozalash", "xotirani ochirish", "xotirani o'chirish", "/tozalash"]:
        await ask_clear_memory(message)
        return

    # Foydalanuvchiga bot o'ylayotganini ko'rsatish ("yozmoqda...")
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

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
            
        await message.answer(reply_text, parse_mode="HTML", reply_markup=get_main_keyboard())

    elif intent == "query_balance":
        categories = await get_category_summary(user_id)
        text = format_balance_report(summary, categories)
        if ai_reply:
            text += f"\n\n💬 <i>{ai_reply}</i>"
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())

    elif intent == "query_expenses":
        expenses = await get_detailed_expenses(user_id, limit=40)
        text = format_detailed_expenses_report(expenses, summary)
        if ai_reply:
            text += f"\n\n💬 <i>{ai_reply}</i>"
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())

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
        await message.answer(reply, parse_mode="HTML", reply_markup=get_main_keyboard())

    elif intent == "clear_all":
        await ask_clear_memory(message)

    else:
        # Umumiy suhbat yoki javob
        if ai_reply:
            if summary["total_income"] > 0 or summary["total_expense"] > 0:
                ai_reply += f"\n\n💳 <i>Hozirgi balansingiz: {format_money(summary['balance'])}</i>"
            await message.answer(ai_reply, parse_mode="HTML", reply_markup=get_main_keyboard())
        else:
            await message.answer(
                "Xabaringizni tushundim. Agar harajat yoki daromad kiritmoqchi bo'lsangiz, masalan:\n"
                "<i>1 kg olma uchun 10 ming som, 2 kg banan uchun 20 ming</i> deb yozing yoki ovozli xabar yuboring.",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
