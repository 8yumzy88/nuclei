#!/usr/bin/env python3
"""VTT - Vulnerability Triage Tool CLI."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .config import ConfigManager
from .scanner import NucleiScanner, ScannerError
from .parser import JSONLParser
from .reporter import Reporter
from .template_manager import TemplateManager
from .utils import validate_target
from .validator import EnvironmentValidator
from .fingerprint import DeviceFingerprinter
from .armis_client import ArmisClient


def print_banner():
    """Print VTT banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║   Vulnerability Triage Tool (VTT)                        ║
║   Security Architecture and Engineering                   ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


def scan_targets_file(
    scanner: NucleiScanner,
    parser: JSONLParser,
    reporter: Reporter,
    targets_file: str,
    fingerprinter: Optional[DeviceFingerprinter] = None,
    armis_client: Optional[ArmisClient] = None
):
    """Scan targets from a file."""
    targets_path = Path(targets_file)
    
    if not targets_path.exists():
        print(f"Error: Targets file not found: {targets_file}")
        return
    
    # Read targets
    targets = []
    with open(targets_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                targets.append(line)
    
    if not targets:
        print(f"Error: No valid targets found in {targets_file}")
        return
    
    print(f"Scanning {len(targets)} target(s) from {targets_file}...")
    print("=" * 70)
    
    # Collect all results for batch reporting
    batch_results = []
    
    # Scan each target
    for target in targets:
        try:
            # Fingerprint device
            device_info = None
            if fingerprinter:
                device_info = fingerprinter.fingerprint_device(target)
            
            # Lookup in Armis
            armis_info = None
            if armis_client and armis_client.is_configured():
                # Extract IP from target
                ip = target.split('://')[-1].split('/')[0].split(':')[0]
                # Check if it's an IP address
                try:
                    import ipaddress
                    ipaddress.ip_address(ip)
                    armis_info = armis_client.lookup_asset(ip)
                except (ValueError, Exception):
                    pass
            
            # Run security scan
            output, return_code = scanner.run_scan(target)
            findings = parser.parse_output(output)
            analysis = parser.analyze_findings(findings)
            
            # Determine status
            significant = analysis["significant_findings"]
            status = 'ok' if significant == 0 else 'denied'
            
            batch_results.append({
                'target': target,
                'status': status,
                'findings': findings,
                'device_info': device_info,
                'armis_info': armis_info,
                'analysis': analysis
            })
            
        except ScannerError as e:
            print(f"✗ Error scanning {target}: {e}")
        except Exception as e:
            print(f"✗ Unexpected error scanning {target}: {e}")
    
    # Generate batch report
    if batch_results:
        batch_report = reporter.generate_batch_report(batch_results, include_ok=True)
        print("\n" + batch_report)


def scan_single_target(
    scanner: NucleiScanner,
    parser: JSONLParser,
    reporter: Reporter,
    target: str,
    fingerprinter: Optional[DeviceFingerprinter] = None,
    armis_client: Optional[ArmisClient] = None
):
    """Scan a single target."""
    # Validate target
    is_valid, error_msg = validate_target(target)
    if not is_valid:
        print(f"Error: {error_msg}")
        return
    
    print(f"Scanning: {target}")
    print("=" * 70)
    
    try:
        # Fingerprint device
        device_info = None
        if fingerprinter:
            print("Fingerprinting device...")
            device_info = fingerprinter.fingerprint_device(target)
        
        # Lookup in Armis
        armis_info = None
        if armis_client and armis_client.is_configured():
            # Extract IP from target
            ip = target.split('://')[-1].split('/')[0].split(':')[0]
            # Check if it's an IP address
            try:
                import ipaddress
                ipaddress.ip_address(ip)
                print("Looking up asset in Armis...")
                armis_info = armis_client.lookup_asset(ip)
            except (ValueError, Exception):
                pass
        
        # Run security scan
        print("Running security scan...")
        output, return_code = scanner.run_scan(target)
        findings = parser.parse_output(output)
        analysis = parser.analyze_findings(findings)
        
        # Generate report
        report = reporter.generate_report(target, findings, device_info, armis_info)
        print("\n" + report)
        
        # Print summary if there are findings
        if analysis["total_findings"] > 0:
            summary = reporter.generate_summary_report(
                target,
                analysis["total_findings"],
                analysis["significant_findings"],
                analysis["grouped_by_severity"]
            )
            print(f"\n{summary}")
            
    except ScannerError as e:
        print(f"Error scanning {target}: {e}")
    except Exception as e:
        print(f"Unexpected error scanning {target}: {e}")


def interactive_menu():
    """Display interactive menu."""
    config = ConfigManager()
    scanner = NucleiScanner(config)
    parser = JSONLParser()
    reporter = Reporter()
    template_manager = TemplateManager(config)
    fingerprinter = DeviceFingerprinter(config)
    armis_client = ArmisClient(config_manager=config)
    
    while True:
        print("\n" + "=" * 60)
        print("VTT Main Menu")
        print("=" * 60)
        print("1. Scan targets from targets.txt")
        print("2. Scan single target (manual input)")
        print("3. Manage Templates")
        print("4. Configuration")
        print("5. Validate Environment")
        print("6. Exit")
        print("=" * 60)
        
        choice = input("\nSelect an option (1-6): ").strip()
        
        if choice == "1":
            targets_file = "targets.txt"
            if not Path(targets_file).exists():
                print(f"\nError: {targets_file} not found in current directory.")
                print("Please create targets.txt with one target per line.")
                continue
            
            scan_targets_file(scanner, parser, reporter, targets_file, fingerprinter, armis_client)
            
        elif choice == "2":
            target = input("\nEnter target (FQDN, IP, or URL): ").strip()
            if target:
                scan_single_target(scanner, parser, reporter, target, fingerprinter, armis_client)
            else:
                print("Error: Target cannot be empty")
                
        elif choice == "3":
            template_menu(template_manager)
            
        elif choice == "4":
            config_menu(config)
            
        elif choice == "5":
            validate_environment(config)
            
        elif choice == "6":
            print("\nExiting VTT. Goodbye!")
            sys.exit(0)
            
        else:
            print("\nInvalid option. Please select 1-6.")


def template_menu(template_manager: TemplateManager):
    """Template management menu."""
    while True:
        print("\n" + "=" * 60)
        print("Template Management")
        print("=" * 60)
        print("1. List installed templates")
        print("2. Search templates")
        print("3. Browse online repositories")
        print("4. Install/Update templates")
        print("5. Install from GitHub repository")
        print("6. List template categories")
        print("7. Back to main menu")
        print("=" * 60)
        
        choice = input("\nSelect an option (1-7): ").strip()
        
        if choice == "1":
            category = input("Filter by category (optional, press Enter to skip): ").strip()
            category = category if category else None
            templates = template_manager.list_installed_templates(category)
            
            if not templates:
                print("\nNo templates found.")
                if not template_manager.template_dir:
                    print("Template directory not configured. Set it in Configuration menu.")
            else:
                print(f"\nFound {len(templates)} template(s):\n")
                for i, template in enumerate(templates[:50], 1):  # Limit to 50
                    severity = template.get('severity', 'unknown').upper()
                    name = template.get('name', 'Unknown')
                    template_id = template.get('id', 'N/A')
                    path = template.get('path', 'N/A')
                    
                    print(f"{i}. [{severity}] {name}")
                    if template_id and template_id != 'N/A':
                        print(f"   ID: {template_id}")
                    print(f"   Path: {path}")
                    if template.get('description'):
                        desc = template['description'][:100].replace('\n', ' ')
                        print(f"   Description: {desc}...")
                    if template.get('tags'):
                        tags_str = ', '.join(template['tags'][:5])
                        print(f"   Tags: {tags_str}")
                    print()
                
                if len(templates) > 50:
                    print(f"... and {len(templates) - 50} more templates")
                    print(f"\nTip: Use category filter to narrow results")
        
        elif choice == "2":
            query = input("Search query: ").strip()
            severity = input("Filter by severity (optional): ").strip() or None
            author = input("Filter by author (optional): ").strip() or None
            tag = input("Filter by tag (optional): ").strip() or None
            
            try:
                results = template_manager.search_templates(query, severity, author, tag)
                
                if not results:
                    print("\nNo matching templates found.")
                    print("Try:")
                    print("  - Different search terms")
                    print("  - Removing filters")
                    print("  - Checking template directory is configured")
                else:
                    print(f"\nFound {len(results)} matching template(s):\n")
                    for i, template in enumerate(results[:20], 1):
                        severity_display = template.get('severity', 'unknown').upper()
                        name = template.get('name', 'Unknown')
                        template_id = template.get('id', '')
                        
                        print(f"{i}. [{severity_display}] {name}")
                        if template_id:
                            print(f"   ID: {template_id}")
                        print(f"   Path: {template.get('path', 'N/A')}")
                        print()
                    
                    if len(results) > 20:
                        print(f"... and {len(results) - 20} more results")
            except Exception as e:
                print(f"\nError searching templates: {e}")
        
        elif choice == "3":
            repos = template_manager.browse_online_repositories()
            print("\nKnown Template Repositories:")
            print("=" * 60)
            for i, repo in enumerate(repos, 1):
                print(f"\n{i}. {repo['name']}")
                print(f"   Repository: {repo['repo']}")
                print(f"   Source: {repo['source']}")
                if repo.get('description'):
                    print(f"   Description: {repo['description']}")
        
        elif choice == "4":
            print("\nUpdating templates...")
            print("This may take a few minutes...")
            try:
                success, message = template_manager.install_templates()
                if success:
                    print(f"✓ {message}")
                else:
                    print(f"✗ {message}")
                    print("\nTroubleshooting:")
                    print("  - Verify Nuclei is installed: nuclei -version")
                    print("  - Check network connectivity")
                    print("  - Try running manually: nuclei -update-templates")
            except Exception as e:
                print(f"✗ Error: {e}")
        
        elif choice == "5":
            repo = input("GitHub repository (format: owner/repo): ").strip()
            if not repo:
                print("Error: Repository cannot be empty")
                continue
                
            if '/' not in repo:
                print("Error: Invalid format. Use: owner/repo (e.g., projectdiscovery/nuclei-templates)")
                continue
                
            branch = input("Branch (default: main): ").strip() or "main"
            print(f"\nInstalling templates from {repo} (branch: {branch})...")
            print("This may take a few minutes...")
            try:
                success, message = template_manager.install_from_github_repo(repo, branch)
                if success:
                    print(f"✓ {message}")
                    print(f"Templates installed to: {template_manager.template_dir}/github/{repo.replace('/', '_')}")
                else:
                    print(f"✗ {message}")
                    print("\nTroubleshooting:")
                    print("  - Verify Git is installed: git --version")
                    print("  - Check repository exists and is accessible")
                    print("  - Verify branch name is correct")
            except Exception as e:
                print(f"✗ Error: {e}")
        
        elif choice == "6":
            try:
                categories = template_manager.get_template_categories()
                if categories:
                    print(f"\nAvailable Template Categories ({len(categories)} total):")
                    print("=" * 60)
                    for cat in sorted(categories):
                        # Count templates in this category
                        cat_templates = template_manager.list_installed_templates(cat)
                        count = len(cat_templates)
                        print(f"  - {cat:<20} ({count} templates)")
                else:
                    print("\nNo template categories found.")
                    if not template_manager.template_dir:
                        print("Template directory not configured. Set it in Configuration menu.")
                    else:
                        print("Templates may not be installed. Run option 4 to install/update templates.")
            except Exception as e:
                print(f"\nError listing categories: {e}")
        
        elif choice == "7":
            break
        
        else:
            print("\nInvalid option. Please select 1-7.")


def validate_environment(config: ConfigManager):
    """Run environment validation."""
    print("\nRunning environment validation...")
    validator = EnvironmentValidator(config)
    all_passed, results = validator.validate_all()
    validator.print_report()
    
    if not all_passed:
        print("\nRecommendations:")
        print("- Run: uv pip install -r requirements.txt")
        print("- Run: nuclei -update-templates")
        print("- Check configuration settings (Option 4)")
        input("\nPress Enter to continue...")


def config_menu(config: ConfigManager):
    """Configuration menu."""
    while True:
        print("\n" + "=" * 60)
        print("Configuration")
        print("=" * 60)
        print(f"1. Nuclei binary path: {config.get_nuclei_path()}")
        template_dir = config.get_template_directory()
        print(f"2. Template directory: {template_dir or '(auto-detected)'}")
        armis_key = config.get_armis_api_key()
        print(f"3. Armis API key: {'***configured***' if armis_key else '(not set)'}")
        armis_url = config.get_armis_base_url()
        print(f"4. Armis base URL: {armis_url or '(not set)'}")
        print("5. View default template categories")
        print("6. Back to main menu")
        print("=" * 60)
        
        choice = input("\nSelect an option (1-6): ").strip()
        
        if choice == "1":
            new_path = input(f"Enter new Nuclei path (current: {config.get_nuclei_path()}): ").strip()
            if new_path:
                config.set_nuclei_path(new_path)
                print(f"✓ Nuclei path updated to: {new_path}")
            else:
                print("Path not changed")
        
        elif choice == "2":
            new_dir = input(f"Enter template directory (current: {template_dir or 'auto'}): ").strip()
            if new_dir:
                config.set_template_directory(new_dir)
                print(f"✓ Template directory updated to: {new_dir}")
            else:
                print("Directory not changed")
        
        elif choice == "3":
            new_key = input(f"Enter Armis API key (current: {'***set***' if armis_key else 'none'}): ").strip()
            if new_key:
                config.set_armis_api_key(new_key)
                print(f"✓ Armis API key updated")
            else:
                print("Key not changed")
        
        elif choice == "4":
            new_url = input(f"Enter Armis base URL (current: {armis_url or 'none'}): ").strip()
            if new_url:
                config.set_armis_base_url(new_url)
                print(f"✓ Armis base URL updated to: {new_url}")
            else:
                print("URL not changed")
        
        elif choice == "5":
            categories = config.get_default_template_categories()
            print("\nDefault Template Categories:")
            for cat in categories:
                print(f"  - {cat}")
        
        elif choice == "6":
            break
        
        else:
            print("\nInvalid option. Please select 1-6.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="VTT - Vulnerability Triage Tool for SAE",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "-t", "--target",
        help="Single target to scan (FQDN, IP, or URL)"
    )
    parser.add_argument(
        "-l", "--list",
        dest="targets_file",
        help="File containing targets to scan (one per line)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Don't print banner"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run environment validation and exit"
    )
    
    args = parser.parse_args()
    
    if not args.no_banner:
        print_banner()
    
    # Initialize components
    try:
        config = ConfigManager()
        scanner = NucleiScanner(config)
        parser_obj = JSONLParser()
        reporter = Reporter()
        fingerprinter = DeviceFingerprinter(config)
        armis_client = ArmisClient(config_manager=config)
    except ScannerError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
    
    # Run validation if requested
    if args.validate:
        validator = EnvironmentValidator(config)
        all_passed, results = validator.validate_all()
        validator.print_report()
        sys.exit(0 if all_passed else 1)
    
    # Run in interactive mode if requested or no arguments provided
    if args.interactive or (not args.target and not args.targets_file):
        interactive_menu()
        return
    
    # Non-interactive mode
    if args.targets_file:
        scan_targets_file(scanner, parser_obj, reporter, args.targets_file, fingerprinter, armis_client)
    elif args.target:
        scan_single_target(scanner, parser_obj, reporter, args.target, fingerprinter, armis_client)


if __name__ == "__main__":
    main()
