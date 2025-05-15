import re
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def is_valid_url(url):
    """
    Check if a URL is valid
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def extract_instagram_urls(urls):
    """
    Extract and validate Instagram image URLs
    
    This function checks if URLs are from Instagram CDN (fbcdn) and 
    ensures they point to image files.
    
    Args:
        urls (list): List of URLs to validate
        
    Returns:
        list: List of valid Instagram image URLs
    """
    valid_urls = []
    
    # Pattern for fbcdn.net or cdninstagram.com URLs
    # Updated to handle various Instagram URL formats including .webp files
    instagram_pattern = r'(https?://(?:.*\.)?(?:fbcdn\.net|cdninstagram\.com|fna\.fbcdn\.net)/.*\.(?:jpg|jpeg|png|webp)(?:\?.*)?)'
    
    for url in urls:
        # Check if it's an Instagram CDN URL directly
        if ('fbcdn.net' in url or 'cdninstagram.com' in url or 'fna.fbcdn.net' in url) and is_valid_url(url):
            # Check if it's an image URL (including webp format)
            if re.search(r'\.(jpg|jpeg|png|webp)(\?.*)?$', url, re.IGNORECASE) or 'stp=dst-jpg' in url:
                valid_urls.append(url)
                logger.debug(f"Found valid Instagram URL: {url}")
                continue
        
        # Try to extract Instagram image URLs from the URL
        matches = re.findall(instagram_pattern, url, re.IGNORECASE)
        if matches:
            for match in matches:
                if is_valid_url(match) and match not in valid_urls:
                    valid_urls.append(match)
                    logger.debug(f"Extracted Instagram URL: {match}")
    
    logger.debug(f"Extracted {len(valid_urls)} valid Instagram image URLs")
    return valid_urls
