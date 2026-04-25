#!/usr/bin/env python3
"""
edisclosure_scraper.py — Парсер финансовой отчётности с e-disclosure.ru
Использует Playwright для обхода защиты от ботов

Автор: KFI-Project
Дата: 2026-04-25
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from playwright.sync_api import sync_playwright, Page, Browser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class EDisclosureScraper:
    """Парсер финансовых отчётов с e-disclosure.ru через Playwright."""

    BASE_URL = "https://www.e-disclosure.ru"

    # Коды строк РСБУ для парсинга
    BALANCE_CODES = {
        "1100": "non_current_assets",
        "1200": "current_assets",
        "1210": "inventory",
        "1240": "short_term_investments",
        "1250": "cash",
        "1300": "equity",
        "1410": "long_term_debt",
        "1500": "current_liabilities",
        "1510": "short_term_debt",
        "1600": "total_assets",
    }

    OPU_CODES = {
        "2110": "revenue",
        "2200": "operating_profit",
        "2330": "interest_expenses",
        "2400": "net_income",
    }

    ODDS_CODES = {
        "4110": "cfo",
        "4220": "capex",
    }

    def __init__(self, headless: bool = True):
        """
        Args:
            headless: Запускать браузер в фоновом режиме
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def __enter__(self):
        """Context manager для автоматического закрытия браузера."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        self.page.set_default_timeout(30000)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрывает браузер при выходе."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def fetch_company_reports(self, company_id: str) -> List[Dict]:
        """
        Получает список финансовых отчётов компании.

        Args:
            company_id: ID компании на e-disclosure.ru (например: "36276")

        Returns:
            Список словарей с информацией об отчётах
        """
        url = f"{self.BASE_URL}/portal/company.aspx?id={company_id}"
        logger.info(f"Загрузка страницы компании: {url}")

        try:
            self.page.goto(url, wait_until="networkidle")
            time.sleep(2)  # Даём странице полностью загрузиться

            # Ищем раздел с финансовой отчётностью
            reports = []

            # Вариант 1: Ищем ссылки на годовую отчётность
            links = self.page.query_selector_all('a[href*="financial"]')
            for link in links:
                text = link.inner_text().strip()
                href = link.get_attribute('href')

                if any(keyword in text.lower() for keyword in ['баланс', 'отчёт', 'финанс']):
                    reports.append({
                        'title': text,
                        'url': href if href.startswith('http') else f"{self.BASE_URL}{href}",
                        'type': self._detect_report_type(text)
                    })

            logger.info(f"Найдено отчётов: {len(reports)}")
            return reports

        except Exception as e:
            logger.error(f"Ошибка при загрузке страницы: {e}")
            return []

    def parse_balance_sheet(self, url: str) -> Dict[str, float]:
        """
        Парсит бухгалтерский баланс (форма 1).

        Args:
            url: URL страницы с балансом

        Returns:
            Словарь {код_строки: значение}
        """
        logger.info(f"Парсинг баланса: {url}")

        try:
            self.page.goto(url, wait_until="networkidle")
            time.sleep(2)

            # Получаем HTML таблицы
            content = self.page.content()

            # Парсим таблицу
            data = self._parse_table(content, self.BALANCE_CODES)
            logger.info(f"Извлечено строк баланса: {len(data)}")

            return data

        except Exception as e:
            logger.error(f"Ошибка парсинга баланса: {e}")
            return {}

    def parse_income_statement(self, url: str) -> Dict[str, float]:
        """
        Парсит отчёт о прибылях и убытках (форма 2).

        Args:
            url: URL страницы с ОПУ

        Returns:
            Словарь {код_строки: значение}
        """
        logger.info(f"Парсинг ОПУ: {url}")

        try:
            self.page.goto(url, wait_until="networkidle")
            time.sleep(2)

            content = self.page.content()
            data = self._parse_table(content, self.OPU_CODES)
            logger.info(f"Извлечено строк ОПУ: {len(data)}")

            return data

        except Exception as e:
            logger.error(f"Ошибка парсинга ОПУ: {e}")
            return {}

    def parse_cash_flow(self, url: str) -> Dict[str, float]:
        """
        Парсит отчёт о движении денежных средств (форма 4).

        Args:
            url: URL страницы с ОДДС

        Returns:
            Словарь {код_строки: значение}
        """
        logger.info(f"Парсинг ОДДС: {url}")

        try:
            self.page.goto(url, wait_until="networkidle")
            time.sleep(2)

            content = self.page.content()
            data = self._parse_table(content, self.ODDS_CODES)
            logger.info(f"Извлечено строк ОДДС: {len(data)}")

            return data

        except Exception as e:
            logger.error(f"Ошибка парсинга ОДДС: {e}")
            return {}

    def fetch_all_financials(self, company_id: str, year: int = None) -> Dict:
        """
        Получает все финансовые данные компании за год.

        Args:
            company_id: ID компании на e-disclosure.ru
            year: Год отчётности (по умолчанию текущий)

        Returns:
            Словарь со всеми финансовыми показателями
        """
        if year is None:
            year = datetime.now().year - 1  # Берём прошлый год

        logger.info(f"Сбор финансовых данных для компании {company_id} за {year} год")

        # Получаем список отчётов
        reports = self.fetch_company_reports(company_id)

        if not reports:
            logger.warning("Отчёты не найдены")
            return {}

        # Фильтруем отчёты по году
        year_reports = [r for r in reports if str(year) in r['title']]

        if not year_reports:
            logger.warning(f"Отчёты за {year} год не найдены")
            year_reports = reports[:3]  # Берём последние 3

        # Собираем данные из всех форм
        result = {
            'company_id': company_id,
            'year': year,
            'fetched_at': datetime.now().isoformat(),
            'source': 'e-disclosure.ru',
        }

        for report in year_reports:
            report_type = report['type']
            url = report['url']

            if report_type == 'balance':
                result.update(self.parse_balance_sheet(url))
            elif report_type == 'income':
                result.update(self.parse_income_statement(url))
            elif report_type == 'cashflow':
                result.update(self.parse_cash_flow(url))

        return result

    def _parse_table(self, html: str, code_map: Dict[str, str]) -> Dict[str, float]:
        """
        Парсит HTML таблицу отчётности и извлекает значения по кодам строк.

        Args:
            html: HTML содержимое страницы
            code_map: Маппинг {код_строки: название_поля}

        Returns:
            Словарь {название_поля: значение}
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')
        result = {}

        # Ищем все строки таблицы
        for row in soup.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue

            # Первая ячейка - код строки
            code_cell = cells[0].get_text(strip=True)

            # Ищем 4-значный код
            code_match = re.search(r'\b(\d{4})\b', code_cell)
            if not code_match:
                continue

            code = code_match.group(1)

            if code not in code_map:
                continue

            # Последняя ячейка - значение
            value_cell = cells[-1].get_text(strip=True)

            # Очищаем значение от пробелов и неразрывных пробелов
            value_str = value_cell.replace(' ', '').replace('\xa0', '').replace(',', '.')

            # Извлекаем число
            value_match = re.search(r'[-]?\d+\.?\d*', value_str)
            if value_match:
                try:
                    value = float(value_match.group())
                    field_name = code_map[code]
                    result[field_name] = value
                    logger.debug(f"  {code} ({field_name}): {value}")
                except ValueError:
                    continue

        return result

    def _detect_report_type(self, title: str) -> str:
        """Определяет тип отчёта по названию."""
        title_lower = title.lower()

        if 'баланс' in title_lower:
            return 'balance'
        elif 'прибыл' in title_lower or 'убыт' in title_lower:
            return 'income'
        elif 'движени' in title_lower and 'денеж' in title_lower:
            return 'cashflow'
        else:
            return 'unknown'


def test_scraper():
    """Тестирует парсер на примере ГТЛК."""

    # ID ГТЛК на e-disclosure.ru (нужно найти реальный)
    company_id = "36276"  # Пример

    with EDisclosureScraper(headless=False) as scraper:
        # Получаем список отчётов
        reports = scraper.fetch_company_reports(company_id)

        print(f"\nНайдено отчётов: {len(reports)}")
        for i, report in enumerate(reports[:5], 1):
            print(f"{i}. {report['title']}")
            print(f"   Тип: {report['type']}")
            print(f"   URL: {report['url'][:80]}...")

        # Пробуем спарсить первый отчёт
        if reports:
            print("\nПарсинг первого отчёта...")
            data = scraper.fetch_all_financials(company_id)

            print(f"\nИзвлечено показателей: {len(data)}")
            for key, value in list(data.items())[:10]:
                print(f"  {key}: {value}")


if __name__ == "__main__":
    test_scraper()
