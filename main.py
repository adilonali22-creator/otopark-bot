import telebot
import os
import json
import math
from datetime import datetime
import pytz
from PIL import Image, ImageDraw

# YENİ TOKEN'INI BURAYA GÜNCELLEDİM
TOKEN = "8925524634:AAHx26QKCGifYHLR_VLON6IAqTeeuJmauQg"

# Telegram botunu başlat ve eski bağlantıları temizle (Conflict hatasını engeller)
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook() 

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

def ucret_hesapla(toplam_dakika):
    if toplam_dakika <= 60:
        return 40
    saat = toplam_dakika // 60
    dakika_kalan = toplam_dakika % 60
    ucret = saat * 40
    if dakika_kalan > 0:
        ekstra_dilim = math.ceil(dakika_kalan / 15)
        ucret += (ekstra_dilim * 10)
    return ucret

def plaka_resmi_olustur_ve_kaydet(plaka, saat):
    # 400x200 boyutunda beyaz bir resim oluştur
    img = Image.new('RGB', (400, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Bilgileri resmin üzerine yaz
    d.text((50, 60), f"PLAKA: {plaka}", fill=(0, 0, 0))
    d.text((50, 100), f"GIRIS: {saat}", fill=(0, 0, 0))
    
    dosya_adi = f"{plaka}.png"
    img.save(dosya_adi)
    return dosya_adi

@bot.message_handler(func=lambda message: True)
def islem(message):
    if message.text.startswith('/'): return
    
    metin = message.text.lower().strip()
    veriler = verileri_yukle()

    # ÇIKIŞ İŞLEMİ
    if metin.startswith('.exit'):
        plaka = metin.replace(".exit", "").strip().upper()
        if plaka in veriler:
            giris_saati_str = veriler[plaka]["giris"]
            giris_dt = datetime.strptime(giris_saati_str, "%H:%M")
            simdi = datetime.now(ZAMAN_DILIMI)
            
            # Gün geçişlerini de doğru hesaplamak için tarih kontrolü (opsiyonel basit hali)
            giris_tam = simdi.replace(hour=giris_dt.hour, minute=giris_dt.minute, second=0, microsecond=0)
            delta = simdi - giris_tam
            toplam_dakika = int(delta.total_seconds() / 60)
            if toplam_dakika < 0: toplam_dakika = 0
            
            ucret = ucret_hesapla(toplam_dakika)
            
            cevap = (
                f"📤 *{plaka} ÇIKIŞ YAPTI*\n\n"
                f"🕒 GİRİŞ: *{giris_saati_str}*\n"
                f"⏳ SÜRE: *{toplam_dakika} dk*\n"
                f"💰 TUTAR: *{ucret} DENAR*"
            )
            bot.reply_to(message, cevap, parse_mode="Markdown")
            
            del veriler[plaka]
            verileri_kaydet(veriler)
        else:
            bot.reply_to(message, "❌ Plaka kayıtlı değil.")
    
    # GİRİŞ İŞLEMİ
    else:
        plaka = metin.upper()
        giris_vakti = datetime.now(ZAMAN_DILIMI).strftime("%H:%M")
        veriler[plaka] = {"giris": giris_vakti}
        verileri_kaydet(veriler)
        
        # Resim oluştur
        plaka_resmi_olustur_ve_kaydet(plaka, giris_vakti)
        
        bot.reply_to(message, f"✅ *{plaka}* giriş yaptı.\n🕒 Giriş: *{giris_vakti}*\n📸 Bilet resmi kaydedildi.", parse_mode="Markdown")

print("Bot aktif...")
bot.polling(none_stop=True) # Render için en kararlı çalışma modu
