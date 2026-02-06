"""
Contact / Demo booking routes
"""
import re
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.extensions import db, limiter
from app.models import DemoBooking

contact_bp = Blueprint('contact', __name__)

EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


@contact_bp.route('/api/contact/book-demo', methods=['POST'])
@limiter.limit("5 per minute")
def book_demo():
    """Book a demo or sales meeting – no auth required."""
    data = request.get_json(silent=True) or {}

    email = (data.get('email') or '').strip().lower()
    preferred_date = (data.get('preferred_date') or '').strip()
    preferred_time = (data.get('preferred_time') or '').strip()

    # --- validation ---
    errors = []
    if not email or not EMAIL_RE.match(email):
        errors.append('A valid email address is required.')
    if not preferred_date:
        errors.append('Preferred date is required.')
    else:
        try:
            d = datetime.strptime(preferred_date, '%Y-%m-%d')
            if d.date() < datetime.utcnow().date():
                errors.append('Preferred date must be today or later.')
        except ValueError:
            errors.append('Date must be in YYYY-MM-DD format.')
    if not preferred_time:
        errors.append('Preferred time is required.')
    else:
        try:
            datetime.strptime(preferred_time, '%H:%M')
        except ValueError:
            errors.append('Time must be in HH:MM format.')

    if errors:
        return jsonify({'error': '; '.join(errors)}), 400

    name = (data.get('name') or '').strip() or None
    message = (data.get('message') or '').strip() or None
    timezone = (data.get('timezone') or 'UTC').strip()
    booking_type = data.get('booking_type', 'demo')
    if booking_type not in ('demo', 'sales'):
        booking_type = 'demo'

    booking = DemoBooking(
        email=email,
        name=name,
        preferred_date=preferred_date,
        preferred_time=preferred_time,
        timezone=timezone,
        message=message,
        booking_type=booking_type,
        status='pending',
    )
    db.session.add(booking)
    db.session.commit()

    return jsonify({
        'message': 'Your demo request has been received! We\'ll contact you shortly.',
        'booking': booking.to_dict()
    }), 201
