# Environment Variables Setup

Create a `.env.local` file in the root directory with these variables:

```env
# NextAuth.js Configuration
AUTH_SECRET=your-secret-key-here-generate-with-openssl-rand-base64-32
NEXTAUTH_URL=http://localhost:3000

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# OpenAI API (for chat functionality)
OPENAI_API_KEY=your-openai-api-key
```

## How to Get Google OAuth Credentials:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Go to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Choose "Web application"
6. Add authorized redirect URI: `http://localhost:3000/api/auth/callback/google`
7. Copy the Client ID and Client Secret

## Generate AUTH_SECRET:

Run this command in terminal:
```bash
openssl rand -base64 32
```

Or use this in Node.js:
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

