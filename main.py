import telebot
import requests
import json
import math
import os
from datetime import datetime
import pytz

TOKEN = "8925524634:AAEmc6YhLixJqCz3wN87JG2Hu4s6JAHH4Bk"
API_TOKEN = "7b62ff5677db55f09f46dfe58a9e81c36cd18e89"
bot = telebot.TeleBot(TOKEN)
VERI_DOSYASI = "otopark_verileri.json"
ZAMAN_DILIMI = pytz.timezone('Europe/Skopje')

# 1. Fiyatlandırma
def ucret_hesapla(toplam_dakika):
    if toplam_dakika <= 60: return 40
    saat = toplam_dakika // 60
    dakika_kalan = toplam_dakika % 60
    return (saat * 40) + (math.ceil(dakika_kalan / 15) * 10)

# 2. Veri Yönetimi
def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {"araclar": {}, "toplam_kazanc": 0, "banli": []}
    return {"araclar": {}, "toplam_kazanc": 0, "banli": []}

def verileri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

# 3. Fotoğraf İşleme (Otomatik Giriş + Ban Kontrolü)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "🚗 Plaka taranıyor...")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("temp.jpg", "wb") as f: f.write(downloaded_file)
    
    with open("temp.jpg", 'rb') as fp:
        r = requests.post('https://api.platerecognizer.com/v1/plate-reader/',
                          data=dict(regions=['mk']), files=dict(upload=fp),
                          headers={'Authorization': f'Token {API_TOKEN}'})
    
    data = verileri_yukle()
    res = r.json()
    if 'results' in res and len(res['results']) > 0:
        plaka = res['results'][0]['plate'].upper()
        
        if plaka in data.get("banli", []):
            bot.reply_to(message, f"🚫 DİKKAT: *{plaka}* plakalı araç BANLIDIR!", parse_mode="Markdown")
        else:
            data["araclar"][plaka] = {"giris": datetime.now(ZAMAN_DILIMI).strftime("%H:%M")}
            verileri_kaydet(data)
            bot.reply_to(message, f"✅ {plaka} giriş yaptı.")
    else:
        bot.reply_to(message, "❌ Plaka okunmadı, manuel gir.")

# 4. İşlem Merkezi
@bot.message_handler(func=lambda message: True)
def islem(message):
    metin = message.text.upper().strip()
    data = verileri_yukle()
    
    if metin.startswith(".BAN "):
        plaka = metin.replace(".BAN ", "").strip()
        if "banli" not in data: data["banli"] = []
        data["banli"].append(plaka)
        verileri_kaydet(data)
        bot.reply_to(message, f"⛔ {plaka} kara listeye alındı.")
        
    elif metin == ".ARABALAR":
        if not data["araclar"]: bot.reply_to(message, "🅿️ Otopark boş.")
        else: bot.reply_to(message, "\n".join([f"🚗 {p} (Giriş: {v['giris']})" for p, v in data["araclar"].items()]))
            
    elif metin == ".PROMET":
        bot.reply_to(message, f"💰 Toplam Gelir: {data['toplam_kazanc']} DENAR")
        
    elif metin.startswith(".EXIT"):
        plaka = metin.replace(".EXIT", "").replace(" ", "").strip()
        for p in list(data["araclar"].keys()):
            if p.replace(" ", "") == plaka:
                giris_saati = data["araclar"][p]["giris"]
                cikis_saati = datetime.now(ZAMAN_DILIMI).strftime("%H:%M")
                
                g_dt = datetime.strptime(giris_saati, "%H:%M")
                c_dt = datetime.now(ZAMAN_DILIMI)
                fark = (c_dt.hour * 60 + c_dt.minute) - (g_dt.hour * 60 + g_dt.minute)
                ucret = ucret_hesapla(max(0, fark))
                
                fis = f"
http://googleusercontent.com/immersive_entry_chip/0



Her şey tek bir `main.py` içinde birleşti. Artık profesyonel bir otopark sistemin var. GitHub'a pushla ve otoparkı yönetmeye başla, bol kazançlar kardeşim! Başka bir isteğin olursa ben buralardayım.
        
