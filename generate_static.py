"""
Script to generate a static version of the energy dashboard.
This creates HTML files that can be hosted on GitHub Pages.
"""

import os
import json
import re
from datetime import datetime
import shutil

# Create static output directory
os.makedirs('static_site', exist_ok=True)

# Load article data
def load_data(filename):
    try:
        with open(f'data/{filename}', 'r') as f:
            return json.load(f)
    except:
        print(f"Warning: Could not load {filename}, using empty list")
        return []

# Load data
articles = load_data('articles.json')
podcasts = load_data('podcasts.json')

print(f"Loaded {len(articles)} articles and {len(podcasts)} podcasts")

try:
    # Read the dashboard template
    with open('dashboard.html', 'r') as f:
        content = f.read()
    
    # Replace the content
    content = content.replace('{{ last_updated }}', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    content = content.replace('{{ now.year }}', str(datetime.now().year))
    
    # Generate a simple version of the dashboard with articles/podcasts
    articles_html = ""
    for article in articles[:6]:
        title = article.get('title', 'Untitled')
        summary = article.get('summary', '')
        link = article.get('link', '#')
        date = article.get('date', '')
        source = article.get('source', '')
        categories = article.get('categories', 'innovation,business')
        
        # Build category badges
        category_badges = ""
        for category in categories.split(','):
            category_name = {
                'policy': 'Policy', 
                'innovation': 'Innovation', 
                'business': 'Business', 
                'climate': 'Climate'
            }.get(category, category)
            category_badges += f"""
            <span class="category-badge category-{category}">
                {category_name}
            </span>
            """
        
        articles_html += f"""
        <div class="news-card p-4 rounded-lg border border-gray-100" 
             data-categories="{categories}">
            <div class="flex flex-wrap gap-2 mb-2">
                {category_badges}
                <span class="ml-auto text-xs text-gray-500">{date}</span>
            </div>
            
            <h3 class="text-xl font-medium text-gray-900 mb-2 leading-tight">
                <a href="{link}" target="_blank" class="hover:text-primary-600">
                    {title}
                </a>
            </h3>
            
            <p class="text-gray-600 mb-3">{summary}</p>
            
            <div class="flex items-center justify-between">
                <span class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                    {source}
                </span>
                <a href="{link}" target="_blank" class="text-primary-600 hover:text-primary-800 text-sm font-medium">
                    Read more <i class="fas fa-arrow-right ml-1"></i>
                </a>
            </div>
        </div>
        """
    
    podcasts_html = ""
    for podcast in podcasts[:4]:
        title = podcast.get('title', 'Untitled')
        summary = podcast.get('summary', '')
        url = podcast.get('url', '#')
        release_date = podcast.get('release_date', '')
        
        podcasts_html += f"""
        <div class="news-card p-4 rounded-lg border border-gray-100">
            <div class="mb-2 flex justify-between items-center">
                <span class="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                    Podcast
                </span>
                <span class="text-xs text-gray-500">{release_date}</span>
            </div>
            
            <h3 class="text-lg font-medium text-gray-900 mb-2 leading-tight">
                <a href="{url}" target="_blank" class="hover:text-primary-600">
                    {title}
                </a>
            </h3>
            
            <p class="text-sm text-gray-600 mb-3">{summary}</p>
            
            <a href="{url}" target="_blank" class="text-primary-600 hover:text-primary-800 text-sm font-medium flex items-center">
                <i class="fas fa-play mr-1"></i> Listen
            </a>
        </div>
        """
    
    # Replace template placeholders with actual content
    content = re.sub(
        r'{% for article in articles\[:6\] %}.*?{% endfor %}',
        articles_html,
        content,
        flags=re.DOTALL
    )
    
    content = re.sub(
        r'{% for podcast in podcasts\[:4\] %}.*?{% endfor %}',
        podcasts_html,
        content,
        flags=re.DOTALL
    )
    
    # Write the static HTML
    with open('static_site/index.html', 'w') as f:
        f.write(content)
    
    print(f"Successfully generated index.html")
    
    # Copy static assets
    if os.path.exists('static'):
        shutil.copytree('static', 'static_site/static', dirs_exist_ok=True)
        print(f"Copied static assets")
    
    print(f"Static site generated successfully in 'static_site' directory")
    
except Exception as e:
    print(f"Error generating static site: {str(e)}")
    import traceback
    traceback.print_exc() 