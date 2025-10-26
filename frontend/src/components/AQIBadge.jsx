import React from 'react'

function pickLevelFromCategory(category) {
  if (!category) return 'unknown'
  const c = category.toLowerCase()
  if (c.includes('buena') || c.includes('good')) return 'good'
  if (c.includes('moderada') || c.includes('moderate')) return 'moderate'
  return 'bad'
}

export default function AQIBadge({ label, value, category }) {
  const level = pickLevelFromCategory(category)
  return (
    <div className={`aqi-badge ${level}`}>
      <div className="aqi-emoji">
        {level === 'good' ? '🟢' : level === 'moderate' ? '🟡' : '🔴'}
      </div>
      <div className="aqi-info">
        <div className="aqi-label">{label}</div>
        <div className="aqi-value">{value ?? '—'}</div>
        <div className="aqi-cat">{category || 'Sin datos'}</div>
      </div>
    </div>
  )
}
