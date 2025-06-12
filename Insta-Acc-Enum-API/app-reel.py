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
CACHE_TTL = int(os.getenv("CACHE_TTL", 1800))  # 30 minutes cache
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 5))  # Default 5 threads

# Validate credentials
if not INSTA_USERNAME or not INSTA_PASSWORD:
    raise ValueError("Both Instagram username and password must be provided in .env file")

cache = TTLCache(maxsize=100, ttl=CACHE_TTL)

def init_client():
    """Initialize and authenticate Instagram client"""
    cl = Client()
    print(f"Logging in as {INSTA_USERNAME}...")
    cl.login(INSTA_USERNAME, INSTA_PASSWORD)
    return cl

def process_reel(reel_media):
    """Extract required fields and convert URLs to strings"""
    # Convert yarl.URL objects to strings
    video_url = str(reel_media.video_url) if reel_media.video_url else None
    thumbnail_url = str(reel_media.thumbnail_url) if reel_media.thumbnail_url else None
    
    return {
        "id": reel_media.id,
        "unique_identifier": reel_media.code,
        "reel_url": f"https://instagram.com/reel/{reel_media.code}",
        "video_url": video_url,
        "thumbnail_url": thumbnail_url,
        "caption": reel_media.caption_text or "",
        "posted_at_utc": reel_media.taken_at.isoformat() + "Z",
        "views": reel_media.view_count,
        "likes": reel_media.like_count,
        "comments": reel_media.comment_count
    }

@cached(cache)
def get_user_reels():
    """Fetch reels with parallel processing"""
    cl = init_client()
    user_id = cl.user_id_from_username(INSTA_USERNAME)
    reels_media = cl.user_clips(user_id, amount=20)  # Get last 20 reels
    
    # Parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        processed_reels = list(executor.map(process_reel, reels_media))
    
    # Sort by most recent
    return sorted(
        processed_reels,
        key=lambda x: x['posted_at_utc'],
        reverse=True
    )

@app.route('/reels', methods=['GET'])
def reels_endpoint():
    """API endpoint for retrieving reels"""
    try:
        start_time = time.perf_counter()
        reels = get_user_reels()
        elapsed = time.perf_counter() - start_time
        
        return jsonify({
            "status": "success",
            "count": len(reels),
            "processing_time": f"{elapsed:.2f} seconds",
            "reels": reels
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Instagram Reels API...")
    print(f"Username: {INSTA_USERNAME}")
    app.run(host='0.0.0.0', port=5000, threaded=True)
