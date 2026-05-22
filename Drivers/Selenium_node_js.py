from selenium import webdriver #type: ignore
from selenium.webdriver.chrome.options import Options #type: ignore
from selenium.webdriver.chrome.service import Service #type: ignore
import subprocess
import json
import os
import sqlite3
import time
import shutil

from pathlib import Path

from logging import getLogger
logger = getLogger(__name__)

from .tool import *

class driver:
    def __init__(self, name:str, proxy:str, eco:bool, headless:bool):
        self.driver: object
        self.chrome_options: object

        self.profile_name: str = name 
        self.proxy:str = proxy if proxy else "None"
 
        self.eco: bool = eco
        self.headless: bool = headless

        self.path_data = f'{os.path.dirname(os.path.abspath(__file__))}'
        self.path_driver = f'{self.path_data}\\driver.js'
        self.path_profiles = f'{self.path_data}\\profiles'

        self.node_process: object

    def start(self):

        logger.info('Запуск браузерного профиля')

        try:
            download_and_extract_chrome_driver(self.path_data)

            port = self.create_profile()

            if not isinstance(port, int):
                raise RuntimeError(f'Некорректный порт: {port}')

            logger.info('Подключение к Chrome DevTools: %s', port)

            options = Options()

            options.add_experimental_option(
                "debuggerAddress",
                f"127.0.0.1:{port}"
            )

            options.add_argument("--window-size=1920,1080")

            if self.headless:
                logger.warning(
                    'Headless может не работать '
                    'при debuggerAddress attach'
                )

            driver_path = Path(self.path_data) / 'chromedriver.exe'

            service = Service(str(driver_path))

            self.driver = webdriver.Chrome(
                service=service,
                options=options
            )

            process = getattr(self.driver.service, 'process', None)

            if process:
                logger.info('ChromeDriver PID: %s', process.pid)

            return self.driver

        except Exception as e:

            logger.exception('Ошибка запуска браузера: %s', e)

            self.close()

            return False
    
    def close(self):
        logger.debug('Завершени сеанса браузера')
        self.driver.quit()

        logger.debug('Завершения процеса драйвера')
        self.node_process.terminate()
   
        if self.eco:
            while True:
                try:
                    shutil.rmtree(f'{self.path_data}\\profiles\\{self.profile_name}')

                    logger.debug('Профиль удалён')
                    break

                except PermissionError:
                    logger.debug('Папка ещё используется...')
                    time.sleep(3)

                except FileNotFoundError:
                    break



    def create_profile(self) -> int | bool:
        """Создание и запуск профиля браузера"""

        # Создание директорий
        Path(self.path_profiles).mkdir(parents=True, exist_ok=True)
        Path(f'{self.path_profiles}\\{self.profile_name}_info').mkdir(parents=True, exist_ok=True)

        cmd = [
            'node',
            self.path_driver,
            self.path_profiles,
            str(self.profile_name),
            str(self.proxy)
        ]

        logger.debug('Запуск Node.js: %s', cmd)

        try:
            self.node_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,           # сразу str вместо bytes
                encoding='utf-8',
                bufsize=1
            )

        except Exception as e:
            logger.exception('Ошибка запуска Node.js: %s', e)
            return False

        logger.debug('Node.js процесс запущен')

        timeout = 30
        start_time = time.time()

        while time.time() - start_time < timeout:

            # Проверка что процесс не умер
            if self.node_process.poll() is not None:
                stderr = self.node_process.stderr.read()

                logger.error(
                    'Node.js процесс завершился\n'
                    'Код: %s\n'
                    'stderr: %s',
                    self.node_process.returncode,
                    stderr
                )

                return False

            line = self.node_process.stdout.readline()

            if not line:
                time.sleep(0.1)
                continue

            logger.debug('Ответ Node.js: %s', line.strip())

            try:
                response = json.loads(line)

            except json.JSONDecodeError:
                logger.warning('Некорректный JSON: %s', line)
                continue

            # Успешное создание
            if response.get('status'):
                logger.debug('Профиль успешно создан')

            # Получен порт
            port = response.get('port')

            if port:
                logger.debug('Получен порт: %s', port)
                return port

        logger.error('Таймаут ожидания ответа Node.js')

        self.node_process.kill()

        return False
