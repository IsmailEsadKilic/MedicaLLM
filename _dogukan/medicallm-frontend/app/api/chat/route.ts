import { openai } from "@ai-sdk/openai";
import { streamText, UIMessage, convertToModelMessages } from "ai";
import { auth } from "@/auth";

export async function POST(req: Request) {
  // Check if user is authenticated
  const session = await auth();
  
  if (!session?.user) {
    return new Response("Unauthorized", { status: 401 });
  }

  const { messages }: { messages: UIMessage[] } = await req.json();
  const result = streamText({
    model: openai("gpt-5-nano"),
    messages: convertToModelMessages(messages),
  });

  return result.toUIMessageStreamResponse();
}
