"""Configuration management for VTT."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class VTTConfig:
    """VTT configuration settings."""
    nuclei_binary_path: str = "/opt/homebrew/bin/nuclei"
    template_directory: Optional[str] = None
    default_template_categories: List[str] = None
    known_repositories: List[Dict[str, str]] = None
    armis_api_key: Optional[str] = None
    armis_base_url: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.default_template_categories is None:
            self.default_template_categories = [
                "ssl",
                "exposures",
                "misconfiguration",
                "default-login",
                "network/"
            ]
        if self.known_repositories is None:
            self.known_repositories = [
                {
                    "name": "Official Nuclei Templates",
                    "repo": "projectdiscovery/nuclei-templates",
                    "source": "github",
                    "description": "Official templates repository maintained by ProjectDiscovery"
                }
            ]


class ConfigManager:
    """Manages VTT configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to config file. Defaults to ~/.vtt/config.json
        """
        if config_path is None:
            config_dir = Path.home() / ".vtt"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "config.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> VTTConfig:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    return VTTConfig(**data)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Warning: Failed to load config: {e}. Using defaults.")
                return VTTConfig()
        else:
            config = VTTConfig()
            self._save_config(config)
            return config
    
    def _save_config(self, config: VTTConfig) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(asdict(config), f, indent=2)
    
    def get_nuclei_path(self) -> str:
        """Get Nuclei binary path."""
        return self.config.nuclei_binary_path
    
    def set_nuclei_path(self, path: str) -> None:
        """Set Nuclei binary path."""
        self.config.nuclei_binary_path = path
        self._save_config(self.config)
    
    def get_template_directory(self) -> Optional[str]:
        """Get template directory path."""
        return self.config.template_directory
    
    def set_template_directory(self, path: str) -> None:
        """Set template directory path."""
        self.config.template_directory = path
        self._save_config(self.config)
    
    def get_default_template_categories(self) -> List[str]:
        """Get default template categories."""
        return self.config.default_template_categories
    
    def get_known_repositories(self) -> List[Dict[str, str]]:
        """Get known template repositories."""
        return self.config.known_repositories
    
    def add_repository(self, name: str, repo: str, source: str = "github", description: str = "") -> None:
        """Add a new template repository."""
        repo_dict = {
            "name": name,
            "repo": repo,
            "source": source,
            "description": description
        }
        if repo_dict not in self.config.known_repositories:
            self.config.known_repositories.append(repo_dict)
            self._save_config(self.config)
    
    def get_armis_api_key(self) -> Optional[str]:
        """Get Armis API key (from config or environment)."""
        if self.config.armis_api_key:
            return self.config.armis_api_key
        import os
        return os.getenv("ARMIS_API_KEY")
    
    def get_armis_base_url(self) -> Optional[str]:
        """Get Armis base URL (from config or environment)."""
        if self.config.armis_base_url:
            return self.config.armis_base_url
        import os
        return os.getenv("ARMIS_BASE_URL")
    
    def set_armis_api_key(self, api_key: str) -> None:
        """Set Armis API key."""
        self.config.armis_api_key = api_key
        self._save_config(self.config)
    
    def set_armis_base_url(self, base_url: str) -> None:
        """Set Armis base URL."""
        self.config.armis_base_url = base_url
        self._save_config(self.config)
    
    def save(self) -> None:
        """Save current configuration."""
        self._save_config(self.config)
