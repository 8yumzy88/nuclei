"""ServiceNow report generation with improved formatting and colors."""

from typing import List, Optional, Dict
from tabulate import tabulate

try:
    from colorama import Fore, Back, Style, init
    # Initialize colorama for cross-platform color support
    init(autoreset=True, strip=False)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    # Fallback color codes if colorama not available
    class Fore:
        GREEN = '\033[92m'
        RED = '\033[91m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        MAGENTA = '\033[95m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        RESET = '\033[0m'
    class Style:
        BRIGHT = '\033[1m'
        DIM = '\033[2m'
        RESET_ALL = '\033[0m'

from .parser import Finding


class Reporter:
    """Generates ServiceNow-formatted reports with tables, colors, and improved formatting."""
    
    # Color mapping for severities
    SEVERITY_COLORS = {
        'critical': Fore.RED + Style.BRIGHT if HAS_COLORAMA else '\033[91m\033[1m',
        'high': Fore.RED if HAS_COLORAMA else '\033[91m',
        'medium': Fore.YELLOW if HAS_COLORAMA else '\033[93m',
        'low': Fore.CYAN if HAS_COLORAMA else '\033[96m',
        'info': Fore.BLUE if HAS_COLORAMA else '\033[94m',
        'unknown': Fore.WHITE if HAS_COLORAMA else '\033[97m',
    }
    
    RESET = Fore.RESET if HAS_COLORAMA else '\033[0m'
    
    @staticmethod
    def _color_severity(severity: str) -> str:
        """Get colored severity string."""
        severity_lower = severity.lower()
        color = Reporter.SEVERITY_COLORS.get(severity_lower, Reporter.RESET)
        return f"{color}{severity.upper()}{Reporter.RESET}"
    
    def generate_report(
        self,
        target: str,
        findings: List[Finding],
        device_info: Optional[Dict] = None,
        armis_info: Optional[Dict] = None,
        include_low_severity: bool = False
    ) -> str:
        """
        Generate report for target based on findings.
        
        Args:
            target: Target that was scanned
            findings: List of findings from scan
            device_info: Device fingerprinting information
            armis_info: Armis asset information
            include_low_severity: Whether to include low severity findings in DENIED report
            
        Returns:
            Formatted report string
        """
        # Filter significant findings (Critical, High, Medium)
        significant_findings = [
            f for f in findings
            if f.severity in ['critical', 'high', 'medium']
        ]
        
        # If including low severity, add those too
        if include_low_severity:
            low_findings = [f for f in findings if f.severity == 'low']
            significant_findings.extend(low_findings)
        
        if not significant_findings:
            return self._generate_ok_report(target, device_info, armis_info)
        else:
            return self._generate_denied_report(target, significant_findings, device_info, armis_info)
    
    def _generate_ok_report(
        self,
        target: str,
        device_info: Optional[Dict] = None,
        armis_info: Optional[Dict] = None
    ) -> str:
        """
        Generate simplified OK approval report with color.
        
        Args:
            target: Target that was scanned
            device_info: Device fingerprinting information
            armis_info: Armis asset information
            
        Returns:
            Simplified OK report string with color
        """
        # Extract IP or hostname
        display_target = target.split('://')[-1].split('/')[0]
        
        # Build device identification
        device_parts = []
        if armis_info:
            if armis_info.get('name') and armis_info['name'] != 'Unknown':
                device_parts.append(armis_info['name'])
            if armis_info.get('type') and armis_info['type'] != 'Unknown':
                device_parts.append(f"({armis_info['type']})")
        elif device_info:
            if device_info.get('server'):
                device_parts.append(device_info['server'])
            if device_info.get('os'):
                device_parts.append(f"({device_info['os']})")
        
        device_str = f" {Fore.CYAN}- {' '.join(device_parts)}{Fore.RESET}" if device_parts else ""
        
        return f"{Fore.GREEN}✓ OK{Fore.RESET}  {Fore.WHITE}{Style.BRIGHT}{display_target}{Fore.RESET}{device_str}"
    
    def _generate_denied_report(
        self,
        target: str,
        findings: List[Finding],
        device_info: Optional[Dict] = None,
        armis_info: Optional[Dict] = None
    ) -> str:
        """
        Generate DENIED report with findings in colored table format.
        
        Args:
            target: Target that was scanned
            findings: List of significant findings
            device_info: Device fingerprinting information
            armis_info: Armis asset information
            
        Returns:
            DENIED report string with colors and tables
        """
        # Extract IP or hostname
        display_target = target.split('://')[-1].split('/')[0]
        
        # Build device info table
        device_rows = []
        if armis_info:
            if armis_info.get('name') and armis_info['name'] != 'Unknown':
                device_rows.append(['Name', armis_info['name']])
            if armis_info.get('type') and armis_info['type'] != 'Unknown':
                device_rows.append(['Type', armis_info['type']])
            if armis_info.get('manufacturer') and armis_info['manufacturer'] != 'Unknown':
                device_rows.append(['Manufacturer', armis_info['manufacturer']])
            if armis_info.get('model') and armis_info['model'] != 'Unknown':
                device_rows.append(['Model', armis_info['model']])
            if armis_info.get('os') and armis_info['os'] != 'Unknown':
                device_rows.append(['OS', armis_info['os']])
        elif device_info:
            if device_info.get('server'):
                device_rows.append(['Server', device_info['server']])
            if device_info.get('os'):
                device_rows.append(['OS', device_info['os']])
            if device_info.get('technologies'):
                device_rows.append(['Technologies', ', '.join(device_info['technologies'][:5])])
        
        # Build findings table with colors
        table_data = []
        for finding in findings:
            severity = finding.severity.lower()
            color = self.SEVERITY_COLORS.get(severity, '')
            severity_display = f"{color}{severity.upper()}{self.RESET}"
            name = finding.name[:60]  # Truncate long names
            description = (finding.description or name)[:70]  # Truncate descriptions
            table_data.append([severity_display, name, description])
        
        findings_table = tabulate(
            table_data,
            headers=[f"{Fore.WHITE}{Style.BRIGHT}Severity{self.RESET}", 
                    f"{Fore.WHITE}{Style.BRIGHT}Issue{self.RESET}", 
                    f"{Fore.WHITE}{Style.BRIGHT}Description{self.RESET}"],
            tablefmt="grid"
        )
        
        # Build report with minimal text
        report_lines = []
        
        # Header
        report_lines.append(f"{Fore.RED}{Style.BRIGHT}✗ DENIED{self.RESET}  {Fore.WHITE}{Style.BRIGHT}{display_target}{self.RESET}")
        
        # Device info table (if available)
        if device_rows:
            device_table = tabulate(device_rows, headers=[f"{Fore.CYAN}Property{self.RESET}", f"{Fore.CYAN}Value{self.RESET}"], tablefmt="simple")
            report_lines.append(f"\n{Fore.CYAN}Device Info:{self.RESET}")
            report_lines.append(device_table)
        
        # Findings table
        report_lines.append(f"\n{Fore.YELLOW}{Style.BRIGHT}Findings ({len(findings)}):{self.RESET}")
        report_lines.append(findings_table)
        
        # Minimal remediation
        report_lines.append(f"\n{Fore.MAGENTA}Remediation:{self.RESET} Review and address vulnerabilities. Refer to IT Policies.")
        
        return "\n".join(report_lines)
    
    def generate_batch_report(
        self,
        results: List[Dict],
        include_ok: bool = True
    ) -> str:
        """
        Generate a batch report with grouped OK and DENIED results in colored tables.
        
        Args:
            results: List of result dictionaries
            include_ok: Whether to include OK results in output
            
        Returns:
            Formatted batch report string with colors
        """
        ok_results = [r for r in results if r.get('status') == 'ok']
        denied_results = [r for r in results if r.get('status') == 'denied']
        
        report_lines = []
        
        # Summary table with colors
        summary_data = [
            [f"{Fore.WHITE}{Style.BRIGHT}Total Scanned{self.RESET}", f"{Fore.CYAN}{len(results)}{self.RESET}"],
            [f"{Fore.GREEN}✓ Approved{self.RESET}", f"{Fore.GREEN}{len(ok_results)}{self.RESET}"],
            [f"{Fore.RED}✗ Denied{self.RESET}", f"{Fore.RED}{len(denied_results)}{self.RESET}"]
        ]
        summary_table = tabulate(summary_data, tablefmt="grid")
        
        report_lines.append(f"{Fore.WHITE}{Style.BRIGHT}{'='*70}{self.RESET}")
        report_lines.append(f"{Fore.WHITE}{Style.BRIGHT}VTT BATCH SCAN RESULTS{self.RESET}")
        report_lines.append(f"{Fore.WHITE}{Style.BRIGHT}{'='*70}{self.RESET}\n")
        report_lines.append(summary_table)
        
        # OK Results (simplified table)
        if include_ok and ok_results:
            report_lines.append(f"\n{Fore.GREEN}{Style.BRIGHT}APPROVED ({len(ok_results)}){self.RESET}")
            
            ok_table_data = []
            for result in ok_results:
                target = result['target'].split('://')[-1].split('/')[0]
                device_str = ""
                
                armis = result.get('armis_info')
                device = result.get('device_info')
                
                if armis:
                    if armis.get('name') and armis['name'] != 'Unknown':
                        device_str = armis['name']
                    elif armis.get('type') and armis['type'] != 'Unknown':
                        device_str = armis['type']
                elif device:
                    if device.get('server'):
                        device_str = device['server']
                    elif device.get('os'):
                        device_str = device['os']
                
                ok_table_data.append([
                    f"{Fore.GREEN}{target}{self.RESET}",
                    f"{Fore.CYAN}{device_str or 'Unknown'}{self.RESET}"
                ])
            
            ok_table = tabulate(
                ok_table_data, 
                headers=[f"{Fore.WHITE}Target{self.RESET}", f"{Fore.WHITE}Device{self.RESET}"], 
                tablefmt="simple"
            )
            report_lines.append(ok_table)
        
        # DENIED Results (compact format)
        if denied_results:
            report_lines.append(f"\n{Fore.RED}{Style.BRIGHT}DENIED ({len(denied_results)}){self.RESET}\n")
            
            for i, result in enumerate(denied_results, 1):
                target = result['target']
                findings = result.get('findings', [])
                device_info = result.get('device_info')
                armis_info = result.get('armis_info')
                
                # Compact denied report
                display_target = target.split('://')[-1].split('/')[0]
                report_lines.append(f"{Fore.RED}✗ {display_target}{self.RESET} - {Fore.YELLOW}{len(findings)} finding(s){self.RESET}")
                
                # Show device info inline if available
                device_parts = []
                if armis_info:
                    if armis_info.get('name') and armis_info['name'] != 'Unknown':
                        device_parts.append(armis_info['name'])
                elif device_info:
                    if device_info.get('server'):
                        device_parts.append(device_info['server'])
                
                if device_parts:
                    report_lines.append(f"  {Fore.CYAN}Device:{self.RESET} {', '.join(device_parts)}")
                
                # Show top 3 findings
                for finding in findings[:3]:
                    severity_color = self.SEVERITY_COLORS.get(finding.severity.lower(), '')
                    report_lines.append(f"  {severity_color}• {finding.severity.upper()}{self.RESET}: {finding.name[:50]}")
                
                if len(findings) > 3:
                    report_lines.append(f"  {Fore.DIM}... and {len(findings) - 3} more{self.RESET}")
                
                if i < len(denied_results):
                    report_lines.append("")  # Spacing between denied items
        
        return "\n".join(report_lines)
    
    def generate_summary_report(
        self,
        target: str,
        total_findings: int,
        significant_findings: int,
        severity_counts: dict
    ) -> str:
        """
        Generate a summary report with statistics in colored table.
        
        Args:
            target: Target that was scanned
            total_findings: Total number of findings
            significant_findings: Number of significant findings
            severity_counts: Dictionary mapping severity to count
            
        Returns:
            Summary report string with colors
        """
        summary_data = [
            [f"{Fore.WHITE}Target{self.RESET}", target],
            [f"{Fore.CYAN}Total Findings{self.RESET}", str(total_findings)],
            [f"{Fore.YELLOW}Significant{self.RESET}", str(significant_findings)],
        ]
        
        for severity in ['critical', 'high', 'medium', 'low', 'info', 'unknown']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                color = self.SEVERITY_COLORS.get(severity, '')
                summary_data.append([f"{color}{severity.capitalize()}{self.RESET}", str(count)])
        
        return tabulate(summary_data, headers=[f"{Fore.WHITE}{Style.BRIGHT}Metric{self.RESET}", f"{Fore.WHITE}{Style.BRIGHT}Value{self.RESET}"], tablefmt="grid")
