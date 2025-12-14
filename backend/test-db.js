const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, PutCommand, GetCommand } = require('@aws-sdk/lib-dynamodb');

const client = new DynamoDBClient({
  region: 'us-east-1',
  endpoint: 'http://localhost:8000'
});

const docClient = DynamoDBDocumentClient.from(client);

async function testDB() {
  try {
    console.log('Testing DynamoDB connection...');
    
    const testUser = {
      email: 'test@test.com',
      userId: 'user_123',
      password: 'hashed',
      name: 'Test',
      createdAt: new Date().toISOString()
    };
    
    console.log('Putting item...');
    await docClient.send(new PutCommand({
      TableName: 'Users',
      Item: testUser
    }));
    
    console.log('Getting item...');
    const result = await docClient.send(new GetCommand({
      TableName: 'Users',
      Key: { email: 'test@test.com' }
    }));
    
    console.log('Success! Item:', result.Item);
  } catch (error) {
    console.error('Error:', error);
  }
}

testDB();
