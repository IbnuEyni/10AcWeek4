"""
Tests for CartographyTracer.
"""

from pathlib import Path
import json
import tempfile
from src.utils.tracer import CartographyTracer


def test_log_action():
    """Test basic action logging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_file = Path(tmpdir) / "test_trace.jsonl"
        tracer = CartographyTracer(str(trace_file))
        
        tracer.log_action(
            agent="TestAgent",
            action="test_action",
            target="test_target",
            evidence="test evidence",
            confidence="0.95"
        )
        
        # Read and verify
        with open(trace_file) as f:
            entry = json.loads(f.readline())
        
        assert entry["agent"] == "TestAgent"
        assert entry["action"] == "test_action"
        assert entry["target"] == "test_target"
        assert entry["evidence"] == "test evidence"
        assert entry["confidence"] == "0.95"
        assert "timestamp" in entry
        print("✓ test_log_action passed")


def test_log_tool_call():
    """Test tool call logging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_file = Path(tmpdir) / "test_trace.jsonl"
        tracer = CartographyTracer(str(trace_file))
        
        tracer.log_tool_call(
            agent="Surveyor",
            tool_name="parse_imports",
            tool_input={"file": "test.py"},
            tool_output="Found 5 imports",
            success=True
        )
        
        # Read and verify
        with open(trace_file) as f:
            entry = json.loads(f.readline())
        
        assert entry["agent"] == "Surveyor"
        assert entry["action"] == "tool_call_parse_imports"
        assert "parse_imports" in entry["evidence"]
        assert entry["confidence"] == "1.0"
        print("✓ test_log_tool_call passed")


def test_log_llm_call():
    """Test LLM call logging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_file = Path(tmpdir) / "test_trace.jsonl"
        tracer = CartographyTracer(str(trace_file))
        
        tracer.log_llm_call(
            agent="Semanticist",
            model="gpt-4",
            prompt="Test prompt",
            response="Test response",
            tokens_used=100,
            cost=0.002
        )
        
        # Read and verify
        with open(trace_file) as f:
            entry = json.loads(f.readline())
        
        assert entry["agent"] == "Semanticist"
        assert entry["action"] == "llm_call"
        assert entry["target"] == "gpt-4"
        assert "Tokens: 100" in entry["evidence"]
        assert "Cost: $0.0020" in entry["evidence"]
        print("✓ test_log_llm_call passed")


def test_log_error():
    """Test error logging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_file = Path(tmpdir) / "test_trace.jsonl"
        tracer = CartographyTracer(str(trace_file))
        
        tracer.log_error(
            agent="Surveyor",
            action="parse_file",
            target="broken.py",
            error_message="SyntaxError: invalid syntax"
        )
        
        # Read and verify
        with open(trace_file) as f:
            entry = json.loads(f.readline())
        
        assert entry["agent"] == "Surveyor"
        assert entry["action"] == "error_parse_file"
        assert entry["confidence"] == "0.0"
        assert "SyntaxError" in entry["evidence"]
        print("✓ test_log_error passed")


def test_log_graph_update():
    """Test graph update logging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_file = Path(tmpdir) / "test_trace.jsonl"
        tracer = CartographyTracer(str(trace_file))
        
        tracer.log_graph_update(
            agent="Surveyor",
            node_id="test.py",
            node_type="module",
            operation="add",
            metadata={"complexity": 10}
        )
        
        # Read and verify
        with open(trace_file) as f:
            entry = json.loads(f.readline())
        
        assert entry["agent"] == "Surveyor"
        assert entry["action"] == "graph_add"
        assert entry["target"] == "test.py"
        assert "module" in entry["evidence"]
        assert "complexity" in entry["evidence"]
        print("✓ test_log_graph_update passed")


def test_get_trace_summary():
    """Test trace summary generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_file = Path(tmpdir) / "test_trace.jsonl"
        tracer = CartographyTracer(str(trace_file))
        
        # Log multiple actions
        tracer.log_action("Surveyor", "action1", "target1")
        tracer.log_action("Surveyor", "action2", "target2")
        tracer.log_action("Hydrologist", "action1", "target3")
        tracer.log_error("Surveyor", "action3", "target4", "error")
        
        summary = tracer.get_trace_summary()
        
        assert summary["total_entries"] == 4
        assert summary["agents"]["Surveyor"] == 3
        assert summary["agents"]["Hydrologist"] == 1
        assert summary["errors"] == 1
        print("✓ test_get_trace_summary passed")


def test_multiple_entries():
    """Test logging multiple entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_file = Path(tmpdir) / "test_trace.jsonl"
        tracer = CartographyTracer(str(trace_file))
        
        # Log 10 entries
        for i in range(10):
            tracer.log_action(
                agent=f"Agent{i % 3}",
                action=f"action{i}",
                target=f"target{i}"
            )
        
        # Verify all entries
        with open(trace_file) as f:
            lines = f.readlines()
        
        assert len(lines) == 10
        
        # Verify each is valid JSON
        for line in lines:
            entry = json.loads(line)
            assert "timestamp" in entry
            assert "agent" in entry
            assert "action" in entry
        
        print("✓ test_multiple_entries passed")


if __name__ == "__main__":
    print("Running CartographyTracer tests...\n")
    test_log_action()
    test_log_tool_call()
    test_log_llm_call()
    test_log_error()
    test_log_graph_update()
    test_get_trace_summary()
    test_multiple_entries()
    print("\n✓ All tests passed!")
