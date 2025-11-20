#!/bin/bash
# SafeOrders Application Startup Script

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment
source venv/bin/activate

# Start application with gunicorn
echo "Starting SafeOrders in $APP_ENV environment..."
exec gunicorn -b 0.0.0.0:8080 \
    --workers 2 \
    --timeout 60 \
    --access-logfile /var/log/safeorders-access.log \
    --error-logfile /var/log/safeorders-error.log \
    --log-level info \
    app:app
