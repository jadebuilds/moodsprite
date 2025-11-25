#!/bin/bash
set -e

# Get current branch name
BRANCH=$(git branch --show-current)
echo "Current branch: $BRANCH"

# Get the repo root (moodsprite)
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Uncommitted changes detected. Committing..."
    git add -A
    git commit -m "Deploy: Update TEN demo with local models"
fi

# Push to remote
echo "Pushing to remote..."
git push origin "$BRANCH"

# SSH into neshemet and deploy
echo "Deploying to neshemet..."
ssh neshemet bash <<EOF
set -e

# Try to find moodsprite repo or clone it
if [ ! -d ~/moodsprite ]; then
    echo "moodsprite repo not found, cloning..."
    cd ~
    git clone git@github.com:jadebuilds/moodsprite.git || git clone https://github.com/jadebuilds/moodsprite.git
fi

cd ~/moodsprite

echo "Fetching latest changes..."
git fetch origin

echo "Checking out branch: $BRANCH"
git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH" "origin/$BRANCH"

echo "Resetting to origin/$BRANCH..."
git reset --hard "origin/$BRANCH"

# Initialize submodules if needed
if [ -f .gitmodules ]; then
    echo "Initializing submodules..."
    git submodule update --init --recursive || true
fi

echo "Navigating to TEN demo directory..."
cd ten_demo/ten-framework/ai_agents/agents/examples/local-demo

echo "Stopping any existing task processes..."
pkill -f "task run" || true
pkill -f "tman" || true
sleep 2

echo "Starting TEN agent in background..."
cd tenapp
nohup task run > /tmp/ten_demo.log 2>&1 &
echo \$! > /tmp/ten_demo.pid

echo "TEN agent started with PID: \$(cat /tmp/ten_demo.pid)"
EOF

echo "Deployment complete!"
echo "Access the web UI at: http://neshemet:3001"
echo "Check logs with: ssh neshemet 'tail -f /tmp/ten_demo.log'"

