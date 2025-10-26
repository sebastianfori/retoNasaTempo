const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchAQI(lat, lon) {
  const url = new URL(`${BASE_URL}/aqi`);
  url.searchParams.set('lat', lat);
  url.searchParams.set('lon', lon);

  const res = await fetch(url.toString(), { method: 'GET' });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}
