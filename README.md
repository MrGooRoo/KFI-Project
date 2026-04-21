# KFI Project — JSON Schemas (Этап 4)

## Файлы

| Файл | Описание |
|------|----------|
| `financial_parse_request.schema.json` | Вход в `financial_parser.py` — параметры эмитента и запроса |
| `financial_parse_result.schema.json`  | Выход парсера — контракт между Этапом 4 и Этапом 5 |
| `example_request_CARMONEY.json`       | Пример запроса для ПАО КарМани (группа 2, МФО) |
| `example_result_CARMONEY.json`        | Пример результата парсинга с реальными значениями |

## Принципы схемы

### Вход (FinancialParseRequest)
- `emitter_id` + `inn` — обязательные идентификаторы
- `industry_group` 1–7 — определяет нормы и нужные отраслевые поля
- `report_request.period` — формат `2025` или `2025Q3`
- `source_hints` — необязательные подсказки для ускорения поиска на e-disclosure

### Выход (FinancialParseResult)

**Три слоя данных:**

1. `statements` — сырые строки РСБУ с оригинальными кодами (1200, 2110, 4100 и т.д.)
2. `normalized_metrics` — канонические имена для kfi_calculator.py (нет зависимости от формата источника)
3. `coverage_flags` — флаги качества, часть которых напрямую активирует штрафы из методологии §4.3

**Правило null:** значение `null` означает «не найдено», не путать с нулём.
Три и более `null` в критических полях → `data_missing_penalty: true` → `КФИ × 0.90`

**Отраслевые поля** заполняются только для соответствующих групп:
- Группа 1 (Девелопмент): `escrow_balance`, `project_finance_debt`
- Группа 2 (МФО): `npl_90_plus`, `loan_loss_reserves`, `nmfk1_ratio`, `interest_income`
- Группа 3 (Лизинг): `leasing_portfolio_net`, `lease_payments_received`, `interest_income`

## Связь со следующими этапами

```
financial_parser.py  →  FinancialParseResult  →  kfi_calculator.py
       ↑                                                 ↓
  e-disclosure                               data/calculations/*.json
```

Схемы заморожены для MVP-0 (5–10 эмитентов).
Расширение схемы — только через новую minor-версию parser_version.
