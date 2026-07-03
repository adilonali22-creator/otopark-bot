import telebot
import requests
import json
import math
import os
from datetime import datetime
import pytz

TOKEN = "8925524634:AAEmc6YhLixJqCz3wN87JG2Hu4s6JAHH4Bk"
bot = telebot.TeleBot(TOKEN)
VERI_DOSYASI = "otopark_verileri.json"
ZAMAN_DILIMI = pytz.timezone('Europe/Skopje')

# 1. FİYATLANDIRMA MANTIĞI
def ucret_hesapla(toplam_dakika):
    if toplam_dakika <= 60: return 40
    saat = toplam_dakika // 60
    dakika_kalan = toplam_dakika % 60
    return (saat * 40) + (math.ceil(dakika_kalan / 15) * 10)

# 2. VERİ YÖNETİMİ
def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {"araclar": {}, "toplam_kazanc": 0}
    return {"araclar": {}, "toplam_kazanc": 0}

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

# 3. PROFESYONEL PLAKA OKUMA (MAKEDONYA ODAKLI)
def plakayi_oku(image_path):
    with open(image_path, 'rb') as fp:
        response = requests.post(
            'https://api.platerecognizer.com/v1/plate-reader/',
            data=dict(regions=['mk']),
            files=dict(upload=fp),
            headers={'Authorization': 'Token 40228389650d52481079366e6b4859f13e512411'})
    data = response.json()
    if 'results' in data and len(data['results']) > 0:
        return data['results'][0]['plate'].upper()
    return None

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "🚗 Plaka taranıyor...")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("temp.jpg", "wb") as f: f.write(downloaded_file)
    
    plaka = plakayi_oku("temp.jpg")
    if plaka:
        bot.reply_to(message, f"✅ Tespit: *{plaka}*\nKayıt etmek için plakayı mesaj olarak yaz veya gönder.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Plaka bulunamadı. Lütfen manuel yaz.")

# 4. İŞLEM MERKEZİ (GİRİŞ, ÇIKIŞ, PROMET)
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
        plaka = metin.replace(".EXIT", "").strip()
        if plaka in data["araclar"]:
            giris = datetime.strptime(data["araclar"][plaka]["giris"], "%H:%M")
            simdi = datetime.now(ZAMAN_DILIMI)
            fark = (simdi.hour * 60 + simdi.minute) - (giris.hour * 60 + giris.minute)
            ucret = ucret_hesapla(max(0, fark))
            data["toplam_kazanc"] += ucret
            del data["araclar"][plaka]
            verileri_kaydet(data)
            bot.reply_to(message, f"📤 {plaka} çıkışı yapıldı. Ödeme: {ucret} DENAR")
        else: bot.reply_to(message, "❌ Araç bulunamadı.")
        
    else:
        # Manuel veya otomatik giriş kaydı
        data["araclar"][metin] = {"giris": datetime.now(ZAMAN_DILIMI).strftime("%H:%M")}
        verileri_kaydet(data)
        bot.reply_to(message, f"✅ {metin} giriş yaptı.")

bot.infinity_polling()
