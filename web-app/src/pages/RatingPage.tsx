import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { EMITTERS, KFICategory, IndustryGroup, getCategoryColor, getCategoryEmoji } from '../data/emitters';
import KFIBadge from '../components/KFIBadge';
import BlockBar from '../components/BlockBar';

const CATEGORIES: KFICategory[] = ['Надёжный', 'Стабильный', 'Умеренный риск', 'Высокий риск', 'Критический'];
const INDUSTRIES: IndustryGroup[] = ['Девелопмент', 'МФО', 'Лизинг', 'Торговля', 'Производство', 'Транспорт', 'Прочие'];

const blockWeights: Record<string, string> = {
  A: '20%', B: '25%', C: '10%', D: '25%', E: '15%', F: '5%',
};

export default function RatingPage() {
  const [selectedCategory, setSelectedCategory] = useState<KFICategory | 'all'>('all');
  const [selectedIndustry, setSelectedIndustry] = useState<IndustryGroup | 'all'>('all');
  const [sortBy, setSortBy] = useState<'kfi' | 'name' | 'updated'>('kfi');
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    let list = [...EMITTERS];

    if (selectedCategory !== 'all') list = list.filter((e) => e.category === selectedCategory);
    if (selectedIndustry !== 'all') list = list.filter((e) => e.industry === selectedIndustry);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter((e) => e.name.toLowerCase().includes(q) || e.inn.includes(q));
    }

    list.sort((a, b) => {
      if (sortBy === 'kfi') return b.kfiFinal - a.kfiFinal;
      if (sortBy === 'name') return a.shortName.localeCompare(b.shortName, 'ru');
      return 0;
    });

    return list;
  }, [selectedCategory, selectedIndustry, sortBy, search]);

  const colorBadge = (cat: KFICategory) => {
    const c = getCategoryColor(cat);
    const map: Record<string, string> = {
      indigo: 'bg-indigo-50 text-indigo-700 border-indigo-200',
      blue: 'bg-blue-50 text-blue-700 border-blue-200',
      amber: 'bg-amber-50 text-amber-700 border-amber-200',
      orange: 'bg-orange-50 text-orange-700 border-orange-200',
      red: 'bg-red-50 text-red-700 border-red-200',
    };
    return map[c] ?? '';
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Hero */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-semibold border border-indigo-100">
            📊 КФИ v2.0
          </span>
          <span className="text-xs text-slate-400">Методология зафиксирована · Апрель 2026</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 leading-tight">
          Рейтинг эмитентов ВДО
        </h1>
        <p className="text-slate-500 max-w-2xl text-base">
          Кредитно-Финансовый Индекс (КФИ) — автоматизированная система скоринга эмитентов высокодоходных облигаций.
          Рассчитывается по 6 аналитическим блокам на основе публично доступных данных.
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Эмитентов в базе', value: EMITTERS.length, icon: '🏢' },
          { label: 'Верифицировано', value: EMITTERS.length, icon: '✅' },
          { label: 'Обновлено сегодня', value: 1, icon: '🔄' },
          { label: 'Ключевая ставка ЦБ', value: '21%', icon: '🏦' },
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
            <div className="text-2xl mb-1">{stat.icon}</div>
            <div className="text-2xl font-bold text-slate-900">{stat.value}</div>
            <div className="text-xs text-slate-400 mt-0.5">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Scale legend */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
        <div className="text-xs font-semibold text-slate-500 mb-3 uppercase tracking-wider">Шкала КФИ</div>
        <div className="flex flex-wrap gap-2">
          {[
            { range: '80–100', label: 'Надёжный', colors: 'bg-indigo-50 text-indigo-700 border-indigo-200', emoji: '🟦' },
            { range: '65–79', label: 'Стабильный', colors: 'bg-blue-50 text-blue-700 border-blue-200', emoji: '🔵' },
            { range: '50–64', label: 'Умеренный риск', colors: 'bg-amber-50 text-amber-700 border-amber-200', emoji: '🟡' },
            { range: '35–49', label: 'Высокий риск', colors: 'bg-orange-50 text-orange-700 border-orange-200', emoji: '🟠' },
            { range: '0–34', label: 'Критический', colors: 'bg-red-50 text-red-700 border-red-200', emoji: '🔴' },
          ].map((item) => (
            <span key={item.range} className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium ${item.colors}`}>
              {item.emoji} <span className="font-bold">{item.range}</span> · {item.label}
            </span>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Поиск по названию или ИНН..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 bg-slate-50"
            />
          </div>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'kfi' | 'name' | 'updated')}
            className="px-3 py-2 rounded-xl border border-slate-200 text-sm text-slate-700 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-300"
          >
            <option value="kfi">По КФИ (убывание)</option>
            <option value="name">По названию</option>
          </select>

          {/* View toggle */}
          <div className="flex rounded-xl border border-slate-200 overflow-hidden bg-slate-50 p-0.5 gap-0.5">
            <button
              onClick={() => setViewMode('table')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${viewMode === 'table' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
            >
              Таблица
            </button>
            <button
              onClick={() => setViewMode('cards')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${viewMode === 'cards' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
            >
              Карточки
            </button>
          </div>
        </div>

        {/* Category filters */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${selectedCategory === 'all' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'}`}
          >
            Все категории
          </button>
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat === selectedCategory ? 'all' : cat)}
              className={`px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${selectedCategory === cat ? colorBadge(cat) + ' border-current' : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'}`}
            >
              {getCategoryEmoji(cat)} {cat}
            </button>
          ))}
        </div>

        {/* Industry filters */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedIndustry('all')}
            className={`px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${selectedIndustry === 'all' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'}`}
          >
            Все отрасли
          </button>
          {INDUSTRIES.map((ind) => (
            <button
              key={ind}
              onClick={() => setSelectedIndustry(ind === selectedIndustry ? 'all' : ind)}
              className={`px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${selectedIndustry === ind ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'}`}
            >
              {ind}
            </button>
          ))}
        </div>

        <div className="text-xs text-slate-400">
          Найдено: <span className="font-semibold text-slate-600">{filtered.length}</span> из {EMITTERS.length} эмитентов
        </div>
      </div>

      {/* Results */}
      {viewMode === 'table' ? (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider w-8">#</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Эмитент</th>
                  <th className="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider w-32">КФИ</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider hidden lg:table-cell">Блоки A–F</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider hidden md:table-cell w-28">Отрасль</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider hidden sm:table-cell w-24">Обновлено</th>
                  <th className="px-5 py-3 w-16"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((emitter, idx) => (
                  <tr key={emitter.id} className="hover:bg-slate-50 transition-colors group">
                    <td className="px-5 py-4 text-sm text-slate-400 font-medium">{idx + 1}</td>
                    <td className="px-5 py-4">
                      <div className="font-semibold text-slate-900 text-sm">{emitter.shortName}</div>
                      <div className="text-xs text-slate-400 mt-0.5">ИНН: {emitter.inn}</div>
                      {emitter.flags.filter(f => f.active).length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {emitter.flags.filter(f => f.active).map(f => (
                            <span key={f.key} className="text-xs text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">{f.label.split(' ').slice(0, 2).join(' ')}</span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex flex-col items-center gap-1">
                        <KFIBadge score={emitter.kfiFinal} category={emitter.category} size="sm" showCategory={false} />
                        <span className={`text-xs font-medium ${colorBadge(emitter.category).split(' ')[1]}`}>
                          {getCategoryEmoji(emitter.category)} {emitter.category}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4 hidden lg:table-cell w-64">
                      <div className="space-y-1">
                        {emitter.blocks.map((block) => (
                          <BlockBar
                            key={block.key}
                            blockKey={block.key}
                            label={block.label.split(' ')[0]}
                            score={block.score}
                            weight={blockWeights[block.key]}
                            compact
                          />
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-4 hidden md:table-cell">
                      <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-slate-100 text-slate-600 text-xs font-medium">
                        {emitter.industry}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-xs text-slate-400 hidden sm:table-cell">{emitter.updatedAt}</td>
                    <td className="px-5 py-4">
                      <Link
                        to={`/emitter/${emitter.id}`}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 text-xs font-semibold hover:bg-indigo-100 transition-colors group-hover:bg-indigo-100"
                      >
                        Разбор
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filtered.length === 0 && (
            <div className="py-16 text-center">
              <div className="text-4xl mb-3">🔍</div>
              <div className="text-slate-500 font-medium">Эмитенты не найдены</div>
              <div className="text-slate-400 text-sm mt-1">Попробуйте изменить фильтры</div>
            </div>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((emitter, idx) => (
            <Link
              key={emitter.id}
              to={`/emitter/${emitter.id}`}
              className="block bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-slate-400">#{idx + 1}</span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 text-xs">{emitter.industry}</span>
                  </div>
                  <h3 className="font-bold text-slate-900 text-sm leading-tight">{emitter.shortName}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">ИНН: {emitter.inn}</p>
                </div>
                <KFIBadge score={emitter.kfiFinal} category={emitter.category} size="md" showCategory={false} />
              </div>

              <div className="space-y-1.5 mb-4">
                {emitter.blocks.map((block) => (
                  <BlockBar
                    key={block.key}
                    blockKey={block.key}
                    label={block.label.split(' ')[0]}
                    score={block.score}
                    weight={blockWeights[block.key]}
                    compact
                  />
                ))}
              </div>

              <div className="flex items-center justify-between">
                <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-semibold ${colorBadge(emitter.category)}`}>
                  {getCategoryEmoji(emitter.category)} {emitter.category}
                </div>
                <span className="text-xs text-slate-400">{emitter.updatedAt}</span>
              </div>

              {emitter.flags.filter(f => f.active).length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap gap-1">
                  {emitter.flags.filter(f => f.active).map(f => (
                    <span key={f.key} className="text-xs text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-100">
                      {f.label}
                    </span>
                  ))}
                </div>
              )}
            </Link>
          ))}

          {filtered.length === 0 && (
            <div className="col-span-full py-16 text-center">
              <div className="text-4xl mb-3">🔍</div>
              <div className="text-slate-500 font-medium">Эмитенты не найдены</div>
            </div>
          )}
        </div>
      )}

      {/* Disclaimer */}
      <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-xs text-slate-500 leading-relaxed">
        ⚖️ <strong>Дисклеймер:</strong> Оценки КФИ сформированы автоматически на основе публично доступных данных.
        Не является инвестиционной рекомендацией. Инвестирование в ВДО сопряжено с повышенным риском потери капитала.
        Методология: <a href="https://github.com/MrGooRoo/KFI-Project" target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">github.com/MrGooRoo/KFI-Project</a>
      </div>
    </div>
  );
}
