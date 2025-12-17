import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import itemsRouter from './routes/items';
import authRouter from './routes/auth';
import drugsRouter from './routes/drugs';
import conversationsRouter from './routes/conversations';
import drugSearchRouter from './routes/drugSearch';
import patientsRouter from './routes/patients';
import { initTables } from './db/init';
import { authMiddleware } from './middleware/auth';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    message: 'Backend proxy is running',
    agent_api_url: process.env.AGENT_API_URL || 'http://localhost:2580'
  });
});

app.use('/api/auth', authRouter);
app.use('/api/items', itemsRouter);
app.use('/api/drugs', drugsRouter);
app.use('/api/conversations', conversationsRouter);
app.use('/api/drug-search', drugSearchRouter);
app.use('/api/patients', authMiddleware, patientsRouter);

app.listen(PORT, async () => {
  console.log(`Backend proxy server running on port ${PORT}`);
  console.log(`Agent API URL: ${process.env.AGENT_API_URL || 'http://localhost:2580'}`);
  await initTables();
});
