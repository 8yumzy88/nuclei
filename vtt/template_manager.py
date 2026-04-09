"""Template management for browsing, installing, and updating Nuclei templates."""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None

from .config import ConfigManager
from .utils import get_template_directory


class TemplateManager:
    """Manages Nuclei template operations."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize template manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager or ConfigManager()
        self.template_dir = self._get_template_directory()
    
    def _get_template_directory(self) -> Optional[str]:
        """Get template directory path."""
        # Try config first
        config_dir = self.config.get_template_directory()
        if config_dir and Path(config_dir).exists():
            return config_dir
        
        # Try to detect from Nuclei
        detected_dir = get_template_directory()
        if detected_dir:
            return detected_dir
        
        # Default location
        default_dir = Path.home() / ".nuclei-templates"
        if default_dir.exists():
            return str(default_dir)
        
        return None
    
    def list_installed_templates(self, category: Optional[str] = None) -> List[Dict]:
        """
        List installed templates.
        
        Args:
            category: Optional category filter (e.g., 'ssl', 'exposures')
            
        Returns:
            List of template metadata dictionaries
        """
        if not self.template_dir:
            return []
        
        templates = []
        template_path = Path(self.template_dir)
        
        if not template_path.exists():
            return []
        
        # Walk through template directory
        for yaml_file in template_path.rglob("*.yaml"):
            try:
                if yaml is None:
                    # Fallback: try to parse as basic YAML without library
                    # This is a simple fallback - full YAML parsing requires pyyaml
                    continue
                    
                with open(yaml_file, 'r') as f:
                    template_data = yaml.safe_load(f)
                    if not isinstance(template_data, dict):
                        continue
                    
                    # Nuclei templates can have 'id' at top level or in 'info'
                    template_id = template_data.get("id", "") or template_data.get("info", {}).get("id", "")
                    info = template_data.get("info", {})
                    name = info.get("name", "")
                    severity = info.get("severity", "unknown")
                    description = info.get("description", "")
                    tags = info.get("tags", [])
                    author = info.get("author", [])
                    
                    # Handle tags - can be string, list, or comma-separated string
                    if isinstance(tags, str):
                        # Split comma-separated tags
                        tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                    elif not isinstance(tags, list):
                        tags = []
                    
                    # Filter by category if specified
                    if category:
                        # Check if category matches path or tags
                        path_str = str(yaml_file.relative_to(template_path))
                        if category.lower() not in path_str.lower():
                            # Check tags
                            if not any(category.lower() in str(tag).lower() for tag in tags):
                                continue
                    
                    templates.append({
                        "id": template_id,
                        "name": name,
                        "severity": severity,
                        "description": description or name,  # Use name if description is empty
                        "tags": tags,  # Already processed above
                        "author": author if isinstance(author, list) else [author] if author else [],
                        "path": str(yaml_file.relative_to(template_path)),
                        "full_path": str(yaml_file)
                    })
            except Exception:
                # Skip malformed templates
                continue
        
        return templates
    
    def browse_online_repositories(self) -> List[Dict[str, str]]:
        """
        Get list of known template repositories.
        
        Returns:
            List of repository dictionaries
        """
        return self.config.get_known_repositories()
    
    def install_templates(self, force: bool = False) -> Tuple[bool, str]:
        """
        Install/update templates using Nuclei's update mechanism.
        
        Args:
            force: Force update even if templates are up to date
            
        Returns:
            Tuple of (success, message)
        """
        nuclei_path = self.config.get_nuclei_path()
        
        if not Path(nuclei_path).exists():
            return False, f"Nuclei binary not found at {nuclei_path}"
        
        try:
            # Use nuclei -ut to update templates
            cmd = [nuclei_path, "-update-templates"]
            if force:
                # Note: Nuclei doesn't have a force flag, but we can try
                # removing the template directory first if force is True
                pass
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return True, "Templates updated successfully"
            else:
                return False, f"Template update failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Template update timed out"
        except Exception as e:
            return False, f"Failed to update templates: {str(e)}"
    
    def install_from_github_repo(
        self,
        repo: str,
        branch: str = "main"
    ) -> Tuple[bool, str]:
        """
        Install templates from a GitHub repository.
        
        Args:
            repo: GitHub repository (format: owner/repo)
            branch: Branch to clone (default: main)
            
        Returns:
            Tuple of (success, message)
        """
        if not self.template_dir:
            return False, "Template directory not configured"
        
        template_path = Path(self.template_dir)
        custom_dir = template_path / "github" / repo.replace("/", "_")
        
        try:
            # Check if directory already exists
            if custom_dir.exists():
                # Try to update via git pull
                result = subprocess.run(
                    ["git", "pull"],
                    cwd=custom_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    return True, f"Updated templates from {repo}"
                else:
                    return False, f"Failed to update: {result.stderr}"
            else:
                # Clone repository
                custom_dir.parent.mkdir(parents=True, exist_ok=True)
                repo_url = f"https://github.com/{repo}.git"
                
                result = subprocess.run(
                    ["git", "clone", "-b", branch, repo_url, str(custom_dir)],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    return True, f"Installed templates from {repo}"
                else:
                    return False, f"Failed to clone repository: {result.stderr}"
                    
        except subprocess.TimeoutExpired:
            return False, "Repository clone timed out"
        except FileNotFoundError:
            return False, "Git not found. Please install Git to clone repositories."
        except Exception as e:
            return False, f"Failed to install from repository: {str(e)}"
    
    def search_templates(
        self,
        query: str,
        severity: Optional[str] = None,
        author: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[Dict]:
        """
        Search installed templates.
        
        Args:
            query: Search query (searches name, description, id)
            severity: Filter by severity
            author: Filter by author
            tag: Filter by tag
            
        Returns:
            List of matching templates
        """
        all_templates = self.list_installed_templates()
        results = []
        
        query_lower = query.lower() if query else ""
        
        for template in all_templates:
            # Apply filters
            if severity and template.get("severity", "").lower() != severity.lower():
                continue
            
            if author:
                authors = template.get("author", [])
                if not any(author.lower() in str(a).lower() for a in authors):
                    continue
            
            if tag:
                tags = template.get("tags", [])
                if not any(tag.lower() in str(t).lower() for t in tags):
                    continue
            
            # Apply query search
            if query_lower:
                searchable_text = " ".join([
                    template.get("id", ""),
                    template.get("name", ""),
                    template.get("description", "")
                ]).lower()
                
                if query_lower not in searchable_text:
                    continue
            
            results.append(template)
        
        return results
    
    def get_template_info(self, template_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific template.
        
        Args:
            template_id: Template ID to look up
            
        Returns:
            Template dictionary or None if not found
        """
        templates = self.list_installed_templates()
        for template in templates:
            if template.get("id") == template_id:
                return template
        return None
    
    def get_template_categories(self) -> List[str]:
        """
        Get list of available template categories.
        
        Returns:
            List of category names
        """
        if not self.template_dir:
            return []
        
        template_path = Path(self.template_dir)
        if not template_path.exists():
            return []
        
        categories = set()
        
        # Get top-level directories
        for item in template_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                categories.add(item.name)
        
        return sorted(list(categories))
