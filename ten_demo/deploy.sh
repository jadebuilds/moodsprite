#!/bin/bash
set -e

# Get current branch name
BRANCH=$(git branch --show-current)
if [ -z "$BRANCH" ]; then
    echo "ERROR: Not on a branch (detached HEAD). Please checkout a branch first."
    exit 1
fi
echo "Current branch: $BRANCH"

# Get the repo root (moodsprite)
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# Check if we're in the middle of a rebase/merge
if [ -d ".git/rebase-merge" ] || [ -d ".git/rebase-apply" ] || [ -f ".git/MERGE_HEAD" ]; then
    echo "ERROR: Git operation in progress. Please complete or abort it first."
    exit 1
fi

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "WARNING: Uncommitted changes detected."
    echo "Please commit or stash your changes before deploying."
    echo "To commit: git add -A && git commit -m 'Your message'"
    exit 1
fi

# Push to remote
echo "Pushing to remote..."
git push origin "$BRANCH" || {
    echo "Push failed. Attempting to pull and merge..."
    git pull origin "$BRANCH"
    git push origin "$BRANCH"
}

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

# Clean up any existing ten-framework directory that's not a submodule
if [ -d "ten_demo/ten-framework" ] && [ ! -f "ten_demo/ten-framework/.git" ]; then
    echo "Removing old ten-framework directory..."
    rm -rf ten_demo/ten-framework
fi

# Initialize and update submodules
if [ -f .gitmodules ]; then
    echo "Initializing submodules..."
    git submodule update --init --recursive
fi

# Note: local-demo should be committed in the ten-framework submodule
# If it doesn't exist, we need to create it (this is a workaround)
if [ ! -d "ten_demo/ten-framework/ai_agents/agents/examples/local-demo" ]; then
    echo "WARNING: local-demo directory not found in ten-framework submodule"
    echo "This should be committed to the ten-framework repo or copied manually"
fi

# Verify the directory exists
if [ ! -d "ten_demo/ten-framework/ai_agents/agents/examples/local-demo" ]; then
    echo "ERROR: TEN demo directory not found!"
    echo "Current directory: \$(pwd)"
    echo "Contents of ten_demo/ten-framework/ai_agents/agents/examples/:"
    ls -la ten_demo/ten-framework/ai_agents/agents/examples/ 2>&1 | head -20
    echo "Submodule status:"
    git submodule status 2>&1
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

