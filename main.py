import telebot
import os
import json
from datetime import datetime
import pytz
from telebot import apihelper

# Token'ı doğrudan buraya yapıştırdık, Render ayarlarıyla uğraşmana gerek kalmadı.
# EĞER HATA ALIRSAN, @BotFather'dan YENİ BİR TOKEN ALIP TIRNAK İÇİNE YAZ.
TOKEN = "8956351837:AAHKLSz02NxLn0bDU4Sz7hq0tpg3k7zjB24"

apihelper.SESSION_TIME_TO_LIVE = 5 * 60

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

@bot.message_handler(commands=['start', 'giris', 'durum'])
def komutlar(message):
    try:
        if message.text.startswith('/start'):
            bot.reply_to(message, "🅿️ Sistem Hazır! /giris PLAKA yazarak araç kaydet.")
        elif message.text.startswith('/giris'):
            plaka = message.text.replace("/giris", "").strip().upper()
            if not plaka:
                bot.reply_to(message, "❌ Plaka yazmalısın. Örn: /giris TE1234AB")
                return
            veriler = verileri_yukle()
            veriler[plaka] = {"giris": datetime.now(ZAMAN_DILIMI).strftime("%H:%M")}
            verileri_kaydet(veriler)
            bot.reply_to(message, f"✅ {plaka} giriş yaptı.")
        elif message.text.startswith('/durum'):
            veriler = verileri_yukle()
            liste = "\n".join([f"🚗 {p}" for p in veriler.keys()])
            bot.reply_to(message, f"🅿️ İçeridekiler:\n{liste if liste else 'Boş'}")
    except Exception as e:
        print(f"Hata: {e}")

@bot.message_handler(content_types=['text'])
def cikis(message):
    if message.text.startswith('/'): return 
    
    plaka = message.text.upper().strip()
    veriler = verileri_yukle()
    if plaka in veriler:
        del veriler[plaka]
        verileri_kaydet(veriler)
        bot.reply_to(message, f"📤 {plaka} çıkış yaptı. (40 Denar)")
    else:
        bot.reply_to(message, "❌ Plaka bulunamadı.")

print("Bot başlatılıyor...")
bot.polling(none_stop=True)
