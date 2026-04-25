#!/usr/bin/env python3
"""
financial_data_manager.py — Менеджер финансовых данных для KFI-Project
Улучшенная система ручного ввода с валидацией и хранением

Автор: KFI-Project
Дата: 2026-04-25
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
from dataclasses import dataclass, asdict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
FINANCIALS_DIR = DATA_DIR / "financials"
EMITTERS_FILE = DATA_DIR / "emitters.json"

FINANCIALS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class FinancialData:
    """Структура финансовых данных эмитента."""

    # Идентификация
    emitter_id: str
    period: str  # Формат: "2024-Q4" или "2024-12"
    industry_group: int

    # Баланс (форма 1) - в тысячах рублей
    current_assets: Optional[float] = None
    inventory: Optional[float] = None
    short_term_investments: Optional[float] = None
    cash: Optional[float] = None
    equity: Optional[float] = None
    long_term_debt: Optional[float] = None
    current_liabilities: Optional[float] = None
    short_term_debt: Optional[float] = None
    total_assets: Optional[float] = None

    # ОПУ (форма 2) - в тысячах рублей
    revenue: Optional[float] = None
    operating_profit: Optional[float] = None
    interest_expenses: Optional[float] = None
    net_income: Optional[float] = None

    # ОДДС (форма 4) - в тысячах рублей
    cfo: Optional[float] = None  # Денежный поток от операционной деятельности
    capex: Optional[float] = None  # Капитальные затраты

    # Предыдущие периоды (для динамики)
    revenue_prev: Optional[float] = None
    cfo_prev: Optional[float] = None

    # Отраслевые показатели - МФО (группа 2)
    npl_90_plus: Optional[float] = None  # Просрочка 90+ дней
    loan_loss_reserves: Optional[float] = None  # Резервы на потери
    nmfk1_ratio: Optional[float] = None  # Норматив НМФК1
    interest_income: Optional[float] = None  # Процентные доходы

    # Отраслевые показатели - Лизинг (группа 3)
    leasing_portfolio_net: Optional[float] = None  # Лизинговый портфель
    lease_payments_received: Optional[float] = None  # Полученные платежи
    overdue_portfolio: Optional[float] = None  # Просроченный портфель

    # Отраслевые показатели - Девелопмент (группа 1)
    escrow_balance: Optional[float] = None  # Остаток на эскроу
    project_finance_debt: Optional[float] = None  # Проектное финансирование

    # Метаданные
    source: str = "manual"  # manual, edisclosure, spark, etc.
    source_url: str = ""
    entered_by: str = ""
    entered_at: str = ""
    notes: str = ""

    def __post_init__(self):
        if not self.entered_at:
            self.entered_at = datetime.now().isoformat()


class FinancialDataManager:
    """Менеджер для работы с финансовыми данными."""

    def __init__(self):
        self.emitters = self._load_emitters()

    def _load_emitters(self) -> list:
        """Загружает список эмитентов."""
        with open(EMITTERS_FILE, encoding='utf-8') as f:
            return json.load(f).get('emitters', [])

    def get_emitter(self, emitter_id: str) -> Optional[dict]:
        """Получает данные эмитента по ID."""
        for emitter in self.emitters:
            if emitter['emitter_id'] == emitter_id:
                return emitter
        return None

    def load_financial_data(self, emitter_id: str, period: str = None) -> Optional[FinancialData]:
        """
        Загружает финансовые данные эмитента.

        Args:
            emitter_id: ID эмитента
            period: Период (например "2024-Q4"). Если None - берёт последний

        Returns:
            FinancialData или None
        """
        # Ищем файлы для эмитента
        files = list(FINANCIALS_DIR.glob(f"{emitter_id}_*.json"))

        if not files:
            return None

        if period:
            # Ищем конкретный период
            target_file = FINANCIALS_DIR / f"{emitter_id}_{period}.json"
            if not target_file.exists():
                return None
            files = [target_file]
        else:
            # Берём последний файл
            files = sorted(files, reverse=True)

        with open(files[0], encoding='utf-8') as f:
            data = json.load(f)

        return FinancialData(**data)

    def save_financial_data(self, data: FinancialData):
        """Сохраняет финансовые данные."""
        filename = f"{data.emitter_id}_{data.period}.json"
        filepath = FINANCIALS_DIR / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(data), f, ensure_ascii=False, indent=2)

        logger.info(f"[OK] Сохранено: {filepath}")

    def interactive_input(self, emitter_id: str) -> Optional[FinancialData]:
        """
        Интерактивный ввод финансовых данных через CLI.

        Args:
            emitter_id: ID эмитента

        Returns:
            FinancialData или None если отменено
        """
        emitter = self.get_emitter(emitter_id)
        if not emitter:
            logger.error(f"Эмитент {emitter_id} не найден")
            return None

        name = emitter.get('name', '')
        industry_group = emitter.get('industry_group', 7)

        print(f"\n{'='*70}")
        print(f"  ВВОД ФИНАНСОВЫХ ДАННЫХ")
        print(f"  Эмитент: {name} ({emitter_id})")
        print(f"  Отраслевая группа: {industry_group}")
        print(f"{'='*70}\n")

        # Период
        period = input("Период (например 2024-Q4 или 2024-12): ").strip()
        if not period:
            print("Отменено")
            return None

        # Проверяем существующие данные
        existing = self.load_financial_data(emitter_id, period)
        if existing:
            print(f"\n[!] Данные за {period} уже существуют")
            overwrite = input("Перезаписать? (y/n): ").strip().lower()
            if overwrite != 'y':
                return None

        data = FinancialData(
            emitter_id=emitter_id,
            period=period,
            industry_group=industry_group
        )

        print("\nВведите значения в ТЫСЯЧАХ рублей.")
        print("Оставьте пустым если значение неизвестно.\n")

        # Баланс
        print("── БАЛАНС (Форма №1) ──")
        data.current_assets = self._input_float("1200  Оборотные активы: ")
        data.inventory = self._input_float("1210  Запасы: ")
        data.short_term_investments = self._input_float("1240  Краткосрочные фин. вложения: ")
        data.cash = self._input_float("1250  Денежные средства: ")
        data.equity = self._input_float("1300  Собственный капитал: ")
        data.long_term_debt = self._input_float("1410  Долгосрочные обязательства: ")
        data.current_liabilities = self._input_float("1500  Краткосрочные обязательства: ")
        data.short_term_debt = self._input_float("1510  Краткосрочные займы: ")
        data.total_assets = self._input_float("1600  Активы (итого): ")

        # ОПУ
        print("\n── ОТЧЁТ О ПРИБЫЛЯХ И УБЫТКАХ (Форма №2) ──")
        data.revenue = self._input_float("2110  Выручка: ")
        data.operating_profit = self._input_float("2200  Прибыль от продаж: ")
        data.interest_expenses = self._input_float("2330  Проценты к уплате: ")
        data.net_income = self._input_float("2400  Чистая прибыль: ")

        # ОДДС
        print("\n── ОТЧЁТ О ДВИЖЕНИИ ДЕНЕЖНЫХ СРЕДСТВ (Форма №4) ──")
        data.cfo = self._input_float("4110  Денежный поток от опер. деятельности: ")
        data.capex = self._input_float("4220  Инвестиции в основные средства: ")

        # Предыдущие периоды
        print("\n── ПРЕДЫДУЩИЕ ПЕРИОДЫ (для динамики) ──")
        data.revenue_prev = self._input_float("  Выручка предыдущего периода: ")
        data.cfo_prev = self._input_float("  CFO предыдущего периода: ")

        # Отраслевые показатели
        self._input_industry_specific(data, industry_group)

        # Метаданные
        print("\n── МЕТАДАННЫЕ ──")
        data.source_url = input("Ссылка на источник: ").strip()
        data.entered_by = input("Кто вводит данные: ").strip() or "unknown"
        data.notes = input("Примечания: ").strip()

        # Показываем сводку
        self._print_summary(data)

        # Подтверждение
        confirm = input("\nСохранить данные? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Отменено")
            return None

        self.save_financial_data(data)
        return data

    def _input_industry_specific(self, data: FinancialData, group: int):
        """Вводит отраслевые показатели."""
        if group == 1:  # Девелопмент
            print("\n── ДЕВЕЛОПМЕНТ (Группа 1) ──")
            data.escrow_balance = self._input_float("  Остаток на эскроу-счетах: ")
            data.project_finance_debt = self._input_float("  Задолженность по проектному финансированию: ")

        elif group == 2:  # МФО
            print("\n── МФО (Группа 2) ──")
            data.npl_90_plus = self._input_float("  Просрочка 90+ дней: ")
            data.loan_loss_reserves = self._input_float("  Резервы на потери по займам: ")
            data.nmfk1_ratio = self._input_float("  Норматив НМФК1 (доля, например 0.08): ")
            data.interest_income = self._input_float("  Процентные доходы: ")

        elif group == 3:  # Лизинг
            print("\n── ЛИЗИНГ (Группа 3) ──")
            data.leasing_portfolio_net = self._input_float("  Лизинговый портфель (нетто): ")
            data.lease_payments_received = self._input_float("  Лизинговые платежи полученные: ")
            data.overdue_portfolio = self._input_float("  Просроченный портфель: ")

    @staticmethod
    def _input_float(prompt: str) -> Optional[float]:
        """Вводит число с обработкой ошибок."""
        value = input(prompt).strip()
        if not value:
            return None
        try:
            # Убираем пробелы и запятые
            value = value.replace(' ', '').replace(',', '.')
            return float(value)
        except ValueError:
            logger.warning(f"  [!] Некорректное число: {value}")
            return None

    def _print_summary(self, data: FinancialData):
        """Выводит сводку введённых данных."""
        print(f"\n{'='*70}")
        print("  СВОДКА ВВЕДЁННЫХ ДАННЫХ")
        print(f"{'='*70}")

        d = asdict(data)
        sections = {
            'Баланс': ['current_assets', 'cash', 'equity', 'total_assets',
                      'long_term_debt', 'current_liabilities'],
            'ОПУ': ['revenue', 'operating_profit', 'interest_expenses', 'net_income'],
            'ОДДС': ['cfo', 'capex'],
        }

        for section, fields in sections.items():
            print(f"\n{section}:")
            for field in fields:
                value = d.get(field)
                if value is not None:
                    print(f"  {field}: {value:,.0f}")

        print(f"\n{'='*70}")

    def list_available_data(self, emitter_id: str = None):
        """Выводит список доступных финансовых данных."""
        if emitter_id:
            files = list(FINANCIALS_DIR.glob(f"{emitter_id}_*.json"))
        else:
            files = list(FINANCIALS_DIR.glob("*.json"))

        if not files:
            print("Нет сохранённых финансовых данных")
            return

        print(f"\nДоступные финансовые данные ({len(files)}):")
        for f in sorted(files):
            print(f"  - {f.name}")


def main():
    """CLI интерфейс."""
    import sys

    manager = FinancialDataManager()

    if len(sys.argv) < 2:
        print("Использование:")
        print("  python financial_data_manager.py <emitter_id>  - ввод данных")
        print("  python financial_data_manager.py list          - список данных")
        print("  python financial_data_manager.py list <id>     - данные эмитента")
        return

    command = sys.argv[1]

    if command == "list":
        emitter_id = sys.argv[2] if len(sys.argv) > 2 else None
        manager.list_available_data(emitter_id)
    else:
        # Ввод данных
        emitter_id = command
        manager.interactive_input(emitter_id)


if __name__ == "__main__":
    main()
