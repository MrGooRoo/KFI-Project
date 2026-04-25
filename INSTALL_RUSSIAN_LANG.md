# Установка русского языка для Tesseract OCR

## Статус

✅ Tesseract OCR установлен: `C:\Program Files\Tesseract-OCR\`  
✅ Русский язык скачан: `rus.traineddata` (19 MB)  
❌ Требуется копирование с правами администратора

## Инструкция по установке

### Вариант 1: Через проводник Windows (рекомендуется)

1. Откройте проводник Windows
2. Перейдите в папку проекта: `F:\GitHub_Projects\KFI-Project\KFI-Project\`
3. Найдите файл `rus.traineddata`
4. Скопируйте его (Ctrl+C)
5. Откройте папку: `C:\Program Files\Tesseract-OCR\tessdata\`
6. Вставьте файл (Ctrl+V)
7. Подтвердите действие с правами администратора

### Вариант 2: Через командную строку (от администратора)

1. Откройте командную строку **от имени администратора**
2. Выполните команду:
   ```cmd
   copy "F:\GitHub_Projects\KFI-Project\KFI-Project\rus.traineddata" "C:\Program Files\Tesseract-OCR\tessdata\rus.traineddata"
   ```

### Вариант 3: Через PowerShell (от администратора)

1. Откройте PowerShell **от имени администратора**
2. Выполните команду:
   ```powershell
   Copy-Item "F:\GitHub_Projects\KFI-Project\KFI-Project\rus.traineddata" "C:\Program Files\Tesseract-OCR\tessdata\rus.traineddata"
   ```

## Проверка установки

После копирования файла проверьте:

```bash
ls "C:/Program Files/Tesseract-OCR/tessdata/" | grep rus
```

Должен появиться файл `rus.traineddata`.

## Настройка в коде

После установки русского языка нужно настроить pytesseract в коде:

```python
import pytesseract

# Указываем путь к tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Используем русский язык
text = pytesseract.image_to_string(image, lang='rus')
```

## Следующий шаг

После установки русского языка можно будет:
1. Добавить OCR в `enhanced_pdf_extractor.py`
2. Протестировать извлечение данных из PDF с изображениями
3. Запустить полный конвейер на реальных отчётах

---

**Файл готов к копированию**: `F:\GitHub_Projects\KFI-Project\KFI-Project\rus.traineddata`
