#!/usr/bin/env python3
"""
fetch_financial_reports.py — Загрузка финансовых отчётов с e-disclosure.ru
"""

import time
from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def fetch_reports_page(company_id: str):
    """Загружает страницу с финансовыми отчётами."""

    url = f"https://www.e-disclosure.ru/portal/files.aspx?id={company_id}&type=3"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='ru-RU',
        )

        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        page = context.new_page()

        try:
            logger.info(f"Загрузка отчётов: {url}")
            page.goto(url, wait_until='domcontentloaded', timeout=60000)

            logger.info("Ожидание 10 секунд...")
            time.sleep(10)

            # Ищем ссылки на отчёты за 2023-2024
            logger.info("\nПоиск отчётов за 2023-2024...")

            # Получаем все ссылки
            links = page.query_selector_all('a')

            reports_2023_2024 = []
            for link in links:
                text = link.inner_text().strip()
                href = link.get_attribute('href')

                if href and ('2023' in text or '2024' in text):
                    if any(keyword in text.lower() for keyword in ['баланс', 'отчёт', 'форма']):
                        reports_2023_2024.append({
                            'text': text,
                            'url': href if href.startswith('http') else f"https://www.e-disclosure.ru{href}"
                        })

            logger.info(f"\nНайдено отчётов: {len(reports_2023_2024)}")

            for i, report in enumerate(reports_2023_2024[:10], 1):
                logger.info(f"{i}. {report['text']}")
                logger.info(f"   {report['url']}\n")

            # Сохраняем HTML
            html = page.content()
            with open('reports_page.html', 'w', encoding='utf-8') as f:
                f.write(html)

            logger.info("HTML сохранён в reports_page.html")

            return reports_2023_2024

        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return []
        finally:
            browser.close()


if __name__ == "__main__":
    # ГТЛК
    company_id = "36276"
    reports = fetch_reports_page(company_id)

    if reports:
        print(f"\n[OK] Найдено {len(reports)} отчётов")
        print("\nПроверьте reports_page.html для детального анализа")
    else:
        print("\n[ERROR] Отчёты не найдены")
