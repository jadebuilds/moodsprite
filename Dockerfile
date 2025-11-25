FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY moodsprite/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY moodsprite/ ./moodsprite/
COPY sera/ ./sera/
COPY moodsprite.proto .

# Generate protobuf files
RUN cd moodsprite && python -m grpc_tools.protoc -I.. --python_out=. --grpc_python_out=. ../moodsprite.proto

# Expose the gRPC port
EXPOSE 50051

# Run the server
CMD ["python", "moodsprite/server.py"]
