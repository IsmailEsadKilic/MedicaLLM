import { Router } from 'express';
import { PutCommand, QueryCommand, GetCommand, DeleteCommand } from '@aws-sdk/lib-dynamodb';
import { docClient } from '../db/dynamodb';
import { v4 as uuidv4 } from 'uuid';
import { AuthRequest } from '../middleware/auth';

const router = Router();

router.get('/', async (req: AuthRequest, res) => {
  try {
    const userId = req.userId;
    const result = await docClient.send(new QueryCommand({
      TableName: 'Patients',
      KeyConditionExpression: 'healthcare_professional_id = :hpId',
      ExpressionAttributeValues: { ':hpId': userId }
    }));
    res.json(result.Items || []);
  } catch (error) {
    console.error('Get patients error:', error);
    res.status(500).json({ error: 'Failed to get patients' });
  }
});

router.post('/', async (req: AuthRequest, res) => {
  try {
    const patient = {
      id: uuidv4(),
      healthcare_professional_id: req.userId,
      ...req.body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    await docClient.send(new PutCommand({
      TableName: 'Patients',
      Item: patient
    }));
    res.status(201).json(patient);
  } catch (error) {
    console.error('Add patient error:', error);
    res.status(500).json({ error: 'Failed to add patient' });
  }
});

router.get('/:id', async (req: AuthRequest, res) => {
  try {
    const result = await docClient.send(new GetCommand({
      TableName: 'Patients',
      Key: { healthcare_professional_id: req.userId, id: req.params.id }
    }));
    if (!result.Item) return res.status(404).json({ error: 'Patient not found' });
    res.json(result.Item);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get patient' });
  }
});

router.put('/:id', async (req: AuthRequest, res) => {
  try {
    const patient = {
      id: req.params.id,
      healthcare_professional_id: req.userId,
      ...req.body,
      updated_at: new Date().toISOString()
    };
    await docClient.send(new PutCommand({
      TableName: 'Patients',
      Item: patient
    }));
    res.json(patient);
  } catch (error) {
    console.error('Update patient error:', error);
    res.status(500).json({ error: 'Failed to update patient' });
  }
});

router.delete('/:id', async (req: AuthRequest, res) => {
  try {
    await docClient.send(new DeleteCommand({
      TableName: 'Patients',
      Key: { healthcare_professional_id: req.userId, id: req.params.id }
    }));
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete patient' });
  }
});

export default router;
