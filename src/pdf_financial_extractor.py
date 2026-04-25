#!/usr/bin/env python3
"""
pdf_financial_extractor.py — Извлечение финансовых данных из PDF-отчётов

Использует PyMuPDF (fitz) для извлечения текста из PDF и регулярные выражения
для поиска финансовых показателей в отчётности (баланс, ОПУ, ОДДС).
"""

import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
    logging.warning("PyMuPDF не установлен. Установите: pip install PyMuPDF")

from financial_data_manager import FinancialData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFFinancialExtractor:
    """Извлекает финансовые показатели из PDF-отчётов."""

    def __init__(self):
        if not fitz:
            raise ImportError("PyMuPDF не установлен. Установите: pip install PyMuPDF")

    def extract_from_pdf(self, pdf_path: str, emitter_id: str, period: str, industry_group: int = 7) -> Optional[FinancialData]:
        """
        Извлекает финансовые данные из PDF-отчёта.

        Args:
            pdf_path: Путь к PDF-файлу
            emitter_id: ID эмитента
            period: Период отчётности (например, 2024-Q4)
            industry_group: Отраслевая группа (по умолчанию 7 - Прочие)

        Returns:
            FinancialData с извлечёнными данными или None
        """
        logger.info(f"Извлечение данных из PDF: {pdf_path}")

        if not Path(pdf_path).exists():
            logger.error(f"Файл не найден: {pdf_path}")
            return None

        try:
            # Открываем PDF и извлекаем текст
            doc = fitz.open(pdf_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()

            logger.info(f"Извлечено {len(full_text)} символов текста")

            # Извлекаем показатели
            data = self._parse_financial_data(full_text, emitter_id, period, industry_group)

            if data:
                logger.info("Успешно извлечены данные из PDF")
                self._log_extracted_fields(data)
            else:
                logger.warning("Не удалось извлечь данные из PDF")

            return data

        except Exception as e:
            logger.error(f"Ошибка при обработке PDF: {e}", exc_info=True)
            return None

    def _parse_financial_data(self, text: str, emitter_id: str, period: str, industry_group: int = 7) -> Optional[FinancialData]:
        """
        Парсит финансовые показатели из текста отчёта.

        Ищет ключевые строки баланса, ОПУ и ОДДС.
        """
        # Нормализуем текст (убираем лишние пробелы, переводы строк)
        text = re.sub(r'\s+', ' ', text)

        # Создаём объект для хранения данных
        data = FinancialData(emitter_id=emitter_id, period=period, industry_group=industry_group)

        # === БАЛАНС ===

        # Активы
        data.current_assets = self._extract_value(text, [
            r'Оборотные активы[^\d]+([\d\s]+)',
            r'Итого по разделу II[^\d]+([\d\s]+)',
            r'ИТОГО ОБОРОТНЫЕ АКТИВЫ[^\d]+([\d\s]+)',
        ])

        data.cash = self._extract_value(text, [
            r'Денежные средства и денежные эквиваленты[^\d]+([\d\s]+)',
            r'Денежные средства[^\d]+([\d\s]+)',
            r'Касса[^\d]+([\d\s]+)',
        ])

        data.inventory = self._extract_value(text, [
            r'Запасы[^\d]+([\d\s]+)',
            r'Товарно-материальные запасы[^\d]+([\d\s]+)',
        ])

        data.total_assets = self._extract_value(text, [
            r'БАЛАНС[^\d]+([\d\s]+)',
            r'Итого активов[^\d]+([\d\s]+)',
            r'Всего активов[^\d]+([\d\s]+)',
        ])

        # Пассивы
        data.current_liabilities = self._extract_value(text, [
            r'Краткосрочные обязательства[^\d]+([\d\s]+)',
            r'Итого по разделу V[^\d]+([\d\s]+)',
            r'ИТОГО КРАТКОСРОЧНЫЕ ОБЯЗАТЕЛЬСТВА[^\d]+([\d\s]+)',
        ])

        data.short_term_debt = self._extract_value(text, [
            r'Краткосрочные заемные средства[^\d]+([\d\s]+)',
            r'Краткосрочные кредиты и займы[^\d]+([\d\s]+)',
        ])

        data.long_term_debt = self._extract_value(text, [
            r'Долгосрочные заемные средства[^\d]+([\d\s]+)',
            r'Долгосрочные кредиты и займы[^\d]+([\d\s]+)',
        ])

        data.equity = self._extract_value(text, [
            r'Капитал и резервы[^\d]+([\d\s]+)',
            r'Итого по разделу III[^\d]+([\d\s]+)',
            r'ИТОГО КАПИТАЛ[^\d]+([\d\s]+)',
        ])

        # === ОТЧЁТ О ПРИБЫЛЯХ И УБЫТКАХ ===

        data.revenue = self._extract_value(text, [
            r'Выручка[^\d]+([\d\s]+)',
            r'Доходы от обычных видов деятельности[^\d]+([\d\s]+)',
            r'Процентные доходы[^\d]+([\d\s]+)',  # Для МФО
        ])

        data.operating_profit = self._extract_value(text, [
            r'Прибыль \(убыток\) от продаж[^\d]+([\d\s]+)',
            r'Операционная прибыль[^\d]+([\d\s]+)',
            r'EBITDA[^\d]+([\d\s]+)',
        ])

        data.net_income = self._extract_value(text, [
            r'Чистая прибыль \(убыток\)[^\d]+([\d\s]+)',
            r'Прибыль \(убыток\) отчетного периода[^\d]+([\d\s]+)',
        ])

        data.interest_expenses = self._extract_value(text, [
            r'Проценты к уплате[^\d]+([\d\s]+)',
            r'Процентные расходы[^\d]+([\d\s]+)',
        ])

        # === ОТЧЁТ О ДВИЖЕНИИ ДЕНЕЖНЫХ СРЕДСТВ ===

        data.cfo = self._extract_value(text, [
            r'Денежные потоки от текущих операций[^\d]+([\d\s]+)',
            r'Чистые денежные средства от операционной деятельности[^\d]+([\d\s]+)',
            r'Сальдо денежных потоков от текущих операций[^\d]+([\d\s]+)',
        ])

        data.capex = self._extract_value(text, [
            r'Приобретение основных средств[^\d]+([\d\s]+)',
            r'Капитальные вложения[^\d]+([\d\s]+)',
            r'Платежи в связи с приобретением.*основных средств[^\d]+([\d\s]+)',
        ])

        # Пытаемся найти данные предыдущего периода для revenue_prev
        data.revenue_prev = self._extract_value(text, [
            r'Выручка.*предыдущий.*период[^\d]+([\d\s]+)',
            r'Выручка.*прошлый.*год[^\d]+([\d\s]+)',
        ])

        return data

    def _extract_value(self, text: str, patterns: list) -> Optional[float]:
        """
        Извлекает числовое значение по списку регулярных выражений.

        Args:
            text: Текст для поиска
            patterns: Список regex-паттернов

        Returns:
            Числовое значение в тысячах рублей или None
        """
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1)
                # Убираем пробелы и конвертируем в число
                value_str = value_str.replace(' ', '').replace('\xa0', '')
                try:
                    value = float(value_str)
                    # Если значение слишком маленькое, возможно это уже в тысячах
                    # Если больше 1000, предполагаем что это рубли и конвертируем в тысячи
                    if value > 1000:
                        value = value / 1000
                    return value
                except ValueError:
                    continue
        return None

    def _log_extracted_fields(self, data: FinancialData):
        """Выводит список извлечённых полей."""
        fields = {
            'Выручка': data.revenue,
            'Чистая прибыль': data.net_income,
            'Операционная прибыль': data.operating_profit,
            'Оборотные активы': data.current_assets,
            'Краткосрочные обязательства': data.current_liabilities,
            'Денежные средства': data.cash,
            'Капитал': data.equity,
            'Всего активов': data.total_assets,
            'Долгосрочный долг': data.long_term_debt,
            'Краткосрочный долг': data.short_term_debt,
            'Процентные расходы': data.interest_expenses,
            'Денежный поток от операций': data.cfo,
            'Капитальные затраты': data.capex,
        }

        found = {k: v for k, v in fields.items() if v is not None}
        missing = {k: v for k, v in fields.items() if v is None}

        logger.info(f"\nИзвлечено полей: {len(found)}/{len(fields)}")
        if found:
            logger.info("Найденные поля:")
            for name, value in found.items():
                logger.info(f"  ✓ {name}: {value:,.0f} тыс. руб.")

        if missing:
            logger.info("\nНе найденные поля:")
            for name in missing.keys():
                logger.info(f"  ✗ {name}")


def main():
    """Тестовый запуск."""
    import sys

    if len(sys.argv) < 4:
        print("""
Использование:
  python src/pdf_financial_extractor.py <PDF_PATH> <EMITTER_ID> <PERIOD>

Пример:
  python src/pdf_financial_extractor.py reports/carmoney_2024q4.pdf CARMONEY 2024-Q4
        """)
        return

    pdf_path = sys.argv[1]
    emitter_id = sys.argv[2]
    period = sys.argv[3]

    extractor = PDFFinancialExtractor()
    data = extractor.extract_from_pdf(pdf_path, emitter_id, period)

    if data:
        print("\n" + "="*70)
        print("РЕЗУЛЬТАТ ИЗВЛЕЧЕНИЯ")
        print("="*70)
        print(f"\nЭмитент: {emitter_id}")
        print(f"Период: {period}")
        print(f"\nИзвлечённые данные сохранены в объект FinancialData")

        # Предлагаем сохранить
        response = input("\nСохранить данные? (y/n): ").strip().lower()
        if response == 'y':
            from financial_data_manager import FinancialDataManager
            manager = FinancialDataManager()
            manager.save_financial_data(data)
            print(f"Данные сохранены в data/financials/{emitter_id}_{period}.json")


if __name__ == "__main__":
    main()
