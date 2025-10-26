import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

import MapPage from './pages/MapPage'
import ResultPage from './pages/ResultPage'
import Login from './pages/Login'                 // 👈 nuevo
import RequireAuth from './auth/RequireAuth'      // 👈 nuevo
import { AuthProvider } from './auth/AuthContext' // 👈 nuevo

import './styles.css'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* pública */}
          <Route path="/login" element={<Login />} />

          {/* protegidas */}
          <Route
            path="/"
            element={
              <RequireAuth>
                <MapPage />
              </RequireAuth>
            }
          />
          <Route
            path="/result"
            element={
              <RequireAuth>
                <ResultPage />
              </RequireAuth>
            }
          />

          {/* opcional: 404 */}
          {/* <Route path="*" element={<Navigate to="/" replace />} /> */}
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>
)
