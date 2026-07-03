import telebot
import os
import json
import math
import time
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread
import pytesseract
from PIL import Image

# Flask web sunucusu (Render için)
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot aktif!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# AYARLAR
TOKEN = "8925524634:AAEmc6YhLixJqCz3wN87JG2Hu4s6JAHH4Bk"
bot = telebot.TeleBot(TOKEN)
VERI_DOSYASI = "otopark_verileri.json"
ZAMAN_DILIMI = pytz.timezone('Europe/Skopje')

def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "araclar" not in data: return {"araclar": data, "toplam_kazanc": 0}
                return data
        except: return {"araclar": {}, "toplam_kazanc": 0}
    return {"araclar": {}, "toplam_kazanc": 0}

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

def ucret_hesapla(toplam_dakika):
    if toplam_dakika <= 60: return 40
    saat = toplam_dakika // 60
    dakika_kalan = toplam_dakika % 60
    ucret = saat * 40 + (math.ceil(dakika_kalan / 15) * 10)
    return ucret

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_path = "temp_plaka.jpg"
    with open(file_path, "wb") as f: f.write(downloaded_file)
    
    try:
        plaka = pytesseract.image_to_string(
            Image.open(file_path), 
            config='--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        ).strip().upper()
        
        if len(plaka) >= 5:
            message.text = plaka
            bot.reply_to(message, f"🔍 Tespit edilen: *{plaka}*", parse_mode="Markdown")
            islem(message)
        else:
            bot.reply_to(message, "❌ Plaka okunamadı. Lütfen daha net çek.")
    finally:
        if os.path.exists(file_path): os.remove(file_path)

@bot.message_handler(func=lambda message: True)
def islem(message):
    if message.text.startswith('/'): return
    metin = message.text.lower().strip()
    data = verileri_yukle()
    veriler = data["araclar"]

    if metin == ".arabalar":
        if not veriler: bot.reply_to(message, "🅿️ Otopark boş.")
        else:
            liste = "\n".join([f"🚗 {p} (Giriş: {v['giris']})" for p, v in veriler.items()])
            bot.reply_to(message, f"📋 *İçerideki Araçlar:*\n\n{liste}", parse_mode="Markdown")
    
    elif metin == ".promet":
        bot.reply_to(message, f"💰 *Toplam Gelir: {data['toplam_kazanc']} DENAR*", parse_mode="Markdown")

    elif metin.startswith('.exit'):
        plaka = metin.replace(".exit", "").strip().upper()
        if plaka in veriler:
            giris_dt = datetime.strptime(veriler[plaka]["giris"], "%H:%M")
            simdi = datetime.now(ZAMAN_DILIMI)
            delta = (simdi - simdi.replace(hour=giris_dt.hour, minute=giris_dt.minute, second=0, microsecond=0)).total_seconds() / 60
            ucret = ucret_hesapla(int(max(0, delta)))
            
            data["toplam_kazanc"] += ucret
            del veriler[plaka]
            verileri_kaydet(data)
            bot.reply_to(message, f"📤 *{plaka}* çıkış yaptı.\n💰 Ödeme: *{ucret} DENAR*", parse_mode="Markdown")
        else: bot.reply_to(message, "❌ Bu plaka kayıtlı değil.")
    
    else:
        plaka = metin.upper()
        giris_vakti = datetime.now(ZAMAN_DILIMI).strftime("%H:%M")
        veriler[plaka] = {"giris": giris_vakti}
        verileri_kaydet(data)
        bot.reply_to(message, f"✅ *{plaka}* giriş yaptı.", parse_mode="Markdown")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    time.sleep(5) # Render portu yakalasın diye
    bot.infinity_polling()
    
