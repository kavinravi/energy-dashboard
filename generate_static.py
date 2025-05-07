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
    # Try to read the dashboard template from different locations
    template_path = None
    template_paths = ['dashboard.html', 'templates/dashboard.html']
    
    for path in template_paths:
        if os.path.exists(path):
            template_path = path
            break
    
    if not template_path:
        raise FileNotFoundError("Could not find dashboard.html template in any expected location")
        
    print(f"Using template at: {template_path}")
        
    # Read the dashboard template
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Replace the static template variables
    content = content.replace('{{ last_updated }}', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    content = content.replace('{{ now.year }}', str(datetime.now().year))
    
    # --- ARTICLES_COLUMN_1_PLACEHOLDER (articles[:3]) ---
    articles_col1_html = ""
    for article in articles[:3]: # First 3 articles
        title = article.get('title', 'Untitled')
        summary = article.get('summary', '')
        link = article.get('link', '#')
        date = article.get('date', '')
        source = article.get('source', '')
        categories = article.get('categories', 'innovation,business')
        category_badges = ""
        for category_str in categories.split(','):
            category_name = {'policy': 'Policy', 'innovation': 'Innovation', 'business': 'Business', 'climate': 'Climate'}.get(category_str.strip(), category_str.strip().capitalize())
            category_badges += f'<span class="category-badge category-{category_str.strip()}">{category_name}</span>\\n'
        
        articles_col1_html += f'''
        <div class="news-card p-4 rounded-lg border border-gray-100" data-categories="{categories}">
            <div class="flex flex-wrap gap-2 mb-2">
                {category_badges}
                <span class="ml-auto text-xs text-gray-500">{date}</span>
            </div>
            <h3 class="text-xl font-medium text-gray-900 mb-2 leading-tight">
                <a href="{link}" target="_blank" class="hover:text-primary-600">{title}</a>
            </h3>
            <p class="text-gray-600 mb-3">{summary}</p>
            <div class="flex items-center justify-between">
                <span class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">{source}</span>
                <a href="{link}" target="_blank" class="text-primary-600 hover:text-primary-800 text-sm font-medium">
                    Read more <i class="fas fa-arrow-right ml-1"></i>
                </a>
            </div>
        </div>
        '''
    content = content.replace('<!-- ARTICLES_COLUMN_1_PLACEHOLDER -->', articles_col1_html)

    # --- PODCASTS_COLUMN_1_PLACEHOLDER (podcasts[:2]) ---
    podcasts_col1_html = ""
    for podcast in podcasts[:2]: # First 2 podcasts
        title = podcast.get('title', 'Untitled')
        summary = podcast.get('summary', '')
        url = podcast.get('url', '#')
        release_date = podcast.get('release_date', '')
        podcasts_col1_html += f'''
        <div class="news-card p-4 rounded-lg border border-gray-100">
            <div class="mb-2 flex justify-between items-center">
                <span class="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">Podcast</span>
                <span class="text-xs text-gray-500">{release_date}</span>
            </div>
            <h3 class="text-lg font-medium text-gray-900 mb-2 leading-tight">
                <a href="{url}" target="_blank" class="hover:text-primary-600">{title}</a>
            </h3>
            <p class="text-sm text-gray-600 mb-3">{summary}</p>
            <a href="{url}" target="_blank" class="text-primary-600 hover:text-primary-800 text-sm font-medium flex items-center">
                <i class="fas fa-play mr-1"></i> Listen
            </a>
        </div>
        '''
    content = content.replace('<!-- PODCASTS_COLUMN_1_PLACEHOLDER -->', podcasts_col1_html)

    # --- ARTICLE_COLUMN_2_PLACEHOLDER (articles[3] if exists) ---
    article_col2_html = ""
    if len(articles) > 3:
        article = articles[3]
        title = article.get('title', 'Untitled')
        summary = article.get('summary', '')
        link = article.get('link', '#')
        date = article.get('date', '')
        source = article.get('source', '')
        categories = article.get('categories', 'innovation,business')
        category_badges = ""
        for category_str in categories.split(','):
            category_name = {'policy': 'Policy', 'innovation': 'Innovation', 'business': 'Business', 'climate': 'Climate'}.get(category_str.strip(), category_str.strip().capitalize())
            category_badges += f'<span class="category-badge category-{category_str.strip()}">{category_name}</span>\\n'
        article_col2_html = f'''
        <div class="news-card p-4 rounded-lg border border-gray-100" data-categories="{categories}">
            <div class="flex flex-wrap gap-2 mb-2">
                {category_badges}
                <span class="ml-auto text-xs text-gray-500">{date}</span>
            </div>
            <h3 class="text-xl font-medium text-gray-900 mb-2 leading-tight">
                <a href="{link}" target="_blank" class="hover:text-primary-600">{title}</a>
            </h3>
            <p class="text-gray-600 mb-3">{summary}</p>
            <div class="flex items-center justify-between">
                <span class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">{source}</span>
                <a href="{link}" target="_blank" class="text-primary-600 hover:text-primary-800 text-sm font-medium">
                    Read more <i class="fas fa-arrow-right ml-1"></i>
                </a>
            </div>
        </div>
        '''
    content = content.replace('<!-- ARTICLE_COLUMN_2_PLACEHOLDER -->', article_col2_html)

    # --- ARTICLE_COLUMN_3_PLACEHOLDER (articles[4] if exists) ---
    article_col3_html = ""
    if len(articles) > 4: # For the article in the "additional row", first column
        article = articles[4]
        title = article.get('title', 'Untitled')
        summary = article.get('summary', '')
        link = article.get('link', '#')
        date = article.get('date', '')
        source = article.get('source', '')
        categories = article.get('categories', 'innovation,business')
        category_badges = ""
        for category_str in categories.split(','):
            category_name = {'policy': 'Policy', 'innovation': 'Innovation', 'business': 'Business', 'climate': 'Climate'}.get(category_str.strip(), category_str.strip().capitalize())
            category_badges += f'<span class="category-badge category-{category_str.strip()}">{category_name}</span>\\n'
        article_col3_html = f'''
        <div class="news-card p-4 rounded-lg border border-gray-100" data-categories="{categories}">
            <div class="flex flex-wrap gap-2 mb-2">
                {category_badges}
                <span class="ml-auto text-xs text-gray-500">{date}</span>
            </div>
            <h3 class="text-xl font-medium text-gray-900 mb-2 leading-tight">
                <a href="{link}" target="_blank" class="hover:text-primary-600">{title}</a>
            </h3>
            <p class="text-gray-600 mb-3">{summary}</p>
            <div class="flex items-center justify-between">
                <span class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">{source}</span>
                <a href="{link}" target="_blank" class="text-primary-600 hover:text-primary-800 text-sm font-medium">
                    Read more <i class="fas fa-arrow-right ml-1"></i>
                </a>
            </div>
        </div>
        '''
    content = content.replace('<!-- ARTICLE_COLUMN_3_PLACEHOLDER -->', article_col3_html)
    
    # --- PODCASTS_COLUMN_2_PLACEHOLDER (podcasts[2] if exists) ---
    podcasts_col2_html = ""
    if len(podcasts) > 2: # For the podcast in the "additional row", second column
        podcast = podcasts[2]
        title = podcast.get('title', 'Untitled')
        summary = podcast.get('summary', '')
        url = podcast.get('url', '#')
        release_date = podcast.get('release_date', '')
        podcasts_col2_html += f'''
        <div class="news-card p-4 rounded-lg border border-gray-100">
            <div class="mb-2 flex justify-between items-center">
                <span class="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">Podcast</span>
                <span class="text-xs text-gray-500">{release_date}</span>
            </div>
            <h3 class="text-lg font-medium text-gray-900 mb-2 leading-tight">
                <a href="{url}" target="_blank" class="hover:text-primary-600">{title}</a>
            </h3>
            <p class="text-sm text-gray-600 mb-3">{summary}</p>
            <a href="{url}" target="_blank" class="text-primary-600 hover:text-primary-800 text-sm font-medium flex items-center">
                <i class="fas fa-play mr-1"></i> Listen
            </a>
        </div>
        '''
    # Note: Your template only shows one podcast here (podcasts[2]). If you intended more, adjust accordingly.
    content = content.replace('<!-- PODCASTS_COLUMN_2_PLACEHOLDER -->', podcasts_col2_html)
    
    # Clean up any leftover Jinja-like template variables if any were missed (should not be necessary for data)
    content = re.sub(r'{{\\s*.*?\\s*}}', '', content) # For {{ variable }}
    content = re.sub(r'{%\\s*.*?\\s*%}', '', content, flags=re.DOTALL) # For {% logic %}

    # Write the static HTML
    with open('static_site/index.html', 'w') as f:
        f.write(content)
    
    # Also write to root index.html for immediate preview
    with open('index.html', 'w') as f:
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