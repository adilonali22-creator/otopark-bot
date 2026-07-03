import telebot
import pytesseract
from PIL import Image
import os
import json
import math
import time
from datetime import datetime
import pytz

# Linux sunucusu (Railway) için tesseract yolu
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

TOKEN = "8925524634:AAEmc6YhLixJqCz3wN87JG2Hu4s6JAHH4Bk"
bot = telebot.TeleBot(TOKEN)
VERI_DOSYASI = "otopark_verileri.json"
ZAMAN_DILIMI = pytz.timezone('Europe/Skopje')

def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {"araclar": {}, "toplam_kazanc": 0}
    return {"araclar": {}, "toplam_kazanc": 0}

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

def ucret_hesapla(toplam_dakika):
    if toplam_dakika <= 60: return 40
    saat = toplam_dakika // 60
    dakika_kalan = toplam_dakika % 60
    return (saat * 40) + (math.ceil(dakika_kalan / 15) * 10)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "🔍 Taranıyor...")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("temp.jpg", "wb") as f: f.write(downloaded_file)
    
    # Yerel okuma
    plaka = pytesseract.image_to_string(Image.open("temp.jpg"), config='--psm 7').strip().upper()
    plaka = "".join(filter(str.isalnum, plaka))
    
    if len(plaka) >= 5:
        bot.reply_to(message, f"✅ Tespit: {plaka}")
        # Tespit edilen plakayı otomatik işle
        message.text = plaka
        islem(message)
    else:
        bot.reply_to(message, "❌ Okunamadı, net çek.")
    if os.path.exists("temp.jpg"): os.remove("temp.jpg")

@bot.message_handler(func=lambda message: True)
def islem(message):
    if message.text.startswith('/'): return
    metin = message.text.lower().strip()
    data = verileri_yukle()
    veriler = data["araclar"]

    if metin == ".arabalar":
        if not veriler: bot.reply_to(message, "🅿️ Boş.")
        else: bot.reply_to(message, "\n".join([f"🚗 {p} (Giriş: {v['giris']})" for p, v in veriler.items()]))
    
    elif metin == ".promet":
        bot.reply_to(message, f"💰 Toplam: {data['toplam_kazanc']} DENAR")

    elif metin.startswith('.exit'):
        plaka = metin.replace(".exit", "").strip().upper()
        if plaka in veriler:
            giris_dt = datetime.strptime(veriler[plaka]["giris"], "%H:%M")
            delta = (datetime.now(ZAMAN_DILIMI) - datetime.now(ZAMAN_DILIMI).replace(hour=giris_dt.hour, minute=giris_dt.minute, second=0)).total_seconds() / 60
            ucret = ucret_hesapla(int(max(0, delta)))
            data["toplam_kazanc"] += ucret
            del veriler[plaka]
            verileri_kaydet(data)
            bot.reply_to(message, f"📤 {plaka} çıktı. Ödeme: {ucret} DENAR")
        else: bot.reply_to(message, "❌ Kayıtlı değil.")
    
    else:
        plaka = metin.upper()
        veriler[plaka] = {"giris": datetime.now(ZAMAN_DILIMI).strftime("%H:%M")}
        verileri_kaydet(data)
        bot.reply_to(message, f"✅ {plaka} giriş yaptı.")

bot.infinity_polling()
