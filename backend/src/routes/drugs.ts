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

// Analyze patient profile
router.post('/analyze-patient', async (req, res) => {
  try {
    const { chronic_conditions, allergies, current_medications } = req.body;
    
    const response = await fetch(`${process.env.AGENT_API_URL}/api/analyze-patient`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chronic_conditions, allergies, current_medications })
    });
    
    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('Patient analysis error:', error);
    res.status(500).json({ error: String(error) });
  }
});

// Generate title using LLM
router.post('/generate-title', async (req, res) => {
  try {
    const { message } = req.body;
    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }
    
    const response = await fetch('http://host.docker.internal:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'llama3.1',
        prompt: `Generate a short, concise title (3-6 words) for this medical question: "${message}". Return ONLY the title, nothing else.`,
        stream: false
      })
    });
    
    const data = await response.json();
    let title = data.response?.trim().replace(/["']/g, '') || message.slice(0, 50);
    if (title.length > 60) title = title.slice(0, 57) + '...';
    
    res.json({ title });
  } catch (error) {
    console.error('Title generation error:', error);
    const { message } = req.body;
    const fallback = message?.split(' ').slice(0, 5).join(' ') || 'New Chat';
    res.json({ title: fallback.length > 30 ? fallback.slice(0, 27) + '...' : fallback });
  }
});

export default router;
