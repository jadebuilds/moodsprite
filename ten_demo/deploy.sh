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
    echo "Uncommitted changes detected. Squashing onto previous commit..."
    git add -A
    git commit --amend --no-edit
fi

# Push to remote (force push if needed for deployment)
echo "Pushing to remote..."
if ! git push origin "$BRANCH" 2>&1 | grep -q "rejected"; then
    echo "Push successful"
else
    echo "Push rejected, pulling first..."
    git pull --rebase origin "$BRANCH" || true
    git push origin "$BRANCH" || git push --force-with-lease origin "$BRANCH"
fi

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

# Initialize submodules if needed (skip ten-framework as it's not in .gitmodules)
if [ -f .gitmodules ]; then
    echo "Initializing submodules..."
    git submodule update --init --recursive 2>&1 | grep -v "ten-framework" || true
fi

echo "Checking TEN framework..."
if [ ! -d "ten_demo/ten-framework" ]; then
    echo "TEN framework not found, cloning..."
    mkdir -p ten_demo
    cd ten_demo
    git clone https://github.com/TEN-framework/ten-framework.git
    cd ..
elif [ -d "ten_demo/ten-framework/.git" ]; then
    echo "TEN framework exists, updating..."
    cd ten_demo/ten-framework
    git fetch origin
    git reset --hard origin/main 2>/dev/null || git reset --hard origin/master 2>/dev/null || true
    cd ../..
fi

# Verify the directory exists
if [ ! -d "ten_demo/ten-framework/ai_agents/agents/examples/local-demo" ]; then
    echo "ERROR: TEN demo directory not found!"
    echo "Current directory: \$(pwd)"
    echo "Contents of ten_demo:"
    ls -la ten_demo/ 2>&1 || echo "ten_demo doesn't exist"
    echo "Trying to create local-demo directory..."
    mkdir -p ten_demo/ten-framework/ai_agents/agents/examples/local-demo
    echo "Please ensure ten-framework is properly cloned and local-demo exists"
    exit 1
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

