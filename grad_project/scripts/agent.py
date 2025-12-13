import boto3
import json
import requests

# DynamoDB setup
dynamodb = boto3.resource('dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)

drugs_table = dynamodb.Table('Drugs')
interactions_table = dynamodb.Table('DrugInteractions')

# Ollama setup
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma2:27b"

# Tool definitions
TOOLS = [
    {
        "name": "get_drug_info",
        "description": "Get detailed information about a drug including indication, mechanism, toxicity, metabolism, etc.",
        "parameters": {
            "drug_name": "Name of the drug (e.g., Warfarin, Aspirin, Ibuprofen)"
        }
    },
    {
        "name": "check_drug_interaction",
        "description": "Check if two drugs interact with each other",
        "parameters": {
            "drug1": "First drug name",
            "drug2": "Second drug name"
        }
    }
]

def get_drug_info(drug_name):
    """Get drug information from Drugs table"""
    try:
        response = drugs_table.get_item(Key={'PK': f'DRUG#{drug_name}'})
        
        if 'Item' not in response:
            return {"error": f"Drug '{drug_name}' not found"}
        
        drug = response['Item']
        
        # If synonym, get actual drug
        if drug.get('type') == 'synonym':
            response = drugs_table.get_item(Key={'PK': f"DRUG#{drug['points_to']}"})
            drug = response['Item']
        
        return {
            "name": drug.get('name'),
            "drug_id": drug.get('drug_id'),
            "indication": drug.get('indication', 'N/A'),
            "mechanism_of_action": drug.get('mechanism_of_action', 'N/A'),
            "pharmacodynamics": drug.get('pharmacodynamics', 'N/A'),
            "toxicity": drug.get('toxicity', 'N/A'),
            "metabolism": drug.get('metabolism', 'N/A'),
            "absorption": drug.get('absorption', 'N/A'),
            "half_life": drug.get('half_life', 'N/A'),
            "protein_binding": drug.get('protein_binding', 'N/A'),
            "groups": drug.get('groups', []),
            "categories": drug.get('categories', [])
        }
    except Exception as e:
        return {"error": str(e)}

def check_drug_interaction(drug1, drug2):
    """Check drug-drug interaction"""
    try:
        # Try both directions
        response = interactions_table.get_item(
            Key={'PK': f'DRUG#{drug1}', 'SK': f'INTERACTS#{drug2}'}
        )
        
        if 'Item' in response:
            return {
                "interaction_found": True,
                "drug1": response['Item']['drug1_name'],
                "drug2": response['Item']['drug2_name'],
                "description": response['Item']['description']
            }
        
        # Try reverse
        response = interactions_table.get_item(
            Key={'PK': f'DRUG#{drug2}', 'SK': f'INTERACTS#{drug1}'}
        )
        
        if 'Item' in response:
            return {
                "interaction_found": True,
                "drug1": response['Item']['drug1_name'],
                "drug2": response['Item']['drug2_name'],
                "description": response['Item']['description']
            }
        
        return {
            "interaction_found": False,
            "message": f"No interaction found between {drug1} and {drug2}"
        }
    except Exception as e:
        return {"error": str(e)}

def call_llm(prompt, system_prompt):
    """Call Ollama LLM"""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    
    response = requests.post(OLLAMA_URL, json=payload)
    return response.json()['response']

def run_agent(user_query):
    """Main agent loop"""
    system_prompt = f"""You are a drug information assistant. You have access to these tools:

{json.dumps(TOOLS, indent=2)}

When you need to use a tool, respond with JSON in this format:
{{"tool": "tool_name", "parameters": {{"param": "value"}}}}

After receiving tool results, provide a helpful answer to the user.
"""
    
    print(f"\n🤖 User: {user_query}\n")
    
    # First LLM call - decide what to do
    response = call_llm(user_query, system_prompt)
    print(f"💭 Agent thinking: {response}\n")
    
    # Check if agent wants to use a tool
    try:
        if '{' in response and '}' in response:
            # Extract JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            tool_call = json.loads(response[start:end])
            
            tool_name = tool_call.get('tool')
            params = tool_call.get('parameters', {})
            
            print(f"🔧 Using tool: {tool_name}")
            print(f"📝 Parameters: {params}\n")
            
            # Execute tool
            if tool_name == 'get_drug_info':
                result = get_drug_info(params['drug_name'])
            elif tool_name == 'check_drug_interaction':
                result = check_drug_interaction(params['drug1'], params['drug2'])
            else:
                result = {"error": "Unknown tool"}
            
            print(f"📊 Tool result: {json.dumps(result, indent=2)}\n")
            
            # Second LLM call - generate final answer
            final_prompt = f"""User asked: {user_query}

Tool result:
{json.dumps(result, indent=2)}

Provide a helpful, concise answer based on this information."""
            
            final_response = call_llm(final_prompt, "You are a helpful drug information assistant.")
            print(f"✅ Agent: {final_response}\n")
            
    except json.JSONDecodeError:
        print(f"✅ Agent: {response}\n")

if __name__ == '__main__':
    # Test queries
    print("=" * 60)
    print("🏥 Drug Information Agent")
    print("=" * 60)
    
    run_agent("What is Warfarin used for?")
    run_agent("Do Warfarin and Ibuprofen interact?")
    run_agent("Tell me about Aspirin")
