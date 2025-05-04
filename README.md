# Energy Sector Dashboard

A dashboard aggregating energy news from Canary Media, Utility Dive, and The Energy Gang podcast.

## Automatic Updates

This dashboard **updates automatically every day** using GitHub Actions. No manual intervention is required to keep the content fresh.

## Viewing the Dashboard

The dashboard is hosted on GitHub Pages at:
`https://YOUR_USERNAME.github.io/energy-dashboard/`

## How It Works

1. A scheduled GitHub Action runs daily
2. It collects the latest energy news and podcast episodes
3. It generates the static dashboard site
4. It deploys the updated content to GitHub Pages

## Setup Instructions (For Repository Owner)

### Initial Setup

1. Create a GitHub repository for this project
2. Push all the code to the repository
3. Add Spotify API credentials as secrets in the repository:
   - Go to Settings > Secrets and variables > Actions
   - Add `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`
4. GitHub Actions will automatically deploy the site to GitHub Pages

### Manual Update (If Needed)

You can manually trigger an update:
1. Go to the Actions tab in your repository
2. Select the "Update Dashboard Content" workflow
3. Click "Run workflow"

## Features

- Aggregates content from multiple energy news sources
- Categorizes articles by topic (policy, innovation, business, climate)
- Provides high-quality summaries of key information
- Filters for recent content only
- Modern, aesthetically pleasing interface

## Project Structure

- `main.py`: Flask application and routes
- `scraper/`: Contains modules for scraping and processing content
  - `web_scraper.py`: Scrapes articles from websites
  - `podcast_scraper.py`: Fetches podcast episodes
  - `summarizer.py`: Processes and summarizes content
- `templates/`: HTML templates
- `data/`: Stores scraped and processed content
- `static/`: Static assets (CSS, JS, etc.)

## Dependencies

- Flask: Web framework
- BeautifulSoup4: Web scraping
- Spotipy: Spotify API client
- Transformers: AI text summarization
- Schedule: Daily updates
- Python-dotenv: Environment variable management 