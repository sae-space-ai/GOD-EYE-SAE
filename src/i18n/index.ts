import esES from './locales/es-ES';
import enUS from './locales/en-US';

export type Locale = 'es-ES' | 'en-US';

export const translations: Record<Locale, typeof esES> = {
  'es-ES': esES,
  'en-US': enUS,
};

export function t(key: string, locale: Locale = 'es-ES'): string {
  const keys = key.split('.');
  let value: any = translations[locale];
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      return key;
    }
  }
  return typeof value === 'string' ? value : key;
}

export function getLocaleName(locale: Locale): string {
  switch (locale) {
    case 'es-ES': return 'Español';
    case 'en-US': return 'English';
    default: return locale;
  }
}

export { esES, enUS };
export default t;
