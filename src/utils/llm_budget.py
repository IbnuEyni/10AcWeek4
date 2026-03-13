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
            "name": "gemini/gemini-2.0-flash-exp",
            "input_cost": 0.0,
            "output_cost": 0.0,
            "fallback": "gemini/gemini-1.5-flash",
            "fallback_input_cost": 0.075,
            "fallback_output_cost": 0.30,
        },
        "expensive": {
            "name": "deepseek/deepseek-chat",
            "input_cost": 0.14,
            "output_cost": 0.28,
            "fallback": "deepseek/deepseek-coder",
            "fallback_input_cost": 0.14,
            "fallback_output_cost": 0.28,
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the budget tracker.
        
        Args:
            api_key: Not used - LiteLLM reads GEMINI_API_KEY and DEEPSEEK_API_KEY from environment
        """
        self.total_tokens = 0
        self.total_cost = 0.0
        self.call_history = []
        
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
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Call an LLM with automatic tier-based routing and budget tracking.
        
        Args:
            prompt: User prompt/question
            tier: Model tier - "cheap" or "expensive"
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt for context
        
        Returns:
            LLM response text
        
        Raises:
            ValueError: If tier is invalid
            Exception: If LLM call fails
        """
        if tier not in self.MODELS:
            raise ValueError(f"Invalid tier '{tier}'. Must be 'cheap' or 'expensive'.")
        
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
            
            # Record call history
            self.call_history.append({
                "model": model_name,
                "tier": tier,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
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
                
                self.call_history.append({
                    "model": fallback_model,
                    "tier": tier,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost": cost,
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
            Dict with total_tokens, total_cost, and call_count
        """
        return {
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 4),
            "call_count": len(self.call_history),
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
