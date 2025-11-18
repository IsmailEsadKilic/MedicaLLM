/**
 * Environment Variable Validation
 * 
 * This file validates that all required environment variables are present
 * Call this early in your app initialization
 */

export function validateEnv() {
  const required = {
    // NextAuth
    AUTH_SECRET: process.env.AUTH_SECRET,
    NEXTAUTH_URL: process.env.NEXTAUTH_URL,
    
    // OAuth
    GOOGLE_CLIENT_ID: process.env.GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET: process.env.GOOGLE_CLIENT_SECRET,
    
    // OpenAI (optional for now)
    // OPENAI_API_KEY: process.env.OPENAI_API_KEY,
  };

  const missing: string[] = [];
  const empty: string[] = [];

  Object.entries(required).forEach(([key, value]) => {
    if (value === undefined) {
      missing.push(key);
    } else if (value === '') {
      empty.push(key);
    }
  });

  if (missing.length > 0 || empty.length > 0) {
    const errors: string[] = [];
    
    if (missing.length > 0) {
      errors.push(`Missing: ${missing.join(', ')}`);
    }
    
    if (empty.length > 0) {
      errors.push(`Empty: ${empty.join(', ')}`);
    }

    throw new Error(
      `❌ Environment variable errors:\n${errors.join('\n')}\n\n` +
      `📝 Create a .env.local file with these variables.\n` +
      `📖 See env.example.txt for template.`
    );
  }

  console.log('✅ All required environment variables are set');
}

// Type-safe environment variables
export const env = {
  AUTH_SECRET: process.env.AUTH_SECRET!,
  NEXTAUTH_URL: process.env.NEXTAUTH_URL!,
  GOOGLE_CLIENT_ID: process.env.GOOGLE_CLIENT_ID!,
  GOOGLE_CLIENT_SECRET: process.env.GOOGLE_CLIENT_SECRET!,
  OPENAI_API_KEY: process.env.OPENAI_API_KEY,
} as const;

