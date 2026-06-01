import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './lib/i18n'
import App from './App.tsx'
import { readPreferences } from './lib/storage'
import { applyPreferencesToDocument } from './lib/applyPreferences'
import { PreferencesProvider } from './lib/PreferencesContext'

// Aplica tema + tamaño de fuente + idioma al <html> ANTES de montar React, para
// evitar el parpadeo (FOUC) del tema/tamaño anterior al recargar. i18n se
// importa también aquí (su init lee el idioma de prefs) para estar listo al
// primer render.
applyPreferencesToDocument(readPreferences())

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <PreferencesProvider>
      <App />
    </PreferencesProvider>
  </StrictMode>,
)
