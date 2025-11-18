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
        // Validate credentials
        const parsedCredentials = z
          .object({
            email: z.string().email(),
            password: z.string().min(6),
          })
          .safeParse(credentials);

        if (!parsedCredentials.success) {
          return null;
        }

        const { email, password } = parsedCredentials.data;

        // Find user in DynamoDB by email (using GSI)
        const { QueryCommand } = await import("@aws-sdk/lib-dynamodb");
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
        if (users.length === 0) {
          return null;
        }

        const user = users[0] as {
          id: string;
          email: string;
          password: string;
          name: string;
        };

        // Verify password
        const passwordMatch = await bcrypt.compare(password, user.password);

        if (!passwordMatch) {
          return null;
        }

        // Return user object
        return {
          id: user.id,
          email: user.email,
          name: user.name,
        };
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

