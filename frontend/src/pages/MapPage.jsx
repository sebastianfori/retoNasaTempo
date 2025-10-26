import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import MapPicker from '../components/MapPicker'

export default function MapPage() {
  const [coords, setCoords] = useState(null)
  const navigate = useNavigate()

  const goResult = () => {
    if (!coords) return
    const q = new URLSearchParams({
      lat: coords.latitude.toString(),
      lon: coords.longitude.toString(),
    })
    navigate(`/result?${q.toString()}`)
  }

  return (
    <div className="page">
      <header className="header">
        <h1>AireClaro</h1>
        <p className="subtitle">Seleccioná un punto en Norteamérica y consultá el AQI</p>
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
        <button className="btn" disabled={!coords} onClick={goResult}>
          Enviar
        </button>
      </section>

      <footer className="footer">Hecho para crecer: rutas, detalles y visualizaciones.</footer>
    </div>
  )
}
