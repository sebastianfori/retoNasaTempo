import React, { useEffect, useMemo, useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import { fetchAQI } from '../api'
import AQIBadge from '../components/AQIBadge'

function useQuery() {
  const { search } = useLocation()
  return useMemo(() => new URLSearchParams(search), [search])
}

function pickBanner(category) {
  if (!category) return 'banner-neutral'
  const c = category.toLowerCase()
  if (c.includes('buena') || c.includes('good')) return 'banner-good'
  if (c.includes('moderada') || c.includes('moderate')) return 'banner-moderate'
  return 'banner-bad'
}

export default function ResultPage() {
  const q = useQuery()
  const lat = parseFloat(q.get('lat'))
  const lon = parseFloat(q.get('lon'))

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)

  useEffect(() => {
    let mounted = true
    async function run() {
      try {
        setLoading(true); setError(null)
        const res = await fetchAQI(lat, lon)
        if (mounted) setData(res)
      } catch (e) {
        if (mounted) setError(e.message || 'Error consultando AQI')
      } finally {
        if (mounted) setLoading(false)
      }
    }
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      setError('Parámetros inválidos'); setLoading(false)
      return
    }
    run()
    return () => { mounted = false }
  }, [lat, lon])

  const surface = data?.aqi?.surface_aqi
  const tempo = data?.aqi?.tempo_aqi
  const globalVal = data?.aqi?.global_aqi
  const bannerClass = pickBanner(surface?.category || tempo?.tempo_aqi_category)

  return (
    <div className="page">
      <header className="header">
        <h1>AireClaro</h1>
        <p className="subtitle">Resultados para ({lat?.toFixed(4)}, {lon?.toFixed(4)})</p>
      </header>

      <div className={`banner ${bannerClass}`}>
        <div className="banner-art" aria-hidden>
          {/* SVG decorativo inline, cambia color con la clase */}
          <svg viewBox="0 0 200 200">
            <path d="M40,-60C52,-50,62,-40,70,-26C78,-12,84,5,79,18C73,31,56,41,40,51C25,62,12,73,-2,76C-16,78,-33,72,-47,62C-60,52,-71,37,-75,20C-79,2,-76,-18,-66,-33C-57,-48,-40,-58,-24,-67C-9,-76,6,-85,20,-86C34,-86,48,-78,40,-60Z"></path>
          </svg>
        </div>
        <div className="banner-content">
          {loading && <h2>Cargando calidad del aire…</h2>}
          {error && <h2>Error: {error}</h2>}
          {!loading && !error && (
            <>
              <h2>
                {surface?.category
                  ? `Calidad del aire: ${surface.category}`
                  : tempo?.tempo_aqi_category
                    ? `Calidad del aire (TEMPO): ${tempo.tempo_aqi_category}`
                    : 'Calidad del aire: Sin datos'}
              </h2>
              <p>Índice global estimado: <strong>{globalVal ?? '—'}</strong></p>
            </>
          )}
        </div>
      </div>

      {!loading && !error && (
        <>
          <section className="cards">
            <AQIBadge
              label="Superficie (OpenAQ)"
              value={surface?.aqi_value}
              category={surface?.category}
            />
            <AQIBadge
              label="Troposférico (TEMPO)"
              value={tempo?.tempo_aqi_value}
              category={tempo?.tempo_aqi_category}
            />
          </section>

          <section className="grid">
            <div className="card">
              <h3>Estación cercana</h3>
              {data?.station ? (
                <ul className="kv">
                  <li><span>Nombre</span><b>{data.station.name}</b></li>
                  <li><span>Distancia</span><b>{data.station.distance_km?.toFixed(2)} km</b></li>
                  <li><span>ID</span><b>{data.station.id}</b></li>
                </ul>
              ) : <p>Sin datos de estación.</p>}
            </div>

            <div className="card">
              <h3>Mediciones recientes</h3>
              {data?.latest_measurements?.length ? (
                <table className="tbl">
                  <thead><tr><th>Parámetro</th><th>Valor</th><th>Fecha</th></tr></thead>
                  <tbody>
                    {data.latest_measurements.map((m, i) => (
                      <tr key={i}>
                        <td>{m.parameter}</td>
                        <td>{m.value} {m.units}</td>
                        <td>{m.datetime}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : <p>Sin mediciones disponibles.</p>}
            </div>

            <div className="card">
              <h3>Datos TEMPO (píxel cercano)</h3>
              {data?.tempo_data ? (
                <ul className="kv">
                  <li><span>NO₂</span><b>{data.tempo_data.no2 ?? '—'}</b></li>
                  <li><span>O₃ total</span><b>{data.tempo_data.o3tot ?? '—'}</b></li>
                  <li><span>HCHO</span><b>{data.tempo_data.hcho ?? '—'}</b></li>
                  <li><span>Distancia (°)</span><b>{Number(data.tempo_data.distance_deg)?.toFixed(4) ?? '—'}</b></li>
                </ul>
              ) : <p>Sin datos TEMPO.</p>}
            </div>
          </section>
        </>
      )}

      <div className="actions">
        <Link to="/" className="btn">Elegir otra ubicación</Link>
      </div>
    </div>
  )
}
