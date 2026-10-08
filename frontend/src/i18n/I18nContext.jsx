import React, { createContext, useContext, useState, useEffect } from 'react';
import { translations } from './translations';

const I18nContext = createContext(null);

export const I18nProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('spaceloop_lang') || 'en';
  });

  useEffect(() => {
    localStorage.setItem('spaceloop_lang', language);
    document.documentElement.lang = language;
  }, [language]);

  const t = (key) => {
    const langDict = translations[language] || translations.en;
    if (langDict[key]) return langDict[key];
    return translations.en[key] || key;
  };

  const formatCurrency = (amount) => {
    const num = Number(amount) || 0;
    return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      const locale = language === 'mr' ? 'mr-IN' : ['hi', 'gsw', 'kfy', 'jns'].includes(language) ? 'hi-IN' : 'en-IN';
      return d.toLocaleDateString(locale, {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <I18nContext.Provider value={{ language, setLanguage, t, formatCurrency, formatDate }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = () => {
  const context = useContext(I18nContext);
  if (!context) {
    return {
      language: 'en',
      setLanguage: () => {},
      t: (k) => translations.en[k] || k,
      formatCurrency: (n) => `₹${Number(n || 0).toFixed(2)}`,
      formatDate: (d) => String(d),
    };
  }
  return context;
};

export default I18nContext;
