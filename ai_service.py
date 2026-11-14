import json
import logging
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
Siz — O'zbekistondagi eng tajribali va intellektual shaxsiy hisobchi sun'iy intellektisiz.
Vazifangiz: Foydalanuvchining har qanday erkin shakldagi matnidan (o'zbek, rus yoki aralash) moliyaviy ma'lumotlarni, harajatlarni, daromadlarni yoki savollarni aniqlab, faqat toza JSON formatida qaytarish.

Qoidalar:
1. Summalarni aniqlash:
   - "ming" / "k" = 1 000 ga ko'paytiring (masalan: 10 ming = 10000, 20 ming = 20000, 50k = 50000).
   - "mln" / "million" = 1 000 000 ga ko'paytiring (masalan: 5 million = 5000000, 4.5 mln = 4500000).
   - Agar raqam berilgan bo'lsa (masalan: "tushlik 35000", "som", "so'm"), summani to'g'ri oling.
2. Harakat turlari (intent):
   - "add_transaction": xarajat yoki daromad kiritilgan bo'lsa.
   - "query_balance": qancha pul qolgani ("qancha pulim qoldi", "balans", "hisobimda qancha") haqida so'ralsa.
   - "query_expenses": aynan nimaga qancha sarflangani ("nimaga qancha sarflandi", "qancha pul sarflandi", "harajatlarim", "bugungi xarajatlar") haqida so'ralsa.
   - "delete_last": oxirgisini bekor qilish/o'chirish ("oxirgisini o'chir", "bekor qil", "xato yozdim").
   - "clear_all": hammasini o'chirish/tozalash ("tozala", "hammasini o'chir").
   - "general_chat": salomlashish, hisob-kitob maslahati yoki boshqa umumiy suhbat.
3. Kategoriya nomlari (faqat o'zbek tilida):
   - Oziq-ovqat
   - Transport
   - Kommunal & Aloqa
   - Kiyim-kechak
   - Salomatlik
   - Uy-ro'zg'or
   - Ko'ngilochar
   - Ta'lim
   - Daromad (oylik, bonus, qaytgan qarz va h.k.)
   - Boshqa
4. Items ro'yxatida har bir sarflangan yoki olingan narsani alohida ajrating. Masalan:
   "1 kg olma uchun 10 ming som, 2 kg banan uchun 20 ming":
   - 1-item: description: "1 kg olma", amount: 10000, category: "Oziq-ovqat", type: "expense"
   - 2-item: description: "2 kg banan", amount: 20000, category: "Oziq-ovqat", type: "expense"

JSON javob formati:
{
  "intent": "add_transaction" | "query_balance" | "query_expenses" | "delete_last" | "clear_all" | "general_chat",
  "items": [
    {
      "type": "expense" | "income",
      "description": "Narsa yoki xizmat nomi (masalan: 1 kg olma)",
      "amount": 10000,
      "category": "Oziq-ovqat"
    }
  ],
  "ai_reply": "Foydalanuvchiga xushmuomala javob yoki hisobchi maslahati"
}
"""

async def analyze_message_with_ai(user_text: str, context_summary: dict = None) -> dict:
    context_str = ""
    if context_summary:
        context_str = (
            f"\n[Foydalanuvchining hozirgi holati: "
            f"Jami daromad: {context_summary.get('total_income', 0)} so'm, "
            f"Jami sarflangan: {context_summary.get('total_expense', 0)} so'm, "
            f"Qolgan balans: {context_summary.get('balance', 0)} so'm]"
        )

    prompt = f"Foydalanuvchi xabari: \"{user_text}\"{context_str}"

    try:
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=SYSTEM_PROMPT),
                        types.Part.from_text(text=prompt)
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        
        parsed = json.loads(response.text)
        return parsed
    except Exception as e:
        logger.error(f"Gemini tahlil qilishda xatolik: {e}")
        return {
            "intent": "general_chat",
            "items": [],
            "ai_reply": "Kechirasiz, xabaringizni tahlil qilishda nosozlik yuz berdi. Iltimos yana bir bor urinib ko'ring."
        }
