from Drivers import Selenium_driver, Selenium_node_js
import logging
logging.basicConfig(level=logging.DEBUG)

# Отключаем логи Selenium и urllib3, оставляем только критические ошибки
logging.getLogger('selenium').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

a = Selenium_driver.driver(
    name="Profile_1",
    proxy="",
    eco=False,
    headless=False)
a.start()