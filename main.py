import telebot
import os
import json
import pytesseract
from PIL import Image
from datetime import datetime
import pytz

# Token'ın burada, başka hiçbir yere dokunma
TOKEN = "8925524634:AAEwFF9ZIxchbgiqZCJkQ9HqrSWqCWpvPq8"
bot = telebot.TeleBot(TOKEN)

VERI_DOSYASI = "otopark_verileri.json"
ZAMAN_DILIMI = pytz.timezone('Europe/Skopje')

def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

# --- FOTOĞRAF İŞLEME (Resim gelirse burası çalışır) ---
@bot.message_handler(content_types=['photo'])
def resim_isle(message):
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        dosya = "temp_plaka.jpg"
        with open(dosya, "wb") as f:
            f.write(downloaded_file)
        
        plaka = pytesseract.image_to_string(Image.open(dosya)).strip().upper()
        os.remove(dosya)
        
        if not plaka:
            bot.reply_to(message, "❌ Plaka okunamadı, lütfen daha net çek.")
            return
            
        veriler = verileri_yukle()
        if plaka in veriler:
            del veriler[plaka]
            verileri_kaydet(veriler)
            bot.reply_to(message, f"📤 {plaka} çıkış yaptı.")
        else:
            veriler[plaka] = {"giris": datetime.now(ZAMAN_DILIMI).strftime("%H:%M")}
            verileri_kaydet(veriler)
            bot.reply_to(message, f"✅ {plaka} giriş yaptı.")
    except Exception as e:
        bot.reply_to(message, f"Hata: {e}")

# --- METİN İŞLEME (Plaka yazarsan burası çalışır) ---
@bot.message_handler(func=lambda message: True)
def metin_isle(message):
    if message.text.startswith('/'): return
    
    plaka = message.text.upper().strip()
    veriler = verileri_yukle()
    
    if plaka in veriler:
        del veriler[plaka]
        verileri_kaydet(veriler)
        bot.reply_to(message, f"📤 {plaka} çıkış yaptı.")
    else:
        veriler[plaka] = {"giris": datetime.now(ZAMAN_DILIMI).strftime("%H:%M")}
        verileri_kaydet(veriler)
        bot.reply_to(message, f"✅ {plaka} giriş yaptı.")

print("Bot aktif...")
bot.infinity_polling()
