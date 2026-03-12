"""
Test and demonstration of ContextWindowBudget class.

Run this to verify LLM integration is working correctly.
"""

from src.utils.llm_budget import ContextWindowBudget


def test_token_estimation():
    """Test token estimation functionality."""
    print("\n" + "="*60)
    print("TEST 1: Token Estimation")
    print("="*60)
    
    budget = ContextWindowBudget()
    
    test_cases = [
        "Hello, world!",
        "This is a longer test string with multiple words and punctuation.",
        """
        This is a multi-line string that contains
        several lines of text to test the token
        estimation functionality of the budget tracker.
        """,
        "def analyze_python_module(filepath: str) -> dict:\n    return {'imports': [], 'functions': []}"
    ]
    
    for i, text in enumerate(test_cases, 1):
        tokens = budget.estimate_tokens(text)
        print(f"\nTest {i}:")
        print(f"  Text: {text[:50]}..." if len(text) > 50 else f"  Text: {text}")
        print(f"  Estimated tokens: {tokens}")


def test_cheap_llm_call():
    """Test cheap tier LLM call."""
    print("\n" + "="*60)
    print("TEST 2: Cheap LLM Call (Gemini Flash)")
    print("="*60)
    
    budget = ContextWindowBudget()
    
    try:
        response = budget.call_llm(
            prompt="Explain what a knowledge graph is in one sentence.",
            tier="cheap",
            max_tokens=100,
            temperature=0.7
        )
        
        print(f"\nPrompt: Explain what a knowledge graph is in one sentence.")
        print(f"Response: {response}")
        print(f"\nTokens used: {budget.total_tokens}")
        print(f"Cost: ${budget.total_cost:.6f}")
        
    except Exception as e:
        print(f"\n❌ Cheap LLM call failed: {e}")
        print("Note: Make sure OPENROUTER_API_KEY is set in environment")


def test_multiple_calls_with_summary():
    """Test multiple LLM calls and budget tracking."""
    print("\n" + "="*60)
    print("TEST 3: Multiple Calls with Budget Tracking")
    print("="*60)
    
    budget = ContextWindowBudget()
    
    prompts = [
        ("What is static analysis?", "cheap"),
        ("What is data lineage?", "cheap"),
        ("Explain PageRank algorithm.", "cheap"),
    ]
    
    for prompt, tier in prompts:
        try:
            response = budget.call_llm(
                prompt=prompt,
                tier=tier,
                max_tokens=50
            )
            print(f"\n✓ Prompt: {prompt}")
            print(f"  Response: {response[:80]}...")
        except Exception as e:
            print(f"\n❌ Failed: {prompt}")
            print(f"  Error: {e}")
    
    # Print summary
    budget.print_summary()


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ContextWindowBudget - Test Suite")
    print("="*60)
    
    # Test 1: Token estimation (always works)
    test_token_estimation()
    
    # Test 2-3: LLM calls (require API key)
    import os
    if os.getenv("OPENROUTER_API_KEY"):
        print("\n✓ OPENROUTER_API_KEY found - running LLM tests")
        test_cheap_llm_call()
        test_multiple_calls_with_summary()
    else:
        print("\n⚠ OPENROUTER_API_KEY not set - skipping LLM tests")
        print("To run LLM tests, set: export OPENROUTER_API_KEY='your-key'")
    
    print("\n" + "="*60)
    print("Test Suite Complete")
    print("="*60)


if __name__ == "__main__":
    main()
