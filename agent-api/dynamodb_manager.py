import os
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from datetime import datetime
import printmeup as pm
from models import Conversation, Message

# * DynamoDB Configuration
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")

class DynamoDBManager:
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=DYNAMODB_ENDPOINT,
            region_name='us-east-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        self.conversations_table = self.dynamodb.Table('Conversations') # type: ignore
        self.drugs_table = self.dynamodb.Table('Drugs') # type: ignore
        self.interactions_table = self.dynamodb.Table('DrugInteractions') # type: ignore
        self.food_interactions_table = self.dynamodb.Table('DrugFoodInteractions') # type: ignore
        pm.suc(f"DynamoDB Manager initialized with endpoint: {DYNAMODB_ENDPOINT}")
 
    # ========================================================================
    # CONVERSATION METHODS
    # ========================================================================
    
    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Get a conversation by chat_id using GSI"""
        try:
            response = self.conversations_table.query(
                IndexName='ChatIdIndex',
                KeyConditionExpression=Key('GSI_PK').eq(f'CHAT#{conversation_id}')
            )
            
            if response['Items']:
                return Conversation.from_dynamo_item(response['Items'][0])
            return None
        except ClientError as e:
            pm.err(e=e, m=f"Error getting conversation {conversation_id}")
            return None

    def get_conversations(self, user_id: str) -> list[Conversation] | None:
        """Get all conversations for a user, sorted by newest first"""
        try:
            response = self.conversations_table.query(
                KeyConditionExpression=Key('PK').eq(f'USER#{user_id}') & Key('SK').begins_with('CHAT#'),
                ScanIndexForward=False  # Newest first
            )
            
            conversations = [Conversation.from_dynamo_item(item) for item in response['Items']]
            pm.inf(f"Found {len(conversations)} conversations for user {user_id}")
            return conversations
        except ClientError as e:
            pm.err(e=e, m=f"Error getting conversations for user {user_id}")
            return None
        
    def create_conversation(self, user_id: str, title: str) -> Conversation:
        """Create a new conversation for a user"""
        try:
            conversation = Conversation.create_new(user_id=user_id, title=title)
            item = conversation.to_dynamo_item()
            
            self.conversations_table.put_item(Item=item)
            pm.suc(f"Created conversation {conversation.id} for user {user_id}")
            return conversation
        except ClientError as e:
            pm.err(e=e, m=f"Error creating conversation for user {user_id}")
            raise

    def save_conversation(self, conversation: Conversation) -> bool:
        """Save/update an existing conversation"""
        try:
            item = conversation.to_dynamo_item()
            item['updated_at'] = datetime.now().isoformat()
            
            self.conversations_table.put_item(Item=item)
            pm.inf(f"Saved conversation {conversation.id}")
            return True
        except ClientError as e:
            pm.err(e=e, m=f"Error saving conversation {conversation.id}")
            return False

    def add_message(self, conversation_id: str, message: Message) -> bool:
        """Add a message to a conversation"""
        try:
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                pm.war(f"Conversation {conversation_id} not found")
                return False
            
            conversation.messages.append(message)
            conversation.updated_at = datetime.now().isoformat()
            
            return self.save_conversation(conversation)
        except Exception as e:
            pm.err(e=e, m=f"Error adding message to conversation {conversation_id}")
            return False

    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update the title of a conversation"""
        try:
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                pm.war(f"Conversation {conversation_id} not found")
                return False
            
            conversation.title = title
            conversation.updated_at = datetime.now().isoformat()
            
            return self.save_conversation(conversation)
        except Exception as e:
            pm.err(e=e, m=f"Error updating title for conversation {conversation_id}")
            return False
 
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        try:
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                pm.war(f"Conversation {conversation_id} not found")
                return False
            
            self.conversations_table.delete_item(
                Key={
                    'PK': f'USER#{conversation.user_id}',
                    'SK': f'CHAT#{conversation.created_at}#{conversation.id}'
                }
            )
            pm.suc(f"Deleted conversation {conversation_id}")
            return True
        except ClientError as e:
            pm.err(e=e, m=f"Error deleting conversation {conversation_id}")
            return False
    
    # ========================================================================
    # DRUG INFORMATION METHODS (for AI Agent Tool Calling)
    # ========================================================================
    
    def get_drug_info(self, drug_name: str) -> dict:
        """
        Get detailed drug information from Drugs table.
        Supports synonym resolution.
        
        Args:
            drug_name: Name of the drug to look up
            
        Returns:
            dict with drug information or error
        """
        try:
            drug_name = drug_name.strip()
            
            # Try different case variations
            for name_variant in [drug_name, drug_name.title(), drug_name.upper(), drug_name.lower()]:
                # First try direct lookup with META
                response = self.drugs_table.get_item(
                    Key={'PK': f'DRUG#{name_variant}', 'SK': 'META'}
                )
                
                if 'Item' in response:
                    drug = response['Item']
                    pm.inf(f"Found drug: {drug.get('name')}")
                    return {
                        'success': True,
                        'drug_name': drug.get('name'),
                        'drug_id': drug.get('drug_id'),
                        'description': drug.get('description', 'N/A'),
                        'indication': drug.get('indication', 'N/A'),
                        'mechanism_of_action': drug.get('mechanism_of_action', 'N/A'),
                        'pharmacodynamics': drug.get('pharmacodynamics', 'N/A'),
                        'toxicity': drug.get('toxicity', 'N/A'),
                        'metabolism': drug.get('metabolism', 'N/A'),
                        'absorption': drug.get('absorption', 'N/A'),
                        'half_life': drug.get('half_life', 'N/A'),
                        'protein_binding': drug.get('protein_binding', 'N/A'),
                        'route_of_elimination': drug.get('route_of_elimination', 'N/A'),
                        'groups': drug.get('groups', []),
                        'categories': drug.get('categories', []),
                        'cas_number': drug.get('cas_number', 'N/A'),
                        'unii': drug.get('unii', 'N/A'),
                        'state': drug.get('state', 'N/A')
                    }
                
                # Try synonym lookup
                synonym_response = self.drugs_table.get_item(
                    Key={'PK': f'DRUG#{name_variant}', 'SK': 'SYNONYM'}
                )
                
                if 'Item' in synonym_response and 'points_to' in synonym_response['Item']:
                    actual_name = synonym_response['Item']['points_to']
                    pm.inf(f"'{name_variant}' is a synonym for '{actual_name}'")
                    
                    # Get the actual drug
                    response = self.drugs_table.get_item(
                        Key={'PK': f'DRUG#{actual_name}', 'SK': 'META'}
                    )
                    
                    if 'Item' in response:
                        drug = response['Item']
                        return {
                            'success': True,
                            'is_synonym': True,
                            'queried_name': drug_name,
                            'actual_name': actual_name,
                            'drug_name': drug.get('name'),
                            'drug_id': drug.get('drug_id'),
                            'description': drug.get('description', 'N/A'),
                            'indication': drug.get('indication', 'N/A'),
                            'mechanism_of_action': drug.get('mechanism_of_action', 'N/A'),
                            'pharmacodynamics': drug.get('pharmacodynamics', 'N/A'),
                            'toxicity': drug.get('toxicity', 'N/A'),
                            'metabolism': drug.get('metabolism', 'N/A'),
                            'absorption': drug.get('absorption', 'N/A'),
                            'half_life': drug.get('half_life', 'N/A'),
                            'protein_binding': drug.get('protein_binding', 'N/A'),
                            'route_of_elimination': drug.get('route_of_elimination', 'N/A'),
                            'groups': drug.get('groups', []),
                            'categories': drug.get('categories', []),
                            'cas_number': drug.get('cas_number', 'N/A'),
                            'unii': drug.get('unii', 'N/A'),
                            'state': drug.get('state', 'N/A')
                        }
            
            pm.war(f"Drug '{drug_name}' not found")
            return {
                'success': False,
                'error': f"Drug '{drug_name}' not found in database"
            }
            
        except Exception as e:
            pm.err(e=e, m=f"Error getting drug info for '{drug_name}'")
            return {
                'success': False,
                'error': str(e)
            }
    
    def resolve_drug_name(self, drug_name: str) -> str:
        """
        Resolve a drug name (synonym or actual name) to its canonical name.
        
        Args:
            drug_name: Name to resolve
            
        Returns:
            Canonical drug name (title case)
        """
        try:
            pm.inf(f"🔎 Resolving drug name: '{drug_name}'")
            # Try title case first as that's how drugs are stored in DB
            for name_variant in [drug_name.title(), drug_name, drug_name.upper()]:
                pm.inf(f"  Trying variant: '{name_variant}'")
                
                # Check if it's a synonym
                syn_resp = self.drugs_table.get_item(
                    Key={'PK': f'DRUG#{name_variant}', 'SK': 'SYNONYM'}
                )
                
                if 'Item' in syn_resp and 'points_to' in syn_resp['Item']:
                    resolved = syn_resp['Item']['points_to']
                    pm.suc(f"  ✅ Found synonym: '{name_variant}' -> '{resolved}'")
                    return resolved
                
                # Check if it's a direct drug
                meta_resp = self.drugs_table.get_item(
                    Key={'PK': f'DRUG#{name_variant}', 'SK': 'META'}
                )
                
                if 'Item' in meta_resp:
                    resolved = meta_resp['Item'].get('name', name_variant)
                    pm.suc(f"  ✅ Found drug META: '{name_variant}' -> '{resolved}'")
                    return resolved
            
            # If not found, return title case as default
            pm.war(f"  ⚠️  Drug not found in DB, using title case: '{drug_name.title()}'")
            return drug_name.title()
            
        except Exception as e:
            pm.err(e=e, m=f"Error resolving drug name '{drug_name}'")
            return drug_name.title()
    
    def check_drug_interaction(self, drug1: str, drug2: str) -> dict:
        """
        Check if two drugs interact with each other.
        Automatically resolves synonyms and tries both directions.
        
        Args:
            drug1: First drug name
            drug2: Second drug name
            
        Returns:
            dict with interaction information or no interaction message
        """
        try:
            drug1 = drug1.strip()
            drug2 = drug2.strip()
            
            pm.inf(f"🔍 [DB] check_drug_interaction: '{drug1}' + '{drug2}' (original input)")
            
            # Resolve synonyms first (returns title case)
            resolved1 = self.resolve_drug_name(drug1)
            resolved2 = self.resolve_drug_name(drug2)
            
            pm.inf(f"🔍 [DB] After resolution: '{resolved1}' + '{resolved2}'")
            
            # Try both orders (since interactions are directional in the DB)
            # resolve_drug_name already returns title case, which matches DB format
            for d1, d2 in [(resolved1, resolved2), (resolved2, resolved1)]:
                pk = f'DRUG#{d1}'
                sk = f'INTERACTS#{d2}'
                pm.inf(f"  [DB] Querying DrugInteractions table: PK={pk}, SK={sk}")
                
                response = self.interactions_table.get_item(
                    Key={'PK': pk, 'SK': sk}
                )
                
                pm.inf(f"  [DB] Response keys: {list(response.keys())}")
                
                if 'Item' in response:
                    interaction = response['Item']
                    pm.suc(f"✅ [DB] Interaction found: {d1} + {d2}")
                    pm.inf(f"  [DB] Interaction keys: {list(interaction.keys())}")
                    pm.inf(f"  [DB] Description length: {len(interaction.get('description', ''))} chars")
                    pm.inf(f"  [DB] Description preview: {interaction.get('description', 'N/A')[:100]}...")
                    
                    result = {
                        'success': True,
                        'interaction_found': True,
                        'drug1': interaction.get('drug1_name'),
                        'drug2': interaction.get('drug2_name'),
                        'drug1_id': interaction.get('drug1_id'),
                        'drug2_id': interaction.get('drug2_id'),
                        'description': interaction.get('description', 'No description available')
                    }
                    pm.inf(f"  [DB] Returning: {result}")
                    return result
                else:
                    pm.inf(f"  ❌ [DB] Not found with PK={pk}, SK={sk}")
            
            pm.war(f"⚠️  [DB] No interaction found between {resolved1} and {resolved2}")
            result = {
                'success': True,
                'interaction_found': False,
                'drug1': resolved1,
                'drug2': resolved2,
                'message': f"No known interaction found between {resolved1} and {resolved2}"
            }
            pm.inf(f"  [DB] Returning: {result}")
            return result
            
        except Exception as e:
            pm.err(e=e, m=f"Error checking interaction between '{drug1}' and '{drug2}'")
            return {
                'success': False,
                'error': str(e)
            }
            
    def get_drug_food_interactions(self, drug_name: str) -> dict:
        """
        Get food interactions for a specific drug.
        
        Args:
            drug_name: Name of the drug
            
        Returns:
            dict with food interaction information
        """
        try:
            drug_name = drug_name.strip()
            resolved_name = self.resolve_drug_name(drug_name)
            
            pm.inf(f"Getting food interactions for: {resolved_name}")
            
            # Try different case variations
            for name_variant in [resolved_name, resolved_name.title()]:
                response = self.food_interactions_table.query(
                    KeyConditionExpression=Key('PK').eq(f'DRUG#{name_variant}')
                )
                
                if response['Items']:
                    interactions = [item['interaction'] for item in response['Items']]
                    pm.suc(f"Found {len(interactions)} food interactions for {name_variant}")
                    return {
                        'success': True,
                        'drug_name': name_variant,
                        'interactions': interactions,
                        'count': len(interactions)
                    }
            
            pm.inf(f"No food interactions found for {resolved_name}")
            return {
                'success': True,
                'drug_name': resolved_name,
                'interactions': [],
                'count': 0,
                'message': f"No food interactions documented for {resolved_name}"
            }
            
        except Exception as e:
            pm.err(e=e, m=f"Error getting food interactions for '{drug_name}'")
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_drugs_by_category(self, search_term: str, limit: int = 10) -> dict:
        """
        Search drugs by therapeutic category or indication.
        
        Args:
            search_term: Category or indication keyword to search for
            limit: Maximum number of drugs to return
            
        Returns:
            dict with matching drugs
        """
        try:
            search_term = search_term.lower()
            pm.inf(f"Searching drugs by category/indication: {search_term}")
            
            response = self.drugs_table.scan(
                FilterExpression='attribute_exists(categories) OR attribute_exists(indication)'
            )
            
            matches = []
            for item in response['Items']:
                if item.get('SK') != 'META':
                    continue
                
                categories = [c.lower() for c in item.get('categories', [])]
                indication = item.get('indication', '').lower()
                
                if any(search_term in cat for cat in categories) or search_term in indication:
                    matches.append({
                        'name': item.get('name'),
                        'indication': item.get('indication', 'N/A')[:200],
                        'categories': item.get('categories', [])[:3]
                    })
                    
                    if len(matches) >= limit:
                        break
            
            pm.suc(f"Found {len(matches)} drugs matching '{search_term}'")
            return {
                'success': True,
                'drugs': matches,
                'count': len(matches)
            }
            
        except Exception as e:
            pm.err(e=e, m=f"Error searching drugs by category '{search_term}'")
            return {
                'success': False,
                'error': str(e)
            }