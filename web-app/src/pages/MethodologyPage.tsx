import { Link } from 'react-router-dom';

const blocks = [
  {
    key: 'A',
    name: 'Платёжная устойчивость',
    weight: '20%',
    question: 'Может ли платить прямо сейчас?',
    color: 'from-indigo-500 to-blue-500',
    bg: 'bg-indigo-50',
    text: 'text-indigo-700',
    border: 'border-indigo-200',
    metrics: ['Коэффициент текущей ликвидности (норма 1.5–2.5)', 'Коэффициент быстрой ликвидности (≥1.0)', 'Абсолютная ликвидность (≥0.2)', 'Покрытие процентов ICR (≥2.0)'],
    note: 'Провал блока A → автоматический кэп КФИ ≤ 40',
  },
  {
    key: 'B',
    name: 'Структурная устойчивость',
    weight: '25%',
    question: 'Устойчива ли структура финансирования?',
    color: 'from-blue-500 to-cyan-500',
    bg: 'bg-blue-50',
    text: 'text-blue-700',
    border: 'border-blue-200',
    metrics: ['Debt/EBITDA (≤3.5)', 'Долг/Собственный капитал D/E (≤2.0)', 'Доля СК в пассивах (≥30%)', 'Покрытие долга активами (≥1.5)'],
    note: 'Провал блока B → автоматический кэп КФИ ≤ 40',
  },
  {
    key: 'C',
    name: 'Рентабельность',
    weight: '10%',
    question: 'Зарабатывает ли бизнес?',
    color: 'from-emerald-500 to-teal-500',
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    border: 'border-emerald-200',
    metrics: ['EBITDA Margin (>20% — отлично)', 'ROE (>20% — отлично)', 'ROA (информационно)'],
    note: 'Санитарный минимум: убыточный бизнес не получает высокий КФИ',
  },
  {
    key: 'D',
    name: 'Денежный поток',
    weight: '25%',
    question: 'Реальны ли эти заработки?',
    color: 'from-violet-500 to-purple-600',
    bg: 'bg-violet-50',
    text: 'text-violet-700',
    border: 'border-violet-200',
    metrics: ['CFO/Чистая прибыль (≥0.8)', 'FCF свободный денежный поток', 'CFO Margin (>10% — норма)', 'Динамика CFO год к году'],
    note: 'Провал блока D → автоматический кэп КФИ ≤ 40',
  },
  {
    key: 'E',
    name: 'Облигационный профиль',
    weight: '15%',
    question: 'Безопасна ли именно эта облигация?',
    color: 'from-amber-500 to-orange-500',
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    border: 'border-amber-200',
    metrics: ['Спред YTM к ключевой ставке ЦБ', 'Срок до погашения/оферты', 'Дневной объём торгов (ликвидность)', 'История выплат купонов/оферт'],
    note: 'Уникальный блок — оценивает конкретный выпуск, а не только компанию',
  },
  {
    key: 'F',
    name: 'Качественная оценка',
    weight: '5%',
    question: 'Можно ли доверять компании?',
    color: 'from-rose-500 to-pink-500',
    bg: 'bg-rose-50',
    text: 'text-rose-700',
    border: 'border-rose-200',
    metrics: ['Арбитражные и уголовные дела', 'Раскрытие информации на e-disclosure', 'Структура собственности', 'Публичный фон (новости, репутация)'],
    note: 'Всегда верифицируется редактором вручную',
  },
];

const corrections = [
  { rule: '1', title: 'Жёсткий кэп при критическом блоке', desc: 'Если A, B или D < 20 баллов → КФИ ≤ 40 (независимо от остальных блоков)', severity: 'critical' },
  { rule: '2', title: 'Штраф за два слабых блока', desc: 'Если два любых блока < 35 баллов → КФИ × 0.85 (штраф 15%)', severity: 'high' },
  { rule: '3', title: 'Флаг bankruptcy_risk', desc: 'Иски о банкротстве или уголовные дела → КФИ ≤ 30', severity: 'critical' },
  { rule: '4', title: 'Флаг revenue_quality_risk', desc: 'Рост выручки > 50% при падении CFO → КФИ × 0.90', severity: 'high' },
  { rule: '5', title: 'Флаг bond_concentration_risk', desc: 'Долг по облигациям > 60% финдолга → КФИ × 0.95', severity: 'medium' },
  { rule: '6', title: 'Флаг data_missing', desc: '3+ критических показателя недоступны → КФИ × 0.90', severity: 'medium' },
  { rule: '7', title: 'Флаг young_issuer', desc: 'История менее 2 лет → КФИ ≤ 50', severity: 'medium' },
];

const industries = [
  { num: '1', name: 'Девелопмент и строительство', share: '20–25%', note: 'Эскроу, проектное финансирование, K_escrow' },
  { num: '2', name: 'МФО и потребкредитование', share: '15–20%', note: 'Нет выручки — процентный доход, норматив НМФК1' },
  { num: '3', name: 'Лизинг', share: '15–20%', note: 'Высокий долг — норма бизнес-модели (леверидж ≤7x)' },
  { num: '4', name: 'Торговля и ритейл', share: '10–15%', note: 'Оборачиваемость, сезонность, EBITDA > 8%' },
  { num: '5', name: 'Производство и промышленность', share: '10–15%', note: 'CAPEX-интенсивность, FCF важнее прибыли' },
  { num: '6', name: 'Транспорт и логистика', share: '5–10%', note: 'Активы, ГСМ, сезонность' },
  { num: '7', name: 'Прочие и диверсифицированные', share: '10–15%', note: 'Базовая методология без поправок' },
];

const scale = [
  { range: '80–100', category: 'Надёжный', color: 'bg-indigo-500', text: 'text-white', meaning: 'Низкий риск, устойчивый эмитент' },
  { range: '65–79', category: 'Стабильный', color: 'bg-blue-500', text: 'text-white', meaning: 'Приемлемый риск для ВДО' },
  { range: '50–64', category: 'Умеренный риск', color: 'bg-amber-400', text: 'text-white', meaning: 'Есть слабые места, нужна осторожность' },
  { range: '35–49', category: 'Высокий риск', color: 'bg-orange-500', text: 'text-white', meaning: 'Серьёзные проблемы, только для опытных' },
  { range: '0–34', category: 'Критический', color: 'bg-red-500', text: 'text-white', meaning: 'Признаки преддефолтного состояния' },
];

export default function MethodologyPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-semibold border border-indigo-100">
            📐 КФИ v2.0
          </span>
          <span className="text-xs text-slate-400">Финальная · Апрель 2026</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 leading-tight">Методология КФИ</h1>
        <p className="text-slate-500 text-base max-w-3xl leading-relaxed">
          Комплексный Финансовый Индикатор (КФИ) — автоматизированная система скоринга эмитентов
          высокодоходных облигаций для частных инвесторов. Рассчитывается по 30+ показателям в 6 аналитических блоках.
        </p>
        <div className="flex flex-wrap gap-3">
          <a href="https://github.com/MrGooRoo/KFI-Project" target="_blank" rel="noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 text-sm text-slate-700 hover:border-indigo-300 hover:text-indigo-700 transition-colors">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
            GitHub: MrGooRoo/KFI-Project
          </a>
          <Link to="/" className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-50 text-indigo-700 text-sm font-medium hover:bg-indigo-100 transition-colors">
            📊 Перейти к рейтингу
          </Link>
        </div>
      </div>

      {/* Formula */}
      <section className="bg-slate-900 rounded-3xl p-6 sm:p-8 space-y-4">
        <h2 className="text-white font-bold text-xl">Финальная формула КФИ</h2>
        <div className="font-mono text-sm sm:text-base text-emerald-400 leading-relaxed">
          КФИ = <span className="text-indigo-400">0.20 × A</span> + <span className="text-blue-400">0.25 × B</span> + <span className="text-emerald-400">0.10 × C</span> + <span className="text-violet-400">0.25 × D</span> + <span className="text-amber-400">0.15 × E</span> + <span className="text-rose-400">0.05 × F</span>
        </div>
        <p className="text-slate-400 text-sm">
          Где каждый блок = взвешенная сумма показателей по шкале 0–100. Шкала итогового КФИ: 0–100.
        </p>
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 pt-2">
          {[
            { key: 'A', w: '20%', color: 'text-indigo-400' },
            { key: 'B', w: '25%', color: 'text-blue-400' },
            { key: 'C', w: '10%', color: 'text-emerald-400' },
            { key: 'D', w: '25%', color: 'text-violet-400' },
            { key: 'E', w: '15%', color: 'text-amber-400' },
            { key: 'F', w: '5%', color: 'text-rose-400' },
          ].map(b => (
            <div key={b.key} className="bg-slate-800 rounded-xl p-3 text-center">
              <div className={`text-xl font-black ${b.color}`}>{b.key}</div>
              <div className="text-slate-400 text-xs mt-0.5">{b.w}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Scale */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-slate-900">Шкала категорий КФИ</h2>
        <div className="space-y-2">
          {scale.map((s) => (
            <div key={s.range} className="flex items-center gap-4 bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
              <div className={`flex items-center justify-center w-16 h-12 rounded-xl ${s.color} ${s.text} font-bold text-sm shrink-0`}>
                {s.range}
              </div>
              <div className="flex-1">
                <div className="font-semibold text-slate-900">{s.category}</div>
                <div className="text-sm text-slate-500">{s.meaning}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Blocks */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-slate-900">Шесть аналитических блоков</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {blocks.map((block) => (
            <div key={block.key} className={`bg-white rounded-2xl border ${block.border} shadow-sm overflow-hidden`}>
              <div className={`h-1 bg-gradient-to-r ${block.color}`} />
              <div className="p-5">
                <div className="flex items-center gap-3 mb-3">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-xl ${block.bg} ${block.text} font-black text-lg`}>
                    {block.key}
                  </div>
                  <div>
                    <div className="font-bold text-slate-900 text-sm">{block.name}</div>
                    <div className={`text-xs font-semibold ${block.text}`}>Вес {block.weight}</div>
                  </div>
                </div>
                <div className={`text-xs font-medium ${block.text} ${block.bg} px-3 py-2 rounded-lg mb-3`}>
                  ❓ {block.question}
                </div>
                <ul className="space-y-1.5 mb-3">
                  {block.metrics.map((m, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                      <span className="text-slate-400 shrink-0 mt-0.5">•</span>
                      {m}
                    </li>
                  ))}
                </ul>
                <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-700">
                  💡 {block.note}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Corrections */}
      <section className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Система корректировок и флагов</h2>
          <p className="text-slate-500 text-sm mt-1">Применяются после базового расчёта, строго последовательно</p>
        </div>
        <div className="space-y-3">
          {corrections.map((c) => {
            const sev = c.severity === 'critical'
              ? 'bg-red-50 border-red-200'
              : c.severity === 'high'
              ? 'bg-orange-50 border-orange-200'
              : 'bg-amber-50 border-amber-200';
            const textSev = c.severity === 'critical' ? 'text-red-700' : c.severity === 'high' ? 'text-orange-700' : 'text-amber-700';
            return (
              <div key={c.rule} className={`flex items-start gap-4 rounded-2xl border p-4 ${sev}`}>
                <div className={`flex items-center justify-center w-7 h-7 rounded-lg bg-white/80 shrink-0 font-bold text-sm ${textSev}`}>
                  {c.rule}
                </div>
                <div>
                  <div className={`font-semibold text-sm ${textSev}`}>{c.title}</div>
                  <div className="text-xs text-slate-600 mt-0.5">{c.desc}</div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Industries */}
      <section className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Отраслевые группы</h2>
          <p className="text-slate-500 text-sm mt-1">7 групп с адаптированными нормами для блоков A и B</p>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100">
                <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider w-8">#</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Отрасль</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider hidden sm:table-cell">Доля в ВДО</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Особенность для КФИ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {industries.map((ind) => (
                <tr key={ind.num} className="hover:bg-slate-50 transition-colors">
                  <td className="px-5 py-4 text-sm font-bold text-slate-400">{ind.num}</td>
                  <td className="px-5 py-4 font-medium text-sm text-slate-900">{ind.name}</td>
                  <td className="px-5 py-4 text-sm text-slate-500 hidden sm:table-cell">{ind.share}</td>
                  <td className="px-5 py-4 text-xs text-slate-600">{ind.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Data sources */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-slate-900">Источники данных</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { icon: '📋', name: 'e-disclosure.ru', desc: 'Баланс, ОПУ, ОДДС, пояснения (РСБУ)', blocks: 'A, B, C, D' },
            { icon: '📈', name: 'MOEX ISS API', desc: 'YTM, объёмы, купоны, параметры выпусков', blocks: 'E' },
            { icon: '🏦', name: 'cbr.ru', desc: 'Ключевая ставка, реестр МФО', blocks: 'A, E' },
            { icon: '⚖️', name: 'kad.arbitr.ru', desc: 'Арбитражные дела', blocks: 'F' },
            { icon: '🔍', name: 'egrul.nalog.ru', desc: 'Структура собственников (API ФНС)', blocks: 'F' },
            { icon: '📰', name: 'Яндекс.Новости', desc: 'Публичный фон компании', blocks: 'F' },
          ].map((src) => (
            <div key={src.name} className="flex items-start gap-3 bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
              <span className="text-2xl shrink-0">{src.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-sm text-slate-900">{src.name}</div>
                <div className="text-xs text-slate-500 mt-0.5">{src.desc}</div>
                <span className="inline-flex items-center mt-1.5 px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-600 text-xs font-medium">
                  Блоки: {src.blocks}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Roadmap */}
      <section className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-3xl p-6 sm:p-8 space-y-5">
        <h2 className="text-white font-bold text-xl">Дорожная карта разработки</h2>
        <div className="space-y-3">
          {[
            { phase: 'Фаза 0', name: 'Методология', status: 'done', desc: 'КФИ v2.0 — финальная версия зафиксирована' },
            { phase: 'Фаза 1', name: 'MVP-0: Данные', status: 'active', desc: 'Ручной расчёт 5–10 эмитентов в JSON-формате' },
            { phase: 'Фаза 2', name: 'MVP-1: Сайт', status: 'active', desc: 'Статический сайт: рейтинг-таблица + карточки эмитентов' },
            { phase: 'Фаза 3', name: 'MVP-2: Админка', status: 'planned', desc: 'Claude API → генерация постов → публикация в TG' },
            { phase: 'Фаза 4', name: 'MVP-3: Парсеры', status: 'planned', desc: 'Авто-парсинг MOEX API, e-disclosure, kad.arbitr' },
            { phase: 'Фаза 5', name: 'MVP-4: n8n', status: 'planned', desc: 'Автопостинг в Telegram по расписанию и алертам' },
            { phase: 'v1.0', name: 'Полный продукт', status: 'planned', desc: '50+ эмитентов, PostgreSQL, история изменений КФИ' },
          ].map((item) => (
            <div key={item.phase} className="flex items-center gap-4">
              <div className={`w-3 h-3 rounded-full shrink-0 ${item.status === 'done' ? 'bg-emerald-400' : item.status === 'active' ? 'bg-amber-400 animate-pulse' : 'bg-slate-600'}`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 text-xs font-mono">{item.phase}</span>
                  <span className="text-white text-sm font-semibold">{item.name}</span>
                  {item.status === 'done' && <span className="text-emerald-400 text-xs">✓ Завершено</span>}
                  {item.status === 'active' && <span className="text-amber-400 text-xs">▶ В работе</span>}
                </div>
                <div className="text-slate-400 text-xs mt-0.5">{item.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Disclaimer */}
      <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-xs text-slate-500 leading-relaxed">
        ⚖️ <strong>Дисклеймер:</strong> Данный проект не является инвестиционной рекомендацией.
        Все расчёты носят информационно-аналитический характер. Автор не несёт ответственности за
        инвестиционные решения, принятые на основе данных системы. Методология открыта и доступна на{' '}
        <a href="https://github.com/MrGooRoo/KFI-Project" target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">
          GitHub
        </a>.
      </div>
    </div>
  );
}
