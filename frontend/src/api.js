const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export async function sendCoordinates({ latitude, longitude }) {
  const res = await fetch(`${BASE_URL}/api/locations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ latitude, longitude })
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}
