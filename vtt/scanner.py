"""Nuclei scanner execution wrapper."""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from .config import ConfigManager
from .utils import check_nuclei_installed


class ScannerError(Exception):
    """Exception raised for scanner errors."""
    pass


class NucleiScanner:
    """Wrapper for executing Nuclei scans."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize Nuclei scanner.
        
        Args:
            config_manager: Configuration manager instance. Creates new one if None.
        """
        self.config = config_manager or ConfigManager()
        self.nuclei_path = self.config.get_nuclei_path()
        self._verify_nuclei()
    
    def _verify_nuclei(self) -> None:
        """Verify Nuclei binary is available."""
        is_installed, error_msg = check_nuclei_installed(self.nuclei_path)
        if not is_installed:
            raise ScannerError(f"Cannot initialize scanner: {error_msg}")
    
    def run_scan(
        self,
        target: str,
        template_categories: Optional[List[str]] = None,
        targets_file: Optional[str] = None,
        timeout: int = 300
    ) -> Tuple[str, int]:
        """
        Run Nuclei scan against target(s).
        
        Args:
            target: Single target (FQDN, IP, or URL). Ignored if targets_file is provided.
            template_categories: List of template categories to use. Defaults to config defaults.
            targets_file: Path to file containing targets (one per line). Overrides target.
            timeout: Maximum execution time in seconds.
            
        Returns:
            Tuple of (jsonl_output, return_code)
            
        Raises:
            ScannerError: If scan execution fails
        """
        if template_categories is None:
            template_categories = self.config.get_default_template_categories()
        
        # Build command
        cmd = [self.nuclei_path, "-silent", "-jsonl", "-nh"]
        
        # Add template categories
        for category in template_categories:
            cmd.extend(["-t", category])
        
        # Add target(s)
        if targets_file:
            targets_path = Path(targets_file)
            if not targets_path.exists():
                raise ScannerError(f"Targets file not found: {targets_file}")
            cmd.extend(["-l", str(targets_path)])
        elif target:
            cmd.extend(["-u", target])
        else:
            raise ScannerError("Either target or targets_file must be provided")
        
        # Execute scan
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.stdout, result.returncode
            
        except subprocess.TimeoutExpired:
            raise ScannerError(f"Scan timed out after {timeout} seconds")
        except Exception as e:
            raise ScannerError(f"Failed to execute Nuclei scan: {str(e)}")
    
    def run_scan_multiple_targets(
        self,
        targets: List[str],
        template_categories: Optional[List[str]] = None,
        timeout: int = 300
    ) -> Tuple[str, int]:
        """
        Run Nuclei scan against multiple targets.
        
        Args:
            targets: List of targets (FQDNs, IPs, or URLs)
            template_categories: List of template categories to use
            timeout: Maximum execution time in seconds
            
        Returns:
            Tuple of (jsonl_output, return_code)
        """
        if template_categories is None:
            template_categories = self.config.get_default_template_categories()
        
        # Build command
        cmd = [self.nuclei_path, "-silent", "-jsonl", "-nh"]
        
        # Add template categories
        for category in template_categories:
            cmd.extend(["-t", category])
        
        # Add all targets
        for target in targets:
            cmd.extend(["-u", target])
        
        # Execute scan
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.stdout, result.returncode
            
        except subprocess.TimeoutExpired:
            raise ScannerError(f"Scan timed out after {timeout} seconds")
        except Exception as e:
            raise ScannerError(f"Failed to execute Nuclei scan: {str(e)}")
