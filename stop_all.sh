#!/bin/bash

# Stop all services

echo "🛑 Stopping AutoContent Calendar services..."

if [ -f "logs/flask.pid" ]; then
    FLASK_PID=$(cat logs/flask.pid)
    if kill -0 $FLASK_PID 2>/dev/null; then
        kill $FLASK_PID
        echo "✓ Flask stopped (PID: $FLASK_PID)"
    fi
    rm logs/flask.pid
fi

if [ -f "logs/celery_worker.pid" ]; then
    CELERY_WORKER_PID=$(cat logs/celery_worker.pid)
    if kill -0 $CELERY_WORKER_PID 2>/dev/null; then
        kill $CELERY_WORKER_PID
        echo "✓ Celery worker stopped (PID: $CELERY_WORKER_PID)"
    fi
    rm logs/celery_worker.pid
fi

if [ -f "logs/celery_beat.pid" ]; then
    CELERY_BEAT_PID=$(cat logs/celery_beat.pid)
    if kill -0 $CELERY_BEAT_PID 2>/dev/null; then
        kill $CELERY_BEAT_PID
        echo "✓ Celery beat stopped (PID: $CELERY_BEAT_PID)"
    fi
    rm logs/celery_beat.pid
fi

echo ""
echo "✅ All services stopped"
