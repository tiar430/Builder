#!/bin/bash

# AI Image Generator - Quick Start Script
# This script helps you get started with the AI Image Generator

echo "=========================================="
echo "  🎨 AI Image Generator - Quick Start"
echo "=========================================="
echo ""

# Check if services are running
echo "📊 Checking service status..."
sudo supervisorctl status

echo ""
echo "🔍 Checking API health..."
curl -s http://localhost:8001/api/health | python3 -m json.tool

echo ""
echo "=========================================="
echo "  ✅ Quick Access URLs"
echo "=========================================="
echo ""
echo "  Frontend (Web App):"
echo "  📱 http://localhost:3000"
echo ""
echo "  Backend API:"
echo "  🔧 http://localhost:8001/api/health"
echo "  📖 http://localhost:8001/docs (API Documentation)"
echo ""
echo "=========================================="
echo "  📚 Useful Commands"
echo "=========================================="
echo ""
echo "  View Backend Logs:"
echo "  $ tail -f /var/log/supervisor/backend.out.log"
echo ""
echo "  View Frontend Logs:"
echo "  $ tail -f /var/log/supervisor/frontend.out.log"
echo ""
echo "  Restart Services:"
echo "  $ sudo supervisorctl restart backend"
echo "  $ sudo supervisorctl restart frontend"
echo ""
echo "  Clear Generated Images:"
echo "  $ curl -X DELETE http://localhost:8001/api/clear"
echo ""
echo "=========================================="
echo "  🚀 Ready to Go!"
echo "=========================================="
echo ""
echo "  Open your Samsung Z Fold 4 browser and go to:"
echo "  http://localhost:3000"
echo ""
echo "  Upload an image and start generating! ✨"
echo ""
