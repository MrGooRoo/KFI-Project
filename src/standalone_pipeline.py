#!/usr/bin/env python3
"""
standalone_pipeline.py — Автономный конвейер анализа эмитента по PDF

Полностью автономный анализ без привязки к базе эмитентов:
1. Загрузка PDF-отчёта
2. Извлечение названия эмитента и периода
3. Извлечение финансовых данных
4. Определение отраслевой группы
5. Расчёт КФИ
6. Генерация карточки и текстов для соцсетей

Использование:
    python src/standalone_pipeline.py path/to/report.pdf
"""

import sys
import json
import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
    print("ERROR: PyMuPDF не установлен. Установите: pip install PyMuPDF")
    sys.exit(1)

from financial_data_manager import FinancialData
from kfi_calculator import KfiCalculator
from card_generator import CardGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class StandalonePipeline:
    """Автономный конвейер анализа эмитента по PDF."""

    # Отраслевые группы
    INDUSTRY_GROUPS = {
        1: "Девелопмент и строительство",
        2: "МФО и потребкредитование",
        3: "Лизинг",
        4: "Торговля и ритейл",
        5: "Производство и промышленность",
        6: "Транспорт и логистика",
        7: "Прочие и диверсифицированные"
    }

    # Ключевые слова для автоопределения отрасли
    INDUSTRY_KEYWORDS = {
        1: ["девелопмент", "строительство", "недвижимость", "застройщик"],
        2: ["мфо", "микрофинанс", "микрокредит", "займ", "потребительский кредит"],
        3: ["лизинг", "финансовая аренда"],
        4: ["торговля", "ритейл", "магазин", "сеть магазинов", "розничная торговля"],
        5: ["производство", "завод", "фабрика", "промышленность", "изготовление"],
        6: ["транспорт", "логистика", "перевозка", "доставка", "грузоперевозки"],
        7: ["холдинг", "группа компаний", "диверсифицированный"]
    }

    def __init__(self):
        self.kfi_calculator = KfiCalculator()
        self.card_generator = CardGenerator()

    def run(self, pdf_path: str):
        """
        Запускает полный конвейер анализа по PDF.

        Args:
            pdf_path: Путь к PDF-файлу с отчётностью
        """
        logger.info("="*70)
        logger.info("  АВТОНОМНЫЙ КОНВЕЙЕР АНАЛИЗА ЭМИТЕНТА")
        logger.info("="*70 + "\n")

        # Шаг 1: Извлечение текста из PDF
        logger.info("[1/7] Извлечение текста из PDF...")
        text = self._extract_text_from_pdf(pdf_path)
        if not text:
            logger.error("Не удалось извлечь текст из PDF")
            return None

        logger.info(f"      Извлечено {len(text)} символов\n")

        # Шаг 2: Определение эмитента и периода
        logger.info("[2/7] Определение эмитента и периода...")
        emitter_name, period = self._extract_emitter_and_period(text)

        if not emitter_name:
            try:
                emitter_name = input("      Не удалось определить название эмитента. Введите вручную: ").strip()
            except (EOFError, OSError):
                logger.error("Не удалось определить название эмитента автоматически")
                return None

        if not period:
            try:
                period = input("      Не удалось определить период. Введите вручную (например, 2024-Q4): ").strip()
            except (EOFError, OSError):
                # Используем текущий год Q4 по умолчанию
                from datetime import datetime
                current_year = datetime.now().year
                period = f"{current_year}-Q4"
                logger.warning(f"      Период не определён, используется по умолчанию: {period}")

        logger.info(f"      Эмитент: {emitter_name}")
        logger.info(f"      Период: {period}\n")

        # Генерируем ID эмитента
        emitter_id = self._generate_emitter_id(emitter_name)

        # Шаг 3: Определение отраслевой группы
        logger.info("[3/7] Определение отраслевой группы...")
        industry_group = self._determine_industry_group(text, emitter_name)
        logger.info(f"      Группа: {industry_group} — {self.INDUSTRY_GROUPS[industry_group]}\n")

        # Шаг 4: Извлечение финансовых данных
        logger.info("[4/7] Извлечение финансовых данных...")
        financial_data = self._extract_financial_data(pdf_path, emitter_id, period, industry_group)

        if not financial_data:
            logger.error("Не удалось извлечь финансовые данные")
            return None

        self._log_extracted_fields(financial_data)

        # Запрашиваем недостающие поля
        financial_data = self._fill_missing_fields(financial_data)

        # Шаг 5: Расчёт КФИ
        logger.info("\n[5/7] Расчёт КФИ...")

        # Создаём объект эмитента для калькулятора
        emitter = {
            'emitter_id': emitter_id,
            'name': emitter_name,
            'short_name': emitter_name,
            'sector': self.INDUSTRY_GROUPS[industry_group],
            'industry_group': industry_group
        }

        kfi_result = self._calculate_kfi(emitter, financial_data, period)

        if not kfi_result:
            logger.error("Ошибка расчёта КФИ")
            return None

        logger.info(f"      КФИ: {kfi_result['kfi_final']:.1f} ({kfi_result['category']})")
        logger.info(f"      Блоки: A={kfi_result['block_scores']['block_a']:.0f} "
                   f"B={kfi_result['block_scores']['block_b']:.0f} "
                   f"C={kfi_result['block_scores']['block_c']:.0f} "
                   f"D={kfi_result['block_scores']['block_d']:.0f} "
                   f"E={kfi_result['block_scores']['block_e']:.0f} "
                   f"F={kfi_result['block_scores']['block_f']:.0f}\n")

        # Шаг 6: Генерация карточки
        logger.info("[6/7] Генерация карточки эмитента...")

        # Сохраняем данные эмитента и расчёты для генератора карточек
        self._save_emitter_data(emitter, financial_data, kfi_result)

        card_path = self._generate_card(emitter_id)
        if card_path:
            logger.info(f"      HTML: {card_path}.html")
            logger.info(f"      PNG:  {card_path}.png\n")

        # Шаг 7: Генерация текстов для соцсетей
        logger.info("[7/7] Генерация текстов для публикации...")
        social_text = self._generate_social_text(emitter, kfi_result)

        logger.info("\n" + "="*70)
        logger.info("  КОНВЕЙЕР ЗАВЕРШЁН УСПЕШНО")
        logger.info("="*70 + "\n")

        # Выводим результаты
        self._print_results(emitter, kfi_result, card_path, social_text)

        return {
            "emitter": emitter,
            "period": period,
            "kfi_result": kfi_result,
            "card_path": card_path,
            "social_text": social_text,
        }

    def _extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """Извлекает текст из PDF."""
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()
            return full_text
        except Exception as e:
            logger.error(f"Ошибка при чтении PDF: {e}")
            return None

    def _extract_emitter_and_period(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Извлекает название эмитента и период отчётности из текста.
        """
        emitter_name = None
        period = None

        # Ищем название организации
        patterns_name = [
            r'(?:ООО|АО|ПАО|ЗАО|ОАО)\s+[«"]([^»"]+)[»"]',
            r'Организация:\s*([^\n]+)',
            r'Наименование:\s*([^\n]+)',
        ]

        for pattern in patterns_name:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                emitter_name = match.group(1).strip()
                break

        # Ищем период отчётности
        patterns_period = [
            r'(?:за|на)\s+(\d{4})\s+год',
            r'(?:за|на)\s+(\d{1,2})\s+месяц[а-я]*\s+(\d{4})',
            r'(?:за|на)\s+(I{1,3}|IV)\s+квартал\s+(\d{4})',
            r'отчетный период[:\s]+([^\n]+)',
            r'(\d{4})\s+год',
            r'за\s+год[,\s]+закончившийся\s+31\s+декабря\s+(\d{4})',
        ]

        for pattern in patterns_period:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Конвертируем в формат YYYY-QX
                if 'месяц' in pattern:
                    month = int(match.group(1))
                    year = match.group(2)
                    quarter = (month - 1) // 3 + 1
                    period = f"{year}-Q{quarter}"
                elif 'квартал' in pattern:
                    quarter_roman = match.group(1)
                    year = match.group(2)
                    quarter_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4}
                    quarter = quarter_map.get(quarter_roman, 4)
                    period = f"{year}-Q{quarter}"
                elif 'год' in pattern:
                    year = match.group(1)
                    period = f"{year}-Q4"  # Годовой отчёт = Q4
                break

        return emitter_name, period

    def _generate_emitter_id(self, name: str) -> str:
        """Генерирует ID эмитента из названия."""
        # Транслитерация и очистка
        translit = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }

        name_lower = name.lower()
        result = ""
        for char in name_lower:
            result += translit.get(char, char)

        # Оставляем только буквы и цифры
        result = re.sub(r'[^a-z0-9]', '', result)
        return result[:20].upper()  # Максимум 20 символов

    def _determine_industry_group(self, text: str, emitter_name: str) -> int:
        """Определяет отраслевую группу по ключевым словам."""
        text_lower = (text + " " + emitter_name).lower()

        # Подсчитываем совпадения для каждой группы
        scores = {}
        for group_id, keywords in self.INDUSTRY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[group_id] = score

        if scores:
            # Возвращаем группу с максимальным количеством совпадений
            best_group = max(scores, key=scores.get)
            logger.info(f"      Автоопределение: найдено {scores[best_group]} совпадений")
            return best_group

        # Если не удалось определить автоматически
        logger.warning("      Не удалось определить автоматически")

        try:
            print("\nВыберите отраслевую группу:")
            for group_id, group_name in self.INDUSTRY_GROUPS.items():
                print(f"  {group_id}. {group_name}")

            while True:
                choice = input("\nВведите номер группы (1-7): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= 7:
                    return int(choice)
                print("Неверный выбор. Введите число от 1 до 7.")
        except (EOFError, OSError):
            # В неинтерактивном режиме используем группу 7 (Прочие) по умолчанию
            logger.warning("      Неинтерактивный режим: используется группа 7 (Прочие) по умолчанию")
            return 7

    def _extract_financial_data(self, pdf_path: str, emitter_id: str, period: str, industry_group: int) -> Optional[FinancialData]:
        """Извлекает финансовые данные из PDF (с поддержкой таблиц)."""
        # Сначала пробуем улучшенный экстрактор с pdfplumber
        try:
            from enhanced_pdf_extractor import EnhancedPDFExtractor

            logger.info("      Используется улучшенный экстрактор (pdfplumber)")
            extractor = EnhancedPDFExtractor()
            data = extractor.extract_from_pdf(pdf_path, emitter_id, period, industry_group)

            if data:
                return data
            else:
                logger.warning("      Улучшенный экстрактор не смог извлечь данные")
        except ImportError as e:
            logger.info(f"      enhanced_pdf_extractor недоступен: {e}")
        except Exception as e:
            logger.warning(f"      Ошибка в улучшенном экстракторе: {e}")

        # Fallback на базовый метод
        logger.info("      Используется базовый экстрактор (PyMuPDF + regex)")
        from pdf_financial_extractor import PDFFinancialExtractor

        extractor = PDFFinancialExtractor()
        data = extractor.extract_from_pdf(pdf_path, emitter_id, period, industry_group)
        return data

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
        missing = [k for k, v in fields.items() if v is None]

        logger.info(f"\n      Извлечено полей: {len(found)}/{len(fields)}")
        if found:
            logger.info("      Найденные поля:")
            for name, value in found.items():
                logger.info(f"        ✓ {name}: {value:,.0f} тыс. руб.")

        if missing:
            logger.info("\n      Не найденные поля:")
            for name in missing:
                logger.info(f"        ✗ {name}")

    def _fill_missing_fields(self, data: FinancialData) -> FinancialData:
        """Запрашивает ручной ввод недостающих критических полей."""
        required_fields = {
            'revenue': 'Выручка',
            'equity': 'Капитал и резервы',
            'cfo': 'Денежный поток от операционной деятельности',
            'current_assets': 'Оборотные активы',
            'current_liabilities': 'Краткосрочные обязательства',
        }

        missing = [field for field in required_fields.keys()
                  if getattr(data, field, None) is None]

        if not missing:
            logger.info("\n      [OK] Все критические поля присутствуют")
            return data

        logger.info("\n" + "="*70)
        logger.info("  РУЧНОЙ ВВОД НЕДОСТАЮЩИХ ПОЛЕЙ")
        logger.info("="*70 + "\n")

        for field in missing:
            field_label = required_fields[field]
            while True:
                try:
                    value_str = input(f"{field_label} (тыс. руб.): ").strip()
                    value = float(value_str.replace(' ', '').replace(',', '.'))
                    setattr(data, field, value)
                    break
                except ValueError:
                    print("  [ERROR] Введите числовое значение")
                except (EOFError, OSError):
                    # В неинтерактивном режиме используем 0
                    logger.warning(f"      Неинтерактивный режим: {field_label} = 0 (по умолчанию)")
                    setattr(data, field, 0)
                    break

        logger.info("\n[OK] Данные дополнены")
        return data

    def _calculate_kfi(self, emitter: Dict, financial_data: FinancialData, period: str) -> Optional[Dict]:
        """Рассчитывает КФИ."""
        try:
            # Конвертируем FinancialData в словарь для калькулятора
            financials_dict = {
                'current_ratio': financial_data.current_assets / financial_data.current_liabilities
                                if financial_data.current_assets and financial_data.current_liabilities else 1.5,
                'quick_ratio': (financial_data.current_assets - (financial_data.inventory or 0)) / financial_data.current_liabilities
                              if financial_data.current_assets and financial_data.current_liabilities else 1.0,
                'cash_ratio': financial_data.cash / financial_data.current_liabilities
                             if financial_data.cash and financial_data.current_liabilities else 0.2,
                'icr': financial_data.operating_profit / financial_data.interest_expenses
                      if financial_data.operating_profit and financial_data.interest_expenses else 2.0,
                'debt_ebitda': ((financial_data.long_term_debt or 0) + (financial_data.short_term_debt or 0)) / financial_data.operating_profit
                              if financial_data.operating_profit else 3.5,
                'equity_ratio': financial_data.equity / financial_data.total_assets
                               if financial_data.equity and financial_data.total_assets else 0.3,
                'roe': financial_data.net_income / financial_data.equity
                      if financial_data.net_income and financial_data.equity else 0.15,
                'fcf_to_ebitda': (financial_data.cfo - (financial_data.capex or 0)) / financial_data.operating_profit
                                if financial_data.cfo and financial_data.operating_profit else 0.5,
            }

            result = self.kfi_calculator.calculate_kfi(emitter, financials_dict, period)
            return result

        except Exception as e:
            logger.error(f"Ошибка расчёта КФИ: {e}", exc_info=True)
            return None

    def _save_emitter_data(self, emitter: Dict, financial_data: FinancialData, kfi_result: Dict):
        """Сохраняет данные эмитента для генератора карточек."""
        # Сохраняем финансовые данные
        from financial_data_manager import FinancialDataManager
        manager = FinancialDataManager()
        manager.save_financial_data(financial_data)

        # Сохраняем расчёты КФИ
        calc_dir = Path("data") / "calculations"
        calc_dir.mkdir(parents=True, exist_ok=True)

        calc_file = calc_dir / f"{emitter['emitter_id']}_{financial_data.period}.json"
        with open(calc_file, 'w', encoding='utf-8') as f:
            json.dump(kfi_result, f, ensure_ascii=False, indent=2)

        # Добавляем эмитента в базу (если его там нет)
        emitters_file = Path("data") / "emitters.json"
        if emitters_file.exists():
            with open(emitters_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Файл имеет структуру с ключом "emitters"
                if isinstance(data, dict) and 'emitters' in data:
                    emitters = data['emitters']
                else:
                    emitters = data if isinstance(data, list) else []
        else:
            emitters = []
            data = {
                "$schema": "https://raw.githubusercontent.com/MrGooRoo/KFI-Project/main/data/schema.json",
                "version": "2.1",
                "updated": datetime.now().strftime("%Y-%m-%d"),
                "emitters": []
            }

        # Проверяем, есть ли уже такой эмитент
        if not any(e['emitter_id'] == emitter['emitter_id'] for e in emitters):
            emitters.append(emitter)

            # Сохраняем обратно
            if isinstance(data, dict) and 'emitters' in data:
                data['emitters'] = emitters
                data['updated'] = datetime.now().strftime("%Y-%m-%d")
            else:
                data = emitters

            with open(emitters_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _generate_card(self, emitter_id: str) -> Optional[str]:
        """Генерирует визуальную карточку эмитента."""
        try:
            self.card_generator.generate_card(emitter_id)
            return f"output/cards/card_{emitter_id.lower()}"
        except Exception as e:
            logger.error(f"Ошибка генерации карточки: {e}")
            return None

    def _generate_social_text(self, emitter: Dict, kfi_result: Dict) -> Dict[str, str]:
        """Генерирует тексты для социальных сетей."""
        emitter_name = emitter['short_name']
        kfi = kfi_result['kfi_final']
        category = kfi_result['category']
        blocks = kfi_result['block_scores']

        # Определяем эмодзи категории
        category_emoji = {
            "Надёжный": "🟢",
            "Стабильный": "🔵",
            "Умеренный риск": "🟡",
            "Высокий риск": "🟠",
            "Критический": "🔴"
        }.get(category, "⚪")

        # Telegram версия (полная)
        telegram_text = f"""📊 Анализ эмитента: {emitter_name}

{category_emoji} КФИ: {kfi:.1f} — {category}

📈 Детализация по блокам:
• Блок A (Ликвидность): {blocks['block_a']:.0f}/100
• Блок B (Долговая нагрузка): {blocks['block_b']:.0f}/100
• Блок C (Рентабельность): {blocks['block_c']:.0f}/100
• Блок D (Денежный поток): {blocks['block_d']:.0f}/100
• Блок E (Облигационный профиль): {blocks['block_e']:.0f}/100
• Блок F (Качественная оценка): {blocks['block_f']:.0f}/100

💡 Что это значит:
{self._get_category_description(category)}

⚠️ Дисклеймер: Оценка КФИ носит информационно-аналитический характер и не является инвестиционной рекомендацией.

#КФИ #{emitter['emitter_id']} #ВДО #Облигации
"""

        # VK/Пульс версия (краткая)
        vk_text = f"""{emitter_name}: КФИ {kfi:.1f} {category_emoji}

Категория: {category}
Ключевые показатели: A={blocks['block_a']:.0f} B={blocks['block_b']:.0f} D={blocks['block_d']:.0f}

{self._get_category_description(category, short=True)}

Полный разбор: [ссылка на карточку]
"""

        # Сохраняем тексты
        output_dir = Path("output") / "social_posts"
        output_dir.mkdir(parents=True, exist_ok=True)

        telegram_file = output_dir / f"{emitter['emitter_id']}_telegram.txt"
        vk_file = output_dir / f"{emitter['emitter_id']}_vk.txt"

        with open(telegram_file, 'w', encoding='utf-8') as f:
            f.write(telegram_text)

        with open(vk_file, 'w', encoding='utf-8') as f:
            f.write(vk_text)

        logger.info(f"      [OK] Telegram: {telegram_file}")
        logger.info(f"      [OK] VK/Пульс: {vk_file}")

        return {
            'telegram': telegram_text,
            'vk': vk_text
        }

    def _get_category_description(self, category: str, short: bool = False) -> str:
        """Возвращает описание категории КФИ."""
        descriptions = {
            "Надёжный": {
                "full": "Эмитент демонстрирует высокую финансовую устойчивость, низкий уровень долговой нагрузки и стабильный денежный поток. Риск дефолта минимален.",
                "short": "Высокая финансовая устойчивость, низкий риск."
            },
            "Стабильный": {
                "full": "Эмитент находится в устойчивом финансовом положении с приемлемым уровнем риска для сегмента ВДО.",
                "short": "Устойчивое положение, приемлемый риск."
            },
            "Умеренный риск": {
                "full": "Выявлены слабые места в финансовых показателях. Требуется осторожность при инвестировании.",
                "short": "Есть слабые места, требуется осторожность."
            },
            "Высокий риск": {
                "full": "Серьёзные проблемы с финансовыми показателями. Рекомендуется только для опытных инвесторов.",
                "short": "Серьёзные проблемы, только для опытных."
            },
            "Критический": {
                "full": "Признаки преддефолтного состояния. Высокий риск потери капитала.",
                "short": "Преддефолтное состояние, высокий риск."
            }
        }

        desc = descriptions.get(category, {"full": "", "short": ""})
        return desc["short"] if short else desc["full"]

    def _print_results(self, emitter: Dict, kfi_result: Dict, card_path: str, social_text: Dict):
        """Выводит итоговые результаты."""
        print("\n" + "="*70)
        print("  РЕЗУЛЬТАТЫ АНАЛИЗА")
        print("="*70)
        print(f"\nЭмитент: {emitter['name']}")
        print(f"Отрасль: {emitter['sector']}")
        print(f"КФИ: {kfi_result['kfi_final']:.1f} — {kfi_result['category']}")
        print(f"\nКарточка: {card_path}.html")
        print(f"          {card_path}.png")
        print(f"\nТексты для соцсетей:")
        print(f"  Telegram: output/social_posts/{emitter['emitter_id']}_telegram.txt")
        print(f"  VK/Пульс: output/social_posts/{emitter['emitter_id']}_vk.txt")
        print("\n" + "="*70)


def main():
    """Точка входа CLI."""
    if len(sys.argv) < 2:
        print("""
Использование:
  python src/standalone_pipeline.py <PDF_PATH>

Пример:
  python src/standalone_pipeline.py F:\\Reports\\carmoney_2024q4.pdf
        """)
        return

    pdf_path = sys.argv[1]

    if not Path(pdf_path).exists():
        print(f"ERROR: Файл не найден: {pdf_path}")
        return

    pipeline = StandalonePipeline()
    pipeline.run(pdf_path)


if __name__ == "__main__":
    main()
