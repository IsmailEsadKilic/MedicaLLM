import express, { Request, Response } from 'express';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { body, validationResult } from 'express-validator';
import { PutCommand, GetCommand } from '@aws-sdk/lib-dynamodb';
import { docClient } from '../db/dynamodb';

const router = express.Router();
const USERS_TABLE = process.env.USERS_TABLE || 'Users';
console.log('USERS_TABLE:', USERS_TABLE);

router.post('/register',
  body('email').isEmail(),
  body('password').isLength({ min: 6 }),
  body('name').notEmpty(),
  async (req: Request, res: Response) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { email, password, name } = req.body;
    console.log('Registration attempt:', { email, name });

    try {
      console.log('Checking existing user...');
      const existing = await docClient.send(new GetCommand({
        TableName: USERS_TABLE,
        Key: { email }
      }));
      console.log('Existing check done:', existing.Item ? 'User exists' : 'User does not exist');

      if (existing.Item) {
        return res.status(400).json({ error: 'User already exists' });
      }

      console.log('Hashing password...');
      const hashedPassword = await bcrypt.hash(password, 10);
      const userId = `user_${Date.now()}`;
      console.log('Creating user with ID:', userId);

      console.log('Saving to DynamoDB...');
      await docClient.send(new PutCommand({
        TableName: USERS_TABLE,
        Item: {
          email,
          userId,
          password: hashedPassword,
          name,
          createdAt: new Date().toISOString()
        }
      }));
      console.log('User saved successfully');

      console.log('Generating JWT token...');
      const jwtSecret = process.env.JWT_SECRET || 'default-secret';
      const token = jwt.sign({ userId }, jwtSecret, { expiresIn: '7d' });
      console.log('Token generated successfully');

      res.status(201).json({ token, user: { userId, email, name } });
    } catch (error: any) {
      console.error('Registration error:', error);
      console.error('Error message:', error.message);
      console.error('Error name:', error.name);
      res.status(500).json({ error: 'Registration failed', details: error.message });
    }
  }
);

router.post('/login',
  body('email').isEmail(),
  body('password').notEmpty(),
  async (req: Request, res: Response) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { email, password } = req.body;

    try {
      const result = await docClient.send(new GetCommand({
        TableName: USERS_TABLE,
        Key: { email }
      }));

      if (!result.Item) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      const isValid = await bcrypt.compare(password, result.Item.password);
      if (!isValid) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      const jwtSecret = process.env.JWT_SECRET || 'default-secret';
      const token = jwt.sign({ userId: result.Item.userId }, jwtSecret, { expiresIn: '7d' });

      res.json({ token, user: { userId: result.Item.userId, email: result.Item.email, name: result.Item.name } });
    } catch (error) {
      console.error('Login error:', error);
      res.status(500).json({ error: 'Login failed' });
    }
  }
);

export default router;
