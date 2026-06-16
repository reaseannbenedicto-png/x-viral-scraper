#!/usr/bin/env python3
"""
X Viral Scraper - Fetch viral tweets using RapidAPI Twitter v24
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


def calculate_virality_score(likes, retweets, replies):
    return (likes * 1) + (retweets * 3) + (replies * 2)


def is_viral(likes, retweets, replies):
    return likes >= MIN_LIKES or retweets >= MIN_RETWEETS or replies >= 10


def parse_tweets(data):
    """Parse the nested API response structure."""
    tweets = []
    try:
        instructions = (
            data["data"]["search_by_raw_query"]
            ["search_timeline"]["timeline"]["instructions"]
        )
        for instruction in instructions:
            entries = instruction.get("entries", [])
            for entry in entries:
                try:
                    item_content = entry.get("content", {}).get("itemContent", {})
                    if item_content.get("itemType") != "TimelineTweet":
                        continue

                    result = item_content["tweet_results"]["result"]
                    legacy = result.get("legacy", {})
                    user_legacy = (
                        result.get("core", {})
                        .get("user_results", {})
                        .get("result", {})
                        .get("legacy", {})
                    )

                    tweets.append({
                        "legacy": legacy,
                        "user_legacy": user_legacy,
                        "tweet_id": legacy.get("id_str", "")
                    })
                except (KeyError, TypeError):
                    continue
    except (KeyError, TypeError) as e:
        print(f"  ⚠️ Parse error: {e}")
    return tweets


def scrape_tweets(keywords, hours=HOURS_BACK, max_tweets=MAX_TWEETS_PER_KEYWORD):
    all_tweets = []
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

    headers = {
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

            raw_tweets = parse_tweets(data)
            count = 0

            for t in raw_tweets:
                legacy = t["legacy"]
                user_legacy = t["user_legacy"]

                likes = legacy.get("favorite_count", 0) or 0
                retweets = legacy.get("retweet_count", 0) or 0
                replies = legacy.get("reply_count", 0) or 0

                if not is_viral(likes, retweets, replies):
                    continue

                # Parse date
                created_at = legacy.get("created_at", "")
                try:
                    tweet_date = datetime.strptime(
                        created_at, "%a %b %d %H:%M:%S +0000 %Y"
                    ).replace(tzinfo=timezone.utc)
                    if tweet_date < cutoff_time:
                        continue
                    date_str = tweet_date.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    date_str = created_at

                username = user_legacy.get("screen_name", "unknown")
                tweet_data = {
                    "url": f"https://twitter.com/{username}/status/{t['tweet_id']}",
                    "date": date_str,
                    "username": f"@{username}",
                    "author_name": user_legacy.get("name", "Unknown"),
                    "content": legacy.get("full_text", ""),
                    "likes": likes,
                    "retweets": retweets,
                    "replies": replies,
                    "virality_score": calculate_virality_score(likes, retweets, replies),
                    "keyword": keyword
                }

                all_tweets.append(tweet_data)
                count += 1
                print(f"  ✓ Found tweet (Score: {tweet_data['virality_score']})")

            print(f"  ✅ Scraped {count} viral tweets for '{keyword}'")
            time.sleep(1)

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
