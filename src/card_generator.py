#!/usr/bin/env python3
"""
KFI Card Generator v3
Исправленная версия с автоматическим определением путей.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

try:
    from jinja2 import Template
    JINJA_AVAILABLE = True
except ImportError:
    JINJA_AVAILABLE = False
    print("⚠️  Jinja2 не установлен. Установите: pip install jinja2")


class CardGenerator:
    def __init__(self, output_dir: str = "output/cards"):
        # Автоматически определяем корень проекта (родитель папки src)
        self.script_dir = Path(__file__).parent
        self.root_dir = self.script_dir.parent
        print(f"🔍 Корень проекта определён как: {self.root_dir}")
        
        self.data_dir = self.root_dir / "data"
        self.output_dir = self.root_dir / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Data directory: {self.data_dir}")
        print(f"📁 Output directory: {self.output_dir}")
        
        self.category_colors = {
            "Надёжный": "#6366f1", "Стабильный": "#3b82f6", "Умеренный риск": "#f59e0b",
            "Высокий риск": "#f97316", "Критический": "#ef4444"
        }
        
        self.block_colors = {
            "block_a": "#22c55e", "block_b": "#eab308", "block_c": "#a855f7",
            "block_d": "#06b6d4", "block_e": "#ec4899", "block_f": "#8b5cf6"
        }

    def load_data(self):
        """Загружает данные с явными путями."""
        emitters_file = self.data_dir / "emitters_corrected.json"
        
        if not emitters_file.exists():
            emitters_file = self.data_dir / "emitters.json"
            if not emitters_file.exists():
                raise FileNotFoundError(f"""
Не найден файл эмитентов!
Проверенные пути:
- {self.data_dir}/emitters_corrected.json
- {self.data_dir}/emitters.json

Текущая директория данных: {self.data_dir}
Содержимое data/: {list(self.data_dir.glob('*')) if self.data_dir.exists() else 'папка не найдена'}
                """)
        
        print(f"✅ Загружаем эмитентов из: {emitters_file.name}")
        with open(emitters_file, encoding="utf-8") as f:
            emitters = {e["emitter_id"]: e for e in json.load(f)["emitters"]}
        
        calc_file = self.data_dir / "calculations" / "test_results.json"
        calculations = {}
        if calc_file.exists():
            with open(calc_file, encoding="utf-8") as f:
                calculations = {c["emitter_id"]: c for c in json.load(f)["calculations"]}
            print(f"✅ Загружено {len(calculations)} расчётов")
        else:
            print("⚠️  test_results.json не найден — будут использованы базовые значения")
        
        return emitters, calculations

    def prepare_context(self, emitter: Dict, calculation: Dict = None) -> Dict:
        if not calculation:
            calculation = {
                "kfi_final": 65.0,
                "category": "Стабильный",
                "block_scores": {"block_a": 68, "block_b": 72, "block_c": 55, "block_d": 61, "block_e": 78, "block_f": 82},
                "calculated_at": datetime.now().strftime("%d.%m.%Y")
            }
        
        flags = emitter.get("qualitative_flags", {})
        summary = {}
        for k, v in list(flags.items())[:6]:
            if isinstance(v, bool):
                summary[k.replace("_", " ").title()] = "positive" if v else "negative"
        
        return {
            "emitter": emitter,
            "kfi_final": calculation["kfi_final"],
            "category": calculation["category"],
            "category_color": self.category_colors.get(calculation["category"], "#64748b"),
            "block_scores": calculation.get("block_scores", {}),
            "block_colors": self.block_colors,
            "qualitative_summary": summary,
            "bonds": emitter.get("bonds", [])[:2],
            "notes": emitter.get("notes", "Анализ по методологии КФИ v2.1"),
            "calculated_at": calculation.get("calculated_at", datetime.now().strftime("%d.%m.%Y"))
        }

    def generate_card(self, emitter_id: str):
        if not JINJA_AVAILABLE:
            print("Установите jinja2: pip install jinja2")
            return
        
        emitters, calculations = self.load_data()
        emitter = emitters.get(emitter_id)
        calc = calculations.get(emitter_id)
        
        if not emitter:
            print(f"❌ Эмитент {emitter_id} не найден в базе")
            return
        
        context = self.prepare_context(emitter, calc)
        
        template_path = self.script_dir / "card_template.html"
        with open(template_path, encoding="utf-8") as f:
            template = Template(f.read())
        
        html = template.render(**context)
        
        output_path = self.output_dir / f"card_{emitter_id.lower()}.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"✅ Карточка для {emitter_id} сохранена → {output_path}")
        return output_path

    def generate_all(self):
        emitters, _ = self.load_data()
        print(f"Найдено {len(emitters)} эмитентов. Начинаем генерацию...\n")
        for emitter_id in list(emitters.keys()):
            self.generate_card(emitter_id)
        print(f"\n🎉 Готово! Все карточки находятся в: {self.output_dir}")


if __name__ == "__main__":
    print("🚀 Запуск генератора карточек KFI...")
    generator = CardGenerator()
    generator.generate_all()