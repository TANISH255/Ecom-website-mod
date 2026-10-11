FROM node:22-alpine

WORKDIR /usr/src/app

# Install dependencies first so Docker can cache this layer
COPY package*.json ./
RUN npm ci --omit=dev

# Copy the app source (filtered by .dockerignore)
COPY . .

ENV NODE_ENV=production
EXPOSE 3000

# Run as the non-root user that ships with the Node image
USER node

CMD ["node", "server.js"]