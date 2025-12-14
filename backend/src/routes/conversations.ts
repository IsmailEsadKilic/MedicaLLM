import { Router } from 'express';
import { authMiddleware, AuthRequest } from '../middleware/auth';
import {
  createConversation,
  getUserConversations,
  getConversation,
  updateConversationTitle,
  deleteConversation,
  addMessage
} from '../services/agentApiService';

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
    console.error('Error getting conversations:', error);
    res.status(500).json({ error: String(error) });
  }
});

// Create new conversation
router.post('/', async (req, res) => {
  try {
    const userId = (req as AuthRequest).userId;
    if (!userId) return res.status(401).json({ error: 'Unauthorized' });

    const { title } = req.body;
    const chatId = await createConversation(userId, title || 'New Chat');
    res.json({ chat_id: chatId });
  } catch (error) {
    console.error('Error creating conversation:', error);
    res.status(500).json({ error: String(error) });
  }
});

// Get specific conversation
router.get('/:chatId', async (req, res) => {
  try {
    const userId = (req as AuthRequest).userId;
    if (!userId) return res.status(401).json({ error: 'Unauthorized' });

    const conversation = await getConversation(req.params.chatId);

    // Verify the conversation belongs to the user
    if (conversation.user_id !== userId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    res.json(conversation);
  } catch (error) {
    console.error('Error fetching conversation:', error);
    res.status(500).json({ error: String(error) });
  }
});

// Update conversation title
router.patch('/:chatId/title', async (req, res) => {
  try {
    const userId = (req as AuthRequest).userId;
    if (!userId) return res.status(401).json({ error: 'Unauthorized' });

    const { title } = req.body;
    if (!title) {
      return res.status(400).json({ error: 'Title is required' });
    }

    // Verify ownership before updating
    const conversation = await getConversation(req.params.chatId);
    if (conversation.user_id !== userId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    await updateConversationTitle(req.params.chatId, title);
    res.json({ success: true });
  } catch (error) {
    console.error('Error updating title:', error);
    res.status(500).json({ error: String(error) });
  }
});

// Delete conversation
router.delete('/:chatId', async (req, res) => {
  try {
    const userId = (req as AuthRequest).userId;
    if (!userId) return res.status(401).json({ error: 'Unauthorized' });

    // Verify ownership before deleting
    const conversation = await getConversation(req.params.chatId);
    if (conversation.user_id !== userId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    await deleteConversation(req.params.chatId);
    res.json({ success: true });
  } catch (error) {
    console.error('Error deleting conversation:', error);
    res.status(500).json({ error: String(error) });
  }
});

// Add message to conversation
router.post('/:chatId/messages', async (req, res) => {
  try {
    const userId = (req as AuthRequest).userId;
    if (!userId) return res.status(401).json({ error: 'Unauthorized' });

    const { message } = req.body;
    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    // Verify ownership
    const conversation = await getConversation(req.params.chatId);
    if (conversation.user_id !== userId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    await addMessage(req.params.chatId, message);
    res.json({ success: true });
  } catch (error) {
    console.error('Error adding message:', error);
    res.status(500).json({ error: String(error) });
  }
});

export default router;
