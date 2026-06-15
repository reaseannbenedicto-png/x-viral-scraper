# Configuration for X Viral Scraper

# Keywords to search for viral tweets
KEYWORDS = [
    "success",
    "AI",
    "artificial intelligence",
    "passive income",
    "side hustle"
]

# Time range in hours
HOURS_BACK = 6

# Minimum engagement threshold for "viral" classification
MIN_LIKES = 50
MIN_RETWEETS = 20
MIN_REPLIES = 5

# Output settings
OUTPUT_DIR = "results"
OUTPUT_FORMAT = "json"  # or "csv"

# Rate limiting
DELAY_BETWEEN_REQUESTS = 0.5  # seconds

# Maximum tweets per keyword search
MAX_TWEETS_PER_KEYWORD = 500
