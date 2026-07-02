import telebot
import os
import json
from datetime import datetime
import pytz
from telebot import apihelper

# Telegram bağlantı ayarı
apihelper.SESSION_TIME_TO_LIVE = 5 * 60

# Render environment variable'dan token al
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN bulunamadı. Render > Environment kısmına eklemelisin.")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

VERI_DOSYASI = "otopark_verileri.json"
ZAMAN_DILIMI = pytz.timezone("Europe/Skopje")
UCRET = 40  # sabit ücret, istersen sonra süreye göre yaparız


def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)


def simdi_str():
    return datetime.now(ZAMAN_DILIMI).strftime("%d.%m.%Y %H:%M")


@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "🅿️ <b>Otopark Botu aktif!</b>\n\n"
        "Komutlar:\n"
        "• <code>/giris PLAKA</code> → araç girişi\n"
        "• <code>/cikis PLAKA</code> → araç çıkışı\n"
        "• <code>/durum</code> → içerideki araçlar\n\n"
        "Örnek:\n"
        "<code>/giris TE1234AB</code>"
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=['giris'])
def giris(message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Kullanım: <code>/giris PLAKA</code>\nÖrn: <code>/giris TE1234AB</code>")
            return

        plaka = parts[1].strip().upper()
        veriler = verileri_yukle()

        if plaka in veriler:
            giris_saati = veriler[plaka].get("giris", "-")
            bot.reply_to(message, f"⚠️ <b>{plaka}</b> zaten içeride.\nGiriş: {giris_saati}")
            return

        veriler[plaka] = {
            "giris": simdi_str()
        }
        verileri_kaydet(veriler)
        bot.reply_to(message, f"✅ <b>{plaka}</b> giriş yaptı.\n🕒 {veriler[plaka]['giris']}")

    except Exception as e:
        bot.reply_to(message, f"❌ Hata oluştu: {e}")


@bot.message_handler(commands=['cikis'])
def cikis_komut(message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Kullanım: <code>/cikis PLAKA</code>\nÖrn: <code>/cikis TE1234AB</code>")
            return

        plaka = parts[1].strip().upper()
        veriler = verileri_yukle()

        if plaka not in veriler:
            bot.reply_to(message, f"❌ <b>{plaka}</b> içeride görünmüyor.")
            return

        giris_saati = veriler[plaka].get("giris", "-")
        del veriler[plaka]
        verileri_kaydet(veriler)

        bot.reply_to(
            message,
            f"📤 <b>{plaka}</b> çıkış yaptı.\n"
            f"🕒 Giriş: {giris_saati}\n"
            f"💵 Ücret: {UCRET} Denar"
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Hata oluştu: {e}")


@bot.message_handler(commands=['durum'])
def durum(message):
    try:
        veriler = verileri_yukle()

        if not veriler:
            bot.reply_to(message, "🅿️ Otopark şu anda boş.")
            return

        satirlar = []
        for plaka, bilgi in veriler.items():
            giris = bilgi.get("giris", "-")
            satirlar.append(f"🚗 <b>{plaka}</b> — {giris}")

        cevap = "🅿️ <b>İçerideki araçlar:</b>\n\n" + "\n".join(satirlar)
        bot.reply_to(message, cevap)

    except Exception as e:
        bot.reply_to(message, f"❌ Hata oluştu: {e}")


@bot.message_handler(func=lambda message: True, content_types=['text'])
def yardimci_mesaj(message):
    bot.reply_to(
        message,
        "Komut kullan:\n"
        "• <code>/giris PLAKA</code>\n"
        "• <code>/cikis PLAKA</code>\n"
        "• <code>/durum</code>"
    )


print("Bot çalışıyor...")
bot.infinity_polling(timeout=30, long_polling_timeout=30)
