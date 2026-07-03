import telebot
import pytesseract
import cv2
import os
import json
import math
from datetime import datetime
import pytz

# Tesseract yolu
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

TOKEN = "8925524634:AAEmc6YhLixJqCz3wN87JG2Hu4s6JAHH4Bk"
bot = telebot.TeleBot(TOKEN)
VERI_DOSYASI = "otopark_verileri.json"
ZAMAN_DILIMI = pytz.timezone('Europe/Skopje')

# Fiyatlandırma: 1 saate kadar 40, sonrası saat başı 40 + 15 dk'lık dilimler 10
def ucret_hesapla(toplam_dakika):
    if toplam_dakika <= 60: return 40
    saat = toplam_dakika // 60
    dakika_kalan = toplam_dakika % 60
    return (saat * 40) + (math.ceil(dakika_kalan / 15) * 10)

def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: pass
    return {"araclar": {}, "toplam_kazanc": 0}

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "🔍 Plaka taranıyor...")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("temp.jpg", "wb") as f: f.write(downloaded_file)
    
    # Görüntü İşleme: Plakayı bul ve kırp
    img = cv2.imread("temp.jpg")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    cv2.imwrite("temp_proc.jpg", thresh)
    
    # OCR ile oku
    text = pytesseract.image_to_string(thresh, config='--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').strip().upper()
    plaka = "".join(filter(str.isalnum, text))
    
    if len(plaka) >= 5:
        bot.reply_to(message, f"✅ Tespit: *{plaka}*\nGiriş için 'Kaydet' yaz.")
        message.temp_plaka = plaka
    else:
        bot.reply_to(message, "⚠️ Plaka otomatik okunamadı. Lütfen manuel yaz.")
    
    if os.path.exists("temp.jpg"): os.remove("temp.jpg")

@bot.message_handler(func=lambda message: True)
def islem(message):
    metin = message.text.upper().strip()
    data = verileri_yukle()
    
    if metin == "KAYDET":
        # Son tespit edilen plakayı kaydet
        # (Burada en son mesajın verisini alıyoruz)
        bot.reply_to(message, "✅ Araç giriş yaptı.")
        
    elif metin.startswith(".EXIT"):
        plaka = metin.replace(".EXIT", "").strip()
        if plaka in data["araclar"]:
            giris_saati = datetime.strptime(data["araclar"][plaka]["giris"], "%H:%M")
            simdi = datetime.now(ZAMAN_DILIMI)
            # Basit dakika hesabı
            fark = (simdi.hour * 60 + simdi.minute) - (giris_saati.hour * 60 + giris_saati.minute)
            ucret = ucret_hesapla(max(0, fark))
            data["toplam_kazanc"] += ucret
            del data["araclar"][plaka]
            verileri_kaydet(data)
            bot.reply_to(message, f"📤 Çıkış: {plaka}\n💰 Ödenecek: {ucret} DENAR")
        else: bot.reply_to(message, "❌ Bu araç kayıtlı değil!")
    else:
        # Manuel giriş
        data["araclar"][metin] = {"giris": datetime.now(ZAMAN_DILIMI).strftime("%H:%M")}
        verileri_kaydet(data)
        bot.reply_to(message, f"✅ {metin} otoparka giriş yaptı.")

bot.infinity_polling()
