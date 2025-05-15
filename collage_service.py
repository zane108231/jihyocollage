import os
import uuid
import logging
import requests
from io import BytesIO
from PIL import Image
from datetime import datetime

logger = logging.getLogger(__name__)

def download_image(url):
    """
    Download an image from a URL and return it as a PIL Image object
    
    Args:
        url (str): The URL of the image to download
        
    Returns:
        tuple: (PIL.Image or None, error message or None)
    """
    try:
        # Add User-Agent header to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
        }
        
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Check content type, but allow the download even if content-type is not explicitly an image
        # Instagram sometimes doesn't set the proper content type
        content_type = response.headers.get('Content-Type', '')
        logger.debug(f"Content-Type for {url}: {content_type}")
        
        # Try to open the image regardless of content type
        img = Image.open(BytesIO(response.content))
        
        # Convert WebP to JPEG if needed
        if img.format == "WEBP":
            logger.debug(f"Converting WebP image to JPEG: {url}")
            rgb_img = img.convert('RGB')
            return rgb_img, None
        
        return img, None
    except requests.RequestException as e:
        logger.error(f"Failed to download image from URL {url}: {str(e)}")
        return None, f"Failed to download image: {str(e)}"
    except Exception as e:
        logger.error(f"Error processing image from URL {url}: {str(e)}")
        return None, f"Error processing image: {str(e)}"

def create_collage(images, max_width=2048, max_height=2048):
    """
    Create a premium Instagram-style collage from a list of PIL Image objects
    
    Args:
        images (list): List of PIL.Image objects
        max_width (int): Maximum width of the collage
        max_height (int): Maximum height of the collage
        
    Returns:
        PIL.Image: Collage image
    """
    import math
    import io
    import random
    from PIL import ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

    if not images:
        return None, "No images provided for collage"
    
    # Determine the layout based on number of images
    num_images = len(images)
    
    if num_images == 1:
        # For single image, add a beautiful frame and filter
        img = images[0]
        
        # Resize if needed
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
        # Add a subtle warm filter
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.1)  # Slightly increase color saturation
        
        # Add contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.05)  # Slightly increase contrast
        
        # Add a premium frame
        frame_width = 40
        frame_color = (255, 255, 255)  # White frame
        frame_img = ImageOps.expand(img, border=frame_width, fill=frame_color)
        
        # Add inner shadow to frame
        frame_with_shadow = Image.new('RGB', frame_img.size, frame_color)
        shadow_width = 5
        
        # Create shadow effect inside frame
        draw = ImageDraw.Draw(frame_with_shadow)
        for i in range(shadow_width):
            # Draw progressively lighter shadow lines
            shadow_color = (220 - i * 10, 220 - i * 10, 220 - i * 10)
            draw.rectangle(
                [frame_width - shadow_width + i, frame_width - shadow_width + i, 
                 frame_with_shadow.width - frame_width + shadow_width - i, 
                 frame_with_shadow.height - frame_width + shadow_width - i], 
                outline=shadow_color
            )
        
        # Paste the image onto the frame with shadow
        frame_with_shadow.paste(img, (frame_width, frame_width))
        
        return frame_with_shadow, None
    
    # PREMIUM COLLAGE LAYOUT FOR MULTIPLE IMAGES
    
    # Optimize layout based on number of images to avoid empty spaces
    # Dynamic grid calculation for best fit
    
    # Define optimal layouts for different image counts
    # Format: (cols, rows)
    optimal_layouts = {
        1: (1, 1),   # 1 image: 1x1
        2: (2, 1),   # 2 images: 2x1
        3: (3, 1),   # 3 images: 3x1
        4: (2, 2),   # 4 images: 2x2
        5: (5, 1),   # 5 images: 5x1
        6: (3, 2),   # 6 images: 3x2
        7: (3, 3),   # 7 images: 3x3 (2 empty spots at the end)
        8: (4, 2),   # 8 images: 4x2
        9: (3, 3),   # 9 images: 3x3
        10: (5, 2),  # 10 images: 5x2
    }
    
    # Get the optimal layout for this number of images
    if num_images in optimal_layouts:
        cols, rows = optimal_layouts[num_images]
    else:
        # For more than 10 images, create rows with 5 images each
        # This will ensure no empty spaces at the end
        cols = 5
        rows = math.ceil(num_images / cols)
    
    # Calculate optimal spacing - reduced to increase image sizes
    SPACING_PERCENT = 0.02  # Spacing as percentage of image width (reduced from 0.03)
    
    # Calculate available space after accounting for spacing between cells
    avail_width = max_width - ((cols - 1) * (max_width * SPACING_PERCENT))
    
    # Calculate cell dimensions
    cell_width = int(avail_width / cols)
    cell_height = cell_width  # Square cells for Instagram look
    
    # Actual spacing in pixels
    SPACING = int(cell_width * SPACING_PERCENT)
    
    # Calculate exact dimensions for the collage
    actual_width = (cell_width * cols) + (SPACING * (cols - 1))
    actual_height = (cell_height * rows) + (SPACING * (rows - 1))
    
    # Add branding space at top and bottom - reduced to increase image sizes
    TOP_PADDING = int(cell_height * 0.1)  # 10% of cell height (reduced from 15%)
    BOTTOM_PADDING = int(cell_height * 0.15)  # 15% of cell height (reduced from 20%)
    SIDE_PADDING = SPACING  # Reduced side padding to allow larger images
    
    # Total collage dimensions
    collage_width = actual_width + (SIDE_PADDING * 2)
    collage_height = actual_height + TOP_PADDING + BOTTOM_PADDING
    
    # Create the base canvas with gradient background
    def create_gradient_background(width, height):
        # Create a subtle Instagram-inspired gradient
        bg = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(bg)
        
        # Define gradient colors (light shades)
        top_color = (250, 250, 252)  # Almost white with slight blue tint
        bottom_color = (252, 252, 250)  # Almost white with slight warm tint
        
        # Draw gradient by creating many horizontal lines
        for y in range(height):
            # Calculate color for this line
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * y / height)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * y / height)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * y / height)
            
            draw.line([(0, y), (width, y)], fill=(r, g, b))
            
        return bg
    
    # Create gradient background
    collage = create_gradient_background(collage_width, collage_height)
    draw = ImageDraw.Draw(collage)
    
    # Try to load fonts for labels and branding
    try:
        number_font = ImageFont.truetype("arial.ttf", 24)
        title_font = ImageFont.truetype("arial.ttf", 18)
        logo_font = ImageFont.truetype("arial.ttf", 26)
    except IOError:
        number_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        logo_font = ImageFont.load_default()
    
    # Process all images to be consistent
    processed_images = []
    
    for img in images:
        # Step 1: Center-crop to square aspect ratio
        width, height = img.size
        
        # Get the smallest dimension
        min_dim = min(width, height)
        
        # Calculate crop box
        left = (width - min_dim) / 2
        top = (height - min_dim) / 2
        right = (width + min_dim) / 2
        bottom = (height + min_dim) / 2
        
        # Crop to square
        img_square = img.crop((left, top, right, bottom))
        
        # Step 2: Apply subtle image enhancements (Instagram-like filters)
        # Enhance color slightly
        enhancer = ImageEnhance.Color(img_square)
        img_enhanced = enhancer.enhance(1.05)
        
        # Increase contrast slightly
        enhancer = ImageEnhance.Contrast(img_enhanced)
        img_enhanced = enhancer.enhance(1.08)
        
        # Increase sharpness slightly
        enhancer = ImageEnhance.Sharpness(img_enhanced)
        img_enhanced = enhancer.enhance(1.1)
        
        # Step 3: Resize to cell size
        img_resized = img_enhanced.resize((cell_width, cell_height), Image.Resampling.LANCZOS)
        
        # Add to processed images
        processed_images.append(img_resized)
    
    # Draw a decorative header
    header_y = TOP_PADDING // 2
    
    # Instagram-inspired logo/brand mark
    # Create a stylish logo block with gradient
    logo_width = 120
    logo_height = 36
    logo_x = SIDE_PADDING
    
    # Draw Instagram-style camera icon
    camera_icon_size = 30
    camera_x = logo_x + logo_width + 10
    camera_y = header_y - camera_icon_size // 2
    
    # Draw camera outline
    draw.rounded_rectangle(
        [camera_x, camera_y, camera_x + camera_icon_size, camera_y + camera_icon_size],
        radius=8,
        outline=(200, 200, 200),
        width=2
    )
    
    # Draw camera lens
    lens_size = camera_icon_size // 2
    lens_x = camera_x + (camera_icon_size - lens_size) // 2
    lens_y = camera_y + (camera_icon_size - lens_size) // 2
    draw.ellipse(
        [lens_x, lens_y, lens_x + lens_size, lens_y + lens_size],
        outline=(200, 200, 200),
        width=2
    )
    
    # Draw camera viewfinder
    viewfinder_size = camera_icon_size // 5
    viewfinder_x = camera_x + camera_icon_size - viewfinder_size - 3
    viewfinder_y = camera_y + 3
    draw.ellipse(
        [viewfinder_x, viewfinder_y, viewfinder_x + viewfinder_size, viewfinder_y + viewfinder_size],
        fill=(220, 220, 220)
    )
    
    # Place images into the collage
    for i, img in enumerate(processed_images):
        if i >= num_images:
            break
            
        # Calculate grid position
        grid_x = i % cols
        grid_y = i // cols
        
        # Special layout for 7 images - center the last image in the bottom row
        if num_images == 7 and i == 6:  # The 7th image (index 6)
            # Calculate center position for the last image
            grid_x = 1  # Center column in a 3x3 grid
        
        # Calculate pixel position
        x = SIDE_PADDING + grid_x * (cell_width + SPACING)
        y = TOP_PADDING + grid_y * (cell_height + SPACING)
        
        # Create frame effect
        border_width = 1
        frame_color = (240, 240, 240)
        
        # Draw subtle frame
        draw.rectangle(
            [x - border_width, y - border_width, 
             x + cell_width + border_width, y + cell_height + border_width],
            outline=frame_color,
            width=border_width
        )
        
        # Create shadow effect
        shadow_img = Image.new('RGBA', (cell_width + 10, cell_height + 10), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_img)
        
        # Draw shadow
        shadow_draw.rectangle(
            [5, 5, cell_width + 5, cell_height + 5],
            fill=(0, 0, 0, 30)
        )
        
        # Blur the shadow
        shadow_blur = shadow_img.filter(ImageFilter.GaussianBlur(5))
        
        # Paste shadow
        collage.paste(shadow_blur, (x - 5, y - 5), shadow_blur)
        
        # Create rounded corners on the image
        corner_radius = 6
        mask = Image.new('L', (cell_width, cell_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (cell_width, cell_height)], radius=corner_radius, fill=255)
        
        # Create RGBA version for composition
        img_with_corners = Image.new('RGBA', (cell_width, cell_height))
        img_with_corners.paste(img, (0, 0), mask)
        
        # Paste the rounded image
        collage.paste(img_with_corners, (x, y), mask)
        
        # Add number indicator
        label_bg_size = 32
        label_margin = 6
        
        # Create circular number badge
        number_badge = Image.new('RGBA', (label_bg_size, label_bg_size), (0, 0, 0, 0))
        number_badge_draw = ImageDraw.Draw(number_badge)
        
        # PREMIUM GRADIENT LABEL
        # Create gradient effect for labels (Instagram-like)
        # Define gradient colors
        colors = [
            (226, 40, 85),   # Instagram-like pink
            (64, 93, 230),   # Instagram-like blue
            (252, 175, 69),  # Instagram-like gold
        ]
        
        # Get colors for this label based on position
        color_idx = i % len(colors)
        color1 = colors[color_idx]
        color2 = colors[(color_idx + 1) % len(colors)]
        
        # Draw gradient circle by drawing concentric circles
        radius = label_bg_size // 2
        for r in range(radius, 0, -1):
            # Calculate color for this radius
            ratio = r / radius
            r_color = int(color1[0] * ratio + color2[0] * (1 - ratio))
            g_color = int(color1[1] * ratio + color2[1] * (1 - ratio))
            b_color = int(color1[2] * ratio + color2[2] * (1 - ratio))
            
            number_badge_draw.ellipse(
                [radius - r, radius - r, radius + r, radius + r],
                fill=(r_color, g_color, b_color)
            )
        
        # Add number text
        number_text = str(i + 1)
        text_width = number_badge_draw.textlength(number_text, font=number_font)
        text_x = (label_bg_size - text_width) // 2
        text_y = (label_bg_size - 24) // 2 - 2  # Use fixed font size instead of font.size
        
        # Add white text shadow for better visibility
        shadow_offset = 1
        number_badge_draw.text(
            (text_x + shadow_offset, text_y + shadow_offset),
            number_text,
            fill=(255, 255, 255, 180),
            font=number_font
        )
        
        # Add main text
        number_badge_draw.text(
            (text_x, text_y),
            number_text,
            fill=(255, 255, 255),
            font=number_font
        )
        
        # Position number badge in top-right corner
        badge_x = x + cell_width - label_bg_size - label_margin
        badge_y = y + label_margin
        collage.paste(number_badge, (badge_x, badge_y), number_badge)
    
    # Add Instagram-inspired footer
    footer_y = collage_height - BOTTOM_PADDING + (BOTTOM_PADDING // 3)
    
    # Draw separator line
    separator_color = (220, 220, 220)
    draw.line(
        [SIDE_PADDING, footer_y, collage_width - SIDE_PADDING, footer_y],
        fill=separator_color,
        width=1
    )
    
    # Add info text
    footer_text = f"Instagram Carousel • {num_images} Photos"
    
    # For 10+ images, add "Swipe ➡️" text
    if num_images >= 10:
        footer_text += " • Swipe ➡️"
    
    footer_x = SIDE_PADDING
    footer_text_y = footer_y + 15
    
    # Draw text shadow
    draw.text(
        (footer_x + 1, footer_text_y + 1),
        footer_text,
        fill=(180, 180, 180),
        font=title_font
    )
    
    # Draw main text
    draw.text(
        (footer_x, footer_text_y),
        footer_text,
        fill=(100, 100, 100),
        font=title_font
    )
    
    # Add timestamp (Instagram-style)
    import time
    timestamp = time.strftime("%b %d, %Y", time.localtime())
    timestamp_width = draw.textlength(timestamp, font=title_font)
    timestamp_x = collage_width - SIDE_PADDING - timestamp_width
    
    # Draw timestamp shadow
    draw.text(
        (timestamp_x + 1, footer_text_y + 1),
        timestamp,
        fill=(180, 180, 180),
        font=title_font
    )
    
    # Draw main timestamp
    draw.text(
        (timestamp_x, footer_text_y),
        timestamp,
        fill=(130, 130, 130),
        font=title_font
    )
    
    # Add Instagram-like engagement icons
    icons_y = footer_text_y + 35
    icon_spacing = 50
    
    # Heart icon
    heart_x = SIDE_PADDING
    heart_color = (220, 50, 50)  # Red for heart
    
    # Draw heart icon
    heart_size = 24
    heart_points = [
        (heart_x + heart_size // 2, icons_y + 8),  # Bottom point
        (heart_x + 4, icons_y - 2),  # Left point
        (heart_x + heart_size // 2, icons_y - 8),  # Top left
        (heart_x + heart_size - 4, icons_y - 2),  # Right point
    ]
    draw.polygon(heart_points, fill=heart_color)
    
    # Add like count
    like_count = random.randint(100, 999)
    like_text = f"{like_count}"
    draw.text((heart_x + heart_size + 5, icons_y - 8), like_text, fill=(100, 100, 100), font=title_font)
    
    # Comment icon
    comment_x = heart_x + icon_spacing + 20
    comment_color = (100, 100, 100)
    
    # Draw comment bubble
    comment_size = 22
    draw.rounded_rectangle(
        [comment_x, icons_y - 10, comment_x + comment_size, icons_y + 6],
        radius=8,
        outline=comment_color,
        width=2
    )
    
    # Add comment count
    comment_count = random.randint(10, 99)
    comment_text = f"{comment_count}"
    draw.text((comment_x + comment_size + 5, icons_y - 8), comment_text, fill=(100, 100, 100), font=title_font)
    
    # Share icon
    share_x = comment_x + icon_spacing + 10
    share_color = (100, 100, 100)
    
    # Draw forward arrow
    arrow_size = 20
    draw.line(
        [share_x, icons_y - 2, share_x + arrow_size, icons_y - 2],
        fill=share_color,
        width=2
    )
    
    # Arrow head
    arrow_head = [
        (share_x + arrow_size - 6, icons_y - 8),
        (share_x + arrow_size, icons_y - 2),
        (share_x + arrow_size - 6, icons_y + 4)
    ]
    draw.polygon(arrow_head, fill=share_color)
    
    # Add bookmark icon on the right
    bookmark_x = collage_width - SIDE_PADDING - 20
    bookmark_color = (100, 100, 100)
    
    # Draw bookmark
    bookmark_size = 20
    draw.rectangle(
        [bookmark_x, icons_y - 10, bookmark_x + bookmark_size, icons_y + 10],
        outline=bookmark_color,
        width=2
    )
    
    # Draw bookmark triangle
    bookmark_triangle = [
        (bookmark_x, icons_y + 5),
        (bookmark_x + bookmark_size // 2, icons_y),
        (bookmark_x + bookmark_size, icons_y + 5)
    ]
    draw.polygon(bookmark_triangle, fill=bookmark_color)
    
    return collage, None

def create_collage_from_urls(urls, max_width=4096, max_height=4096):
    """
    Download images from URLs and create a collage
    
    Args:
        urls (list): List of image URLs
        max_width (int): Maximum width of the collage (default: 2048px)
        max_height (int): Maximum height of the collage (default: 2048px)
        
    Returns:
        tuple: (filename of saved collage or None, error message or None)
    """
    # Download all images
    images = []
    for url in urls:
        img, error = download_image(url)
        if img:
            images.append(img)
        else:
            logger.warning(f"Failed to download image: {error}")
    
    if not images:
        return None, "Failed to download any valid images"
    
    # Create the collage with specified dimensions
    collage, error = create_collage(images, max_width=max_width, max_height=max_height)
    if error or collage is None:
        return None, error or "Failed to create collage"
    
    # Generate a unique filename
    filename = f"collage_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join('static/collages', filename)
    
    # Save the collage with high quality setting
    try:
        # Use quality=95 for better details when zooming
        collage.save(filepath, format='JPEG', quality=95, optimize=True)
        logger.info(f"Collage saved to {filepath}")
        return filename, None
    except Exception as e:
        logger.error(f"Error saving collage: {str(e)}")
        return None, f"Error saving collage: {str(e)}"
