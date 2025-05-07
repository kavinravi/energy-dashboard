"""
Script to generate a static version of the energy dashboard.
This creates HTML files that can be hosted on GitHub Pages.
"""

import os
import json
import re
from datetime import datetime
import shutil
import pytz  # Add pytz for timezone handling

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
    pacific_tz = pytz.timezone('America/Los_Angeles')
    current_time_pst = datetime.now(pytz.utc).astimezone(pacific_tz)
    content = content.replace('{{ last_updated }}', current_time_pst.strftime("%Y-%m-%d %H:%M:%S %Z"))
    content = content.replace('{{ now.year }}', str(current_time_pst.year))

    # Helper function to generate a single article card HTML
    def generate_article_card(article):
        title = article.get('title', 'Untitled')
        summary = article.get('summary', '')
        link = article.get('link', '#')
        date = article.get('date', '')
        source = article.get('source', '')
        categories = article.get('categories', 'innovation,business') # Default categories
        # Clean up category string: remove newlines and ensure comma separation
        cleaned_categories = ",".join(c.strip() for c in categories.replace('\\n', ',').split(',') if c.strip())
        
        category_badges = ""
        for category_str in cleaned_categories.split(','):
            if not category_str: continue # Skip empty category strings
            category_name = {'policy': 'Policy', 'innovation': 'Innovation', 'business': 'Business', 'climate': 'Climate'}.get(category_str, category_str.capitalize())
            category_badges += f'<span class="category-badge category-{category_str}">{category_name}</span>\\n'
        
        return f'''
        <div class="news-card p-4 rounded-lg border border-gray-100" data-categories="{cleaned_categories}">
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

    # Helper function to generate a single podcast card HTML
    def generate_podcast_card(podcast):
        title = podcast.get('title', 'Untitled')
        summary = podcast.get('summary', 'LLM summary failed or not available.') # Default summary
        url = podcast.get('url', '#')
        release_date = podcast.get('release_date', '')
        return f'''
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

    # --- Main Content Sections ---
    articles_col1_html = "".join(generate_article_card(article) for article in articles[:3])
    content = content.replace('<!-- ARTICLES_COLUMN_1_PLACEHOLDER -->', articles_col1_html)

    podcasts_col1_html = "".join(generate_podcast_card(podcast) for podcast in podcasts[:2])
    content = content.replace('<!-- PODCASTS_COLUMN_1_PLACEHOLDER -->', podcasts_col1_html)

    article_col2_html = generate_article_card(articles[3]) if len(articles) > 3 else ""
    content = content.replace('<!-- ARTICLE_COLUMN_2_PLACEHOLDER -->', article_col2_html)

    article_col3_html = generate_article_card(articles[4]) if len(articles) > 4 else ""
    content = content.replace('<!-- ARTICLE_COLUMN_3_PLACEHOLDER -->', article_col3_html)
    
    podcasts_col2_html = generate_podcast_card(podcasts[2]) if len(podcasts) > 2 else ""
    content = content.replace('<!-- PODCASTS_COLUMN_2_PLACEHOLDER -->', podcasts_col2_html)

    # --- Sidebar Sections ---
    featured_podcast_html = ""
    if len(podcasts) > 3:
        podcast = podcasts[3]
        featured_podcast_html = f'''
        <div class="bg-white rounded-xl shadow-sm p-6">
            <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <span class="text-energy-yellow mr-2"><i class="fas fa-podcast"></i></span>
                Featured Podcast
            </h2>
            {generate_podcast_card(podcast)}
        </div>
        '''
    content = content.replace('<!-- FEATURED_PODCAST_PLACEHOLDER -->', featured_podcast_html)

    policy_update_article_html = ""
    if len(articles) > 5:
        article = articles[5]
        policy_update_article_html = f'''
        <div class="bg-white rounded-xl shadow-sm p-6">
            <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <span class="text-energy-blue mr-2"><i class="fas fa-newspaper"></i></span>
                Policy Update
            </h2>
            {generate_article_card(article)}
        </div>
        '''
    content = content.replace('<!-- POLICY_UPDATE_ARTICLE_PLACEHOLDER -->', policy_update_article_html)
    
    # Final cleanup of any stray template tags that were not replaced by placeholders
    # This specifically targets tags that might be left if a placeholder was missed or data was empty
    content = re.sub(r'<!-- [A-Z0-9_]+_PLACEHOLDER -->', '', content) # Remove any unfilled placeholders
    content = re.sub(r'{{\s*.*?\s*}}', '', content) # Remove {{ variable }} if data was missing for it
    # The {% if ... %} tags should ideally be handled by the conditional logic above (e.g. if len(articles) > X)
    # If some are still left, it indicates a mismatch between template structure and generation logic.
    # A more robust solution for complex templates is a proper templating engine like Jinja2.
    # For now, let's try a slightly more aggressive cleanup for leftover {% ... %} blocks if they are simple
    content = re.sub(r'{%\s*if.*?%}(.*?){%\s*endif\s*%}', lambda m: m.group(1) if "PLACEHOLDER" not in m.group(1) else "", content, flags=re.DOTALL)
    content = re.sub(r'{%\s*.*?\s*%}', '', content, flags=re.DOTALL) # General catch-all for other tags

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