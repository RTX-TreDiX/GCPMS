from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64, sys, os, paramiko

client_key = "7acbe2c3a12c9fbf8a76cd1185dc874f8def2b8f0a81bf146ae39405a357ef79"
client_iv = bytes.fromhex("b96808845430d3e213c059a6c9979f39")


def find_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def find_app_path(filename):
    return os.path.join(os.getcwd(), filename)


def encrypt_aes(text, key, iv):
    cipher = AES.new(bytes.fromhex(key), AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(text.encode("utf-8"), AES.block_size))
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_aes(enc_text, key, iv):
    result = ""
    try:
        cipher = AES.new(bytes.fromhex(key), AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(base64.b64decode(enc_text)), AES.block_size)
        result = decrypted.decode("utf-8")
    except Exception as e:
        result = False
    return result


def try_decrypt(key, iv):
    file_path = find_app_path("settings.csv")
    result = ""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content != "":
                reader = decrypt_aes(content, client_key, client_iv)
                if reader:
                    result = download_via_sftp(reader, key, iv)
            else:
                result = (False, 1)
    else:
        result = (False, 1)

    return result


def load_data(DATA, key, iv):
    with open(find_app_path("Prices.csv"), "r", encoding="utf-8") as f:
        encrypted_data = f.readlines()
        for line in encrypted_data:
            line = line.strip().split(",")
            if line[0] not in DATA["Time"]:
                DATA["Time"].append(line[0])
                decrypted_line = decrypt_aes(line[1], key, bytes.fromhex(iv)).split(
                    ","
                )  # ?time
                # print(decrypted_line)
                DATA["Gold"].append(int(decrypted_line[2]))  # ?gold
                DATA["Coin"].append(int(decrypted_line[3]))  # ?coin
                DATA["USD"].append(int(decrypted_line[1]))  # ?usd
                DATA["USDT"].append(int(decrypted_line[0]))  # ?usdt


def load_local_settings():
    settings = []
    file_path = find_app_path("settings.csv")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content != "":
                reader = decrypt_aes(content, client_key, client_iv)
                if reader:
                    settings = reader.split(",")
    return settings


def add_server_key_iv_tosettings(key, iv):
    settings = load_local_settings()
    while len(settings) < 5:
        settings.append("")
    settings[3] = key
    settings[4] = iv
    with open(find_app_path("settings.csv"), "w", newline="", encoding="utf-8") as f:
        f.write(encrypt_aes(",".join(settings), client_key, client_iv))


def download_via_sftp(enter, key, iv):
    result = ""
    try:
        row = enter.split(",")
        transport = paramiko.Transport((row[0], int(row[1])))
        transport.connect(username=row[2], password=row[3])
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.get("/home/debian/Prices.csv", find_app_path("Prices.csv"))
        sftp.close()
        transport.close()
        result = (True, 1)
    except Exception as e:
        result = (False, 2)
    if result[0]:
        try:
            with open(find_app_path("Prices.csv"), "r", encoding="utf-8") as f:
                encrypted_data = f.readlines()
                for line in encrypted_data:
                    line = line.strip().split(",")
                    decrypted_line = decrypt_aes(line[1], key, bytes.fromhex(iv))
                    add_server_key_iv_tosettings(key, iv)
                    result = (True, 1)
                    break
        except Exception as e:
            result = (False, 3)
    return result


def save_settings(settings, key, iv):
    with open(find_app_path("settings.csv"), "w", newline="", encoding="utf-8") as f:
        data = ",".join(settings)
        f.write(encrypt_aes(data, key, iv))


def ensure_data_files():
    prices_path = os.path.join(os.getcwd(), "Prices.csv")
    settings_path = os.path.join(os.getcwd(), "settings.csv")

    # Prices.csv
    if not os.path.exists(prices_path):
        with open(prices_path, "w", encoding="utf-8") as f:
            pass

    # settings.csv
    if not os.path.exists(settings_path):
        with open(settings_path, "w", encoding="utf-8") as f:
            pass
