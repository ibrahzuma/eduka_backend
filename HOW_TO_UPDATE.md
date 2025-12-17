# Deployment Update Guide

Follow these steps to update your live server with the latest changes.

## 1. Connect to your Server
Open your terminal or command prompt and SSH into your server:
```bash
ssh root@<your-server-ip>
# Or if you use a specific user/key:
# ssh -i /path/to/key.pem user@<your-server-ip>
```

## 2. Navigate to the Project Directory
Change into the directory where your project code lives. This is likely:
```bash
cd /var/www/eduka_backend
# OR
cd ~/eduka_backend
```
*(Adjust the path if your project is located elsewhere)*

## 3. Pull the Latest Changes
Fetch the recent commits from GitHub:
```bash
git pull origin main
```
*If you have local changes on the server that conflict, you might need to stash them first (`git stash`).*

## 4. Run Maintenance Commands
Since we updated templates (static files might be involved) and potentially models:

```bash
# Activate your virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Collect static files (Important for CSS/JS changes)
python manage.py collectstatic --noinput
```

## 5. Restart the Application Server
Restart Gunicorn (or your specific service) to load the new code.
```bash
sudo systemctl restart gunicorn
```
*(If you are using Supervisor or another manager, restart that instead, e.g., `sudo supervisorctl restart all`)*

Your server is now updated!
