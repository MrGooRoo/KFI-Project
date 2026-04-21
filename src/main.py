#!/usr/bin/env python3
"""
KFI Project — Main Pipeline
Запуск полного пайплайна: сбор данных → расчёт КФИ → генерация карточек
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def cmd_collect(emitter_ids=None):
    """Сбор финансовых данных (этап 4)."""
    from financial_parser import FinancialParser, rsbu_to_financials, load_financial_data
    from moex_parser import MOEXBondParser, load_emitters as load_moex_emitters

    # Финансовые данные (блоки A-D)
    parser = FinancialParser()
    emitters = load_moex_emitters()

    if emitter_ids:
        emitters = [e for e in emitters if e["emitter_id"] in emitter_ids]

    for emitter in emitters:
        eid = emitter["emitter_id"]
        existing = load_financial_data(eid)
        if existing:
            logger.info(f"✅ {eid}: финансовые данные уже есть")
            continue
        result = parser.fetch_for_emitter(emitter)
        if result:
            financials = rsbu_to_financials(result)
            logger.info(f"✅ {eid}: коэффициенты рассчитаны")

    # Рыночные данные (блок E)
    moex = MOEXBondParser()
    for emitter in emitters:
        eid = emitter["emitter_id"]
        logger.info(f"MOEX: собираем данные для {eid}...")
        try:
            results = moex.fetch_emitter(emitter)
            logger.info(f"✅ {eid}: MOEX данные сохранены")
        except Exception as e:
            logger.error(f"❌ {eid}: MOEX ошибка — {e}")

    logger.info("═══ Сбор данных завершён ═══")


def cmd_generate(emitter_ids=None):
    """Генерация карточек."""
    from card_generator import CardGenerator
    generator = CardGenerator()

    if emitter_ids:
        for eid in emitter_ids:
            generator.generate_card(eid)
    else:
        generator.generate_all()


def cmd_calculate(emitter_ids=None):
    """Расчёт КФИ без генерации карточек."""
    import json
    from kfi_calculator import KfiCalculator
    from financial_parser import load_financial_data, rsbu_to_financials
    from moex_parser import load_emitters

    calculator = KfiCalculator()
    emitters = load_emitters()

    if emitter_ids:
        emitters = [e for e in emitters if e["emitter_id"] in emitter_ids]

    for emitter in emitters:
        eid = emitter["emitter_id"]
        raw = load_financial_data(eid)
        if raw:
            financials = rsbu_to_financials(raw)
        else:
            logger.warning(f"⚠️ {eid}: нет финансовых данных, используются демо")
            financials = {
                'current_ratio': 1.6, 'quick_ratio': 1.1, 'cash_ratio': 0.25, 'icr': 2.5,
                'debt_ebitda': 3.8, 'de_ratio': 2.2, 'equity_ratio': 0.35,
                'assets_debt_coverage': 1.6, 'fcf_to_ebitda': 0.75,
                'ocf_growth': 0.08, 'capex_coverage': 1.2, 'ebitda_approximated': False,
                'roe': 0.15, 'roa': 0.08, 'operating_margin': 0.18,
            }

        result = calculator.calculate_kfi(emitter, financials, "2024-Q4")
        scores = result["block_scores"]
        print(f"{eid:15} | KFI: {result['kfi_final']:5.1f} | {result['category']:15} | "
              f"A:{scores['block_a']:5.1f} B:{scores['block_b']:5.1f} "
              f"C:{scores['block_c']:5.1f} D:{scores['block_d']:5.1f} "
              f"E:{scores['block_e']:5.1f} F:{scores['block_f']:5.1f}")

    calculator.save_calculations("data/calculations/all_results.json")
    logger.info("═══ Расчёт КФИ завершён ═══")


def cmd_full(emitter_ids=None):
    """Полный пайплайн: сбор → расчёт → карточки."""
    logger.info("🚀 Полный пайплайн KFI")
    cmd_collect(emitter_ids)
    cmd_calculate(emitter_ids)
    cmd_generate(emitter_ids)


def main():
    if len(sys.argv) < 2:
        print("""
KFI Project — Управление пайплайном

Использование:
  python main.py collect [ID1 ID2 ...]   — Сбор данных (РСБУ + MOEX)
  python main.py calculate [ID1 ...]     — Расчёт КФИ
  python main.py generate [ID1 ...]      — Генерация карточек
  python main.py full [ID1 ...]          — Полный пайплайн

Примеры:
  python main.py collect CARMONEY GTLK   — Данные для двух эмитентов
  python main.py calculate                — Расчёт для всех
  python main.py generate CARMONEY        — Карточка для Кармани
  python main.py full                     — Всё для всех
        """)
        return

    command = sys.argv[1]
    emitter_ids = sys.argv[2:] if len(sys.argv) > 2 else None

    commands = {
        "collect": cmd_collect,
        "calculate": cmd_calculate,
        "generate": cmd_generate,
        "full": cmd_full,
    }

    if command not in commands:
        print(f"❌ Неизвестная команда: {command}")
        return

    commands[command](emitter_ids)


if __name__ == "__main__":
    main()
