const config = {
    // Change this to your domain when deploying
    // For production: 'https://yourdomain.com'
    // For EC2 testing: 'http://98.80.152.122'
    // For local dev: 'http://localhost:3001'
    API_URL: process.env.VITE_API_URL || 'http://localhost:3001',
};

export default config;
