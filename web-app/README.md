# КФИ Web App — React Application

> Современный веб-интерфейс для системы анализа эмитентов ВДО

## Технологии

- **React** 19.2.3 — UI библиотека
- **TypeScript** 5.9.3 — типобезопасность
- **Tailwind CSS** 4.1.17 — стили
- **React Router** 7.14.2 — роутинг
- **Recharts** 3.8.1 — графики
- **Vite** 7.2.4 — сборщик

## Установка

```bash
# Установить зависимости
npm install

# Запустить dev сервер
npm run dev

# Собрать production
npm run build

# Предпросмотр production
npm run preview
```

## Структура

```
web-app/
├── src/
│   ├── App.tsx              # Главный компонент
│   ├── main.tsx             # Точка входа
│   ├── components/
│   │   ├── Header.tsx       # Шапка
│   │   ├── KFIBadge.tsx     # Бейдж КФИ
│   │   └── BlockBar.tsx     # Прогресс-бары
│   ├── pages/
│   │   ├── RatingPage.tsx   # Рейтинг эмитентов
│   │   ├── EmitterPage.tsx  # Страница эмитента
│   │   └── MethodologyPage.tsx # Методология
│   ├── data/
│   │   └── emitters.ts      # Данные эмитентов
│   └── utils/
│       └── cn.ts            # Утилиты
├── package.json
├── tsconfig.json
├── vite.config.ts
└── index.html
```

## Страницы

### 1. Рейтинг эмитентов (/)
- Таблица и карточки
- Фильтры по категориям
- Фильтры по отраслям
- Поиск по названию/ИНН
- Сортировка

### 2. Страница эмитента (/emitter/:id)
- Детальная информация
- 6 блоков анализа (A-F)
- Флаги рисков
- Облигации
- Графики

### 3. Методология (/methodology)
- Полное описание КФИ v2.0
- Формулы расчёта
- Отраслевые группы
- Шкала категорий

## Интеграция с Python backend

### Вариант 1: Статические данные
Данные из `src/data/emitters.ts` встроены в приложение.

### Вариант 2: API (будущее)
```typescript
// Загрузка данных из API
const response = await fetch('/api/emitters');
const emitters = await response.json();
```

## Сборка

```bash
# Production build
npm run build

# Результат в dist/
# Скопировать в output/web-app/
```

## Особенности

- ✅ Адаптивный дизайн
- ✅ Темная/светлая тема
- ✅ Анимации
- ✅ TypeScript
- ✅ SEO-friendly
- ✅ Быстрая загрузка

## Разработка

```bash
# Dev сервер с hot reload
npm run dev

# Открыть http://localhost:5173
```

## Деплой

1. Собрать production: `npm run build`
2. Скопировать `dist/` на сервер
3. Настроить веб-сервер (nginx/apache)

## Лицензия

Часть проекта КФИ — https://github.com/MrGooRoo/KFI-Project
