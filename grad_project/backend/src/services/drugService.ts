import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand } from '@aws-sdk/lib-dynamodb';

const client = new DynamoDBClient({
  endpoint: 'http://localhost:8000',
  region: 'us-east-1',
  credentials: {
    accessKeyId: 'dummy',
    secretAccessKey: 'dummy'
  }
});

const docClient = DynamoDBDocumentClient.from(client);

async function resolveDrugName(drugName: string): Promise<string> {
  try {
    // First check if it's a synonym
    const synonymResponse = await docClient.send(new GetCommand({
      TableName: 'Drugs',
      Key: { PK: `DRUG#${drugName}`, SK: 'SYNONYM' }
    }));

    if (synonymResponse.Item && synonymResponse.Item.type === 'synonym') {
      return synonymResponse.Item.points_to as string;
    }

    // Check if it's a direct drug
    const drugResponse = await docClient.send(new GetCommand({
      TableName: 'Drugs',
      Key: { PK: `DRUG#${drugName}`, SK: 'META' }
    }));

    if (drugResponse.Item) {
      return drugResponse.Item.name as string;
    }

    // Not found, return original
    return drugName;
  } catch (error) {
    return drugName;
  }
}

export async function getDrugInfo(drugName: string) {
  try {
    // First check if it's a synonym
    const synonymResponse = await docClient.send(new GetCommand({
      TableName: 'Drugs',
      Key: { PK: `DRUG#${drugName}`, SK: 'SYNONYM' }
    }));

    let drug;
    let queriedName = drugName;
    let actualName = drugName;

    if (synonymResponse.Item && synonymResponse.Item.type === 'synonym') {
      // It's a synonym, get the actual drug
      actualName = synonymResponse.Item.points_to as string;
      const actualResponse = await docClient.send(new GetCommand({
        TableName: 'Drugs',
        Key: { PK: `DRUG#${actualName}`, SK: 'META' }
      }));
      drug = actualResponse.Item;
    } else {
      // Try to get as direct drug
      const drugResponse = await docClient.send(new GetCommand({
        TableName: 'Drugs',
        Key: { PK: `DRUG#${drugName}`, SK: 'META' }
      }));
      drug = drugResponse.Item;
    }

    if (!drug) {
      return { error: `Drug '${drugName}' not found` };
    }

    // is_synonym true only if actualName is different from queriedName (case-insensitive)
    const isSynonym = queriedName.toLowerCase() !== actualName.toLowerCase();

    return {
      queried_name: queriedName,
      actual_name: actualName,
      is_synonym: isSynonym,
      name: drug.name,
      drug_id: drug.drug_id,
      indication: drug.indication || 'N/A',
      mechanism_of_action: drug.mechanism_of_action || 'N/A',
      pharmacodynamics: drug.pharmacodynamics || 'N/A',
      toxicity: drug.toxicity || 'N/A',
      metabolism: drug.metabolism || 'N/A',
      absorption: drug.absorption || 'N/A',
      half_life: drug.half_life || 'N/A',
      protein_binding: drug.protein_binding || 'N/A',
      groups: drug.groups || [],
      categories: drug.categories || []
    };
  } catch (error) {
    return { error: String(error) };
  }
}

export async function checkDrugInteraction(drug1: string, drug2: string) {
  try {
    // Resolve synonyms first
    const resolvedDrug1 = await resolveDrugName(drug1);
    const resolvedDrug2 = await resolveDrugName(drug2);

    // Try first direction
    let response = await docClient.send(new GetCommand({
      TableName: 'DrugInteractions',
      Key: {
        PK: `DRUG#${resolvedDrug1}`,
        SK: `INTERACTS#${resolvedDrug2}`
      }
    }));

    if (response.Item) {
      return {
        interaction_found: true,
        drug1: response.Item.drug1_name,
        drug2: response.Item.drug2_name,
        description: response.Item.description
      };
    }

    // Try reverse direction
    response = await docClient.send(new GetCommand({
      TableName: 'DrugInteractions',
      Key: {
        PK: `DRUG#${resolvedDrug2}`,
        SK: `INTERACTS#${resolvedDrug1}`
      }
    }));

    if (response.Item) {
      return {
        interaction_found: true,
        drug1: response.Item.drug1_name,
        drug2: response.Item.drug2_name,
        description: response.Item.description
      };
    }

    return {
      interaction_found: false,
      message: `No interaction found between ${resolvedDrug1} and ${resolvedDrug2}`
    };
  } catch (error) {
    return { error: String(error) };
  }
}
