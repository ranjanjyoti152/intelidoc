#!/bin/bash
# InteliDoc RAG Pipeline - Startup Script

set -e

echo "🚀 Starting InteliDoc RAG Pipeline..."

# Check for .env file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
fi

# Create uploads directory
mkdir -p uploads

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🐳 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check if Ollama has the model
echo "🤖 Checking LLM model..."
MODEL=${LLM_MODEL:-llama3.2}
if ! docker exec intelidoc-ollama ollama list 2>/dev/null | grep -q "$MODEL"; then
    echo "📥 Pulling $MODEL model (this may take a while)..."
    docker exec intelidoc-ollama ollama pull "$MODEL"
fi

# Health check
echo "🏥 Checking service health..."
sleep 5
curl -s http://localhost:8000/health | python3 -m json.tool || echo "API not ready yet, please wait..."

echo ""
echo "✅ InteliDoc RAG Pipeline is starting!"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🏥 Health Check:      http://localhost:8000/health"
echo ""
echo "📋 View logs: docker-compose logs -f"
echo "🛑 Stop:      docker-compose down"
