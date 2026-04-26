interface SettingsProps {
  language: string;
  setLanguage: (lang: string) => void;
  scale: number;
  setScale: (scale: number) => void;
  disabled?: boolean;
}

const LANGUAGES = [
  { code: 'rus', label: 'Русский' },
  { code: 'eng', label: 'English' },
  { code: 'rus+eng', label: 'Русский + English' },
  { code: 'deu', label: 'Deutsch' },
  { code: 'fra', label: 'Français' },
  { code: 'spa', label: 'Español' },
  { code: 'ita', label: 'Italiano' },
  { code: 'por', label: 'Português' },
  { code: 'pol', label: 'Polski' },
  { code: 'ukr', label: 'Українська' },
  { code: 'chi_sim', label: '中文 (简体)' },
  { code: 'jpn', label: '日本語' },
  { code: 'kor', label: '한국어' },
  { code: 'ara', label: 'العربية' },
];

const SCALES = [
  { value: 1, label: '1x — Быстро' },
  { value: 1.5, label: '1.5x — Баланс' },
  { value: 2, label: '2x — Качественно' },
  { value: 3, label: '3x — Максимум' },
];

export default function Settings({ language, setLanguage, scale, setScale, disabled }: SettingsProps) {
  return (
    <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5">
      <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        Настройки распознавания
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1.5">Язык распознавания</label>
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            disabled={disabled}
            className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent disabled:opacity-50 transition-colors"
          >
            {LANGUAGES.map(l => (
              <option key={l.code} value={l.code}>{l.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1.5">Масштаб рендеринга</label>
          <select
            value={scale}
            onChange={e => setScale(Number(e.target.value))}
            disabled={disabled}
            className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent disabled:opacity-50 transition-colors"
          >
            {SCALES.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
      </div>

      <p className="mt-3 text-xs text-slate-400">
        Более высокий масштаб улучшает качество распознавания, но замедляет обработку.
      </p>
    </div>
  );
}
