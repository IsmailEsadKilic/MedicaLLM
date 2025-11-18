// API base URL - Backend server
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

export const api = {
  baseURL: API_BASE_URL,
  
  // Auth endpoints
  auth: {
    register: `${API_BASE_URL}/api/auth/register`,
    sendVerification: `${API_BASE_URL}/api/auth/send-verification`,
    verifyEmail: `${API_BASE_URL}/api/auth/verify-email`,
  },
};

