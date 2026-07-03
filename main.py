import telebot
import requests
import json
import math
import os
from datetime import datetime
import pytz

# API ve Bot ayarları
TOKEN = "8925524634:AAEmc6YhLixJqCz3wN87JG2Hu4s6JAHH4Bk"
API_TOKEN = "7b62ff5677db55f09f46dfe58a9e81c36cd18e89"
bot = telebot.TeleBot(TOKEN)
VERI_DOSYASI = "otopark_verileri.json"
ZAMAN_DILIMI = pytz.timezone('Europe/Skopje')

# Fiyatlandırma
def ucret_hesapla(toplam_dakika):
    if toplam_dakika <= 60: return 40
    saat = toplam_dakika // 60
    dakika_kalan = toplam_dakika % 60
    return (saat * 40) + (math.ceil(dakika_kalan / 15) * 10)

# Veri Yönetimi
def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {"araclar": {}, "toplam_kazanc": 0}
    return {"araclar": {}, "toplam_kazanc": 0}

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

# Fotoğraf işleme ve otomatik giriş
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "🚗 Plaka taranıyor ve giriş kaydediliyor...")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("temp.jpg", "wb") as f: f.write(downloaded_file)
    
    with open("temp.jpg", 'rb') as fp:
        response = requests.post(
            'https://api.platerecognizer.com/v1/plate-reader/',
            data=dict(regions=['mk']),
            files=dict(upload=fp),
            headers={'Authorization': f'Token {API_TOKEN}'})
    
    data = response.json()
    if 'results' in data and len(data['results']) > 0:
        plaka = data['results'][0]['plate'].upper()
        
        otopark_data = verileri_yukle()
        otopark_data["araclar"][plaka] = {"giris": datetime.now(ZAMAN_DILIMI).strftime("%H:%M")}
        verileri_kaydet(otopark_data)
        
        bot.reply_to(message, f"✅ {plaka} otoparka giriş yaptı.")
    else:
        bot.reply_to(message, "❌ Plaka okunamadı. Manuel olarak yaz (örn: TE1234AB).")

# İşlem Merkezi (.EXIT, .ARABALAR, .PROMET)
@bot.message_handler(func=lambda message: True)
def islem(message):
    metin = message.text.upper().strip()
    data = verileri_yukle()
    
    if metin == ".ARABALAR":
        if not data["araclar"]: bot.reply_to(message, "🅿️ Otopark boş.")
        else: bot.reply_to(message, "\n".join([f"🚗 {p} (Giriş: {v['giris']})" for p, v in data["araclar"].items()]))
            
    elif metin == ".PROMET":
        bot.reply_to(message, f"💰 Toplam Gelir: {data['toplam_kazanc']} DENAR")
        
    elif metin.startswith(".EXIT"):
        plaka = metin.replace(".EXIT", "").replace(" ", "").strip()
        bulundu = False
        for p in list(data["araclar"].keys()):
            if p.replace(" ", "") == plaka:
                giris = datetime.strptime(data["araclar"][p]["giris"], "%H:%M")
                simdi = datetime.now(ZAMAN_DILIMI)
                fark = (simdi.hour * 60 + simdi.minute) - (giris.hour * 60 + giris.minute)
                ucret = ucret_hesapla(max(0, fark))
                data["toplam_kazanc"] += ucret
                del data["araclar"][p]
                verileri_kaydet(data)
                bot.reply_to(message, f"📤 {p} çıkış. Ödeme: {ucret} DENAR")
                bulundu = True
                break
        if not bulundu: bot.reply_to(message, "❌ Araç bulunamadı!")
    
    # Manuel giriş (otomatik okumazsa)
    elif len(metin) >= 5:
        data["araclar"][metin] = {"giris": datetime.now(ZAMAN_DILIMI).strftime("%H:%M")}
        verileri_kaydet(data)
        bot.reply_to(message, f"✅ {metin} manuel giriş yaptı.")

bot.infinity_polling()
