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
import feedparser
import openai

class PodcastScraper:
    def __init__(self): # Removed client_id and client_secret
        """Initialize Podcast Scraper"""
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        self.stop_words = set(stopwords.words('english'))
        self.rss_feed_url = "https://feeds.megaphone.fm/catalyst"
        self.whisper_model = None # To be loaded on demand

    def _load_whisper_model(self):
        import whisper # <-- IMPORT WHISPER HERE
        if self.whisper_model is None:
            try:
                print("Loading Whisper model (base.en)... This might take a moment on first run.")
                self.whisper_model = whisper.load_model("base.en")
                print("Whisper model loaded successfully.")
            except Exception as e:
                print(f"Error loading Whisper model: {str(e)}")
                traceback.print_exc()
                # Potentially raise an error or handle it so transcription is skipped
        return self.whisper_model

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
    
    def get_latest_episodes(self, limit: int = 5) -> List[Dict]: # Reduced limit for testing/daily runs
        """Get latest podcast episodes from RSS, download audio, and transcribe."""
        print(f"Fetching podcast episodes from RSS feed: {self.rss_feed_url}")
        feed = feedparser.parse(self.rss_feed_url)
        
        if feed.bozo:
            print(f"Error parsing RSS feed: {feed.bozo_exception}")
            return []

        episodes_data = []
        model = self._load_whisper_model()
        if not model:
            print("Whisper model not loaded, cannot transcribe. Returning episodes without transcripts.")
            # Fallback to just getting metadata if transcription fails to load
            for entry in feed.entries[:limit]:
                release_date_parsed = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                episodes_data.append({
                    'title': entry.title if hasattr(entry, 'title') else "Untitled Episode",
                    'description': entry.summary if hasattr(entry, 'summary') else "",
                    'summary': self.summarize_text(entry.summary if hasattr(entry, 'summary') else ""),
                    'release_date': release_date_parsed.strftime('%Y-%m-%d'),
                    'duration_ms': 0, # Not easily available from all RSS, can parse entry.itunes_duration
                    'url': entry.link if hasattr(entry, 'link') else "",
                    'audio_url': next((link.href for link in entry.links if link.type.startswith('audio/')), None),
                    'transcript': "Transcription failed or model not loaded.",
                    'source': feed.feed.title if hasattr(feed.feed, 'title') else 'Catalyst Podcast RSS',
                    'timestamp': datetime.now().isoformat()
                })
            return self.filter_recent_episodes(episodes_data)

        for entry in feed.entries[:limit]:
            print(f"Processing episode: {entry.title if hasattr(entry, 'title') else 'Untitled'}")
            audio_url = None
            if hasattr(entry, 'enclosures'):
                for enclosure in entry.enclosures:
                    if enclosure.type.startswith('audio/'):
                        audio_url = enclosure.href
                        break
            
            if not audio_url: # Fallback to links if no enclosure
                 if hasattr(entry, 'links'):
                    audio_url = next((link.href for link in entry.links if link.type.startswith('audio/')), None)

            transcript_text = "Audio URL not found or transcription skipped."
            description_text = entry.summary if hasattr(entry, 'summary') else ""
            current_summary = "Summary not generated." # Default

            if audio_url:
                try:
                    print(f"Downloading audio from: {audio_url}")
                    audio_response = requests.get(audio_url, timeout=30) # Increased timeout
                    audio_response.raise_for_status()
                    
                    # Save temporary audio file
                    temp_audio_filename = "temp_podcast_audio.m4a" # Or determine extension
                    with open(temp_audio_filename, 'wb') as f:
                        f.write(audio_response.content)
                    print(f"Audio downloaded to {temp_audio_filename}")

                    print("Starting transcription...")
                    # Ensure API key is set if using OpenAI's API directly (Whisper model might use it implicitly)
                    # openai.api_key = os.getenv("OPENAI_API_KEY") # Uncomment if direct API calls are made elsewhere for transcription
                    result = model.transcribe(temp_audio_filename)
                    transcript_text = result["text"]
                    print("Transcription complete.")
                    
                    os.remove(temp_audio_filename) # Clean up
                    print(f"Temporary audio file {temp_audio_filename} removed.")

                except requests.exceptions.RequestException as req_e:
                    print(f"Error downloading audio for {entry.title if hasattr(entry, 'title') else 'Untitled'}: {str(req_e)}")
                    traceback.print_exc() # Add traceback for download errors
                    transcript_text = "Audio download failed."
                except Exception as e:
                    print(f"Error during transcription for {entry.title if hasattr(entry, 'title') else 'Untitled'}: {type(e).__name__} - {str(e)}")
                    traceback.print_exc()  # This will print the full traceback
                    transcript_text = "Transcription failed."
                    if os.path.exists("temp_podcast_audio.m4a"):
                        os.remove("temp_podcast_audio.m4a")

            if transcript_text and transcript_text not in ["Audio URL not found or transcription skipped.", "Audio download failed.", "Transcription failed.", "Transcription failed or model not loaded."]:
                print(f"Attempting LLM summary from transcript for: {entry.title if hasattr(entry, 'title') else 'Untitled'}")
                current_summary = self.summarize_transcript_with_llm(transcript_text)
                
                # Fallback to NLTK summary of transcript if LLM summary failed or wasn't suitable
                if current_summary in ["Summary not available.", "LLM Summary not available (API key missing).", "LLM summary generation failed."]:
                    print(f"LLM summary failed or not suitable. Falling back to NLTK summary of transcript for: {entry.title if hasattr(entry, 'title') else 'Untitled'}")
                    current_summary = self.summarize_text(transcript_text, num_sentences=5)
            else:
                # Fallback to summarizing the original description if transcript is unavailable
                print(f"Transcript not available. Generating summary from description for: {entry.title if hasattr(entry, 'title') else 'Untitled'}")
                current_summary = self.summarize_text(description_text, num_sentences=3)

            release_date_parsed = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
            
            episodes_data.append({
                'title': entry.title if hasattr(entry, 'title') else "Untitled Episode",
                'description': description_text, # Keep original description
                'summary': current_summary, # This will now prioritize LLM summary
                'transcript': transcript_text,
                'release_date': release_date_parsed.strftime('%Y-%m-%d'),
                'duration_ms': self.parse_duration(getattr(entry, 'itunes_duration', '0')) * 1000,
                'url': entry.link if hasattr(entry, 'link') else audio_url, 
                'source': feed.feed.title if hasattr(feed.feed, 'title') else 'Catalyst Podcast RSS',
                'timestamp': datetime.now().isoformat()
            })

        return self.filter_recent_episodes(episodes_data) # Apply existing filter

    def parse_duration(self, duration_str: str) -> int:
        """Parse itunes:duration string (HH:MM:SS, MM:SS, or S) into seconds."""
        parts = list(map(int, duration_str.split(':')))
        seconds = 0
        if len(parts) == 3: # HH:MM:SS
            seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2: # MM:SS
            seconds = parts[0] * 60 + parts[1]
        elif len(parts) == 1: # S
            seconds = parts[0]
        return seconds

    def filter_recent_episodes(self, episodes: List[Dict], days: int = 30) -> List[Dict]:
        """Filter and deduplicate recent episodes"""
        try:
            # Convert dates to datetime objects if they are strings
            for episode in episodes:
                if isinstance(episode.get('release_date'), str):
                    try:
                        episode['release_date_dt'] = datetime.strptime(episode['release_date'], '%Y-%m-%d')
                    except ValueError:
                         # Handle cases where date might be in a different format or invalid
                        print(f"Warning: Could not parse date for episode {episode.get('title')}: {episode.get('release_date')}")
                        episode['release_date_dt'] = datetime.now() # Default to now if parsing fails
                elif isinstance(episode.get('release_date'), datetime):
                     episode['release_date_dt'] = episode['release_date']
                else: # if 'release_date' field doesn't exist or is not recognized type
                    episode['release_date_dt'] = datetime.now()

            cutoff_date = datetime.now() - timedelta(days=days)
            recent_episodes = [
                episode for episode in episodes
                if episode.get('release_date_dt', datetime.now()) >= cutoff_date # Use .get for safety
            ]

            # Deduplicate similar content (simple title check for now)
            unique_episodes = []
            seen_titles = set()
            for episode in recent_episodes:
                simple_title = ''.join(c.lower() for c in episode['title'] if c.isalnum())
                # A more robust check might involve GUIDs from RSS if available (entry.id)
                # For now, keeping title similarity
                is_similar = False
                for seen in seen_titles:
                    # Basic similarity: if one title is a substring of another or very close
                    # This could be improved with fuzzy matching if needed
                    if simple_title in seen or seen in simple_title or \
                       len(set(simple_title) & set(seen)) / len(set(simple_title) | set(seen)) > 0.8:
                        is_similar = True
                        break
                if not is_similar:
                    unique_episodes.append(episode)
                    seen_titles.add(simple_title)
            
            # Clean up the temporary datetime object
            for episode in unique_episodes:
                if 'release_date_dt' in episode:
                    del episode['release_date_dt']

            return unique_episodes
        except Exception as e:
            print(f"Error filtering episodes: {str(e)}")
            traceback.print_exc()
            return episodes # Return original list if filtering fails
    
    def save_episodes(self, episodes: List[Dict], filename: str):
        """Save episodes to a JSON file"""
        try:
            # Convert datetime objects to strings
            serializable_episodes = []
            for episode in episodes:
                episode_copy = episode.copy()
                if isinstance(episode_copy.get('release_date'), datetime):
                    episode_copy['release_date'] = episode_copy['release_date'].strftime('%Y-%m-%d')
                # Ensure 'timestamp' is also stringified if it's a datetime object
                if isinstance(episode_copy.get('timestamp'), datetime):
                     episode_copy['timestamp'] = episode_copy['timestamp'].isoformat()
                serializable_episodes.append(episode_copy)
            
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Save to both root and data directory for compatibility
            # Root location
            with open(filename, 'w') as f:
                json.dump(serializable_episodes, f, indent=2)
            
            # Data directory
            with open(os.path.join('data', filename), 'w') as f:
                json.dump(serializable_episodes, f, indent=2)
            
            print(f"Successfully saved {len(episodes)} episodes to {filename}")
        except Exception as e:
            print(f"Error saving episodes: {str(e)}")
            traceback.print_exc()
    
    def load_episodes(self, filename: str) -> List[Dict]:
        """Load episodes from a JSON file"""
        try:
            # Try loading from root first, then from data directory
            try:
                with open(filename, 'r') as f:
                    episodes = json.load(f)
            except FileNotFoundError:
                with open(os.path.join('data', filename), 'r') as f:
                    episodes = json.load(f)
                
            return episodes
        except Exception as e:
            print(f"Error loading episodes: {str(e)}")
            traceback.print_exc()
            return []

    def summarize_transcript_with_llm(self, transcript_text: str) -> str:
        if not transcript_text or len(transcript_text.split()) < 30: # Min length for meaningful summary
            print("Transcript too short for LLM summarization or not available.")
            return "Summary not available."

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("OPENAI_API_KEY not found in environment. Skipping LLM summarization.")
            return "LLM Summary not available (API key missing)."
        
        openai.api_key = api_key
        # Shorten transcript if it's too long to reduce token usage/cost
        # OpenAI's gpt-3.5-turbo has a context window (e.g., 4k or 16k tokens)
        # 1 token is roughly 3/4 of a word.
        max_input_chars = 20000 # Approx 5000 tokens, adjust as needed
        truncated_transcript = transcript_text[:max_input_chars]

        try:
            print(f"Attempting OpenAI API call for summarization. Transcript length (chars): {len(truncated_transcript)}")
            print(f"Sending transcript (truncated to {len(truncated_transcript)} chars) to LLM for summarization...")
            completion = openai.chat.completions.create(
                model="gpt-3.5-turbo", # Or another cost-effective model
                messages=[
                    {"role": "system", "content": "You are an expert at summarizing podcast transcripts. Provide a concise, engaging summary of the key topics discussed in about 100-150 words."},
                    {"role": "user", "content": f"Summarize this podcast transcript:\n\n{truncated_transcript}"}
                ],
                max_tokens=200, # Max tokens for the summary itself
                temperature=0.6,
            )
            llm_summary = completion.choices[0].message.content.strip()
            print("LLM summary generated.")
            return llm_summary
        except openai.RateLimitError as rle:
            print(f"OpenAI API rate limit hit during summarization: {str(rle)}")
            return "LLM summary failed due to rate limit."
        except Exception as e:
            print(f"Error during LLM summarization: {str(e)}")
            traceback.print_exc() # Add traceback for other LLM errors
            return "LLM summary generation failed." 