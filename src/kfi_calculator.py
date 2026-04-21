#!/usr/bin/env python3
"""
KFI Calculator v2.1
Реализация расчёта Комплексного Финансового Индекса по методологии v2.0.
Поддерживает 7 отраслевых групп, 6 блоков с весами, качественные флаги.
"""

import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


class KfiCalculator:
    """Основной класс для расчёта КФИ."""

    # Веса блоков согласно методологии
    BLOCK_WEIGHTS = {
        'a': 0.20,
        'b': 0.25,
        'c': 0.10,
        'd': 0.25,
        'e': 0.15,
        'f': 0.05
    }

    # Диапазоны категорий
    CATEGORIES = {
        (80, 101): "Надёжный",
        (60, 80): "Стабильный",
        (40, 60): "Умеренный риск",
        (20, 40): "Высокий риск",
        (0, 20): "Критический"
    }

    def __init__(self):
        self.calculations: List[Dict] = []

    def score_block_a(self, financials: Dict, industry_group: int, qualitative: Dict) -> float:
        """Block A: Платёжная устойчивость (ликвидность). 20%"""
        # Базовые метрики (примерные, в реальности из парсера РСБУ)
        current_ratio = financials.get('current_ratio', 1.5)      # ОА / КО
        quick_ratio = financials.get('quick_ratio', 1.0)
        cash_ratio = financials.get('cash_ratio', 0.3)
        icr = financials.get('icr', 2.0)                          # EBIT / % expenses

        base_score = 0.0

        if industry_group == 2:  # МФО
            nmfk1 = financials.get('nmfk1', 0.08)  # >=6% по ЦБ
            portfolio_coverage = financials.get('portfolio_coverage', 1.1)
            base_score = (
                35 * (1 if nmfk1 >= 0.06 else max(0, nmfk1 / 0.06)) +
                35 * min(100, portfolio_coverage * 80) +
                30 * min(100, icr * 30)
            )
        elif industry_group == 3:  # Лизинг
            base_score = (
                40 * min(100, icr * 40) +
                35 * min(100, financials.get('portfolio_debt_coverage', 1.0) * 70) +
                25 * min(100, cash_ratio * 200)
            )
        else:  # Стандартные группы
            base_score = (
                30 * min(100, (current_ratio - 0.5) * 40) +
                25 * min(100, quick_ratio * 80) +
                20 * min(100, cash_ratio * 300) +
                25 * min(100, icr * 35)
            )

        # Корректировка qualitative (например, disclosure_delays)
        if qualitative.get('disclosure_delays', False):
            base_score *= 0.85

        return round(min(100.0, max(0.0, base_score)), 1)

    def score_block_b(self, financials: Dict, industry_group: int, qualitative: Dict) -> float:
        """Block B: Структурная устойчивость (капитал и долг). 25%"""
        debt_ebitda = financials.get('debt_ebitda', 3.5)
        de_ratio = financials.get('de_ratio', 2.0)
        equity_ratio = financials.get('equity_ratio', 0.35)
        assets_debt_coverage = financials.get('assets_debt_coverage', 1.6)

        if industry_group == 1:  # Девелопмент — особые правила с эскроу
            escrow_adjusted = financials.get('escrow_coverage', 1.2)
            score = (
                30 * max(0, (5.0 - debt_ebitda) / 3.0 * 100) +
                25 * max(0, (4.0 - de_ratio) / 2.5 * 100) +
                25 * min(100, equity_ratio * 200) +
                20 * min(100, escrow_adjusted * 60)
            )
        elif industry_group in (2, 3):  # МФО и Лизинг — высокая долговая нагрузка норма
            score = (
                35 * max(0, (6.0 - debt_ebitda) / 4.0 * 100) +  # более мягкие нормы
                25 * min(100, (equity_ratio * 250)) +
                25 * min(100, assets_debt_coverage * 50) +
                15 * (90 if qualitative.get('owner_group_support', False) else 50)
            )
        else:
            score = (
                35 * max(0, (4.0 - debt_ebitda) / 2.5 * 100) +
                25 * max(0, (2.5 - de_ratio) / 1.8 * 100) +
                25 * min(100, equity_ratio * 220) +
                15 * min(100, assets_debt_coverage * 55)
            )

        # Owner support сильно помогает
        if qualitative.get('owner_group_support', False):
            score = min(100, score * 1.15)

        return round(min(100.0, max(10.0, score)), 1)  # минимум 10 для реализма

    def score_block_c(self, financials: Dict, qualitative: Dict) -> float:
        """Block C: Операционная эффективность (рентабельность). 10%"""
        roe = financials.get('roe', 0.15)
        roa = financials.get('roa', 0.08)
        margin = financials.get('operating_margin', 0.12)

        score = (roe * 250 + roa * 400 + margin * 300) / 3
        if not qualitative.get('no_revenue_concentration', True):
            score *= 0.85
        return round(min(100.0, max(0.0, score)), 1)

    def score_block_d(self, financials: Dict, qualitative: Dict) -> float:
        """Block D: Денежный поток (реальность прибыли). 25% — самый важный"""
        fcf_ebitda = financials.get('fcf_to_ebitda', 0.6)
        ocf_growth = financials.get('ocf_growth', 0.05)
        capex_coverage = financials.get('capex_coverage', 1.1)

        score = (
            40 * min(100, fcf_to_ebitda * 110) +
            35 * min(100, (ocf_growth + 0.2) * 250) +
            25 * min(100, capex_coverage * 70)
        )

        if qualitative.get('related_party_risk', False):
            score *= 0.75
        if financials.get('ebitda_approximated', False):
            score *= 0.9

        return round(min(100.0, max(0.0, score)), 1)

    def score_block_e(self, emitter: Dict) -> float:
        """Block E: Облигационный профиль (специфика ВДО). 15%"""
        bonds = emitter.get('bonds', [])
        qualitative = emitter.get('qualitative_flags', {})

        if not bonds:
            return 50.0

        avg_coupon = sum(b.get('coupon_rate', 0) for b in bonds) / len(bonds)
        has_offer = any(b.get('offer_date') for b in bonds)
        volume = sum(b.get('issue_volume_rub', 0) for b in bonds)

        score = 65.0
        score += 15 if avg_coupon < 16 else -10          # слишком высокая купонка = риск
        score += 10 if qualitative.get('market_maker_present', False) else -15
        score += 15 if qualitative.get('organizer_reputable', True) else -20
        score -= 20 if has_offer else 0
        score = max(20, min(95, score))

        # Размер выпуска влияет
        if volume > 5_000_000_000:
            score += 8

        return round(score, 1)

    def score_block_f(self, qualitative: Dict) -> float:
        """Block F: Качественная оценка (нефинансовые факторы). 5%"""
        negative_count = 0
        total_factors = 0

        # Основные негативные флаги
        if qualitative.get('related_party_risk', False): negative_count += 2
        if qualitative.get('litigation_risk', False): negative_count += 2
        if qualitative.get('media_negative', False): negative_count += 1.5
        if qualitative.get('management_changes', False): negative_count += 1
        if qualitative.get('cross_default_risk', False): negative_count += 2
        if qualitative.get('covenant_breach_risk', False): negative_count += 2
        if qualitative.get('esg_controversies', False): negative_count += 1
        if qualitative.get('disclosure_quality', 'standard') == 'minimal': negative_count += 1.5
        if not qualitative.get('owner_transparency', True): negative_count += 1
        if not qualitative.get('no_management_instability', True): negative_count += 1
        if not qualitative.get('clean_audit', True) and not qualitative.get('qualified_audit', True):
            negative_count += 1.5

        # Позитивные
        positive = 0
        if qualitative.get('owner_group_support', False): positive += 18
        if qualitative.get('market_maker_present', False): positive += 8
        if qualitative.get('organizer_reputable', False): positive += 10
        if qualitative.get('auditor_big4', False): positive += 12
        if qualitative.get('disclosure_quality', '') == 'high': positive += 15

        score = 75 - (negative_count * 9) + positive
        return round(max(20.0, min(100.0, score)), 1)

    def calculate_kfi(self, emitter: Dict[str, Any], financials: Dict[str, Any], period: str = "2024-Q4") -> Dict:
        """Полный расчёт КФИ для одного эмитента."""
        industry_group = emitter.get('industry_group', 7)
        qualitative = emitter.get('qualitative_flags', {})

        block_scores = {
            'block_a': self.score_block_a(financials, industry_group, qualitative),
            'block_b': self.score_block_b(financials, industry_group, qualitative),
            'block_c': self.score_block_c(financials, qualitative),
            'block_d': self.score_block_d(financials, qualitative),
            'block_e': self.score_block_e(emitter),
            'block_f': self.score_block_f(qualitative)
        }

        # Взвешенный KFI base
        kfi_base = sum(
            block_scores[f'block_{k}'] * weight
            for k, weight in [('a',0.2),('b',0.25),('c',0.1),('d',0.25),('e',0.15),('f',0.05)]
        )

        # Финальные корректировки (risk flags)
        risk_flags = {
            'bankruptcy_risk': qualitative.get('litigation_risk', False),
            'revenue_quality_risk': not qualitative.get('no_revenue_concentration', True),
            'bond_concentration_risk': len(emitter.get('bonds', [])) > 3,  # пример
            'data_missing': False,
            'young_issuer': emitter.get('founded_year', 2010) > 2018,
            'ebitda_approximated': financials.get('ebitda_approximated', False)
        }

        kfi_final = kfi_base
        if risk_flags['bankruptcy_risk']:
            kfi_final *= 0.65
        if risk_flags['revenue_quality_risk']:
            kfi_final *= 0.9

        kfi_final = round(max(5.0, min(98.0, kfi_final)), 1)

        # Категория
        category = "Критический"
        for (low, high), cat in self.CATEGORIES.items():
            if low <= kfi_final < high:
                category = cat
                break

        calculation = {
            "id": f"kfi_{emitter['emitter_id']}_{period.replace('-', '')}",
            "emitter_id": emitter['emitter_id'],
            "period": period,
            "report_date": "2025-02-15",
            "block_scores": block_scores,
            "kfi_base": round(kfi_base, 1),
            "kfi_final": kfi_final,
            "category": category,
            "risk_flags": risk_flags,
            "qualitative_adjustments": {"block_f_contribution": block_scores['block_f']},
            "verified_by": "test_engine",
            "calculated_at": datetime.now().isoformat()
        }

        self.calculations.append(calculation)
        return calculation

    def save_calculations(self, path: str = "data/calculations/test_results.json"):
        """Сохраняет результаты расчётов."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({"calculations": self.calculations, "version": "2.1", "generated": datetime.now().isoformat()}, 
                      f, ensure_ascii=False, indent=2)
        print(f"Расчёты сохранены в {path}")


# ====================== ТЕСТОВЫЕ РАСЧЁТЫ ======================
if __name__ == "__main__":
    calculator = KfiCalculator()

    # Примерные финансовые метрики (в реальности из financial_parser.py)
    test_emitters = [
        ("GTLK", 3, {  # Лизинг, сильный
            'current_ratio': 1.8, 'quick_ratio': 1.2, 'cash_ratio': 0.25, 'icr': 2.8,
            'debt_ebitda': 5.2, 'de_ratio': 4.1, 'equity_ratio': 0.28, 'assets_debt_coverage': 1.4,
            'portfolio_debt_coverage': 1.35, 'roe': 0.14, 'roa': 0.06, 'operating_margin': 0.22,
            'fcf_to_ebitda': 0.75, 'ocf_growth': 0.12, 'capex_coverage': 1.4, 'ebitda_approximated': False
        }),
        ("pkb-001", 2, {  # Коллектор МФО, средний
            'current_ratio': 1.1, 'quick_ratio': 0.9, 'cash_ratio': 0.15, 'icr': 1.4,
            'debt_ebitda': 4.8, 'de_ratio': 3.2, 'equity_ratio': 0.22, 'nmfk1': 0.09,
            'roe': 0.28, 'roa': 0.11, 'operating_margin': 0.45, 'fcf_to_ebitda': 0.95,
            'ocf_growth': -0.05, 'capex_coverage': 0.8, 'ebitda_approximated': True
        }),
        ("myasnichiy-001", 5, {  # Малый производитель, слабый
            'current_ratio': 0.9, 'quick_ratio': 0.6, 'cash_ratio': 0.08, 'icr': 1.1,
            'debt_ebitda': 6.5, 'de_ratio': 4.8, 'equity_ratio': 0.18, 'assets_debt_coverage': 1.1,
            'roe': 0.04, 'roa': 0.02, 'operating_margin': 0.07, 'fcf_to_ebitda': 0.35,
            'ocf_growth': -0.15, 'capex_coverage': 0.6, 'ebitda_approximated': True
        }),
        ("delo-001", 6, {  # Крупный транспорт, сильный
            'current_ratio': 2.1, 'quick_ratio': 1.6, 'cash_ratio': 0.45, 'icr': 4.2,
            'debt_ebitda': 2.8, 'de_ratio': 1.9, 'equity_ratio': 0.42, 'assets_debt_coverage': 2.1,
            'roe': 0.18, 'roa': 0.09, 'operating_margin': 0.19, 'fcf_to_ebitda': 0.85,
            'ocf_growth': 0.22, 'capex_coverage': 1.6, 'ebitda_approximated': False
        })
    ]

    # Загружаем emitters для получения qualitative_flags и bonds
    try:
        with open("data/emitters_corrected.json", encoding="utf-8") as f:
            emitters_data = json.load(f)
            emitters_dict = {e["emitter_id"]: e for e in emitters_data["emitters"]}
    except Exception as e:
        print("Предупреждение: emitters_corrected.json не найден, используем минимальные данные.", e)
        emitters_dict = {}

    print("=== ТЕСТОВЫЕ РАСЧЁТЫ КФИ ===\n")
    for emitter_id, group, fin in test_emitters:
        emitter = emitters_dict.get(emitter_id, {
            "emitter_id": emitter_id,
            "industry_group": group,
            "qualitative_flags": {"owner_group_support": group in (3,6), "market_maker_present": True,
                                  "organizer_reputable": True, "media_negative": False, "related_party_risk": False,
                                  "disclosure_quality": "high" if group in (6,) else "standard"}
        })

        result = calculator.calculate_kfi(emitter, fin, "2024-Q4")
        print(f"{emitter_id:12} | KFI: {result['kfi_final']:5.1f} | {result['category']:15} | "
              f"A:{result['block_scores']['block_a']:4.1f} B:{result['block_scores']['block_b']:4.1f} "
              f"F:{result['block_scores']['block_f']:4.1f}")

    calculator.save_calculations("data/calculations/test_results.json")
    print("\nГотово. Файл test_results.json создан.")