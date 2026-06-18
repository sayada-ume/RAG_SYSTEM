# Deployment Guide

This guide covers deploying HR Assist Pro to various environments.

## Table of Contents
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Production Checklist](#production-checklist)

## Local Development

### Quick Start
```bash
# 1. Clone the repository
git clone https://github.com/sayada-ume/RAG_SYSTEM.git
cd RAG_SYSTEM

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env and add your GOOGLE_GENAI_API_KEY

# 5. Run application
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Docker Deployment

### Prerequisites
- Docker >= 20.10
- Docker Compose >= 2.0

### Build and Run

```bash
# Build Docker image
docker build -t hr-assist-pro:latest .

# Run container
docker run -p 8501:8501 \
  -e GOOGLE_GENAI_API_KEY=your_key_here \
  -e CHROMA_TELEMETRY_DISABLED=True \
  -v ./chroma_db:/app/chroma_db \
  -v ./sample_pdfs:/app/sample_pdfs \
  hr-assist-pro:latest
```

### Using Docker Compose

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Cloud Deployment

### Heroku

```bash
# 1. Install Heroku CLI
# Visit: https://devcenter.heroku.com/articles/heroku-cli

# 2. Login to Heroku
heroku login

# 3. Create Heroku app
heroku create hr-assist-pro

# 4. Set environment variables
heroku config:set GOOGLE_GENAI_API_KEY=your_key_here

# 5. Deploy
git push heroku main

# 6. View app
heroku open
```

### AWS (ECS)

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name hr-assist-pro

# 2. Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account-id.dkr.ecr.us-east-1.amazonaws.com

# 3. Build and push image
docker build -t hr-assist-pro:latest .
docker tag hr-assist-pro:latest your-account-id.dkr.ecr.us-east-1.amazonaws.com/hr-assist-pro:latest
docker push your-account-id.dkr.ecr.us-east-1.amazonaws.com/hr-assist-pro:latest

# 4. Create ECS task definition
# See AWS documentation for detailed steps
```

### Google Cloud Run

```bash
# 1. Authenticate with Google Cloud
gcloud auth login
gcloud config set project your-project-id

# 2. Build and push to Container Registry
gcloud builds submit --tag gcr.io/your-project-id/hr-assist-pro

# 3. Deploy to Cloud Run
gcloud run deploy hr-assist-pro \
  --image gcr.io/your-project-id/hr-assist-pro \
  --platform managed \
  --region us-central1 \
  --set-env-vars GOOGLE_GENAI_API_KEY=your_key_here \
  --allow-unauthenticated
```

## Production Checklist

### Security
- [ ] Change all default passwords
- [ ] Set strong API keys
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up rate limiting
- [ ] Enable authentication if needed
- [ ] Regular security audits
- [ ] Update dependencies regularly

### Performance
- [ ] Configure caching
- [ ] Enable compression
- [ ] Optimize database indices
- [ ] Set up monitoring
- [ ] Configure auto-scaling
- [ ] Load testing completed
- [ ] Response times acceptable

### Operations
- [ ] Backup strategy implemented
- [ ] Logging configured
- [ ] Monitoring alerts set
- [ ] Incident response plan
- [ ] Documentation complete
- [ ] Runbooks created
- [ ] Team trained

### Monitoring & Logging

```bash
# View application logs
docker-compose logs -f hr-assist-pro

# Monitor resource usage
docker stats

# Health check
curl http://localhost:8501/_stcore/health
```

## Environment Variables

Required for production:
```env
GOOGLE_GENAI_API_KEY=your_api_key
CHROMA_TELEMETRY_DISABLED=True
```

Optional:
```env
STREAMLIT_THEME=dark
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///chroma_db
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs container_id

# Verify image
docker images

# Rebuild
docker build -t hr-assist-pro:latest --no-cache .
```

### Port Already in Use
```bash
# Use different port
docker run -p 8502:8501 hr-assist-pro:latest

# Or find and kill process
lsof -i :8501
kill -9 pid
```

### API Connection Issues
- Verify API key is set correctly
- Check network connectivity
- Review API quotas and limits
- Check logs for detailed errors

## Support

For deployment issues:
1. Check the [README](README.md)
2. Review logs for errors
3. Open a GitHub issue with details
4. Contact the development team

---

**Last Updated:** 2026-06-18
