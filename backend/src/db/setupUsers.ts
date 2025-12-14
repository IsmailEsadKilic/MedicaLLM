import { CreateTableCommand } from '@aws-sdk/client-dynamodb';
import { client } from './dynamodb';
import dotenv from 'dotenv';

dotenv.config();

const createUsersTable = async () => {
  const params = {
    TableName: process.env.USERS_TABLE!,
    KeySchema: [
      { AttributeName: 'email', KeyType: 'HASH' as const }
    ],
    AttributeDefinitions: [
      { AttributeName: 'email', AttributeType: 'S' as const }
    ],
    BillingMode: 'PAY_PER_REQUEST' as const
  };

  try {
    await client.send(new CreateTableCommand(params));
    console.log(`Table ${process.env.USERS_TABLE} created successfully`);
  } catch (error: any) {
    if (error.name === 'ResourceInUseException') {
      console.log(`Table ${process.env.USERS_TABLE} already exists`);
    } else {
      console.error('Error creating table:', error);
    }
  }
};

createUsersTable();
