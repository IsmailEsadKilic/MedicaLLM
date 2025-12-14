import express, { Request, Response } from 'express';
import { PutCommand, GetCommand, ScanCommand, DeleteCommand } from '@aws-sdk/lib-dynamodb';
import { docClient } from '../db/dynamodb';

const router = express.Router();
const TABLE_NAME = process.env.TABLE_NAME;

router.post('/', async (req: Request, res: Response) => {
  const { id, name } = req.body;
  await docClient.send(new PutCommand({
    TableName: TABLE_NAME,
    Item: { id, name, createdAt: new Date().toISOString() }
  }));
  res.json({ message: 'Item created', id });
});

router.get('/', async (req: Request, res: Response) => {
  const { Items } = await docClient.send(new ScanCommand({ TableName: TABLE_NAME }));
  res.json(Items);
});

router.get('/:id', async (req: Request, res: Response) => {
  const { Item } = await docClient.send(new GetCommand({
    TableName: TABLE_NAME,
    Key: { id: req.params.id }
  }));
  res.json(Item || {});
});

router.delete('/:id', async (req: Request, res: Response) => {
  await docClient.send(new DeleteCommand({
    TableName: TABLE_NAME,
    Key: { id: req.params.id }
  }));
  res.json({ message: 'Item deleted' });
});

export default router;
