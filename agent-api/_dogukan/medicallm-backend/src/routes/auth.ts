import express, { Request, Response } from "express";
import bcrypt from "bcryptjs";
import { z } from "zod";
import { PutCommand, QueryCommand } from "@aws-sdk/lib-dynamodb";
import { randomUUID } from "crypto";
import { dynamoDB, USERS_TABLE, ensureTableExists } from "../services/dynamodb";
import { generateVerificationCode, saveVerificationCode, verifyCode } from "../services/verification";
import { sendVerificationEmail } from "../services/email";
import { ensureVerificationTableExists } from "../services/dynamodb";

const router = express.Router();

const registerSchema = z.object({
  name: z.string().min(2, "İsim en az 2 karakter olmalıdır"),
  email: z.string().email("Geçerli bir email adresi girin"),
  password: z.string().min(6, "Şifre en az 6 karakter olmalıdır"),
});

// Register endpoint
router.post("/register", async (req: Request, res: Response) => {
  console.log("📝 Register request received");
  try {
    // Ensure table exists (for local development)
    console.log("🔍 Ensuring DynamoDB table exists...");
    await ensureTableExists();
    console.log("✅ Table check complete");

    // Validate input
    const validation = registerSchema.safeParse(req.body);

    if (!validation.success) {
      return res.status(400).json({
        error: validation.error.errors[0].message,
      });
    }

    const { name, email, password } = validation.data;
    console.log(`👤 Registering user: ${name} (${email})`);

    // Check if user already exists (using email index)
    console.log("🔍 Checking if user already exists...");
    const existingUserResult = await dynamoDB.send(
      new QueryCommand({
        TableName: USERS_TABLE,
        IndexName: "email-index",
        KeyConditionExpression: "email = :email",
        ExpressionAttributeValues: {
          ":email": email,
        },
        Limit: 1,
      })
    );

    if (existingUserResult.Items && existingUserResult.Items.length > 0) {
      return res.status(409).json({
        error: "Bu email zaten kayıtlı",
      });
    }

    // Hash password
    console.log("🔐 Hashing password...");
    const hashedPassword = await bcrypt.hash(password, 10);

    // Create user
    console.log("👤 Creating user record...");
    const userId = randomUUID();
    const now = new Date().toISOString();

    const user = {
      id: userId,
      email,
      name,
      password: hashedPassword,
      createdAt: now,
      updatedAt: now,
    };

    console.log(`💾 Saving user to DynamoDB table: ${USERS_TABLE}`);
    await dynamoDB.send(
      new PutCommand({
        TableName: USERS_TABLE,
        Item: user,
      })
    );
    console.log("✅ User saved successfully");

    // Return user without password
    const { password: _, ...userWithoutPassword } = user;

    console.log("🎉 Registration successful!");
    return res.status(201).json({
      message: "Kayıt başarılı",
      user: userWithoutPassword,
    });
  } catch (error: any) {
    console.error("Registration error:", error);

    // More detailed error message for debugging
    const errorMessage = error?.message || "Kayıt sırasında bir hata oluştu";
    const errorCode = error?.code || "UNKNOWN_ERROR";

    console.error("Error details:", {
      message: errorMessage,
      code: errorCode,
      name: error?.name,
      stack: error?.stack,
    });

    return res.status(500).json({
      error: "Kayıt sırasında bir hata oluştu",
      details: process.env.NODE_ENV === "development" ? errorMessage : undefined,
    });
  }
});

const sendVerificationSchema = z.object({
  email: z.string().email("Geçerli bir email adresi girin"),
});

// Send verification code endpoint
router.post("/send-verification", async (req: Request, res: Response) => {
  try {
    // Ensure verification table exists
    await ensureVerificationTableExists();

    const validation = sendVerificationSchema.safeParse(req.body);

    if (!validation.success) {
      return res.status(400).json({
        error: validation.error.errors[0].message,
      });
    }

    const { email } = validation.data;

    // Generate verification code
    const code = generateVerificationCode();

    // Save code to database
    await saveVerificationCode(email, code);

    // Send email (development: console, production: real email)
    const emailSent = await sendVerificationEmail(email, code);

    if (!emailSent) {
      return res.status(500).json({
        error: "Email gönderilemedi",
      });
    }

    return res.status(200).json({
      message: "Doğrulama kodu email adresinize gönderildi",
    });
  } catch (error: any) {
    console.error("Send verification error:", error);
    return res.status(500).json({
      error: "Doğrulama kodu gönderilemedi",
    });
  }
});

const verifyEmailSchema = z.object({
  email: z.string().email("Geçerli bir email adresi girin"),
  code: z.string().length(6, "Kod 6 haneli olmalıdır"),
});

// Verify email endpoint
router.post("/verify-email", async (req: Request, res: Response) => {
  try {
    const validation = verifyEmailSchema.safeParse(req.body);

    if (!validation.success) {
      return res.status(400).json({
        error: validation.error.errors[0].message,
      });
    }

    const { email, code } = validation.data;

    // Verify code
    const isValid = await verifyCode(email, code);

    if (!isValid) {
      return res.status(400).json({
        error: "Geçersiz veya süresi dolmuş kod",
      });
    }

    return res.status(200).json({
      message: "Email doğrulandı",
    });
  } catch (error: any) {
    console.error("Verify email error:", error);
    return res.status(500).json({
      error: "Doğrulama sırasında bir hata oluştu",
    });
  }
});

export default router;

