"""Utility functions for VTT."""

import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple
import ipaddress


def validate_target(target: str) -> Tuple[bool, Optional[str]]:
    """
    Validate target format (FQDN or IP address).
    
    Args:
        target: Target string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    target = target.strip()
    
    if not target:
        return False, "Target cannot be empty"
    
    # Check if it's a URL
    if target.startswith(('http://', 'https://')):
        # Extract hostname from URL
        try:
            from urllib.parse import urlparse
            parsed = urlparse(target)
            hostname = parsed.netloc.split(':')[0]  # Remove port if present
            if not hostname:
                return False, "Invalid URL format"
            # Validate the hostname part
            return validate_target(hostname)
        except Exception:
            return False, "Invalid URL format"
    
    # Check if it's an IP address
    try:
        ipaddress.ip_address(target)
        return True, None
    except ValueError:
        pass
    
    # Check if it's a valid FQDN
    # Basic FQDN validation: alphanumeric, dots, hyphens
    fqdn_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if re.match(fqdn_pattern, target):
        return True, None
    
    # Also allow simple hostnames (single word)
    if re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$', target):
        return True, None
    
    return False, f"Invalid target format: {target}. Must be FQDN, IP address, or URL"


def check_nuclei_installed(nuclei_path: str) -> Tuple[bool, Optional[str]]:
    """
    Verify Nuclei binary exists and is executable.
    
    Args:
        nuclei_path: Path to Nuclei binary
        
    Returns:
        Tuple of (is_installed, error_message)
    """
    path = Path(nuclei_path)
    
    if not path.exists():
        return False, f"Nuclei binary not found at {nuclei_path}"
    
    if not path.is_file():
        return False, f"Nuclei path is not a file: {nuclei_path}"
    
    if not os.access(path, os.X_OK):
        return False, f"Nuclei binary is not executable: {nuclei_path}"
    
    # Try to run nuclei --version to verify it works
    try:
        result = subprocess.run(
            [str(path), "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return False, f"Nuclei binary exists but failed to execute: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Nuclei binary timed out during verification"
    except Exception as e:
        return False, f"Error verifying Nuclei binary: {str(e)}"
    
    return True, None


def get_template_directory() -> Optional[str]:
    """
    Query Nuclei config for template directory location.
    
    Returns:
        Template directory path or None if not found
    """
    # Check NUCLEI_TEMPLATES_DIR environment variable
    env_dir = os.environ.get("NUCLEI_TEMPLATES_DIR")
    if env_dir and Path(env_dir).exists():
        return env_dir
    
    # Check default locations
    default_locations = [
        Path.home() / ".nuclei-templates",
        Path.home() / ".config" / "nuclei" / "templates",
    ]
    
    for location in default_locations:
        if location.exists() and location.is_dir():
            return str(location)
    
    # Try to query Nuclei config file
    config_paths = [
        Path.home() / ".config" / "nuclei" / "config.yaml",
        Path.home() / ".nuclei-config" / "config.yaml",
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            try:
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if isinstance(config, dict) and 'templates-directory' in config:
                        template_dir = Path(config['templates-directory'])
                        if template_dir.exists():
                            return str(template_dir)
            except Exception:
                # If YAML parsing fails, continue to next location
                continue
    
    return None


def format_severity(severity: str) -> str:
    """
    Normalize severity string to standard format.
    
    Args:
        severity: Severity string (case-insensitive)
        
    Returns:
        Normalized severity string (critical, high, medium, low, info, unknown)
    """
    severity_lower = severity.lower().strip()
    
    severity_map = {
        'critical': 'critical',
        'high': 'high',
        'medium': 'medium',
        'low': 'low',
        'info': 'info',
        'information': 'info',
        'unknown': 'unknown',
    }
    
    return severity_map.get(severity_lower, 'unknown')


def is_significant_severity(severity: str) -> bool:
    """
    Check if severity is significant (Critical, High, or Medium).
    
    Args:
        severity: Severity string
        
    Returns:
        True if severity is Critical, High, or Medium
    """
    normalized = format_severity(severity)
    return normalized in ['critical', 'high', 'medium']
