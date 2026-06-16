#!/usr/bin/env python3
"""
Extract top 3 viral trends from the latest scrape and update trends.json
"""

import json
import os
from datetime import datetime
from pathlib import Path

def get_latest_scrape():
    """Get the most recently created scrape file"""
    results_dir = Path("results")
    if not results_dir.exists():
        return None
    
    json_files = sorted(results_dir.glob("viral_tweets_*.json"), reverse=True)
    return json_files[0] if json_files else None

def extract_top_trends(scrape_file, top_n=3):
    """Extract top N trends by keyword and aggregate stats"""
    with open(scrape_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Group by keyword and calculate aggregate virality
    trends = {}
    for tweet in data['tweets']:
        keyword = tweet['keyword']
        if keyword not in trends:
            trends[keyword] = {
                'keyword': keyword,
                'total_tweets': 0,
                'total_virality': 0,
                'total_likes': 0,
                'total_retweets': 0,
                'total_replies': 0,
                'avg_virality': 0
            }
        
        trends[keyword]['total_tweets'] += 1
        trends[keyword]['total_virality'] += tweet['virality_score']
        trends[keyword]['total_likes'] += tweet['likes']
        trends[keyword]['total_retweets'] += tweet['retweets']
        trends[keyword]['total_replies'] += tweet['replies']
    
    # Calculate averages and sort
    for keyword in trends:
        total = trends[keyword]['total_tweets']
        trends[keyword]['avg_virality'] = trends[keyword]['total_virality'] / total if total > 0 else 0
    
    # Sort by total virality and get top N
    sorted_trends = sorted(trends.values(), key=lambda x: x['total_virality'], reverse=True)
    return sorted_trends[:top_n]

def update_trends_history(top_trends):
    """Append top trends to trends.json with timestamp"""
    trends_file = Path("trends.json")
    
    # Load existing trends or create new
    if trends_file.exists():
        with open(trends_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = {'trend_history': []}
    
    # Add new entry
    entry = {
        'timestamp': datetime.now().isoformat(),
        'top_trends': top_trends
    }
    history['trend_history'].append(entry)
    
    # Keep only last 100 entries to avoid file bloat
    if len(history['trend_history']) > 100:
        history['trend_history'] = history['trend_history'][-100:]
    
    # Save updated trends
    with open(trends_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    return history

def main():
    print("\n📊 Extracting top 3 viral trends...")
    
    # Get latest scrape
    scrape_file = get_latest_scrape()
    if not scrape_file:
        print("❌ No scrape results found")
        return
    
    print(f"📁 Found scrape: {scrape_file}")
    
    # Extract top 3 trends
    top_trends = extract_top_trends(scrape_file)
    
    if not top_trends:
        print("❌ No trends extracted")
        return
    
    print(f"\n🔥 TOP 3 VIRAL TRENDS:")
    for i, trend in enumerate(top_trends, 1):
        print(f"\n{i}. {trend['keyword']}")
        print(f"   📊 Total Tweets: {trend['total_tweets']}")
        print(f"   💪 Total Virality Score: {trend['total_virality']}")
        print(f"   ⭐ Avg Virality: {trend['avg_virality']:.0f}")
        print(f"   ❤️  Total Likes: {trend['total_likes']}")
        print(f"   🔄 Total Retweets: {trend['total_retweets']}")
        print(f"   💬 Total Replies: {trend['total_replies']}")
    
    # Update trends history
    history = update_trends_history(top_trends)
    print(f"\n✅ Updated trends.json with {len(history['trend_history'])} historical records")

if __name__ == "__main__":
    main()
