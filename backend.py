from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64 ,sys , os,paramiko

# key = bytes.fromhex("6acbe2c3a12c9fbf8a76cd1185dc874f8def2b8f0a81bf146ae39405a357ef79")
# iv = bytes.fromhex("a96808845430d3e213c059a6c9979f39")


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def app_path(filename):
    return os.path.join(os.getcwd(), filename)


def encrypt_aes(text,key,iv):
    cipher = AES.new(bytes.fromhex(key), AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(text.encode("utf-8"), AES.block_size))
    return base64.b64encode(encrypted).decode("utf-8")



def decrypt_aes(enc_text, key,iv):
    try:
        cipher = AES.new(bytes.fromhex(key), AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(base64.b64decode(enc_text)), AES.block_size)
        return decrypted.decode("utf-8")
    except Exception as e:
        return False
    

def try_decrypt(key,iv):
    file_path = app_path("settings.csv")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content == "":
                return "2"
            reader = decrypt_aes(content, key,iv)
            if reader:
                return reader
            else:
                return "1"
    return "2"

def load_data(DATA,key,iv):
    with open(app_path("Prices.csv"), "r", encoding="utf-8") as f:
        encrypted_data = f.readlines()
        for line in encrypted_data:
            line = line.strip().split(",")
            if line[0] not in DATA["Time"]:
                DATA["Time"].append(line[0])
                decrypted_line = decrypt_aes(line[1], key,iv).split(",")  # ?time
                DATA["Gold"].append(int(decrypted_line[2]))  # ?gold
                DATA["Coin"].append(int(decrypted_line[3]))  # ?coin
                DATA["USD"].append(int(decrypted_line[1]))  # ?usd
                DATA["USDT"].append(int(decrypted_line[0]))  # ?usdt

def download_via_sftp(result):
    try:
        row = result.split(",")
        transport = paramiko.Transport((row[0], int(row[1])))
        transport.connect(username=row[2], password=row[3])
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.get("/home/debian/Prices.csv", app_path("Prices.csv"))
        sftp.close()
        transport.close()
        return True,1
    except Exception as e:
        return False,e


def save_settings(settings,key,iv):
	with open(app_path("settings.csv") ,"w",newline="", encoding="utf-8") as f:
			data = ",".join(settings)
			f.write(encrypt_aes(data,key,iv))
   
def ensure_data_files():
    prices_path = os.path.join(os.getcwd(), "Prices.csv")
    settings_path = os.path.join(os.getcwd(), "settings.csv")

    # Prices.csv
    if not os.path.exists(prices_path):
        with open(prices_path, "w", encoding="utf-8") as f:
            pass  # empty file

    # settings.csv
    if not os.path.exists(settings_path):
        with open(settings_path, "w", encoding="utf-8") as f:
            pass  # empty file

   
# file_path = app_path("settings.csv")
#             row = [
#                 inputs[0].text().strip(),
#                 inputs[1].text().strip(),
#                 inputs[2].text().strip(),
#                 inputs[3].text().strip(),
#             ]

#             with open(file_path, "w", newline="", encoding="utf-8") as f:
#                 data = ",".join(row)
#                 f.write(encrypt_aes(data))



