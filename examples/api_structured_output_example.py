#!/usr/bin/env python3
"""
Example demonstrating structured output access via the Briefler API.

This example shows how to:
1. Execute analysis via REST API
2. Access structured data from API responses
3. Build metrics dashboards
4. Filter and process email data programmatically
5. Monitor token usage and costs
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional


API_BASE_URL = "http://localhost:8000"


def execute_analysis(sender_emails: List[str], language: str = "en", days: int = 7) -> Dict:
    """Execute Gmail analysis via API."""
    response = requests.post(
        f"{API_BASE_URL}/api/flows/gmail-read",
        json={
            "sender_emails": sender_emails,
            "language": language,
            "days": days
        }
    )
    response.raise_for_status()
    return response.json()


def get_urgent_action_items(data: Dict) -> List[Dict]:
    """Extract action items from emails with deadlines."""
    structured = data.get("structured_result")
    if not structured:
        return []
    
    urgent_items = []
    for email in structured["email_summaries"]:
        if email["has_deadline"] and email["action_items"]:
            for item in email["action_items"]:
                urgent_items.append({
                    "item": item,
                    "from_email": email["subject"],
                    "sender": email["sender"],
                    "date": email["timestamp"]
                })
    
    return urgent_items


def calculate_cost(token_usage: Dict) -> Dict[str, float]:
    """Calculate approximate API cost based on token usage."""
    # Example pricing: GPT-4
    prompt_rate = 0.00003  # $0.03 per 1K tokens
    completion_rate = 0.00006  # $0.06 per 1K tokens
    
    prompt_cost = token_usage["prompt_tokens"] * prompt_rate
    completion_cost = token_usage["completion_tokens"] * completion_rate
    total_cost = prompt_cost + completion_cost
    
    return {
        "prompt_cost": prompt_cost,
        "completion_cost": completion_cost,
        "total_cost": total_cost
    }


def get_analysis_metrics(analysis_id: str) -> Optional[Dict]:
    """Extract key metrics from an analysis."""
    response = requests.get(f"{API_BASE_URL}/api/history/{analysis_id}")
    if response.status_code != 200:
        return None
    
    data = response.json()
    structured = data.get("structured_result")
    
    if not structured:
        return None
    
    token_usage = data.get("token_usage", {})
    
    return {
        "analysis_id": data["analysis_id"],
        "timestamp": data["timestamp"],
        "total_emails": structured["total_count"],
        "total_action_items": len(structured["action_items"]),
        "urgent_emails": sum(1 for e in structured["email_summaries"] if e["has_deadline"]),
        "priority": structured["priority_assessment"],
        "tokens_used": token_usage.get("total_tokens", 0),
        "execution_time": data["execution_time_seconds"]
    }


def display_dashboard(limit: int = 10):
    """Display metrics dashboard for recent analyses."""
    response = requests.get(f"{API_BASE_URL}/api/history?limit={limit}")
    history = response.json()
    
    print("\n📊 Analysis Dashboard")
    print("=" * 90)
    print(f"{'Date':<20} {'Emails':<8} {'Actions':<8} {'Urgent':<8} {'Tokens':<10} {'Time':<8} {'Priority':<15}")
    print("-" * 90)
    
    for item in history["items"]:
        metrics = get_analysis_metrics(item["analysis_id"])
        if metrics:
            date = datetime.fromisoformat(metrics["timestamp"].replace("Z", "+00:00"))
            priority_short = metrics["priority"][:12] + "..." if len(metrics["priority"]) > 15 else metrics["priority"]
            print(f"{date.strftime('%Y-%m-%d %H:%M'):<20} "
                  f"{metrics['total_emails']:<8} "
                  f"{metrics['total_action_items']:<8} "
                  f"{metrics['urgent_emails']:<8} "
                  f"{metrics['tokens_used']:<10} "
                  f"{metrics['execution_time']:.1f}s{'':<6} "
                  f"{priority_short:<15}")


def main():
    """Main example demonstrating structured output access via API."""
    
    print("=" * 70)
    print("Briefler API - Structured Output Example")
    print("=" * 70)
    
    # Check API health
    try:
        health = requests.get(f"{API_BASE_URL}/health").json()
        print(f"\n✅ API Status: {health['status']}")
    except Exception as e:
        print(f"\n❌ API not available: {e}")
        print("Please start the API server with: uvicorn api.main:app --reload")
        return
    
    # Execute analysis
    print("\n🔄 Executing Gmail analysis...")
    sender_emails = ["notifications@github.com"]
    
    try:
        data = execute_analysis(sender_emails, language="en", days=7)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return
    
    print(f"✅ Analysis complete! ID: {data['analysis_id']}")
    
    # Access structured data
    if data.get("structured_result"):
        structured = data["structured_result"]
        
        print("\n📊 Summary Statistics")
        print("-" * 70)
        print(f"Total emails analyzed: {structured['total_count']}")
        print(f"Total action items: {len(structured['action_items'])}")
        print(f"Priority: {structured['priority_assessment']}")
        
        # Display all action items
        if structured["action_items"]:
            print("\n✓ All Action Items:")
            for i, item in enumerate(structured["action_items"], 1):
                print(f"  {i}. {item}")
        
        # Display urgent emails
        urgent_emails = [e for e in structured["email_summaries"] if e["has_deadline"]]
        if urgent_emails:
            print("\n⚠️  Urgent Emails:")
            for email in urgent_emails:
                print(f"  • {email['subject']} (from {email['sender']})")
        
        # Display individual email summaries
        print("\n📧 Email Summaries")
        print("-" * 70)
        
        for i, email in enumerate(structured["email_summaries"], 1):
            print(f"\n{i}. {email['subject']}")
            print(f"   From: {email['sender']}")
            print(f"   Date: {email['timestamp']}")
            
            if email["has_deadline"]:
                print("   ⚠️  TIME-SENSITIVE")
            
            if email["key_points"]:
                print("\n   Key Points:")
                for point in email["key_points"]:
                    print(f"     • {point}")
    
    else:
        print("\n⚠️  Structured result not available")
        print("Using raw result instead")
    
    # Display token usage and cost
    if data.get("token_usage"):
        usage = data["token_usage"]
        cost = calculate_cost(usage)
        
        print("\n💰 Token Usage & Cost Analysis")
        print("-" * 70)
        print(f"Total tokens: {usage['total_tokens']}")
        print(f"  Prompt tokens: {usage['prompt_tokens']}")
        print(f"  Completion tokens: {usage['completion_tokens']}")
        print(f"\nEstimated cost: ${cost['total_cost']:.4f}")
        print(f"  Prompt cost: ${cost['prompt_cost']:.4f}")
        print(f"  Completion cost: ${cost['completion_cost']:.4f}")
    
    # Display execution metrics
    print("\n⏱️  Execution Metrics")
    print("-" * 70)
    print(f"Execution time: {data['execution_time_seconds']:.2f} seconds")
    print(f"Timestamp: {data['timestamp']}")
    
    # Display metrics dashboard
    print("\n" + "=" * 70)
    print("Recent Analysis History")
    print("=" * 70)
    display_dashboard(limit=5)
    
    # Extract urgent action items
    urgent_items = get_urgent_action_items(data)
    if urgent_items:
        print("\n⚠️  Urgent Action Items Requiring Immediate Attention")
        print("-" * 70)
        for item in urgent_items:
            print(f"\n• {item['item']}")
            print(f"  From: {item['from_email']} ({item['sender']})")
            print(f"  Date: {item['date']}")
    
    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
