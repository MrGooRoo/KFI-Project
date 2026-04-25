#!/usr/bin/env python3
"""
test_ocr_output.py — Диагностика OCR-вывода для отладки извлечения данных
"""

import pdfplumber
import pytesseract
from pathlib import Path

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def test_ocr_on_page(pdf_path: str, page_num: int):
    """Тестирует OCR на конкретной странице и выводит результат."""

    print(f"\n{'='*70}")
    print(f"ТЕСТ OCR: Страница {page_num}")
    print(f"{'='*70}\n")

    with pdfplumber.open(pdf_path) as pdf:
        if page_num > len(pdf.pages):
            print(f"Ошибка: в PDF только {len(pdf.pages)} страниц")
            return

        page = pdf.pages[page_num - 1]

        # Пробуем извлечь таблицы напрямую
        tables = page.extract_tables()
        print(f"[1] pdfplumber нашёл таблиц: {len(tables)}")

        if tables:
            print("\nПервая таблица (первые 5 строк):")
            for i, row in enumerate(tables[0][:5]):
                print(f"  {i+1}: {row}")

        # Пробуем OCR
        print(f"\n[2] Запуск OCR...")
        pil_image = page.to_image(resolution=300).original
        text = pytesseract.image_to_string(pil_image, lang='rus+eng')

        print(f"OCR распознал {len(text)} символов\n")

        # Выводим первые 2000 символов
        print("="*70)
        print("РАСПОЗНАННЫЙ ТЕКСТ (первые 2000 символов):")
        print("="*70)
        print(text[:2000])
        print("="*70)

        # Ищем ключевые слова
        keywords = [
            'баланс', 'актив', 'пассив', 'капитал', 'обязательства',
            'оборотные', 'внеоборотные', 'денежные средства', 'запасы',
            'выручка', 'прибыль', 'убыток'
        ]

        print("\n[3] Поиск ключевых слов:")
        found = []
        for keyword in keywords:
            if keyword in text.lower():
                found.append(keyword)
                # Находим контекст вокруг ключевого слова
                idx = text.lower().find(keyword)
                context = text[max(0, idx-50):min(len(text), idx+100)]
                print(f"  ✓ '{keyword}' найдено:")
                print(f"    ...{context}...")

        if not found:
            print("  ✗ Ключевые слова не найдены")

        # Сохраняем полный текст в файл
        output_file = f"ocr_page_{page_num}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"\n[4] Полный текст сохранён в: {output_file}")


def main():
    import sys

    if len(sys.argv) < 3:
        print("""
Использование:
  python src/test_ocr_output.py <PDF_PATH> <PAGE_NUM>

Пример:
  python src/test_ocr_output.py "D:/Downloads/SG_Otchetnost' Sehtl Grupp. 2025.pdf" 15
        """)
        return

    pdf_path = sys.argv[1]
    page_num = int(sys.argv[2])

    if not Path(pdf_path).exists():
        print(f"Ошибка: файл не найден: {pdf_path}")
        return

    test_ocr_on_page(pdf_path, page_num)


if __name__ == "__main__":
    main()
