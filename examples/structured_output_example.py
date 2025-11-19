#!/usr/bin/env python3
"""
Example demonstrating structured output access from Gmail Reader Crew.

This example shows how to:
1. Execute the Gmail Reader Flow
2. Access structured task outputs via Pydantic models
3. Extract specific fields programmatically
4. Monitor token usage for cost tracking
5. Process email summaries and action items
"""

from briefler.flows.gmail_read_flow import GmailReadFlow


def main():
    """Execute Gmail analysis and demonstrate structured output access."""
    
    print("=" * 70)
    print("Gmail Reader - Structured Output Example")
    print("=" * 70)
    
    # Initialize and execute flow
    flow = GmailReadFlow()
    
    print("\n🔄 Executing Gmail analysis flow...")
    flow.kickoff({
        "crewai_trigger_payload": {
            "sender_emails": ["notifications@github.com"],
            "language": "en",
            "days": 7
        }
    })
    
    print("\n✅ Analysis complete!\n")
    
    # Access structured result
    if flow.state.structured_result:
        structured = flow.state.structured_result
        
        # Display summary statistics
        print("📊 Summary Statistics")
        print("-" * 70)
        print(f"Total emails analyzed: {structured.total_count}")
        print(f"Total action items: {len(structured.action_items)}")
        print(f"Priority assessment: {structured.priority_assessment}")
        
        # Display all action items
        if structured.action_items:
            print("\n✓ All Action Items:")
            for i, item in enumerate(structured.action_items, 1):
                print(f"  {i}. {item}")
        
        # Display individual email summaries
        print("\n📧 Email Summaries")
        print("-" * 70)
        
        for i, email in enumerate(structured.email_summaries, 1):
            print(f"\n{i}. {email.subject}")
            print(f"   From: {email.sender}")
            print(f"   Date: {email.timestamp}")
            
            if email.has_deadline:
                print("   ⚠️  TIME-SENSITIVE")
            
            if email.key_points:
                print("\n   Key Points:")
                for point in email.key_points:
                    print(f"     • {point}")
            
            if email.action_items:
                print("\n   Action Items:")
                for item in email.action_items:
                    print(f"     ✓ {item}")
        
        # Filter urgent emails
        urgent_emails = [e for e in structured.email_summaries if e.has_deadline]
        if urgent_emails:
            print("\n⚠️  Urgent Emails Requiring Immediate Attention")
            print("-" * 70)
            for email in urgent_emails:
                print(f"• {email.subject} (from {email.sender})")
    
    else:
        print("⚠️  Structured result not available")
        print("Falling back to raw result:")
        print(flow.state.result)
    
    # Display token usage statistics
    if flow.state.total_token_usage:
        usage = flow.state.total_token_usage
        
        print("\n💰 Token Usage Statistics")
        print("-" * 70)
        print(f"Total tokens: {usage.total_tokens}")
        print(f"Prompt tokens: {usage.prompt_tokens}")
        print(f"Completion tokens: {usage.completion_tokens}")
        
        # Calculate approximate cost (example: GPT-4 pricing)
        prompt_cost = usage.prompt_tokens * 0.00003  # $0.03 per 1K tokens
        completion_cost = usage.completion_tokens * 0.00006  # $0.06 per 1K tokens
        total_cost = prompt_cost + completion_cost
        
        print(f"\nEstimated cost: ${total_cost:.4f}")
        print(f"  Prompt cost: ${prompt_cost:.4f}")
        print(f"  Completion cost: ${completion_cost:.4f}")
    
    # Backward compatibility - raw result still available
    print("\n📄 Raw Markdown Result (Backward Compatibility)")
    print("-" * 70)
    print(flow.state.result[:500] + "..." if len(flow.state.result) > 500 else flow.state.result)
    
    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
