import subprocess
import json
from pathlib import Path
from typing import Set, Optional
from datetime import datetime


class IncrementalTracker:
    """Track and identify changed files for incremental analysis."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.state_file = self.repo_path / ".cartography" / "last_analysis.json"
    
    def get_changed_files(self, since_commit: Optional[str] = None) -> Set[str]:
        """
        Get list of files changed since HEAD~1.
        
        Args:
            since_commit: Git commit hash to compare against (None = HEAD~1)
        
        Returns:
            Set of relative file paths that have changed
        """
        if since_commit is None:
            since_commit = "HEAD~1"
        
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", since_commit],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"IncrementalTracker: git diff failed, analyzing all files")
                return self._get_all_tracked_files()
            
            changed_files = set(result.stdout.strip().split('\n'))
            changed_files = {f for f in changed_files if f}
            
            print(f"IncrementalTracker: Found {len(changed_files)} changed files since {since_commit}")
            return changed_files
        
        except Exception as e:
            print(f"IncrementalTracker: Error: {e}")
            return self._get_all_tracked_files()
    
    def _get_all_tracked_files(self) -> Set[str]:
        """Get all tracked files in the repository."""
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                files = set(result.stdout.strip().split('\n'))
                return {f for f in files if f}
        except Exception:
            pass
        
        return set()
    
    def _get_last_commit(self) -> Optional[str]:
        """Get the commit hash from last analysis."""
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                return state.get("last_commit")
        except Exception:
            return None
    
    def save_state(self):
        """Save current analysis state."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                commit_hash = result.stdout.strip()
                
                state = {
                    "last_commit": commit_hash,
                    "last_analysis_time": datetime.now().isoformat(),
                    "analysis_version": "1.0"
                }
                
                self.state_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.state_file, 'w') as f:
                    json.dump(state, f, indent=2)
                
                print(f"IncrementalTracker: Saved state at commit {commit_hash[:8]}")
        
        except Exception as e:
            print(f"IncrementalTracker: Error saving state: {e}")
