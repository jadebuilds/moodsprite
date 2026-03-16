FROM node:22-bookworm-slim

ARG AGENT_NAME

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl jq sudo ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Create agent user with sudo
RUN useradd -m -s /bin/bash agent \
  && echo 'agent ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers.d/agent

WORKDIR /app

# Install SDK dependencies and build
COPY sdk/package.json sdk/tsconfig.json ./sdk/
COPY sdk/src/ ./sdk/src/
COPY package.json ./
RUN npm install && npm run build

# Install tsx for running agent TypeScript directly
RUN npm install -g tsx

# Copy agent code
COPY agents/tsconfig.json ./agents/
COPY agents/${AGENT_NAME}/ ./agents/${AGENT_NAME}/

# Writable workspace for agent self-modification
RUN mkdir -p /workspace && chown agent:agent /workspace
VOLUME /workspace

USER agent

ENV AGENT_NAME=${AGENT_NAME}
CMD sh -c "node --import tsx agents/${AGENT_NAME}/index.ts"
