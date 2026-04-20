import os
import telebot
import easyocr
import cv2
import numpy as np
from flask import Flask, request
from PIL import Image
import io

# 1. Sozlamalarni Render'dan olamiz
TOKEN = os.environ.get('BOT_TOKEN')
RENDER_URL = os.environ.get('RENDER_URL') # Masalan: https://bot-nomi.onrender.com

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# OCR modelini yuklash (faqat bir marta xotiraga yuklanadi)
# O'zbek va ingliz tillari uchun
try:
    reader = easyocr.Reader(['uz', 'en'], gpu=False)
except Exception as e:
    print(f"Model yuklashda xatolik: {e}")

# 2. Webhook sozlamalari
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    # Webhook manzilini o'rnatish
    status = bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    if status:
        return "Webhook muvaffaqiyatli o'rnatildi!", 200
    else:
        return "Webhook o'rnatishda xatolik yuz berdi.", 500

# 3. Bot komandalari
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Salom! Men mutlaqo bepul OCR botman. Rasm yuboring, undagi matnlarni o'qib beraman.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    msg = bot.reply_to(message, "Rasm tahlil qilinmoqda, iltimos kuting...")
    
    try:
        # Rasmni yuklab olish
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Rasmni numpy arrayga o'tkazish
        image_bytes = io.BytesIO(downloaded_file)
        img = Image.open(image_bytes)
        img_np = np.array(img)

        # Matnni aniqlash (EasyOCR)
        result = reader.readtext(img_np, detail=0)
        
        if result:
            final_text = "\n".join(result)
            # Agar matn juda uzun bo'lsa, Telegram limitiga moslash
            if len(final_text) > 4000:
                final_text = final_text[:4000] + "..."
            bot.edit_message_text(f"Aniqlangan matn:\n\n`{final_text}`", message.chat.id, msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text("Rasmda matn topilmadi.", message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"Xatolik yuz berdi. Balki rasm juda kattadir yoki serverda xotira yetmadi.", message.chat.id, msg.message_id)
        print(f"Xatolik: {e}")

if __name__ == "__main__":
    # Render avtomatik beradigan PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
