# Deploying Hydra to TrueNAS Scale

This guide explains how to deploy the Hydra Multi-Agent Job Application Assistant to TrueNAS Scale using Docker.

## Prerequisites

- TrueNAS Scale with Docker/Kubernetes support
- Git access to clone this repository
- API keys for at least one LLM provider (OpenAI, Anthropic, etc.)

## Quick Start

### Option 1: Deploy Pre-built Image (Recommended)

1. **Build and push to Docker Hub** (from your development machine):
   ```bash
   docker build -t yourusername/hydra:latest .
   docker push yourusername/hydra:latest
   ```

2. **On TrueNAS Scale**, create a new Docker container:
   - Image: `yourusername/hydra:latest`
   - Port mappings: `4321:4321` (frontend), `8000:8000` (backend API)
   - Environment variables (see below)

### Option 2: Build Locally on TrueNAS

1. **Clone the repository** to your TrueNAS server:
   ```bash
   git clone https://github.com/your-repo/composable-crew.git
   cd composable-crew
   ```

2. **Copy and configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Build and run**:
   ```bash
   docker compose up -d
   ```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes* | OpenAI API key for GPT models |
| `ANTHROPIC_API_KEY` | Yes* | Anthropic API key for Claude models |
| `GLM_API_KEY` | No | Z.AI GLM API key |
| `CHUTES_API_KEY` | No | Chutes API key (fallback) |
| `TOGETHER_API_KEY` | No | Together AI API key (fallback) |
| `GITHUB_TOKEN` | No | GitHub token for integrations |

*At least one LLM provider key is required.

## TrueNAS Scale App Configuration

### Using TrueNAS Apps (ix-charts)

1. Go to **Apps** → **Available Applications** → **Custom App**
2. Configure:
   - **Application Name**: `hydra`
   - **Image Repository**: `yourusername/hydra`
   - **Image Tag**: `latest`
3. **Port Forwarding**:
   - Container Port: `4321` → Node Port: `4321`
   - Container Port: `8000` → Node Port: `8000`
4. **Environment Variables**: Add your API keys
5. **Storage**: Create a persistent volume for `/app/web/backend/data`

### Accessing the Application

Once deployed, access Hydra at:
```
http://YOUR_TRUENAS_IP:4321
```

## Updating

To update the application:

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Troubleshooting

### Container won't start
- Check logs: `docker logs hydra-app`
- Verify environment variables are set

### API errors
- Ensure your LLM API keys are valid
- Check network connectivity to LLM providers

### Database issues
- The SQLite database is stored in `/app/web/backend/data/jobs.db`
- To reset: `docker exec hydra-app rm /app/web/backend/data/jobs.db`
