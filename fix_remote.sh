#!/bin/bash
echo "--- REMOTE FIX SCRIPT ---"
# Try to find directory, or stay in current
if [ -d "/var/www/eduka_backend" ]; then
    cd /var/www/eduka_backend
fi

echo "[1] Pulling latest code..."
git pull origin main

echo "[2] Installing Dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
fi
pip install -r requirements.txt

echo "[3] Collecting Static Files..."
# Force collectstatic
python manage.py collectstatic --noinput --clear

echo "[4] Applying Migrations..."
python manage.py migrate

echo "[5] Restarting Gunicorn..."
# Check if systemctl exists
if command -v systemctl &> /dev/null; then
    sudo systemctl restart gunicorn
else
    echo "WARNING: systemctl not found. Please restart Gunicorn manually."
fi

echo "--- FIX COMPLETE. Check site now. ---"
