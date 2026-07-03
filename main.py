import telebot
import requests
import json
import math
import os
from datetime import datetime
import pytz

TOKEN = "8925524634:AAEmc6YhLixJqCz3wN87JG2Hu4s6JAHH4Bk"
DEEPAI_API_KEY = "a417036e-d30e-436d-b873-1f19c8f6e80b" # DeepAI API Key
bot = telebot.TeleBot(TOKEN)
VERI_DOSYASI = "otopark_verileri.json"
ZAMAN_DILIMI = pytz.timezone('Europe/Skopje')

# Fiyatlandırma: 1 saate kadar 40, sonrası saat başı 40 + 15dk 10
def ucret_hesapla(toplam_dakika):
    if toplam_dakika <= 60: return 40
    saat = toplam_dakika // 60
    dakika_kalan = toplam_dakika % 60
    return (saat * 40) + (math.ceil(dakika_kalan / 15) * 10)

def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {"araclar": {}, "toplam_kazanc": 0}
    return {"araclar": {}, "toplam_kazanc": 0}

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "🚀 DeepAI ile plaka çözümleniyor...")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("temp.jpg", "wb") as f: f.write(downloaded_file)
    
    # DeepAI'ye gönder
    with open("temp.jpg", 'rb') as f:
        r = requests.post("https://api.deepai.org/api/ocr", files={'image': f}, headers={'api-key': DEEPAI_API_KEY})
    
    response = r.json()
    if 'output' in response:
        plaka = "".join(filter(str.isalnum, response['output'])).upper()
        bot.reply_to(message, f"✅ Tespit edilen: *{plaka}*\nOnaylıyorsan 'Giriş' yaz.", parse_mode="Markdown")
        message.temp_plaka = plaka
    else:
        bot.reply_to(message, "❌ DeepAI plakayı bulamadı. Lütfen manuel giriş yap.")

@bot.message_handler(func=lambda message: True)
def islem(message):
    text = message.text.upper().strip()
    data = verileri_yukle()
    
    if text == "GİRİŞ":
        # (Burada mantığı sen istediğin gibi tetikleyebilirsin)
        bot.reply_to(message, "✅ Giriş kaydedildi.")
    elif text.startswith(".EXIT"):
        plaka = text.replace(".EXIT", "").strip()
        if plaka in data["araclar"]:
            giris_saati = datetime.strptime(data["araclar"][plaka]["giris"], "%H:%M")
            fark = (datetime.now(ZAMAN_DILIMI).hour * 60 + datetime.now(ZAMAN_DILIMI).minute) - \
                   (giris_saati.hour * 60 + giris_saati.minute)
            ucret = ucret_hesapla(max(0, fark))
            data["toplam_kazanc"] += ucret
            del data["araclar"][plaka]
            verileri_kaydet(data)
            bot.reply_to(message, f"📤 Çıkış: {plaka}\n💰 Ödenecek: {ucret} Denar")
        else: bot.reply_to(message, "❌ Araç kayıtlı değil!")
    else:
        # Manuel kayıt
        data["araclar"][text] = {"giris": datetime.now(ZAMAN_DILIMI).strftime("%H:%M")}
        verileri_kaydet(data)
        bot.reply_to(message, f"✅ {text} kaydedildi.")

bot.infinity_polling()
