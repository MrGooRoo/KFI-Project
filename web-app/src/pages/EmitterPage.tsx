import { useParams, Link, Navigate } from 'react-router-dom';
import { EMITTERS, getCategoryColor, BlockScore } from '../data/emitters';
import KFIBadge from '../components/KFIBadge';
import BlockBar from '../components/BlockBar';

const blockWeights: Record<string, string> = {
  A: '20%', B: '25%', C: '10%', D: '25%', E: '15%', F: '5%',
};



function getScoreColor(score: number) {
  if (score >= 75) return { bg: 'bg-indigo-50', text: 'text-indigo-700', bar: 'bg-indigo-400' };
  if (score >= 60) return { bg: 'bg-blue-50', text: 'text-blue-700', bar: 'bg-blue-400' };
  if (score >= 45) return { bg: 'bg-amber-50', text: 'text-amber-700', bar: 'bg-amber-400' };
  if (score >= 25) return { bg: 'bg-orange-50', text: 'text-orange-700', bar: 'bg-orange-400' };
  return { bg: 'bg-red-50', text: 'text-red-700', bar: 'bg-red-400' };
}

function BlockCard({ block, weight }: { block: BlockScore; weight: string }) {
  const colors = getScoreColor(block.score);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className={`px-5 py-4 border-b border-slate-100 flex items-center justify-between ${colors.bg}`}>
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-xl bg-white/80 shadow-sm">
            <span className="text-sm font-black text-slate-700">{block.key}</span>
          </div>
          <div>
            <div className="font-semibold text-slate-900 text-sm">{block.label}</div>
            <div className="text-xs text-slate-500">вес {weight}</div>
          </div>
        </div>
        <div className={`flex items-center justify-center w-12 h-12 rounded-2xl bg-white/80 shadow-sm`}>
          <span className={`font-black text-xl tabular-nums ${colors.text}`}>{block.score}</span>
        </div>
      </div>

      {/* Progress */}
      <div className="px-5 pt-3 pb-1">
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${colors.bar}`}
            style={{ width: `${block.score}%` }}
          />
        </div>
      </div>

      {/* Description */}
      <p className="px-5 py-2 text-xs text-slate-400">{block.description}</p>

      {/* Details */}
      <div className="px-5 pb-4 space-y-3">
        {block.details.map((detail, i) => {
          const dc = getScoreColor(detail.score);
          return (
            <div key={i} className="space-y-1">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-slate-700">{detail.name}</div>
                  {detail.note && (
                    <div className="text-xs text-slate-400 mt-0.5">{detail.note}</div>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-sm font-semibold text-slate-800">{detail.value}</span>
                  <span className={`text-xs font-bold px-1.5 py-0.5 rounded-md ${dc.bg} ${dc.text}`}>{detail.score}</span>
                </div>
              </div>
              <div className="h-1 bg-slate-100 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${dc.bar}`} style={{ width: `${detail.score}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function EmitterPage() {
  const { id } = useParams();
  const emitter = EMITTERS.find((e) => e.id === id);

  if (!emitter) return <Navigate to="/" replace />;

  const categoryColor = getCategoryColor(emitter.category);

  const colorMap: Record<string, { bg: string; text: string; border: string; gradient: string }> = {
    indigo: { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200', gradient: 'from-indigo-500 to-blue-600' },
    blue: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', gradient: 'from-blue-500 to-cyan-600' },
    amber: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', gradient: 'from-amber-500 to-orange-500' },
    orange: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200', gradient: 'from-orange-500 to-red-500' },
    red: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', gradient: 'from-red-500 to-rose-600' },
  };
  const cc = colorMap[categoryColor];

  const activeFlags = emitter.flags.filter((f) => f.active);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-slate-400">
        <Link to="/" className="hover:text-indigo-600 transition-colors">Рейтинг</Link>
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
        <span className="text-slate-700 font-medium">{emitter.shortName}</span>
      </nav>

      {/* Hero Card */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Color strip */}
        <div className={`h-1.5 bg-gradient-to-r ${cc.gradient}`} />

        <div className="p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row sm:items-start gap-6">
            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-slate-100 text-slate-600 text-xs font-medium">
                  {emitter.industry}
                </span>
                <span className="text-xs text-slate-400">ИНН: {emitter.inn}</span>
                <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border text-xs font-medium ${cc.bg} ${cc.text} ${cc.border}`}>
                  ✅ Верифицировано · {emitter.verifiedAt}
                </span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-4 leading-tight">{emitter.name}</h1>

              {/* Summary */}
              <p className="text-slate-600 text-sm leading-relaxed mb-4">{emitter.summary}</p>

              {/* Meta */}
              <div className="flex flex-wrap gap-4 text-xs text-slate-400">
                <span>📅 Обновлено: <strong className="text-slate-600">{emitter.updatedAt}</strong></span>
                <span>👤 Верификация: <strong className="text-slate-600">{emitter.verifiedBy}</strong></span>
                <span>📊 Методология: <strong className="text-slate-600">КФИ v2.0</strong></span>
              </div>
            </div>

            {/* Score */}
            <div className="shrink-0">
              <KFIBadge score={emitter.kfiFinal} category={emitter.category} size="xl" showCategory />
              {emitter.kfiBase !== emitter.kfiFinal && (
                <div className="mt-2 text-center text-xs text-slate-400">
                  База: {emitter.kfiBase} → Финал: {emitter.kfiFinal}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Risk Flags */}
      {activeFlags.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider px-1">⚠️ Флаги риска</h2>
          <div className="space-y-2">
            {activeFlags.map((flag) => (
              <div key={flag.key} className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-2xl px-5 py-4">
                <div className="shrink-0 text-amber-600 font-bold text-sm mt-0.5">{flag.label}</div>
                <div className="text-xs text-amber-700 leading-relaxed">{flag.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Block Overview */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h2 className="text-base font-bold text-slate-900 mb-5">Сводка по блокам КФИ</h2>
        <div className="space-y-3">
          {emitter.blocks.map((block) => (
            <BlockBar
              key={block.key}
              blockKey={block.key}
              label={block.label}
              score={block.score}
              weight={blockWeights[block.key]}
            />
          ))}
        </div>

        {/* Formula */}
        <div className="mt-5 pt-5 border-t border-slate-100">
          <div className="text-xs text-slate-400 font-mono bg-slate-50 rounded-xl px-4 py-3">
            КФИ = 0.20×{emitter.blocks.find(b=>b.key==='A')?.score}(A)
            {' + '}0.25×{emitter.blocks.find(b=>b.key==='B')?.score}(B)
            {' + '}0.10×{emitter.blocks.find(b=>b.key==='C')?.score}(C)
            {' + '}0.25×{emitter.blocks.find(b=>b.key==='D')?.score}(D)
            {' + '}0.15×{emitter.blocks.find(b=>b.key==='E')?.score}(E)
            {' + '}0.05×{emitter.blocks.find(b=>b.key==='F')?.score}(F)
            {' = '}
            <strong className="text-slate-700">{emitter.kfiBase}</strong>
            {' → '}
            <strong className={`${cc.text}`}>КФИ = {emitter.kfiFinal}</strong>
          </div>
        </div>
      </div>

      {/* Block Details */}
      <div>
        <h2 className="text-base font-bold text-slate-900 mb-4 px-1">Детальный разбор по блокам</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {emitter.blocks.map((block) => (
            <BlockCard key={block.key} block={block} weight={blockWeights[block.key]} />
          ))}
        </div>
      </div>

      {/* Bonds */}
      {emitter.bonds.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-3">
            <span className="text-base font-bold text-slate-900">Выпуски облигаций</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs font-medium">
              {emitter.bonds.length}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">ISIN</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Название</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">YTM</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Купон</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Погашение</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider hidden sm:table-cell">Объём (млн)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {emitter.bonds.map((bond) => (
                  <tr key={bond.isin} className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-4">
                      <span className="font-mono text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">{bond.isin}</span>
                    </td>
                    <td className="px-5 py-4 font-medium text-sm text-slate-800">{bond.name}</td>
                    <td className="px-5 py-4 text-right">
                      <span className="font-bold text-sm text-orange-600">{bond.ytm.toFixed(1)}%</span>
                    </td>
                    <td className="px-5 py-4 text-right font-medium text-sm text-slate-700">{bond.couponRate.toFixed(1)}%</td>
                    <td className="px-5 py-4 text-right text-sm text-slate-500">{bond.maturityDate}</td>
                    <td className="px-5 py-4 text-right text-sm text-slate-500 hidden sm:table-cell">{bond.volume} млн ₽</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Back */}
      <div className="flex items-center gap-4">
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 text-slate-700 text-sm font-medium hover:bg-slate-200 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Назад к рейтингу
        </Link>
      </div>

      {/* Disclaimer */}
      <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-xs text-slate-500 leading-relaxed">
        ⚖️ <strong>Дисклеймер:</strong> {emitter.disclaimer}
        {' '}Верификатор: <strong>{emitter.verifiedBy}</strong> · {emitter.verifiedAt}.
        Методология: <a href="https://github.com/MrGooRoo/KFI-Project" target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">КФИ v2.0</a>
      </div>
    </div>
  );
}
