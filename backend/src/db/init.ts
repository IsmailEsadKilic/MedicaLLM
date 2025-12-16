import { CreateTableCommand } from '@aws-sdk/client-dynamodb';
import { client } from './dynamodb';

const tables = [
  {
    TableName: 'Users',
    KeySchema: [{ AttributeName: 'email', KeyType: 'HASH' as const }],
    AttributeDefinitions: [{ AttributeName: 'email', AttributeType: 'S' as const }],
    BillingMode: 'PAY_PER_REQUEST' as const
  },
  {
    TableName: process.env.TABLE_NAME || 'Conversations',
    KeySchema: [{ AttributeName: 'id', KeyType: 'HASH' as const }],
    AttributeDefinitions: [{ AttributeName: 'id', AttributeType: 'S' as const }],
    BillingMode: 'PAY_PER_REQUEST' as const
  },
  {
    TableName: 'Patients',
    KeySchema: [
      { AttributeName: 'healthcare_professional_id', KeyType: 'HASH' as const },
      { AttributeName: 'id', KeyType: 'RANGE' as const }
    ],
    AttributeDefinitions: [
      { AttributeName: 'healthcare_professional_id', AttributeType: 'S' as const },
      { AttributeName: 'id', AttributeType: 'S' as const }
    ],
    BillingMode: 'PAY_PER_REQUEST' as const
  }
];

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const initTables = async (retries = 5) => {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      for (const params of tables) {
        try {
          await client.send(new CreateTableCommand(params));
          console.log(`Table ${params.TableName} created`);
        } catch (error: any) {
          if (error.name === 'ResourceInUseException') {
            console.log(`Table ${params.TableName} exists`);
          } else {
            throw error;
          }
        }
      }
      return; // Success, exit the retry loop
    } catch (error: any) {
      if (attempt < retries && (error.code === 'ECONNREFUSED' || error.$metadata?.httpStatusCode === 503)) {
        console.log(`DynamoDB not ready, retrying in 2s... (attempt ${attempt}/${retries})`);
        await sleep(2000);
      } else {
        console.error(`Error initializing tables:`, error.message);
        if (attempt === retries) {
          console.error(`Failed to connect to DynamoDB after ${retries} attempts`);
        }
        throw error;
      }
    }
  }
};
