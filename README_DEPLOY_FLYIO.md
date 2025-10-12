# Deploying Django (Supabase + Embeddings) to Fly.io

This guide assumes Windows PowerShell.

## 1) Install flyctl
- https://fly.io/docs/hands-on/install-flyctl/
- Login:
```powershell
fly auth login
```

## 2) Configure environment (Fly.io Secrets)
Set your production secrets:
```powershell
# In project root
fly secrets set DJANGO_SECRET_KEY="<your-secret>"
fly secrets set DJANGO_DEBUG="False"
fly secrets set DJANGO_ALLOWED_HOSTS="*"
fly secrets set OPENAI_API_KEY="<your-openai-key>"
# Supabase
fly secrets set DATABASE_URL="<your-supabase-pooling-url>"
fly secrets set DIRECT_URL="<your-supabase-direct-url>"
fly secrets set SUPABASE_PASSWORD="<your-db-password>"
```

Notes:
- DATABASE_URL must be the pooling URL (psql). DIRECT_URL is the direct connection for migrations.
- Password placeholders like [YOUR-PASSWORD] will be substituted in settings.

## 3) Build and deploy
```powershell
# First time
fly launch --no-deploy  # choose existing app name or confirm app name
# Or if app already created
fly deploy
```

## 4) Database migrations & static files
```powershell
fly ssh console -C "python manage.py migrate && python manage.py collectstatic --noinput"
```

## 5) Scale
```powershell
fly scale count 1
fly scale memory 512
```

## 6) Logs / troubleshooting
```powershell
fly logs
```

## 7) Rollback
Redeploy previous image if needed:
```powershell
fly releases
fly deploy --image <previous_image>
```

## 8) Health check
- Health check path: `/` (config in fly.toml)

## 9) CORS/CSRF/Host
- We set `DJANGO_ALLOWED_HOSTS="*"`. Set a specific hostname later for tighter security.

