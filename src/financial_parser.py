
#!/usr/bin/env python3
"""
financial_parser.py — Парсер финансовой отчётности для KFI-Project
Этап 4: Сбор данных РСБУ для расчёта КФИ (блоки A, B, C, D)

Источники:
  - e-disclosure.ru API (автоматический парсинг)
  - Ручной ввод через CLI (fallback для MVP)

Данные, которые нужно получить:
  Баланс (форма 1):  1100, 1200, 1210, 1240, 1250, 1300, 1410, 1500, 1510, 1600
  ОПУ (форма 2):     2110, 2200, 2330, 2400
  ОДДС (форма 4):    4110, 4220
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

import requests

try:
    from edisclosure_scraper import EDisclosureScraper
    SCRAPER_AVAILABLE = True
except ImportError:
    SCRAPER_AVAILABLE = False
    logger.warning("EDisclosureScraper не доступен. Используйте ручной ввод.")

# ─── Настройка логирования ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
CALC_DIR = DATA_DIR / "calculations"
EMITTERS_FILE = DATA_DIR / "emitters.json"

CALC_DIR.mkdir(parents=True, exist_ok=True)


# ─── Структура данных ────────────────────────────────────────────────────────
@dataclass
class RSBUMetrics:
    """Канонические строки РСБУ для расчёта КФИ."""

    # Баланс (форма №1)
    non_current_assets: Optional[float] = None
    current_assets: Optional[float] = None
    inventory: Optional[float] = None
    short_term_investments: Optional[float] = None
    cash: Optional[float] = None
    equity: Optional[float] = None
    long_term_debt: Optional[float] = None
    current_liabilities: Optional[float] = None
    short_term_debt: Optional[float] = None
    total_assets: Optional[float] = None

    # ОПУ (форма №2)
    revenue: Optional[float] = None
    operating_profit: Optional[float] = None
    interest_expenses: Optional[float] = None
    net_income: Optional[float] = None

    # ОДДС (форма №4)
    cfo: Optional[float] = None
    capex: Optional[float] = None

    # Предыдущий период (для динамики)
    revenue_prev: Optional[float] = None
    cfo_prev: Optional[float] = None

    # Группа 1 (Девелопмент)
    escrow_balance: Optional[float] = None
    project_finance_debt: Optional[float] = None

    # Группа 2 (МФО)
    npl_90_plus: Optional[float] = None
    loan_loss_reserves: Optional[float] = None
    nmfk1_ratio: Optional[float] = None
    interest_income: Optional[float] = None

    # Группа 3 (Лизинг)
    leasing_portfolio_net: Optional[float] = None
    lease_payments_received: Optional[float] = None
    overdue_portfolio: Optional[float] = None

    # Метаданные
    period: str = ""
    source_url: str = ""
    fetched_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ebitda_approximated: bool = True


# ─── e-disclosure.ru API ─────────────────────────────────────────────────────
class EDisclosureAPI:
    """Клиент для API e-disclosure.ru."""

    BASE_URL = "https://www.e-disclosure.ru"
    REQUEST_DELAY = 2.0
    TIMEOUT = 30

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "KFI-Project/2.0 (kfi-project@github.com)",
            "Accept": "application/json",
        })
        self._last_request = 0.0

    def _wait(self):
        elapsed = time.time() - self._last_request
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)

    def get(self, url: str, params: dict = None) -> Optional[dict]:
        self._wait()
        try:
            resp = self.session.get(url, params=params, timeout=self.TIMEOUT)
            resp.raise_for_status()
            self._last_request = time.time()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"e-disclosure API ошибка: {e}")
            return None

    def get_financial_reports(self, company_id: str) -> Optional[list]:
        """Получает список финансовых отчётов компании."""
        url = f"{self.BASE_URL}/api/v1/reports/"
        params = {"company_id": company_id, "type": "financial", "limit": 10}
        data = self.get(url, params)
        if data and "results" in data:
            return data["results"]
        return None

    def get_financial_data(self, company_id: str) -> Optional[dict]:
        """Получает агрегированные финансовые данные."""
        url = f"{self.BASE_URL}/api/v1/financial_data/"
        params = {"company_id": company_id}
        return self.get(url, params)


# ─── Парсер РСБУ из HTML-таблиц ───────────────────────────────────────────────
class RSBUParser:
    """Парсит строки РСБУ из HTML-таблиц отчётности."""

    CODE_MAP = {
        "1100": "non_current_assets", "1200": "current_assets",
        "1210": "inventory", "1240": "short_term_investments",
        "1250": "cash", "1300": "equity",
        "1410": "long_term_debt", "1500": "current_liabilities",
        "1510": "short_term_debt", "1600": "total_assets",
        "2110": "revenue", "2200": "operating_profit",
        "2330": "interest_expenses", "2400": "net_income",
        "4110": "cfo", "4220": "capex",
    }

    @classmethod
    def parse_html_table(cls, html: str) -> dict:
        """Парсит HTML-таблицу отчётности."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        result = {}

        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            code_cell = cells[0].get_text(strip=True)
            code = None
            for token in code_cell.split():
                if token.isdigit() and len(token) == 4:
                    code = token
                    break
            if code and code in cls.CODE_MAP:
                value_cell = cells[-1].get_text(strip=True).replace(" ", "").replace("\u00a0", "")
                try:
                    result[code] = float(value_cell.replace(",", ""))
                except ValueError:
                    continue
        return result


# ─── Основной парсер ──────────────────────────────────────────────────────────
class FinancialParser:
    """Основной класс для получения финансовых данных."""

    def __init__(self):
        self.api = EDisclosureAPI()

    def fetch_for_emitter(self, emitter: dict, auto_only: bool = False) -> Optional[dict]:
        """Получает финансовые данные для одного эмитента."""
        emitter_id = emitter["emitter_id"]
        disclosure_id = emitter.get("e_disclosure_id", "")
        industry_group = emitter.get("industry_group", 7)

        logger.info(f"═══ {emitter_id} ({emitter.get('name', '')}) ═══")

        financial_data = None
        if disclosure_id:
            financial_data = self._try_api(disclosure_id, emitter_id)

        if not financial_data and not auto_only:
            logger.info("Автоматический парсинг не удался. Ручной ввод...")
            financial_data = self._manual_input(emitter)

        if financial_data:
            self._save_result(emitter_id, financial_data)
            return financial_data

        logger.warning(f"Нет данных для {emitter_id}")
        return None

    def _try_api(self, disclosure_id: str, emitter_id: str) -> Optional[dict]:
        """Пробует получить данные через e-disclosure парсер."""

        # Сначала пробуем новый скрапер
        if SCRAPER_AVAILABLE:
            logger.info("  Запуск Playwright скрапера...")
            try:
                with EDisclosureScraper(headless=True) as scraper:
                    data = scraper.fetch_all_financials(disclosure_id)
                    if data and len(data) > 5:  # Проверяем что получили данные
                        logger.info(f"  [OK] Скрапер: получено {len(data)} показателей")
                        return self._normalize_scraper_data(data)
                    else:
                        logger.info("  [WARN] Скрапер: данные не найдены")
            except Exception as e:
                logger.error(f"  [ERROR] Ошибка скрапера: {e}")

        # Fallback на старый API метод
        logger.info("  Запрос к e-disclosure API...")
        reports = self.api.get_financial_reports(disclosure_id)
        if not reports:
            logger.info("  API: отчёты не найдены")
            return None

        logger.info(f"  API: найдено {len(reports)} отчётов")
        latest = reports[0]
        logger.info(f"  Последний отчёт: {latest.get('type', '')} от {latest.get('date', '')}")

        fin_data = self.api.get_financial_data(disclosure_id)
        if fin_data:
            return self._normalize_api_data(fin_data)
        return None

    def _normalize_api_data(self, raw_data: dict) -> Optional[dict]:
        metrics = RSBUMetrics()
        for code, field_name in RSBUParser.CODE_MAP.items():
            if code in raw_data:
                setattr(metrics, field_name, raw_data[code])
        return asdict(metrics)

    def _normalize_scraper_data(self, raw_data: dict) -> Optional[dict]:
        """Нормализует данные из EDisclosureScraper в формат RSBUMetrics."""
        metrics = RSBUMetrics()

        # Копируем все поля которые совпадают с RSBUMetrics
        for field in ['non_current_assets', 'current_assets', 'inventory',
                      'short_term_investments', 'cash', 'equity', 'long_term_debt',
                      'current_liabilities', 'short_term_debt', 'total_assets',
                      'revenue', 'operating_profit', 'interest_expenses', 'net_income',
                      'cfo', 'capex']:
            if field in raw_data:
                setattr(metrics, field, raw_data[field])

        # Метаданные
        metrics.period = raw_data.get('year', datetime.now().year)
        metrics.source_url = f"e-disclosure.ru (company_id: {raw_data.get('company_id', '')})"
        metrics.fetched_at = raw_data.get('fetched_at', datetime.now().isoformat())

        return asdict(metrics)

    def _manual_input(self, emitter: dict) -> Optional[dict]:
        """Интерактивный ввод данных РСБУ через CLI."""
        emitter_id = emitter["emitter_id"]
        name = emitter.get("name", "")
        industry_group = emitter.get("industry_group", 7)

        print(f"\n{'='*60}")
        print(f"  Ручной ввод РСБУ: {name} ({emitter_id})")
        print(f"  Отраслевая группа: {industry_group}")
        print(f"{'='*60}\n")
        print("Введите значения строк РСБУ (в тысячах рублей).")
        print("Оставьте пустым если значение неизвестно.\n")

        metrics = RSBUMetrics()
        metrics.period = input("Период (например: 2024-Q4): ").strip() or "2024-Q4"

        print("\n── БАЛАНС (Форма №1) ──")
        metrics.current_assets = self._input_float("1200  Оборотные активы: ")
        metrics.inventory = self._input_float("1210  Запасы: ")
        metrics.short_term_investments = self._input_float("1240  Краткосрочные фин. вложения: ")
        metrics.cash = self._input_float("1250  Денежные средства: ")
        metrics.equity = self._input_float("1300  Собственный капитал: ")
        metrics.long_term_debt = self._input_float("1410  Долгосрочные обязательства: ")
        metrics.current_liabilities = self._input_float("1500  Краткосрочные обязательства: ")
        metrics.short_term_debt = self._input_float("1510  Краткосрочные займы: ")
        metrics.total_assets = self._input_float("1600  Активы (итого): ")

        print("\n── ОТЧЁТ О ПРИБЫЛЯХ И УБЫТКАХ (Форма №2) ──")
        metrics.revenue = self._input_float("2110  Выручка: ")
        metrics.operating_profit = self._input_float("2200  Прибыль от продаж: ")
        metrics.interest_expenses = self._input_float("2330  Проценты к уплате: ")
        metrics.net_income = self._input_float("2400  Чистая прибыль: ")

        print("\n── ОТЧЁТ О ДВИЖЕНИИ ДЕНЕЖНЫХ СРЕДСТВ (Форма №4) ──")
        metrics.cfo = self._input_float("4110  Денежный поток от опер. деятельности: ")
        metrics.capex = self._input_float("4220  Инвестиции в основные средства: ")

        print("\n── ПРЕДЫДУЩИЕ ПЕРИОДЫ (для динамики) ──")
        metrics.revenue_prev = self._input_float("  Выручка t-1: ")
        metrics.cfo_prev = self._input_float("  CFO t-2: ")

        self._input_industry_fields(metrics, industry_group)

        metrics.source_url = input("\nСсылка на источник: ").strip()

        result = asdict(metrics)
        result["emitter_id"] = emitter_id
        result["industry_group"] = industry_group

        print(f"\n{'='*60}")
        print("  Введённые данные:")
        for key, value in result.items():
            if value is not None and key not in ("fetched_at",):
                print(f"    {key}: {value}")
        print(f"{'='*60}\n")

        confirm = input("Сохранить? (y/n): ").strip().lower()
        if confirm != "y":
            return None
        return result

    def _input_industry_fields(self, metrics: RSBUMetrics, group: int):
        """Вводит отраслевые поля для специфичных групп."""
        if group == 1:
            print("\n── ДЕВЕЛОПМЕНТ (Группа 1) ──")
            metrics.escrow_balance = self._input_float("  Остаток на эскроу-счетах: ")
            metrics.project_finance_debt = self._input_float("  Задолженность по проектному финансированию: ")
        elif group == 2:
            print("\n── МФО (Группа 2) ──")
            metrics.npl_90_plus = self._input_float("  Просрочка 90+ дней: ")
            metrics.loan_loss_reserves = self._input_float("  Резервы на потери по займам: ")
            metrics.nmfk1_ratio = self._input_float("  Норматив НМФК1 (доля, напр. 0.08): ")
            metrics.interest_income = self._input_float("  Процентные доходы: ")
        elif group == 3:
            print("\n── ЛИЗИНГ (Группа 3) ──")
            metrics.leasing_portfolio_net = self._input_float("  Лизинговый портфель (нетто): ")
            metrics.lease_payments_received = self._input_float("  Лизинговые платежи полученные: ")
            metrics.overdue_portfolio = self._input_float("  Просроченный портфель: ")

    @staticmethod
    def _input_float(prompt: str) -> Optional[float]:
        """Вводит число с обработкой ошибок."""
        value = input(prompt).strip()
        if not value:
            return None
        try:
            return float(value.replace(",", "").replace(" ", ""))
        except ValueError:
            logger.warning(f"  Некорректное число: {value}")
            return None

    def _save_result(self, emitter_id: str, data: dict):
        """Сохраняет результат в JSON."""
        year = datetime.now().year
        filepath = CALC_DIR / f"{emitter_id}_{year}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"Сохранено: {filepath}")


# ─── Конвертер: сырые РСБУ → финансовые коэффициенты для КФИ ─────────────────
def rsbu_to_financials(metrics: dict) -> dict:
    """Преобразует сырые строки РСБУ в финансовые коэффициенты для kfi_calculator.py."""

    def safe_div(a, b):
        if b and b != 0:
            return a / b
        return None

    ca = metrics.get("current_assets")
    cl = metrics.get("current_liabilities")
    inv = metrics.get("inventory")
    cash = metrics.get("cash")
    st_inv = metrics.get("short_term_investments")
    op_profit = metrics.get("operating_profit")
    int_exp = metrics.get("interest_expenses")
    equity = metrics.get("equity")
    lt_debt = metrics.get("long_term_debt")
    st_debt = metrics.get("short_term_debt")
    total_assets = metrics.get("total_assets")
    revenue = metrics.get("revenue")
    net_income = metrics.get("net_income")
    cfo = metrics.get("cfo")
    capex = metrics.get("capex")
    cfo_prev = metrics.get("cfo_prev")

    financials = {}

    # ── Блок A: Платёжная устойчивость ──
    financials["current_ratio"] = safe_div(ca, cl) or 1.5
    financials["quick_ratio"] = safe_div((ca or 0) - (inv or 0), cl) or 1.0
    financials["cash_ratio"] = safe_div((cash or 0) + (st_inv or 0), cl) or 0.3

    if int_exp and int_exp > 0:
        financials["icr"] = (op_profit or 0) / int_exp
    else:
        financials["icr"] = 2.0

    # МФО
    if metrics.get("nmfk1_ratio"):
        financials["nmfk1"] = metrics["nmfk1_ratio"]
    if metrics.get("loan_loss_reserves") and metrics.get("npl_90_plus"):
        financials["portfolio_coverage"] = safe_div(
            metrics["loan_loss_reserves"], metrics["npl_90_plus"]
        ) or 1.1

    # Лизинг
    if metrics.get("leasing_portfolio_net") and (lt_debt or st_debt):
        total_debt = (lt_debt or 0) + (st_debt or 0)
        financials["portfolio_debt_coverage"] = safe_div(
            metrics["leasing_portfolio_net"], total_debt
        ) or 1.0

    # ── Блок B: Структурная устойчивость ──
    total_debt = (lt_debt or 0) + (st_debt or 0)
    ebitda = op_profit or 0
    financials["ebitda_approximated"] = True

    if ebitda > 0:
        financials["debt_ebitda"] = total_debt / ebitda
    else:
        financials["debt_ebitda"] = 5.0

    financials["de_ratio"] = safe_div(total_debt, equity) or 2.0
    financials["equity_ratio"] = safe_div(equity, total_assets) or 0.35
    financials["assets_debt_coverage"] = safe_div(total_assets, total_debt) or 1.6

    if metrics.get("escrow_balance") and metrics.get("project_finance_debt"):
        financials["escrow_coverage"] = safe_div(
            metrics["escrow_balance"], metrics["project_finance_debt"]
        ) or 1.0

    # ── Блок C: Рентабельность ──
    financials["roe"] = safe_div(net_income, equity) or 0.15
    financials["roa"] = safe_div(net_income, total_assets) or 0.08
    financials["operating_margin"] = safe_div(op_profit, revenue) or 0.12

    # ── Блок D: Денежный поток ──
    if ebitda > 0:
        fcf = (cfo or 0) - abs(capex or 0)
        financials["fcf_to_ebitda"] = fcf / ebitda
    else:
        financials["fcf_to_ebitda"] = 0.3

    if cfo_prev and cfo_prev != 0:
        financials["ocf_growth"] = ((cfo or 0) - cfo_prev) / abs(cfo_prev)
    else:
        financials["ocf_growth"] = 0.05

    if capex and capex != 0:
        financials["capex_coverage"] = safe_div(cfo or 0, abs(capex)) or 1.1
    else:
        financials["capex_coverage"] = 1.1

    return financials


# ─── Загрузчик сохранённых данных ─────────────────────────────────────────────
def load_financial_data(emitter_id: str) -> Optional[dict]:
    """Загружает сохранённые финансовые данные для эмитента."""
    year = datetime.now().year
    filepath = CALC_DIR / f"{emitter_id}_{year}.json"
    if not filepath.exists():
        return None
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


# ─── CLI ──────────────────────────────────────────────────────────────────────
def run(emitter_ids: list = None):
    """Основная функция: собирает финансовые данные для эмитентов."""
    parser = FinancialParser()

    with open(EMITTERS_FILE, encoding="utf-8") as f:
        emitters = json.load(f).get("emitters", [])

    if emitter_ids:
        emitters = [e for e in emitters if e["emitter_id"] in emitter_ids]
        logger.info(f"Фильтр: {emitter_ids}. Найдено: {len(emitters)} эмитентов")

    for emitter in emitters:
        eid = emitter["emitter_id"]

        existing = load_financial_data(eid)
        if existing:
            logger.info(f"✅ {eid}: данные уже сохранены за {datetime.now().year} г.")
            continue

        result = parser.fetch_for_emitter(emitter)
        if result:
            financials = rsbu_to_financials(result)
            logger.info(f"✅ {eid}: коэффициенты рассчитаны")

    logger.info("═══ Сбор финансовых данных завершён ═══")


if __name__ == "__main__":
    import sys
    ids = sys.argv[1:] if len(sys.argv) > 1 else None
    run(ids)
