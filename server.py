import requests
from bs4 import BeautifulSoup
import time
import datetime
import csv
import os
import base64
import logging
import pytz
import json
import sys
import re
import hashlib
import secrets

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from requests.exceptions import RequestException

# ===================== CONFIG =====================

URL = "https://www.tgju.org/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Cache-Control": "no-cache",
}

FILE_NAME = "Prices.csv"
LOG_FILE = "server_log.log"
CONFIG_FILE = "config.json"
HASH_FILE = "aes_hash.txt"

iran_tz = pytz.timezone("Asia/Tehran")

# ===================== LOGGING =====================

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
)

logger = logging.getLogger("TGJU-Logger")

# ===================== VALIDATION =====================

HEX_KEY_RE = re.compile(r"^[0-9a-f]{64}$")  # 32 bytes
HEX_IV_RE = re.compile(r"^[0-9a-f]{32}$")  # 16 bytes

# ===================== CONFIG BOOTSTRAP =====================


def create_default_config(config_path):
    key_hex = secrets.token_bytes(32).hex()
    iv_hex = secrets.token_bytes(16).hex()

    data = {"key": key_hex, "iv": iv_hex}

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    logger.warning("config.json not found. Default AES key/IV generated.")


def load_and_validate_aes(config_path):
    if not os.path.isfile(config_path):
        logger.warning("Config file missing. Creating default config.json")
        create_default_config(config_path)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        key_hex = cfg.get("key")
        iv_hex = cfg.get("iv")

        if not isinstance(key_hex, str) or not isinstance(iv_hex, str):
            raise ValueError("key and iv must be strings")

        if not HEX_KEY_RE.fullmatch(key_hex):
            raise ValueError("Invalid key format (must be 64 hex lowercase chars)")

        if not HEX_IV_RE.fullmatch(iv_hex):
            raise ValueError("Invalid iv format (must be 32 hex lowercase chars)")

        key = bytes.fromhex(key_hex)
        iv = bytes.fromhex(iv_hex)

        logger.info("AES key and IV validated successfully")
        return key, iv

    except Exception as e:
        logger.critical(f"AES config validation failed: {e}")
        sys.exit(1)


# ===================== CSV RESET ON KEY CHANGE =====================


def get_key_iv_hash(key: bytes, iv: bytes) -> str:
    return hashlib.sha256(key + iv).hexdigest()


def check_reset_csv(key: bytes, iv: bytes):
    current_hash = get_key_iv_hash(key, iv)
    previous_hash = None

    if os.path.isfile(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            previous_hash = f.read().strip()

    if previous_hash != current_hash:
        logger.warning("AES key/IV changed → clearing Prices.csv")

        if os.path.isfile(FILE_NAME):
            os.remove(FILE_NAME)
            logger.info("Prices.csv removed")

        with open(HASH_FILE, "w") as f:
            f.write(current_hash)


# ===================== LOAD AES =====================

key, iv = load_and_validate_aes(CONFIG_FILE)
check_reset_csv(key, iv)

# ===================== PRICE FUNCTIONS =====================


def fetch_price(item_id, retries=3):
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Fetching {item_id} (attempt {attempt})")

            response = requests.get(URL, headers=HEADERS, timeout=10)
            logger.debug(f"{item_id} HTTP {response.status_code}")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            item = soup.find("li", id=item_id)

            if not item:
                raise RuntimeError("Item not found in HTML")

            price_text = item.find("span", class_="info-price").text.strip()
            return int(price_text.replace(",", ""))

        except (RequestException, RuntimeError, ValueError) as e:
            logger.warning(f"{item_id} failed: {e}")
            time.sleep(5)

    raise RuntimeError(f"{item_id} failed after retries")


def get_tether_price():
    return fetch_price("l-crypto-tether-irr")


def get_usd_price():
    return fetch_price("l-price_dollar_rl")


def get_gold_price():
    return fetch_price("l-geram18")


def get_coin_price():
    return fetch_price("l-sekee")


# ===================== ENCRYPT & SAVE =====================


def encrypt_data(data: str) -> str:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(data.encode(), AES.block_size))
    return base64.b64encode(encrypted).decode()


def write_to_csv(file_path, row):
    try:
        with open(file_path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)
            logger.info("Row written to CSV")
    except Exception as e:
        logger.error(f"CSV write error: {e}", exc_info=True)


# ===================== MAIN =====================

if __name__ == "__main__":
    logger.info("TGJU price logger started")

    try:
        while True:
            try:
                now = datetime.datetime.now(iran_tz).strftime("%Y-%m-%d %H:%M:%S")

                tether = get_tether_price()
                usd = get_usd_price()
                gold = get_gold_price()
                coin = get_coin_price()

                raw_data = f"{tether},{usd},{gold},{coin}"
                encrypted = encrypt_data(raw_data)

                write_to_csv(FILE_NAME, [now, encrypted])
                logger.info(f"Logged: {raw_data}")

            except Exception as e:
                logger.error(f"Loop error: {e}", exc_info=True)

            time.sleep(60)

    except KeyboardInterrupt:
        logger.warning("Program stopped by user")
