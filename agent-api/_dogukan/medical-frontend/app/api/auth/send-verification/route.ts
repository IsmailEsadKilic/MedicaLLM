import { NextResponse } from "next/server";
import { z } from "zod";
import { generateVerificationCode, saveVerificationCode } from "@/lib/verification";
import { sendVerificationEmail } from "@/lib/email";
import { ensureVerificationTableExists } from "@/lib/dynamodb";

const sendVerificationSchema = z.object({
  email: z.string().email("Geçerli bir email adresi girin"),
});

export async function POST(request: Request) {
  try {
    // Ensure verification table exists
    await ensureVerificationTableExists();

    const body = await request.json();
    const validation = sendVerificationSchema.safeParse(body);

    if (!validation.success) {
      return NextResponse.json(
        { error: validation.error.errors[0].message },
        { status: 400 }
      );
    }

    const { email } = validation.data;

    // Generate verification code
    const code = generateVerificationCode();

    // Save code to database
    await saveVerificationCode(email, code);

    // Send email (development: console, production: real email)
    const emailSent = await sendVerificationEmail(email, code);

    if (!emailSent) {
      return NextResponse.json(
        { error: "Email gönderilemedi" },
        { status: 500 }
      );
    }

    return NextResponse.json(
      { 
        message: "Doğrulama kodu email adresinize gönderildi"
      },
      { status: 200 }
    );
  } catch (error: any) {
    console.error("Send verification error:", error);
    return NextResponse.json(
      { error: "Doğrulama kodu gönderilemedi" },
      { status: 500 }
    );
  }
}

