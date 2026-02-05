#!/bin/bash

# Run all services in the background
# Logs will be written to logs/ directory

echo "🚀 Starting AutoContent Calendar services..."

# Create logs directory
mkdir -p logs

# Activate virtual environment
source venv/bin/activate

# Start Flask app
echo "▶️  Starting Flask application..."
PORT=${PORT:-5000}
if lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
	echo "⚠️  Port $PORT is in use. Switching to 5001."
	PORT=5001
fi
PORT=$PORT python3 app.py > logs/flask.log 2>&1 &
FLASK_PID=$!
echo "Flask running with PID: $FLASK_PID"

# Wait a moment for Flask to start
sleep 2

# Start Celery worker (use solo pool on macOS to avoid fork crashes)
echo "▶️  Starting Celery worker..."
if [[ "$(uname)" == "Darwin" ]]; then
	celery -A celery_worker.celery worker --loglevel=info --pool=solo --concurrency=1 > logs/celery_worker.log 2>&1 &
else
	celery -A celery_worker.celery worker --loglevel=info > logs/celery_worker.log 2>&1 &
fi
CELERY_WORKER_PID=$!
echo "Celery worker running with PID: $CELERY_WORKER_PID"

# Start Celery beat
echo "▶️  Starting Celery beat..."
celery -A celery_worker.celery beat --loglevel=info > logs/celery_beat.log 2>&1 &
CELERY_BEAT_PID=$!
echo "Celery beat running with PID: $CELERY_BEAT_PID"

# Save PIDs to file for easy stopping
echo $FLASK_PID > logs/flask.pid
echo $CELERY_WORKER_PID > logs/celery_worker.pid
echo $CELERY_BEAT_PID > logs/celery_beat.pid

echo ""
echo "✅ All services started!"
echo ""
echo "🌐 Application: http://localhost:${PORT}"
echo ""
echo "📋 Logs:"
echo "  Flask:         tail -f logs/flask.log"
echo "  Celery Worker: tail -f logs/celery_worker.log"
echo "  Celery Beat:   tail -f logs/celery_beat.log"
echo ""
echo "🛑 To stop all services, run:"
echo "  ./stop_all.sh"
echo ""
