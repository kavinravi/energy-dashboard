from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request
from web_scraper import WebScraper
from podcast_scraper import PodcastScraper
import os
from datetime import datetime
import json
import traceback
import logging
from logging.handlers import RotatingFileHandler
import re
import pytz

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up file handler
os.makedirs('logs', exist_ok=True)
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Load environment variables from .env file
logger.info("Starting application...")
load_dotenv()

# Debug: Print environment variables
print("SPOTIFY_CLIENT_ID:", os.getenv('SPOTIFY_CLIENT_ID'))
print("SPOTIFY_CLIENT_SECRET:", os.getenv('SPOTIFY_CLIENT_SECRET'))
print("SPOTIPY_REDIRECT_URI:", os.getenv('SPOTIPY_REDIRECT_URI'))  # Keep this for debugging

app = Flask(__name__)

# Add custom Jinja2 filter for splitting strings
@app.template_filter('split')
def split_filter(value, delimiter=','):
    """Split a string into a list on the given delimiter"""
    return value.split(delimiter)

# Initialize scrapers
try:
    # Get Spotify credentials from environment variables (still read for now, but not passed to PodcastScraper)
    spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
    spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not spotify_client_id or not spotify_client_secret:
        logger.warning("Spotify credentials not found in environment variables. Podcast features requiring Spotify API (if any in future) may not work.")
    
    web_scraper = WebScraper()
    podcast_scraper = PodcastScraper() # No arguments needed now
    
    logger.info("Successfully initialized scrapers (PodcastScraper using RSS)")
except Exception as e:
    logger.error(f"Error initializing scrapers: {str(e)}")
    traceback.print_exc()
    raise

def categorize_articles(articles):
    """Automatically categorize articles based on content and title"""
    category_keywords = {
        'policy': [
            'policy', 'regulation', 'law', 'bill', 'legislation', 'government', 
            'epa', 'regulatory', 'compliance', 'mandate', 'tax', 'incentive', 'subsidy',
            'administration', 'congress', 'senate', 'house', 'department', 'agency',
            'IRA', 'inflation reduction act', 'DOE', 'FERC'
        ],
        'innovation': [
            'innovation', 'technology', 'research', 'development', 'breakthrough',
            'prototype', 'invention', 'startup', 'efficiency', 'advanced', 'novel',
            'solution', 'discovery', 'cutting-edge', 'emerging', 'battery', 'storage',
            'inverter', 'grid', 'smart', 'digital', 'AI', 'artificial intelligence'
        ],
        'business': [
            'investment', 'merger', 'acquisition', 'funding', 'IPO', 'capital',
            'market', 'stock', 'shares', 'venture', 'profit', 'revenue', 'cost',
            'price', 'company', 'corporation', 'industry', 'commercial', 'economics',
            'billion', 'million', 'financial', 'CEO', 'executive', 'board'
        ],
        'climate': [
            'climate', 'emissions', 'carbon', 'pollution', 'global warming', 'greenhouse',
            'renewable', 'clean energy', 'sustainable', 'sustainability', 'environment',
            'net-zero', 'decarbonization', 'methane', 'fossil fuel', 'coal', 'natural gas',
            'conservation', 'biodiversity', 'ecosystem'
        ]
    }
    
    for article in articles:
        # Combine title and summary text for categorization
        text = (article['title'] + ' ' + article['summary']).lower()
        
        # Count occurrences of category keywords
        category_counts = {category: 0 for category in category_keywords}
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    category_counts[category] += 1
        
        # Assign categories (can have multiple)
        assigned_categories = []
        for category, count in category_counts.items():
            if count >= 1:  # If at least one keyword match, assign the category
                assigned_categories.append(category)
        
        # Ensure at least one category
        if not assigned_categories:
            # Default to most likely based on energy news
            assigned_categories = ['innovation', 'business']
        
        article['categories'] = ','.join(assigned_categories)
    
    return articles

def update_content() -> bool:
    """Update all content sources with improved error handling"""
    try:
        logger.info("Starting content update...")
        
        # Scrape articles with configurable date filters
        article_days = int(os.getenv('ARTICLE_DAYS_FILTER', '7'))
        podcast_days = int(os.getenv('PODCAST_DAYS_FILTER', '30'))
        
        # Scrape and filter articles
        canary_articles = web_scraper.scrape_canary_media()
        utility_dive_articles = web_scraper.scrape_utility_dive()
        
        # Combine and filter articles
        all_articles = web_scraper.filter_recent_content(
            canary_articles + utility_dive_articles,
            days=article_days
        )
        
        # Categorize articles
        all_articles = categorize_articles(all_articles)
        
        # Save articles even if we can't get podcasts
        if all_articles:
            web_scraper.save_articles(all_articles, 'articles.json')
            logger.info(f"Successfully updated {len(all_articles)} articles")
        
        # Try to get podcast episodes, but don't fail if we can't
        try:
            # Scrape and filter podcast episodes
            podcast_episodes = podcast_scraper.get_latest_episodes()
            filtered_episodes = podcast_scraper.filter_recent_episodes(
                podcast_episodes,
                days=podcast_days
            )
            
            # Save episodes
            if filtered_episodes:
                podcast_scraper.save_episodes(filtered_episodes, 'podcasts.json')
                logger.info(f"Successfully updated {len(filtered_episodes)} podcast episodes")
        except Exception as e:
            logger.error(f"Error updating podcast content: {str(e)}")
            logger.info("Continuing with article content only")
        
        return True
    except Exception as e:
        logger.error(f"Error updating content: {str(e)}")
        traceback.print_exc()
        return False

@app.route('/')
def dashboard():
    """Render the main dashboard with error handling"""
    try:
        # Load content
        articles = web_scraper.load_articles('articles.json')
        podcasts = podcast_scraper.load_episodes('podcasts.json')
        
        # Sort content by date
        articles.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)
        podcasts.sort(key=lambda x: datetime.strptime(x['release_date'], '%Y-%m-%d'), reverse=True)
        
        # Ensure articles have categories
        articles = categorize_articles(articles)
        
        # Get current time in Pacific timezone
        pacific_tz = pytz.timezone('America/Los_Angeles')
        current_time_pst = datetime.now(pytz.utc).astimezone(pacific_tz)
        
        return render_template(
            'dashboard.html',
            articles=articles,
            podcasts=podcasts,
            last_updated=current_time_pst.strftime("%Y-%m-%d %H:%M:%S %Z"),
            now=current_time_pst
        )
    except Exception as e:
        logger.error(f"Error rendering dashboard: {str(e)}")
        traceback.print_exc()
        return render_template('error.html', error=str(e)), 500

@app.route('/api/update')
def update():
    """API endpoint to trigger content update with improved response"""
    try:
        success = update_content()
        if success:
            return jsonify({
                "status": "success",
                "message": "Content updated successfully",
                "timestamp": datetime.now().isoformat()
            })
        return jsonify({
            "status": "error",
            "message": "Failed to update content",
            "timestamp": datetime.now().isoformat()
        }), 500
    except Exception as e:
        logger.error(f"Error in update endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/test')
def test():
    """Simple test endpoint to verify connectivity"""
    return "Connection successful! The server is running."

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Initial content update - don't fail if it doesn't work
    try:
        update_content()
    except Exception as e:
        logger.warning(f"Initial content update failed: {str(e)}")
        logger.warning("Will continue with existing content")
    
    # Get port from environment variable for hosting platforms like Heroku
    port = int(os.environ.get('PORT', 9000))
    
    # Run the Flask application
    logger.info(f"Starting Flask application on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
