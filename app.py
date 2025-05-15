import os
import logging
import time
from flask import Flask, request, jsonify, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from collage_service import create_collage_from_urls
from utils import is_valid_url, extract_instagram_urls

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# No rate limiting - unlimited usage
# Keeping empty data structure for compatibility with existing code
rate_limit_data = {}

# Ensure collage storage directory exists
os.makedirs('static/collages', exist_ok=True)

@app.route('/')
def index():
    """Simple frontend to test the API"""
    return render_template('index.html')

@app.route('/api/create-collage', methods=['POST'])
def create_collage_endpoint():
    """
    API endpoint to create a collage from Instagram carousel URLs
    
    Expected JSON input:
    {
        "urls": ["url1", "url2", ...]
    }
    
    Returns:
    {
        "success": true/false,
        "message": "Information message",
        "collage_url": "URL to the created collage" (only if successful)
    }
    """
    # No rate limiting - process all requests
    # Removing all rate limit checks as requested
    
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'urls' not in data:
            return jsonify({
                "success": False,
                "message": "Missing required parameter: urls"
            }), 400
            
        urls = data['urls']
        
        # Validate URLs
        if not urls or not isinstance(urls, list):
            return jsonify({
                "success": False,
                "message": "URLs must be provided as a non-empty list"
            }), 400
            
        # Validate each URL
        valid_urls = []
        for url in urls:
            if isinstance(url, str) and is_valid_url(url):
                valid_urls.append(url)
            else:
                logger.warning(f"Invalid URL provided: {url}")
        
        if not valid_urls:
            return jsonify({
                "success": False,
                "message": "No valid URLs provided"
            }), 400
        
        # Extract Instagram URLs if needed
        instagram_urls = extract_instagram_urls(valid_urls)
        
        if not instagram_urls:
            return jsonify({
                "success": False,
                "message": "No valid Instagram image URLs found"
            }), 400
            
        # Create the collage with larger dimensions for better zoom quality
        logger.info(f"Creating collage from {len(instagram_urls)} images")
        # Using much higher resolution for better quality when zooming
        collage_filename, error = create_collage_from_urls(instagram_urls, max_width=4096, max_height=4096)
        
        if error:
            return jsonify({
                "success": False,
                "message": f"Failed to create collage: {error}"
            }), 500
            
        # Create URL for the collage
        host = request.host_url.rstrip('/')
        collage_url = f"{host}/static/collages/{collage_filename}"
        
        return jsonify({
            "success": True,
            "message": "Collage created successfully",
            "collage_url": collage_url
        }), 200
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Internal server error: {str(e)}"
        }), 500
