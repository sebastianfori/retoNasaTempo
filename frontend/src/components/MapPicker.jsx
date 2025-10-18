import React, { useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix de íconos para Leaflet en bundlers
import markerIcon2xUrl from 'leaflet/dist/images/marker-icon-2x.png'
import markerIconUrl from 'leaflet/dist/images/marker-icon.png'
import markerShadowUrl from 'leaflet/dist/images/marker-shadow.png'

const defaultIcon = new L.Icon({
  iconUrl: markerIconUrl,
  iconRetinaUrl: markerIcon2xUrl,
  shadowUrl: markerShadowUrl,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  tooltipAnchor: [16, -28],
  shadowSize: [41, 41]
})
L.Marker.prototype.options.icon = defaultIcon

function ClickHandler({ onPick }) {
  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng
      onPick({ latitude: lat, longitude: lng })
    }
  })
  return null
}

export default function MapPicker({ onPick }) {
  const [position, setPosition] = useState(null)

  const boundsNA = useMemo(
    () => L.latLngBounds(L.latLng(5, -167), L.latLng(83, -10)),
    []
  )

  useEffect(() => {
    if (onPick && position) onPick({ latitude: position.lat, longitude: position.lng })
  }, [position, onPick])

  return (
    <div className="map-wrap">
      <MapContainer
        center={[39.8, -98.6]} // centro aproximado de Norteamérica
        zoom={4}
        minZoom={3}
        maxBounds={boundsNA}
        className="map"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ClickHandler onPick={({ latitude, longitude }) => setPosition({ lat: latitude, lng: longitude })} />
        {position && <Marker position={position} />}
      </MapContainer>
    </div>
  )
}
