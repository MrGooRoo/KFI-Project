#!/usr/bin/env python3
"""
create_test_data.py — Создание тестовых финансовых данных для эмитентов
"""

import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"
FINANCIALS_DIR = DATA_DIR / "financials"
FINANCIALS_DIR.mkdir(parents=True, exist_ok=True)

# Тестовые данные для CARMONEY (МФО)
carmoney_data = {
    "emitter_id": "CARMONEY",
    "period": "2024-Q4",
    "industry_group": 2,

    # Баланс (в тысячах рублей)
    "current_assets": 1500000,
    "inventory": None,
    "short_term_investments": 100000,
    "cash": 250000,
    "equity": 800000,
    "long_term_debt": 500000,
    "current_liabilities": 700000,
    "short_term_debt": 400000,
    "total_assets": 2000000,

    # ОПУ
    "revenue": 450000,
    "operating_profit": 180000,
    "interest_expenses": 60000,
    "net_income": 120000,

    # ОДДС
    "cfo": 150000,
    "capex": 20000,

    # Предыдущие периоды
    "revenue_prev": 420000,
    "cfo_prev": 140000,

    # МФО специфичные
    "npl_90_plus": 45000,
    "loan_loss_reserves": 50000,
    "nmfk1_ratio": 0.08,
    "interest_income": 420000,

    # Лизинг
    "leasing_portfolio_net": None,
    "lease_payments_received": None,
    "overdue_portfolio": None,

    # Девелопмент
    "escrow_balance": None,
    "project_finance_debt": None,

    # Метаданные
    "source": "test_data",
    "source_url": "https://carmoney.ru/investors/",
    "entered_by": "system",
    "entered_at": datetime.now().isoformat(),
    "notes": "Тестовые данные для отладки системы"
}

# Тестовые данные для GTLK (Лизинг)
gtlk_data = {
    "emitter_id": "GTLK",
    "period": "2024-Q4",
    "industry_group": 3,

    # Баланс
    "current_assets": 5000000,
    "inventory": None,
    "short_term_investments": 500000,
    "cash": 800000,
    "equity": 3500000,
    "long_term_debt": 8000000,
    "current_liabilities": 2500000,
    "short_term_debt": 1500000,
    "total_assets": 15000000,

    # ОПУ
    "revenue": 2500000,
    "operating_profit": 800000,
    "interest_expenses": 400000,
    "net_income": 350000,

    # ОДДС
    "cfo": 900000,
    "capex": 200000,

    # Предыдущие периоды
    "revenue_prev": 2300000,
    "cfo_prev": 850000,

    # МФО
    "npl_90_plus": None,
    "loan_loss_reserves": None,
    "nmfk1_ratio": None,
    "interest_income": None,

    # Лизинг специфичные
    "leasing_portfolio_net": 12000000,
    "lease_payments_received": 2400000,
    "overdue_portfolio": 450000,

    # Девелопмент
    "escrow_balance": None,
    "project_finance_debt": None,

    # Метаданные
    "source": "test_data",
    "source_url": "https://gtlk.ru/investors/",
    "entered_by": "system",
    "entered_at": datetime.now().isoformat(),
    "notes": "Тестовые данные для отладки системы"
}

# Тестовые данные для SETL (Торговля)
setl_data = {
    "emitter_id": "SETL",
    "period": "2024-Q4",
    "industry_group": 4,

    # Баланс
    "current_assets": 3000000,
    "inventory": 800000,
    "short_term_investments": 200000,
    "cash": 400000,
    "equity": 1800000,
    "long_term_debt": 1200000,
    "current_liabilities": 1500000,
    "short_term_debt": 800000,
    "total_assets": 4500000,

    # ОПУ
    "revenue": 5000000,
    "operating_profit": 600000,
    "interest_expenses": 100000,
    "net_income": 400000,

    # ОДДС
    "cfo": 550000,
    "capex": 150000,

    # Предыдущие периоды
    "revenue_prev": 4800000,
    "cfo_prev": 520000,

    # Отраслевые (не применимо)
    "npl_90_plus": None,
    "loan_loss_reserves": None,
    "nmfk1_ratio": None,
    "interest_income": None,
    "leasing_portfolio_net": None,
    "lease_payments_received": None,
    "overdue_portfolio": None,
    "escrow_balance": None,
    "project_finance_debt": None,

    # Метаданные
    "source": "test_data",
    "source_url": "https://setl.ru/investors/",
    "entered_by": "system",
    "entered_at": datetime.now().isoformat(),
    "notes": "Тестовые данные для отладки системы"
}

# Сохраняем данные
datasets = [
    ("CARMONEY_2024-Q4.json", carmoney_data),
    ("GTLK_2024-Q4.json", gtlk_data),
    ("SETL_2024-Q4.json", setl_data),
]

for filename, data in datasets:
    filepath = FINANCIALS_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] Создан: {filepath}")

print(f"\n[OK] Создано {len(datasets)} файлов с тестовыми данными")
print(f"Директория: {FINANCIALS_DIR}")
