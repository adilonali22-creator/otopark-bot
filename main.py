import telebot
import os
import json
from datetime import datetime
import pytz

TOKEN = "8629632358:AAGRpPRIy083KuEIXDft42D3rKLFPJTSI44"

# PythonAnywhere için özel bağlantı ayarı
from telebot import apihelper
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
        if '/start' in message.text:
            bot.reply_to(message, "🅿️ Sistem Hazır! /giris PLAKA yazarak araç kaydet.")
        elif '/giris' in message.text:
            plaka = message.text.replace("/giris", "").strip().upper()
            if not plaka:
                bot.reply_to(message, "❌ Plaka yazmalısın. Örn: /giris TE1234AB")
                return
            veriler = verileri_yukle()
            veriler[plaka] = {"giris": datetime.now(ZAMAN_DILIMI).strftime("%H:%M")}
            verileri_kaydet(veriler)
            bot.reply_to(message, f"✅ {plaka} giriş yaptı.")
        elif '/durum' in message.text:
            veriler = verileri_yukle()
            liste = "\n".join([f"🚗 {p}" for p in veriler.keys()])
            bot.reply_to(message, f"🅿️ İçeridekiler:\n{liste if liste else 'Boş'}")
    except Exception as e:
        bot.reply_to(message, "Bir hata oluştu ama sistem ayakta.")

@bot.message_handler(content_types=['text'])
def cikis(message):
    plaka = message.text.upper().strip()
    veriler = verileri_yukle()
    if plaka in veriler:
        del veriler[plaka]
        verileri_kaydet(veriler)
        bot.reply_to(message, f"📤 {plaka} çıkış yaptı. (40 Denar)")
    else:
        bot.reply_to(message, "❌ Plaka bulunamadı.")

print("Bot çalışıyor, Telegram'a mesaj at!")
bot.polling(none_stop=True)
