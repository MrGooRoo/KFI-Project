interface ProgressBarProps {
  progress: number;
  currentPage: number;
  totalPages: number;
  status: string;
  fileName?: string;
}

export default function ProgressBar({ progress, currentPage, totalPages, status, fileName }: ProgressBarProps) {
  const statusText = () => {
    switch (status) {
      case 'loading': return 'Загрузка PDF файла...';
      case 'processing': return `Обработка страницы ${currentPage} из ${totalPages}...`;
      case 'done': return 'Обработка завершена!';
      case 'error': return 'Ошибка обработки';
      default: return '';
    }
  };

  return (
    <div className="rounded-xl bg-white p-6 shadow-sm border border-slate-200">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`
            flex items-center justify-center w-10 h-10 rounded-lg
            ${status === 'done' ? 'bg-green-100 text-green-600' :
              status === 'error' ? 'bg-red-100 text-red-600' :
              'bg-blue-100 text-blue-600'}
          `}>
            {status === 'done' ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            ) : status === 'error' ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-700">{statusText()}</p>
            {fileName && <p className="text-xs text-slate-500 mt-0.5 truncate max-w-xs">{fileName}</p>}
          </div>
        </div>
        <span className="text-2xl font-bold text-slate-700">{progress}%</span>
      </div>

      <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
        <div
          className={`
            h-full rounded-full transition-all duration-500 ease-out
            ${status === 'done' ? 'bg-gradient-to-r from-green-400 to-green-500' :
              status === 'error' ? 'bg-gradient-to-r from-red-400 to-red-500' :
              'bg-gradient-to-r from-blue-400 to-blue-600'}
          `}
          style={{ width: `${progress}%` }}
        />
      </div>

      {status === 'processing' && (
        <div className="flex gap-1 mt-3">
          {Array.from({ length: totalPages }, (_, i) => (
            <div
              key={i}
              className={`
                h-1.5 flex-1 rounded-full transition-colors duration-300
                ${i + 1 < currentPage ? 'bg-blue-500' :
                  i + 1 === currentPage ? 'bg-blue-400 animate-pulse' :
                  'bg-slate-200'}
              `}
            />
          ))}
        </div>
      )}
    </div>
  );
}
