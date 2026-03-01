Let me do a thorough review of your entire project. I'll start by reading all the key files across your four services.

Now let me check a few more remaining files and the remaining parts of key files:

I've now read through your entire project. Here's my thorough critique:

MedicaLLM Project Review
1. Architecture & Separation of Concerns
The Good: You clearly understand the 4-container model and why you want it. The Python agent handles AI, the Node backend handles auth, the frontend handles UI, DynamoDB handles storage. That's a solid intuition.

The Bad:

Your "separation of concerns" is violated immediately. The agent-api (Python) talks directly to DynamoDB for conversations, drugs, interactions. The backend (Node) ALSO talks directly to DynamoDB for users, patients, AND also has its own drug search routes in drugSearch.ts that duplicate the same drug lookup logic that exists in dynamodb_manager.py. You have two separate services doing the same DynamoDB drug lookups with the same case-variant retry logic, copy-pasted across languages. This defeats the purpose of your backend being "the bridge."

The backend is barely a bridge. Look at agentApiService.ts — it's just a thin axios.post() proxy to the Python API. The conversations routes fetch from the agent-api, then re-verify ownership. But the drug search routes in drugSearch.ts bypass the agent-api entirely and go straight to DynamoDB. There's no consistent pattern for who "owns" what data.

Who owns conversations? The agent-api creates conversations, stores them, manages messages. But the backend also creates a Conversations table in init.ts with a DIFFERENT schema (single id hash key) than what setup_database.py creates (PK/SK composite key with GSI). You have two incompatible table definitions for the same concept.

2. File Structure Problems
agent-api is a junk drawer. Everything sits at root level: api_server.py, medical_agent.py, vector_store.py, pdf_processor.py, dynamodb_manager.py, models.py, session.py. There's no package structure. For a Python project, you should have a proper package like:

printmeup/ is vendored inside your project. This appears to be a custom logging/pretty-print library bundled directly into the repo. It should either be a proper installable package or just use Python's logging module with rich for formatting.

drugbank_schema/ with generated xsdata code sits at root level of agent-api with no clear connection to anything — I see no imports of it anywhere in the actual application code. Dead code.

docker-compose.yml — there's a SECOND docker-compose file inside agent-api/scripts. Why?

data/ directory inside agent-api contains actual DrugBank XML data. This should not be in the repo. It should be downloaded at build time or mounted as a volume.

chroma_db/ with chroma.sqlite3 is checked into git. Database files should never be committed.

__pycache__/ directories visible in the tree — your .gitignore may not be catching everything.

Frontend has App.jsx AND Chat.jsx that are essentially the SAME component with different implementations. App.jsx has an old hardcoded version that doesn't use the router, and Chat.jsx has the newer version. App.jsx should be a shell that just renders the router, not a 250-line component duplicating Chat functionality.

test.html, test-db.js, DrugSearchTest.jsx — test artifacts littered around with no test framework.

items.ts route — this is clearly scaffolding/boilerplate left over from a tutorial. It's a generic CRUD router with no relevance to a medical app. Dead code.

3. Security Issues (Critical)
Hardcoded credentials everywhere:

dynamodb.ts:8: accessKeyId: 'dummy' hardcoded
dynamodb_manager.py:19: aws_access_key_id='dummy' hardcoded
Docker-compose: AWS_ACCESS_KEY_ID=test
These should ALL come from environment variables, even for local dev.
JWT secret defaults to 'default-secret' in auth.ts:14 and 'change-me-in-production' in docker-compose. If anyone forgets to set it, tokens are trivially forgeable.

No auth on the agent-api at all. Anyone who can reach port 2580 can create conversations, query the AI, read any conversation by ID. The backend adds auth middleware, but the agent-api is wide open. In your Docker network this is somewhat mitigated, but the port IS mapped to the host (ports: "2580:2580").

No input sanitization on the Python side. User queries go directly into LLM prompts without any sanitization — prompt injection risk.

Passwords are logged — look at auth.ts:28: console.log('Registration attempt:', { email, name, accountType }) logs are everywhere. While passwords aren't in that specific line, the verbose error logging (console.error('Registration error:', error)) could leak sensitive info.

4. Code Quality Issues
Global mutable state in Python:

active_sessions = {} in api_server.py:40 — sessions stored in a dict that grows forever. No eviction, no cleanup, memory leak.
_retriever and _last_search_sources as module-level globals in medical_agent.py:15-16 — this is thread-unsafe. If two requests hit search_medical_documents concurrently, they'll stomp on each other's sources.
The RAG tool creates a NEW LLM instance on every call. Look at medical_agent.py:290: search_medical_documents creates ChatBedrock(...) inside the tool function. This means every RAG query spins up a new client, AND you're making TWO LLM calls per RAG query (one in the tool, one from the agent wrapping it). You're burning double the API cost.

Conversation history is re-serialized on every message. add_message() in dynamodb_manager.py calls get_conversation() (full read), appends a message, then calls save_conversation() (full write of the entire conversation including ALL messages). As conversations grow, this becomes 
O
(
n
)
O(n) per message. DynamoDB charges per KB written.

Frontend manually builds conversation history as a string in Chat.jsx:283:

This is appalling. You're sending the ENTIRE conversation as a giant string in each query, AND the agent-api also maintains conversation history in its Session. You're double-sending context, wasting tokens, and the string format will confuse the LLM.

pyproject.toml says requires-python = ">=3.13" but Dockerfile uses python:3.11-slim. These are incompatible.

Title generation calls Ollama via http://host.docker.internal:11434 — a 5th undeclared service! It's in drugs.ts:54 and session.py:295 (which uses ChatOllama), but there's no Ollama container in your docker-compose. This will silently fail.

5. Docker Issues
Frontend runs Vite dev server in production. The Dockerfile's CMD is npx vite --host 0.0.0.0. This is a development server. For production, you should npm run build and serve the static files with nginx.

Frontend Dockerfile installs dev dependencies (--include=dev), runs rm -rf node_modules && npm cache clean --force which is a sign of previous debugging desperation. This shouldn't be necessary in a clean build.

Backend Dockerfile installs python3 make g++ — these are native build dependencies for bcrypt. This is technically necessary but you should use a multi-stage build to avoid shipping compiler tools in production.

No .env file exists but .env is referenced in .gitignore and load_dotenv(). New developers cloning the repo will have no idea what environment variables are needed.

No multi-stage Docker builds anywhere. Your Python image ships with all build tools, source code, and the entire UV binary.

VITE_BACKEND_URL=http://backend:3001 in docker-compose is wrong for a browser-side app. Vite injects VITE_* vars at BUILD time, and the browser can't resolve backend:3001 (that's a Docker-internal hostname). Your config.js hardcodes localhost:3001 which is what actually works, making the environment variable useless.

Agent-api is exposed on port 2580 to the host. Since the backend is supposed to be the bridge, the agent-api should only be accessible within the Docker network (remove the ports mapping and only keep the internal network exposure).

6. Library / Technology Choices
LangChain is brutally over-engineered for what you're doing. You're using langchain, langchain-core, langchain-aws, langchain-community, langchain-chroma, langchain-huggingface — that's 6 LangChain packages. Your actual usage is: call Bedrock, do a vector search, run an agent with tools. You could do this with boto3 + chromadb directly in ~100 lines. LangChain adds massive dependency weight (your Docker image is probably 3-4 GB) and makes debugging nightmarish.

sentence-transformers + torch (CPU) pulled in for embeddings. This is a ~2GB dependency. Consider using fastembed or an API-based embedding service instead — especially since you're already paying for Bedrock.

einops is in dependencies — this is a tensor manipulation library. I see zero usage of it anywhere. Dead dependency.

undici is in backend dependencies — Node.js 20 already ships with undici built-in as the fetch implementation. Redundant.

xsdata in Python dependencies — seems to be for parsing the DrugBank XML schema, but the generated drugbank_schema/ code isn't imported anywhere in the app. Dead dependency.

No state management in frontend. Everything is useState spaghetti with prop drilling. For a chat app with auth, conversations, and multiple views, you should use React Context at minimum, or Zustand/Redux Toolkit.

No TypeScript in frontend. Given that the backend is TypeScript, the frontend should be too for consistency.

Express.js without helmet, rate limiting, or compression. Trivially DDoS-able.

7. Other Issues
No tests. Zero. Not a single test file with an actual test framework. For a medical application, this is particularly concerning.

No environment variable validation. If BEDROCK_MODEL_ID or AWS_REGION is missing, things silently use defaults or crash at runtime.

No API documentation. FastAPI auto-generates OpenAPI docs, which is great, but the Express backend has no documentation at all.

Console.log everywhere. Both Python (pm.inf/pm.suc/pm.err) and Node (console.log) produce verbose output. There's no log level control in the Node backend.

No error boundaries in React. If any component throws, the whole app white-screens.

Commented-out code scattered throughout — old model IDs, alternative URLs, etc. Clean these up.

The README.md files — I haven't checked them in detail, but given the state of the code, they're likely outdated.

Summary: Priority Fixes
Priority	Issue
P0	Remove hardcoded credentials, fix JWT secret defaults
P0	Don't expose agent-api port to host
P0	Fix Python version mismatch (pyproject.toml vs Dockerfile)
P1	Eliminate duplicated drug lookup logic (pick ONE service to own DynamoDB)
P1	Fix double conversation history (frontend string concat + backend session)
P1	Stop running Vite dev server in "production" Docker
P1	Remove the ghost Ollama dependency or add it to docker-compose
P1	Fix the memory leak in active_sessions
P2	Remove dead code (items.ts, App.jsx old chat, drugbank_schema/, einops, undici)
P2	Add proper Python package structure
P2	Add at least basic integration tests
P3	Consider dropping LangChain for direct Bedrock + ChromaDB usage
P3	Add React Context or Zustand for state management
P3	Add rate limiting, helmet, error boundaries
For uni students, the core idea and ambition are solid. But the project has the hallmark signs of "make it work first, clean up later" — except the cleanup never happened. The biggest systemic problem is the unclear ownership boundary between your Python and Node services. Define which service owns which data, make the backend a real gateway, and half of your issues will resolve themselves.