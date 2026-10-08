import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { I18nProvider } from './i18n/I18nContext';
import { AppRoutes } from './routes/AppRoutes';

export const App = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <I18nProvider>
            <BrowserRouter>
              <AppRoutes />
            </BrowserRouter>
          </I18nProvider>
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  );
};


export default App;
