FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Clean install all dependencies
RUN rm -rf node_modules && \
    npm cache clean --force && \
    npm install --include=dev && \
    npm list vite || echo "Vite check failed but continuing..."

# Copy rest of the application
COPY . .

EXPOSE 3000

# Run dev server with host binding for Docker using npx to ensure vite is found
CMD ["npx", "vite", "--host", "0.0.0.0"]
