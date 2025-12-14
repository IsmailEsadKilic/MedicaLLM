import { Router } from 'express';
import { authMiddleware, AuthRequest } from '../middleware/auth';
import { 
  createConversation, 
  getUserConversations, 
  getConversation,
  addMessage,
  updateTitle,
  deleteConversation 
} from '../services/conversationService';

const router = Router();

// Apply auth middleware to all routes
router.use(authMiddleware);

// Get all conversations for user
router.get('/', async (req, res) => {
  try {
    const userId = (req as AuthRequest).userId;
    if (!userId) return res.status(401).json({ error: 'Unauthorized' });
    
    const conversations = await getUserConversations(userId);
    res.json(conversations);
  } catch (error) {
    res.status(500).json({ error: String(error) });
  }
});

// Create new conversation
router.post('/', async (req, res) => {
  try {
    const userId = (req as AuthRequest).userId;
    if (!userId) return res.status(401).json({ error: 'Unauthorized' });
    
    const { title } = req.body;
    const chatId = await createConversation(userId, title);
    res.json({ chat_id: chatId });
  } catch (error) {
    res.status(500).json({ error: String(error) });
  }
});

// Get specific conversation
router.get('/:chatId', async (req, res) => {
  try {
    const userId = (req as AuthRequest).userId;
    if (!userId) return res.status(401).json({ error: 'Unauthorized' });
    
    const conversation = await getConversation(userId, req.params.chatId);
    if (!conversation) return res.status(404).json({ error: 'Not found' });
    
    res.json(conversation);
  } catch (error) {
    res.status(500).json({ error: String(error) });
  }
});

// Add message to conversation
router.post('/:chatId/messages', async (req, res) => {
  try {
    const userId = (req as AuthRequest).userId;
    if (!userId) return res.status(401).json({ error: 'Unauthorized' });
    
    const { message } = req.body;
    await addMessage(userId, req.params.chatId, message);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: String(error) });
  }
});

// Update conversation title
router.patch('/:chatId/title', async (req, res) => {
  try {
    const userId = (req as AuthRequest).userId;
    if (!userId) return res.status(401).json({ error: 'Unauthorized' });
    
    const { title } = req.body;
    await updateTitle(userId, req.params.chatId, title);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: String(error) });
  }
});

// Delete conversation
router.delete('/:chatId', async (req, res) => {
  try {
    const userId = (req as AuthRequest).userId;
    if (!userId) return res.status(401).json({ error: 'Unauthorized' });
    
    await deleteConversation(userId, req.params.chatId);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: String(error) });
  }
});

export default router;
