import { Router } from 'express';
import { GetCommand, ScanCommand } from '@aws-sdk/lib-dynamodb';
import { docClient } from '../db/dynamodb';

const router = Router();

router.get('/search/:query', async (req, res) => {
  try {
    const { query } = req.params;
    const searchTerm = query.toLowerCase();
    
    // Search both main drugs and synonyms
    const [mainResult, synResult] = await Promise.all([
      docClient.send(new ScanCommand({
        TableName: 'Drugs',
        FilterExpression: 'SK = :meta AND (begins_with(name_lower, :search) OR contains(name_lower, :search))',
        ExpressionAttributeValues: { ':meta': 'META', ':search': searchTerm },
        Limit: 50
      })),
      docClient.send(new ScanCommand({
        TableName: 'Drugs',
        FilterExpression: 'SK = :syn AND (begins_with(synonym_lower, :search) OR contains(synonym_lower, :search))',
        ExpressionAttributeValues: { ':syn': 'SYNONYM', ':search': searchTerm },
        Limit: 50
      }))
    ]);
    
    // Combine and deduplicate results
    const drugMap = new Map();
    
    // Add main drugs
    (mainResult.Items || []).forEach(item => {
      drugMap.set(item.name, { name: item.name, drug_id: item.drug_id, name_lower: item.name_lower });
    });
    
    // Add drugs from synonyms (use actual drug name, not synonym)
    (synResult.Items || []).forEach(item => {
      if (item.points_to && !drugMap.has(item.points_to)) {
        drugMap.set(item.points_to, { name: item.points_to, drug_id: item.drug_id, name_lower: item.points_to.toLowerCase() });
      }
    });
    
    // Sort and limit
    const drugs = Array.from(drugMap.values())
      .sort((a, b) => {
        const aStarts = a.name_lower.startsWith(searchTerm);
        const bStarts = b.name_lower.startsWith(searchTerm);
        if (aStarts && !bStarts) return -1;
        if (!aStarts && bStarts) return 1;
        return a.name.localeCompare(b.name);
      })
      .slice(0, 10)
      .map(({ name, drug_id }) => ({ name, drug_id }));
    
    res.json({ drugs, count: drugs.length });
  } catch (error: any) {
    console.error('Search error:', error);
    res.status(500).json({ error: 'Failed to search drugs', details: error.message });
  }
});

router.get('/:drugName', async (req, res) => {
  try {
    const { drugName } = req.params;
    const name = drugName.trim();
    
    // Try direct lookup
    for (const variant of [name, name.charAt(0).toUpperCase() + name.slice(1).toLowerCase()]) {
      const result = await docClient.send(new GetCommand({
        TableName: 'Drugs',
        Key: { PK: `DRUG#${variant}`, SK: 'META' }
      }));
      
      if (result.Item) {
        return res.json({
          success: true,
          drug_name: result.Item.name,
          drug_id: result.Item.drug_id,
          description: result.Item.description || 'N/A',
          indication: result.Item.indication || 'N/A',
          mechanism_of_action: result.Item.mechanism_of_action || 'N/A',
          pharmacodynamics: result.Item.pharmacodynamics || 'N/A',
          toxicity: result.Item.toxicity || 'N/A',
          metabolism: result.Item.metabolism || 'N/A',
          absorption: result.Item.absorption || 'N/A',
          half_life: result.Item.half_life || 'N/A',
          groups: result.Item.groups || [],
          categories: result.Item.categories || []
        });
      }
      
      // Try synonym
      const synResult = await docClient.send(new GetCommand({
        TableName: 'Drugs',
        Key: { PK: `DRUG#${variant}`, SK: 'SYNONYM' }
      }));
      
      if (synResult.Item?.points_to) {
        const actualResult = await docClient.send(new GetCommand({
          TableName: 'Drugs',
          Key: { PK: `DRUG#${synResult.Item.points_to}`, SK: 'META' }
        }));
        
        if (actualResult.Item) {
          return res.json({
            success: true,
            is_synonym: true,
            queried_name: drugName,
            actual_name: synResult.Item.points_to,
            drug_name: actualResult.Item.name,
            drug_id: actualResult.Item.drug_id,
            description: actualResult.Item.description || 'N/A',
            indication: actualResult.Item.indication || 'N/A',
            mechanism_of_action: actualResult.Item.mechanism_of_action || 'N/A',
            pharmacodynamics: actualResult.Item.pharmacodynamics || 'N/A',
            toxicity: actualResult.Item.toxicity || 'N/A',
            metabolism: actualResult.Item.metabolism || 'N/A',
            absorption: actualResult.Item.absorption || 'N/A',
            half_life: actualResult.Item.half_life || 'N/A',
            groups: actualResult.Item.groups || [],
            categories: actualResult.Item.categories || []
          });
        }
      }
    }
    
    res.status(404).json({ error: `Drug '${drugName}' not found` });
  } catch (error: any) {
    res.status(500).json({ error: 'Failed to fetch drug info' });
  }
});

router.get('/interaction/:drug1/:drug2', async (req, res) => {
  try {
    const { drug1, drug2 } = req.params;
    
    // Try both directions
    for (const [d1, d2] of [[drug1, drug2], [drug2, drug1]]) {
      for (const v1 of [d1, d1.charAt(0).toUpperCase() + d1.slice(1).toLowerCase()]) {
        for (const v2 of [d2, d2.charAt(0).toUpperCase() + d2.slice(1).toLowerCase()]) {
          const result = await docClient.send(new GetCommand({
            TableName: 'DrugInteractions',
            Key: { PK: `DRUG#${v1}`, SK: `INTERACTS#${v2}` }
          }));
          
          if (result.Item) {
            return res.json({
              success: true,
              interaction_found: true,
              drug1: result.Item.drug1_name,
              drug2: result.Item.drug2_name,
              description: result.Item.description || 'No description available'
            });
          }
        }
      }
    }
    
    res.json({
      success: true,
      interaction_found: false,
      drug1,
      drug2,
      message: `No known interaction found between ${drug1} and ${drug2}`
    });
  } catch (error: any) {
    res.status(500).json({ error: 'Failed to check interaction' });
  }
});

export default router;
