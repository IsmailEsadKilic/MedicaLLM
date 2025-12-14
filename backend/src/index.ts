import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import itemsRouter from './routes/items';
import authRouter from './routes/auth';
import drugsRouter from './routes/drugs';
import conversationsRouter from './routes/conversations';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Backend is running' });
});

app.use('/api/auth', authRouter);
app.use('/api/items', itemsRouter);
app.use('/api/drugs', drugsRouter);
app.use('/api/conversations', conversationsRouter);

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
