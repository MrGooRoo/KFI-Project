interface BlockBarProps {
  label: string;
  blockKey: string;
  score: number;
  weight: string;
  compact?: boolean;
}

function getBlockColor(score: number): string {
  if (score >= 75) return 'bg-indigo-500';
  if (score >= 60) return 'bg-blue-500';
  if (score >= 45) return 'bg-amber-500';
  if (score >= 25) return 'bg-orange-500';
  return 'bg-red-500';
}

function getBlockTextColor(score: number): string {
  if (score >= 75) return 'text-indigo-700';
  if (score >= 60) return 'text-blue-700';
  if (score >= 45) return 'text-amber-700';
  if (score >= 25) return 'text-orange-700';
  return 'text-red-700';
}

export default function BlockBar({ label, blockKey, score, weight, compact = false }: BlockBarProps) {
  const barColor = getBlockColor(score);
  const textColor = getBlockTextColor(score);

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 w-28 shrink-0">
          <span className="text-xs font-bold text-slate-500 w-5">{blockKey}</span>
          <span className="text-xs text-slate-600 truncate">{label}</span>
        </div>
        <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${barColor}`}
            style={{ width: `${score}%` }}
          />
        </div>
        <span className={`text-sm font-bold w-8 text-right tabular-nums ${textColor}`}>{score}</span>
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center justify-center w-6 h-6 rounded-md bg-slate-100 text-xs font-bold text-slate-600">
            {blockKey}
          </span>
          <span className="text-sm font-medium text-slate-700">{label}</span>
          <span className="text-xs text-slate-400 hidden sm:inline">вес {weight}</span>
        </div>
        <span className={`text-sm font-bold tabular-nums ${textColor}`}>{score}/100</span>
      </div>
      <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
