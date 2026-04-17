#!/usr/bin/env python3
"""Test ChatOpenAI initialization"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

print("Testing ChatOpenAI initialization...")
print(f"OpenAI API key present: {bool(os.getenv('OPENAI_API_KEY'))}")

try:
    # Try without any extra parameters first
    llm = ChatOpenAI(
        model='gpt-4-turbo-preview',
        temperature=0.1
    )
    print("SUCCESS: ChatOpenAI initialized without errors")
    print(f"Model: {llm.model_name}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Made with Bob
