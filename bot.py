import os
import telebot
import easyocr
import cv2
import numpy as np
from flask import Flask, request
from PIL import Image
import io
# Tokenlarni Render sozlamalaridan olamiz
TOKEN = os.environ.get('BOT_TOKEN')
# Agar Gemini ishlatsangiz:
# GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# OCR modelini yuklash (faqat bir marta xotiraga yuklanadi)
# O'zbek ('uz') va ingliz ('en') tillari uchun
reader = easyocr.Reader(['uz', 'en'])

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Salom! Men mutlaqo bepul OCR botman. Rasm yuboring, undagi matnlarni o'qib beraman.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    msg = bot.reply_to(message, "Rasm tahlil qilinmoqda...")
    
    try:
        # Rasmni yuklab olish
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Rasmni numpy arrayga o'tkazish (EasyOCR uchun)
        image_bytes = io.BytesIO(downloaded_file)
        img = Image.open(image_bytes)
        img_np = np.array(img)

        # Matnni aniqlash
        result = reader.readtext(img_np, detail=0)
        
        if result:
            final_text = "\n".join(result)
            bot.edit_message_text(f"Aniqlangan matn:\n\n`{final_text}`", message.chat.id, msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text("Rasmda matn topilmadi.", message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"Xatolik: {str(e)}", message.chat.id, msg.message_id)

if __name__ == "__main__":
    # Render uchun port
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
