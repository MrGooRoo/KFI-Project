# 📐 Схема данных KFI-Project v2.0

Машиночитаемая JSON Schema находится в файле data/schema.json
Schema.md — человекочитаемое описание той же структуры.

## Структура файлов

```
data/
├── emitters.json          ← База эмитентов и выпусков облигаций
├── schema.md              ← Этот файл: описание полей
└── calculations/
    ├── template.json      ← Шаблон результата расчёта
    ├── CARMONEY_2024.json ← Расчёт КФИ для конкретного эмитента/периода
    ├── GTRK_2024.json
    └── SELTL_2024.json
```

---

## emitters.json — Поля эмитента

| Поле | Тип | Источник | Описание |
|------|-----|----------|----------|
| `emitter_id` | string | ручной | Уникальный ID (тикер/аббревиатура) |
| `name` | string | MOEX / ручной | Полное юридическое название |
| `inn` | string | ручной / ЕГРЮЛ | ИНН эмитента |
| `sector` | string | ручной | Отрасль (свободный текст) |
| `sector_profile` | enum | ручной | Профиль порогов КФИ |
| `sources.rating_agency` | string | парсинг РА | Рейтинговое агентство |
| `sources.rating_value` | string | парсинг РА | Текущий рейтинг |
| `sources.rating_outlook` | string | парсинг РА | Прогноз рейтинга |

### Допустимые значения sector_profile:
- `profile_base` — Нефинансовый бизнес (производство, торговля, IT)
- `profile_leasing` — Лизинг
- `profile_mfo` — МФО
- `profile_developer` — Девелопмент
- `profile_financial` — Финансовые посредники (факторинг, коллекторы)
- `profile_trade` - Торговля
- `profile_transport` - Транспорт

---

## emitters.json — Поля выпуска облигации

| Поле | Тип | Источник | Описание |
|------|-----|----------|----------|
| `isin` | string | MOEX ISS API | Идентификатор ценной бумаги |
| `ticker` | string | MOEX ISS API | Тикер на бирже |
| `board_id` | string | MOEX ISS API | Режим торгов (TQCB = осн. рынок) |
| `coupon_rate` | float | MOEX ISS API | Ставка купона, % годовых |
| `coupon_type` | string | MOEX ISS API | Тип купона (Фиксированный/Флоатер/...) |
| `coupon_frequency` | int | MOEX ISS API | Выплат в год |
| `next_coupon_date` | date | MOEX ISS API | Дата следующего купона |
| `offer_date` | date | MOEX ISS API | Дата оферты (null если нет) |
| `maturity_date` | date | MOEX ISS API | Дата погашения |
| `issue_volume_rub` | int | MOEX ISS API | Объём выпуска, руб. |
| `face_value` | int | MOEX ISS API | Номинал, руб. |

---

## calculations/*.json — Финансовые данные (financials)

| Поле | Тип | Источник | Форма РСБУ |
|------|-----|----------|-----------|
| `revenue` | float | e-disclosure | ОФР стр. 2110 |
| `ebitda` | float | расчёт | Прибыль от продаж + D&A |
| `net_profit` | float | e-disclosure | ОФР стр. 2400 |
| `operating_cash_flow` | float | e-disclosure | ОДДС стр. 4100 |
| `free_cash_flow` | float | расчёт | OCF − CAPEX |
| `capex` | float | e-disclosure | ОДДС стр. 4221 |
| `cash_and_equivalents` | float | e-disclosure | Баланс стр. 1250 |
| `current_assets` | float | e-disclosure | Баланс стр. 1200 |
| `current_liabilities` | float | e-disclosure | Баланс стр. 1500 |
| `total_assets` | float | e-disclosure | Баланс стр. 1600 |
| `total_debt` | float | расчёт | КК (1510) + ДК (1410) |
| `short_term_debt` | float | e-disclosure | Баланс стр. 1510 |
| `long_term_debt` | float | e-disclosure | Баланс стр. 1410 |
| `equity` | float | e-disclosure | Баланс стр. 1300 |
| `interest_expense` | float | e-disclosure | ОФР стр. 2330 |
| `accounts_receivable` | float | e-disclosure | Баланс стр. 1230 |

---

## calculations/*.json — Рыночные данные по облигации (bond_market)

| Поле | Тип | Источник | Описание |
|------|-----|----------|----------|
| `market_price_pct` | float | MOEX ISS API | Рыночная цена, % от номинала |
| `ytm` | float | MOEX ISS API | Доходность к погашению/оферте, % |
| `g_spread_bps` | float | расчёт | Спред к ОФЗ, б.п. |
| `trading_volume_30d_rub` | float | MOEX ISS API | Объём торгов за 30 дней, руб. |
| `total_bond_debt_rub` | float | MOEX ISS API | Совокупный долг по облигациям |
| `days_to_next_redemption` | int | расчёт | Дней до ближайшего погашения/оферты |
| `covenant_headroom_pct` | float | ручной | Запас по ковенантам, % |

---

## Правило «слабого звена»

- Любой блок < 20 → КФИ_итог ≤ 45
- Два и более блоков < 30 → КФИ_итог ≤ 35

## Шкала КФИ

| Диапазон | Категория | Цвет |
|----------|-----------|------|
| 80–100 | Надёжный | #4F5BD5 (Индиго) |
| 60–79 | Стабильный | #3B82F6 (Синий) |
| 40–59 | Уязвимый | #F59E0B (Янтарный) |
| 20–39 | Слабый | #F97316 (Коралловый) |
| 0–19 | Критический | #EF4444 (Красный) |
