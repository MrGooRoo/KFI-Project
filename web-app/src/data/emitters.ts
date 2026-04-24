export type IndustryGroup =
  | 'Девелопмент'
  | 'МФО'
  | 'Лизинг'
  | 'Торговля'
  | 'Производство'
  | 'Транспорт'
  | 'Прочие';

export type KFICategory =
  | 'Надёжный'
  | 'Стабильный'
  | 'Умеренный риск'
  | 'Высокий риск'
  | 'Критический';

export type RiskFlag = {
  key: string;
  label: string;
  description: string;
  active: boolean;
};

export type BlockScore = {
  score: number;
  label: string;
  key: 'A' | 'B' | 'C' | 'D' | 'E' | 'F';
  description: string;
  details: { name: string; value: string; score: number; note?: string }[];
};

export type Emitter = {
  id: string;
  name: string;
  shortName: string;
  inn: string;
  industry: IndustryGroup;
  kfiBase: number;
  kfiFinal: number;
  category: KFICategory;
  updatedAt: string;
  verifiedBy: string;
  verifiedAt: string;
  blocks: BlockScore[];
  flags: RiskFlag[];
  bonds: {
    isin: string;
    name: string;
    ytm: number;
    maturityDate: string;
    couponRate: number;
    volume: number;
  }[];
  summary: string;
  disclaimer: string;
};

export function getCategory(score: number): KFICategory {
  if (score >= 80) return 'Надёжный';
  if (score >= 65) return 'Стабильный';
  if (score >= 50) return 'Умеренный риск';
  if (score >= 35) return 'Высокий риск';
  return 'Критический';
}

export function getCategoryColor(category: KFICategory): string {
  switch (category) {
    case 'Надёжный': return 'indigo';
    case 'Стабильный': return 'blue';
    case 'Умеренный риск': return 'amber';
    case 'Высокий риск': return 'orange';
    case 'Критический': return 'red';
  }
}

export function getCategoryEmoji(category: KFICategory): string {
  switch (category) {
    case 'Надёжный': return '🟦';
    case 'Стабильный': return '🔵';
    case 'Умеренный риск': return '🟡';
    case 'Высокий риск': return '🟠';
    case 'Критический': return '🔴';
  }
}

export const EMITTERS: Emitter[] = [
  {
    id: 'romashka-leasing',
    name: 'ООО «Ромашка Лизинг»',
    shortName: 'Ромашка Лизинг',
    inn: '7701234567',
    industry: 'Лизинг',
    kfiBase: 73,
    kfiFinal: 71,
    category: 'Стабильный',
    updatedAt: '20.04.2026',
    verifiedBy: 'MrGooRoo',
    verifiedAt: '20.04.2026',
    summary:
      'Компания демонстрирует устойчивую бизнес-модель с хорошим покрытием долга лизинговым портфелем. Леверидж 6.2x находится в пределах отраслевой нормы для лизинговых компаний. Основные риски — умеренный рост просроченной задолженности и концентрация в сегменте автолизинга.',
    blocks: [
      {
        key: 'A',
        label: 'Платёжная устойчивость',
        score: 72,
        description: 'Способность выполнять краткосрочные обязательства',
        details: [
          { name: 'ICR (EBIT / Проценты)', value: '1.6x', score: 68, note: 'Норма для лизинга ≥ 1.3x' },
          { name: 'Покрытие долга портфелем', value: '1.12x', score: 78, note: '⚠️ Отраслевая норма' },
          { name: 'Абсолютная ликвидность', value: '0.13', score: 71 },
        ],
      },
      {
        key: 'B',
        label: 'Структурная устойчивость',
        score: 68,
        description: 'Устойчивость структуры капитала и долговая нагрузка',
        details: [
          { name: 'Финансовый леверидж', value: '6.2x', score: 65, note: '⚠️ Норма для лизинга ≤ 7.0x' },
          { name: 'Качество портфеля (просрочка)', value: '3.8%', score: 75, note: 'Норма ≤ 5%' },
          { name: 'ICR по долгу (лизинг/займы)', value: '1.31x', score: 63 },
        ],
      },
      {
        key: 'C',
        label: 'Рентабельность',
        score: 58,
        description: 'Способность бизнеса генерировать прибыль',
        details: [
          { name: 'EBITDA Margin', value: '18.4%', score: 62 },
          { name: 'ROE', value: '14.2%', score: 58 },
          { name: 'ROA', value: '3.1%', score: 52 },
        ],
      },
      {
        key: 'D',
        label: 'Денежный поток',
        score: 74,
        description: 'Реальность прибыли и качество денежных потоков',
        details: [
          { name: 'CFO / Чистая прибыль', value: '0.91x', score: 76 },
          { name: 'FCF (свободный денежный поток)', value: '+182 млн ₽', score: 74 },
          { name: 'CFO Margin', value: '16.7%', score: 71 },
        ],
      },
      {
        key: 'E',
        label: 'Облигационный профиль',
        score: 80,
        description: 'Безопасность конкретного облигационного выпуска',
        details: [
          { name: 'YTM vs ключевая ставка ЦБ', value: '+3.2% спред', score: 82 },
          { name: 'Срок до погашения', value: '2.1 года', score: 78 },
          { name: 'Объём торгов (ликвидность)', value: '18.4 млн/день', score: 80 },
        ],
      },
      {
        key: 'F',
        label: 'Качественная оценка',
        score: 62,
        description: 'Нефинансовые факторы: репутация, прозрачность, структура',
        details: [
          { name: 'Судебные дела (арбитраж)', value: 'Нет существенных', score: 70 },
          { name: 'Раскрытие информации', value: 'Удовлетворительное', score: 60 },
          { name: 'Структура собственности', value: 'Прозрачная', score: 55 },
        ],
      },
    ],
    flags: [
      {
        key: 'ebitda_approximated',
        label: 'ℹ️ EBITDA приближённая',
        description: 'Амортизация не выделена в РСБУ-отчётности отдельной строкой. EBITDA ≈ Прибыль от продаж.',
        active: true,
      },
      { key: 'bankruptcy_risk', label: '⚠️ Риск банкротства', description: '', active: false },
      { key: 'revenue_quality_risk', label: '⚠️ Риск качества выручки', description: '', active: false },
    ],
    bonds: [
      { isin: 'RU000A107HR0', name: 'Ромашка Лизинг БО-01', ytm: 19.8, maturityDate: '15.06.2028', couponRate: 18.5, volume: 500 },
    ],
    disclaimer:
      'Оценка КФИ сформирована автоматически на основе публично доступных данных. Не является инвестиционной рекомендацией. Инвестирование в ВДО сопряжено с повышенным риском потери капитала.',
  },
  {
    id: 'alfa-stroy',
    name: 'ООО «Альфа Строй»',
    shortName: 'Альфа Строй',
    inn: '5032198765',
    industry: 'Девелопмент',
    kfiBase: 61,
    kfiFinal: 58,
    category: 'Умеренный риск',
    updatedAt: '18.04.2026',
    verifiedBy: 'MrGooRoo',
    verifiedAt: '18.04.2026',
    summary:
      'Девелопер среднего сегмента с двумя активными проектами. Коэффициент покрытия эскроу (K_escrow = 82%) находится в зоне нормы ЦБ. Основной риск — замедление продаж на фоне высокой ключевой ставки и снижения доступности ипотеки.',
    blocks: [
      {
        key: 'A',
        label: 'Платёжная устойчивость',
        score: 55,
        description: 'Способность выполнять краткосрочные обязательства',
        details: [
          { name: 'Текущая ликвидность', value: '1.42x', score: 52, note: 'Норма 1.5–2.5x (ниже нормы)' },
          { name: 'Быстрая ликвидность', value: '0.78x', score: 48 },
          { name: 'ICR (EBIT / Проценты)', value: '2.3x', score: 65 },
        ],
      },
      {
        key: 'B',
        label: 'Структурная устойчивость',
        score: 62,
        description: 'Устойчивость структуры капитала и долговая нагрузка',
        details: [
          { name: 'Debt/EBITDA', value: '4.2x', score: 60, note: 'Норма ≤ 5.0x для девелопмента' },
          { name: 'K_escrow (эскроу/ПФ-долг)', value: '82%', score: 72, note: '✅ Норматив ЦБ ≥ 75%' },
          { name: 'Доля СК в пассивах', value: '28%', score: 58 },
          { name: 'Покрытие долга активами', value: '1.35x', score: 55 },
        ],
      },
      {
        key: 'C',
        label: 'Рентабельность',
        score: 52,
        description: 'Способность бизнеса генерировать прибыль',
        details: [
          { name: 'EBITDA Margin', value: '12.1%', score: 58 },
          { name: 'ROE', value: '11.8%', score: 55 },
          { name: 'ROA', value: '3.4%', score: 45 },
        ],
      },
      {
        key: 'D',
        label: 'Денежный поток',
        score: 50,
        description: 'Реальность прибыли и качество денежных потоков',
        details: [
          { name: 'CFO / Чистая прибыль', value: '0.68x', score: 48, note: 'Риск качества прибыли' },
          { name: 'FCF (свободный денежный поток)', value: '-45 млн ₽', score: 38 },
          { name: 'CFO Margin', value: '8.2%', score: 62 },
        ],
      },
      {
        key: 'E',
        label: 'Облигационный профиль',
        score: 65,
        description: 'Безопасность конкретного облигационного выпуска',
        details: [
          { name: 'YTM vs ключевая ставка ЦБ', value: '+4.8% спред', score: 70 },
          { name: 'Срок до погашения', value: '3.5 года', score: 58 },
          { name: 'Объём торгов (ликвидность)', value: '6.2 млн/день', score: 65 },
        ],
      },
      {
        key: 'F',
        label: 'Качественная оценка',
        score: 55,
        description: 'Нефинансовые факторы: репутация, прозрачность, структура',
        details: [
          { name: 'Судебные дела (арбитраж)', value: '2 дела (несущественные)', score: 55 },
          { name: 'Раскрытие информации', value: 'Удовлетворительное', score: 58 },
          { name: 'Структура собственности', value: 'Частично раскрыта', score: 52 },
        ],
      },
    ],
    flags: [
      {
        key: 'ebitda_approximated',
        label: 'ℹ️ EBITDA приближённая',
        description: 'Амортизация не выделена в РСБУ-отчётности. EBITDA ≈ Прибыль от продаж.',
        active: true,
      },
      { key: 'bankruptcy_risk', label: '⚠️ Риск банкротства', description: '', active: false },
      { key: 'revenue_quality_risk', label: '⚠️ Риск качества выручки', description: '', active: false },
    ],
    bonds: [
      { isin: 'RU000A108AB1', name: 'Альфа Строй БО-02', ytm: 23.4, maturityDate: '01.10.2029', couponRate: 20.0, volume: 300 },
    ],
    disclaimer:
      'Оценка КФИ сформирована автоматически на основе публично доступных данных. Не является инвестиционной рекомендацией. Инвестирование в ВДО сопряжено с повышенным риском потери капитала.',
  },
  {
    id: 'mfo-bystro',
    name: 'ООО МФК «Быстро Деньги»',
    shortName: 'МФО Быстро',
    inn: '6319078432',
    industry: 'МФО',
    kfiBase: 47,
    kfiFinal: 43,
    category: 'Высокий риск',
    updatedAt: '15.04.2026',
    verifiedBy: 'MrGooRoo',
    verifiedAt: '15.04.2026',
    summary:
      'МФК с агрессивной моделью роста: портфель вырос на +68% г/г при снижении операционного денежного потока. Уровень NPL 90+ (18.5%) превышает норму. Норматив НМФК1 (8.2%) выполняется, но с минимальным запасом. Высокий риск для неопытных инвесторов.',
    blocks: [
      {
        key: 'A',
        label: 'Платёжная устойчивость',
        score: 42,
        description: 'Способность выполнять краткосрочные обязательства',
        details: [
          { name: 'Норматив НМФК1', value: '8.2%', score: 52, note: '✅ Норматив ЦБ ≥ 6% (минимальный запас)' },
          { name: 'Покрытие NPL резервами', value: '78%', score: 32, note: 'Норма ≥ 100% — не выполняется!' },
          { name: 'ICR (EBIT / Проценты)', value: '1.4x', score: 42 },
        ],
      },
      {
        key: 'B',
        label: 'Структурная устойчивость',
        score: 38,
        description: 'Устойчивость структуры капитала и долговая нагрузка',
        details: [
          { name: 'Финансовый леверидж', value: '5.8x', score: 42, note: 'Норма ≤ 5.0x — нарушена' },
          { name: 'NPL 90+ / Портфель', value: '18.5%', score: 28, note: 'Норма ≤ 15% — нарушена' },
          { name: 'Доля СК в пассивах', value: '14.7%', score: 44, note: 'Норма ≥ 15%' },
        ],
      },
      {
        key: 'C',
        label: 'Рентабельность',
        score: 60,
        description: 'Способность бизнеса генерировать прибыль',
        details: [
          { name: 'EBITDA Margin (по проц. доходу)', value: '34.2%', score: 72, note: 'МФО: знаменатель — процентные доходы' },
          { name: 'ROE', value: '16.4%', score: 62 },
          { name: 'ROA', value: '2.4%', score: 48 },
        ],
      },
      {
        key: 'D',
        label: 'Денежный поток',
        score: 35,
        description: 'Реальность прибыли и качество денежных потоков',
        details: [
          { name: 'CFO / Чистая прибыль', value: '0.41x', score: 28, note: '⚠️ Рост выручки +68% при падении CFO' },
          { name: 'FCF (свободный денежный поток)', value: '-312 млн ₽', score: 22 },
          { name: 'CFO Margin', value: '14.1%', score: 55 },
        ],
      },
      {
        key: 'E',
        label: 'Облигационный профиль',
        score: 58,
        description: 'Безопасность конкретного облигационного выпуска',
        details: [
          { name: 'YTM vs ключевая ставка ЦБ', value: '+6.2% спред', score: 62 },
          { name: 'Срок до погашения', value: '1.4 года', score: 68 },
          { name: 'Объём торгов (ликвидность)', value: '3.1 млн/день', score: 42 },
        ],
      },
      {
        key: 'F',
        label: 'Качественная оценка',
        score: 48,
        description: 'Нефинансовые факторы: репутация, прозрачность, структура',
        details: [
          { name: 'Судебные дела (арбитраж)', value: '7 дел, 3 существенных', score: 40 },
          { name: 'Раскрытие информации', value: 'Ограниченное', score: 42 },
          { name: 'Структура собственности', value: 'Частично раскрыта', score: 62 },
        ],
      },
    ],
    flags: [
      {
        key: 'revenue_quality_risk',
        label: '⚠️ Риск качества прибыли',
        description: 'Рост портфеля +68% г/г при снижении операционного денежного потока. Прибыль может быть бумажной.',
        active: true,
      },
      {
        key: 'bond_concentration_risk',
        label: '⚠️ Концентрация облигаций',
        description: 'Доля долга по облигациям составляет 64% от финансового долга. КФИ скорректирован на ×0.95.',
        active: true,
      },
      { key: 'bankruptcy_risk', label: '⚠️ Риск банкротства', description: '', active: false },
    ],
    bonds: [
      { isin: 'RU000A106XZ8', name: 'Быстро Деньги БО-03', ytm: 26.8, maturityDate: '20.09.2027', couponRate: 22.0, volume: 200 },
    ],
    disclaimer:
      'Оценка КФИ сформирована автоматически на основе публично доступных данных. Не является инвестиционной рекомендацией. Инвестирование в ВДО сопряжено с повышенным риском потери капитала.',
  },
  {
    id: 'torgovy-dom-nord',
    name: 'АО «Торговый Дом Норд»',
    shortName: 'ТД Норд',
    inn: '7812345678',
    industry: 'Торговля',
    kfiBase: 67,
    kfiFinal: 67,
    category: 'Стабильный',
    updatedAt: '17.04.2026',
    verifiedBy: 'MrGooRoo',
    verifiedAt: '17.04.2026',
    summary:
      'Региональный торговый дом с диверсифицированной товарной линейкой. Показатели ликвидности и долговой нагрузки соответствуют нормам. Умеренная рентабельность характерна для отрасли. Денежные потоки стабильны.',
    blocks: [
      {
        key: 'A',
        label: 'Платёжная устойчивость',
        score: 70,
        description: 'Способность выполнять краткосрочные обязательства',
        details: [
          { name: 'Текущая ликвидность', value: '1.78x', score: 72, note: 'Норма 1.5–2.5x ✓' },
          { name: 'Быстрая ликвидность', value: '1.02x', score: 68 },
          { name: 'ICR', value: '3.1x', score: 70 },
        ],
      },
      {
        key: 'B',
        label: 'Структурная устойчивость',
        score: 65,
        description: 'Устойчивость структуры капитала и долговая нагрузка',
        details: [
          { name: 'Debt/EBITDA', value: '2.8x', score: 70 },
          { name: 'D/E', value: '1.6x', score: 62 },
          { name: 'Доля СК в пассивах', value: '38%', score: 68 },
          { name: 'Покрытие активами', value: '1.72x', score: 62 },
        ],
      },
      {
        key: 'C',
        label: 'Рентабельность',
        score: 52,
        description: 'Способность бизнеса генерировать прибыль',
        details: [
          { name: 'EBITDA Margin', value: '9.2%', score: 55, note: 'Торговля: норма > 8%' },
          { name: 'ROE', value: '12.1%', score: 58 },
          { name: 'ROA', value: '4.6%', score: 44 },
        ],
      },
      {
        key: 'D',
        label: 'Денежный поток',
        score: 72,
        description: 'Реальность прибыли и качество денежных потоков',
        details: [
          { name: 'CFO / Чистая прибыль', value: '1.08x', score: 78 },
          { name: 'FCF', value: '+94 млн ₽', score: 70 },
          { name: 'CFO Margin', value: '9.9%', score: 68 },
        ],
      },
      {
        key: 'E',
        label: 'Облигационный профиль',
        score: 72,
        description: 'Безопасность конкретного облигационного выпуска',
        details: [
          { name: 'YTM vs ключевая ставка ЦБ', value: '+2.9% спред', score: 75 },
          { name: 'Срок до погашения', value: '1.8 года', score: 72 },
          { name: 'Объём торгов', value: '11.3 млн/день', score: 70 },
        ],
      },
      {
        key: 'F',
        label: 'Качественная оценка',
        score: 68,
        description: 'Нефинансовые факторы: репутация, прозрачность, структура',
        details: [
          { name: 'Судебные дела', value: 'Нет существенных', score: 72 },
          { name: 'Раскрытие информации', value: 'Хорошее', score: 70 },
          { name: 'Структура собственности', value: 'Прозрачная', score: 62 },
        ],
      },
    ],
    flags: [
      { key: 'bankruptcy_risk', label: '⚠️ Риск банкротства', description: '', active: false },
      { key: 'revenue_quality_risk', label: '⚠️ Риск качества выручки', description: '', active: false },
      { key: 'ebitda_approximated', label: 'ℹ️ EBITDA приближённая', description: 'Амортизация приближена по пояснениям.', active: true },
    ],
    bonds: [
      { isin: 'RU000A105KL3', name: 'ТД Норд БО-01', ytm: 18.9, maturityDate: '12.03.2028', couponRate: 17.5, volume: 400 },
    ],
    disclaimer:
      'Оценка КФИ сформирована автоматически на основе публично доступных данных. Не является инвестиционной рекомендацией. Инвестирование в ВДО сопряжено с повышенным риском потери капитала.',
  },
  {
    id: 'promstanok',
    name: 'ООО «ПромСтанок»',
    shortName: 'ПромСтанок',
    inn: '6612098712',
    industry: 'Производство',
    kfiBase: 82,
    kfiFinal: 82,
    category: 'Надёжный',
    updatedAt: '19.04.2026',
    verifiedBy: 'MrGooRoo',
    verifiedAt: '19.04.2026',
    summary:
      'Производитель промышленного оборудования с устойчивыми финансовыми показателями. Низкая долговая нагрузка, высокий операционный денежный поток. Импортозамещение создаёт дополнительный спрос. Флагманский эмитент в рейтинге КФИ.',
    blocks: [
      {
        key: 'A',
        label: 'Платёжная устойчивость',
        score: 84,
        description: 'Способность выполнять краткосрочные обязательства',
        details: [
          { name: 'Текущая ликвидность', value: '2.1x', score: 85 },
          { name: 'Быстрая ликвидность', value: '1.38x', score: 82 },
          { name: 'ICR', value: '5.2x', score: 88 },
        ],
      },
      {
        key: 'B',
        label: 'Структурная устойчивость',
        score: 85,
        description: 'Устойчивость структуры капитала и долговая нагрузка',
        details: [
          { name: 'Debt/EBITDA', value: '1.4x', score: 90 },
          { name: 'D/E', value: '0.7x', score: 88 },
          { name: 'Доля СК в пассивах', value: '58%', score: 85 },
          { name: 'Покрытие активами', value: '2.4x', score: 80 },
        ],
      },
      {
        key: 'C',
        label: 'Рентабельность',
        score: 76,
        description: 'Способность бизнеса генерировать прибыль',
        details: [
          { name: 'EBITDA Margin', value: '22.8%', score: 82 },
          { name: 'ROE', value: '18.4%', score: 72 },
          { name: 'ROA', value: '10.7%', score: 76 },
        ],
      },
      {
        key: 'D',
        label: 'Денежный поток',
        score: 80,
        description: 'Реальность прибыли и качество денежных потоков',
        details: [
          { name: 'CFO / Чистая прибыль', value: '1.22x', score: 84 },
          { name: 'FCF', value: '+487 млн ₽', score: 82 },
          { name: 'CFO Margin', value: '19.6%', score: 76 },
        ],
      },
      {
        key: 'E',
        label: 'Облигационный профиль',
        score: 78,
        description: 'Безопасность конкретного облигационного выпуска',
        details: [
          { name: 'YTM vs ключевая ставка ЦБ', value: '+2.1% спред', score: 80 },
          { name: 'Срок до погашения', value: '2.8 года', score: 75 },
          { name: 'Объём торгов', value: '24.6 млн/день', score: 82 },
        ],
      },
      {
        key: 'F',
        label: 'Качественная оценка',
        score: 80,
        description: 'Нефинансовые факторы: репутация, прозрачность, структура',
        details: [
          { name: 'Судебные дела', value: 'Нет', score: 90 },
          { name: 'Раскрытие информации', value: 'Высокое', score: 82 },
          { name: 'Структура собственности', value: 'Полностью раскрыта', score: 70 },
        ],
      },
    ],
    flags: [
      { key: 'bankruptcy_risk', label: '⚠️ Риск банкротства', description: '', active: false },
      { key: 'revenue_quality_risk', label: '⚠️ Риск качества выручки', description: '', active: false },
    ],
    bonds: [
      { isin: 'RU000A109PQ2', name: 'ПромСтанок БО-01', ytm: 17.6, maturityDate: '30.07.2029', couponRate: 16.5, volume: 750 },
    ],
    disclaimer:
      'Оценка КФИ сформирована автоматически на основе публично доступных данных. Не является инвестиционной рекомендацией. Инвестирование в ВДО сопряжено с повышенным риском потери капитала.',
  },
  {
    id: 'transnord-logistic',
    name: 'ООО «ТрансНорд Логистик»',
    shortName: 'ТрансНорд',
    inn: '7804321098',
    industry: 'Транспорт',
    kfiBase: 32,
    kfiFinal: 30,
    category: 'Критический',
    updatedAt: '12.04.2026',
    verifiedBy: 'MrGooRoo',
    verifiedAt: '12.04.2026',
    summary:
      'Транспортная компания в предкризисном состоянии. Блок A (ликвидность) провален — ICR 0.9x означает, что EBIT не покрывает даже проценты. Два слабых блока (A и D) автоматически ограничивают КФИ. Флаг data_missing применён из-за отсутствия ОДДС за последний период.',
    blocks: [
      {
        key: 'A',
        label: 'Платёжная устойчивость',
        score: 18,
        description: 'Способность выполнять краткосрочные обязательства',
        details: [
          { name: 'Текущая ликвидность', value: '0.82x', score: 12, note: '🔴 Критично: ОА < КО' },
          { name: 'Быстрая ликвидность', value: '0.51x', score: 18 },
          { name: 'ICR', value: '0.9x', score: 8, note: '🔴 EBIT не покрывает проценты!' },
        ],
      },
      {
        key: 'B',
        label: 'Структурная устойчивость',
        score: 35,
        description: 'Устойчивость структуры капитала и долговая нагрузка',
        details: [
          { name: 'Debt/EBITDA', value: '6.8x', score: 28, note: 'Норма ≤ 3.5x' },
          { name: 'D/E', value: '4.2x', score: 22 },
          { name: 'Доля СК в пассивах', value: '19%', score: 42 },
          { name: 'Покрытие активами', value: '1.18x', score: 48 },
        ],
      },
      {
        key: 'C',
        label: 'Рентабельность',
        score: 42,
        description: 'Способность бизнеса генерировать прибыль',
        details: [
          { name: 'EBITDA Margin', value: '6.4%', score: 38 },
          { name: 'ROE', value: '4.2%', score: 35 },
          { name: 'ROA', value: '0.8%', score: 52 },
        ],
      },
      {
        key: 'D',
        label: 'Денежный поток',
        score: 22,
        description: 'Реальность прибыли и качество денежных потоков',
        details: [
          { name: 'CFO / Чистая прибыль', value: '0.28x', score: 18 },
          { name: 'FCF', value: '-218 млн ₽', score: 12 },
          { name: 'CFO Margin', value: '1.8%', score: 38 },
        ],
      },
      {
        key: 'E',
        label: 'Облигационный профиль',
        score: 48,
        description: 'Безопасность конкретного облигационного выпуска',
        details: [
          { name: 'YTM vs ключевая ставка ЦБ', value: '+9.4% спред', score: 55, note: 'Высокий спред = высокий риск' },
          { name: 'Срок до погашения', value: '0.8 года', score: 72 },
          { name: 'Объём торгов', value: '1.2 млн/день', score: 22, note: 'Низкая ликвидность' },
        ],
      },
      {
        key: 'F',
        label: 'Качественная оценка',
        score: 32,
        description: 'Нефинансовые факторы: репутация, прозрачность, структура',
        details: [
          { name: 'Судебные дела', value: '12 дел, в т.ч. 4 существенных', score: 22 },
          { name: 'Раскрытие информации', value: 'Неполное (ОДДС отсутствует)', score: 28 },
          { name: 'Структура собственности', value: 'Не раскрыта', score: 45 },
        ],
      },
    ],
    flags: [
      {
        key: 'data_missing',
        label: '⚠️ Отсутствие данных',
        description: 'ОДДС за последний отчётный период не опубликован на e-disclosure. Применён штраф ×0.90 к КФИ.',
        active: true,
      },
      {
        key: 'bankruptcy_risk',
        label: '🔴 Риск банкротства',
        description: 'Зафиксированы существенные арбитражные иски. КФИ ограничен значением ≤ 30.',
        active: false,
      },
    ],
    bonds: [
      { isin: 'RU000A104WN7', name: 'ТрансНорд БО-02', ytm: 34.2, maturityDate: '05.01.2027', couponRate: 19.0, volume: 150 },
    ],
    disclaimer:
      'Оценка КФИ сформирована автоматически на основе публично доступных данных. Не является инвестиционной рекомендацией. Инвестирование в ВДО сопряжено с повышенным риском потери капитала.',
  },
];
