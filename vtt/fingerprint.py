"""Device fingerprinting using Nuclei tech-detect templates."""

import subprocess
from typing import Dict, Optional, List
from .config import ConfigManager
from .parser import JSONLParser


class DeviceFingerprinter:
    """Fingerprints devices using Nuclei tech-detect templates."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize device fingerprinter.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager or ConfigManager()
        self.nuclei_path = self.config.get_nuclei_path()
        self.parser = JSONLParser()
    
    def fingerprint_device(self, target: str, timeout: int = 30) -> Dict[str, any]:
        """
        Fingerprint a device to identify technologies and services.
        
        Args:
            target: Target to fingerprint (IP, FQDN, or URL)
            timeout: Maximum execution time in seconds
            
        Returns:
            Dictionary with fingerprint information:
            {
                'technologies': List[str],
                'services': List[str],
                'os': Optional[str],
                'server': Optional[str],
                'raw_findings': List[Dict]
            }
        """
        # Use Nuclei's tech-detect templates and automatic scan
        # Try tech-detect tag first, then fallback to automatic scan
        cmd = [
            self.nuclei_path,
            "-silent",
            "-jsonl",
            "-nh",
            "-as",  # Automatic scan mode (uses wappalyzer technology detection)
            "-u", target
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            findings = self.parser.parse_output(result.stdout)
            
            # Extract technologies and services
            technologies = []
            services = []
            os_info = None
            server_info = None
            
            for finding in findings:
                name = finding.name.lower()
                description = finding.description.lower() if finding.description else ""
                
                # Extract technology names
                if "tech" in name or "detect" in name:
                    tech_name = finding.name.replace(" Detection", "").replace(" Detect", "")
                    technologies.append(tech_name)
                
                # Extract OS information
                if "os" in name or "operating system" in description:
                    os_info = finding.name
                
                # Extract server information
                if "server" in name and ("software" in name or "version" in name):
                    server_info = finding.name
                
                # Extract service information
                if any(svc in name for svc in ["http", "https", "ssh", "ftp", "smtp", "dns", "rdp", "vnc"]):
                    services.append(finding.name)
            
            return {
                'technologies': list(set(technologies)),
                'services': list(set(services)),
                'os': os_info,
                'server': server_info,
                'raw_findings': [f.to_dict() for f in findings]
            }
            
        except subprocess.TimeoutExpired:
            return {
                'technologies': [],
                'services': [],
                'os': None,
                'server': None,
                'raw_findings': [],
                'error': 'Fingerprinting timed out'
            }
        except Exception as e:
            return {
                'technologies': [],
                'services': [],
                'os': None,
                'server': None,
                'raw_findings': [],
                'error': str(e)
            }
