"""
Social media platform integration services
Handles posting to different platforms
"""
import requests
from flask import current_app
from app.models import PlatformType, OAuthToken
from app.utils.encryption import EncryptionService
from app.extensions import db
from datetime import datetime, timedelta
import os


def publish_to_platform(post, access_token):
    """
    Publish post to the appropriate platform
    
    Args:
        post: Post model instance
        access_token: Decrypted OAuth access token
    
    Returns:
        dict: {'success': bool, 'post_id': str, 'error': str}
    """
    if post.platform == PlatformType.FACEBOOK:
        return publish_to_facebook(post, access_token)
    elif post.platform == PlatformType.INSTAGRAM:
        return publish_to_instagram(post, access_token)
    elif post.platform == PlatformType.LINKEDIN:
        return publish_to_linkedin(post, access_token)
    elif post.platform == PlatformType.TWITTER:
        return publish_to_twitter(post, access_token)
    else:
        return {'success': False, 'error': 'Unsupported platform'}


def publish_to_facebook(post, access_token):
    """Publish to Facebook Page"""
    try:
        # Get user's Facebook pages
        pages_url = f"https://graph.facebook.com/v18.0/me/accounts"
        pages_response = requests.get(
            pages_url,
            params={'access_token': access_token}
        )
        
        if pages_response.status_code != 200:
            return {'success': False, 'error': 'Failed to get Facebook pages'}
        
        pages = pages_response.json().get('data', [])
        if not pages:
            return {'success': False, 'error': 'No Facebook pages found'}
        
        # Use first page (in production, let user select)
        page_id = pages[0]['id']
        page_access_token = pages[0]['access_token']
        
        # Prepare post data
        post_data = {
            'message': post.content,
            'access_token': page_access_token
        }
        
        # Add media if present
        if post.media_path and post.media_type == 'image':
            media_url = f"{current_app.config['FRONTEND_URL']}/uploads/{post.media_path}"
            post_data['url'] = media_url
            endpoint = f"https://graph.facebook.com/v18.0/{page_id}/photos"
        else:
            endpoint = f"https://graph.facebook.com/v18.0/{page_id}/feed"
        
        # Make API call
        response = requests.post(endpoint, data=post_data)
        
        if response.status_code in [200, 201]:
            result = response.json()
            return {
                'success': True,
                'post_id': result.get('id') or result.get('post_id')
            }
        else:
            return {
                'success': False,
                'error': response.json().get('error', {}).get('message', 'Unknown error')
            }
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def publish_to_instagram(post, access_token):
    """Publish to Instagram (using Facebook Graph API)"""
    try:
        # Instagram requires media
        if not post.media_path:
            return {'success': False, 'error': 'Instagram posts require media'}
        
        # Get Instagram business account
        accounts_url = "https://graph.facebook.com/v18.0/me/accounts"
        accounts_response = requests.get(
            accounts_url,
            params={'access_token': access_token, 'fields': 'instagram_business_account'}
        )
        
        if accounts_response.status_code != 200:
            return {'success': False, 'error': 'Failed to get Instagram account'}
        
        accounts = accounts_response.json().get('data', [])
        ig_account_id = None
        
        for account in accounts:
            if 'instagram_business_account' in account:
                ig_account_id = account['instagram_business_account']['id']
                break
        
        if not ig_account_id:
            return {'success': False, 'error': 'No Instagram business account found'}
        
        # Create media container
        media_url = f"{current_app.config['FRONTEND_URL']}/uploads/{post.media_path}"
        
        container_data = {
            'image_url' if post.media_type == 'image' else 'video_url': media_url,
            'caption': post.content,
            'access_token': access_token
        }
        
        container_response = requests.post(
            f"https://graph.facebook.com/v18.0/{ig_account_id}/media",
            data=container_data
        )
        
        if container_response.status_code not in [200, 201]:
            return {'success': False, 'error': 'Failed to create media container'}
        
        container_id = container_response.json().get('id')
        
        # Publish container
        publish_response = requests.post(
            f"https://graph.facebook.com/v18.0/{ig_account_id}/media_publish",
            data={
                'creation_id': container_id,
                'access_token': access_token
            }
        )
        
        if publish_response.status_code in [200, 201]:
            return {
                'success': True,
                'post_id': publish_response.json().get('id')
            }
        else:
            return {'success': False, 'error': 'Failed to publish media'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def publish_to_linkedin(post, access_token):
    """Publish to LinkedIn"""
    try:
        # Get user profile
        profile_url = "https://api.linkedin.com/v2/me"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        profile_response = requests.get(profile_url, headers=headers)
        
        if profile_response.status_code != 200:
            return {'success': False, 'error': 'Failed to get LinkedIn profile'}
        
        user_id = profile_response.json().get('id')
        author = f"urn:li:person:{user_id}"
        
        # Prepare post data
        share_data = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post.content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # Add media if present
        if post.media_path and post.media_type == 'image':
            # LinkedIn requires uploading images first (complex flow)
            # For simplicity, posting without media
            pass
        
        # Make API call
        response = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            },
            json=share_data
        )
        
        if response.status_code in [200, 201]:
            post_id = response.headers.get('X-RestLi-Id')
            return {'success': True, 'post_id': post_id}
        else:
            return {
                'success': False,
                'error': response.json().get('message', 'Unknown error')
            }
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def publish_to_twitter(post, access_token):
    """Publish to Twitter/X using API v2"""
    try:
        import tweepy
        
        # Create Twitter client
        client = tweepy.Client(bearer_token=access_token)
        
        # Check content length
        if len(post.content) > 280:
            return {'success': False, 'error': 'Tweet exceeds 280 characters'}
        
        # Post tweet (media handling requires additional setup)
        response = client.create_tweet(text=post.content)
        
        if response.data:
            return {
                'success': True,
                'post_id': response.data['id']
            }
        else:
            return {'success': False, 'error': 'Failed to create tweet'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def refresh_oauth_token(oauth_token):
    """
    Refresh an expired OAuth token
    
    Args:
        oauth_token: OAuthToken model instance
    
    Returns:
        str: New access token if successful, None otherwise
    """
    if not oauth_token.refresh_token:
        return None
    
    refresh_token = EncryptionService.decrypt(oauth_token.refresh_token)
    
    try:
        if oauth_token.platform == PlatformType.FACEBOOK:
            # Facebook uses long-lived tokens, no refresh needed
            return None
        
        elif oauth_token.platform == PlatformType.LINKEDIN:
            response = requests.post(
                'https://www.linkedin.com/oauth/v2/accessToken',
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token,
                    'client_id': current_app.config['LINKEDIN_CLIENT_ID'],
                    'client_secret': current_app.config['LINKEDIN_CLIENT_SECRET']
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                new_access_token = data['access_token']
                new_refresh_token = data.get('refresh_token', refresh_token)
                
                # Update token in database
                oauth_token.access_token = EncryptionService.encrypt(new_access_token)
                oauth_token.refresh_token = EncryptionService.encrypt(new_refresh_token)
                oauth_token.expires_at = datetime.utcnow() + timedelta(seconds=data.get('expires_in', 3600))
                db.session.commit()
                
                return new_access_token
        
        # Add other platforms as needed
        
    except Exception as e:
        current_app.logger.error(f"Failed to refresh token: {str(e)}")
        return None
    
    return None
