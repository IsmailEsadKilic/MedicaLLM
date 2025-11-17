import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient } from "@aws-sdk/lib-dynamodb";

// Determine if we're in local development
const isLocal = process.env.NODE_ENV === "development" || process.env.USE_LOCAL_DYNAMODB === "true";

// DynamoDB configuration
const config = isLocal
  ? {
      // Local DynamoDB endpoint
      endpoint: process.env.DYNAMODB_LOCAL_ENDPOINT || "http://localhost:8000",
      region: "local",
      credentials: {
        accessKeyId: "local",
        secretAccessKey: "local",
      },
    }
  : {
      // Production AWS DynamoDB
      region: process.env.AWS_REGION || "us-east-1",
    };

// Create DynamoDB client
const client = new DynamoDBClient(config);

// Create DynamoDB Document Client (easier to work with)
export const dynamoDB = DynamoDBDocumentClient.from(client, {
  marshallOptions: {
    removeUndefinedValues: true,
  },
});

// Table names
export const USERS_TABLE = process.env.USERS_TABLE || "medicallm-users";
export const VERIFICATION_TABLE = process.env.VERIFICATION_TABLE || "medicallm-verifications";

// Helper function to ensure table exists (for local development)
export async function ensureTableExists() {
  if (!isLocal) {
    // In production, table should already exist
    return;
  }

  try {
    const { DynamoDBClient: DBClient, DescribeTableCommand, CreateTableCommand } = await import("@aws-sdk/client-dynamodb");
    
    const dbClient = new DBClient(config);
    
    // Check if table exists
    try {
      const describeResult = await dbClient.send(
        new DescribeTableCommand({
          TableName: USERS_TABLE,
        })
      );
      
      // Table exists, check if it's active
      if (describeResult.Table?.TableStatus === "ACTIVE") {
        console.log(`✅ DynamoDB table "${USERS_TABLE}" already exists and is active`);
        return;
      }
      
      // Table exists but not active, wait a bit
      console.log(`⏳ Table "${USERS_TABLE}" exists but status is ${describeResult.Table?.TableStatus}, waiting...`);
      await new Promise(resolve => setTimeout(resolve, 2000));
      return;
    } catch (error: any) {
      if (error.name !== "ResourceNotFoundException") {
        console.error("Error checking table:", error);
        throw error;
      }
      // Table doesn't exist, create it
      console.log(`📦 Creating DynamoDB table "${USERS_TABLE}"...`);
    }

    // Create table
    await dbClient.send(
      new CreateTableCommand({
        TableName: USERS_TABLE,
        KeySchema: [
          { AttributeName: "id", KeyType: "HASH" }, // Partition key
        ],
        AttributeDefinitions: [
          { AttributeName: "id", AttributeType: "S" },
          { AttributeName: "email", AttributeType: "S" },
        ],
        GlobalSecondaryIndexes: [
          {
            IndexName: "email-index",
            KeySchema: [{ AttributeName: "email", KeyType: "HASH" }],
            Projection: { ProjectionType: "ALL" },
            ProvisionedThroughput: {
              ReadCapacityUnits: 5,
              WriteCapacityUnits: 5,
            },
          },
        ],
        BillingMode: "PROVISIONED",
        ProvisionedThroughput: {
          ReadCapacityUnits: 5,
          WriteCapacityUnits: 5,
        },
      })
    );

    console.log(`✅ DynamoDB table "${USERS_TABLE}" created successfully`);
    
    // Wait for table to be ACTIVE (poll every 500ms, max 10 seconds)
    let attempts = 0;
    const maxAttempts = 20;
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 500));
      try {
        const describeResult = await dbClient.send(
          new DescribeTableCommand({
            TableName: USERS_TABLE,
          })
        );
        if (describeResult.Table?.TableStatus === "ACTIVE") {
          console.log(`✅ Table "${USERS_TABLE}" is now ACTIVE`);
          return;
        }
      } catch (error) {
        // Ignore errors during polling
      }
      attempts++;
    }
    console.log(`⚠️ Table "${USERS_TABLE}" created but may not be fully ready yet`);
  } catch (error: any) {
    console.error("Error ensuring table exists:", error);
    
    // If it's a ResourceInUseException, table already exists - that's fine
    if (error?.name === "ResourceInUseException") {
      console.log(`ℹ️ Table "${USERS_TABLE}" already exists`);
      return;
    }
    
    // For other errors, log but don't throw - might be connection issues
    console.error("Error details:", {
      name: error?.name,
      message: error?.message,
      code: error?.code,
    });
  }
}

// Helper function to ensure verification table exists
export async function ensureVerificationTableExists() {
  if (!isLocal) {
    return;
  }

  try {
    const { DynamoDBClient: DBClient, DescribeTableCommand, CreateTableCommand } = await import("@aws-sdk/client-dynamodb");
    
    const dbClient = new DBClient(config);
    
    try {
      const describeResult = await dbClient.send(
        new DescribeTableCommand({
          TableName: VERIFICATION_TABLE,
        })
      );
      
      if (describeResult.Table?.TableStatus === "ACTIVE") {
        console.log(`✅ DynamoDB table "${VERIFICATION_TABLE}" already exists and is active`);
        return;
      }
      
      console.log(`⏳ Table "${VERIFICATION_TABLE}" exists but status is ${describeResult.Table?.TableStatus}, waiting...`);
      await new Promise(resolve => setTimeout(resolve, 2000));
      return;
    } catch (error: any) {
      if (error.name !== "ResourceNotFoundException") {
        console.error("Error checking table:", error);
        throw error;
      }
      console.log(`📦 Creating DynamoDB table "${VERIFICATION_TABLE}"...`);
    }

    // Create verification table
    await dbClient.send(
      new CreateTableCommand({
        TableName: VERIFICATION_TABLE,
        KeySchema: [
          { AttributeName: "email", KeyType: "HASH" },
        ],
        AttributeDefinitions: [
          { AttributeName: "email", AttributeType: "S" },
        ],
        BillingMode: "PROVISIONED",
        ProvisionedThroughput: {
          ReadCapacityUnits: 5,
          WriteCapacityUnits: 5,
        },
      })
    );

    console.log(`✅ DynamoDB table "${VERIFICATION_TABLE}" created successfully`);
    
    // Wait for table to be ACTIVE
    let attempts = 0;
    const maxAttempts = 20;
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 500));
      try {
        const describeResult = await dbClient.send(
          new DescribeTableCommand({
            TableName: VERIFICATION_TABLE,
          })
        );
        if (describeResult.Table?.TableStatus === "ACTIVE") {
          console.log(`✅ Table "${VERIFICATION_TABLE}" is now ACTIVE`);
          return;
        }
      } catch (error) {
        // Ignore errors during polling
      }
      attempts++;
    }
    console.log(`⚠️ Table "${VERIFICATION_TABLE}" created but may not be fully ready yet`);
  } catch (error: any) {
    if (error?.name === "ResourceInUseException") {
      console.log(`ℹ️ Table "${VERIFICATION_TABLE}" already exists`);
      return;
    }
    console.error("Error ensuring verification table exists:", error);
  }
}

