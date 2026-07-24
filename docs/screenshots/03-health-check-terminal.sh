┌─────────────────────────────────────────────────────────────┐
│                    Enterprise AI Support Agent               │
│                      Health Check Response                   │
└─────────────────────────────────────────────────────────────┘

$ curl http://localhost:8000/health

{
  "status": "healthy",
  "service": "enterprise-ai-support-agent",
  "version": "1.0.0",
  "components": {
    "api": "healthy",
    "llm": "healthy",
    "rag": "healthy",
    "database": "healthy"
  }
}

✓ All systems operational