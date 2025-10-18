import React, { useState } from 'react'
import MapPicker from './components/MapPicker'
import { sendCoordinates } from './api'

export default function App() {
  const [coords, setCoords] = useState(null)
  const [sending, setSending] = useState(false)
  const [response, setResponse] = useState(null)
  const [error, setError] = useState(null)

  const handleSend = async () => {
    if (!coords) return
    setSending(true)
    setError(null)
    setResponse(null)
    try {
      const res = await sendCoordinates(coords)
      setResponse(res)
    } catch (e) {
      setError(e?.message || 'Error enviando coordenadas')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="page">
      <header className="header">
        <h1>AireClaro</h1>
        <p className="subtitle">Seleccioná un punto en Norteamérica y enviá sus coordenadas</p>
      </header>

      <section className="map-card">
        <MapPicker onPick={setCoords} />
      </section>

      <section className="panel">
        <div className="coords">
          <span className="label">Latitud:</span>
          <span>{coords ? coords.latitude.toFixed(6) : '—'}</span>
          <span className="label">Longitud:</span>
          <span>{coords ? coords.longitude.toFixed(6) : '—'}</span>
        </div>
        <button className="btn" disabled={!coords || sending} onClick={handleSend}>
          {sending ? 'Enviando…' : 'Enviar'}
        </button>
      </section>

      {error && <div className="alert error">{error}</div>}
      {response && (
        <div className="alert ok">
          <strong>Respuesta API:</strong>
          <pre>{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}

      <footer className="footer">Listo para extender a más páginas.</footer>
    </div>
  )
}
