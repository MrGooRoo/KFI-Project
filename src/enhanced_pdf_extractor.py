#!/usr/bin/env python3
"""
enhanced_pdf_extractor.py — Улучшенный экстрактор финансовых данных из PDF

Использует pdfplumber для извлечения таблиц и PyMuPDF для текста.
Поддерживает:
- Извлечение таблиц из PDF
- Поиск финансовых показателей в таблицах
- Распознавание структуры баланса, ОПУ, ОДДС
"""

import re
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

try:
    import pdfplumber
except ImportError:
    pdfplumber = None
    logging.warning("pdfplumber не установлен. Установите: pip install pdfplumber")

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
    logging.warning("PyMuPDF не установлен. Установите: pip install PyMuPDF")

try:
    import pytesseract
    from PIL import Image
    import io

    # Настройка пути к tesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    TESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None
    TESSERACT_AVAILABLE = False
    logging.warning("pytesseract не установлен. OCR недоступен.")

from financial_data_manager import FinancialData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedPDFExtractor:
    """Улучшенный экстрактор финансовых данных из PDF с поддержкой таблиц."""

    # Маппинг названий строк баланса на поля FinancialData
    BALANCE_MAPPING = {
        # Активы
        'оборотные активы': 'current_assets',
        'итого по разделу ii': 'current_assets',
        'итого раздел ii': 'current_assets',
        'оборотные активы итого': 'current_assets',
        'денежные средства': 'cash',
        'денежные средства и денежные эквиваленты': 'cash',
        'запасы': 'inventory',
        'баланс': 'total_assets',
        'всего активов': 'total_assets',
        'актив баланс': 'total_assets',
        'валюта баланса': 'total_assets',

        # Пассивы
        'краткосрочные обязательства': 'current_liabilities',
        'итого по разделу v': 'current_liabilities',
        'итого раздел v': 'current_liabilities',
        'краткосрочные обязательства итого': 'current_liabilities',
        'краткосрочные заемные средства': 'short_term_debt',
        'краткосрочные займы': 'short_term_debt',
        'долгосрочные заемные средства': 'long_term_debt',
        'долгосрочные займы': 'long_term_debt',
        'капитал и резервы': 'equity',
        'итого по разделу iii': 'equity',
        'итого раздел iii': 'equity',
        'капитал итого': 'equity',
    }

    # Маппинг ОПУ
    OPU_MAPPING = {
        'выручка': 'revenue',
        'доходы от обычных видов деятельности': 'revenue',
        'доходы от обычной деятельности': 'revenue',
        'выручка от продаж': 'revenue',
        'прибыль (убыток) от продаж': 'operating_profit',
        'прибыль от продаж': 'operating_profit',
        'операционная прибыль': 'operating_profit',
        'чистая прибыль': 'net_income',
        'чистая прибыль (убыток)': 'net_income',
        'прибыль убыток отчетного периода': 'net_income',
        'проценты к уплате': 'interest_expenses',
        'процентные расходы': 'interest_expenses',
    }

    # Маппинг ОДДС
    ODDS_MAPPING = {
        'денежные потоки от текущих операций': 'cfo',
        'сальдо денежных потоков от текущих операций': 'cfo',
        'денежный поток от операционной деятельности': 'cfo',
        'чистые денежные средства от текущей деятельности': 'cfo',
        'приобретение основных средств': 'capex',
        'платежи в связи с приобретением основных средств': 'capex',
        'капитальные вложения': 'capex',
    }

    def __init__(self):
        if not pdfplumber:
            raise ImportError("pdfplumber не установлен")
        if not fitz:
            raise ImportError("PyMuPDF не установлен")

    def extract_from_pdf(self, pdf_path: str, emitter_id: str, period: str, industry_group: int = 7) -> Optional[FinancialData]:
        """
        Извлекает финансовые данные из PDF с использованием таблиц.
        """
        logger.info(f"Улучшенное извлечение данных из PDF: {pdf_path}")

        if not Path(pdf_path).exists():
            logger.error(f"Файл не найден: {pdf_path}")
            return None

        try:
            # Создаём объект для хранения данных
            data = FinancialData(emitter_id=emitter_id, period=period, industry_group=industry_group)

            # Открываем PDF с pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"Всего страниц: {len(pdf.pages)}")

                # Извлекаем таблицы со всех страниц
                all_tables = []
                for i, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    if tables:
                        logger.info(f"Страница {i+1}: найдено {len(tables)} таблиц")
                        all_tables.extend([(i+1, table) for table in tables])
                    else:
                        # Если таблиц нет, пробуем OCR
                        if TESSERACT_AVAILABLE:
                            logger.info(f"Страница {i+1}: таблиц не найдено, пробуем OCR...")
                            ocr_tables = self._extract_tables_with_ocr(page, i+1)
                            if ocr_tables:
                                all_tables.extend([(i+1, table) for table in ocr_tables])

                logger.info(f"Всего извлечено таблиц: {len(all_tables)}")

                # Обрабатываем таблицы
                for page_num, table in all_tables:
                    self._process_table(table, data, page_num)

            # Логируем результаты
            self._log_extracted_fields(data)

            return data

        except Exception as e:
            logger.error(f"Ошибка при обработке PDF: {e}", exc_info=True)
            return None

    def _extract_tables_with_ocr(self, page, page_num: int) -> List[List[List[str]]]:
        """
        Извлекает таблицы из страницы с помощью OCR.
        Конвертирует страницу в изображение и распознаёт текст.
        """
        try:
            # Конвертируем страницу в изображение
            pil_image = page.to_image(resolution=300).original

            # Распознаём текст с помощью Tesseract (русский + английский)
            text = pytesseract.image_to_string(pil_image, lang='rus+eng')

            if not text.strip():
                logger.debug(f"Страница {page_num}: OCR не распознал текст")
                return []

            logger.info(f"Страница {page_num}: OCR распознал {len(text)} символов")

            # Парсим текст построчно, ищем финансовые показатели
            lines = text.split('\n')
            table = []

            for line in lines:
                line = line.strip()
                if not line or len(line) < 5:
                    continue

                # Нормализуем пробелы
                line = re.sub(r'\s+', ' ', line)

                # Ищем строки с числами (финансовые показатели)
                # Формат: "Название показателя ... число число"
                if re.search(r'\d', line):
                    # Разбиваем на слова
                    parts = line.split()

                    # Ищем числа в конце строки
                    numbers = []
                    text_parts = []

                    for part in parts:
                        # Убираем пробелы внутри чисел (OCR может разбить)
                        part_clean = part.replace(' ', '').replace('\xa0', '')

                        # Проверяем, это число?
                        if re.match(r'^-?\d+[\d\s]*$', part_clean):
                            numbers.append(part_clean)
                        else:
                            text_parts.append(part)

                    # Если есть название и хотя бы одно число
                    if text_parts and numbers:
                        # Собираем название из первых слов
                        name = ' '.join(text_parts)
                        # Создаём строку таблицы: [название, число1, число2, ...]
                        row = [name] + numbers
                        table.append(row)

            if table:
                logger.info(f"Страница {page_num}: OCR извлёк таблицу с {len(table)} строками")
                return [table]

            return []

        except Exception as e:
            logger.warning(f"Страница {page_num}: Ошибка OCR: {e}")
            return []

    def _process_table(self, table: List[List[str]], data: FinancialData, page_num: int):
        """
        Обрабатывает одну таблицу и извлекает финансовые показатели.
        """
        if not table or len(table) < 2:
            return

        # Проходим по всем строкам таблицы
        for row in table:
            if not row or len(row) < 2:
                continue

            # Первая ячейка - название показателя
            name = str(row[0]).lower().strip() if row[0] else ''

            # Нормализуем название (убираем лишние пробелы, знаки)
            name = re.sub(r'\s+', ' ', name)
            name = name.replace('ё', 'е')  # OCR может путать ё и е

            # Ищем числовое значение в строке
            value = self._extract_number_from_row(row)

            if not value or not name:
                continue

            # Проверяем маппинги (используем частичное совпадение)
            field_name = None

            # Баланс
            for key, field in self.BALANCE_MAPPING.items():
                # Проверяем, содержится ли ключевое слово в названии
                if key in name or self._fuzzy_match(key, name):
                    field_name = field
                    break

            # ОПУ
            if not field_name:
                for key, field in self.OPU_MAPPING.items():
                    if key in name or self._fuzzy_match(key, name):
                        field_name = field
                        break

            # ОДДС
            if not field_name:
                for key, field in self.ODDS_MAPPING.items():
                    if key in name or self._fuzzy_match(key, name):
                        field_name = field
                        break

            # Если нашли соответствие - сохраняем
            if field_name:
                current_value = getattr(data, field_name, None)
                if current_value is None or current_value == 0:
                    setattr(data, field_name, value)
                    logger.info(f"Страница {page_num}: {field_name} = {value:,.0f} ({name[:50]})")

    def _fuzzy_match(self, pattern: str, text: str) -> bool:
        """
        Нечёткое сопоставление с учётом OCR-ошибок.
        Проверяет, содержатся ли ключевые слова паттерна в тексте.
        """
        # Разбиваем паттерн на слова
        pattern_words = pattern.split()

        # Проверяем, есть ли все ключевые слова в тексте
        matches = 0
        for word in pattern_words:
            if len(word) >= 4 and word in text:  # Ищем только значимые слова
                matches += 1

        # Если найдено больше половины ключевых слов - считаем совпадением
        return matches > 0 and matches >= len(pattern_words) / 2

    def _extract_number_from_row(self, row: List[str]) -> Optional[float]:
        """
        Извлекает числовое значение из строки таблицы.
        Ищет в последних колонках (обычно там текущий период).
        """
        # Проверяем последние 3 колонки (обычно: предыдущий год, текущий год, ещё что-то)
        for cell in reversed(row[-3:]):
            if not cell:
                continue

            # Убираем пробелы и ищем число
            cell_str = str(cell).replace(' ', '').replace('\xa0', '').replace(',', '.')

            # Ищем число (может быть с минусом, может быть разделено пробелами)
            # OCR может распознать "1 234 567" как отдельные части
            cell_str = re.sub(r'[^\d\-\.]', '', cell_str)

            # Ищем число
            match = re.search(r'-?\d+\.?\d*', cell_str)
            if match:
                try:
                    value = float(match.group())
                    # Если число больше 1000, считаем что это уже в тысячах
                    # Если меньше - возможно в миллионах, конвертируем
                    if value > 1000:
                        return value
                    elif value > 0:
                        # Проверяем, может это миллионы
                        return value * 1000
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

        found = {k: v for k, v in fields.items() if v is not None and v != 0}
        missing = [k for k, v in fields.items() if v is None or v == 0]

        logger.info(f"\nИзвлечено полей: {len(found)}/{len(fields)}")
        if found:
            logger.info("Найденные поля:")
            for name, value in found.items():
                logger.info(f"  ✓ {name}: {value:,.0f} тыс. руб.")

        if missing:
            logger.info("\nНе найденные поля:")
            for name in missing:
                logger.info(f"  ✗ {name}")


def main():
    """Тестовый запуск."""
    import sys

    if len(sys.argv) < 4:
        print("""
Использование:
  python src/enhanced_pdf_extractor.py <PDF_PATH> <EMITTER_ID> <PERIOD>

Пример:
  python src/enhanced_pdf_extractor.py reports/setl_2025.pdf SETL 2025-Q4
        """)
        return

    pdf_path = sys.argv[1]
    emitter_id = sys.argv[2]
    period = sys.argv[3]

    extractor = EnhancedPDFExtractor()
    data = extractor.extract_from_pdf(pdf_path, emitter_id, period)

    if data:
        print("\n" + "="*70)
        print("РЕЗУЛЬТАТ ИЗВЛЕЧЕНИЯ")
        print("="*70)
        print(f"\nЭмитент: {emitter_id}")
        print(f"Период: {period}")

        # Предлагаем сохранить
        response = input("\nСохранить данные? (y/n): ").strip().lower()
        if response == 'y':
            from financial_data_manager import FinancialDataManager
            manager = FinancialDataManager()
            manager.save_financial_data(data)
            print(f"Данные сохранены в data/financials/{emitter_id}_{period}.json")


if __name__ == "__main__":
    main()
