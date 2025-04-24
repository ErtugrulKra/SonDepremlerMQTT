#!/usr/bin/python3 
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import paho.mqtt.client as mqtt
import os

def fetch_recent_significant_earthquakes(min_magnitude=3.5, retry_count=5, wait_seconds=5):
    url = "https://deprem.afad.gov.tr/last-earthquakes.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    for attempt in range(retry_count):
        response = requests.get("https://deprem.afad.gov.tr/home-page", headers=headers)
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            print(f"[{attempt+1}] Hata: Sayfa alınamadı ({response.status_code})")
            time.sleep(wait_seconds)
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="content-table")
        if not table or not table.tbody:
            print(f"[{attempt+1}] Hata: Tablo bulunamadı.")
            time.sleep(wait_seconds)
            continue

        rows = table.tbody.find_all("tr")
        data = []
        valid_dates = []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 7:
                record = [cell.get_text(strip=True) for cell in cells[:7]]
                try:
                    quake_date = datetime.strptime(record[0], "%Y-%m-%d %H:%M:%S").date()
                    valid_dates.append(quake_date)
                    data.append(record)
                except Exception as e:
                    continue

        if any(d in [today, yesterday] for d in valid_dates):
            df = pd.DataFrame(data, columns=["Tarih", "Enlem", "Boylam", "Derinlik", "Tip", "Büyüklük", "Yer"])
            df["Büyüklük"] = pd.to_numeric(df["Büyüklük"], errors="coerce")
            df_filtered = df[df["Büyüklük"] >= min_magnitude].reset_index(drop=True)
            print(f"[{attempt+1}] Güncel veriler alındı.")
            return df_filtered

        print(f"[{attempt+1}] Güncel veri yok, {wait_seconds} sn sonra tekrar denenecek...")
        time.sleep(wait_seconds)

    print("Uyarı: Güncel veriler alınamadı.")
    return pd.DataFrame()  # Boş DataFrame döner



def push_to_mqtt(df, broker=None, port=None, topic="home/earthquake"):
    broker = broker or os.getenv("MQTT_BROKER", "localhost")
    port = int(port or os.getenv("MQTT_PORT", 1883))
    client = mqtt.Client()
    try:
        client.connect(broker, port, 60)
        client.loop_start()

        for _, row in df.iterrows():
            map_link = f"https://www.google.com/maps?q={row['Enlem']},{row['Boylam']}"
            message = {
                "tarih": row["Tarih"],
                "enlem": row["Enlem"],
                "boylam": row["Boylam"],
                "derinlik": row["Derinlik"],
                "tip": row["Tip"],
                "buyukluk": row["Büyüklük"],
                "yer": row["Yer"],
                "harita": map_link
            }
            client.publish(topic, json.dumps(message))
            print(f"MQTT Yayınlandı: {message}")

        client.loop_stop()
        client.disconnect()
        print("Tüm veriler MQTT ile gönderildi.")

    except Exception as e:
        print(f"MQTT Bağlantı Hatası: {e}")

def main_loop():
    while True:
        print("Veri kontrolü başlatılıyor...")
        df = fetch_recent_significant_earthquakes()
        if not df.empty:
            print("Uygun veriler bulundu, MQTT'ye gönderiliyor...")
            push_to_mqtt(df)
        else:
            print("Uygun tarihli veri bulunamadı.")
        print("10 dakika bekleniyor...\n")
        time.sleep(30)  # 30 saniye

if __name__ == "__main__":
    main_loop()