from datetime import datetime
import pytz
from telethon import TelegramClient, events
import google.generativeai as genai

# البيانات الأساسية وتوكن البوت الخاص بك
API_ID = 30770901
API_HASH = 'ab37305203102e7e98aa426eaeba7b114'
BOT_TOKEN = '8713539183:AAHQHS9ghWVitetG1XluFjNtZE4UA5FYQmU'

GEMINI_API_KEY = 'AQ.Ab8RN6LFblP7fgCmxodDWz4zXZXV6nD5eBI3XTPAp-nBskEA7Q'

genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# تشغيل البوت عبر التوكن (لا يطلب رقم هاتف ولا رمز تحقق)
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
seen_messages = set()

def ai_analyze_deal(message_text):
    prompt = f"""
    أنت خبير محترف في ألعاب الفيديو، الاشتراكات، الأسعار، واللهجات العربية المختلفة.
    قم بتحليل النص التالي المستخرج من مجموعة تليجرام:
    ---
    {message_text}
    ---
    أجب بكلمة واحدة فقط: "YES" إذا كان النص يحتوي على عرض حقيقي لألعاب، اشتراكات، أو بطاقات رقمية بسعر أو خصم.
    أجب بكلمة "NO" إذا كان النص مجرد دردشة عادية، سؤال، استفسار، إزعاج (Spam)، أو كلام عام لا يمثل عرضاً صريحاً.
    """
    try:
        response = ai_model.generate_content(prompt)
        answer = response.text.strip().upper()
        return "YES" in answer
    except Exception:
        return False

@client.on(events.NewMessage(pattern=r'/search\s+(.+?)\s+(\d{2}:\d{2})'))
async def smart_search_handler(event):
    target_group = event.pattern_match.group(1).strip()
    time_str = event.pattern_match.group(2).strip()
    
    try:
        hour, minute = map(int, time_str.split(':'))
    except ValueError:
        await event.respond("❌ صيغة الوقت غير صحيحة. استخدم الشكل التالي:\n`/search اسم_المجموعة 16:00`")
        return

    await event.respond(f"🔍 جاري فحص مجموعة `{target_group}` وبحث العروض منذ الساعة {time_str}...")

    now = datetime.now(pytz.utc)
    start_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    results_count = 0
    unique_deals = []

    try:
        async for message in client.iter_messages(target_group, limit=150):
            if message.date >= start_time and message.raw_text:
                
                msg_signature = message.raw_text[:60]
                if msg_signature in seen_messages:
                    continue
                
                if ai_analyze_deal(message.raw_text):
                    seen_messages.add(msg_signature)
                    
                    sender = await message.get_sender()
                    sender_name = "مجهول"
                    sender_username = "لا يوجد"
                    publisher_link = "لا يوجد"
                    
                    if sender:
                        sender_name = getattr(sender, 'first_name', '') or getattr(sender, 'title', 'غير معروف')
                        if getattr(sender, 'last_name', None):
                            sender_name += f" {sender.last_name}"
                            
                        if getattr(sender, 'username', None):
                            sender_username = f"@{sender.username}"
                            publisher_link = f"https://t.me/{sender.username}"

                    chat = await message.get_chat()
                    chat_username = getattr(chat, 'username', None)
                    
                    if chat_username:
                        message_link = f"https://t.me/{chat_username}/{message.id}"
                    else:
                        message_link = f"معرف داخلي للرسالة: {message.id} (المجموعة خاصة)"

                    deal_card = (
                        f"🎮 **عرض مؤكد ومنقح:**\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"{message.raw_text}\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"👤 **اسم الناشر:** {sender_name}\n"
                        f"🆔 **يوزر الناشر:** {sender_username}\n"
                        f"🔗 **رابط الحساب:** {publisher_link}\n"
                        f"📍 **رابط الرسالة الأصلية:** [اضغط للانتقال للعرض]({message_link})\n"
                    )
                    
                    unique_deals.append(deal_card)
                    results_count += 1
                    
                    if results_count >= 8:
                        break

        if unique_deals:
            final_report = f"✅ **تم العثور على {results_count} عرضاً مطابقاً لطلبك:**\n\n" + "\n\n".join(unique_deals)
            await event.respond(final_report)
        else:
            await event.respond(f"⚠️ لم يتم العثور على أي عروض جديدة في `{target_group}` بعد الساعة {time_str}.")

    except Exception as e:
        await event.respond(f"❌ حدث خطأ أثناء تنفيذ البحث: `{str(e)}`")

if __name__ == '__main__':
    print("البوت يعمل الآن بكامل طاقته عبر الـ Token...")
    client.run_until_disconnected()
