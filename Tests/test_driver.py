# tests/test_driver.py
# pytest -s -v Tests/test_driver.py
# pytest -v -s --log-cli-level=DEBUG Tests/test_driver.py

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


def test_driver_base():
    """
    Проверка запуска драйвера
    """

    driver = Selenium_driver.driver(
        name="Profile_base",
        proxy="",
        eco=True,
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
        driver.close()

def test_driver_node():
    """
    Проверка запуска драйвера
    """

    driver = Selenium_node_js.driver(
        name="Profile_node_1",
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
        driver.close()