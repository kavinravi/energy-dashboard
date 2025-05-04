FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Download NLTK data
RUN python -m nltk.downloader punkt stopwords

# Create necessary directories
RUN mkdir -p data logs

# Expose the port
EXPOSE 9000

# Run the application
CMD ["python", "main.py"] 