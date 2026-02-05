from flask import Blueprint, request, jsonify, redirect, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import OAuthToken, PlatformType, User
from app.extensions import db
from app.utils.encryption import EncryptionService
from app.utils.decorators import active_user_required, get_current_user_id
from app.utils.audit import log_action
from datetime import datetime, timedelta
import requests
from urllib.parse import urlencode
from itsdangerous import URLSafeSerializer, BadSignature
import base64
import hashlib
import secrets

bp = Blueprint('oauth', __name__, url_prefix='/api/oauth')


def _get_oauth_serializer():
    return URLSafeSerializer(current_app.config['SECRET_KEY'], salt='oauth-state')


def _build_state(user_id, platform, code_verifier=None):
    payload = {
        'user_id': user_id,
        'platform': platform
    }
    if code_verifier:
        payload['code_verifier'] = code_verifier
    return _get_oauth_serializer().dumps(payload)


def _parse_state(state):
    try:
        return _get_oauth_serializer().loads(state)
    except BadSignature:
        return None


def _require_config(*keys):
    missing = [key for key in keys if not current_app.config.get(key)]
    if missing:
        return f"Missing OAuth configuration: {', '.join(missing)}"
    return None


def _generate_pkce_pair():
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge


@bp.route('/<platform>/connect', methods=['GET'])
@jwt_required()
@active_user_required
def connect_platform(platform):
    """Initiate OAuth flow for a platform"""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401
    
    try:
        platform_enum = PlatformType(platform)
    except ValueError:
        return jsonify({'error': 'Invalid platform'}), 400
    
    # Build authorization URL based on platform
    if platform_enum == PlatformType.FACEBOOK:
        config_error = _require_config('FACEBOOK_CLIENT_ID', 'FACEBOOK_CLIENT_SECRET', 'FACEBOOK_REDIRECT_URI')
        if config_error:
            return jsonify({'error': config_error}), 400
        auth_url = 'https://www.facebook.com/v18.0/dialog/oauth'
        params = {
            'client_id': current_app.config['FACEBOOK_CLIENT_ID'],
            'redirect_uri': current_app.config['FACEBOOK_REDIRECT_URI'],
            'scope': 'pages_manage_posts,pages_read_engagement',
            'state': _build_state(user_id, platform)
        }
    elif platform_enum == PlatformType.INSTAGRAM:
        config_error = _require_config('INSTAGRAM_CLIENT_ID', 'INSTAGRAM_CLIENT_SECRET', 'INSTAGRAM_REDIRECT_URI')
        if config_error:
            return jsonify({'error': config_error}), 400
        auth_url = 'https://api.instagram.com/oauth/authorize'
        params = {
            'client_id': current_app.config['INSTAGRAM_CLIENT_ID'],
            'redirect_uri': current_app.config['INSTAGRAM_REDIRECT_URI'],
            'scope': 'user_profile,user_media',
            'response_type': 'code',
            'state': _build_state(user_id, platform)
        }
    elif platform_enum == PlatformType.LINKEDIN:
        config_error = _require_config('LINKEDIN_CLIENT_ID', 'LINKEDIN_CLIENT_SECRET', 'LINKEDIN_REDIRECT_URI')
        if config_error:
            return jsonify({'error': config_error}), 400
        auth_url = 'https://www.linkedin.com/oauth/v2/authorization'
        params = {
            'client_id': current_app.config['LINKEDIN_CLIENT_ID'],
            'redirect_uri': current_app.config['LINKEDIN_REDIRECT_URI'],
            'scope': 'w_member_social',
            'response_type': 'code',
            'state': _build_state(user_id, platform)
        }
    elif platform_enum == PlatformType.TWITTER:
        config_error = _require_config('TWITTER_CLIENT_ID', 'TWITTER_REDIRECT_URI')
        if config_error:
            return jsonify({'error': config_error}), 400
        code_verifier, code_challenge = _generate_pkce_pair()
        auth_url = 'https://twitter.com/i/oauth2/authorize'
        params = {
            'client_id': current_app.config['TWITTER_CLIENT_ID'],
            'redirect_uri': current_app.config['TWITTER_REDIRECT_URI'],
            'scope': 'tweet.read tweet.write users.read',
            'response_type': 'code',
            'state': _build_state(user_id, platform, code_verifier),
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
    else:
        return jsonify({'error': 'Platform not supported yet'}), 400
    
    redirect_url = f"{auth_url}?{urlencode(params)}"
    
    return jsonify({
        'authorization_url': redirect_url
    }), 200


@bp.route('/<platform>/callback', methods=['GET'])
def oauth_callback(platform):
    """Handle OAuth callback from platform"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return jsonify({'error': f'OAuth error: {error}'}), 400
    
    if not code or not state:
        return jsonify({'error': 'Missing authorization code or state'}), 400
    
    # Parse state to get user_id and platform
    state_data = _parse_state(state)
    if not state_data:
        return jsonify({'error': 'Invalid state parameter'}), 400
    try:
        user_id = int(state_data.get('user_id'))
        platform_name = state_data.get('platform')
        platform_enum = PlatformType(platform_name)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid state parameter'}), 400
    
    # Exchange code for access token
    token_data = exchange_code_for_token(platform_enum, code, state_data)
    
    if not token_data:
        return jsonify({'error': 'Failed to exchange code for token'}), 400
    
    # Save or update token
    oauth_token = OAuthToken.query.filter_by(
        user_id=user_id,
        platform=platform_enum
    ).first()
    
    if oauth_token:
        # Update existing token
        oauth_token.access_token = EncryptionService.encrypt(token_data['access_token'])
        oauth_token.refresh_token = EncryptionService.encrypt(token_data.get('refresh_token', ''))
        oauth_token.token_type = token_data.get('token_type')
        oauth_token.expires_at = token_data.get('expires_at')
        oauth_token.scope = token_data.get('scope')
        oauth_token.is_active = True
    else:
        # Create new token
        oauth_token = OAuthToken(
            user_id=user_id,
            platform=platform_enum,
            access_token=EncryptionService.encrypt(token_data['access_token']),
            refresh_token=EncryptionService.encrypt(token_data.get('refresh_token', '')),
            token_type=token_data.get('token_type'),
            expires_at=token_data.get('expires_at'),
            scope=token_data.get('scope'),
            is_active=True
        )
        db.session.add(oauth_token)
    
    db.session.commit()
    
    log_action(user_id, 'oauth_connect', 'success', platform=platform_enum)
    
    # Redirect to frontend with success message
    frontend_url = current_app.config.get('FRONTEND_URL') or request.host_url.rstrip('/')
    return redirect(f"{frontend_url.rstrip('/')}/settings.html?oauth_success=true&platform={platform}")


def exchange_code_for_token(platform, code, state_data=None):
    """Exchange authorization code for access token"""
    token_data = None
    
    try:
        if platform == PlatformType.FACEBOOK:
            response = requests.post(
                'https://graph.facebook.com/v18.0/oauth/access_token',
                data={
                    'client_id': current_app.config['FACEBOOK_CLIENT_ID'],
                    'client_secret': current_app.config['FACEBOOK_CLIENT_SECRET'],
                    'redirect_uri': current_app.config['FACEBOOK_REDIRECT_URI'],
                    'code': code
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                expires_in = data.get('expires_in', 3600)
                token_data = {
                    'access_token': data['access_token'],
                    'token_type': data.get('token_type', 'Bearer'),
                    'expires_at': datetime.utcnow() + timedelta(seconds=expires_in),
                    'scope': None
                }
        
        elif platform == PlatformType.LINKEDIN:
            response = requests.post(
                'https://www.linkedin.com/oauth/v2/accessToken',
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'client_id': current_app.config['LINKEDIN_CLIENT_ID'],
                    'client_secret': current_app.config['LINKEDIN_CLIENT_SECRET'],
                    'redirect_uri': current_app.config['LINKEDIN_REDIRECT_URI']
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                expires_in = data.get('expires_in', 3600)
                token_data = {
                    'access_token': data['access_token'],
                    'refresh_token': data.get('refresh_token'),
                    'token_type': data.get('token_type', 'Bearer'),
                    'expires_at': datetime.utcnow() + timedelta(seconds=expires_in),
                    'scope': data.get('scope')
                }
        
        elif platform == PlatformType.INSTAGRAM:
            response = requests.post(
                'https://api.instagram.com/oauth/access_token',
                data={
                    'client_id': current_app.config['INSTAGRAM_CLIENT_ID'],
                    'client_secret': current_app.config['INSTAGRAM_CLIENT_SECRET'],
                    'grant_type': 'authorization_code',
                    'redirect_uri': current_app.config['INSTAGRAM_REDIRECT_URI'],
                    'code': code
                }
            )

            if response.status_code == 200:
                data = response.json()
                expires_in = data.get('expires_in', 3600)
                token_data = {
                    'access_token': data['access_token'],
                    'token_type': 'Bearer',
                    'expires_at': datetime.utcnow() + timedelta(seconds=expires_in),
                    'scope': None
                }

        elif platform == PlatformType.TWITTER:
            code_verifier = (state_data or {}).get('code_verifier')
            if not code_verifier:
                return None

            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': current_app.config['TWITTER_CLIENT_ID'],
                'redirect_uri': current_app.config['TWITTER_REDIRECT_URI'],
                'code_verifier': code_verifier
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            auth = None
            if current_app.config.get('TWITTER_CLIENT_SECRET'):
                auth = (current_app.config['TWITTER_CLIENT_ID'], current_app.config['TWITTER_CLIENT_SECRET'])

            response = requests.post(
                'https://api.twitter.com/2/oauth2/token',
                data=data,
                headers=headers,
                auth=auth
            )

            if response.status_code == 200:
                data = response.json()
                expires_in = data.get('expires_in', 7200)
                token_data = {
                    'access_token': data['access_token'],
                    'refresh_token': data.get('refresh_token'),
                    'token_type': data.get('token_type', 'Bearer'),
                    'expires_at': datetime.utcnow() + timedelta(seconds=expires_in),
                    'scope': data.get('scope')
                }
        
    except Exception as e:
        current_app.logger.error(f"Error exchanging code for token: {str(e)}")
        return None
    
    return token_data


@bp.route('/tokens', methods=['GET'])
@jwt_required()
@active_user_required
def get_oauth_tokens():
    """Get all OAuth tokens for current user"""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401
    
    tokens = OAuthToken.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        'tokens': [token.to_dict(include_tokens=False) for token in tokens]
    }), 200


@bp.route('/tokens/<int:token_id>', methods=['DELETE'])
@jwt_required()
@active_user_required
def disconnect_platform(token_id):
    """Disconnect a platform (delete OAuth token)"""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401
    
    token = OAuthToken.query.filter_by(id=token_id, user_id=user_id).first()
    
    if not token:
        return jsonify({'error': 'Token not found'}), 404
    
    platform = token.platform
    db.session.delete(token)
    db.session.commit()
    
    log_action(user_id, 'oauth_disconnect', 'success', platform=platform)
    
    return jsonify({'message': 'Platform disconnected successfully'}), 200
