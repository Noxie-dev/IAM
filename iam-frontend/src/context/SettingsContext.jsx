import React, { createContext, useState, useEffect, useMemo, useContext } from 'react';

export const SettingsContext = createContext();

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

export const SettingsProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => localStorage.getItem('iam-theme') || 'dark');
  const [fontSize, setFontSize] = useState(() => localStorage.getItem('iam-font-size') || 'medium');
  const [highContrast, setHighContrast] = useState(() => localStorage.getItem('iam-high-contrast') === 'true');
  const [reducedMotion, setReducedMotion] = useState(() => localStorage.getItem('iam-reduced-motion') === 'true');

  useEffect(() => {
    localStorage.setItem('iam-theme', theme);
    const body = document.body;
    body.classList.remove('theme-light', 'theme-dark');
    body.classList.add(`theme-${theme}`);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('iam-font-size', fontSize);
    const body = document.body;
    body.classList.remove('font-size-small', 'font-size-medium', 'font-size-large');
    body.classList.add(`font-size-${fontSize}`);
  }, [fontSize]);

  useEffect(() => {
    localStorage.setItem('iam-high-contrast', highContrast);
    document.body.classList.toggle('high-contrast', highContrast);
  }, [highContrast]);

  useEffect(() => {
    localStorage.setItem('iam-reduced-motion', reducedMotion);
    document.body.classList.toggle('reduced-motion', reducedMotion);
  }, [reducedMotion]);

  const value = useMemo(() => ({
    theme, setTheme,
    fontSize, setFontSize,
    highContrast, setHighContrast,
    reducedMotion, setReducedMotion
  }), [theme, fontSize, highContrast, reducedMotion]);

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};




