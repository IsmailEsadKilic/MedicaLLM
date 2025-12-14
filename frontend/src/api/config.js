const config = {
    // If VITE_API_URL is set, use it. Otherwise, use empty string to imply relative path (proxied by Vite)
    API_URL: import.meta.env.VITE_API_URL || '',
};

export default config;
