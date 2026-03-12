# LLM Budget Tracker

Context window management and cost tracking for LLM API calls.

## Features

- **Token Estimation**: Uses `tiktoken` for accurate token counting
- **Tiered Routing**: Automatic model selection based on task complexity
- **Cost Tracking**: Real-time tracking of tokens and costs
- **Fallback Support**: Automatic fallback to alternative models on failure
- **Budget Summary**: Detailed usage reports

## Installation

Dependencies are already in `pyproject.toml`:
```bash
pip install tiktoken litellm
```

## Setup

Set your OpenRouter API key:
```bash
export OPENROUTER_API_KEY='your-key-here'
```

Get a free API key at: https://openrouter.ai/

## Usage

### Basic Example

```python
from src.utils.llm_budget import ContextWindowBudget

# Initialize
budget = ContextWindowBudget()

# Estimate tokens
tokens = budget.estimate_tokens("Your text here")
print(f"Tokens: {tokens}")

# Call cheap LLM (Gemini Flash - free)
response = budget.call_llm(
    prompt="What is a knowledge graph?",
    tier="cheap",
    max_tokens=100
)
print(response)

# Call expensive LLM (Claude Sonnet)
response = budget.call_llm(
    prompt="Analyze this complex architecture...",
    tier="expensive",
    max_tokens=500,
    system_prompt="You are a software architect."
)

# Get summary
budget.print_summary()
```

### Model Tiers

**Cheap Tier** (`tier="cheap"`):
- Primary: `openrouter/google/gemini-2.0-flash-exp:free` (FREE)
- Fallback: `gpt-3.5-turbo` ($0.50/$1.50 per 1M tokens)
- Use for: Bulk analysis, simple questions, code summarization

**Expensive Tier** (`tier="expensive"`):
- Primary: `openrouter/anthropic/claude-3.5-sonnet` ($3/$15 per 1M tokens)
- Fallback: `gpt-4o` ($2.50/$10 per 1M tokens)
- Use for: Complex reasoning, architecture analysis, critical decisions

### Advanced Usage

```python
# With system prompt
response = budget.call_llm(
    prompt="Analyze this code...",
    tier="cheap",
    system_prompt="You are an expert code reviewer.",
    temperature=0.3,  # Lower = more deterministic
    max_tokens=1000
)

# Check budget before expensive call
summary = budget.get_summary()
if summary['total_cost'] < 1.0:  # Under $1
    response = budget.call_llm(prompt, tier="expensive")

# Reset budget
budget.reset()
```

## Testing

Run the test suite:
```bash
python tests/test_llm_budget.py
```

Tests include:
1. Token estimation (no API key needed)
2. Cheap LLM calls (requires API key)
3. Multiple calls with budget tracking
4. Budget reset functionality

## Budget Summary Output

```
============================================================
LLM Budget Summary
============================================================
Total API Calls:        5
Total Tokens Used:      1,234
Total Cost:             $0.0123
Avg Tokens per Call:    247
Avg Cost per Call:      $0.0025
============================================================

Recent Calls:
  1. openrouter/google/gemini-2.0-flash-exp:free
     Tokens: 245 | Cost: $0.0000
     Prompt: What is a knowledge graph?
  2. gpt-4o (fallback)
     Tokens: 512 | Cost: $0.0051
     Prompt: Analyze this complex architecture...
```

## Integration with Semanticist Agent

```python
from src.utils.llm_budget import ContextWindowBudget

class Semanticist:
    def __init__(self, knowledge_graph):
        self.kg = knowledge_graph
        self.budget = ContextWindowBudget()
    
    def generate_purpose_statement(self, module_path: str) -> str:
        # Read module code
        code = Path(module_path).read_text()
        
        # Estimate tokens
        tokens = self.budget.estimate_tokens(code)
        
        # Use cheap tier for simple modules
        tier = "cheap" if tokens < 2000 else "expensive"
        
        # Generate purpose
        prompt = f"Analyze this Python module and describe its purpose:\n\n{code}"
        purpose = self.budget.call_llm(prompt, tier=tier, max_tokens=200)
        
        return purpose
    
    def print_budget_summary(self):
        self.budget.print_summary()
```

## Cost Optimization Tips

1. **Use cheap tier by default**: Gemini Flash is free and fast
2. **Batch similar requests**: Reduces overhead
3. **Set appropriate max_tokens**: Don't request more than needed
4. **Monitor budget**: Check `get_summary()` regularly
5. **Use system prompts**: Better results with fewer tokens

## Error Handling

The budget tracker handles errors gracefully:
- Falls back to alternative models automatically
- Logs errors with context
- Continues tracking even on failures

```python
try:
    response = budget.call_llm(prompt, tier="cheap")
except Exception as e:
    print(f"LLM call failed: {e}")
    # Budget still tracks partial usage
```

## API Key Security

Never commit API keys to git:
```bash
# Add to .gitignore
echo ".env" >> .gitignore

# Use .env file
echo "OPENROUTER_API_KEY=your-key" > .env

# Load in code
from dotenv import load_dotenv
load_dotenv()
```

## Pricing Reference

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Gemini Flash (free) | $0.00 | $0.00 |
| GPT-3.5 Turbo | $0.50 | $1.50 |
| GPT-4o | $2.50 | $10.00 |
| Claude 3.5 Sonnet | $3.00 | $15.00 |

**Example costs**:
- 100 cheap calls (100 tokens each): ~$0.00 (free tier)
- 100 expensive calls (500 tokens each): ~$0.75
- Analyzing 1,000 modules (cheap): ~$0.00-$0.50

## Troubleshooting

**"No module named 'tiktoken'"**:
```bash
pip install tiktoken
```

**"No module named 'litellm'"**:
```bash
pip install litellm
```

**"API key not found"**:
```bash
export OPENROUTER_API_KEY='your-key'
```

**"Rate limit exceeded"**:
- Wait a few seconds between calls
- Use free tier (Gemini Flash) for bulk operations
- Consider batching requests

## License

Part of the Brownfield Cartographer project.
