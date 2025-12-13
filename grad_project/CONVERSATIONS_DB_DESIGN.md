# Conversations Database Design

## Table: Conversations

### Structure
```
PK: USER#<user_id>
SK: CHAT#<timestamp>#<chat_id>
```

### Attributes
```json
{
  "PK": "USER#user123",
  "SK": "CHAT#2025-01-09T10:30:00Z#chat-uuid",
  "chat_id": "chat-uuid",
  "user_id": "user123",
  "title": "Warfarin Information",
  "messages": [
    {
      "role": "user",
      "content": "What is Warfarin?",
      "timestamp": "2025-01-09T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Warfarin is...",
      "timestamp": "2025-01-09T10:30:05Z",
      "tool_used": "get_drug_info",
      "tool_result": {...}
    }
  ],
  "created_at": "2025-01-09T10:30:00Z",
  "updated_at": "2025-01-09T10:35:00Z"
}
```

### Access Patterns

1. **Get all chats for a user** (sorted by most recent)
   - Query: `PK = USER#user123`, `SK begins_with CHAT#`
   - Returns: All chats sorted by timestamp (newest first)

2. **Get specific chat**
   - Query: `PK = USER#user123`, `SK = CHAT#timestamp#chat-uuid`

3. **Update chat** (add message, update title)
   - Update: Same keys

4. **Delete chat**
   - Delete: Same keys

### GSI (Optional): ChatIdIndex
```
GSI_PK: CHAT#<chat_id>
GSI_SK: USER#<user_id>
```
For quick lookup by chat_id without knowing user_id.

## Benefits

✅ **Fast queries**: Get all user chats in one query
✅ **Sorted**: Chats automatically sorted by timestamp
✅ **Scalable**: Each user's chats are partitioned
✅ **Simple**: Single table, no joins needed
✅ **Efficient**: Messages stored as array (no separate table needed)

## Alternative: Separate Messages Table

If messages get very large (100+ per chat), consider:

### Table: Messages
```
PK: CHAT#<chat_id>
SK: MSG#<timestamp>
```

But for typical use (5-20 messages per chat), storing in array is simpler and faster.

## Recommendation

Use **single table with messages array** because:
- Most chats have < 50 messages
- Simpler queries (1 query vs many)
- Faster load times
- DynamoDB item limit is 400KB (enough for ~100 messages)
