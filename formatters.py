def format_money(amount: float | int) -> str:
    """Raqamni chiroyli ko'rinishda formatlaydi: 10000 -> 10 000 so'm"""
    amount_int = int(amount) if int(amount) == amount else round(amount, 2)
    return f"{amount_int:,}".replace(",", " ") + " so'm"

def format_transaction_saved(items: list[dict], summary: dict) -> str:
    """Xarajat yoki daromad qo'shilgandagi xabar matni"""
    incomes = [i for i in items if i.get("type") == "income"]
    expenses = [i for i in items if i.get("type") == "expense"]
    
    lines = []
    
    if expenses:
        lines.append("💸 <b>Xarajatlar saqlandi:</b>")
        for idx, item in enumerate(expenses, 1):
            desc = item.get("description", "Xarajat")
            amt = format_money(item.get("amount", 0))
            cat = item.get("category", "Boshqa")
            lines.append(f"  {idx}. <b>{desc}</b> — {amt} <i>({cat})</i>")
        
        cur_spent = sum(i.get("amount", 0) for i in expenses)
        lines.append(f"➖ <b>Kiritilgan jami xarajat:</b> {format_money(cur_spent)}")
        lines.append("")

    if incomes:
        lines.append("💰 <b>Daromad saqlandi:</b>")
        for idx, item in enumerate(incomes, 1):
            desc = item.get("description", "Daromad")
            amt = format_money(item.get("amount", 0))
            lines.append(f"  {idx}. <b>{desc}</b> — {amt}")
        
        cur_inc = sum(i.get("amount", 0) for i in incomes)
        lines.append(f"➕ <b>Kiritilgan jami daromad:</b> {format_money(cur_inc)}")
        lines.append("")

    lines.append("📊 <b>Hozirgi moliyaviy holatingiz:</b>")
    lines.append(f"• Jami daromad: <b>{format_money(summary['total_income'])}</b>")
    lines.append(f"• Jami sarflandi: <b>{format_money(summary['total_expense'])}</b>")
    
    balance = summary['balance']
    if balance >= 0:
        lines.append(f"• <b>Qolgan pulingiz:</b> 🟢 <b>{format_money(balance)}</b>")
    else:
        lines.append(f"• <b>Qolgan pulingiz (minusda):</b> 🔴 <b>{format_money(balance)}</b>")

    return "\n".join(lines)

def format_balance_report(summary: dict, categories: list[dict] = None) -> str:
    """Foydalanuvchi balansi va umumiy holat hisoboti"""
    lines = [
        "💳 <b>MOLIYAVIY HISOBOT</b>\n",
        f"💰 <b>Jami daromad:</b> {format_money(summary['total_income'])}",
        f"💸 <b>Jami sarflandi:</b> {format_money(summary['total_expense'])}",
    ]
    
    balance = summary["balance"]
    if balance >= 0:
        lines.append(f"🟢 <b>Qolgan pulingiz:</b> <b>{format_money(balance)}</b>\n")
    else:
        lines.append(f"🔴 <b>Qolgan pulingiz (kassada kamomad):</b> <b>{format_money(balance)}</b>\n")
        
    if categories:
        lines.append("🏷 <b>Xarajatlar kategoriyalar bo'yicha:</b>")
        for cat in categories:
            name = cat["category"]
            tot = format_money(cat["total_amount"])
            cnt = cat["count"]
            lines.append(f"• {name}: <b>{tot}</b> ({cnt} ta xarid)")
            
    if summary["total_income"] == 0 and summary["total_expense"] == 0:
        lines.append("<i>Hozircha hech qanday ma'lumot kiritilmagan. Oyligingiz yoki harajatlaringizni yozing!</i>")

    return "\n".join(lines)

def format_detailed_expenses_report(expenses: list[dict], summary: dict) -> str:
    """Aynan nimaga qancha pul sarflanganining batafsil ro'yxati"""
    if not expenses:
        return (
            "📭 <b>Hozircha hech qanday xarajat kiritilmagan.</b>\n\n"
            "Masalan shunday yozing:\n"
            "<i>1 kg olma uchun 10 ming som, 2 kg banan uchun 20 ming</i>"
        )
    
    lines = [
        "📝 <b>XARAJATLAR RO'YXATI (Nimaga qancha sarflandi):</b>\n"
    ]
    
    for idx, exp in enumerate(expenses, 1):
        desc = exp["description"]
        amt = format_money(exp["amount"])
        cat = exp["category"]
        date_str = exp["timestamp"][:16] if "timestamp" in exp and exp["timestamp"] else ""
        lines.append(f"{idx}. <b>{desc}</b> — {amt} <i>({cat})</i>")
        
    lines.append("")
    lines.append(f"💸 <b>Jami sarflangan summa:</b> {format_money(summary['total_expense'])}")
    lines.append(f"🟢 <b>Qolgan pulingiz:</b> {format_money(summary['balance'])}")
    
    return "\n".join(lines)
