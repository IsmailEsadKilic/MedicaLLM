# Database Documentation

## Overview
AWS DynamoDB is used for data persistence. Development uses DynamoDB Local via Docker.

## Database Technology
- **Service**: AWS DynamoDB
- **SDK**: @aws-sdk/client-dynamodb v3.490.0
- **Document Client**: @aws-sdk/lib-dynamodb v3.490.0
- **Development**: DynamoDB Local (Docker)

## Connection Configuration

### Development (DynamoDB Local)
```typescript
// src/db/dynamodb.ts
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient } from '@aws-sdk/lib-dynamodb';

const client = new DynamoDBClient({
  region: process.env.AWS_REGION,
  endpoint: process.env.DYNAMODB_ENDPOINT // http://localhost:8000
});

const docClient = DynamoDBDocumentClient.from(client);
```

### Environment Variables
```env
DYNAMODB_ENDPOINT=http://localhost:8000
AWS_REGION=us-east-1
TABLE_NAME=Items
USERS_TABLE=Users
```

## Tables

### 1. Users Table

#### Schema
```typescript
{
  email: string;          // Partition Key (HASH)
  userId: string;         // Unique user identifier
  password: string;       // Bcrypt hashed password
  name: string;           // User's display name
  createdAt: string;      // ISO 8601 timestamp
}
```

#### Configuration
- **Table Name**: Users
- **Partition Key**: email (String)
- **Billing Mode**: PAY_PER_REQUEST
- **No Sort Key**

#### Setup Script
```bash
npm run db:setup-users
```

#### Creation Code
```typescript
// src/db/setupUsers.ts
const params = {
  TableName: 'Users',
  KeySchema: [
    { AttributeName: 'email', KeyType: 'HASH' }
  ],
  AttributeDefinitions: [
    { AttributeName: 'email', AttributeType: 'S' }
  ],
  BillingMode: 'PAY_PER_REQUEST'
};
```

#### Operations

**Create User**
```typescript
await docClient.send(new PutCommand({
  TableName: USERS_TABLE,
  Item: {
    email: 'user@example.com',
    userId: 'user_1234567890',
    password: 'hashed_password',
    name: 'John Doe',
    createdAt: new Date().toISOString()
  }
}));
```

**Get User by Email**
```typescript
const result = await docClient.send(new GetCommand({
  TableName: USERS_TABLE,
  Key: { email: 'user@example.com' }
}));
```

### 2. Items Table

#### Schema
```typescript
{
  id: string;            // Partition Key (HASH)
  name: string;          // Item name
  description?: string;  // Optional description
  createdAt: string;     // ISO 8601 timestamp
  // Additional fields as needed
}
```

#### Configuration
- **Table Name**: Items
- **Partition Key**: id (String)
- **Billing Mode**: PAY_PER_REQUEST

#### Setup Script
```bash
npm run db:setup
```

#### Operations

**Create Item**
```typescript
await docClient.send(new PutCommand({
  TableName: TABLE_NAME,
  Item: {
    id: 'item_123',
    name: 'Sample Item',
    description: 'Description here',
    createdAt: new Date().toISOString()
  }
}));
```

**Get All Items**
```typescript
const result = await docClient.send(new ScanCommand({
  TableName: TABLE_NAME
}));
```

**Get Item by ID**
```typescript
const result = await docClient.send(new GetCommand({
  TableName: TABLE_NAME,
  Key: { id: 'item_123' }
}));
```

**Update Item**
```typescript
await docClient.send(new UpdateCommand({
  TableName: TABLE_NAME,
  Key: { id: 'item_123' },
  UpdateExpression: 'SET #name = :name',
  ExpressionAttributeNames: { '#name': 'name' },
  ExpressionAttributeValues: { ':name': 'Updated Name' }
}));
```

**Delete Item**
```typescript
await docClient.send(new DeleteCommand({
  TableName: TABLE_NAME,
  Key: { id: 'item_123' }
}));
```

## DynamoDB Local Setup

### Docker Compose
```yaml
version: '3.8'
services:
  dynamodb-local:
    image: amazon/dynamodb-local:latest
    container_name: dynamodb-local
    ports:
      - "8000:8000"
    command: "-jar DynamoDBLocal.jar -sharedDb -dbPath ./data"
    volumes:
      - ./dynamodb-data:/home/dynamodblocal/data
```

### Start DynamoDB Local
```bash
docker-compose up -d
```

### Stop DynamoDB Local
```bash
docker-compose down
```

### Verify Running
```bash
docker ps | grep dynamodb
```

### Access DynamoDB Local
- **Endpoint**: http://localhost:8000
- **AWS CLI**: Use `--endpoint-url http://localhost:8000`

## AWS SDK v3 Commands

### Import Statements
```typescript
import { 
  PutCommand, 
  GetCommand, 
  ScanCommand, 
  UpdateCommand, 
  DeleteCommand 
} from '@aws-sdk/lib-dynamodb';
```

### Command Pattern
All operations use the command pattern:
```typescript
const result = await docClient.send(new CommandName(params));
```

## Data Access Patterns

### Users Table
- **Primary Access**: Get user by email (login/registration)
- **Pattern**: Key-value lookup using email as partition key
- **No Secondary Indexes**: Simple email-based access

### Items Table
- **Primary Access**: Get item by ID
- **Secondary Access**: Scan all items (for listing)
- **Pattern**: Key-value lookup + full table scan

## Future Enhancements

### Conversations Table (Planned)
```typescript
{
  conversationId: string;  // Partition Key
  userId: string;          // GSI Partition Key
  title: string;
  messages: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
  }>;
  createdAt: string;
  updatedAt: string;
}
```

### Messages Table (Alternative Design)
```typescript
{
  conversationId: string;  // Partition Key
  messageId: string;       // Sort Key
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}
```

## Best Practices

✅ **Use Document Client**: Simplifies data marshalling
✅ **PAY_PER_REQUEST**: Good for development and variable workloads
✅ **ISO Timestamps**: Consistent date format
✅ **Error Handling**: Catch and handle DynamoDB exceptions
✅ **Environment Variables**: Table names configurable

## Common Issues & Solutions

### Issue: Table Already Exists
```
Error: ResourceInUseException
```
**Solution**: Table already created, safe to ignore or delete and recreate

### Issue: Cannot Connect to DynamoDB
```
Error: connect ECONNREFUSED 127.0.0.1:8000
```
**Solution**: Start DynamoDB Local with `docker-compose up -d`

### Issue: Invalid Endpoint
```
Error: Invalid endpoint
```
**Solution**: Check DYNAMODB_ENDPOINT in .env file

## Migration to AWS (Production)

### Changes Needed
1. Remove `endpoint` from DynamoDBClient config
2. Configure AWS credentials (IAM role or access keys)
3. Update region if needed
4. Consider provisioned capacity vs PAY_PER_REQUEST
5. Add Global Secondary Indexes if needed
6. Enable Point-in-Time Recovery
7. Set up CloudWatch alarms
8. Configure auto-scaling (if using provisioned capacity)

### AWS CDK Deployment (Planned)
Tables will be created via CDK infrastructure code in the `cdk/` directory.
