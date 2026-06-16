#!/usr/bin/env python3
"""
X Viral Scraper - Fetch viral tweets using RapidAPI Twitter v24
No X API key required!
"""

import requests
import json
import os
from datetime import datetime, timedelta, timezone
import argparse
import time
from config import (
    KEYWORDS, HOURS_BACK, MIN_LIKES, MIN_RETWEETS,
    OUTPUT_DIR, MAX_TWEETS_PER_KEYWORD
)


RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
RAPIDAPI_HOST = "twitter-v24.p.rapidapi.com"


def calculate_virality_score(tweet):
    likes = tweet.get("favorite_count", 0) or 0
    retweets = tweet.get("retweet_count", 0) or 0
    replies = tweet.get("reply_count", 0) or 0
    return (likes * 1) + (retweets * 3) + (replies * 2)


def is_viral(tweet):
    likes = tweet.get("favorite_count", 0) or 0
    retweets = tweet.get("retweet_count", 0) or 0
    replies = tweet.get("reply_count", 0) or 0
    return likes >= MIN_LIKES or retweets >= MIN_RETWEETS or replies >= 10


def scrape_tweets(keywords, hours=HOURS_BACK, max_tweets=MAX_TWEETS_PER_KEYWORD):
    all_tweets = []
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }

    for keyword in keywords:
        print(f"\n🔍 Searching for: '{keyword}'")

        try:
            params = {
                "query": f"{keyword} lang:en -is:retweet",
                "section": "top",
                "limit": max_tweets
            }

            response = requests.get(
                "https://twitter-v24.p.rapidapi.com/search/",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()

            tweets = data.get("results", []) or data.get("tweets", []) or []

            count = 0
            for tweet in tweets:
                if not is_viral(tweet):
                    continue

                # Parse date if available
                created_at = tweet.get("creation_date") or tweet.get("created_at", "")
                try:
                    tweet_date = datetime.strptime(created_at, "%a %b %d %H:%M:%S +0000 %Y").replace(tzinfo=timezone.utc)
                    if tweet_date < cutoff_time:
                        continue
                    date_str = tweet_date.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    date_str = created_at

                user = tweet.get("user", {})
                tweet_data = {
                    "url": f"https://twitter.com/{user.get('username', 'unknown')}/status/{tweet.get('tweet_id', '')}",
                    "date": date_str,
                    "username": f"@{user.get('username', 'unknown')}",
                    "author_name": user.get("name", "Unknown"),
                    "content": tweet.get("text", ""),
                    "likes": tweet.get("favorite_count", 0) or 0,
                    "retweets": tweet.get("retweet_count", 0) or 0,
                    "replies": tweet.get("reply_count", 0) or 0,
                    "virality_score": calculate_virality_score(tweet),
                    "keyword": keyword
                }

                all_tweets.append(tweet_data)
                count += 1
                print(f"  ✓ Found tweet (Score: {tweet_data['virality_score']})")

            print(f"  ✅ Scraped {count} viral tweets for '{keyword}'")
            time.sleep(1)  # be gentle with the API

        except Exception as e:
            print(f"  ❌ Error scraping '{keyword}': {e}")

    return all_tweets


def main():
    parser = argparse.ArgumentParser(description='Scrape viral tweets from X')
    parser.add_argument('--keywords', type=str, default=','.join(KEYWORDS))
    parser.add_argument('--hours', type=int, default=HOURS_BACK)
    parser.add_argument('--output', type=str, default=f'{OUTPUT_DIR}/viral_tweets.json')
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    keywords = [k.strip() for k in args.keywords.split(',')]

    print("\n" + "="*50)
    print("🚀 X VIRAL SCRAPER (RapidAPI)")
    print("="*50)
    print(f"Keywords: {', '.join(keywords)}")
    print(f"Timeframe: Last {args.hours} hours")
    print("="*50)

    tweets = scrape_tweets(keywords, hours=args.hours)

    if not tweets:
        print("\n❌ No viral tweets found.")
        return

    output = {
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_tweets": len(tweets),
        "tweets": sorted(tweets, key=lambda x: x['virality_score'], reverse=True)
    }

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved {len(tweets)} tweets to {args.output}")

    print("\n📊 TOP 5 MOST VIRAL TWEETS:")
    print("-" * 50)
    for i, tweet in enumerate(output['tweets'][:5], 1):
        print(f"\n{i}. {tweet['author_name']} ({tweet['username']})")
        print(f"   Content: {tweet['content'][:100]}...")
        print(f"   Score: {tweet['virality_score']}")


if __name__ == "__main__":
    main()
