import { getDrugInfo, checkDrugInteraction } from './drugService';
import axios from 'axios';

const OLLAMA_URL = 'http://127.0.0.1:11434/api/generate';
const MODEL = 'llama2';

interface Tool {
  name: string;
  description: string;
  parameters: Record<string, string>;
}

const TOOLS: Tool[] = [
  {
    name: 'get_drug_info',
    description: 'Get detailed information about a drug including indication, mechanism, toxicity, metabolism, etc.',
    parameters: {
      drug_name: 'Name of the drug (e.g., Warfarin, Aspirin, Ibuprofen)'
    }
  },
  {
    name: 'check_drug_interaction',
    description: 'Check if two drugs interact with each other',
    parameters: {
      drug1: 'First drug name',
      drug2: 'Second drug name'
    }
  }
];

async function callLLM(prompt: string, systemPrompt: string): Promise<string> {
  const response = await axios.post(OLLAMA_URL, {
    model: MODEL,
    prompt,
    system: systemPrompt,
    stream: false
  });

  return response.data.response;
}

export async function processQuery(userQuery: string) {
  const systemPrompt = `You are a drug information assistant. You have access to these tools:

${JSON.stringify(TOOLS, null, 2)}

When you need to use a tool, respond with JSON in this format:
{"tool": "tool_name", "parameters": {"param": "value"}}

IMPORTANT: When the database returns "is_synonym: true", the queried drug name is mapped to another drug in the database. You MUST use the returned data and explain that according to the database, the queried name refers to the actual drug. Do not reject the database mapping.`;

  // First LLM call - decide what to do
  const response = await callLLM(userQuery, systemPrompt);

  // Check if agent wants to use a tool
  try {
    if (response.includes('{') && response.includes('}')) {
      const start = response.indexOf('{');
      const end = response.lastIndexOf('}') + 1;
      const toolCall = JSON.parse(response.substring(start, end));

      const toolName = toolCall.tool;
      const params = toolCall.parameters || {};

      let result: any;

      // Execute tool
      if (toolName === 'get_drug_info') {
        result = await getDrugInfo(params.drug_name);
      } else if (toolName === 'check_drug_interaction') {
        result = await checkDrugInteraction(params.drug1, params.drug2);
      } else {
        result = { error: 'Unknown tool' };
      }

      // Second LLM call - generate final answer
      const finalPrompt = `User asked: ${userQuery}

Tool result:
${JSON.stringify(result, null, 2)}

IMPORTANT: If "is_synonym: true":
- Clearly state: "In our database, [queried_name] is listed as [actual_name]."
- Provide the information about the actual drug
- Add a note: "Note: If this doesn't match what you're looking for, please verify the drug name or consult a healthcare professional."

Be clear and transparent about what the database contains.

Provide a helpful answer.`;

      const finalResponse = await callLLM(finalPrompt, 'You are a helpful drug information assistant.');

      return {
        answer: finalResponse,
        tool_used: toolName,
        tool_result: result
      };
    }

    return {
      answer: response,
      tool_used: null,
      tool_result: null
    };
  } catch (error) {
    return {
      answer: response,
      tool_used: null,
      tool_result: null,
      error: String(error)
    };
  }
}
