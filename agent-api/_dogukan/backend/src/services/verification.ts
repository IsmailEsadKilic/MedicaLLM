import { dynamoDB, VERIFICATION_TABLE } from "./dynamodb";
import { PutCommand, GetCommand, DeleteCommand } from "@aws-sdk/lib-dynamodb";
import { randomInt } from "crypto";

// 6 haneli doğrulama kodu oluştur
export function generateVerificationCode(): string {
  return randomInt(100000, 999999).toString();
}

// Doğrulama kodunu kaydet (10 dakika geçerli)
export async function saveVerificationCode(
  email: string,
  code: string
): Promise<void> {
  const expiresAt = new Date();
  expiresAt.setMinutes(expiresAt.getMinutes() + 10); // 10 dakika

  await dynamoDB.send(
    new PutCommand({
      TableName: VERIFICATION_TABLE,
      Item: {
        email,
        code,
        expiresAt: expiresAt.toISOString(),
        createdAt: new Date().toISOString(),
      },
    })
  );
}

// Doğrulama kodunu kontrol et
export async function verifyCode(
  email: string,
  code: string
): Promise<boolean> {
  try {
    const result = await dynamoDB.send(
      new GetCommand({
        TableName: VERIFICATION_TABLE,
        Key: { email },
      })
    );

    if (!result.Item) {
      return false;
    }

    const { code: savedCode, expiresAt } = result.Item;

    // Kod eşleşmiyor
    if (savedCode !== code) {
      return false;
    }

    // Kod süresi dolmuş
    if (new Date(expiresAt) < new Date()) {
      await dynamoDB.send(
        new DeleteCommand({
          TableName: VERIFICATION_TABLE,
          Key: { email },
        })
      );
      return false;
    }

    // Kod doğru ve geçerli - sil
    await dynamoDB.send(
      new DeleteCommand({
        TableName: VERIFICATION_TABLE,
        Key: { email },
      })
    );

    return true;
  } catch (error) {
    console.error("Verification error:", error);
    return false;
  }
}

