import requests
import json
import random
import time
import threading
import os
from urllib.parse import urlencode
from flask import Flask, request, jsonify

# Flask ilovasi
app = Flask(__name__)

# Bot sozlamalari
BOT_TOKEN = "7228078072:AAEh8Bl0OcAlxKZ0NFzTd8ZZQ39UbZr6A54"
CHANNEL_USERNAME = "@Sardor_ludoman"
ADMIN_ID = 6852738257
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
WEBHOOK_URL = " https://ker-lq4x.onrender.com"  # Bu yerga o'z domeningizni kiriting

# Global o'zgaruvchilar
user_states = {}
user_data = {}
admin_data = {
    'guide_video': None,
    'platforms': {
        'betwinner': {
            'registration_link': None,
            'download_link': None
        },
        'winwinbet': {
            'registration_link': None,
            'download_link': None
        },
        '1xbet': {
            'registration_link': None,
            'download_link': None
        },
        'xparibet': {
            'registration_link': None,
            'download_link': None
        }
    }
}

def send_request(method, data=None):
    """API ga so'rov yuborish"""
    try:
        url = f"{BASE_URL}/{method}"
        if data:
            response = requests.post(url, json=data)
        else:
            response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"API so'rovida xato: {e}")
        return None

def send_message(chat_id, text, reply_markup=None):
    """Xabar yuborish"""
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        data['reply_markup'] = reply_markup
    return send_request('sendMessage', data)

def edit_message_text(chat_id, message_id, text, reply_markup=None):
    """Xabarni tahrirlash"""
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        data['reply_markup'] = reply_markup
    return send_request('editMessageText', data)

def send_video(chat_id, video_id, caption=None):
    """Video yuborish"""
    data = {
        'chat_id': chat_id,
        'video': video_id
    }
    if caption:
        data['caption'] = caption
    return send_request('sendVideo', data)

def answer_callback_query(callback_query_id, text=None, show_alert=False):
    """Callback so'rovga javob berish"""
    data = {
        'callback_query_id': callback_query_id
    }
    if text:
        data['text'] = text
    if show_alert:
        data['show_alert'] = show_alert
    return send_request('answerCallbackQuery', data)

def get_chat_member(chat_id, user_id):
    """Foydalanuvchi statusini tekshirish"""
    data = {
        'chat_id': chat_id,
        'user_id': user_id
    }
    return send_request('getChatMember', data)

def create_inline_keyboard(buttons):
    """Inline klaviatura yaratish"""
    return {
        'inline_keyboard': buttons
    }

def check_subscription(user_id):
    """Kanalga obunani tekshirish"""
    try:
        result = get_chat_member(CHANNEL_USERNAME, user_id)
        if result and result.get('ok'):
            status = result['result']['status']
            return status not in ['left', 'kicked']
        return False
    except:
        return False

def set_webhook():
    """Webhook o'rnatish"""
    data = {
        'url': WEBHOOK_URL
    }
    return send_request('setWebhook', data)

def show_main_menu(chat_id, message_id=None, user_name="Foydalanuvchi"):
    """Asosiy menyuni ko'rsatish"""
    text = f"Salom {user_name} va Botga xush kelibsiz! O'zingiz foydalanadigan kantorni tanlang 👇"

    keyboard = create_inline_keyboard([
        [
            {'text': '🎰 Betwinner', 'callback_data': 'platform_betwinner'},
            {'text': '🎯 Winwinbet', 'callback_data': 'platform_winwinbet'}
        ],
        [
            {'text': '🎲 1xbet', 'callback_data': 'platform_1xbet'},
            {'text': '⚡ Xparibet', 'callback_data': 'platform_xparibet'}
        ],
        [{'text': '📖 Qo\'llanma', 'callback_data': 'guide'}]
    ])

    if message_id:
        edit_message_text(chat_id, message_id, text, keyboard)
    else:
        send_message(chat_id, text, keyboard)

def handle_platform_selection(chat_id, message_id, platform, user_name="Foydalanuvchi"):
    """Platform tanlovi"""
    promocodes = {
        'betwinner': 'SPED666',
        'winwinbet': 'SPED',
        '1xbet': 'SPED77',
        'xparibet': 'SPED'
    }

    platform_names = {
        'betwinner': 'Betwinner',
        'winwinbet': 'Winwinbet',
        '1xbet': '1xbet',
        'xparibet': 'Xparibet'
    }

    promo = promocodes.get(platform, 'SPED')
    platform_name = platform_names.get(platform, platform.title())

    text = f"""👤 Hurmatli foydalanuvchi! {user_name}

Eslatma! Bot to'g'ri ishlashi uchun:

1. 🟢 {platform_name} vzlom ilovasini yuklab oling


2. Ro'yxatdan o'tish va Promokod joyiga {promo} kiriting


3. Botga o'sha ro'yxatdan o'tgan profil ID tashlang


4. Botga noto'g'ri yoki feyk ID tashlansa bot hato signal ko'rsatadi!



Shartlarni bajargach "Davom etish" tugmasini bosing."""

    keyboard = create_inline_keyboard([
        [
            {'text': '📝 Ro\'yxatdan o\'tish', 'callback_data': f'register_{platform}'},
            {'text': '📱 Ilovani yuklab olish', 'callback_data': f'download_{platform}'}
        ],
        [{'text': '➡️ Davom etish', 'callback_data': f'continue_{platform}'}],
        [{'text': '🔙 Orqaga', 'callback_data': 'back_to_menu'}]
    ])

    edit_message_text(chat_id, message_id, text, keyboard)

def handle_continue(chat_id, message_id, platform, user_id):
    """Davom etish - ID so'rash"""
    user_states[user_id] = f"waiting_id_{platform}"

    text = """🆔 Iltimos, o'z profil ID'ingizni kiriting (9-11 raqamli son):

❗ Diqqat: Faqat raqamlarni kiriting!"""

    edit_message_text(chat_id, message_id, text)

def show_signal_menu(chat_id, user_id):
    """Signal menyusini ko'rsatish"""
    text = "🎯 Signal turini tanlang:"

    keyboard = create_inline_keyboard([
        [{'text': '🍎 Apple Fortuna Signal', 'callback_data': 'signal_apple'}],
        [{'text': '💣 Kamikadze Signal', 'callback_data': 'signal_kamikadze'}],
        [{'text': '🔙 Orqaga', 'callback_data': 'back_to_menu'}]
    ])

    send_message(chat_id, text, keyboard)

def handle_signal(chat_id, message_id, signal_type, user_id):
    """Signallarni ketma-ket berish"""
    if signal_type == "apple":
        game_name = "🍎 Apple Fortuna"
        emoji = "🍎"
    else:
        game_name = "💣 Kamikadze"
        emoji = "💣"

    # Foydalanuvchi holati - signal berish boshlangan
    if user_id not in user_data:
        user_data[user_id] = {}
    
    user_data[user_id]['signal_count'] = user_data[user_id].get('signal_count', 0) + 1
    signal_num = user_data[user_id]['signal_count']

    if signal_num <= 4:
        random_num = random.randint(1, 5)
        text = f"🎯 {game_name} Signal #{signal_num}:\n\n{emoji} O'yin signali: {random_num}"
        
        keyboard = create_inline_keyboard([
            [{'text': '🔄 Keyingi signal', 'callback_data': f'signal_{signal_type}'}],
            [{'text': '🔙 Orqaga', 'callback_data': 'back_to_menu'}]
        ])
    else:
        # 5-signal - to'xtash
        text = f"🎯 {game_name} Signal #{signal_num}:\n\n🛑 To'xtang! Pulni oling! 💰\n\n✅ Barcha signallar tugadi! Omad tilaymiz!"
        
        # Signal hisoblagichni tozalash
        user_data[user_id]['signal_count'] = 0
        
        keyboard = create_inline_keyboard([
            [{'text': '💰 Pulni oldim', 'callback_data': 'money_taken'}],
            [{'text': '🔄 Yangi signal boshlash', 'callback_data': f'new_signal_{signal_type}'}]
        ])

    edit_message_text(chat_id, message_id, text, keyboard)

def show_admin_panel(chat_id, message_id=None):
    """Admin panelini ko'rsatish"""
    text = "🔧 Admin paneli:\n\n"
    text += f"📹 Qo'llanma videosi: {'✅ Mavjud' if admin_data.get('guide_video') else '❌ Mavjud emas'}\n\n"
    
    # Har bir platform uchun havolalar holati
    for platform, data in admin_data['platforms'].items():
        platform_name = platform.title()
        reg_status = '✅' if data.get('registration_link') else '❌'
        down_status = '✅' if data.get('download_link') else '❌'
        text += f"{platform_name}:\n"
        text += f"  📝 Ro'yxat: {reg_status}  📱 Yuklab: {down_status}\n"

    keyboard = create_inline_keyboard([
        [{'text': '📹 Qo\'llanma videosini o\'zgartirish', 'callback_data': 'admin_change_video'}],
        [
            {'text': '🎰 Betwinner', 'callback_data': 'admin_platform_betwinner'},
            {'text': '🎯 Winwinbet', 'callback_data': 'admin_platform_winwinbet'}
        ],
        [
            {'text': '🎲 1xbet', 'callback_data': 'admin_platform_1xbet'},
            {'text': '⚡ Xparibet', 'callback_data': 'admin_platform_xparibet'}
        ]
    ])

    if message_id:
        edit_message_text(chat_id, message_id, text, keyboard)
    else:
        send_message(chat_id, text, keyboard)

def show_platform_admin(chat_id, message_id, platform):
    """Platform admin menyusi"""
    platform_names = {
        'betwinner': 'Betwinner',
        'winwinbet': 'Winwinbet',
        '1xbet': '1xbet',
        'xparibet': 'Xparibet'
    }
    
    platform_name = platform_names.get(platform, platform.title())
    platform_data = admin_data['platforms'][platform]
    
    text = f"🔧 {platform_name} sozlamalari:\n\n"
    text += f"📝 Ro'yxatdan o'tish: {'✅ Mavjud' if platform_data.get('registration_link') else '❌ Mavjud emas'}\n"
    text += f"📱 Yuklab olish: {'✅ Mavjud' if platform_data.get('download_link') else '❌ Mavjud emas'}"

    keyboard = create_inline_keyboard([
        [{'text': '📝 Ro\'yxat havolasini o\'zgartirish', 'callback_data': f'admin_register_{platform}'}],
        [{'text': '📱 Yuklab olish havolasini o\'zgartirish', 'callback_data': f'admin_download_{platform}'}],
        [{'text': '🔙 Admin panelga qaytish', 'callback_data': 'admin_back'}]
    ])

    edit_message_text(chat_id, message_id, text, keyboard)

def handle_start(update):
    """Start buyrug'ini qayta ishlash"""
    user_id = update.get('from', {}).get('id')
    chat_id = update.get('chat', {}).get('id')
    user_name = update.get('from', {}).get('first_name', 'Foydalanuvchi')

    # Obunani tekshirish
    if not check_subscription(user_id):
        text = "🔒 Botdan foydalanish uchun avval kanalimizga obuna bo'ling:"
        keyboard = create_inline_keyboard([
            [{'text': '📢 Kanalga obuna bo\'lish', 'url': f'https://t.me/{CHANNEL_USERNAME[1:]}'}],
            [{'text': '✅ Tekshirish', 'callback_data': 'check_subscription'}]
        ])
        send_message(chat_id, text, keyboard)
        return

    # Asosiy menyu
    show_main_menu(chat_id, user_name=user_name)

def handle_message(update):
    """Xabarlarni qayta ishlash"""
    user_id = update.get('from', {}).get('id')
    chat_id = update.get('chat', {}).get('id')
    text = update.get('text', '').strip()

    # Admin buyruqlari
    if text == '/admin' and user_id == ADMIN_ID:
        show_admin_panel(chat_id)
        return

    # ID kutish holati
    if user_id in user_states and user_states[user_id].startswith("waiting_id_"):
        platform = user_states[user_id].replace("waiting_id_", "")

        # ID validatsiyasi
        if text.isdigit() and 9 <= len(text) <= 11:
            if user_id not in user_data:
                user_data[user_id] = {}
            user_data[user_id]['platform'] = platform
            user_data[user_id]['user_id'] = text
            user_data[user_id]['signal_count'] = 0  # Signal hisoblagichni tozalash
            del user_states[user_id]

            show_signal_menu(chat_id, user_id)
        else:
            send_message(chat_id, """❌ Noto'g'ri ID format!

ID 9-11 raqamli son bo'lishi kerak.
Masalan: 123456789 yoki 12345678901""")
        return

    # Admin holatlar
    if user_id == ADMIN_ID and user_id in user_states:
        state = user_states[user_id]

        if state == "waiting_video":
            send_message(chat_id, "❌ Video fayl yuboring, matn emas!")
            return

        # Platform havolalarini kutish
        for platform in admin_data['platforms'].keys():
            if state == f"waiting_register_{platform}":
                if text.startswith(('http://', 'https://')):
                    admin_data['platforms'][platform]['registration_link'] = text
                    del user_states[user_id]
                    send_message(chat_id, f"✅ {platform.title()} ro'yxatdan o'tish havolasi saqlandi:\n{text}")
                    show_platform_admin(chat_id, platform)
                else:
                    send_message(chat_id, "❌ Noto'g'ri havola formati! HTTP yoki HTTPS bilan boshlang.")
                return

            elif state == f"waiting_download_{platform}":
                if text.startswith(('http://', 'https://')):
                    admin_data['platforms'][platform]['download_link'] = text
                    del user_states[user_id]
                    send_message(chat_id, f"✅ {platform.title()} yuklab olish havolasi saqlandi:\n{text}")
                    show_platform_admin(chat_id, platform)
                else:
                    send_message(chat_id, "❌ Noto'g'ri havola formati! HTTP yoki HTTPS bilan boshlang.")
                return

def handle_callback_query(update):
    """Callback so'rovlarini qayta ishlash"""
    callback_query = update.get('callback_query', {})
    data = callback_query.get('data')
    user_id = callback_query.get('from', {}).get('id')
    chat_id = callback_query.get('message', {}).get('chat', {}).get('id')
    message_id = callback_query.get('message', {}).get('message_id')
    user_name = callback_query.get('from', {}).get('first_name', 'Foydalanuvchi')
    callback_query_id = callback_query.get('id')

    # Callback javobini berish
    answer_callback_query(callback_query_id)

    # Obunani tekshirish
    if data == "check_subscription":
        if check_subscription(user_id):
            show_main_menu(chat_id, message_id, user_name)
        else:
            answer_callback_query(callback_query_id, "❌ Siz hali kanalga obuna bo'lmadingiz!", True)
        return

    # Platform tanlovi
    if data.startswith("platform_"):
        platform = data.replace("platform_", "")
        handle_platform_selection(chat_id, message_id, platform, user_name)
        return

    # Davom etish
    if data.startswith("continue_"):
        platform = data.replace("continue_", "")
        handle_continue(chat_id, message_id, platform, user_id)
        return

    # Ro'yxatdan o'tish
    if data.startswith("register_"):
        platform = data.replace("register_", "")
        reg_link = admin_data['platforms'][platform].get('registration_link')
        if reg_link:
            keyboard = create_inline_keyboard([
                [{'text': '🔗 Ro\'yxatdan o\'tish', 'url': reg_link}]
            ])
            edit_message_text(chat_id, message_id, "📝 Ro'yxatdan o'tish uchun tugmani bosing:", keyboard)
        else:
            answer_callback_query(callback_query_id, f"❌ {platform.title()} ro'yxatdan o'tish havolasi hali sozlanmagan!", True)
        return

    # Yuklab olish
    if data.startswith("download_"):
        platform = data.replace("download_", "")
        download_link = admin_data['platforms'][platform].get('download_link')
        if download_link:
            keyboard = create_inline_keyboard([
                [{'text': '📱 Ilovani yuklab olish', 'url': download_link}]
            ])
            edit_message_text(chat_id, message_id, "📱 Ilovani yuklab olish uchun tugmani bosing:", keyboard)
        else:
            answer_callback_query(callback_query_id, f"❌ {platform.title()} yuklab olish havolasi hali sozlanmagan!", True)
        return

    # Qo'llanma
    if data == "guide":
        if admin_data.get('guide_video'):
            send_video(chat_id, admin_data['guide_video'], "📖 Qo'llanma videosi")
            keyboard = create_inline_keyboard([
                [{'text': '🔙 Asosiy menyu', 'callback_data': 'back_to_menu'}]
            ])
            edit_message_text(chat_id, message_id, "📖 Qo'llanma videosi yuborildi!", keyboard)
        else:
            answer_callback_query(callback_query_id, "❌ Qo'llanma videosi hali yuklanmagan!", True)
        return

    # Signal turlari
    if data.startswith("signal_"):
        signal_type = data.replace("signal_", "")
        handle_signal(chat_id, message_id, signal_type, user_id)
        return

    # Yangi signal boshlash
    if data.startswith("new_signal_"):
        signal_type = data.replace("new_signal_", "")
        # Signal hisoblagichni tozalash
        if user_id in user_data:
            user_data[user_id]['signal_count'] = 0
        handle_signal(chat_id, message_id, signal_type, user_id)
        return

    # Pulni olish
    if data == "money_taken":
        answer_callback_query(callback_query_id, "🎉 Tabriklaymiz! Muvaffaqiyatli o'yin!", True)
        show_main_menu(chat_id, message_id, user_name)
        return

    # Orqaga qaytish
    if data == "back_to_menu":
        show_main_menu(chat_id, message_id, user_name)
        return

    # Admin panel
    if user_id == ADMIN_ID:
        if data == "admin_change_video":
            user_states[user_id] = "waiting_video"
            edit_message_text(chat_id, message_id, """📹 Yangi qo'llanma videosini yuboring:

Video fayl sifatida yuboring!""")

        elif data.startswith("admin_platform_"):
            platform = data.replace("admin_platform_", "")
            show_platform_admin(chat_id, message_id, platform)

        elif data.startswith("admin_register_"):
            platform = data.replace("admin_register_", "")
            user_states[user_id] = f"waiting_register_{platform}"
            edit_message_text(chat_id, message_id, f"""🔗 {platform.title()} uchun yangi ro'yxatdan o'tish havolasini kiriting:

Masalan: https://example.com/register""")

        elif data.startswith("admin_download_"):
            platform = data.replace("admin_download_", "")
            user_states[user_id] = f"waiting_download_{platform}"
            edit_message_text(chat_id, message_id, f"""📱 {platform.title()} uchun yangi yuklab olish havolasini kiriting:

Masalan: https://example.com/download""")

        elif data == "admin_back":
            show_admin_panel(chat_id, message_id)

def handle_video(update):
    """Video xabarlarini qayta ishlash"""
    user_id = update.get('from', {}).get('id')
    chat_id = update.get('chat', {}).get('id')

    if user_id == ADMIN_ID and user_states.get(user_id) == "waiting_video":
        video = update.get('video', {})
        if video:
            admin_data['guide_video'] = video.get('file_id')
            del user_states[user_id]
            send_message(chat_id, "✅ Qo'llanma videosi muvaffaqiyatli saqlandi!")
            show_admin_panel(chat_id)

def process_update(update):
    """Yangilanishni qayta ishlash"""
    try:
        # Start buyrug'i
        if 'message' in update and update['message'].get('text') == '/start':
            handle_start(update['message'])

        # Oddiy xabarlar
        elif 'message' in update and 'text' in update['message']:
            handle_message(update['message'])

        # Video xabarlar
        elif 'message' in update and 'video' in update['message']:
            handle_video(update['message'])

        # Callback so'rovlar
        elif 'callback_query' in update:
            handle_callback_query(update)

    except Exception as e:
        print(f"❌ Xato: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint"""
    try:
        update = request.get_json()
        if update:
            process_update(update)
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Webhook xatosi: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/')
def index():
    """Asosiy sahifa"""
    return "Bot ishlayapti!"

@app.route('/set_webhook')
def setup_webhook():
    """Webhookni o'rnatish"""
    result = set_webhook()
    if result and result.get('ok'):
        return "Webhook muvaffaqiyatli o'rnatildi!"
    else:
        return f"Webhook o'rnatishda xato: {result}"

if __name__ == "__main__":
    print("🤖 Flask Bot ishga tushmoqda...")
    print("🔗 Webhook o'rnatish uchun: /set_webhook sahifasiga kiring")

    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)

