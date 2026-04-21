#!/usr/bin/env python3
"""
financial_parser.py — Полностью автоматический парсер финансовой отчётности
Этап 4: Сбор финансовых данных через bo.nalog.ru (ФНС)

Архитектура:
  1. NalogBFOClient — клиент API bo.nalog.ru (скрытый REST API ФНС)
  2. RSBUMapper — маппит строки РСБУ → метрики для kfi_calculator.py
  3. FinancialParser — оркестратор

Источники (бесплатно, без ключей):
  - bo.nalog.ru (БФО ФНС) — все строки баланса, ОПУ, ОДДС
  - MOEX ISS API — рыночные данные (moex_parser.py)

Результат: JSON-файлы в data/calculations/ для kfi_calculator.py
"""

import json
import re
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

# ─── Настройка логирования ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Пути ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"
CALC_DIR = DATA_DIR / "calculations"
CALC_DIR.mkdir(parents=True, exist_ok=True)

REQUEST_DELAY = 1.5
REQUEST_TIMEOUT = 20
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "*/*",
    "Accept-Language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
    "Host": "bo.nalog.gov.ru",
}


# ═════════════════════════════════════════════════════════════════════════════
#  1. NalogBFOClient — клиент API bo.nalog.ru
# ═════════════════════════════════════════════════════════════════════════════
#
#  Скрытый API ФНС (теневой API):
#
#  Шаг 1: Поиск организации по ИНН
#    POST https://bo.nalog.gov.ru/advanced-search/organizations/search?query={ИНН}
#    Ответ: { "content": { "id": 12345678, "name": "...", "inn": "..." } }
#
#  Шаг 2: Получение финансовой отчётности
#    GET  https://bo.nalog.gov.ru/nbo/organizations/{ID}/bfo/
#    Ответ: {
#      "period": "2024",
#      "typeCorrections": {
#        "correction": {
#          "financialResult": {
#            "current2110": 12345,   ← Выручка
#            "current2200": 5678,    ← Прибыль от продаж
#            "current2330": 123,     ← Проценты к уплате
#            "current2400": 4567,    ← Чистая прибыль
#            ...
#          },
#          "balance": {
#            "current1100": ...,     ← Внеоборотные активы
#            "current1200": ...,     ← Оборотные активы
#            "current1300": ...,     ← Собственный капитал
#            ...
#          },
#          "cashFlow": {
#            "current4110": ...,     ← CFO
#            "current4220": ...,     ← CAPEX
#            ...
#          }
#        },
#        "prevCorrections": [        ← Данные за предыдущие годы
#          { "period": "2023", ... },
#          { "period": "2022", ... }
#        ]
#      }
#    }
# ═════════════════════════════════════════════════════════════════════════════

class NalogBFOClient:
    """Клиент скрытого API bo.nalog.ru для получения финансовой отчётности."""

    BASE = "https://bo.nalog.gov.ru"

    def __init__(self, delay: float = REQUEST_DELAY):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.delay = delay
        self._last_request = 0.0

    # ── HTTP ──────────────────────────────────────────────────────────────

    def _wait(self):
        elapsed = time.time() - self._last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def _get(self, url: str, params: dict = None) -> Optional[dict]:
        self._wait()
        for attempt in range(1, 4):
            try:
                resp = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                self._last_request = time.time()
                if resp.status_code == 200:
                    return resp.json()
                logger.warning("  HTTP %s, попытка %d/3", resp.status_code, attempt)
                time.sleep(2 ** attempt)
            except (requests.RequestException, json.JSONDecodeError) as e:
                logger.warning("  Ошибка (попытка %d/3): %s", attempt, e)
                time.sleep(2 ** attempt)
        return None

    def _post(self, url: str, json_data: dict = None) -> Optional[dict]:
        self._wait()
        for attempt in range(1, 4):
            try:
                resp = self.session.post(url, json=json_data, timeout=REQUEST_TIMEOUT)
                self._last_request = time.time()
                if resp.status_code == 200:
                    return resp.json()
                logger.warning("  HTTP %s, попытка %d/3", resp.status_code, attempt)
                time.sleep(2 ** attempt)
            except (requests.RequestException, json.JSONDecodeError) as e:
                logger.warning("  Ошибка (попытка %d/3): %s", attempt, e)
                time.sleep(2 ** attempt)
        return None

    # ── Шаг 1: Поиск организации по ИНН ───────────────────────────────────

    def search_by_inn(self, inn: str) -> Optional[dict]:
        """
        Ищет организацию по ИНН.

        Возвращает:
        {
            "id": 12345678,
            "name": "ООО «Кармани»",
            "inn": "9715291160",
            "ogrn": "...",
            ...
        }
        """
        url = "{}/advanced-search/organizations/search".format(self.BASE)
        params = {"query": inn}
        logger.info("  Поиск по ИНН %s...", inn)

        data = self._post(url, json_data=params)
        if data is None:
            logger.error("  Поиск не удался")
            return None

        content = data.get("content", {})
        orgs = content if isinstance(content, list) else [content]

        if not orgs:
            logger.warning("  Организация с ИНН %s не найдена", inn)
            return None

        # Берём первый результат (обычно он точный при поиске по ИНН)
        org = orgs[0]
        org_id = org.get("id")
        logger.info("  Найдено: %s (id=%s)", org.get("name", ""), org_id)
        return org

    # ── Шаг 2: Получение финансовой отчётности ────────────────────────────

    def get_bfo(self, org_id) -> Optional[dict]:
        """
        Получает полную финансовую отчётность организации.

        Возвращает структуру с данными за все доступные годы:
        {
            "period": "2024",
            "years": {
                "2024": { "balance": {...}, "income": {...}, "cashflow": {...} },
                "2023": { ... },
                ...
            }
        }
        """
        url = "{}/nbo/organizations/{}/bfo/".format(self.BASE, org_id)
        logger.info("  Загрузка БФО (org_id=%s)...", org_id)

        data = self._get(url)
        if data is None:
            logger.error("  БФО не загружена")
            return None

        # Парсим структуру ответа API
        result = self._parse_bfo_response(data)
        if result is None:
            logger.warning("  Не удалось распарсить БФО")
            return None

        logger.info("  Доступные периоды: %s", ", ".join(result.get("years", {}).keys()))
        return result

    def _parse_bfo_response(self, data: dict) -> Optional[dict]:
        """
        Парсит ответ API bo.nalog.ru в унифицированную структуру.

        API возвращает данные в формате:
        {
          "typeCorrections": {
            "correction": {
              "financialResult": { "current2110": ..., "prev2110": ... },
              "balance": { "current1100": ..., "prev1100": ... },
              "cashFlow": { "current4110": ..., "prev4110": ... }
            },
            "prevCorrections": [
              { "period": "2023", "financialResult": {...}, ... },
              { "period": "2022", ... }
            ]
          }
        }
        """
        tc = data.get("typeCorrections", {})
        if not tc:
            return None

        current = tc.get("correction", {})
        period = data.get("period", "unknown")

        years = {}

        # Текущий год
        years[period] = self._extract_year_data(current, period)

        # Предыдущие годы
        prev_corrections = tc.get("prevCorrections", [])
        for pc in prev_corrections:
            yr = pc.get("period", "unknown")
            years[yr] = self._extract_year_data(pc, yr)

        return {
            "period": period,
            "years": years,
        }

    def _extract_year_data(self, section: dict, period: str) -> dict:
        """
        Извлекает строки РСБУ из секции за один год.

        Коды строк хранятся как ключи вида: "current2110", "prev2110" и т.д.
        Нам нужны "current..." — это данные за отчётный год.
        """
        balance = {}
        income = {}
        cashflow = {}

        # Маппинг разделов API → наши словари
        sections_map = {
            "balance": balance,
            "financialResult": income,
            "cashFlow": cashflow,
        }

        for api_key, target_dict in sections_map.items():
            section_data = section.get(api_key, {})
            for key, value in section_data.items():
                # Извлекаем числовой код строки из ключа "current2110" → 2110
                match = re.search(r"(\d{4})$", key)
                if match:
                    code = int(match.group(1))
                    # value может быть dict с полем "value" или просто числом
                    if isinstance(value, dict):
                        val = value.get("value", value.get("СумОтч"))
                    else:
                        val = value
                    if val is not None:
                        try:
                            target_dict[code] = float(val)
                        except (ValueError, TypeError):
                            pass

        return {
            "balance": balance,
            "income": income,
            "cashflow": cashflow,
        }


# ═════════════════════════════════════════════════════════════════════════════
#  2. RSBUMapper — Маппер строк РСБУ → метрики для калькулятора
# ═════════════════════════════════════════════════════════════════════════════

class RSBUMapper:
    """Преобразует строки РСБУ в расчётные метрики для kfi_calculator.py"""

    @staticmethod
    def calculate_metrics(balance: dict, income: dict, cashflow: dict,
                          prev_income: dict = None, prev_balance: dict = None,
                          prev_cashflow: dict = None) -> dict:
        """
        Вычисляет метрики из строк РСБУ.

        balance: {1100: ..., 1200: ..., 1210: ..., 1240: ..., 1250: ..., 1300: ..., 1410: ..., 1500: ..., 1510: ..., 1600: ...}
        income:  {2110: ..., 2200: ..., 2330: ..., 2400: ...}
        cashflow:{4110: ..., 4220: ...}
        """
        m = {}

        g = balance.get
        gi = income.get
        gc = cashflow.get

        # ── Блок A: Платёжная устойчивость ──
        ko = g(1500)
        if ko and ko > 0:
            m["current_ratio"] = round(g(1200, 0) / ko, 2)
            inv = g(1210, 0) or 0
            m["quick_ratio"] = round((g(1200, 0) - inv) / ko, 2)
            cash = (g(1250, 0) or 0) + (g(1240, 0) or 0)
            m["cash_ratio"] = round(cash / ko, 2)

        # ── Блок B: Структурная устойчивость ──
        lt_debt = g(1410, 0) or 0
        st_debt = g(1510, 0) or 0
        total_debt = lt_debt + st_debt
        ebitda = gi(2200)  # на MVP EBITDA ≈ прибыль от продаж

        if total_debt > 0 and ebitda and ebitda > 0:
            m["debt_ebitda"] = round(total_debt / ebitda, 2)

        if total_debt > 0 and g(1300) and g(1300) > 0:
            m["de_ratio"] = round(total_debt / g(1300), 2)

        ta = g(1600)
        eq = g(1300)
        if ta and ta > 0 and eq:
            m["equity_ratio"] = round(eq / ta, 3)

        if total_debt > 0 and ta and ta > 0:
            m["assets_debt_coverage"] = round(ta / total_debt, 2)

        # ── Блок C: Рентабельность ──
        if ebitda and abs(gi(2330, 0) or 0) > 0:
            m["icr"] = round(ebitda / abs(gi(2330, 0)), 2)

        np_ = gi(2400)
        if np_ is not None and eq and eq > 0:
            m["roe"] = round(np_ / eq, 3)

        if np_ is not None and ta and ta > 0:
            m["roa"] = round(np_ / ta, 3)

        rev = gi(2110)
        if rev and rev > 0 and ebitda is not None:
            m["operating_margin"] = round(ebitda / rev, 3)

        # ── Блок D: Денежный поток ──
        cfo = gc(4110)
        if cfo is not None and ebitda and ebitda > 0:
            capex = abs(gc(4220, 0)) if gc(4220, 0) else 0
            fcf = cfo - capex
            m["fcf_to_ebitda"] = round(fcf / ebitda, 3)

        # Динамика выручки (если есть предыдущий год)
        if prev_income and rev and prev_income.get(2110) and prev_income[2110] > 0:
            rev_growth = (rev - prev_income[2110]) / abs(prev_income[2110])
            m["revenue_growth"] = round(rev_growth, 3)

        # Динамика CFO (если есть данные 2 года назад)
        if prev_cashflow and cfo is not None:
            prev_cfo = prev_cashflow.get(4110)
            if prev_cfo is not None and prev_cfo != 0:
                cfo_growth = (cfo - prev_cfo) / abs(prev_cfo)
                m["cfo_growth"] = round(cfo_growth, 3)

        # ── Флаги ──
        m["ebitda_approximated"] = True

        critical = ["current_ratio", "debt_ebitda", "roe", "fcf_to_ebitda", "icr"]
        missing = sum(1 for f in critical if m.get(f) is None)
        m["data_missing_penalty"] = missing >= 3
        m["missing_critical_count"] = missing

        return m


# ═════════════════════════════════════════════════════════════════════════════
#  3. FinancialParser — Главный оркестратор
# ═════════════════════════════════════════════════════════════════════════════

class FinancialParser:
    """
    Полностью автоматический пайплайн:
      1. bo.nalog.ru → автоматический сбор всех строк РСБУ
      2. Расчёт метрик
      3. Сохранение в data/calculations/
    """

    def __init__(self):
        self.client = NalogBFOClient()
        self.mapper = RSBUMapper()
        self.emitters = self._load_emitters()

    def _load_emitters(self) -> list:
        f = DATA_DIR / "emitters.json"
        if not f.exists():
            logger.error("Файл %s не найден!", f)
            return []
        with open(f, encoding="utf-8") as fh:
            return json.load(fh).get("emitters", [])

    def parse_emitter(self, emitter: dict) -> Optional[dict]:
        """
        Автоматический сбор финансовой отчётности одного эмитента.

        1. Поиск по ИНН → org_id
        2. Загрузка БФО → строки РСБУ за все годы
        3. Расчёт метрик
        4. Сохранение в JSON
        """
        inn = emitter.get("inn", "")
        eid = emitter.get("emitter_id", "unknown")
        name = emitter.get("short_name", emitter.get("name", "Неизвестный"))

        print("\n" + "=" * 65)
        print("  {} ({})  ИНН: {}".format(name, eid, inn))
        print("=" * 65)

        if not inn or len(inn) not in (10, 12):
            logger.warning("  Некорректный ИНН: %s", inn)
            return None

        # Шаг 1: Найти организацию
        org = self.client.search_by_inn(inn)
        if org is None:
            logger.warning("  Организация не найдена в БФО ФНС")
            return None

        org_id = org.get("id")
        if not org_id:
            logger.warning("  Не получен ID организации")
            return None

        # Шаг 2: Загрузить финансовую отчётность
        bfo = self.client.get_bfo(org_id)
        if bfo is None:
            logger.warning("  БФО не загружена")
            return None

        years = bfo.get("years", {})
        sorted_years = sorted(years.keys(), reverse=True)

        print("\n  Доступные периоды: {}".format(", ".join(sorted_years)))

        results = []
        for year in sorted_years:
            yd = years[year]
            balance = yd.get("balance", {})
            income = yd.get("income", {})
            cashflow = yd.get("cashflow", {})

            # Данные за предыдущий год (для динамики)
            prev_data = None
            prev_income = {}
            prev_balance = {}
            prev_cashflow = {}
            for prev_yr in sorted_years:
                if prev_yr < year:
                    prev_data = years[prev_yr]
                    prev_income = prev_data.get("income", {})
                    prev_balance = prev_data.get("balance", {})
                    prev_cashflow = prev_data.get("cashflow", {})
                    break

            # Расчёт метрик
            metrics = self.mapper.calculate_metrics(
                balance, income, cashflow,
                prev_income, prev_balance, prev_cashflow,
            )

            # Сохранение
            result = {
                "emitter_id": eid,
                "inn": inn,
                "industry_group": emitter.get("industry_group", 7),
                "period": year,
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "bo.nalog.gov.ru (БФО ФНС)",
                "source_url": "https://bo.nalog.gov.ru/organization/{}/".format(inn),
                "raw_data": {
                    "balance": {str(k): v for k, v in balance.items()},
                    "income": {str(k): v for k, v in income.items()},
                    "cashflow": {str(k): v for k, v in cashflow.items()},
                },
                "calculated_metrics": metrics,
                "parser_version": "4.1-auto",
                "parsed_at": datetime.now().isoformat(),
            }

            filename = "{}_{}.json".format(eid, year)
            filepath = CALC_DIR / filename
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print("\n  {}:".format(year))
            print("     Выручка: {:,.0f}".format(income.get(2110, 0)))
            print("     Прибыль от продаж: {:,.0f}".format(income.get(2200, 0)))
            print("     Чистая прибыль: {:,.0f}".format(income.get(2400, 0)))
            print("     Активы: {:,.0f}".format(balance.get(1600, 0)))
            print("     СК: {:,.0f}".format(balance.get(1300, 0)))

            skip = {"data_missing_penalty", "missing_critical_count", "ebitda_approximated"}
            calc = [k for k, v in metrics.items() if v is not None and k not in skip]
            print("     Рассчитано метрик: {}".format(len(calc)))
            if metrics.get("data_missing_penalty"):
                print("     Штраф: {} критических показателя отсутствуют".format(
                    metrics.get("missing_critical_count")))

            results.append(result)

        return results


def run(emitter_ids: list = None):
    """
    Запуск парсера.

    python financial_parser.py              # все эмитенты
    python financial_parser.py CARMONEY     # конкретный
    python financial_parser.py CARMONEY GTLK
    """
    parser = FinancialParser()
    emitters = parser.emitters

    if emitter_ids:
        emitters = [e for e in emitters if e["emitter_id"] in emitter_ids]
        logger.info("Фильтр: %s. Найдено: %d", emitter_ids, len(emitters))

    if not emitters:
        logger.error("Эмитенты не найдены!")
        return

    results = []
    for emitter in emitters:
        try:
            result = parser.parse_emitter(emitter)
            if result:
                results.extend(result)
        except KeyboardInterrupt:
            print("\n\nПрервано пользователем.")
            break
        except Exception as e:
            logger.error("  Критическая ошибка %s: %s",
                         emitter.get("emitter_id", "?"), e, exc_info=True)

    print("\n" + "=" * 65)
    print("  Готово! Эмитентов: {}, файлов сохранено: {}".format(
        len(set(r["emitter_id"] for r in results)), len(results)))
    print("  Файлы: {}".format(CALC_DIR))
    print("=" * 65)
    return results


if __name__ == "__main__":
    import sys

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    ids = args if args else None
    run(emitter_ids=ids)
