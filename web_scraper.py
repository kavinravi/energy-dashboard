import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict
import traceback
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import re

class WebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('stopwords')
        self.stop_words = set(stopwords.words('english'))
        
        # Site-specific selectors
        self.site_selectors = {
            'canarymedia.com': {
                'content': ['div.article-content', 'div.post-content'],
                'exclude': ['div.newsletter-signup', 'div.social-share', 'div.related-content'],
                'date': ['time.entry-date', 'span.date']
            },
            'utilitydive.com': {
                'content': ['div.article-body', 'div.content-body'],
                'exclude': ['div.related-articles', 'div.advertisement', 'div.sidebar'],
                'date': ['time.published', 'span.date']
            }
        }
    
    def get_article_content(self, url: str) -> str:
        """Get the full content of an article with improved extraction"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get domain-specific selectors
            domain = url.split('/')[2]
            selectors = next((v for k, v in self.site_selectors.items() if k in domain), None)
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            if selectors:
                # Remove site-specific unwanted elements
                for exclude_selector in selectors['exclude']:
                    for element in soup.select(exclude_selector):
                        element.decompose()
                
                # Try site-specific content selectors
                for content_selector in selectors['content']:
                    content_element = soup.select_one(content_selector)
                    if content_element:
                        break
            else:
                # Fallback to generic selectors
                content_element = (
                    soup.find('div', class_='article-content') or
                    soup.find('div', class_='content') or
                    soup.find('article') or
                    soup.find('main')
                )
            
            if content_element:
                # Extract paragraphs and clean content
                paragraphs = content_element.find_all('p')
                content = ' '.join(
                    p.text.strip() 
                    for p in paragraphs 
                    if p.text.strip() and len(p.text.strip()) > 50  # Filter out short snippets
                )
                return content
            return ''
        except Exception as e:
            print(f"Error getting article content from {url}: {str(e)}")
            traceback.print_exc()
            return ''
    
    def extract_date(self, article_element, domain: str = None) -> datetime:
        """Extract date from article element with improved parsing"""
        try:
            selectors = self.site_selectors.get(domain, {}).get('date', []) if domain else []
            
            # Try site-specific date selectors first
            for selector in selectors:
                date_element = article_element.select_one(selector)
                if date_element:
                    break
            
            # Fallback to generic selectors
            if not date_element:
                date_element = (
                    article_element.find('time') or
                    article_element.find('span', class_='date') or
                    article_element.find('div', class_='date')
                )
            
            if date_element:
                if date_element.get('datetime'):
                    return datetime.fromisoformat(date_element['datetime'].split('T')[0])
                elif date_element.text:
                    date_text = date_element.text.strip()
                    # Try multiple date formats
                    for date_format in ['%B %d, %Y', '%Y-%m-%d', '%d %B %Y', '%m/%d/%Y']:
                        try:
                            return datetime.strptime(date_text, date_format)
                        except ValueError:
                            continue
            
            # If no date found or parsing failed, return current date
            return datetime.now()
        except Exception:
            return datetime.now()
    
    def summarize_content(self, content: str, num_sentences: int = 4) -> str:
        """Generate a high-quality summary focused on key information"""
        try:
            # If content is too short, return it as is
            if len(content) < 200:
                return content
                
            # Tokenize content into sentences
            sentences = sent_tokenize(content)
            if len(sentences) <= num_sentences:
                return content
            
            # Define keywords related to important energy sector developments
            energy_keywords = {
                # Business and financial terms
                'acquisition': 3.0, 'merger': 3.0, 'investment': 2.5, 'funding': 2.5, 
                'billion': 2.5, 'million': 2.0, 'profit': 2.0, 'revenue': 2.0, 'growth': 2.0,
                'budget': 2.0, 'cost': 1.5, 'price': 1.5, 'market': 1.5, 'stock': 1.5,
                
                # Technology and innovation
                'innovation': 3.0, 'technology': 2.5, 'breakthrough': 3.0, 'efficiency': 2.5, 
                'development': 2.0, 'research': 2.0, 'discovery': 2.5, 'patent': 2.5,
                'prototype': 2.5, 'launch': 2.0, 'announce': 2.0, 'introduce': 2.0,
                
                # Energy sources
                'renewable': 2.5, 'solar': 2.0, 'wind': 2.0, 'hydro': 2.0, 'nuclear': 2.0,
                'battery': 2.5, 'storage': 2.5, 'grid': 2.0, 'power': 1.5, 'electricity': 1.5,
                'energy': 1.5, 'oil': 1.5, 'gas': 1.5, 'coal': 1.5, 'hydrogen': 2.5,
                
                # Policy and regulation
                'policy': 2.5, 'regulation': 2.5, 'law': 2.5, 'legislation': 2.5, 
                'government': 2.0, 'epa': 2.5, 'subsidy': 2.5, 'incentive': 2.5,
                'tax': 2.0, 'carbon': 2.5, 'emissions': 2.5, 'climate': 2.0,
                
                # Key events and time indicators
                'announce': 2.0, 'report': 2.0, 'release': 2.0, 'unveil': 2.5,
                'today': 2.0, 'yesterday': 2.0, 'week': 1.5, 'month': 1.5, 'year': 1.5
            }
            
            # Tokenize words and remove stopwords
            words = word_tokenize(content.lower())
            words = [word for word in words if word.isalnum() and word not in self.stop_words]
            
            # Calculate word frequencies
            freq_dist = {}
            for word in words:
                freq_dist[word] = freq_dist.get(word, 0) + 1
            
            max_freq = max(freq_dist.values()) if freq_dist else 1
            
            # Score sentences based on multiple factors
            sentence_scores = {}
            entity_pattern = r'([A-Z][a-z]+ )+(?:Inc\.?|LLC|Ltd\.?|Corp\.?|Corporation|Company|Group|Technologies|Energy|Solar|Wind|Power)'
            
            for idx, sentence in enumerate(sentences):
                # Position weights (first few and last few sentences often contain key info)
                position_weight = 1.5 if idx < 2 or idx > len(sentences) - 3 else 1.0
                
                # Presence of entities (companies, organizations)
                entity_weight = 1.5 if re.search(entity_pattern, sentence) else 1.0
                
                # Length weight (prefer medium-sized sentences)
                length = len(sentence.split())
                length_weight = 1.2 if 10 <= length <= 25 else 0.8 if length > 40 else 1.0
                
                # Calculate base score from word frequencies
                score = 0
                for word in word_tokenize(sentence.lower()):
                    # Apply special weighting for energy sector keywords
                    if word in energy_keywords:
                        score += freq_dist.get(word, 0) * energy_keywords[word]
                    elif word in freq_dist:
                        score += freq_dist[word]
                
                # Normalize score by sentence length to avoid favoring long sentences
                base_score = score / max(1, length)
                
                # Apply all weights
                sentence_scores[sentence] = base_score * position_weight * entity_weight * length_weight
                
                # Boost sentences containing numbers (often indicate key metrics)
                if re.search(r'\d+', sentence):
                    sentence_scores[sentence] *= 1.3
                
                # Boost sentences with quotes (often contain important statements)
                if re.search(r'"[^"]+"', sentence) or re.search(r"'[^']+'", sentence):
                    sentence_scores[sentence] *= 1.4
            
            # Get top sentences and sort them by original order
            top_sentences = sorted(
                sentence_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:num_sentences]
            
            top_sentences.sort(key=lambda x: sentences.index(x[0]))
            
            # Create cohesive summary
            summary = ' '.join(sentence for sentence, _ in top_sentences)
            
            # If the summary is too short, add more sentences
            if len(summary) < 200 and len(sentences) > num_sentences:
                additional_sentences = sorted(
                    [(s, score) for s, score in sentence_scores.items() if s not in [sent for sent, _ in top_sentences]],
                    key=lambda x: x[1],
                    reverse=True
                )[:2]
                
                # Add these sentences in original order
                all_sentences = top_sentences + additional_sentences
                all_sentences.sort(key=lambda x: sentences.index(x[0]))
                summary = ' '.join(sentence for sentence, _ in all_sentences)
            
            return summary
        except Exception as e:
            print(f"Error in summarization: {str(e)}")
            traceback.print_exc()
            return content[:300] + '...' if len(content) > 300 else content
    
    def filter_recent_content(self, articles: List[Dict], days: int = 7) -> List[Dict]:
        """Filter and deduplicate recent content"""
        try:
            # Convert dates to datetime objects
            for article in articles:
                if isinstance(article['date'], str):
                    article['date'] = datetime.strptime(article['date'], '%Y-%m-%d')
            
            # Filter by date
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_articles = [
                article for article in articles 
                if article['date'] >= cutoff_date
            ]
            
            # Deduplicate similar content
            unique_articles = []
            seen_titles = set()
            for article in recent_articles:
                # Create a simplified version of the title for comparison
                simple_title = ''.join(
                    c.lower() for c in article['title'] 
                    if c.isalnum()
                )
                
                # Check if we've seen a similar title
                if not any(
                    len(set(simple_title) & set(seen)) / len(set(simple_title) | set(seen)) > 0.8
                    for seen in seen_titles
                ):
                    unique_articles.append(article)
                    seen_titles.add(simple_title)
            
            return unique_articles
        except Exception as e:
            print(f"Error filtering content: {str(e)}")
            return articles
    
    def scrape_canary_media(self) -> List[Dict]:
        """Scrape latest articles from Canary Media"""
        try:
            print("Scraping Canary Media...")
            url = "https://www.canarymedia.com/"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            print(f"Response status code: {response.status_code}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []
            
            # Try different selectors
            article_elements = (
                soup.find_all('article') or 
                soup.find_all('div', class_='article') or
                soup.find_all('div', class_='post')
            )
            
            print(f"Found {len(article_elements)} article elements")
            
            for article in article_elements:
                # Get article date
                article_date = self.extract_date(article)
                # Skip articles older than 7 days
                if datetime.now() - article_date > timedelta(days=7):
                    continue
                
                # Get title and link
                title_element = (
                    article.find('h2') or 
                    article.find('h3') or
                    article.find('div', class_='title')
                )
                title = title_element.text.strip() if title_element else ''
                
                link_element = article.find('a')
                link = link_element['href'] if link_element else ''
                if link and not link.startswith('http'):
                    link = f"https://www.canarymedia.com{link}"
                
                if title and link:
                    # Get full article content
                    content = self.get_article_content(link)
                    summary = self.summarize_content(content) if content else ''
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'summary': summary,
                        'source': 'Canary Media',
                        'date': article_date.strftime('%Y-%m-%d'),
                        'timestamp': datetime.now().isoformat()
                    })
            
            print(f"Successfully scraped {len(articles)} recent articles from Canary Media")
            return articles
            
        except Exception as e:
            print(f"Error scraping Canary Media: {str(e)}")
            traceback.print_exc()
            return []
    
    def scrape_utility_dive(self) -> List[Dict]:
        """Scrape latest articles from Utility Dive"""
        try:
            print("Scraping Utility Dive...")
            url = "https://www.utilitydive.com/"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            print(f"Response status code: {response.status_code}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []
            
            # Try different selectors
            article_elements = (
                soup.find_all('div', class_='feed__item') or
                soup.find_all('div', class_='article-card') or
                soup.find_all('article')
            )
            
            print(f"Found {len(article_elements)} article elements")
            
            for article in article_elements:
                # Get article date
                article_date = self.extract_date(article)
                # Skip articles older than 7 days
                if datetime.now() - article_date > timedelta(days=7):
                    continue
                
                # Get title and link
                title_element = (
                    article.find('h3') or
                    article.find('h2') or
                    article.find('div', class_='title')
                )
                title = title_element.text.strip() if title_element else ''
                
                link_element = article.find('a')
                link = link_element['href'] if link_element else ''
                if link and not link.startswith('http'):
                    link = f"https://www.utilitydive.com{link}"
                
                if title and link:
                    # Get full article content
                    content = self.get_article_content(link)
                    summary = self.summarize_content(content) if content else ''
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'summary': summary,
                        'source': 'Utility Dive',
                        'date': article_date.strftime('%Y-%m-%d'),
                        'timestamp': datetime.now().isoformat()
                    })
            
            print(f"Successfully scraped {len(articles)} recent articles from Utility Dive")
            return articles
            
        except Exception as e:
            print(f"Error scraping Utility Dive: {str(e)}")
            traceback.print_exc()
            return []
    
    def save_articles(self, articles: List[Dict], filename: str):
        """Save articles to a JSON file"""
        try:
            # Convert datetime objects to strings
            serializable_articles = []
            for article in articles:
                article_copy = article.copy()
                if isinstance(article_copy.get('date'), datetime):
                    article_copy['date'] = article_copy['date'].strftime('%Y-%m-%d')
                if isinstance(article_copy.get('timestamp'), datetime):
                    article_copy['timestamp'] = article_copy['timestamp'].isoformat()
                serializable_articles.append(article_copy)
            
            os.makedirs('data', exist_ok=True)
            with open(f'data/{filename}', 'w') as f:
                json.dump(serializable_articles, f, indent=2)
            print(f"Successfully saved {len(articles)} articles to {filename}")
        except Exception as e:
            print(f"Error saving articles: {str(e)}")
            traceback.print_exc()
    
    def load_articles(self, filename: str) -> List[Dict]:
        """Load articles from a JSON file"""
        try:
            with open(f'data/{filename}', 'r') as f:
                articles = json.load(f)
            print(f"Successfully loaded {len(articles)} articles from {filename}")
            return articles
        except FileNotFoundError:
            print(f"No articles file found at {filename}")
            return []
        except Exception as e:
            print(f"Error loading articles: {str(e)}")
            traceback.print_exc()
            return [] 