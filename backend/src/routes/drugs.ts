import { Router } from 'express';
import { queryAgent } from '../services/agentApiService';

const router = Router();

// AI agent query - proxy to agent API
router.post('/query', async (req, res) => {
  try {
    const { query, conversation_id } = req.body;
    
    if (!query) {
      return res.status(400).json({ error: 'Query is required' });
    }

    if (!conversation_id) {
      return res.status(400).json({ error: 'Conversation ID is required' });
    }

    const result = await queryAgent(conversation_id, query);
    
    res.json({
      answer: result.answer,
      tool_used: result.tool_used,
      sources: result.sources
    });
  } catch (error) {
    console.error('Query error:', error);
    res.status(500).json({ error: String(error) });
  }
});

// Generate title - simplified
router.post('/generate-title', async (req, res) => {
  try {
    const { message } = req.body;
    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }
    const words = message.split(' ').slice(0, 5).join(' ');
    const title = words.length > 30 ? words.slice(0, 27) + '...' : words;
    res.json({ title });
  } catch (error) {
    res.status(500).json({ error: String(error) });
  }
});

export default router;
