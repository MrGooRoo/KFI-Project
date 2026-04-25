# План очистки проекта КФИ

**Дата**: 2026-04-25  
**Цель**: Удалить мусор, дубликаты и оставить только необходимое для MVP

---

## 📊 Анализ текущего состояния

### Размеры директорий
- `web-app/` — **127 MB** (React приложение с node_modules)
- `src/` — ~3400 строк кода в 12 файлах
- Документация — 20+ markdown файлов в корне и docs/

### Проблемы
1. **Дублирование**: `financial_parser.py` и `financial_parser (2).py`
2. **Временные файлы**: множество отчётов сессий (SESSION_*, FINAL_REPORT.md и т.д.)
3. **Неиспользуемые скрипты**: create_test_data.py, improved_scraper.py и др.
4. **React приложение**: 127MB, не интегрировано, есть простой web/index.html
5. **Дубли документации**: Chat_Prompts.md в корне и docs/
6. **__pycache__**: не в .gitignore
7. **Временные HTML**: page_content.html, reports_page.html в корне

---

## 🗑️ Что удалить

### 1. Временные отчёты и сессии (корень)
```
❌ FINAL_REPORT.md
❌ FINANCIAL_DATA_REPORT.md
❌ PROGRESS.md
❌ SESSION_COMPLETE.md
❌ SESSION_SUMMARY.md
❌ REACT_INTEGRATION_PLAN.md
❌ README_NEXT.md
❌ GitHub_Setup_Guide.md
❌ page_content.html
❌ reports_page.html
❌ VERIFICATION_NEEDED.md
```

### 2. Дубликаты документации
```
❌ Chat_Prompts.md (корень) — есть в docs/
```

### 3. React приложение (127MB)
```
❌ web-app/ (вся директория)
```
**Причина**: Есть рабочий web/index.html (18KB), React не интегрирован, занимает 127MB

### 4. Дублирующиеся Python файлы
```
❌ src/financial_parser (2).py — дубликат
```

### 5. Временные/тестовые скрипты
```
❌ src/create_test_data.py
❌ src/create_gtlk_estimated_data.py
❌ src/improved_scraper.py
❌ src/fetch_financial_reports.py
```
**Причина**: Одноразовые скрипты для создания тестовых данных

### 6. Кэш Python
```
❌ src/__pycache__/
```

### 7. Устаревшие расчёты
```
❌ data/calculations/CARMONEY_2026.json
❌ data/calculations/evrotrans-001_2026.json
❌ data/calculations/legenda-001_2026.json
❌ data/calculations/myasnichiy-001_2026.json
❌ data/calculations/naftatrans-001_2026.json
❌ data/calculations/pkb-001_2026.json
❌ data/calculations/whoosh-001_2026.json
❌ data/calculations/test_results.json
```
**Причина**: Старые расчёты, актуальные в all_results.json

### 8. Дубли в docs/
```
❌ docs/methodology.md — устарела, есть methodology_v2.0.md
❌ docs/changelog.md — пустой или неактуальный
```

---

## ✅ Что оставить

### Корень
```
✅ README.md — главное описание
✅ CLAUDE.md — документация для разработки
✅ .gitignore — обновить
✅ .gitattributes
```

### src/ (основной код)
```
✅ main.py — главный пайплайн
✅ kfi_calculator.py — расчётный движок
✅ card_generator.py — генератор карточек
✅ card_template.html — шаблон карточки
✅ moex_parser.py — MOEX API
✅ financial_parser.py — парсер РСБУ
✅ financial_data_manager.py — ручной ввод данных
✅ edisclosure_scraper.py — Playwright скрапер (экспериментально)
```

### data/
```
✅ emitters.json — база эмитентов
✅ schema.json — JSON Schema
✅ financials/ — все файлы (реальные данные)
✅ calculations/all_results.json — актуальные расчёты
✅ calculations/template.json — шаблон
```

### docs/
```
✅ methodology_v2.0.md — полная методология
✅ roadmap.md — дорожная карта
✅ financial_data_guide.md — гайд по данным
✅ Chat_Prompts.md — промпты
```

### web/
```
✅ index.html — рейтинг-таблица
```

### output/
```
✅ cards/ — все сгенерированные карточки
```

### schemas/
```
✅ Все файлы — JSON Schema для валидации
```

---

## 🔧 Дополнительные действия

### 1. Обновить .gitignore
```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary
*.tmp
*.log
*.bak

# Node (если понадобится в будущем)
node_modules/
package-lock.json

# Project specific
src/__pycache__/
*.html.bak
```

### 2. Очистить src/__pycache__/data/
```
❌ src/__pycache__/data/ — вложенная структура, не должна быть в кэше
```

---

## 📈 Результат после очистки

### До
- Размер: ~130+ MB
- Python файлов: 12
- Markdown файлов: 20+
- Проблемы: дубли, мусор, неясная структура

### После
- Размер: ~3-5 MB
- Python файлов: 8 (только рабочие)
- Markdown файлов: 6 (только актуальные)
- Структура: чистая, понятная, готова к MVP

---

## 🎯 Итоговая структура

```
KFI-Project/
├── README.md
├── CLAUDE.md
├── .gitignore (обновлён)
├── .gitattributes
│
├── src/
│   ├── main.py
│   ├── kfi_calculator.py
│   ├── card_generator.py
│   ├── card_template.html
│   ├── moex_parser.py
│   ├── financial_parser.py
│   ├── financial_data_manager.py
│   └── edisclosure_scraper.py
│
├── data/
│   ├── emitters.json
│   ├── schema.json
│   ├── financials/
│   │   ├── CARMONEY_2024-Q4.json
│   │   ├── GTLK_2024-Q4.json
│   │   ├── GTLK_2023-12_ESTIMATED.json
│   │   └── SETL_2024-Q4.json
│   └── calculations/
│       ├── all_results.json
│       └── template.json
│
├── docs/
│   ├── methodology_v2.0.md
│   ├── roadmap.md
│   ├── financial_data_guide.md
│   └── Chat_Prompts.md
│
├── web/
│   └── index.html
│
├── output/
│   └── cards/
│       ├── card_*.html (10 файлов)
│       └── card_*.png (10 файлов)
│
└── schemas/
    ├── example_request_CARMONEY.json
    ├── example_result_CARMONEY.json
    ├── financial_parse_request.schema.json
    └── financial_parse_result.schema.json
```

---

## ⚠️ Важно

1. **Перед удалением**: создать коммит текущего состояния
2. **React**: можно будет пересоздать позже, если понадобится
3. **Отчёты**: информация сохранена в git истории
4. **Тестовые скрипты**: можно восстановить из git при необходимости

---

## 🚀 Следующие шаги после очистки

1. Обновить CLAUDE.md с новой структурой
2. Обновить README.md
3. Проверить работоспособность: `python src/main.py calculate`
4. Создать коммит: "Очистка проекта: удалён мусор, оставлен MVP"
