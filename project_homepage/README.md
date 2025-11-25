# Moodsprite - AI Character Interface

A Next.js application that bridges between a Python gRPC backend and a React frontend, providing real-time AI character interactions with mood-based keyframe animations.

## Architecture

```
Frontend (React) <--> Next.js Server <--> Python gRPC Server
                         |
                         v
                    PostgreSQL DB
```

## Features

- **Real-time Character Streaming**: Live keyframe animations based on AI mood cues
- **Clerk Authentication**: Secure user authentication and session management
- **Comprehensive Logging**: Detailed interaction tracking with Prisma and PostgreSQL
- **Responsive UI**: Modern, mobile-friendly interface with Tailwind CSS
- **Docker Support**: Full containerization with Docker Compose

## Prerequisites

- Node.js 18+ 
- Docker and Docker Compose
- Clerk account (for authentication)

## Quick Start

### 1. Environment Setup

Create a `.env.local` file in the project root:

```bash
# Database
DATABASE_URL="postgresql://moodsprite:moodsprite123@localhost:5432/moodsprite"

# Clerk Authentication (get these from your Clerk dashboard)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="pk_test_..."
CLERK_SECRET_KEY="sk_test_..."

# gRPC Server
GRPC_SERVER_URL="localhost:50051"
```

### 2. Generate Protobuf Files

```bash
# From the moodsprite root directory
./build_proto.sh
```

This generates both Python and TypeScript gRPC client code.

### 3. Start with Docker Compose

```bash
# From the moodsprite root directory
docker-compose up --build
```

This will start:
- PostgreSQL database on port 5432
- Python gRPC server on port 50051
- Next.js application on port 3000

### 4. Run Database Migrations

```bash
# In a new terminal, from project_homepage directory
cd project_homepage
npx prisma migrate dev
```

### 5. Access the Application

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Development

### Local Development (without Docker)

1. **Start PostgreSQL** (using Docker or local installation):
   ```bash
   docker run --name moodsprite-postgres -e POSTGRES_DB=moodsprite -e POSTGRES_USER=moodsprite -e POSTGRES_PASSWORD=moodsprite123 -p 5432:5432 -d postgres:15
   ```

2. **Start Python gRPC Server**:
   ```bash
   cd moodsprite
   source .venv/bin/activate
   python server.py
   ```

3. **Start Next.js Development Server**:
   ```bash
   cd project_homepage
   npm run dev
   ```

### Database Management

```bash
# View database in Prisma Studio
npx prisma studio

# Reset database
npx prisma migrate reset

# Generate Prisma client after schema changes
npx prisma generate
```

## API Endpoints

### REST Endpoints

- `GET /api/character` - Fetch character data and keyframes
- `GET /api/history` - Fetch character history (with optional filtering)

### Streaming Endpoint

- `GET /api/stream` - Server-Sent Events stream for live keyframe cues

## Project Structure

```
project_homepage/
├── src/
│   ├── app/
│   │   ├── (auth)/              # Authentication pages
│   │   ├── (dashboard)/         # Protected dashboard pages
│   │   │   ├── sprite/          # Main sprite viewer
│   │   │   └── settings/        # Settings page
│   │   └── api/                 # API routes
│   │       ├── character/       # Character data endpoint
│   │       ├── history/         # Character history endpoint
│   │       └── stream/          # Live streaming endpoint
│   ├── components/              # React components
│   │   ├── menu-bar.tsx         # Top navigation
│   │   └── loading-modal.tsx    # Loading states
│   └── lib/                     # Utilities and generated code
│       ├── grpc-client.ts       # gRPC client wrapper
│       ├── logging.ts           # Database logging utilities
│       └── generated/           # Generated protobuf code
├── prisma/
│   └── schema.prisma            # Database schema
└── middleware.ts                # Clerk authentication middleware
```

## Database Schema

The application uses two main tables:

- **InteractionLog**: Comprehensive logging of all user interactions
- **Session**: User session tracking with keyframe serving metrics

## Authentication

The application uses Clerk for authentication. Configure your Clerk application:

1. Create a new application in [Clerk Dashboard](https://dashboard.clerk.com)
2. Add your domain to allowed origins
3. Copy the publishable key and secret key to your `.env.local`

## Troubleshooting

### Common Issues

1. **gRPC Connection Errors**: Ensure the Python server is running on port 50051
2. **Database Connection Issues**: Check PostgreSQL is running and credentials are correct
3. **Authentication Errors**: Verify Clerk keys are correctly set in environment variables
4. **Protobuf Generation Errors**: Run `./build_proto.sh` from the moodsprite root directory

### Logs

Check Docker logs for debugging:
```bash
docker-compose logs -f nextjs-app
docker-compose logs -f grpc-server
docker-compose logs -f postgres
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Moodsprite AI character system.