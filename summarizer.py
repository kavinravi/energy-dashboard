import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist
from typing import List, Dict
import json
import os

class ContentSummarizer:
    def __init__(self):
        """Initialize the NLTK-based summarizer"""
        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('stopwords')
        self.stop_words = set(stopwords.words('english'))
    
    def summarize_text(self, text: str, num_sentences: int = 3) -> str:
        """Summarize text using frequency-based extractive summarization"""
        # Tokenize the text into sentences
        sentences = sent_tokenize(text)
        
        if len(sentences) <= num_sentences:
            return text
        
        # Tokenize words and remove stopwords
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalnum() and word not in self.stop_words]
        
        # Calculate word frequencies
        freq_dist = FreqDist(words)
        
        # Score sentences based on word frequencies
        sentence_scores = {}
        for sentence in sentences:
            for word in word_tokenize(sentence.lower()):
                if word in freq_dist:
                    if sentence not in sentence_scores:
                        sentence_scores[sentence] = freq_dist[word]
                    else:
                        sentence_scores[sentence] += freq_dist[word]
        
        # Get top sentences
        summary_sentences = sorted(sentence_scores.items(), 
                                 key=lambda x: x[1], 
                                 reverse=True)[:num_sentences]
        
        # Sort sentences by their original order
        summary_sentences = sorted(summary_sentences, 
                                 key=lambda x: sentences.index(x[0]))
        
        # Join sentences
        summary = ' '.join(sentence for sentence, score in summary_sentences)
        return summary
    
    def process_articles(self, articles: List[Dict]) -> List[Dict]:
        """Process and summarize a list of articles"""
        processed_articles = []
        for article in articles:
            if 'content' in article and article['content']:
                summary = self.summarize_text(article['content'])
                article['summary'] = summary
            processed_articles.append(article)
        return processed_articles
    
    def process_podcast_transcript(self, transcript: str) -> str:
        """Process and summarize a podcast transcript"""
        return self.summarize_text(transcript, num_sentences=5)
    
    def process_podcast_episodes(self, episodes: List[Dict]) -> List[Dict]:
        """Process and summarize podcast episode descriptions"""
        summarized_episodes = []
        for episode in episodes:
            summary = self.summarize_text(episode['description'])
            summarized_episodes.append({
                'title': episode['title'],
                'url': episode['url'],
                'summary': summary,
                'source': episode['source'],
                'release_date': episode['release_date'],
                'timestamp': episode['timestamp']
            })
        return summarized_episodes
    
    def save_summaries(self, summaries: List[Dict], filename: str):
        """Save summaries to a JSON file"""
        os.makedirs('data', exist_ok=True)
        with open(f'data/{filename}', 'w') as f:
            json.dump(summaries, f, indent=2)
    
    def load_summaries(self, filename: str) -> List[Dict]:
        """Load summaries from a JSON file"""
        try:
            with open(f'data/{filename}', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return [] 