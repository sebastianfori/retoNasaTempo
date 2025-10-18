import express from 'express';
import cors from 'cors';
import morgan from 'morgan';

const app = express();
app.use(cors());
app.use(express.json());
app.use(morgan('tiny'));

app.get('/health', (req, res) => {
  res.json({ ok: true, service: 'aireclaro-api' });
});

app.post('/api/locations', (req, res) => {
  const { latitude, longitude } = req.body || {};
  if (typeof latitude !== 'number' || typeof longitude !== 'number') {
    return res.status(400).json({ ok: false, error: 'latitude/longitude inválidos' });
  }

  console.log('[POST /api/locations]', { latitude, longitude });

  return res.json({
    ok: true,
    received: { latitude, longitude },
    message: 'Coordenadas recibidas correctamente'
  });
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log(`API escuchando en http://0.0.0.0:${PORT}`));
