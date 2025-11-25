#!/bin/bash

# Generate Python and TypeScript code from protobuf schema
# Target the moodsprite package directory for Python and project_homepage for TypeScript

# Generate Python files
cd moodsprite/server
source ../.venv/bin/activate
python -m grpc_tools.protoc -I../.. --python_out=. --grpc_python_out=. ../../moodsprite.proto

echo "Generated Python files from moodsprite.proto in moodsprite/server package"
# Generate TypeScript files
cd ../project_homepage
mkdir -p lib/generated

# Install grpc-tools if not already installed
if ! command -v grpc_tools_node_protoc &> /dev/null; then
    echo "Installing grpc-tools..."
    npm install -g grpc-tools
fi

# Generate TypeScript files
grpc_tools_node_protoc \
  --plugin=protoc-gen-grpc=./node_modules/.bin/grpc_tools_node_protoc_plugin \
  --js_out=import_style=commonjs,binary:./lib/generated \
  --grpc_out=grpc_js:./lib/generated \
  --plugin=protoc-gen-ts=./node_modules/.bin/protoc-gen-ts \
  --ts_out=grpc_js:./lib/generated \
  -I.. \
  ../moodsprite.proto

echo "Generated TypeScript files from moodsprite.proto in project_homepage/lib/generated"

