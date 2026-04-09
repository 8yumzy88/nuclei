"""Armis API client for asset lookup via MCP server."""

import os
import json
from typing import Dict, Optional, List
from urllib.parse import quote


class ArmisClient:
    """Client for Armis API to lookup asset information via MCP server."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, config_manager = None):
        """
        Initialize Armis API client.
        
        Args:
            api_key: Armis API key. If None, reads from ARMIS_API_KEY env var.
            base_url: Armis MCP server base URL. If None, uses default MCP server URL.
            config_manager: Optional ConfigManager instance (not used for MCP, kept for compatibility)
        """
        # For MCP server, always read from environment variable
        self.api_key = api_key or os.getenv("ARMIS_API_KEY")
        
        # Default to MCP server URL if not provided
        if base_url:
            self.mcp_url = base_url.rstrip('/')
        elif config_manager:
            # Try config, but prefer MCP server
            config_url = config_manager.get_armis_base_url()
            self.mcp_url = (config_url or "https://revvity.armis.com/mcp").rstrip('/')
        else:
            # Default MCP server URL
            self.mcp_url = os.getenv("ARMIS_MCP_URL", "https://revvity.armis.com/mcp").rstrip('/')
        
        # Legacy base_url for compatibility (not used with MCP)
        self.base_url = self.mcp_url
    
    def lookup_asset(self, ip_address: str) -> Optional[Dict]:
        """
        Lookup asset information by IP address via MCP server.
        
        Args:
            ip_address: IP address to lookup
            
        Returns:
            Dictionary with asset information or None if not found/error
        """
        # Defensive check: Don't attempt API calls without proper credentials
        if not self.is_configured():
            return None
        
        # Additional validation: ensure API key and URL are not just whitespace
        if not self.api_key or not self.api_key.strip():
            return None
        if not self.mcp_url or not self.mcp_url.strip():
            return None
        
        try:
            import requests
            
            # Make MCP protocol request (JSON-RPC 2.0 format)
            # Try different MCP endpoint patterns
            mcp_payloads = [
                # Pattern 1: Direct device lookup endpoint
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "devices/search",
                    "params": {
                        "query": f"ipAddress:{ip_address}"
                    }
                },
                # Pattern 2: Generic search
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "search",
                    "params": {
                        "type": "device",
                        "query": f"ipAddress:{ip_address}"
                    }
                },
                # Pattern 3: REST-style endpoint (fallback)
                None  # Will try direct REST API call
            ]
            
            headers = {
                "Authorization": f"Bearer {self.api_key.strip()}",
                "Content-Type": "application/json"
            }
            
            # Try MCP protocol requests first
            for payload in mcp_payloads:
                if payload is None:
                    # Fallback to REST API style
                    try:
                        query = quote(f"ipAddress:{ip_address}")
                        url = f"{self.mcp_url.strip()}/api/v1/search/devices?q={query}"
                        response = requests.get(url, headers=headers, timeout=10)
                    except Exception:
                        continue
                else:
                    # MCP JSON-RPC request
                    try:
                        url = f"{self.mcp_url.strip()}"
                        response = requests.post(
                            url,
                            headers=headers,
                            json=payload,
                            timeout=10
                        )
                    except Exception:
                        continue
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Handle MCP JSON-RPC response
                        if "result" in data:
                            result = data["result"]
                            # Handle different response structures
                            if isinstance(result, list) and len(result) > 0:
                                device = result[0]
                            elif isinstance(result, dict) and "results" in result:
                                devices = result["results"]
                                if devices and len(devices) > 0:
                                    device = devices[0]
                                else:
                                    continue
                            elif isinstance(result, dict):
                                device = result
                            else:
                                continue
                        # Handle direct REST API response
                        elif "results" in data:
                            if data["results"] and len(data["results"]) > 0:
                                device = data["results"][0]
                            else:
                                continue
                        # Handle direct device object
                        elif isinstance(data, dict) and ("name" in data or "deviceName" in data):
                            device = data
                        else:
                            continue
                        
                        return self._format_armis_device(device, ip_address)
                    except (KeyError, ValueError, TypeError) as e:
                        # Try next pattern
                        continue
                        
        except Exception as e:
            # Silently fail - return None
            pass
        
        return None
    
    def _format_armis_device(self, device: Dict, ip_address: str) -> Dict:
        """
        Format Armis device data into standard format.
        
        Args:
            device: Raw device data from Armis API
            ip_address: IP address of the device
            
        Returns:
            Formatted device dictionary
        """
        return {
            'ip': ip_address,
            'name': device.get('name') or device.get('deviceName') or 'Unknown',
            'type': device.get('type') or device.get('deviceType') or 'Unknown',
            'manufacturer': device.get('manufacturer') or 'Unknown',
            'model': device.get('model') or device.get('deviceModel') or 'Unknown',
            'os': device.get('os') or device.get('operatingSystem') or 'Unknown',
            'risk_level': device.get('riskLevel') or device.get('risk') or 'Unknown',
            'tags': device.get('tags', []) or device.get('deviceTags', []),
            'last_seen': device.get('lastSeen') or device.get('last_seen') or 'Unknown'
        }
    
    def is_configured(self) -> bool:
        """
        Check if Armis client is properly configured.
        
        Returns:
            True if API key is set and non-empty (MCP URL has default)
        """
        # For MCP server, we only need the API key
        # The MCP URL has a default value
        api_key_valid = bool(self.api_key and self.api_key.strip())
        mcp_url_valid = bool(self.mcp_url and self.mcp_url.strip())
        return api_key_valid and mcp_url_valid
