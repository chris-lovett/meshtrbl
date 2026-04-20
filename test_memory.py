#!/usr/bin/env python3
"""
Quick test script to verify conversation memory functionality.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.agent import TroubleshootingAgent

def test_memory():
    """Test memory functionality without requiring actual K8s/Consul clusters."""
    
    print("=" * 70)
    print("Testing Conversation Memory Functionality")
    print("=" * 70)
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  OPENAI_API_KEY not set. This test requires an API key.")
        print("Set it with: export OPENAI_API_KEY=your_key_here")
        return False
    
    try:
        # Create agent with memory enabled
        print("\n1. Creating agent with memory enabled...")
        agent = TroubleshootingAgent(
            model="gpt-4o-mini",
            enable_memory=True,
            verbose=False
        )
        print("✓ Agent created successfully")
        
        # Test memory initialization
        print("\n2. Testing memory initialization...")
        history = agent.get_conversation_history()
        print(f"✓ Initial history length: {len(history)} (should be 0)")
        assert len(history) == 0, "Initial history should be empty"
        
        # Test manual context saving
        print("\n3. Testing manual context saving...")
        agent.save_context(
            {"input": "What is Kubernetes?"},
            {"output": "Kubernetes is a container orchestration platform."}
        )
        history = agent.get_conversation_history()
        print(f"✓ History after save_context: {len(history)} messages")
        assert len(history) == 2, "Should have 2 messages (input + output)"
        
        # Test conversation summary
        print("\n4. Testing conversation summary...")
        summary = agent.get_conversation_summary()
        print(f"✓ Summary generated:\n{summary}")
        
        # Test memory clearing
        print("\n5. Testing memory clearing...")
        agent.clear_memory()
        history = agent.get_conversation_history()
        print(f"✓ History after clear: {len(history)} (should be 0)")
        assert len(history) == 0, "History should be empty after clear"
        
        # Test agent without memory
        print("\n6. Creating agent with memory disabled...")
        agent_no_mem = TroubleshootingAgent(
            model="gpt-4o-mini",
            enable_memory=False,
            verbose=False
        )
        print("✓ Agent created successfully")
        
        summary = agent_no_mem.get_conversation_summary()
        print(f"✓ Summary for no-memory agent: {summary}")
        assert "disabled" in summary.lower(), "Should indicate memory is disabled"
        
        print("\n" + "=" * 70)
        print("✅ All memory tests passed!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_memory()
    sys.exit(0 if success else 1)

# Made with Bob
