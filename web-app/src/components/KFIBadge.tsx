import { KFICategory, getCategoryColor } from '../data/emitters';

interface KFIBadgeProps {
  score: number;
  category: KFICategory;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showCategory?: boolean;
}

const colorMap: Record<string, { bg: string; text: string; ring: string; bar: string }> = {
  indigo: {
    bg: 'bg-indigo-50',
    text: 'text-indigo-700',
    ring: 'ring-indigo-200',
    bar: 'bg-indigo-500',
  },
  blue: {
    bg: 'bg-blue-50',
    text: 'text-blue-700',
    ring: 'ring-blue-200',
    bar: 'bg-blue-500',
  },
  amber: {
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    ring: 'ring-amber-200',
    bar: 'bg-amber-500',
  },
  orange: {
    bg: 'bg-orange-50',
    text: 'text-orange-700',
    ring: 'ring-orange-200',
    bar: 'bg-orange-500',
  },
  red: {
    bg: 'bg-red-50',
    text: 'text-red-700',
    ring: 'ring-red-200',
    bar: 'bg-red-500',
  },
};

const categoryEmoji: Record<KFICategory, string> = {
  'Надёжный': '🟦',
  'Стабильный': '🔵',
  'Умеренный риск': '🟡',
  'Высокий риск': '🟠',
  'Критический': '🔴',
};

export default function KFIBadge({ score, category, size = 'md', showCategory = true }: KFIBadgeProps) {
  const color = getCategoryColor(category);
  const colors = colorMap[color];
  const emoji = categoryEmoji[category];

  if (size === 'xl') {
    return (
      <div className="flex flex-col items-center gap-2">
        <div className={`relative flex items-center justify-center w-28 h-28 rounded-3xl ${colors.bg} ring-4 ${colors.ring} shadow-lg`}>
          <span className={`font-black text-5xl ${colors.text} tabular-nums`}>{score}</span>
        </div>
        {showCategory && (
          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full ${colors.bg} ${colors.text} font-semibold text-sm`}>
            <span>{emoji}</span>
            <span>{category.toUpperCase()}</span>
          </div>
        )}
      </div>
    );
  }

  if (size === 'lg') {
    return (
      <div className="flex items-center gap-3">
        <div className={`flex items-center justify-center w-16 h-16 rounded-2xl ${colors.bg} ring-2 ${colors.ring}`}>
          <span className={`font-black text-2xl ${colors.text} tabular-nums`}>{score}</span>
        </div>
        {showCategory && (
          <div>
            <div className={`font-semibold text-sm ${colors.text}`}>
              {emoji} {category}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">КФИ score</div>
          </div>
        )}
      </div>
    );
  }

  if (size === 'sm') {
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-bold ${colors.bg} ${colors.text}`}>
        {score}
        {showCategory && <span className="font-normal">· {emoji}</span>}
      </span>
    );
  }

  // md default
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl ${colors.bg} ring-1 ${colors.ring}`}>
      <span className={`font-black text-xl ${colors.text} tabular-nums`}>{score}</span>
      {showCategory && (
        <div className="flex flex-col">
          <span className={`text-xs font-semibold ${colors.text}`}>{emoji} {category}</span>
        </div>
      )}
    </div>
  );
}
