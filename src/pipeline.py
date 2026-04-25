#!/usr/bin/env python3
"""
pipeline.py — Автоматизированный конвейер обработки эмитента

Этапы:
1. Выбор эмитента
2. Парсинг финансовых данных (MOEX + e-disclosure)
3. Ручной ввод недостающих данных (если нужно)
4. Расчёт КФИ
5. Генерация карточки эмитента
6. Генерация текста для соцсетей

Использование:
    python src/pipeline.py CARMONEY
    python src/pipeline.py --interactive
"""

import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Импорт модулей проекта
from moex_parser import MOEXBondParser, load_emitters
from financial_data_manager import FinancialDataManager
from kfi_calculator import KfiCalculator
from card_generator import CardGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


class EmitterPipeline:
    """Конвейер обработки эмитента от данных до публикации."""

    def __init__(self):
        self.moex_parser = MOEXBondParser()
        self.financial_manager = FinancialDataManager()
        self.kfi_calculator = KfiCalculator()
        self.card_generator = CardGenerator()
        self.emitters = load_emitters()

    def run(self, emitter_id: str, period: str = None, skip_parsing: bool = False):
        """
        Запускает полный конвейер для эмитента.

        Args:
            emitter_id: ID эмитента (например, CARMONEY)
            period: Период отчётности (например, 2024-Q4). Если None - текущий квартал
            skip_parsing: Пропустить парсинг, использовать существующие данные
        """
        logger.info(f"{'='*70}")
        logger.info(f"  КОНВЕЙЕР ОБРАБОТКИ ЭМИТЕНТА: {emitter_id}")
        logger.info(f"{'='*70}\n")

        # Шаг 1: Получение информации об эмитенте
        emitter = self._get_emitter(emitter_id)
        if not emitter:
            logger.error(f"Эмитент {emitter_id} не найден в базе")
            return None

        logger.info(f"[1/6] Эмитент: {emitter['name']}")
        logger.info(f"      Сектор: {emitter['sector']}")
        logger.info(f"      Группа: {emitter['industry_group']}\n")

        # Определяем период
        if not period:
            period = self._get_current_period()
        logger.info(f"      Период: {period}\n")

        # Шаг 2: Парсинг данных
        if not skip_parsing:
            logger.info("[2/6] Парсинг данных...")
            financial_data = self._parse_data(emitter, period)
        else:
            logger.info("[2/6] Парсинг пропущен, загружаем существующие данные...")
            financial_data = self.financial_manager.load_financial_data(emitter_id, period)

        # Шаг 3: Проверка полноты данных и ручной ввод
        logger.info("[3/6] Проверка полноты данных...")
        financial_data = self._ensure_complete_data(emitter_id, period, financial_data)

        if not financial_data:
            logger.error("Не удалось получить финансовые данные")
            return None

        # Шаг 4: Расчёт КФИ
        logger.info("[4/6] Расчёт КФИ...")
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

        # Шаг 5: Генерация карточки
        logger.info("[5/6] Генерация карточки эмитента...")
        card_path = self._generate_card(emitter_id)

        if card_path:
            logger.info(f"      HTML: {card_path}.html")
            logger.info(f"      PNG:  {card_path}.png\n")

        # Шаг 6: Генерация текста для соцсетей
        logger.info("[6/6] Генерация текста для публикации...")
        social_text = self._generate_social_text(emitter, kfi_result)

        logger.info(f"\n{'='*70}")
        logger.info("  КОНВЕЙЕР ЗАВЕРШЁН УСПЕШНО")
        logger.info(f"{'='*70}\n")

        # Возвращаем результаты
        return {
            "emitter_id": emitter_id,
            "period": period,
            "kfi_result": kfi_result,
            "card_path": card_path,
            "social_text": social_text,
        }

    def _get_emitter(self, emitter_id: str) -> Optional[Dict]:
        """Получает данные эмитента из базы."""
        for emitter in self.emitters:
            if emitter['emitter_id'] == emitter_id:
                return emitter
        return None

    def _get_current_period(self) -> str:
        """Определяет текущий отчётный период."""
        now = datetime.now()
        year = now.year
        month = now.month

        # Определяем квартал
        if month <= 3:
            quarter = "Q1"
        elif month <= 6:
            quarter = "Q2"
        elif month <= 9:
            quarter = "Q3"
        else:
            quarter = "Q4"

        return f"{year}-{quarter}"

    def _parse_data(self, emitter: Dict, period: str) -> Optional[Any]:
        """
        Парсит финансовые данные из доступных источников.

        Пытается получить данные из:
        1. MOEX API (рыночные данные)
        2. Существующие файлы (если уже загружены)
        """
        emitter_id = emitter['emitter_id']

        # Проверяем, есть ли уже данные
        existing_data = self.financial_manager.load_financial_data(emitter_id, period)
        if existing_data:
            logger.info(f"      [OK] Найдены существующие данные за {period}")
            return existing_data

        # Пытаемся получить данные с MOEX
        logger.info("      Попытка получить данные с MOEX...")
        try:
            moex_data = self.moex_parser.fetch_emitter(emitter)
            if moex_data:
                logger.info(f"      [OK] Получены данные MOEX для {len(moex_data)} облигаций")
        except Exception as e:
            logger.warning(f"      [WARN] MOEX: {e}")

        # TODO: Здесь можно добавить парсинг e-disclosure.ru
        # через edisclosure_scraper.py

        logger.info("      [WARN] Автоматический парсинг не дал полных данных")
        return None

    def _ensure_complete_data(self, emitter_id: str, period: str,
                             financial_data: Optional[Any]) -> Optional[Any]:
        """
        Проверяет полноту данных и запускает ручной ввод если нужно.
        """
        if financial_data:
            # Проверяем критические поля
            required_fields = ['revenue', 'equity', 'cfo', 'current_assets', 'current_liabilities']
            missing_fields = [f for f in required_fields if getattr(financial_data, f, None) is None]

            if not missing_fields:
                logger.info("      [OK] Все критические данные присутствуют")
                return financial_data
            else:
                logger.warning(f"      [WARN] Отсутствуют поля: {', '.join(missing_fields)}")

        # Данных нет или они неполные - запускаем ручной ввод
        logger.info("\n" + "="*70)
        logger.info("  ТРЕБУЕТСЯ РУЧНОЙ ВВОД ФИНАНСОВЫХ ДАННЫХ")
        logger.info("="*70 + "\n")

        response = input("Запустить интерактивный ввод данных? (y/n): ").strip().lower()
        if response == 'y':
            financial_data = self.financial_manager.interactive_input(emitter_id)
            return financial_data
        else:
            logger.warning("Ручной ввод пропущен. Будут использованы демо-данные.")
            return None

    def _calculate_kfi(self, emitter: Dict, financial_data: Any, period: str) -> Optional[Dict]:
        """Рассчитывает КФИ на основе финансовых данных."""
        try:
            # Конвертируем FinancialData в словарь для калькулятора
            if financial_data:
                financials_dict = {
                    'current_ratio': financial_data.current_assets / financial_data.current_liabilities
                                    if financial_data.current_assets and financial_data.current_liabilities else 1.5,
                    'quick_ratio': (financial_data.current_assets - (financial_data.inventory or 0)) / financial_data.current_liabilities
                                  if financial_data.current_assets and financial_data.current_liabilities else 1.0,
                    'cash_ratio': financial_data.cash / financial_data.current_liabilities
                                 if financial_data.cash and financial_data.current_liabilities else 0.2,
                    'icr': financial_data.operating_profit / financial_data.interest_expenses
                          if financial_data.operating_profit and financial_data.interest_expenses else 2.0,
                    'debt_ebitda': (financial_data.long_term_debt + financial_data.short_term_debt) / financial_data.operating_profit
                                  if financial_data.operating_profit else 3.5,
                    'equity_ratio': financial_data.equity / financial_data.total_assets
                                   if financial_data.equity and financial_data.total_assets else 0.3,
                    'roe': financial_data.net_income / financial_data.equity
                          if financial_data.net_income and financial_data.equity else 0.15,
                    'fcf_to_ebitda': (financial_data.cfo - financial_data.capex) / financial_data.operating_profit
                                    if financial_data.cfo and financial_data.operating_profit else 0.5,
                }
            else:
                # Демо-данные
                financials_dict = {
                    'current_ratio': 1.6, 'quick_ratio': 1.1, 'cash_ratio': 0.25, 'icr': 2.5,
                    'debt_ebitda': 3.8, 'equity_ratio': 0.35, 'roe': 0.15, 'fcf_to_ebitda': 0.75,
                }

            result = self.kfi_calculator.calculate_kfi(emitter, financials_dict, period)
            return result

        except Exception as e:
            logger.error(f"Ошибка расчёта КФИ: {e}", exc_info=True)
            return None

    def _generate_card(self, emitter_id: str) -> Optional[str]:
        """Генерирует визуальную карточку эмитента."""
        try:
            self.card_generator.generate_card(emitter_id)
            return f"output/cards/card_{emitter_id.lower()}"
        except Exception as e:
            logger.error(f"Ошибка генерации карточки: {e}")
            return None

    def _generate_social_text(self, emitter: Dict, kfi_result: Dict) -> str:
        """
        Генерирует текст для публикации в социальных сетях.

        Формат:
        - Telegram: полный разбор
        - VK/Пульс: краткая версия
        """
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

        return telegram_text

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


def interactive_mode():
    """Интерактивный режим выбора эмитента."""
    pipeline = EmitterPipeline()

    print("\n" + "="*70)
    print("  КОНВЕЙЕР ОБРАБОТКИ ЭМИТЕНТА - ИНТЕРАКТИВНЫЙ РЕЖИМ")
    print("="*70 + "\n")

    # Показываем список эмитентов
    print("Доступные эмитенты:\n")
    for i, emitter in enumerate(pipeline.emitters, 1):
        print(f"  {i}. {emitter['emitter_id']:15} — {emitter['short_name']}")

    print()
    choice = input("Выберите номер эмитента (или введите ID): ").strip()

    # Определяем эмитента
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(pipeline.emitters):
            emitter_id = pipeline.emitters[idx]['emitter_id']
        else:
            print("Неверный номер")
            return
    else:
        emitter_id = choice.upper()

    # Запрашиваем период
    period = input("Период (например 2024-Q4, Enter для текущего): ").strip() or None

    # Запускаем конвейер
    result = pipeline.run(emitter_id, period)

    if result:
        print("\n" + "="*70)
        print("  РЕЗУЛЬТАТЫ")
        print("="*70)
        print(f"\nТекст для Telegram:\n")
        print(result['social_text'])


def main():
    """Точка входа CLI."""
    if len(sys.argv) < 2:
        print("""
Использование:
  python src/pipeline.py <EMITTER_ID> [PERIOD]     — Обработать эмитента
  python src/pipeline.py --interactive              — Интерактивный режим

Примеры:
  python src/pipeline.py CARMONEY
  python src/pipeline.py GTLK 2024-Q4
  python src/pipeline.py --interactive
        """)
        return

    if sys.argv[1] == '--interactive':
        interactive_mode()
    else:
        emitter_id = sys.argv[1].upper()
        period = sys.argv[2] if len(sys.argv) > 2 else None

        pipeline = EmitterPipeline()
        pipeline.run(emitter_id, period)


if __name__ == "__main__":
    main()
