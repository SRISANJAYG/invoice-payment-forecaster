const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;
const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/invoice-forecaster';

// Middleware
app.use(cors());
app.use(express.json());

// Health check route
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Invoice Forecaster API is running' });
});

// Routes
const forecastRouter = require('./routes/forecast');
app.use('/api/forecast', forecastRouter);

// Connect to MongoDB and start server
mongoose
  .connect(MONGO_URI)
  .then(() => {
    console.log('✅ Connected to MongoDB');
    app.listen(PORT, () => console.log(`🚀 Server running on http://localhost:${PORT}`));
  })
  .catch((err) => {
    console.warn('⚠️  MongoDB not available, starting without DB:', err.message);
    app.listen(PORT, () => console.log(`🚀 Server running (no DB) on http://localhost:${PORT}`));
  });
