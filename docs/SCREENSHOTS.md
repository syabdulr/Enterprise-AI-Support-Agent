# Screenshots & Demos Guide

This document describes the screenshots and demo content for the Enterprise AI Support Agent project.

## Screenshots Overview

### Required Screenshots

1. **API Documentation - Swagger UI**
   - URL: http://localhost:8000/docs
   - Shows interactive API documentation
   - Demonstrates OpenAPI specification

2. **API Documentation - ReDoc**
   - URL: http://localhost:8000/redoc
   - Shows alternative API documentation
   - Demonstrates structured API reference

3. **Health Check Endpoint**
   - URL: http://localhost:8000/health
   - Shows system health status
   - Demonstrates monitoring capabilities

4. **Incident Submission**
   - POST request to `/incident` endpoint
   - Shows request/response JSON
   - Demonstrates incident processing

5. **RAG Query**
   - POST request to `/rag/query` endpoint
   - Shows knowledge base query
   - Demonstrates semantic search

6. **Docker Compose Running**
   - Terminal showing `docker-compose ps`
   - Shows all services running
   - Demonstrates containerization

7. **GitHub Actions CI/CD**
   - GitHub Actions workflow run
   - Shows green checkmarks
   - Demonstrates automated testing

8. **Test Results**
   - Pytest output showing passing tests
   - Shows coverage report
   - Demonstrates testing suite

9. **Architecture Diagram**
   - Mermaid diagram from README.md
   - Shows system architecture
   - Demonstrates visual documentation

10. **Project Structure**
    - File tree showing project organization
    - Demonstrates clean architecture

## How to Take Screenshots

### Using Terminal Commands

```bash
# Start API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Access documentation
open http://localhost:8000/docs  # Mac
xdg-open http://localhost:8000/docs  # Linux

# Take screenshot (Mac)
Cmd + Shift + 4

# Take screenshot (Linux)
gnome-screenshot --area
```

### Using Browser DevTools

```bash
# Open browser with DevTools
google-chrome --auto-open-devtools-for-tabs http://localhost:8000/docs

# Take full page screenshot
# Chrome DevTools -> Command Menu -> Capture full size screenshot
```

## Demo Video Script

### Video Structure (5-10 minutes)

1. **Introduction (30s)**
   - Project title and overview
   - Tech stack preview
   - What you'll see

2. **Architecture Overview (1m)**
   - Show README.md
   - Explain system architecture
   - Show Mermaid diagrams

3. **API Demo (2m)**
   - Start API server
   - Show Swagger UI
   - Submit incident request
   - Show response

4. **RAG Demo (2m)**
   - Query knowledge base
   - Show retrieved documents
   - Explain semantic search

5. **Docker Demo (1m)**
   - Show docker-compose.yml
   - Start services with Docker
   - Show running containers

6. **CI/CD Demo (1m)**
   - Show GitHub Actions workflow
   - Explain pipeline stages
   - Show test results

7. **Testing Demo (1m)**
   - Run pytest
   - Show coverage report
   - Explain test categories

8. **Conclusion (30s)**
   - Summary of features
   - Call to action
   - Contact information

### Demo Commands

```bash
# Start API
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Test API
curl http://localhost:8000/health

# Submit incident
curl -X POST http://localhost:8000/incident \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "DEMO-001",
    "description": "Network timeout when connecting to database",
    "severity": "High"
  }'

# Query RAG
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "database connection timeout",
    "n_results": 3
  }'

# Run tests
pytest tests/ -v --cov=src

# Start Docker
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## Screenshot Locations

```
docs/screenshots/
├── 01-swagger-ui.png
├── 02-redoc.png
├── 03-health-check.png
├── 04-incident-submission.png
├── 05-rag-query.png
├── 06-docker-compose.png
├── 07-github-actions.png
├── 08-test-results.png
├── 09-architecture-diagram.png
└── 10-project-structure.png
```

## Demo Video Location

```
docs/demos/
└── demo-presentation.mp4
```

## Adding Screenshots to README

### Using Markdown

```markdown
## Screenshots

### API Documentation - Swagger UI

![Swagger UI](docs/screenshots/01-swagger-ui.png)

### Health Check

![Health Check](docs/screenshots/03-health-check.png)

### Docker Services

![Docker Compose](docs/screenshots/06-docker-compose.png)
```

### Using HTML (for GitHub)

```html
<p align="center">
  <img src="docs/screenshots/01-swagger-ui.png" width="800" />
</p>
```

## Creating Demo Video

### Using OBS Studio

```bash
# Install OBS Studio
sudo apt install obs-studio  # Linux
brew install --cask obs       # Mac

# Configure recording
- Scene: Display capture
- Audio: Mic audio
- Resolution: 1920x1080
- FPS: 30
- Format: MP4
- Encoder: H.264

# Record
1. Start recording
2. Follow demo script
3. Stop recording
4. Export video
```

### Using Terminal Recording

```bash
# Install asciinema
brew install asciinema  # Mac
sudo apt install asciinema  # Linux

# Record terminal session
asciinema rec docs/demos/terminal-demo.cast

# Playback
asciinema play docs/demos/terminal-demo.cast

# Export to GIF
asciinema cat docs/demos/terminal-demo.cast > demo.gif
```

## Optimization Tips

### Image Optimization

```bash
# Compress PNG images
optipng -o7 docs/screenshots/*.png

# Resize images
convert docs/screenshots/*.png -resize 800x600 docs/screenshots/*.png

# Convert to WebP
for file in docs/screenshots/*.png; do
  cwebp -q 80 "$file" -o "${file%.png}.webp"
done
```

### Video Optimization

```bash
# Compress video using FFmpeg
ffmpeg -i demo.mp4 \
  -vcodec libx264 \
  -crf 28 \
  -preset slow \
  -vf scale=1280:-2 \
  demo-compressed.mp4

# Extract thumbnail
ffmpeg -i demo.mp4 \
  -ss 00:00:30 \
  -vframes 1 \
  thumbnail.png
```

## README Integration

### Adding Screenshots Section

```markdown
## 📸 Screenshots

### API Documentation

![Swagger UI](docs/screenshots/01-swagger-ui.png)

Interactive API documentation with Swagger UI showing all endpoints.

### System Health

![Health Check](docs/screenshots/03-health-check.png)

Comprehensive health check showing all component statuses.

### Running Services

![Docker Compose](docs/screenshots/06-docker-compose.png)

All services running via Docker Compose.

## 🎬 Demo Video

[![Demo Video](docs/screenshots/09-architecture-diagram.png)](docs/demos/demo-presentation.mp4)

Click image to watch the demo video (5 min)
```

## GitHub Profile Integration

### Adding Screenshots to Profile README

```markdown
## Projects

### Enterprise AI Support Agent

![API Demo](docs/screenshots/01-swagger-ui.png)

**Tech Stack:** LangChain, LangGraph, ChromaDB, Azure OpenAI, FastAPI

[📦 View Project](https://github.com/syabdulr/Enterprise-AI-Support-Agent)
```

## Final Checklist

- [ ] All 10 screenshots taken
- [ ] Screenshots are properly named
- [ ] Images are compressed and optimized
- [ ] Demo video recorded (5-10 min)
- [ ] Video is compressed and has thumbnail
- [ ] Screenshots added to README.md
- [ ] Demo video linked in README.md
- [ ] Screenshots added to GitHub profile
- [ ] All visual content is high quality
- [ ] File sizes are reasonable (< 500KB per image)

---

**Document Version:** 1.0.0  
**Last Updated:** July 24, 2026  
**Maintainer:** Abdul Syed