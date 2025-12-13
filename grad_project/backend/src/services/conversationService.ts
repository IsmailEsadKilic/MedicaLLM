import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand, QueryCommand, UpdateCommand, DeleteCommand } from '@aws-sdk/lib-dynamodb';
import { randomUUID } from 'crypto';

const client = new DynamoDBClient({
  endpoint: 'http://localhost:8000',
  region: 'us-east-1',
  credentials: {
    accessKeyId: 'dummy',
    secretAccessKey: 'dummy'
  }
});

const docClient = DynamoDBDocumentClient.from(client);

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  tool_used?: string;
  tool_result?: any;
}

interface Conversation {
  PK: string;
  SK: string;
  chat_id: string;
  user_id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export async function createConversation(userId: string, title: string = 'New Chat'): Promise<string> {
  const chatId = randomUUID();
  const timestamp = new Date().toISOString();
  
  await docClient.send(new PutCommand({
    TableName: 'Conversations',
    Item: {
      PK: `USER#${userId}`,
      SK: `CHAT#${timestamp}#${chatId}`,
      chat_id: chatId,
      user_id: userId,
      title,
      messages: [],
      created_at: timestamp,
      updated_at: timestamp
    }
  }));
  
  return chatId;
}

export async function getUserConversations(userId: string): Promise<Conversation[]> {
  const response = await docClient.send(new QueryCommand({
    TableName: 'Conversations',
    KeyConditionExpression: 'PK = :pk AND begins_with(SK, :sk)',
    ExpressionAttributeValues: {
      ':pk': `USER#${userId}`,
      ':sk': 'CHAT#'
    },
    ScanIndexForward: false // Sort by newest first
  }));
  
  return (response.Items || []) as Conversation[];
}

export async function getConversation(userId: string, chatId: string): Promise<Conversation | null> {
  const conversations = await getUserConversations(userId);
  return conversations.find(c => c.chat_id === chatId) || null;
}

export async function addMessage(userId: string, chatId: string, message: Message): Promise<void> {
  const conversation = await getConversation(userId, chatId);
  if (!conversation) throw new Error('Conversation not found');
  
  const messages = [...conversation.messages, message];
  const timestamp = new Date().toISOString();
  
  await docClient.send(new UpdateCommand({
    TableName: 'Conversations',
    Key: {
      PK: `USER#${userId}`,
      SK: conversation.SK
    },
    UpdateExpression: 'SET messages = :messages, updated_at = :updated',
    ExpressionAttributeValues: {
      ':messages': messages,
      ':updated': timestamp
    }
  }));
}

export async function updateTitle(userId: string, chatId: string, title: string): Promise<void> {
  const conversation = await getConversation(userId, chatId);
  if (!conversation) throw new Error('Conversation not found');
  
  await docClient.send(new UpdateCommand({
    TableName: 'Conversations',
    Key: {
      PK: `USER#${userId}`,
      SK: conversation.SK
    },
    UpdateExpression: 'SET title = :title, updated_at = :updated',
    ExpressionAttributeValues: {
      ':title': title,
      ':updated': new Date().toISOString()
    }
  }));
}

export async function deleteConversation(userId: string, chatId: string): Promise<void> {
  const conversation = await getConversation(userId, chatId);
  if (!conversation) throw new Error('Conversation not found');
  
  await docClient.send(new DeleteCommand({
    TableName: 'Conversations',
    Key: {
      PK: `USER#${userId}`,
      SK: conversation.SK
    }
  }));
}
