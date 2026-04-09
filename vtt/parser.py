"""JSONL parsing and severity analysis."""

import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from .utils import format_severity, is_significant_severity


@dataclass
class Finding:
    """Represents a security finding."""
    severity: str
    name: str
    description: str
    host: str
    matched_at: str
    template_id: str
    template_path: Optional[str] = None
    url: Optional[str] = None
    ip: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert finding to dictionary."""
        return {
            "severity": self.severity,
            "name": self.name,
            "description": self.description,
            "host": self.host,
            "matched_at": self.matched_at,
            "template_id": self.template_id,
            "template_path": self.template_path,
            "url": self.url,
            "ip": self.ip
        }


class JSONLParser:
    """Parser for Nuclei JSONL output."""
    
    def parse_output(self, jsonl_output: str) -> List[Finding]:
        """
        Parse JSONL output from Nuclei.
        
        Args:
            jsonl_output: JSONL formatted string from Nuclei
            
        Returns:
            List of Finding objects
        """
        findings = []
        
        for line in jsonl_output.strip().split('\n'):
            if not line.strip():
                continue
            
            try:
                data = json.loads(line)
                finding = self._parse_finding(data)
                if finding:
                    findings.append(finding)
            except json.JSONDecodeError:
                # Skip invalid JSON lines
                continue
        
        return findings
    
    def _parse_finding(self, data: Dict) -> Optional[Finding]:
        """
        Parse a single finding from JSON data.
        
        Args:
            data: JSON object from Nuclei output
            
        Returns:
            Finding object or None if invalid
        """
        try:
            # Extract info block
            info = data.get("info", {})
            severity = info.get("severity", "unknown")
            name = info.get("name", "Unknown")
            description = info.get("description", "")
            
            # Extract location information
            host = data.get("host", data.get("matched-at", ""))
            matched_at = data.get("matched-at", data.get("host", ""))
            url = data.get("url", "")
            ip = data.get("ip", "")
            
            # Extract template information
            template_id = data.get("template-id", "")
            template_path = data.get("template-path", "")
            
            return Finding(
                severity=format_severity(severity),
                name=name,
                description=description or name,  # Use name if description is empty
                host=host,
                matched_at=matched_at,
                template_id=template_id,
                template_path=template_path,
                url=url,
                ip=ip
            )
        except (KeyError, TypeError) as e:
            # Skip malformed findings
            return None
    
    def filter_significant_findings(self, findings: List[Finding]) -> List[Finding]:
        """
        Filter findings to only include significant severities (Critical, High, Medium).
        
        Args:
            findings: List of all findings
            
        Returns:
            Filtered list of significant findings
        """
        return [
            finding for finding in findings
            if is_significant_severity(finding.severity)
        ]
    
    def group_by_severity(self, findings: List[Finding]) -> Dict[str, List[Finding]]:
        """
        Group findings by severity level.
        
        Args:
            findings: List of findings
            
        Returns:
            Dictionary mapping severity to list of findings
        """
        grouped = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": [],
            "unknown": []
        }
        
        for finding in findings:
            severity = finding.severity
            if severity in grouped:
                grouped[severity].append(finding)
            else:
                grouped["unknown"].append(finding)
        
        return grouped
    
    def analyze_findings(self, findings: List[Finding]) -> Dict:
        """
        Analyze findings and return structured summary.
        
        Args:
            findings: List of findings
            
        Returns:
            Dictionary with analysis results
        """
        significant = self.filter_significant_findings(findings)
        grouped = self.group_by_severity(findings)
        
        return {
            "total_findings": len(findings),
            "significant_findings": len(significant),
            "grouped_by_severity": {
                severity: len(finds) for severity, finds in grouped.items()
            },
            "findings": findings,
            "significant": significant
        }
