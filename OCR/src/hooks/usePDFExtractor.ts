import { useState, useCallback, useRef } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import Tesseract from 'tesseract.js';

pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;

export interface PageResult {
  pageNumber: number;
  imageDataUrl: string;
  text: string;
  status: 'pending' | 'rendering' | 'ocr' | 'done' | 'error';
  error?: string;
}

export interface ExtractionState {
  pages: PageResult[];
  totalPages: number;
  currentPage: number;
  status: 'idle' | 'loading' | 'processing' | 'done' | 'error';
  overallProgress: number;
  error?: string;
  fileName?: string;
}

const initialState: ExtractionState = {
  pages: [],
  totalPages: 0,
  currentPage: 0,
  status: 'idle',
  overallProgress: 0,
  fileName: undefined,
  error: undefined,
};

export function usePDFExtractor() {
  const [state, setState] = useState<ExtractionState>(initialState);
  const abortRef = useRef(false);
  const workerRef = useRef<Tesseract.Worker | null>(null);

  const reset = useCallback(() => {
    abortRef.current = true;
    if (workerRef.current) {
      workerRef.current.terminate();
      workerRef.current = null;
    }
    setState(initialState);
    setTimeout(() => { abortRef.current = false; }, 100);
  }, []);

  const processFile = useCallback(async (file: File, language: string, scale: number) => {
    abortRef.current = false;

    setState({
      ...initialState,
      status: 'loading',
      fileName: file.name,
    });

    try {
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      const totalPages = pdf.numPages;

      const emptyPages: PageResult[] = Array.from({ length: totalPages }, (_, i) => ({
        pageNumber: i + 1,
        imageDataUrl: '',
        text: '',
        status: 'pending' as const,
      }));

      setState(prev => ({
        ...prev,
        totalPages,
        pages: emptyPages,
        status: 'processing',
      }));

      // Create Tesseract worker
      const worker = await Tesseract.createWorker(language, undefined, {
        logger: () => {},
      });
      workerRef.current = worker;

      for (let i = 0; i < totalPages; i++) {
        if (abortRef.current) break;

        const pageNum = i + 1;

        setState(prev => ({
          ...prev,
          currentPage: pageNum,
          overallProgress: Math.round(((i) / totalPages) * 100),
          pages: prev.pages.map(p =>
            p.pageNumber === pageNum ? { ...p, status: 'rendering' as const } : p
          ),
        }));

        // Render page to canvas
        const page = await pdf.getPage(pageNum);
        const viewport = page.getViewport({ scale });
        const canvas = document.createElement('canvas');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        const ctx = canvas.getContext('2d')!;

        await page.render({ canvasContext: ctx, viewport }).promise;

        const imageDataUrl = canvas.toDataURL('image/png');

        setState(prev => ({
          ...prev,
          pages: prev.pages.map(p =>
            p.pageNumber === pageNum
              ? { ...p, imageDataUrl, status: 'ocr' as const }
              : p
          ),
        }));

        if (abortRef.current) break;

        // OCR
        try {
          const { data } = await worker.recognize(canvas);
          setState(prev => ({
            ...prev,
            overallProgress: Math.round(((i + 1) / totalPages) * 100),
            pages: prev.pages.map(p =>
              p.pageNumber === pageNum
                ? { ...p, text: data.text, status: 'done' as const }
                : p
            ),
          }));
        } catch (ocrErr: any) {
          setState(prev => ({
            ...prev,
            pages: prev.pages.map(p =>
              p.pageNumber === pageNum
                ? { ...p, status: 'error' as const, error: ocrErr.message }
                : p
            ),
          }));
        }

        canvas.width = 0;
        canvas.height = 0;
      }

      await worker.terminate();
      workerRef.current = null;

      if (!abortRef.current) {
        setState(prev => ({
          ...prev,
          status: 'done',
          overallProgress: 100,
        }));
      }
    } catch (err: any) {
      setState(prev => ({
        ...prev,
        status: 'error',
        error: err.message || 'Неизвестная ошибка',
      }));
    }
  }, []);

  return { state, processFile, reset };
}
