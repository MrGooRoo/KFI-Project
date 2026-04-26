import { useState } from 'react';
import type { PageResult as PageResultType } from '../hooks/usePDFExtractor';

interface PageResultProps {
  page: PageResultType;
}

export default function PageResult({ page }: PageResultProps) {
  const [showImage, setShowImage] = useState(false);
  const [copied, setCopied] = useState(false);

  const copyText = () => {
    navigator.clipboard.writeText(page.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const statusBadge = () => {
    switch (page.status) {
      case 'pending':
        return <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-500">Ожидание</span>;
      case 'rendering':
        return <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-700 animate-pulse">Рендеринг...</span>;
      case 'ocr':
        return <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2.5 py-1 text-xs font-medium text-blue-700 animate-pulse">OCR...</span>;
      case 'done':
        return <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-700">✓ Готово</span>;
      case 'error':
        return <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2.5 py-1 text-xs font-medium text-red-700">Ошибка</span>;
    }
  };

  return (
    <div className="rounded-xl bg-white border border-slate-200 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-md">
      <div className="flex items-center justify-between p-4 border-b border-slate-100 bg-slate-50/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-100 text-blue-700 text-sm font-bold">
            {page.pageNumber}
          </div>
          <span className="text-sm font-medium text-slate-600">Страница {page.pageNumber}</span>
        </div>
        <div className="flex items-center gap-2">
          {statusBadge()}
          {page.imageDataUrl && (
            <button
              onClick={() => setShowImage(v => !v)}
              className="inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {showImage ? 'Скрыть' : 'Показать'}
            </button>
          )}
          {page.status === 'done' && page.text && (
            <button
              onClick={copyText}
              className={`
                inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors
                ${copied
                  ? 'bg-green-100 text-green-700'
                  : 'bg-blue-100 text-blue-700 hover:bg-blue-200'}
              `}
            >
              {copied ? (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  Скопировано
                </>
              ) : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Копировать
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {showImage && page.imageDataUrl && (
        <div className="p-4 bg-slate-50 border-b border-slate-100">
          <img
            src={page.imageDataUrl}
            alt={`Страница ${page.pageNumber}`}
            className="max-h-96 mx-auto rounded-lg shadow-sm border border-slate-200"
          />
        </div>
      )}

      {page.status === 'done' && (
        <div className="p-4">
          {page.text.trim() ? (
            <pre className="whitespace-pre-wrap text-sm text-slate-700 leading-relaxed font-sans max-h-64 overflow-y-auto">
              {page.text}
            </pre>
          ) : (
            <p className="text-sm text-slate-400 italic">Текст не распознан на этой странице</p>
          )}
        </div>
      )}

      {page.status === 'error' && (
        <div className="p-4">
          <p className="text-sm text-red-500">{page.error || 'Ошибка обработки страницы'}</p>
        </div>
      )}

      {(page.status === 'pending' || page.status === 'rendering' || page.status === 'ocr') && (
        <div className="p-6 flex justify-center">
          <div className="flex items-center gap-3 text-slate-400">
            <div className="w-5 h-5 border-2 border-slate-300 border-t-blue-500 rounded-full animate-spin" />
            <span className="text-sm">
              {page.status === 'rendering' ? 'Рендеринг страницы...' :
               page.status === 'ocr' ? 'Распознавание текста...' :
               'Ожидание обработки...'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
