#!/bin/bash
# deploy.sh - Standard Update Script for Linode

echo "--- Starting Update Process ---"

# 1. Update Codebase
echo "[1/5] Pulling latest code..."
git pull origin main

# 2. Update Dependencies
echo "[2/5] Updating dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
fi
pip install -r requirements.txt

# 3. Database Migrations
echo "[3/5] Applying migrations..."
python manage.py makemigrations
python manage.py migrate

# 4. Static Files
echo "[4/5] Collecting static files..."
python manage.py collectstatic --noinput

# 5. Restart Application
echo "[5/5] Restarting Gunicorn..."
sudo systemctl restart gunicorn

echo "--- Update Complete! ---"
