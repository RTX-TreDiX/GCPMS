import requests
from bs4 import BeautifulSoup
import time
import datetime
import csv
import os
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

key = bytes.fromhex("6acbe2c3a12c9fbf8a76cd1185dc874f8def2b8f0a81bf146ae39405a357ef79")
iv = bytes.fromhex("a96808845430d3e213c059a6c9979f39")

URL = "https://www.tgju.org/"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def fetch_price(item_id):
    response = requests.get(URL, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    item = soup.find("li", id=item_id)

    if item is None:
        raise RuntimeError("Element not found")

    price_text = item.find("span", class_="info-price").text.strip()
    return int(price_text.replace(",", ""))

def get_tether_price():
    return fetch_price("l-crypto-tether-irr")

def get_usd_price():
    return fetch_price("l-price_dollar_rl")

def get_gold_price():
    return fetch_price("l-geram18")

def get_coin_price():
    return fetch_price("l-sekee")

def encrypt_data(data: str) -> str:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(data.encode(), AES.block_size))
    return base64.b64encode(encrypted).decode()



def write_to_csv(file_path, row):
    file_exists = os.path.isfile(file_path)

    with open(file_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["datetime", "data"])
        writer.writerow(row)

if __name__ == "__main__":
    FILE_NAME = "Prices.csv"

    while True:
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            tether = get_tether_price()
            usd = get_usd_price()
            gold = get_gold_price()
            coin = get_coin_price()

            raw_data = f"{tether},{usd},{gold},{coin}"
            encrypted_data = encrypt_data(raw_data)

            write_to_csv(FILE_NAME, [now, encrypted_data])

            print(f"Logged data at {now}")

        except Exception as e:
            print(e)

        time.sleep(1800)
