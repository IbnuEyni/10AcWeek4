"""
LLM Budget Tracker for Context Window Management.

Tracks token usage and costs across LLM API calls with tiered routing.
"""

import os
from typing import Optional
import tiktoken
from litellm import completion


class ContextWindowBudget:
    """
    Manages LLM API calls with token and cost tracking.
    
    Supports tiered routing:
    - "cheap": Fast, inexpensive models (Gemini Flash, GPT-3.5)
    - "expensive": High-quality models (Claude Sonnet, GPT-4)
    """
    
    # Model configurations with pricing (per 1M tokens)
    MODELS = {
        "cheap": {
            "name": "deepseek/deepseek-chat",
            "input_cost": 0.14,
            "output_cost": 0.28,
            "fallback": "deepseek/deepseek-coder",
            "fallback_input_cost": 0.14,
            "fallback_output_cost": 0.28,
        },
        "expensive": {
            "name": "deepseek/deepseek-chat",
            "input_cost": 0.14,
            "output_cost": 0.28,
            "fallback": "deepseek/deepseek-coder",
            "fallback_input_cost": 0.14,
            "fallback_output_cost": 0.28,
        },
    }
    
    # Token budget limits
    MAX_TOKENS_CHEAP = 500000  # 500K tokens for cheap tier
    MAX_TOKENS_EXPENSIVE = 100000  # 100K tokens for expensive tier
    MAX_TOTAL_TOKENS = 1000000  # 1M total token budget
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the budget tracker.
        
        Args:
            api_key: Not used - LiteLLM reads GEMINI_API_KEY and DEEPSEEK_API_KEY from environment
        """
        self.total_tokens = 0
        self.total_cost = 0.0
        self.call_history = []
        self.tokens_by_tier = {"cheap": 0, "expensive": 0}
        
        # LiteLLM automatically reads GEMINI_API_KEY and DEEPSEEK_API_KEY from environment
        # No need to set API keys manually
        
        # Initialize tokenizer (using cl100k_base for GPT-4/3.5 compatibility)
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            print(f"Warning: Could not load tiktoken encoding: {e}")
            self.tokenizer = None
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.
        
        Args:
            text: Input text to tokenize
        
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                print(f"Warning: Token estimation failed: {e}")
        
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4
    
    def call_llm(
        self,
        prompt: str,
        tier: str = "cheap",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
        task_importance: str = "normal"
    ) -> str:
        """
        Call an LLM with automatic tier-based routing, budget tracking, and auto-downgrade.
        
        Args:
            prompt: User prompt/question
            tier: Model tier - "cheap" or "expensive"
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt for context
            task_importance: "critical", "normal", or "low" - affects auto-downgrade behavior
        
        Returns:
            LLM response text
        
        Raises:
            ValueError: If tier is invalid or budget exceeded
            Exception: If LLM call fails
        """
        if tier not in self.MODELS:
            raise ValueError(f"Invalid tier '{tier}'. Must be 'cheap' or 'expensive'.")
        
        # Check total budget
        if self.total_tokens >= self.MAX_TOTAL_TOKENS:
            raise ValueError(f"Total token budget exceeded: {self.total_tokens}/{self.MAX_TOTAL_TOKENS}")
        
        # Auto-downgrade expensive tier if budget low
        original_tier = tier
        if tier == "expensive":
            if self.tokens_by_tier["expensive"] >= self.MAX_TOKENS_EXPENSIVE:
                if task_importance != "critical":
                    print(f"  ⚠ Auto-downgrading to cheap tier (expensive budget exhausted)")
                    tier = "cheap"
                else:
                    raise ValueError(f"Expensive tier budget exceeded and task is critical")
        
        # Check tier-specific budget
        if tier == "cheap" and self.tokens_by_tier["cheap"] >= self.MAX_TOKENS_CHEAP:
            if task_importance == "low":
                raise ValueError(f"Cheap tier budget exceeded, skipping low-importance task")
        
        model_config = self.MODELS[tier]
        model_name = model_config["name"]
        
        # Estimate input tokens
        input_text = prompt
        if system_prompt:
            input_text = system_prompt + "\n\n" + prompt
        
        input_tokens = self.estimate_tokens(input_text)
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            # Call LLM via litellm
            response = completion(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Estimate output tokens
            output_tokens = self.estimate_tokens(response_text)
            
            # Calculate cost
            total_tokens = input_tokens + output_tokens
            cost = (
                (input_tokens / 1_000_000) * model_config["input_cost"] +
                (output_tokens / 1_000_000) * model_config["output_cost"]
            )
            
            # Update budget trackers
            self.total_tokens += total_tokens
            self.total_cost += cost
            self.tokens_by_tier[tier] += total_tokens
            
            # Record call history
            self.call_history.append({
                "model": model_name,
                "tier": tier,
                "original_tier": original_tier,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
                "task_importance": task_importance,
                "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt
            })
            
            return response_text
        
        except Exception as e:
            print(f"Error calling {model_name}: {e}")
            
            # Try fallback model
            fallback_model = model_config["fallback"]
            print(f"Attempting fallback to {fallback_model}...")
            
            try:
                response = completion(
                    model=fallback_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                
                response_text = response.choices[0].message.content
                output_tokens = self.estimate_tokens(response_text)
                total_tokens = input_tokens + output_tokens
                
                # Use fallback pricing
                cost = (
                    (input_tokens / 1_000_000) * model_config["fallback_input_cost"] +
                    (output_tokens / 1_000_000) * model_config["fallback_output_cost"]
                )
                
                self.total_tokens += total_tokens
                self.total_cost += cost
                self.tokens_by_tier[tier] += total_tokens
                
                self.call_history.append({
                    "model": fallback_model,
                    "tier": tier,
                    "original_tier": original_tier,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost": cost,
                    "task_importance": task_importance,
                    "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    "fallback": True
                })
                
                return response_text
            
            except Exception as fallback_error:
                print(f"Fallback to {fallback_model} also failed: {fallback_error}")
                raise Exception(f"Both primary and fallback LLM calls failed: {e}, {fallback_error}")
    
    def get_summary(self) -> dict:
        """
        Get a summary of token usage and costs.
        
        Returns:
            Dict with total_tokens, total_cost, call_count, and budget status
        """
        return {
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 4),
            "call_count": len(self.call_history),
            "tokens_by_tier": self.tokens_by_tier,
            "budget_remaining": {
                "cheap": max(0, self.MAX_TOKENS_CHEAP - self.tokens_by_tier["cheap"]),
                "expensive": max(0, self.MAX_TOKENS_EXPENSIVE - self.tokens_by_tier["expensive"]),
                "total": max(0, self.MAX_TOTAL_TOKENS - self.total_tokens)
            },
            "avg_tokens_per_call": (
                round(self.total_tokens / len(self.call_history))
                if self.call_history else 0
            ),
            "avg_cost_per_call": (
                round(self.total_cost / len(self.call_history), 4)
                if self.call_history else 0.0
            )
        }
    
    def print_summary(self):
        """Print a formatted summary of budget usage."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("LLM Budget Summary")
        print("="*60)
        print(f"Total API Calls:        {summary['call_count']}")
        print(f"Total Tokens Used:      {summary['total_tokens']:,}")
        print(f"Total Cost:             ${summary['total_cost']:.4f}")
        print(f"Avg Tokens per Call:    {summary['avg_tokens_per_call']:,}")
        print(f"Avg Cost per Call:      ${summary['avg_cost_per_call']:.4f}")
        print("\nTokens by Tier:")
        print(f"  Cheap:     {summary['tokens_by_tier']['cheap']:,} / {self.MAX_TOKENS_CHEAP:,}")
        print(f"  Expensive: {summary['tokens_by_tier']['expensive']:,} / {self.MAX_TOKENS_EXPENSIVE:,}")
        print("\nBudget Remaining:")
        print(f"  Cheap:     {summary['budget_remaining']['cheap']:,} tokens")
        print(f"  Expensive: {summary['budget_remaining']['expensive']:,} tokens")
        print(f"  Total:     {summary['budget_remaining']['total']:,} tokens")
        print("="*60)
        
        if self.call_history:
            print("\nRecent Calls:")
            for i, call in enumerate(self.call_history[-5:], 1):
                fallback_marker = " (fallback)" if call.get("fallback") else ""
                print(f"  {i}. {call['model']}{fallback_marker}")
                print(f"     Tokens: {call['total_tokens']:,} | Cost: ${call['cost']:.4f}")
                print(f"     Prompt: {call['prompt_preview']}")
    
    def reset(self):
        """Reset all budget trackers and call history."""
        self.total_tokens = 0
        self.total_cost = 0.0
        self.call_history = []
        print("Budget tracker reset.")


# Example usage
if __name__ == "__main__":
    # Initialize budget tracker
    budget = ContextWindowBudget()
    
    # Test token estimation
    test_text = "This is a test prompt for the Brownfield Cartographer system."
    tokens = budget.estimate_tokens(test_text)
    print(f"Estimated tokens: {tokens}")
    
    # Test cheap LLM call
    try:
        response = budget.call_llm(
            prompt="What is the purpose of a knowledge graph in software analysis?",
            tier="cheap",
            max_tokens=100
        )
        print(f"\nCheap LLM Response:\n{response}")
    except Exception as e:
        print(f"Cheap LLM call failed: {e}")
    
    # Print budget summary
    budget.print_summary()
