#!/bin/bash

set -e  # Выход при ошибке

APP_DIR="/home/alex/catty-reminders-app"
LOG_FILE="/home/alex/deploy.log"

echo "=== DEPLOYMENT STARTED ===" > $LOG_FILE
echo "Time: $(date)" >> $LOG_FILE
echo "User: $(whoami)" >> $LOG_FILE
echo "PWD: $(pwd)" >> $LOG_FILE

cd "$APP_DIR" || { echo "❌ Cannot cd to $APP_DIR" | tee -a $LOG_FILE; exit 1; }

echo "📦 Pulling latest code..." | tee -a $LOG_FILE
git pull origin master

echo "📦 Installing dependencies..." | tee -a $LOG_FILE
pip3 install --break-system-packages -r requirements.txt

echo "🔧 Restarting service..." | tee -a $LOG_FILE
sudo systemctl restart catty-reminders

echo "✅ Checking service status..." | tee -a $LOG_FILE
sudo systemctl status catty-reminders --no-pager >> $LOG_FILE

echo "🎉 DEPLOYMENT COMPLETED: $(date)" >> $LOG_FILE
echo "✅ Deployment completed successfully!" | tee -a $LOG_FILE
