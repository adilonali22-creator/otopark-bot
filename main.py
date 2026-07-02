import telebot
import os
import json
import pytesseract
from PIL import Image
from datetime import datetime
import pytz

TOKEN = "8925524634:AAEwFF9ZIxchbgiqZCJkQ9HqrSWqCWpvPq8"
bot = telebot.TeleBot(TOKEN)
VERI_DOSYASI = "otopark_verileri.json"
ZAMAN_DILIMI = pytz.timezone('Europe/Skopje')

# ... verileri_yukle ve verileri_kaydet fonksiyonları aynı kalacak ...

@bot.message_handler(content_types=['photo'])
def resim_isle(message):
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    with open("temp.jpg", "wb") as new_file:
        new_file.write(downloaded_file)
    
    # Plaka okuma (Tesseract OCR)
    plaka = pytesseract.image_to_string("temp.jpg").strip().upper()
    os.remove("temp.jpg") # Resmi siliyoruz
    
    # Plakayı kaydetme işlemi
    veriler = verileri_yukle()
    veriler[plaka] = {"giris": datetime.now(ZAMAN_DILIMI).strftime("%H:%M")}
    verileri_kaydet(veriler)
    bot.reply_to(message, f"📸 Fotoğraftan okunan plaka: {plaka}\n✅ Kaydedildi.")

@bot.message_handler(content_types=['text'])
def mesaj_isle(message):
    if message.text.startswith('/'): return
    
    plaka = message.text.upper().strip()
    veriler = verileri_yukle()
    
    if plaka in veriler:
        del veriler[plaka]
        verileri_kaydet(veriler)
        bot.reply_to(message, f"📤 {plaka} çıkış yaptı. (40 Denar)")
    else:
        # Plaka kayıtlı değilse GİRİŞ yap
        veriler[plaka] = {"giris": datetime.now(ZAMAN_DILIMI).strftime("%H:%M")}
        verileri_kaydet(veriler)
        bot.reply_to(message, f"✅ {plaka} giriş yaptı.")

bot.infinity_polling()
