import { HashRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import RatingPage from './pages/RatingPage';
import EmitterPage from './pages/EmitterPage';
import MethodologyPage from './pages/MethodologyPage';

export default function App() {
  return (
    <HashRouter>
      <div className="min-h-screen bg-slate-50">
        <Header />
        <main className="pb-16">
          <Routes>
            <Route path="/" element={<RatingPage />} />
            <Route path="/emitter/:id" element={<EmitterPage />} />
            <Route path="/methodology" element={<MethodologyPage />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-200 bg-white py-6 px-4">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <div className="flex items-center justify-center w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-500 to-blue-600">
                <span className="text-white font-bold text-xs">К</span>
              </div>
              <span><strong className="text-slate-600">КФИ</strong> — Кредитно-Финансовый Индекс v2.0</span>
            </div>
            <div className="flex items-center gap-4">
              <a href="https://github.com/MrGooRoo/KFI-Project" target="_blank" rel="noreferrer" className="hover:text-indigo-600 transition-colors">
                GitHub
              </a>
              <span>·</span>
              <span>Не является инвестиционной рекомендацией</span>
            </div>
          </div>
        </footer>
      </div>
    </HashRouter>
  );
}
