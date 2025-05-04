import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import traceback
import re

class PodcastScraper:
    def __init__(self, client_id: str, client_secret: str):
        """Initialize Spotify client with credentials"""
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        self.show_id = "4C5Qx3wJn0GeTnDxIVYcAR"  # The Energy Gang podcast ID
        
        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('stopwords')
        self.stop_words = set(stopwords.words('english'))
    
    def summarize_text(self, text: str, num_sentences: int = 4) -> str:
        """Generate a high-quality summary focused on key information"""
        try:
            # If content is too short, return it as is
            if len(text) < 200:
                return text
                
            # Tokenize content into sentences
            sentences = sent_tokenize(text)
            if len(sentences) <= num_sentences:
                return text
            
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
            words = word_tokenize(text.lower())
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
            return text[:300] + '...' if len(text) > 300 else text
    
    def filter_recent_episodes(self, episodes: List[Dict], days: int = 30) -> List[Dict]:
        """Filter and deduplicate recent episodes"""
        try:
            # Convert dates to datetime objects
            for episode in episodes:
                if isinstance(episode['release_date'], str):
                    episode['release_date'] = datetime.strptime(episode['release_date'], '%Y-%m-%d')
            
            # Filter by date
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_episodes = [
                episode for episode in episodes 
                if episode['release_date'] >= cutoff_date
            ]
            
            # Deduplicate similar content
            unique_episodes = []
            seen_titles = set()
            for episode in recent_episodes:
                # Create a simplified version of the title for comparison
                simple_title = ''.join(
                    c.lower() for c in episode['title'] 
                    if c.isalnum()
                )
                
                # Check if we've seen a similar title
                if not any(
                    len(set(simple_title) & set(seen)) / len(set(simple_title) | set(seen)) > 0.8
                    for seen in seen_titles
                ):
                    unique_episodes.append(episode)
                    seen_titles.add(simple_title)
            
            return unique_episodes
        except Exception as e:
            print(f"Error filtering episodes: {str(e)}")
            traceback.print_exc()
            return episodes
    
    def get_latest_episodes(self, limit: int = 10) -> List[Dict]:
        """Get the latest episodes of the podcast with improved handling"""
        try:
            print("Fetching podcast episodes...")
            results = self.sp.show_episodes(self.show_id, limit=limit)
            episodes = []
            
            for episode in results['items']:
                try:
                    # Convert release date to datetime
                    release_date = datetime.strptime(episode['release_date'], '%Y-%m-%d')
                    
                    # Skip episodes older than 30 days
                    if datetime.now() - release_date > timedelta(days=30):
                        continue
                    
                    # Clean and summarize description
                    description = episode['description'].replace('\n', ' ').strip()
                    summary = self.summarize_text(description)
                    
                    episodes.append({
                        'title': episode['name'],
                        'description': description,
                        'summary': summary,
                        'release_date': episode['release_date'],
                        'duration_ms': episode['duration_ms'],
                        'url': episode['external_urls']['spotify'],
                        'source': 'The Energy Gang Podcast',
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as e:
                    print(f"Error processing episode {episode.get('name', 'Unknown')}: {str(e)}")
                    traceback.print_exc()
                    continue
            
            # Filter and deduplicate episodes
            episodes = self.filter_recent_episodes(episodes)
            
            print(f"Successfully fetched {len(episodes)} recent podcast episodes")
            return episodes
            
        except Exception as e:
            print(f"Error fetching podcast episodes: {str(e)}")
            traceback.print_exc()
            return []
    
    def save_episodes(self, episodes: List[Dict], filename: str):
        """Save episodes to a JSON file"""
        try:
            # Convert datetime objects to strings
            serializable_episodes = []
            for episode in episodes:
                episode_copy = episode.copy()
                if isinstance(episode_copy.get('release_date'), datetime):
                    episode_copy['release_date'] = episode_copy['release_date'].strftime('%Y-%m-%d')
                if isinstance(episode_copy.get('timestamp'), datetime):
                    episode_copy['timestamp'] = episode_copy['timestamp'].isoformat()
                serializable_episodes.append(episode_copy)
            
            os.makedirs('data', exist_ok=True)
            with open(f'data/{filename}', 'w') as f:
                json.dump(serializable_episodes, f, indent=2)
            print(f"Successfully saved {len(episodes)} episodes to {filename}")
        except Exception as e:
            print(f"Error saving episodes: {str(e)}")
            traceback.print_exc()
    
    def load_episodes(self, filename: str) -> List[Dict]:
        """Load episodes from a JSON file"""
        try:
            with open(f'data/{filename}', 'r') as f:
                episodes = json.load(f)
            print(f"Successfully loaded {len(episodes)} episodes from {filename}")
            return episodes
        except FileNotFoundError:
            print(f"No episodes file found at {filename}")
            return []
        except Exception as e:
            print(f"Error loading episodes: {str(e)}")
            traceback.print_exc()
            return [] 