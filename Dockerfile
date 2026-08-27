# Base Image: Linux Debian 12 Bookworm (node:20-bookworm-slim)
FROM node:20-bookworm-slim

# Install system media dependencies: ffmpeg, fonts-noto-cjk, libass-dev, fontconfig
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-noto-cjk \
    libass-dev \
    fontconfig \
    ca-certificates \
 && fc-cache -fv \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy application source code and configurations
COPY . .

# Create volume mount directories
RUN mkdir -p /data/ZENION-MUSIC /data/ACE-Step-1.5 /app/data

# Expose backend and client ports
EXPOSE 3000 5173

# Set default environment variables
ENV NODE_ENV=production
ENV PORT=3000
ENV ZENION_ROOT_DIR=/data/ZENION-MUSIC
ENV ACE_WATCH_DIR=/data/ACE-Step-1.5
ENV DATA_DIR=/app/data

# Start application server
CMD ["npm", "start"]
