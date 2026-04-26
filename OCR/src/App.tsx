import { useState, useCallback } from 'react';
import FileUpload from './components/FileUpload';
import Settings from './components/Settings';
import ProgressBar from './components/ProgressBar';
import PageResult from './components/PageResult';
import { usePDFExtractor } from './hooks/usePDFExtractor';

export default function App() {
  const [language, setLanguage] = useState('rus+eng');
  const [scale, setScale] = useState(2);
  const [copiedAll, setCopiedAll] = useState(false);

  const { state, processFile, reset } = usePDFExtractor();

  const handleFileSelected = useCallback(
    (file: File) => {
      processFile(file, language, scale);
    },
    [processFile, language, scale]
  );

  const allText = state.pages
    .filter(p => p.status === 'done' && p.text.trim())
    .map(p => `--- Страница ${p.pageNumber} ---\n${p.text}`)
    .join('\n\n');

  const copyAllText = () => {
    navigator.clipboard.writeText(allText);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2500);
  };

  const downloadText = () => {
    const blob = new Blob([allText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = (state.fileName?.replace('.pdf', '') || 'extracted') + '.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  const isProcessing = state.status === 'loading' || state.status === 'processing';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-slate-100">
      {/* Header */}
      <header className="border-b border-slate-200/80 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-200">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800">PDF OCR</h1>
              <p className="text-xs text-slate-500">Извлечение текста из отсканированных PDF</p>
            </div>
          </div>

          {state.status !== 'idle' && (
            <button
              onClick={reset}
              className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              Новый файл
            </button>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* Info Banner */}
        {state.status === 'idle' && (
          <div className="rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 p-6 text-white shadow-lg shadow-blue-200/50">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <div className="flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-semibold">Как это работает?</h2>
                <p className="text-blue-100 text-sm mt-1">
                  Загрузите PDF файл с отсканированными страницами. Каждая страница будет отрендерена как изображение,
                  затем с помощью технологии OCR (Tesseract.js) текст будет извлечён автоматически.
                  Вся обработка происходит прямо в вашем браузере — файлы никуда не отправляются.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Settings */}
        <Settings
          language={language}
          setLanguage={setLanguage}
          scale={scale}
          setScale={setScale}
          disabled={isProcessing}
        />

        {/* File Upload */}
        {state.status === 'idle' && (
          <FileUpload onFileSelected={handleFileSelected} disabled={isProcessing} />
        )}

        {/* Progress */}
        {state.status !== 'idle' && (
          <ProgressBar
            progress={state.overallProgress}
            currentPage={state.currentPage}
            totalPages={state.totalPages}
            status={state.status}
            fileName={state.fileName}
          />
        )}

        {/* Error */}
        {state.status === 'error' && state.error && (
          <div className="rounded-xl bg-red-50 border border-red-200 p-5">
            <div className="flex items-start gap-3">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div>
                <h3 className="text-sm font-semibold text-red-800">Произошла ошибка</h3>
                <p className="text-sm text-red-600 mt-1">{state.error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Actions for done state */}
        {state.status === 'done' && allText && (
          <div className="flex flex-wrap gap-3">
            <button
              onClick={copyAllText}
              className={`
                inline-flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold shadow-sm transition-all
                ${copiedAll
                  ? 'bg-green-500 text-white shadow-green-200'
                  : 'bg-blue-600 text-white hover:bg-blue-700 shadow-blue-200 hover:shadow-blue-300'}
              `}
            >
              {copiedAll ? (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  Скопировано!
                </>
              ) : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Копировать весь текст
                </>
              )}
            </button>

            <button
              onClick={downloadText}
              className="inline-flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 shadow-sm transition-all"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Скачать как .txt
            </button>
          </div>
        )}

        {/* Pages */}
        {state.pages.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-slate-700 flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              Результаты по страницам
              <span className="text-sm font-normal text-slate-400">
                ({state.pages.filter(p => p.status === 'done').length} из {state.totalPages} обработано)
              </span>
            </h2>

            {state.pages.map(page => (
              <PageResult key={page.pageNumber} page={page} />
            ))}
          </div>
        )}

        {/* Footer */}
        <footer className="pt-8 pb-4 text-center text-xs text-slate-400">
          <p>PDF OCR — Обработка происходит локально в вашем браузере</p>
          <p className="mt-1">Powered by Tesseract.js & PDF.js</p>
        </footer>
      </main>
    </div>
  );
}
