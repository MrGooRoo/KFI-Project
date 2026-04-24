#!/usr/bin/env python3
"""
KFI Card Generator v5.0 — Реальные данные + financial_parser интеграция
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

try:
    from jinja2 import Template
    JINJA_AVAILABLE = True
except ImportError:
    JINJA_AVAILABLE = False
    print("⚠️ Установите jinja2: pip install jinja2")

try:
    from kfi_calculator import KfiCalculator
    CALCULATOR_AVAILABLE = True
except ImportError:
    CALCULATOR_AVAILABLE = False
    print("⚠️ kfi_calculator.py не найден")

try:
    from financial_parser import load_financial_data, rsbu_to_financials
    FINANCIAL_PARSER_AVAILABLE = True
except ImportError:
    FINANCIAL_PARSER_AVAILABLE = False
    print("⚠️ financial_parser.py не найден")

try:
    from moex_parser import MOEXBondParser
    MOEX_AVAILABLE = True
except ImportError:
    MOEX_AVAILABLE = False
    print("⚠️ moex_parser.py не найден")

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright не установлен. PNG не будут генерироваться.")


# ─── Mock-данные (fallback когда реальных данных нет) ────────────────────────
MOCK_FINANCIALS = {
    'current_ratio': 1.6, 'quick_ratio': 1.1, 'cash_ratio': 0.25, 'icr': 2.5,
    'debt_ebitda': 3.8, 'de_ratio': 2.2, 'equity_ratio': 0.35, 'assets_debt_coverage': 1.6,
    'fcf_to_ebitda': 0.75, 'ocf_growth': 0.08, 'capex_coverage': 1.2, 'ebitda_approximated': False,
    'roe': 0.15, 'roa': 0.08, 'operating_margin': 0.18, 'nmfk1': 0.09,
    'portfolio_debt_coverage': 1.3, 'escrow_coverage': 1.4
}


class CardGenerator:
    def __init__(self, output_dir: str = "output/cards"):
        self.script_dir = Path(__file__).parent
        self.root_dir = self.script_dir.parent
        self.data_dir = self.root_dir / "data"
        self.output_dir = self.root_dir / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.kfi_calculator = KfiCalculator() if CALCULATOR_AVAILABLE else None
        self.moex_parser = MOEXBondParser() if MOEX_AVAILABLE else None

        self.category_colors = {
            "Надёжный": "#6366f1", "Стабильный": "#3b82f6", "Умеренный риск": "#f59e0b",
            "Высокий риск": "#f97316", "Критический": "#ef4444"
        }

        self.block_descriptions = {
            "block_a": "Платёжная устойчивость",
            "block_b": "Структурная устойчивость",
            "block_c": "Рентабельность",
            "block_d": "Денежный поток",
            "block_e": "Облигационный профиль",
            "block_f": "Качественная оценка"
        }

        self.block_norms = {
            "block_a": "Ликвидность ≥1.5 | ICR ≥2.0",
            "block_b": "Debt/EBITDA ≤3.5 | D/E ≤2.0",
            "block_c": "ROE ≥15% | Маржа ≥12%",
            "block_d": "FCF/EBITDA ≥60%",
            "block_e": "Купон <16%, есть MM",
            "block_f": "Нет красных флагов"
        }

        self.flag_names = {
            "owner_group_support": "Поддержка группы",
            "auditor_big4": "Аудит Big4",
            "qualified_audit": "Квалифицированный аудит",
            "related_party_risk": "Риск связанных сторон",
            "owner_transparency": "Прозрачность собственников",
            "litigation_risk": "Судебные риски",
            "media_negative": "Негатив в СМИ",
            "management_changes": "Смена менеджмента",
            "cross_default_risk": "Риск кросс-дефолта",
            "covenant_breach_risk": "Нарушение ковенант",
            "disclosure_quality": "Качество раскрытия",
            "no_revenue_concentration": "Нет концентрации выручки",
            "no_affiliated_loans": "Нет аффилированных займов",
            "disclosure_delays": "Задержки раскрытия",
            "market_maker_present": "Есть маркет-мейкер",
            "organizer_reputable": "Надёжный организатор",
            "esg_controversies": "ESG-конфликты",
            "no_management_instability": "Стабильный менеджмент",
            "clean_audit": "Чистый аудит"
        }

    def load_emitters(self):
        """Загружает базу эмитентов."""
        emitters_file = self.data_dir / "emitters.json"
        with open(emitters_file, encoding="utf-8") as f:
            return {e["emitter_id"]: e for e in json.load(f)["emitters"]}

    def load_financials(self, emitter_id: str) -> dict:
        """
        Загружает реальные финансовые данные для эмитента.
        Приоритет: сохранённый JSON → MOEX API → mock-данные.
        """
        if FINANCIAL_PARSER_AVAILABLE:
            raw_data = load_financial_data(emitter_id)
            if raw_data:
                financials = rsbu_to_financials(raw_data)
                print(f"  [OK] Реальные данные загружены для {emitter_id}")
                return financials

        print(f"  [WARN] Нет сохранённых данных для {emitter_id} — используются демо-данные")
        return MOCK_FINANCIALS.copy()

    def enrich_block_e(self, emitter: dict) -> dict:
        """Обогащает блок E данными из MOEX API (если доступен)."""
        if not self.moex_parser or not emitter.get("bonds"):
            return emitter

        for bond in emitter["bonds"]:
            isin = bond.get("isin")
            if not isin:
                continue
            try:
                market_data = self.moex_parser.get_market_data(
                    isin, bond.get("board_id", "TQCB")
                )
                if market_data:
                    bond["ytm"] = market_data.get("ytm")
                    bond["market_price_pct"] = market_data.get("market_price_pct")
                    bond["duration"] = market_data.get("duration")
                    print(f"    [MOEX] {isin} YTM={market_data.get('ytm')}%")
            except Exception as e:
                print(f"    [ERROR] MOEX ошибка для {isin}: {e}")

        return emitter

    def get_or_calculate(self, emitter: dict) -> Dict:
        """
        Рассчитывает КФИ с реальными данными.
        """
        emitter_id = emitter.get("emitter_id", "unknown")

        # Загружаем реальные финансовые данные (блоки A-D)
        financials = self.load_financials(emitter_id)

        # Обогащаем блок E из MOEX API
        emitter = self.enrich_block_e(emitter)

        if self.kfi_calculator:
            try:
                result = self.kfi_calculator.calculate_kfi(
                    emitter, financials, "2024-Q4"
                )
                print(f"  [CALC] КФИ рассчитан: {result['kfi_final']} — {result['category']}")
                return result
            except Exception as e:
                print(f"  [ERROR] Ошибка расчёта {emitter_id}: {e}")
                return self._fallback_calculation(emitter)

        return self._fallback_calculation(emitter)

    def _fallback_calculation(self, emitter: dict) -> dict:
        """Расчёт без калькулятора (fallback)."""
        return {
            "kfi_final": 68.0, "category": "Стабильный",
            "block_scores": {
                "block_a": 65, "block_b": 70, "block_c": 58,
                "block_d": 62, "block_e": 81, "block_f": 77
            },
            "calculated_at": datetime.now().strftime("%d.%m.%Y")
        }

    def prepare_context(self, emitter: dict, calculation: dict = None) -> dict:
        if not calculation:
            calculation = self.get_or_calculate(emitter)

        flags = emitter.get("qualitative_flags", {})
        summary = {}
        for k, v in flags.items():
            russian_name = self.flag_names.get(k, k.replace("_", " ").title())
            if isinstance(v, bool):
                summary[russian_name] = "positive" if v else "negative"
            else:
                summary[russian_name] = "neutral"

        # Активные облигации
        active_bonds = []
        today = datetime.now().date()
        for b in emitter.get("bonds", []):
            status = str(b.get("status", "")).lower()
            if status in ("redeemed", "pogashen"):
                continue
            maturity_str = b.get("maturity_date")
            if maturity_str:
                try:
                    maturity_date = datetime.strptime(
                        maturity_str.split("T")[0], "%Y-%m-%d"
                    ).date()
                    if maturity_date >= today:
                        active_bonds.append(b)
                except Exception:
                    active_bonds.append(b)
            else:
                active_bonds.append(b)

        return {
            "emitter": emitter,
            "kfi_final": round(calculation.get("kfi_final", 65), 1),
            "category": calculation.get("category", "Стабильный"),
            "category_color": self.category_colors.get(
                calculation.get("category"), "#64748b"
            ),
            "block_scores": calculation.get("block_scores", {}),
            "block_descriptions": self.block_descriptions,
            "block_norms": self.block_norms,
            "qualitative_summary": summary,
            "bonds": active_bonds,
            "notes": emitter.get("notes", calculation.get("notes", "Анализ по методологии КФИ v2.1")),
            "calculated_at": calculation.get("calculated_at", datetime.now().strftime("%d.%m.%Y"))
        }

    async def generate_png(self, html_path: Path, png_path: Path):
        if not PLAYWRIGHT_AVAILABLE:
            return False
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 480, "height": 920},
                    device_scale_factor=2
                )
                page = await context.new_page()
                await page.goto(f"file://{html_path.absolute()}")
                await page.wait_for_timeout(1000)
                await page.screenshot(path=str(png_path), scale="device")
                await browser.close()
                print(f"  [PNG] Сохранён: {png_path.name}")
                return True
        except Exception as e:
            print(f"  [ERROR] Не удалось создать PNG: {e}")
            return False

    def generate_card(self, emitter_id: str):
        if not JINJA_AVAILABLE:
            print("Установите jinja2: pip install jinja2")
            return

        emitters = self.load_emitters()
        emitter = emitters.get(emitter_id)
        if not emitter:
            print(f"[ERROR] Эмитент {emitter_id} не найден")
            return

        print(f"\n{'='*50}")
        print(f"Генерация карточки: {emitter_id}")
        print(f"{'='*50}")

        calculation = self.get_or_calculate(emitter)
        context = self.prepare_context(emitter, calculation)

        template_path = self.script_dir / "card_template.html"
        with open(template_path, encoding="utf-8") as f:
            template = Template(f.read())

        html = template.render(**context)

        html_path = self.output_dir / f"card_{emitter_id.lower()}.html"
        png_path = self.output_dir / f"card_{emitter_id.lower()}.png"

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  [OK] HTML-карточка сохранена")

        if PLAYWRIGHT_AVAILABLE:
            asyncio.run(self.generate_png(html_path, png_path))

        return html_path

    def generate_all(self):
        emitters = self.load_emitters()
        print(f"Найдено {len(emitters)} эмитентов.\n")
        for emitter_id in emitters:
            self.generate_card(emitter_id)
        print(f"\n[DONE] Все карточки сохранены в: {self.output_dir}")


if __name__ == "__main__":
    print("🚀 Запуск KFI Card Generator v5.0 (реальные данные)")
    generator = CardGenerator()
    generator.generate_all()
