#!/bin/bash

# --- Configuration Section ---
# Replace these with your actual server and registry details
REMOTE_USER="your_user"
REMOTE_HOST="your_server_ip"
REMOTE_PATH="~/finance_dashboard"
DOCKER_REGISTRY="" # e.g., "docker.io/your_username" or "" for local transfer
# -----------------------------

set -e

echo "🚀 Starting Deployment Process..."

# 1. Check for .env file
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found. Please create one before deploying."
    exit 1
fi

# 2. Build and Push Images (Registry Method)
if [ -n "$DOCKER_REGISTRY" ]; then
    echo "📦 Building and Pushing images to $DOCKER_REGISTRY..."
    docker-compose build
    docker tag finance_backend:latest $DOCKER_REGISTRY/finance_backend:latest
    docker tag finance_frontend:latest $DOCKER_REGISTRY/finance_frontend:latest
    docker push $DOCKER_REGISTRY/finance_backend:latest
    docker push $DOCKER_REGISTRY/finance_frontend:latest
else
    # 2. Alternative: Sync Files and Build on Server (Simpler for Small Servers)
    echo "📂 Syncing files to remote server $REMOTE_HOST..."
    ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_PATH"
    rsync -avz --exclude 'venv' --exclude 'node_modules' --exclude '.git' ./ $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH
fi

# 3. Remote Update
echo "⚙️  Updating remote containers..."
ssh $REMOTE_USER@$REMOTE_HOST << EOF
    cd $REMOTE_PATH
    if [ -n "$DOCKER_REGISTRY" ]; then
        docker pull $DOCKER_REGISTRY/finance_backend:latest
        docker pull $DOCKER_REGISTRY/finance_frontend:latest
    fi
    docker-compose up -d --build
    docker image prune -f
EOF

echo "✅ Deployment Successful!"
echo "📍 Access your application at http://$REMOTE_HOST:3000"
