import { Router } from 'express';
import { getDrugInfo, checkDrugInteraction } from '../services/drugService';
import { processQuery } from '../services/aiService';
import { generateTitle } from '../services/titleService';

const router = Router();

// Get drug information
router.get('/info/:drugName', async (req, res) => {
  try {
    const result = await getDrugInfo(req.params.drugName);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: String(error) });
  }
});

// Check drug interaction
router.get('/interaction/:drug1/:drug2', async (req, res) => {
  try {
    const result = await checkDrugInteraction(req.params.drug1, req.params.drug2);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: String(error) });
  }
});

// AI agent query
router.post('/query', async (req, res) => {
  try {
    const { query } = req.body;
    if (!query) {
      return res.status(400).json({ error: 'Query is required' });
    }
    const result = await processQuery(query);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: String(error) });
  }
});

// Generate conversation title
router.post('/generate-title', async (req, res) => {
  try {
    const { message } = req.body;
    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }
    const title = await generateTitle(message);
    res.json({ title });
  } catch (error) {
    res.status(500).json({ error: String(error) });
  }
});

export default router;
