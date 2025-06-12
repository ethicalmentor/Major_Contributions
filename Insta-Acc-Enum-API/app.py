import os
import time
import concurrent.futures
from flask import Flask, jsonify
from instagrapi import Client
from cachetools import cached, TTLCache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")
CACHE_TTL = int(os.getenv("CACHE_TTL", 1800))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 5))

# Validate credentials
if not INSTA_USERNAME or not INSTA_PASSWORD:
    raise ValueError("Instagram credentials missing in .env file")

cache = TTLCache(maxsize=100, ttl=CACHE_TTL)

# Initialize Instagram client
def init_client():
    """Create authenticated Instagram client"""
    cl = Client()
    cl.login(INSTA_USERNAME, INSTA_PASSWORD)
    return cl

# Helper function to convert URLs to strings
def url_to_str(url):
    return str(url) if url else None

# ======================
# DATA PROCESSING FUNCTIONS
# ======================

def process_reel(reel_media):
    return {
        "id": reel_media.id,
        "unique_identifier": reel_media.code,
        "reel_url": f"https://instagram.com/reel/{reel_media.code}",
        "video_url": url_to_str(reel_media.video_url),
        "thumbnail_url": url_to_str(reel_media.thumbnail_url),
        "caption": reel_media.caption_text or "",
        "posted_at_utc": reel_media.taken_at.isoformat() + "Z",
        "views": reel_media.view_count,
        "likes": reel_media.like_count,
        "comments": reel_media.comment_count
    }

def process_post(post):
    return {
        "id": post.id,
        "post_url": f"https://instagram.com/p/{post.code}",
        "type": "video" if post.is_video else "image",
        "media_url": url_to_str(post.video_url) if post.is_video else url_to_str(post.thumbnail_url),
        "caption": post.caption_text or "",
        "posted_at_utc": post.taken_at.isoformat() + "Z",
        "likes": post.like_count,
        "comments": post.comment_count
    }

def process_user(user):
    return {
        "user_id": user.pk,
        "username": user.username,
        "full_name": user.full_name or "",
        "is_private": user.is_private,
        "profile_pic_url": url_to_str(user.profile_pic_url)
    }

def process_highlight(highlight):
    return {
        "id": highlight.id,
        "title": highlight.title or "Untitled",
        "cover_url": url_to_str(highlight.cover_url),
        "story_count": highlight.media_count
    }

# ======================
# API ENDPOINTS
# ======================

@app.route('/reels', methods=['GET'])
@cached(cache)
def reels_endpoint():
    """Get user's reels"""
    try:
        start = time.perf_counter()
        cl = init_client()
        user_id = cl.user_id_from_username(INSTA_USERNAME)
        reels = cl.user_clips(user_id, amount=20)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            processed = list(executor.map(process_reel, reels))
        
        elapsed = time.perf_counter() - start
        return jsonify({
            "status": "success",
            "count": len(processed),
            "time": f"{elapsed:.2f}s",
            "reels": processed
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/profile', methods=['GET'])
def profile_endpoint():
    """Get user profile information"""
    try:
        cl = init_client()
        user_id = cl.user_id_from_username(INSTA_USERNAME)
        profile = cl.user_info(user_id)
        
        return jsonify({
            "username": profile.username,
            "full_name": profile.full_name or "",
            "bio": profile.biography or "",
            "followers": profile.follower_count,
            "following": profile.following_count,
            "posts": profile.media_count,
            "profile_pic": url_to_str(profile.profile_pic_url),
            "is_private": profile.is_private,
            "is_verified": profile.is_verified
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/posts', methods=['GET'])
def posts_endpoint():
    """Get regular feed posts"""
    try:
        cl = init_client()
        user_id = cl.user_id_from_username(INSTA_USERNAME)
        posts = cl.user_medias(user_id, amount=20)
        
        processed = [process_post(p) for p in posts]
        return jsonify({
            "status": "success",
            "count": len(processed),
            "posts": processed
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/followers', methods=['GET'])
def followers_endpoint():
    """Get user followers"""
    try:
        cl = init_client()
        user_id = cl.user_id_from_username(INSTA_USERNAME)
        followers = cl.user_followers(user_id, amount=100)
        
        processed = [process_user(u) for u in followers.values()]
        return jsonify({
            "status": "success",
            "count": len(processed),
            "followers": processed
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/following', methods=['GET'])
def following_endpoint():
    """Get who user is following"""
    try:
        cl = init_client()
        user_id = cl.user_id_from_username(INSTA_USERNAME)
        following = cl.user_following(user_id, amount=100)
        
        processed = [process_user(u) for u in following.values()]
        return jsonify({
            "status": "success",
            "count": len(processed),
            "following": processed
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/highlights', methods=['GET'])
def highlights_endpoint():
    """Get story highlights"""
    try:
        cl = init_client()
        user_id = cl.user_id_from_username(INSTA_USERNAME)
        highlights = cl.user_highlights(user_id)
        
        processed = [process_highlight(h) for h in highlights]
        return jsonify({
            "status": "success",
            "count": len(processed),
            "highlights": processed
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/stories', methods=['GET'])
def stories_endpoint():
    """Get active stories"""
    try:
        cl = init_client()
        user_id = cl.user_id_from_username(INSTA_USERNAME)
        stories = cl.user_stories(user_id)
        
        processed = []
        for story in stories:
            processed.append({
                "id": story.pk,
                "created_at": story.taken_at.isoformat() + "Z",
                "media_url": url_to_str(story.video_url) if story.is_video else url_to_str(story.thumbnail_url),
                "is_video": story.is_video,
                "duration": story.video_duration if story.is_video else 0
            })
        
        return jsonify({
            "status": "success",
            "count": len(processed),
            "stories": processed
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/tagged', methods=['GET'])
def tagged_endpoint():
    """Get posts where user is tagged"""
    try:
        cl = init_client()
        user_id = cl.user_id_from_username(INSTA_USERNAME)
        tagged = cl.usertag_medias(user_id, amount=20)
        
        processed = [process_post(p) for p in tagged]
        return jsonify({
            "status": "success",
            "count": len(processed),
            "tagged_posts": processed
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/insights', methods=['GET'])
def insights_endpoint():
    """Get account insights (business accounts only)"""
    try:
        cl = init_client()
        insights = cl.account_insights()
        
        return jsonify({
            "impressions": insights.impressions,
            "reach": insights.reach,
            "profile_views": insights.profile_views,
            "email_contacts": insights.email_contacts,
            "follower_growth": insights.follower_growth
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Business account required for insights",
            "details": str(e)
        }), 400

if __name__ == '__main__':
    print(f"Starting Instagram API for @{INSTA_USERNAME}")
    app.run(host='0.0.0.0', port=5000, threaded=True)
