import { NextResponse } from "next/server";
import { z } from "zod";
import { verifyCode } from "@/lib/verification";

const verifyEmailSchema = z.object({
  email: z.string().email("Geçerli bir email adresi girin"),
  code: z.string().length(6, "Kod 6 haneli olmalıdır"),
});

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const validation = verifyEmailSchema.safeParse(body);

    if (!validation.success) {
      return NextResponse.json(
        { error: validation.error.errors[0].message },
        { status: 400 }
      );
    }

    const { email, code } = validation.data;

    // Verify code
    const isValid = await verifyCode(email, code);

    if (!isValid) {
      return NextResponse.json(
        { error: "Geçersiz veya süresi dolmuş kod" },
        { status: 400 }
      );
    }

    return NextResponse.json(
      { message: "Email doğrulandı" },
      { status: 200 }
    );
  } catch (error: any) {
    console.error("Verify email error:", error);
    return NextResponse.json(
      { error: "Doğrulama sırasında bir hata oluştu" },
      { status: 500 }
    );
  }
}

