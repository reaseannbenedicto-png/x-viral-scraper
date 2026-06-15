#!/usr/bin/env python3
"""
X Viral Scraper - Fetch viral tweets using snscrape
No API key required!
"""

import snscrape.modules.twitter as sntwitter
import json
import csv
import os
from datetime import datetime, timedelta
import argparse
import time
from config import (
    KEYWORDS, HOURS_BACK, MIN_LIKES, MIN_RETWEETS, MIN_REPLIES,
    OUTPUT_DIR, OUTPUT_FORMAT, DELAY_BETWEEN_REQUESTS, MAX_TWEETS_PER_KEYWORD
)


def calculate_virality_score(tweet):
    """
    Calculate a simple virality score based on engagement metrics.
    """
    likes = tweet.likeCount or 0
    retweets = tweet.retweetCount or 0
    replies = tweet.replyCount or 0
    
    # Weighted score: retweets are more valuable for virality
    score = (likes * 1) + (retweets * 3) + (replies * 2)
    return score


def is_viral(tweet, min_likes=MIN_LIKES, min_retweets=MIN_RETWEETS, min_replies=MIN_REPLIES):
    """
    Determine if a tweet meets virality thresholds.
    """
    likes = tweet.likeCount or 0
    retweets = tweet.retweetCount or 0
    replies = tweet.replyCount or 0
    
    return likes >= min_likes or retweets >= min_retweets or replies >= min_replies


def is_within_timeframe(tweet, hours=HOURS_BACK):
    """
    Check if tweet was posted within the specified timeframe.
    """
    if tweet.date is None:
        return False
    
    cutoff_time = datetime.now(tweet.date.tzinfo) - timedelta(hours=hours)
    return tweet.date >= cutoff_time


def scrape_tweets(keywords, hours=HOURS_BACK, max_tweets=MAX_TWEETS_PER_KEYWORD):
    """
    Scrape tweets from multiple keywords.
    """
    all_tweets = []
    
    for keyword in keywords:
        print(f"\n🔍 Searching for: '{keyword}'")
        
        try:
            # Search query with language filter
            query = f"{keyword} lang:en -is:retweet"
            
            tweet_count = 0
            for tweet in sntwitter.TwitterSearchScraper(query).get_items():
                # Stop if we've reached max tweets
                if tweet_count >= max_tweets:
                    break
                
                # Only include tweets from the last N hours
                if not is_within_timeframe(tweet, hours):
                    continue
                
                # Only include viral tweets
                if not is_viral(tweet):
                    continue
                
                tweet_data = {
                    "url": f"https://twitter.com/{tweet.user.username}/status/{tweet.id}",
                    "date": tweet.date.strftime("%Y-%m-%d %H:%M:%S") if tweet.date else "Unknown",
                    "username": f"@{tweet.user.username}",
                    "author_name": tweet.user.displayname,
                    "content": tweet.content,
                    "likes": tweet.likeCount or 0,
                    "retweets": tweet.retweetCount or 0,
                    "replies": tweet.replyCount or 0,
                    "virality_score": calculate_virality_score(tweet),
                    "keyword": keyword
                }
                
                all_tweets.append(tweet_data)
                tweet_count += 1
                print(f"  ✓ Found tweet (Score: {tweet_data['virality_score']})")
                
                # Rate limiting
                time.sleep(DELAY_BETWEEN_REQUESTS)
            
            print(f"  ✅ Scraped {tweet_count} viral tweets for '{keyword}'")
            
        except Exception as e:
            print(f"  ❌ Error scraping '{keyword}': {e}")
    
    return all_tweets


def save_to_json(tweets, filename):
    """
    Save tweets to JSON file.
    """
    output = {
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_tweets": len(tweets),
        "tweets": sorted(tweets, key=lambda x: x['virality_score'], reverse=True)
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(tweets)} tweets to {filename}")


def save_to_csv(tweets, filename):
    """
    Save tweets to CSV file.
    """
    if not tweets:
        print("No tweets to save.")
        return
    
    sorted_tweets = sorted(tweets, key=lambda x: x['virality_score'], reverse=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted_tweets[0].keys())
        writer.writeheader()
        writer.writerows(sorted_tweets)
    
    print(f"\n✅ Saved {len(tweets)} tweets to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Scrape viral tweets from X')
    parser.add_argument('--keywords', type=str, default=','.join(KEYWORDS),
                       help='Keywords to search (comma-separated)')
    parser.add_argument('--hours', type=int, default=HOURS_BACK,
                       help='Search tweets from last N hours')
    parser.add_argument('--output', type=str, default=f'{OUTPUT_DIR}/viral_tweets.json',
                       help='Output file path')
    parser.add_argument('--format', type=str, default=OUTPUT_FORMAT,
                       choices=['json', 'csv'], help='Output format')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Parse keywords
    keywords = [k.strip() for k in args.keywords.split(',')]
    
    print("\n" + "="*50)
    print("🚀 X VIRAL SCRAPER")
    print("="*50)
    print(f"Keywords: {', '.join(keywords)}")
    print(f"Timeframe: Last {args.hours} hours")
    print(f"Output: {args.output}")
    print("="*50)
    
    # Scrape tweets
    tweets = scrape_tweets(keywords, hours=args.hours)
    
    if not tweets:
        print("\n❌ No viral tweets found.")
        return
    
    # Save results
    if args.format == 'json':
        save_to_json(tweets, args.output)
    else:
        save_to_csv(tweets, args.output)
    
    # Print top 5 viral tweets
    print("\n📊 TOP 5 MOST VIRAL TWEETS:")
    print("-" * 50)
    for i, tweet in enumerate(sorted(tweets, key=lambda x: x['virality_score'], reverse=True)[:5], 1):
        print(f"\n{i}. {tweet['author_name']} ({tweet['username']})")
        print(f"   Content: {tweet['content'][:100]}...")
        print(f"   Likes: {tweet['likes']} | Retweets: {tweet['retweets']} | Replies: {tweet['replies']}")
        print(f"   Virality Score: {tweet['virality_score']}")
        print(f"   URL: {tweet['url']}")


if __name__ == "__main__":
    main()
