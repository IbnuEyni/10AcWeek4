"""
Cartography Tracer - Logging for Analysis Steps and Tool Calls.

Logs every analysis action to a JSONL file for debugging, auditing, and replay.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any


class CartographyTracer:
    """
    Logs all analysis steps and tool calls to a JSONL trace file.
    
    Each log entry includes:
    - Timestamp (ISO 8601 format)
    - Agent name (Surveyor, Hydrologist, Semanticist)
    - Action type (analyze_file, extract_imports, call_llm, etc.)
    - Target (file path, dataset name, etc.)
    - Evidence (code snippet, SQL query, etc.)
    - Confidence score (0.0-1.0)
    """
    
    def __init__(self, trace_file: str = ".cartography/cartography_trace.jsonl"):
        """
        Initialize the tracer.
        
        Args:
            trace_file: Path to JSONL trace file (default: .cartography/cartography_trace.jsonl)
        """
        self.trace_file = Path(trace_file)
        
        # Create parent directory if it doesn't exist
        self.trace_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize trace file (create if doesn't exist)
        if not self.trace_file.exists():
            self.trace_file.touch()
    
    def log_action(
        self,
        agent: str,
        action: str,
        target: str,
        evidence: str = "",
        confidence: str = "1.0"
    ) -> None:
        """
        Log an analysis action to the trace file.
        
        Args:
            agent: Name of the agent performing the action (e.g., "Surveyor", "Hydrologist")
            action: Type of action being performed (e.g., "analyze_file", "extract_imports")
            target: Target of the action (e.g., file path, dataset name)
            evidence: Supporting evidence for the action (e.g., code snippet, SQL query)
            confidence: Confidence score as string (e.g., "0.95", "high", "medium")
        """
        # Create log entry
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "agent": agent,
            "action": action,
            "target": target,
            "evidence": evidence,
            "confidence": confidence
        }
        
        # Append to trace file (JSONL format - one JSON object per line)
        try:
            with open(self.trace_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            # Don't fail the analysis if logging fails
            print(f"Warning: Failed to write trace entry: {e}")
    
    def log_tool_call(
        self,
        agent: str,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Optional[str] = None,
        success: bool = True
    ) -> None:
        """
        Log a LangGraph tool call.
        
        Args:
            agent: Name of the agent calling the tool
            tool_name: Name of the tool being called
            tool_input: Input parameters to the tool
            tool_output: Output from the tool (optional)
            success: Whether the tool call succeeded
        """
        # Format evidence with tool input/output
        evidence_parts = [f"Tool: {tool_name}"]
        
        if tool_input:
            evidence_parts.append(f"Input: {json.dumps(tool_input, indent=2)}")
        
        if tool_output:
            # Truncate long outputs
            output_preview = tool_output[:500] + "..." if len(tool_output) > 500 else tool_output
            evidence_parts.append(f"Output: {output_preview}")
        
        evidence = "\n".join(evidence_parts)
        
        # Log with appropriate confidence
        confidence = "1.0" if success else "0.0"
        action = f"tool_call_{tool_name}"
        
        self.log_action(
            agent=agent,
            action=action,
            target=tool_name,
            evidence=evidence,
            confidence=confidence
        )
    
    def log_llm_call(
        self,
        agent: str,
        model: str,
        prompt: str,
        response: str,
        tokens_used: int = 0,
        cost: float = 0.0
    ) -> None:
        """
        Log an LLM API call.
        
        Args:
            agent: Name of the agent making the LLM call
            model: LLM model name
            prompt: Prompt sent to the LLM
            response: Response from the LLM
            tokens_used: Number of tokens used
            cost: Cost of the API call
        """
        # Truncate prompt and response for readability
        prompt_preview = prompt[:300] + "..." if len(prompt) > 300 else prompt
        response_preview = response[:300] + "..." if len(response) > 300 else response
        
        evidence = f"""Model: {model}
Tokens: {tokens_used}
Cost: ${cost:.4f}

Prompt:
{prompt_preview}

Response:
{response_preview}
"""
        
        self.log_action(
            agent=agent,
            action="llm_call",
            target=model,
            evidence=evidence,
            confidence="1.0"
        )
    
    def log_error(
        self,
        agent: str,
        action: str,
        target: str,
        error_message: str
    ) -> None:
        """
        Log an error that occurred during analysis.
        
        Args:
            agent: Name of the agent where error occurred
            action: Action that was being performed
            target: Target of the action
            error_message: Error message or stack trace
        """
        self.log_action(
            agent=agent,
            action=f"error_{action}",
            target=target,
            evidence=f"Error: {error_message}",
            confidence="0.0"
        )
    
    def log_graph_update(
        self,
        agent: str,
        node_id: str,
        node_type: str,
        operation: str = "add",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a knowledge graph update.
        
        Args:
            agent: Name of the agent updating the graph
            node_id: ID of the node being added/updated
            node_type: Type of node (module, dataset, function, etc.)
            operation: Operation type (add, update, delete)
            metadata: Additional metadata about the node
        """
        evidence_parts = [
            f"Operation: {operation}",
            f"Node Type: {node_type}",
            f"Node ID: {node_id}"
        ]
        
        if metadata:
            evidence_parts.append(f"Metadata: {json.dumps(metadata, indent=2)}")
        
        evidence = "\n".join(evidence_parts)
        
        self.log_action(
            agent=agent,
            action=f"graph_{operation}",
            target=node_id,
            evidence=evidence,
            confidence="1.0"
        )
    
    def get_trace_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the trace file.
        
        Returns:
            Dict with trace statistics (total entries, actions by agent, etc.)
        """
        if not self.trace_file.exists():
            return {
                "total_entries": 0,
                "agents": {},
                "actions": {},
                "errors": 0
            }
        
        summary = {
            "total_entries": 0,
            "agents": {},
            "actions": {},
            "errors": 0
        }
        
        try:
            with open(self.trace_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        entry = json.loads(line)
                        summary["total_entries"] += 1
                        
                        # Count by agent
                        agent = entry.get("agent", "unknown")
                        summary["agents"][agent] = summary["agents"].get(agent, 0) + 1
                        
                        # Count by action
                        action = entry.get("action", "unknown")
                        summary["actions"][action] = summary["actions"].get(action, 0) + 1
                        
                        # Count errors
                        if action.startswith("error_") or entry.get("confidence") == "0.0":
                            summary["errors"] += 1
                    
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            print(f"Warning: Failed to read trace file: {e}")
        
        return summary
    
    def print_summary(self) -> None:
        """Print a formatted summary of the trace file."""
        summary = self.get_trace_summary()
        
        print("\n" + "="*60)
        print("Cartography Trace Summary")
        print("="*60)
        print(f"Total Entries:      {summary['total_entries']}")
        print(f"Errors:             {summary['errors']}")
        
        if summary['agents']:
            print("\nActions by Agent:")
            for agent, count in sorted(summary['agents'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {agent:20} {count:5} actions")
        
        if summary['actions']:
            print("\nTop Actions:")
            top_actions = sorted(summary['actions'].items(), key=lambda x: x[1], reverse=True)[:10]
            for action, count in top_actions:
                print(f"  {action:30} {count:5} times")
        
        print("="*60)
    
    def clear_trace(self) -> None:
        """Clear the trace file (delete all entries)."""
        if self.trace_file.exists():
            self.trace_file.unlink()
            self.trace_file.touch()
            print(f"Trace file cleared: {self.trace_file}")


# Example usage
if __name__ == "__main__":
    # Initialize tracer
    tracer = CartographyTracer()
    
    # Log some example actions
    tracer.log_action(
        agent="Surveyor",
        action="analyze_file",
        target="src/models/schema.py",
        evidence="Found 5 class definitions and 12 imports",
        confidence="1.0"
    )
    
    tracer.log_action(
        agent="Hydrologist",
        action="extract_sql_dependencies",
        target="models/customers.sql",
        evidence="SELECT * FROM raw.users JOIN raw.orders",
        confidence="0.95"
    )
    
    tracer.log_llm_call(
        agent="Semanticist",
        model="qwen-2.5-7b",
        prompt="Analyze this Python module...",
        response="This module provides data validation...",
        tokens_used=250,
        cost=0.0
    )
    
    tracer.log_error(
        agent="Surveyor",
        action="parse_imports",
        target="src/broken.py",
        error_message="SyntaxError: invalid syntax at line 42"
    )
    
    tracer.log_graph_update(
        agent="Surveyor",
        node_id="src/models/schema.py",
        node_type="module",
        operation="add",
        metadata={"complexity": 12, "pagerank": 0.0456}
    )
    
    # Print summary
    tracer.print_summary()
    
    print(f"\nTrace file location: {tracer.trace_file}")
