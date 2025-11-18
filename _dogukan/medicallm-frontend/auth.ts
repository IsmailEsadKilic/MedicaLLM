import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { z } from "zod";
import bcrypt from "bcryptjs";
import { dynamoDB, USERS_TABLE } from "@/lib/dynamodb";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      authorize: async (credentials) => {
        try {
          // Validate credentials
          const parsedCredentials = z
            .object({
              email: z.string().email(),
              password: z.string().min(6),
            })
            .safeParse(credentials);

          if (!parsedCredentials.success) {
            console.error("❌ Invalid credentials format:", parsedCredentials.error);
            return null;
          }

          const { email, password } = parsedCredentials.data;
          console.log(`🔐 Attempting to authenticate user: ${email}`);

          // Find user in DynamoDB by email (using GSI)
          const { QueryCommand } = await import("@aws-sdk/lib-dynamodb");
          console.log(`🔍 Querying DynamoDB table: ${USERS_TABLE}, endpoint: ${process.env.DYNAMODB_LOCAL_ENDPOINT || "http://localhost:8000"}`);
          
          const result = await dynamoDB.send(
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

          const users = result.Items || [];
          console.log(`👥 Found ${users.length} user(s) with email: ${email}`);
          
          if (users.length === 0) {
            console.error("❌ User not found in database");
            return null;
          }

          const user = users[0] as {
            id: string;
            email: string;
            password: string;
            name: string;
          };

          // Verify password
          console.log("🔐 Verifying password...");
          const passwordMatch = await bcrypt.compare(password, user.password);

          if (!passwordMatch) {
            console.error("❌ Password mismatch");
            return null;
          }

          console.log("✅ Authentication successful!");
          // Return user object
          return {
            id: user.id,
            email: user.email,
            name: user.name,
          };
        } catch (error: any) {
          console.error("❌ Authentication error:", error);
          console.error("Error details:", {
            name: error?.name,
            message: error?.message,
            code: error?.code,
            stack: error?.stack,
          });
          return null;
        }
      },
    }),
  ],
  secret: process.env.AUTH_SECRET,
  pages: {
    signIn: "/auth/signin",
  },
  callbacks: {
    authorized: async ({ auth }) => {
      // Logged in users are authenticated, otherwise redirect to login page
      return !!auth;
    },
  },
  debug: process.env.NODE_ENV === "development",
});

