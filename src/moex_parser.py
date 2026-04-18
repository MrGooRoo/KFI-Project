"""
moex_parser.py — Парсер данных MOEX ISS API для KFI-Project
Этап 3: Сбор рыночных данных по облигациям

Документация MOEX ISS API: https://iss.moex.com/iss/reference/
"""

import json
import time
import logging
from datetime import date, datetime, timedelta
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

# ─── Константы ────────────────────────────────────────────────────────────────
MOEX_BASE_URL = "https://iss.moex.com/iss"
DATA_DIR = Path(__file__).parent.parent / "data"
EMITTERS_FILE = DATA_DIR / "emitters.json"
CALC_DIR = DATA_DIR / "calculations"

REQUEST_DELAY = 0.5   # сек между запросами (соблюдаем политику MOEX)
REQUEST_TIMEOUT = 15  # сек таймаут запроса
MAX_RETRIES = 3


# ─── HTTP-клиент ──────────────────────────────────────────────────────────────
class MOEXClient:
    """Базовый HTTP-клиент для MOEX ISS API с retry и rate-limit."""

    def __init__(self, delay: float = REQUEST_DELAY, timeout: int = REQUEST_TIMEOUT):
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self.delay = delay
        self.timeout = timeout
        self._last_request_at: float = 0.0

    def _wait(self):
        elapsed = time.time() - self._last_request_at
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def get(self, url: str, params: dict = None) -> dict:
        self._wait()
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                self._last_request_at = time.time()
                return resp.json()
            except requests.RequestException as e:
                logger.warning(f"Попытка {attempt}/{MAX_RETRIES} — ошибка: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)
                else:
                    raise


# ─── Парсер облигаций ─────────────────────────────────────────────────────────
class MOEXBondParser:
    """
    Получает рыночные данные по облигациям с MOEX ISS API.

    Основные endpoints:
      /iss/engines/stock/markets/bonds/securities/{ISIN}  — статика выпуска
      /iss/engines/stock/markets/bonds/securities         — поиск по эмитенту
      /iss/engines/stock/markets/bonds/securities/{ISIN}/candles — история
    """

    def __init__(self, client: MOEXClient = None):
        self.client = client or MOEXClient()

    # ── Поиск выпусков по ИНН эмитента ────────────────────────────────────────
    def search_bonds_by_inn(self, inn: str) -> list[dict]:
        """
        Ищет все выпуски облигаций эмитента по ИНН.
        Возвращает список dict с основными параметрами выпуска.
        """
        url = f"{MOEX_BASE_URL}/securities.json"
        params = {
            "q": inn,
            "type": "stock_bonds",
            "limit": 100,
            "is_traded": 1,
        }
        data = self.client.get(url, params)
        rows = _parse_iss_table(data, "securities")
        logger.info(f"ИНН {inn}: найдено {len(rows)} выпусков")
        return rows

    # ── Получение статики по ISIN ──────────────────────────────────────────────
    def get_bond_info(self, isin: str) -> Optional[dict]:
        """
        Возвращает полный набор статических параметров выпуска:
        купон, номинал, даты, объём, тип.
        """
        url = f"{MOEX_BASE_URL}/securities/{isin}.json"
        data = self.client.get(url)

        description = _parse_iss_table(data, "description")
        if not description:
            logger.warning(f"ISIN {isin}: пустой ответ от ISS")
            return None

        info = {row["name"]: row.get("value") for row in description}

        return {
            "isin": isin,
            "name": info.get("NAME"),
            "short_name": info.get("SHORTNAME"),
            "issuer_inn": info.get("ISSUERID"),
            "face_value": _to_float(info.get("FACEVALUE")),
            "currency": info.get("FACEUNIT", "RUB"),
            "issue_volume": _to_float(info.get("ISSUESIZE")),
            "issue_volume_rub": _to_float(info.get("ISSUEVOLUME")),
            "coupon_rate": _to_float(info.get("COUPONPERCENT")),
            "coupon_value": _to_float(info.get("COUPONVALUE")),
            "coupon_frequency": _coupon_freq(info.get("COUPONPERIOD")),
            "coupon_type": info.get("COUPONTYPE"),
            "next_coupon_date": info.get("NEXTCOUPON"),
            "maturity_date": info.get("MATDATE"),
            "offer_date": info.get("OFFERDATE"),
            "board_id": info.get("BOARDID", "TQCB"),
            "listing_level": _to_int(info.get("LISTINGLEVEL")),
            "status": info.get("STATUS"),
        }

    # ── Получение рыночных данных (котировки, YTM) ─────────────────────────────
    def get_market_data(self, isin: str, board_id: str = "TQCB") -> Optional[dict]:
        """
        Возвращает текущие рыночные данные: цена, доходность, объём торгов.
        """
        url = (
            f"{MOEX_BASE_URL}/engines/stock/markets/bonds"
            f"/boards/{board_id}/securities/{isin}.json"
        )
        data = self.client.get(url)

        securities = _parse_iss_table(data, "securities")
        marketdata = _parse_iss_table(data, "marketdata")

        if not securities or not marketdata:
            # Пробуем без указания доски
            url_fallback = (
                f"{MOEX_BASE_URL}/engines/stock/markets/bonds/securities/{isin}.json"
            )
            data = self.client.get(url_fallback)
            securities = _parse_iss_table(data, "securities")
            marketdata = _parse_iss_table(data, "marketdata")

        if not securities:
            logger.warning(f"ISIN {isin}: нет котировок на MOEX")
            return None

        sec = securities[0] if securities else {}
        mkt = marketdata[0] if marketdata else {}

        return {
            "isin": isin,
            "market_price_pct": _to_float(mkt.get("LAST") or mkt.get("PREVPRICE")),
            "ytm": _to_float(mkt.get("YIELD")),
            "accrued_interest": _to_float(sec.get("ACCRUEDINT")),
            "duration": _to_float(mkt.get("DURATION")),
            "trading_volume_today_rub": _to_float(mkt.get("VALTODAY")),
            "bid": _to_float(mkt.get("BID")),
            "ask": _to_float(mkt.get("OFFER")),
            "open": _to_float(mkt.get("OPEN")),
            "high": _to_float(mkt.get("HIGH")),
            "low": _to_float(mkt.get("LOW")),
            "last": _to_float(mkt.get("LAST")),
            "prev_price": _to_float(mkt.get("PREVPRICE")),
            "fetched_at": datetime.now().isoformat(),
        }

    # ── Объём торгов за N дней ─────────────────────────────────────────────────
    def get_volume_30d(self, isin: str, days: int = 30) -> float:
        """
        Считает суммарный объём торгов за последние N дней.
        Нужно для Блока E: оценка ликвидности выпуска.
        """
        date_from = (date.today() - timedelta(days=days)).isoformat()
        date_till = date.today().isoformat()

        url = (
            f"{MOEX_BASE_URL}/engines/stock/markets/bonds"
            f"/securities/{isin}/candles.json"
        )
        params = {
            "from": date_from,
            "till": date_till,
            "interval": 24,  # дневные свечи
        }
        data = self.client.get(url, params)
        candles = _parse_iss_table(data, "candles")

        total_volume = sum(_to_float(c.get("value", 0)) for c in candles)
        logger.info(f"ISIN {isin}: объём за {days}д = {total_volume:,.0f} руб.")
        return total_volume

    # ── Спред к ОФЗ (G-spread) ────────────────────────────────────────────────
    def get_ofz_yield(self, duration_years: float) -> Optional[float]:
        """
        Получает доходность ОФЗ для расчёта G-spread.
        Использует ближайшую по дюрации ОФЗ из MOEX.
        """
        # Базовые ISIN ОФЗ по срокам для интерполяции
        OFZ_BENCHMARKS = {
            1: "SU26234RMFS6",   # ~1 год
            2: "SU26222RMFS2",   # ~2 года
            3: "SU26229RMFS8",   # ~3 года
            5: "SU26238RMFS8",   # ~5 лет
            7: "SU26240RMFS4",   # ~7 лет
            10: "SU26243RMFS8",  # ~10 лет
        }
        # Выбираем ближайший бенчмарк
        closest = min(OFZ_BENCHMARKS.keys(), key=lambda x: abs(x - duration_years))
        ofz_isin = OFZ_BENCHMARKS[closest]

        mkt = self.get_market_data(ofz_isin, board_id="TQOB")
        if mkt and mkt.get("ytm"):
            return mkt["ytm"]
        return None

    def calc_g_spread(self, bond_ytm: float, duration_years: float) -> Optional[float]:
        """Рассчитывает G-spread в базисных пунктах."""
        ofz_ytm = self.get_ofz_yield(duration_years)
        if ofz_ytm is None:
            return None
        g_spread_bps = round((bond_ytm - ofz_ytm) * 100, 1)
        return g_spread_bps

    # ── Полный сбор данных по эмитенту ────────────────────────────────────────
    def fetch_emitter(self, emitter: dict) -> dict:
        """
        Собирает все рыночные данные по эмитенту из emitters.json.
        Обновляет поля bond_market в шаблоне расчёта.

        Возвращает dict bond_market для каждого ISIN.
        """
        results = {}
        for bond in emitter.get("bonds", []):
            isin = bond["isin"]
            logger.info(f"Обрабатываем {emitter['emitter_id']} / {isin}")

            info = self.get_bond_info(isin)
            market = self.get_market_data(isin, bond.get("board_id", "TQCB"))
            volume_30d = self.get_volume_30d(isin, days=30)

            if not info and not market:
                logger.error(f"ISIN {isin}: данные недоступны")
                continue

            # Рассчитываем G-spread если есть YTM и дюрация
            g_spread = None
            if market and market.get("ytm") and market.get("duration"):
                duration_years = (market["duration"] or 365) / 365
                g_spread = self.calc_g_spread(market["ytm"], duration_years)

            # Дней до ближайшего события (погашение / оферта)
            next_date = info.get("offer_date") or info.get("maturity_date") if info else None
            days_to_next = _days_to(next_date) if next_date else None

            bond_market = {
                "market_price_pct": market.get("market_price_pct") if market else None,
                "ytm": market.get("ytm") if market else None,
                "g_spread_bps": g_spread,
                "accrued_interest": market.get("accrued_interest") if market else None,
                "duration": market.get("duration") if market else None,
                "trading_volume_today_rub": market.get("trading_volume_today_rub") if market else None,
                "trading_volume_30d_rub": volume_30d,
                "days_to_next_redemption": days_to_next,
                "next_redemption_date": next_date,
                "listing_level": info.get("listing_level") if info else None,
                "fetched_at": datetime.now().isoformat(),
            }
            results[isin] = bond_market

        return results


# ─── Утилиты ──────────────────────────────────────────────────────────────────
def _parse_iss_table(data: dict, table_name: str) -> list[dict]:
    """
    MOEX ISS возвращает данные в виде:
    { "table_name": { "columns": [...], "data": [[...], ...] } }
    Функция преобразует это в список dict.
    """
    table = data.get(table_name, {})
    columns = table.get("columns", [])
    rows = table.get("data", [])
    return [dict(zip(columns, row)) for row in rows]


def _to_float(value) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def _to_int(value) -> Optional[int]:
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def _coupon_freq(period_days) -> Optional[int]:
    """Конвертирует период купона в днях в количество выплат в год."""
    d = _to_float(period_days)
    if d is None or d <= 0:
        return None
    return round(365 / d)


def _days_to(date_str: str) -> Optional[int]:
    """Возвращает количество дней до указанной даты."""
    try:
        target = date.fromisoformat(date_str[:10])
        delta = (target - date.today()).days
        return delta if delta >= 0 else None
    except (ValueError, TypeError):
        return None


def load_emitters(path: Path = EMITTERS_FILE) -> list[dict]:
    """Загружает базу эмитентов из JSON."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("emitters", [])


def save_bond_market(emitter_id: str, isin: str, bond_market: dict):
    """
    Сохраняет данные bond_market в соответствующий файл расчёта.
    Создаёт файл если не существует (по шаблону).
    """
    CALC_DIR.mkdir(parents=True, exist_ok=True)
    year = date.today().year
    calc_file = CALC_DIR / f"{emitter_id}_{year}.json"

    if calc_file.exists():
        with open(calc_file, encoding="utf-8") as f:
            calc = json.load(f)
    else:
        # Создаём из шаблона
        template_file = DATA_DIR / "calculations" / "template.json"
        if template_file.exists():
            with open(template_file, encoding="utf-8") as f:
                calc = json.load(f)
            calc["emitter_id"] = emitter_id
            calc["isin"] = isin
            calc["calculated_at"] = datetime.now().isoformat()
        else:
            calc = {"emitter_id": emitter_id, "isin": isin}

    calc["bond_market"] = bond_market

    with open(calc_file, "w", encoding="utf-8") as f:
        json.dump(calc, f, ensure_ascii=False, indent=2)

    logger.info(f"Сохранено: {calc_file}")


# ─── CLI ──────────────────────────────────────────────────────────────────────
def run(emitter_ids: list[str] = None):
    """
    Основная функция: собирает рыночные данные по всем (или указанным) эмитентам.

    Использование:
        python moex_parser.py                     # все эмитенты
        python moex_parser.py CARMONEY SELTL      # конкретные
    """
    parser = MOEXBondParser()
    emitters = load_emitters()

    if emitter_ids:
        emitters = [e for e in emitters if e["emitter_id"] in emitter_ids]
        logger.info(f"Фильтр: {emitter_ids}. Найдено: {len(emitters)} эмитентов")

    for emitter in emitters:
        eid = emitter["emitter_id"]
        logger.info(f"═══ Начинаем: {eid} ({emitter['name']}) ═══")
        try:
            results = parser.fetch_emitter(emitter)
            for isin, bond_market in results.items():
                save_bond_market(eid, isin, bond_market)
        except Exception as e:
            logger.error(f"{eid}: критическая ошибка — {e}", exc_info=True)

    logger.info("═══ Парсинг MOEX завершён ═══")


if __name__ == "__main__":
    import sys
    ids = sys.argv[1:] if len(sys.argv) > 1 else None
    run(ids)
