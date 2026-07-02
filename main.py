import telebot
import os
import json
import math
import threading
from datetime import datetime
from flask import Flask
import pytz # <-- Buraya ekle

TOKEN = "8925524634:AAEwFF9ZIxchbgiqZCJkQ9HqrSWqCWpvPq8"
bot = telebot.TeleBot(TOKEN)
VERI_DOSYASI = "otopark_verileri.json"
TETOVO_TZ = pytz.timezone('Europe/Skopje') # <-- Buraya ekle
app = Flask(__name__)
PORT = int(os.environ.get("PORT", 8080))

@app.route('/')
def home():
    return "Bot aktif."

def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f: json.dump(veri, f, ensure_ascii=False, indent=4)

def ucret_hesapla(toplam_dakika):
    if toplam_dakika <= 60: return 40
    saat = toplam_dakika // 60
    dakika_kalan = toplam_dakika % 60
    ucret = saat * 40
    if dakika_kalan > 0:
        ekstra_dilim = math.ceil(dakika_kalan / 15)
        ucret += (ekstra_dilim * 10)
    return ucret

@bot.message_handler(func=lambda message: True)
def islem(message):
    if message.text.startswith('/'): return
    metin = message.text.lower().strip()
    veriler = verileri_yukle()
    
    if metin.startswith('.exit'):
        plaka = metin.replace(".exit", "").strip().upper()
        if plaka in veriler:
            giris_saati_str = veriler[plaka]["giris"]
            giris_dt = datetime.strptime(giris_saati_str, "%H:%M")
            # Giriş saatini o günün tarihiyle birleştiriyoruz (Tetovo saatiyle)
            simdi = datetime.now(TETOVO_TZ)
            giris_tam = simdi.replace(hour=giris_dt.hour, minute=giris_dt.minute, second=0, microsecond=0)
            
            delta = simdi - giris_tam
            toplam_dakika = int(delta.total_seconds() / 60)
            if toplam_dakika < 0: toplam_dakika = 0
            
            ucret = ucret_hesapla(toplam_dakika)
            cevap = f"📤 *{plaka} ÇIKIŞ YAPTI*\n\n🕒 GİRİŞ: *{giris_saati_str}*\n⏳ SÜRE: *{toplam_dakika} dk*\n💰 ÖDENECEK: *{ucret} DENAR*"
            bot.reply_to(message, cevap, parse_mode="Markdown")
            del veriler[plaka]
            verileri_kaydet(veriler)
        else: bot.reply_to(message, "❌ Plaka bulunamadı.")
    else:
        plaka = metin.upper()
        # Tetovo saatini burada alıyoruz
        giris_vakti = datetime.now(TETOVO_TZ).strftime("%H:%M")
        veriler[plaka] = {"giris": giris_vakti}
        verileri_kaydet(veriler)
        bot.reply_to(message, f"✅ *{plaka}* giriş yaptı.\n🕒 Giriş: *{giris_vakti}*", parse_mode="Markdown")

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT)).start()
    bot.infinity_polling()
            
