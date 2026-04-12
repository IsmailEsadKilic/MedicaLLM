// O11: When VITE_USE_HTTPS=true is supplied at build time, the app will use
// HTTPS for any absolute URL it constructs (e.g. direct WebSocket connections).
// In the standard Docker deployment Nginx proxies /api/ requests, so API_URL
// stays an empty string (relative). Set VITE_BACKEND_URL only when running the
// Vite dev server with the backend on a different origin.
const useHttps = import.meta.env.VITE_USE_HTTPS === 'true';

const config = {
    API_URL: import.meta.env.VITE_BACKEND_URL || '',
    // Expose the TLS flag so other modules can select ws:// vs wss:// or
    // http:// vs https:// when constructing absolute URLs.
    USE_HTTPS: useHttps,
};

export default config;
