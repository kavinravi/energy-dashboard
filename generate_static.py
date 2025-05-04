"""
Script to generate a static version of the energy dashboard.
This creates HTML files that can be hosted on GitHub Pages.
"""

import os
import json
import re
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Load article data
def load_data(filename):
    try:
        with open(f'data/{filename}', 'r') as f:
            return json.load(f)
    except:
        print(f"Warning: Could not load {filename}, using empty list")
        return []

# Create static output directory
os.makedirs('static_site', exist_ok=True)

# Load templates
env = Environment(loader=FileSystemLoader('templates'))

# Add split filter to Jinja env
def split_filter(value, delimiter=','):
    """Split a string into a list on the given delimiter"""
    if not value:
        return []
    return value.split(delimiter)

env.filters['split'] = split_filter

# Load data
articles = load_data('articles.json')
podcasts = load_data('podcasts.json')

print(f"Loaded {len(articles)} articles and {len(podcasts)} podcasts")

# Process articles to ensure they have categories
def categorize_article(article):
    """Ensure article has categories field"""
    if 'categories' not in article or not article['categories']:
        # Default categories
        article['categories'] = 'innovation,business'
    return article

articles = [categorize_article(article) for article in articles]

# Sort content by date
articles.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)
podcasts.sort(key=lambda x: datetime.strptime(x['release_date'], '%Y-%m-%d'), reverse=True)

try:
    # Render the dashboard
    dashboard_template = env.get_template('dashboard.html')
    html_content = dashboard_template.render(
        articles=articles,
        podcasts=podcasts,
        last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        now=datetime.now()
    )

    # Write the HTML to file
    with open('static_site/index.html', 'w') as f:
        f.write(html_content)
    
    print(f"Successfully generated index.html")

    # Copy any static assets
    import shutil
    if os.path.exists('static'):
        shutil.copytree('static', 'static_site/static', dirs_exist_ok=True)
        print(f"Copied static assets")
    
    # Create a simple CSS file if static doesn't exist
    if not os.path.exists('static_site/static'):
        os.makedirs('static_site/static', exist_ok=True)
        with open('static_site/static/styles.css', 'w') as f:
            f.write("/* Basic styles */\n")
        print(f"Created basic static directory")
    
    print(f"Static site generated in 'static_site' directory.")
    print(f"Upload these files to GitHub Pages to share with your friend.")
except Exception as e:
    print(f"Error generating static site: {str(e)}")
    import traceback
    traceback.print_exc() 