# tests/test_driver.py
# pytest -s -v tests/test_driver.py

import logging
import pytest
import sys
sys.path.append('../')
from Drivers import Selenium_driver, Selenium_node_js

# Логи
logging.basicConfig(level=logging.DEBUG)

# Отключаем мусорные логи
logging.getLogger("selenium").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)


@pytest.mark.parametrize("driver_class", [
    Selenium_driver.driver,
    Selenium_node_js.driver
])
def test_driver_start(driver_class):
    """
    Проверка запуска драйвера
    """

    driver = driver_class(
        name="Profile_1",
        proxy="",
        eco=False,
        headless=False
    )

    assert driver is not None

    # запуск
    driver.start()

    # если есть selenium driver
    if hasattr(driver, "driver"):
        assert driver.driver is not None

    # закрытие браузера после теста
    if hasattr(driver, "driver") and driver.driver:
        driver.driver.quit()