# Use the official Node.js image as a base
FROM node:18

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of your application files to the container
COPY . .

# Run npm audit and fix vulnerabilities (if desired)
# Run npm audit and ignore failures
RUN npm audit || echo "npm audit failed, continuing..."

# Attempt to fix vulnerabilities and ignore failures
RUN npm audit fix --force || echo "npm audit fix failed, continuing..."

# Expose the port your app runs on
EXPOSE 3000

# Command to run your app
CMD ["node", "server.js"]
