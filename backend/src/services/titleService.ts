import axios from 'axios';

const OLLAMA_URL = 'http://127.0.0.1:11434/api/generate';
const MODEL = 'gemma2:27b';

export async function generateTitle(message: string): Promise<string> {
  try {
    const response = await axios.post(OLLAMA_URL, {
      model: MODEL,
      prompt: `Generate a short 3-5 word title for this conversation based on the user's first message. Only return the title, nothing else.\n\nUser message: ${message}\n\nTitle:`,
      stream: false
    });

    const title = response.data.response.trim().replace(/^["']|["']$/g, '');
    return title.slice(0, 40);
  } catch (error) {
    return message.slice(0, 30);
  }
}
