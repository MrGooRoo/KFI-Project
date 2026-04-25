# Инструкция по установке Tesseract OCR

## Проблема

PDF-файлы с отчётностью содержат **таблицы в виде изображений** (сканы), а не текстовые таблицы. 
Для извлечения данных из таких PDF требуется **OCR (Optical Character Recognition)**.

## Решение

### Вариант 1: Установка Tesseract OCR (рекомендуется)

1. **Скачать Tesseract для Windows**:
   - https://github.com/UB-Mannheim/tesseract/wiki
   - Скачать установщик: `tesseract-ocr-w64-setup-5.x.x.exe`

2. **Установить**:
   - Запустить установщик
   - Выбрать путь установки (по умолчанию: `C:\Program Files\Tesseract-OCR`)
   - Обязательно установить **русский язык** (Russian language pack)

3. **Добавить в PATH**:
   ```bash
   setx PATH "%PATH%;C:\Program Files\Tesseract-OCR"
   ```

4. **Проверить установку**:
   ```bash
   tesseract --version
   ```

5. **Настроить pytesseract**:
   В коде Python указать путь к tesseract.exe:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

### Вариант 2: Использование онлайн-сервисов

Если не хотите устанавливать Tesseract, можно:
1. Конвертировать PDF в текст через онлайн-сервисы (например, Adobe Acrobat Online)
2. Скачать текстовую версию отчётности с e-disclosure.ru (если доступна)
3. Использовать ручной ввод данных через `financial_data_manager.py`

### Вариант 3: Ручной ввод (текущее решение)

Конвейер уже поддерживает ручной ввод недостающих данных:

```bash
python src/standalone_pipeline.py report.pdf
```

Если данные не извлечены автоматически, система запросит их вручную.

## Статус

**Текущая реализация**:
- ✅ PyMuPDF - извлечение текста из PDF
- ✅ pdfplumber - извлечение таблиц из текстовых PDF
- ✅ pytesseract - библиотека установлена
- ❌ Tesseract OCR - **требуется установка**

**После установки Tesseract**:
- Конвейер автоматически будет использовать OCR для страниц с изображениями
- Извлечение данных из сканированных PDF будет работать

## Альтернатива: Использование готовых данных

Для тестирования можно использовать эмитентов, у которых уже есть данные:

```bash
# Эмитенты с готовыми данными
python src/pipeline.py CARMONEY
python src/pipeline.py GTLK
python src/pipeline.py SETL
```

Или ввести данные вручную:

```bash
python src/financial_data_manager.py SETLGRUPP
```

---

**Вывод**: Для полноценной работы с PDF-отчётностью (сканами) требуется установка Tesseract OCR.
