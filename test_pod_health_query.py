#!/usr/bin/env python3
"""
Test script to verify the agent can handle "are all pods healthy" type queries.
This tests that list_pods can be called without parameters.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tools.kubernetes import KubernetesTools


def test_list_pods_no_params():
    """Test that list_pods works without parameters (uses default namespace)."""
    print("Testing list_pods with no parameters...")
    
    try:
        k8s = KubernetesTools(namespace="default")
        
        # This should work - simulates what the agent does with empty input
        result = k8s.list_pods()
        
        print("✓ list_pods() called successfully without parameters")
        print("\nResult preview:")
        print(result[:500] if len(result) > 500 else result)
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_list_pods_with_namespace():
    """Test that list_pods works with namespace parameter."""
    print("\n\nTesting list_pods with namespace parameter...")
    
    try:
        k8s = KubernetesTools(namespace="default")
        
        # This should also work
        result = k8s.list_pods(namespace="default")
        
        print("✓ list_pods(namespace='default') called successfully")
        print("\nResult preview:")
        print(result[:500] if len(result) > 500 else result)
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_parse_and_call_simulation():
    """Simulate how the agent's _parse_and_call method works."""
    print("\n\nSimulating agent's _parse_and_call behavior...")
    
    try:
        k8s = KubernetesTools(namespace="default")
        
        # Simulate _parse_and_call with empty input
        input_str = ""
        if not input_str or input_str.strip() == "":
            result = k8s.list_pods()
        else:
            parts = [p.strip() for p in input_str.split(',')]
            result = k8s.list_pods(*parts)
        
        print("✓ Simulated _parse_and_call with empty input works")
        print("\nResult preview:")
        print(result[:500] if len(result) > 500 else result)
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("Testing Pod Health Query Functionality")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("list_pods() no params", test_list_pods_no_params()))
    results.append(("list_pods(namespace)", test_list_pods_with_namespace()))
    results.append(("_parse_and_call simulation", test_parse_and_call_simulation()))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ All tests passed! The agent should now handle 'are all pods healthy' queries.")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    print("=" * 70)
    
    sys.exit(0 if all_passed else 1)

# Made with Bob
