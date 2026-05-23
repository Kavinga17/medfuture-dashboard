# Medfuture Operations Dashboard

Live dashboard connecting to 3 APIs — auto refreshes every 1 hour.

## APIs
- Job Orders
- Client Prospects  
- Candidates

## Deploy to Render (free)

1. Push this folder to GitHub
2. Go to render.com → New Web Service
3. Connect your GitHub repo
4. Settings:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:server --bind 0.0.0.0:$PORT`
5. Click Deploy

## Run locally

```bash
pip install -r requirements.txt
python app.py
```
Open browser: http://localhost:8050
