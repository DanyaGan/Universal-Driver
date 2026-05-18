import os

import platform
import requests #type: ignore
import zipfile
import io
import sqlite3
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM #type: ignore

from logging import getLogger
logger = getLogger(__name__)

def ensure_directory_exists(directory_path):
        # Checking if the directory exists
    if not os.path.exists(directory_path):
        # Create a directory if it doesn't exist
        os.makedirs(directory_path)

def get_User_Agent(path_profiles, profile_name):
    try:
        with open(f"{path_profiles}/{profile_name}_info", "r", encoding="utf-8") as f:
            data = json.load(f)
            user_agent = data.get("ua")
    except Exception as e:
        logger.error(f"Ошибка чтения fingerprint.json: {e}")
        return
    return user_agent

def get_cookies(self, consider=(), ignore=()): 
    logger.debug("Получения кукков")

    def get_chrome_master_key():
        logger.debug("Начало получения Chrome master key")

        try:
            logger.debug("Формирование пути к файлу Local State")
            local_state_path = os.path.join(os.environ.get('LOCALAPPDATA', ''),r"Google\Chrome\User Data\Local State")

            logger.debug("Путь к Local State: %s", local_state_path)

            if not os.path.exists(local_state_path):
                logger.error("Файл Local State не найден")
                return None

            logger.debug("Чтение файла Local State")
            with open(local_state_path, 'r', encoding='utf-8') as f: local_state = json.load(f)

            logger.debug("Получение зашифрованного master key из Local State")
            encrypted_key_b64 = local_state.get('os_crypt', {}).get('encrypted_key')

            if not encrypted_key_b64:
                logger.error("Поле os_crypt.encrypted_key отсутствует")
                return None

            logger.debug("Base64-декодирование master key")
            encrypted_key = base64.b64decode(encrypted_key_b64)

            logger.debug("Удаление префикса DPAPI")
            encrypted_key = encrypted_key[5:]  # remove "DPAPI"

            logger.debug("Расшифровка master key через Windows DPAPI")
            master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

            logger.info("Chrome master key успешно получен")

            return master_key

        except Exception as e:
            logger.exception("Ошибка при получении Chrome master key: %s", e)
            return None

    def decrypt_chrome_cookie(encrypted_value: bytes, master_key: bytes) -> str:
        logger.debug("Начало расшифровки Chrome cookie")

        try:
            if not encrypted_value:
                logger.debug("Пустое значение encrypted_value")
                return ''

            # Новый формат Chrome (AES-GCM, v10)
            if encrypted_value.startswith(b'v10'):
                logger.debug("Обнаружен формат cookie: AES-GCM (v10)")

                iv = encrypted_value[3:15]
                payload = encrypted_value[15:]

                logger.debug("Инициализация AES-GCM")
                cipher = AESGCM(master_key)

                logger.debug("Расшифровка cookie через AES-GCM")
                decrypted = cipher.decrypt(iv, payload, None)

                logger.debug("Cookie успешно расшифрована (AES-GCM)")
                return decrypted.decode('utf-8', errors='ignore')

            # Старый формат (DPAPI)
            else:
                logger.debug("Обнаружен формат cookie: DPAPI (старый)")

                decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1]

                logger.debug("Cookie успешно расшифрована (DPAPI)")
                return decrypted.decode('utf-8', errors='ignore')

        except Exception as e:
            logger.debug("Ошибка расшифровки cookie: %s", e)
            return ''
    
    if platform == "Windows":
        import win32crypt #type: ignore

        
        logger.info("Чтение cookies Chrome (Windows)")

        cookies_db = os.path.join(self.path_profiles, self.profile_name, "Default", "Network", "Cookies")

        logger.debug("Путь к базе cookies: %s", cookies_db)

        logger.debug("Получение master key Chrome")
        master_key = get_chrome_master_key()

        cookies = []

        logger.debug("Подключение к SQLite базе cookies")
        conn = sqlite3.connect(cookies_db)
        conn.text_factory = bytes
        cursor = conn.cursor()

        logger.debug("Выполнение SQL-запроса на получение cookies")
        cursor.execute("SELECT host_key, name, value, path, expires_utc, is_secure, is_httponly, encrypted_value FROM cookies")

        rows = cursor.fetchall()
        logger.debug("Получено cookies из БД: %d", len(rows))

        for idx, row in enumerate(rows, start=1):
            (host_key, name, value, path, expires_utc,is_secure, is_httponly, encrypted_value) = row

            host_key = host_key.decode("utf-8", errors="ignore")
            name = name.decode("utf-8", errors="ignore")
            path = path.decode("utf-8", errors="ignore")

            # Фильтрация
            if consider and host_key not in consider:
                logger.debug("Cookie #%d пропущена (не в consider): %s", idx, host_key)
                continue

            if host_key in ignore:
                logger.debug("Cookie #%d пропущена (в ignore): %s", idx, host_key)
                continue

            # Получение значения cookie
            if value:
                cookie_value = value.decode("utf-8", errors="ignore")
                logger.debug("Cookie #%d получена из value", idx)
            else:
                cookie_value = decrypt_chrome_cookie(encrypted_value, master_key)
                logger.debug("Cookie #%d расшифрована через encrypted_value", idx)

            cookies.append({"domain": host_key, "name": name, "value": cookie_value, "path": path, "expires": expires_utc, "secure": bool(is_secure), "httponly": bool(is_httponly)})

        logger.debug("Закрытие соединения с SQLite")
        conn.close()

        path_file = f"{self.path_profiles}/{self.profile_name}_info"
        if path_file:
            logger.debug("Подготовка директории для сохранения cookies")
            os.makedirs(path_file, exist_ok=True)

            output = os.path.join(path_file, f"cookies_{self.profile_name}.json")
            logger.debug("Путь выходного файла: %s", output)
            with open(output, "w", encoding="utf-8") as f: json.dump(cookies, f, ensure_ascii=False, indent=2)

        return cookies

def download_and_extract_chrome_driver(path_data) -> bool:
    logger.info('Запущена функция скачивания драйвера')
    file_driver = 'chromedriver.exe'
    filename_in_archive = 'chromedriver-win64/chromedriver.exe'

    # Path to the extracted driver file and the new destination
    extracted_file_path = os.path.join(path_data, filename_in_archive)
    new_file_path = os.path.join(path_data, file_driver)

    logger.debug('Проверка на наличия драйвера')
    if os.path.exists(f'{path_data}\\{file_driver}'):
        logger.info('Драйвер есть, завершении функции')
        return True

    try:
        logger.debug('Скачивание архива драйвера') 
        response = requests.get('https://storage.googleapis.com/chrome-for-testing-public/127.0.6483.0/win64/chromedriver-win64.zip')
        response.raise_for_status()  # Check for successful request
        logger.debug('Архив драйвера загружен') 
    except requests.exceptions.RequestException as e:
        logger.error('Ошибка скачивания драйвера')
        return False

    try:
        logger.debug('Загрузка архива в ОЗУ')
        zip_buffer = io.BytesIO(response.content)
        logger.debug("Архив Загружен в ОЗУ")

        logger.debug('Распаковка архива')
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            zip_ref.extract(filename_in_archive, path_data)
        logger.debug('Архив Распакован')
    except (zipfile.BadZipFile, KeyError) as e:
        logger.error('Ошибка распаковки архива')
        return False

    try:
        logger.debug('Переменования файла и перемещения')
        os.rename(extracted_file_path, new_file_path)
        logger.debug("Файл переменован и перемещен")
    except FileNotFoundError:
        logger.error('Ошибка перемещения и переменования файла')
        return False
    
    logger.info('Драйвер установлен')
    return True

def set_cookies(self, name_profile: str, cookies: list):
    logger.debug('Запущена функция загрзуки куков в профиль')

    # Define paths for cookie database and JSON file
    db_cookies_path = f'{self.path_data}\\profiles\\{name_profile}\\Default\\Network\\Cookies'
    cookies_path = f'{self.path_data}\\profiles\\{name_profile}_info\\cookies_{name_profile}.json'
    
    logger.debug('Проверка на наличия файла куков')
    if not os.path.exists(cookies_path): 
        logger.debug('Файла куков нету, заверщения функции')
        return False
    
    logger.debug('Получения куков из файла')
    with open(cookies_path, 'r', encoding="utf-8") as f:
        cookies = eval(f.read())
    
    logger.debug('Подключеня к базе данных профиля браузера')
    conn = sqlite3.connect(db_cookies_path)
    c = conn.cursor()
    
    logger.debug('Удаления лишних куков з профиля браузера')
    try:
        c.execute("DELETE FROM cookies")
        conn.commit()
    except: 
        pass

    logger.debug('Загрузка куков')
    for cookie in cookies:
        try:
            c.execute("""
                INSERT INTO cookies (
                    host_key, name, path, expires_utc, creation_utc, top_frame_site_key, last_access_utc, 
                    is_secure, is_httponly, has_expires, is_persistent, priority, samesite, source_scheme, 
                    source_port, last_update_utc, encrypted_value, value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cookie['domain'],     # host_key
                cookie['name'],       # name
                cookie['path'],       # path
                cookie['expires'],    # expires_utc
                13359226438123929,    # creation_utc (placeholder value)
                '',                   # top_frame_site_key
                13359226438123929,    # last_access_utc (placeholder value)
                cookie['secure'],     # is_secure
                cookie['httponly'],   # is_httponly
                1,                    # has_expires
                1,                    # is_persistent
                1,                    # priority
                0,                    # samesite
                2,                    # source_scheme
                443,                  # source_port
                13359226438123929,    # last_update_utc (placeholder value)
                '',                   # encrypted_value
                cookie['value']       # value
            ))
            conn.commit()
        except Exception as e:
            # Handle any exceptions that occur during insertion
            return False
    
    logger.debug('Отлкючения от базы данных')
    conn.close()

    return True