import axios from 'axios';

const AGENT_API_URL = process.env.AGENT_API_URL || 'http://localhost:2580';

interface QueryRequest {
  conversation_id: string;
  query: string;
}

interface QueryResponse {
  success: boolean;
  answer: string;
  conversation_id: string;
  sources?: any[];
  tool_used?: string;
}

interface CreateConversationRequest {
  user_id: string;
  title?: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface Conversation {
  id: string;
  user_id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export async function createConversation(userId: string, title: string = 'New Chat'): Promise<string> {
  try {
    const response = await axios.post(`${AGENT_API_URL}/api/create-conversation`, {
      user_id: userId,
      title
    });
    return response.data.conversation_id;
  } catch (error) {
    console.error('Failed to create conversation:', error);
    throw new Error(`Failed to create conversation: ${error}`);
  }
}

export async function getUserConversations(userId: string): Promise<Conversation[]> {
  try {
    const response = await axios.get(`${AGENT_API_URL}/api/conversations`, {
      params: { user_id: userId }
    });
    return response.data.conversations;
  } catch (error) {
    console.error('Failed to get conversations:', error);
    throw new Error(`Failed to get conversations: ${error}`);
  }
}

export async function getConversation(conversationId: string): Promise<Conversation> {
  try {
    const response = await axios.get(`${AGENT_API_URL}/api/conversation/${conversationId}`);
    return response.data.conversation;
  } catch (error) {
    console.error('Failed to get conversation:', error);
    throw new Error(`Failed to get conversation: ${error}`);
  }
}

export async function updateConversationTitle(conversationId: string, title: string): Promise<void> {
  try {
    await axios.patch(`${AGENT_API_URL}/api/conversation/title`, {
      conversation_id: conversationId,
      title
    });
  } catch (error) {
    console.error('Failed to update title:', error);
    throw new Error(`Failed to update title: ${error}`);
  }
}

export async function deleteConversation(conversationId: string): Promise<void> {
  try {
    await axios.delete(`${AGENT_API_URL}/api/conversation/${conversationId}`);
  } catch (error) {
    console.error('Failed to delete conversation:', error);
    throw new Error(`Failed to delete conversation: ${error}`);
  }
}

export async function queryAgent(conversationId: string, query: string): Promise<QueryResponse> {
  try {
    const response = await axios.post(`${AGENT_API_URL}/api/query`, {
      conversation_id: conversationId,
      query
    });
    return response.data;
  } catch (error) {
    console.error('Failed to query agent:', error);
    throw new Error(`Failed to query agent: ${error}`);
  }
}

export async function generateTitle(message: string): Promise<string> {
  try {
    // Simple title generation from first few words
    const words = message.split(' ').slice(0, 5).join(' ');
    return words.length > 30 ? words.slice(0, 27) + '...' : words;
  } catch (error) {
    return message.slice(0, 30);
  }
}

export async function addMessage(conversationId: string, message: Message): Promise<void> {
  try {
    await axios.post(`${AGENT_API_URL}/api/conversation/add-message`, {
      conversation_id: conversationId,
      message
    });
  } catch (error) {
    console.error('Failed to add message:', error);
    throw new Error(`Failed to add message: ${error}`);
  }
}
