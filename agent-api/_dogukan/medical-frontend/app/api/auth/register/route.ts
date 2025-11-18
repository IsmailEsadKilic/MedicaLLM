import { dynamoDB, USERS_TABLE, ensureTableExists } from "@/lib/dynamodb";
import bcrypt from "bcryptjs";
import { NextResponse } from "next/server";
import { z } from "zod";
import { PutCommand, QueryCommand } from "@aws-sdk/lib-dynamodb";
import { randomUUID } from "crypto";

const registerSchema = z.object({
  name: z.string().min(2, "İsim en az 2 karakter olmalıdır"),
  email: z.string().email("Geçerli bir email adresi girin"),
  password: z.string().min(6, "Şifre en az 6 karakter olmalıdır"),
});

export async function POST(request: Request) {
  console.log("📝 Register request received");
  try {
    // Ensure table exists (for local development)
    console.log("🔍 Ensuring DynamoDB table exists...");
    await ensureTableExists();
    console.log("✅ Table check complete");

    const body = await request.json();

    // Validate input
    const validation = registerSchema.safeParse(body);

    if (!validation.success) {
      return NextResponse.json(
        { error: validation.error.errors[0].message },
        { status: 400 }
      );
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
      return NextResponse.json(
        { error: "Bu email zaten kayıtlı" },
        { status: 409 }
      );
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
    return NextResponse.json(
      { message: "Kayıt başarılı", user: userWithoutPassword },
      { status: 201 }
    );
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
    
    return NextResponse.json(
      { 
        error: "Kayıt sırasında bir hata oluştu",
        details: process.env.NODE_ENV === "development" ? errorMessage : undefined
      },
      { status: 500 }
    );
  }
}

