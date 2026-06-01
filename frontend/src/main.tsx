import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { readPreferences } from './lib/storage'
import { applyPreferencesToDocument } from './lib/applyPreferences'
import { PreferencesProvider } from './lib/PreferencesContext'

// Aplica tema + tamaño de fuente al <html> ANTES de montar React, para evitar
// el parpadeo (FOUC) del tema/tamaño anterior al recargar.
applyPreferencesToDocument(readPreferences())

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <PreferencesProvider>
      <App />
    </PreferencesProvider>
  </StrictMode>,
)
