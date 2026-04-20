#!/usr/bin/env python3
"""
Test memory structure without requiring API keys or live clusters.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

def test_memory_structure():
    """Test that memory components are properly integrated."""
    
    print("=" * 70)
    print("Testing Memory Structure (No API Key Required)")
    print("=" * 70)
    
    try:
        # Test imports
        print("\n1. Testing imports...")
        from langchain.memory import ConversationBufferMemory
        from langchain_core.messages import BaseMessage
        print("✓ Memory imports successful")
        
        # Test memory creation
        print("\n2. Testing memory creation...")
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        print("✓ Memory object created")
        
        # Test memory operations
        print("\n3. Testing memory operations...")
        
        # Save context
        memory.save_context(
            {"input": "Test question"},
            {"output": "Test answer"}
        )
        
        # Get messages
        messages = memory.chat_memory.messages
        print(f"✓ Messages stored: {len(messages)} (expected: 2)")
        assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"
        
        # Check message types
        print(f"✓ Message 1 type: {messages[0].type}")
        print(f"✓ Message 2 type: {messages[1].type}")
        assert messages[0].type == "human", "First message should be human"
        assert messages[1].type == "ai", "Second message should be ai"
        
        # Clear memory
        memory.clear()
        messages = memory.chat_memory.messages
        print(f"✓ Messages after clear: {len(messages)} (expected: 0)")
        assert len(messages) == 0, f"Expected 0 messages after clear, got {len(messages)}"
        
        print("\n" + "=" * 70)
        print("✅ All memory structure tests passed!")
        print("=" * 70)
        print("\nMemory integration is working correctly.")
        print("To test with the full agent, set OPENAI_API_KEY and run:")
        print("  python3 test_memory.py")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_memory_structure()
    sys.exit(0 if success else 1)

# Made with Bob
