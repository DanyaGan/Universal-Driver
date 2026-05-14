from selenium import webdriver #type: ignore
from selenium.webdriver.chrome.options import Options #type: ignore
import time, os
import shutil

from logging import getLogger
logger = getLogger(__name__)

from .tool import *

class driver:
    def __init__(self, name, proxy, eco, headless):
        self.driver: object
        self.chrome_options: object

        self.profile_name: str = name 
        self.proxy:str = proxy

        self.eco: bool = eco
        self.headless: bool = headless

        self.path_data = f'{os.path.dirname(os.path.abspath(__file__))}'
        self.path_driver = f'{self.path_data}/driver.js'
        self.path_profiles = f'{self.path_data}/profiles'
    
    def start(self, ):
        ensure_directory_exists(f'{self.path_profiles}/{self.profile_name}')
        ensure_directory_exists(f'{self.path_profiles}/{self.profile_name}_info')

        chrome_options = Options()
        chrome_options.add_argument(f"--user-data-dir={self.path_profiles}/{self.profile_name}")
        chrome_options.add_argument(f"--profile-directory={self.profile_name}")

        # 3. Скрытый режим (headless)
        if self.headless:
            chrome_options.add_argument("--headless=new")  # для новых версий Chrome

        # Дополнительно (часто нужно для headless)
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=chrome_options)
    
    def close(self):
        logger.debug('Завершени сеанса браузера')
        if self.driver:
            logger.debug('Завершения процеса драйвера')
            self.driver.quit()

        if self.eco:
            logger.debug('Удаления профиля браузера')
            shutil.rmtree(f'{self.path_data }\\profiles\\{self.profile_name}')


if __name__ == '__main__':
    driver().start('test')
    time.sleep(1000)