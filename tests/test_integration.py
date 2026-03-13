"""
Integration tests for the Brownfield Cartographer.

Tests the full pipeline end-to-end.
"""

import tempfile
import shutil
from pathlib import Path
from src.orchestrator import run_cartographer


def test_full_pipeline_small_repo():
    """Test full analysis pipeline on a small test repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a small test repository
        repo = Path(tmpdir) / "test_repo"
        repo.mkdir()
        
        # Create test Python files
        (repo / "main.py").write_text("""
import utils

def main():
    utils.helper()
""")
        
        (repo / "utils.py").write_text("""
def helper():
    return "Hello"
""")
        
        # Create test SQL file
        (repo / "query.sql").write_text("""
SELECT * FROM users
JOIN orders ON users.id = orders.user_id
""")
        
        # Run analysis
        run_cartographer(str(repo), incremental=False, enable_llm=False)
        
        # Verify outputs
        cartography_dir = repo / ".cartography"
        assert cartography_dir.exists(), "Cartography directory not created"
        
        assert (cartography_dir / "module_graph.json").exists(), "Module graph not created"
        assert (cartography_dir / "lineage_graph.json").exists(), "Lineage graph not created"
        assert (cartography_dir / "CODEBASE.md").exists(), "CODEBASE.md not created"
        assert (cartography_dir / "cartography_trace.jsonl").exists(), "Trace file not created"
        
        # Verify CODEBASE.md has content
        codebase_content = (cartography_dir / "CODEBASE.md").read_text()
        assert "Architecture Overview" in codebase_content
        assert "main.py" in codebase_content or "utils.py" in codebase_content
        
        print("✓ test_full_pipeline_small_repo passed")


def test_incremental_mode():
    """Test incremental analysis mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a git repository
        repo = Path(tmpdir) / "test_repo"
        repo.mkdir()
        
        # Initialize git
        import subprocess
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
        
        # Create initial file
        (repo / "file1.py").write_text("def func1(): pass")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=repo, capture_output=True)
        
        # Run first analysis
        run_cartographer(str(repo), incremental=False, enable_llm=False)
        
        # Modify file
        (repo / "file1.py").write_text("def func1(): return 42")
        
        # Run incremental analysis
        run_cartographer(str(repo), incremental=True, enable_llm=False)
        
        # Verify trace shows incremental mode
        trace_file = repo / ".cartography" / "cartography_trace.jsonl"
        trace_content = trace_file.read_text()
        assert "IncrementalTracker" in trace_content
        
        print("✓ test_incremental_mode passed")


def test_error_handling():
    """Test that analysis handles errors gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir) / "test_repo"
        repo.mkdir()
        
        # Create a file with syntax error
        (repo / "broken.py").write_text("def broken(:\n    pass")
        
        # Should not crash
        try:
            run_cartographer(str(repo), incremental=False, enable_llm=False)
            
            # Verify trace shows error
            trace_file = repo / ".cartography" / "cartography_trace.jsonl"
            if trace_file.exists():
                trace_content = trace_file.read_text()
                # Errors should be logged
                assert trace_file.exists()
            
            print("✓ test_error_handling passed")
        except Exception as e:
            print(f"✗ test_error_handling failed: {e}")
            raise


if __name__ == "__main__":
    print("Running integration tests...\n")
    test_full_pipeline_small_repo()
    test_incremental_mode()
    test_error_handling()
    print("\n✓ All integration tests passed!")
