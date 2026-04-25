#!/usr/bin/env python3
"""
improved_scraper.py — Улучшенный парсер с обходом защиты
"""

import time
from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_with_stealth(url: str, wait_time: int = 10):
    """
    Парсинг с имитацией реального пользователя.

    Args:
        url: URL страницы
        wait_time: Время ожидания загрузки (секунды)
    """
    with sync_playwright() as p:
        # Запускаем браузер с реальными параметрами
        browser = p.chromium.launch(
            headless=False,  # Видимый браузер
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )

        # Создаём контекст с реальным User-Agent
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='ru-RU',
            timezone_id='Europe/Moscow',
        )

        # Скрываем признаки автоматизации
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = context.new_page()

        try:
            logger.info(f"Загрузка: {url}")

            # Переходим на страницу
            page.goto(url, wait_until='domcontentloaded', timeout=60000)

            # Имитируем поведение пользователя
            logger.info(f"Ожидание {wait_time} секунд...")
            time.sleep(wait_time)

            # Прокручиваем страницу
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            time.sleep(2)

            # Получаем HTML
            html = page.content()

            logger.info(f"Получено {len(html)} символов")

            # Сохраняем для анализа
            with open('page_content.html', 'w', encoding='utf-8') as f:
                f.write(html)

            logger.info("HTML сохранён в page_content.html")

            return html

        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return None
        finally:
            browser.close()


def test_edisclosure():
    """Тест парсинга e-disclosure.ru"""

    # Пример: ГТЛК
    company_id = "36276"
    url = f"https://www.e-disclosure.ru/portal/company.aspx?id={company_id}"

    html = scrape_with_stealth(url, wait_time=15)

    if html:
        print("\n✅ Страница загружена успешно")
        print(f"Размер: {len(html)} символов")
        print("\nПроверьте файл page_content.html для анализа структуры")
    else:
        print("\n❌ Не удалось загрузить страницу")


if __name__ == "__main__":
    test_edisclosure()
