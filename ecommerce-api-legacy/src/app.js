const express = require('express');
const settings = require('./config/settings');
const { getDb } = require('./database/connection');
const routes = require('./routes/index');
const { errorHandler } = require('./middlewares/errorHandler');

const app = express();
app.use(express.json());

// Initialize DB on startup
getDb().then(() => {
    console.log('Database initialized.');
}).catch(err => {
    console.error('Failed to initialize database:', err.message);
    process.exit(1);
});

app.use('/api', routes);

app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
});

app.use(errorHandler);

app.listen(settings.port, () => {
    console.log(`LMS API running on port ${settings.port}`);
});
