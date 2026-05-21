from selenium import webdriver #type: ignore
from selenium.webdriver.chrome.options import Options #type: ignore
from selenium.webdriver.chrome.service import Service #type: ignore
import subprocess
import json
import os
import sqlite3
import time
import shutil

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

        self.port: int        
        self.node_process: object

    def start(self, ) -> bool:
        logger.debug('Открытия профиля')

        logger.debug('Проверки наличия драйвера')
        download_and_extract_chrome_driver(self.path_data)

        self.create_profile()

        logger.debug(f'Port:{self.port}')
        if self.port:
            logger.debug('Настройка к подключению браузеру')
            self.chrome_options = Options()
            self.chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.port}")
            self.chrome_options.add_argument("--window-size=1920,1080")
            self.chrome_options.add_argument("--start-maximized")
            
            if self.headless:
                 self.chrome_options.add_argument("--headless=new")  # для новых версий Chrome

            logger.debug('Подключения к браузеру')
            self.driver = webdriver.Chrome(options=self.chrome_options, service=Service(f'{self.path_data}\\chromedriver.exe'))

            pid = self.driver.service.process.pid
            logger.debug(f"Pid prossec: {pid}")
            return self.driver
        else:
            logger.error('Порт не коректный для подключения')
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

    def create_profile(self, ) -> bool:
        '''Функция запуска и создания профиля браузера'''

        # Ensure the existence of necessary directories
        ensure_directory_exists(self.path_profiles)
        ensure_directory_exists(f'{self.path_profiles}\\{self.profile_name}_info')
        
        logger.debug('Проверка параметра на эконом памяти')
        if not self.proxy:
            self
        if self.eco:
            logger.debug('Эконом памяти включена')
            
            logger.debug(f'Запуск файла node.js| name:{self.profile_name}, eco_mode:{self.eco}, proxy:{self.proxy}')
            self.node_process = subprocess.Popen(['node', self.path_driver, self.path_profiles, str(self.profile_name), str(self.proxy)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.debug('Файл node.js запущен')

            logger.debug('Запуск цыкла просмотра ответа файла node.js')
            for _ in range(100):
                logger.debug('Получения ответа')
                output = self.node_process.stdout.readline()
                logger.debug('Получен ответ %s', output)

                try:
                    r = json.loads(output.decode('utf-8'))
                    logger.debug('Получен ответ драйвера %s', r)
                    break
                except Exception:
                    time.sleep(1)
            else:
                logger.error('Ошибка создания профиля')
            
            self.port = r['port']
            return True

        else:
            logger.debug('Эконом памяти выключен')

            logger.debug(f'Запуск драйвера {self.path_driver, self.path_profiles, self.profile_name, str(self.proxy)}')
            self.node_process = subprocess.Popen(['node', self.path_driver, self.path_profiles, str(self.profile_name), str(self.proxy)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.debug('Файл node.js запущен')

        logger.debug('Запуск цыкла просмотра ответа файла node.js')
        for _ in range(100):
            logger.debug('Получения ответа драйвера')
            output = self.node_process.stdout.readline()
            logger.debug('Получен ответ %s', output)

            try:
                r = json.loads(output.decode('utf-8'))
                logger.debug('Получен ответ драйвера %s', r)

                logger.debug('Проверка ответа')
                if 'status' in r.keys():
                    logger.debug('Ответ драйвера о том что профиль создан')
                    return self.create_profile(self.profile_name, self.proxy, self.eco)
                break
            except Exception:
                time.sleep(1)
        else:
            logger.error('Ошибка создания или запуска профиля')
            return False
        
        self.port = r['port']
        return True
