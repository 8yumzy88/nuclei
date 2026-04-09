"""Environment validation for VTT."""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict
from .config import ConfigManager
from .utils import check_nuclei_installed, get_template_directory


class ValidationResult:
    """Represents a validation check result."""
    
    def __init__(self, name: str, status: bool, message: str, details: str = ""):
        self.name = name
        self.status = status
        self.message = message
        self.details = details
    
    def __repr__(self):
        status_icon = "✓" if self.status else "✗"
        return f"{status_icon} {self.name}: {self.message}"


class EnvironmentValidator:
    """Validates VTT environment and requirements."""
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        Initialize environment validator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager or ConfigManager()
        self.results: List[ValidationResult] = []
    
    def validate_all(self) -> Tuple[bool, List[ValidationResult]]:
        """
        Run all validation checks.
        
        Returns:
            Tuple of (all_passed, results_list)
        """
        self.results = []
        
        # Run all checks
        self._check_python_version()
        self._check_python_packages()
        self._check_nuclei_binary()
        self._check_nuclei_version()
        self._check_template_directory()
        self._check_templates_installed()
        self._check_config_file()
        self._check_write_permissions()
        
        # Determine overall status
        all_passed = all(result.status for result in self.results)
        
        return all_passed, self.results
    
    def _check_python_version(self) -> None:
        """Check Python version (3.8+ required)."""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major >= 3 and version.minor >= 8:
            self.results.append(ValidationResult(
                "Python Version",
                True,
                f"Python {version_str} (3.8+ required)",
                f"Major: {version.major}, Minor: {version.minor}, Micro: {version.micro}"
            ))
        else:
            self.results.append(ValidationResult(
                "Python Version",
                False,
                f"Python {version_str} (3.8+ required)",
                f"Current version is too old. Please upgrade to Python 3.8 or higher."
            ))
    
    def _check_python_packages(self) -> None:
        """Check required Python packages."""
        required_packages = {
            'yaml': 'pyyaml',
            'requests': 'requests',
        }
        
        missing_packages = []
        installed_packages = []
        
        for module_name, package_name in required_packages.items():
            try:
                __import__(module_name)
                installed_packages.append(package_name)
            except ImportError:
                missing_packages.append(package_name)
        
        # Also check if requirements.txt exists and mentions these packages
        requirements_file = Path.cwd() / "requirements.txt"
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r') as f:
                    requirements_content = f.read()
                    # Check if packages are mentioned in requirements.txt
                    for pkg in missing_packages:
                        if pkg.lower() in requirements_content.lower():
                            # Package is in requirements.txt but not installed
                            pass
            except Exception:
                pass
        
        if not missing_packages:
            self.results.append(ValidationResult(
                "Python Packages",
                True,
                f"All required packages installed ({', '.join(installed_packages)})",
                f"Installed: {', '.join(installed_packages)}"
            ))
        else:
            # Check if requirements.txt exists
            requirements_file = Path.cwd() / "requirements.txt"
            if requirements_file.exists():
                details = f"Run: uv pip install -r requirements.txt (or: uv pip install {' '.join(missing_packages)})"
            else:
                details = f"Run: uv pip install {' '.join(missing_packages)}"
            
            self.results.append(ValidationResult(
                "Python Packages",
                False,
                f"Missing packages: {', '.join(missing_packages)}",
                details
            ))
    
    def _check_nuclei_binary(self) -> None:
        """Check Nuclei binary exists and is executable."""
        nuclei_path = self.config.get_nuclei_path()
        is_installed, error_msg = check_nuclei_installed(nuclei_path)
        
        if is_installed:
            self.results.append(ValidationResult(
                "Nuclei Binary",
                True,
                f"Nuclei found at {nuclei_path}",
                f"Binary exists and is executable"
            ))
        else:
            self.results.append(ValidationResult(
                "Nuclei Binary",
                False,
                f"Nuclei not found at {nuclei_path}",
                f"Error: {error_msg}. Update path in configuration."
            ))
    
    def _check_nuclei_version(self) -> None:
        """Check Nuclei version."""
        nuclei_path = self.config.get_nuclei_path()
        
        if not Path(nuclei_path).exists():
            self.results.append(ValidationResult(
                "Nuclei Version",
                False,
                "Cannot check version (binary not found)",
                ""
            ))
            return
        
        try:
            result = subprocess.run(
                [nuclei_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version_output = result.stdout.strip()
                self.results.append(ValidationResult(
                    "Nuclei Version",
                    True,
                    f"Nuclei version: {version_output.split()[0] if version_output else 'Unknown'}",
                    version_output
                ))
            else:
                self.results.append(ValidationResult(
                    "Nuclei Version",
                    False,
                    "Failed to get Nuclei version",
                    result.stderr
                ))
        except Exception as e:
            self.results.append(ValidationResult(
                "Nuclei Version",
                False,
                f"Error checking version: {str(e)}",
                ""
            ))
    
    def _check_template_directory(self) -> None:
        """Check template directory exists."""
        # Try config first
        template_dir = self.config.get_template_directory()
        
        # Try auto-detection
        if not template_dir:
            template_dir = get_template_directory()
        
        # Check alternative locations
        if not template_dir:
            # Check default location
            default_dir = Path.home() / ".nuclei-templates"
            if default_dir.exists():
                template_dir = str(default_dir)
            # Check user home nuclei-templates (common alternative)
            elif (Path.home() / "nuclei-templates").exists():
                template_dir = str(Path.home() / "nuclei-templates")
        
        if template_dir and Path(template_dir).exists():
            template_path = Path(template_dir)
            yaml_count = len(list(template_path.rglob("*.yaml")))
            
            self.results.append(ValidationResult(
                "Template Directory",
                True,
                f"Templates directory found: {template_dir}",
                f"Contains {yaml_count} YAML template file(s)"
            ))
        else:
            self.results.append(ValidationResult(
                "Template Directory",
                False,
                "Template directory not found",
                "Run: nuclei -update-templates or configure template directory"
            ))
    
    def _check_templates_installed(self) -> None:
        """Check if templates are installed."""
        template_dir = self.config.get_template_directory()
        if not template_dir:
            template_dir = get_template_directory()
        
        if not template_dir:
            default_dir = Path.home() / ".nuclei-templates"
            if default_dir.exists():
                template_dir = str(default_dir)
        
        if not template_dir or not Path(template_dir).exists():
            self.results.append(ValidationResult(
                "Templates Installed",
                False,
                "Cannot check templates (directory not found)",
                ""
            ))
            return
        
        template_path = Path(template_dir)
        
        # Check for required categories
        required_categories = self.config.get_default_template_categories()
        found_categories = []
        missing_categories = []
        
        for category in required_categories:
            # Remove trailing slash for directory check
            cat_clean = category.rstrip('/')
            category_path = template_path / cat_clean
            
            # Also check if it's a directory or if templates with this tag exist
            if category_path.exists() and category_path.is_dir():
                yaml_files = list(category_path.rglob("*.yaml"))
                if yaml_files:
                    found_categories.append(category)
                else:
                    missing_categories.append(category)
            else:
                # Check if any templates have this tag in their path
                matching = list(template_path.rglob(f"*{cat_clean}*.yaml"))
                if matching:
                    found_categories.append(category)
                else:
                    missing_categories.append(category)
        
        # Check if we have at least some templates installed
        total_templates = len(list(template_path.rglob("*.yaml")))
        
        if total_templates == 0:
            self.results.append(ValidationResult(
                "Templates Installed",
                False,
                "No templates found in template directory",
                "Run: nuclei -update-templates"
            ))
        elif missing_categories and len(found_categories) == 0:
            # No required categories found, but templates exist
            self.results.append(ValidationResult(
                "Templates Installed",
                False,
                f"Required categories not found: {', '.join(missing_categories)}",
                f"Found {total_templates} templates total, but none in required categories"
            ))
        elif missing_categories:
            # Some categories missing, but some found - this is a warning, not failure
            self.results.append(ValidationResult(
                "Templates Installed",
                True,  # Still pass if we have templates
                f"Found {len(found_categories)}/{len(required_categories)} required categories",
                f"Found: {', '.join(found_categories)}. Missing: {', '.join(missing_categories)} (may be optional)"
            ))
        else:
            self.results.append(ValidationResult(
                "Templates Installed",
                True,
                f"All required template categories found ({len(found_categories)}/{len(required_categories)})",
                f"Categories: {', '.join(found_categories)} ({total_templates} templates total)"
            ))
    
    def _check_config_file(self) -> None:
        """Check configuration file."""
        config_path = Path.home() / ".vtt" / "config.json"
        
        if config_path.exists():
            try:
                import json
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                self.results.append(ValidationResult(
                    "Configuration File",
                    True,
                    f"Config file exists: {config_path}",
                    f"Contains {len(config_data)} setting(s)"
                ))
            except Exception as e:
                self.results.append(ValidationResult(
                    "Configuration File",
                    False,
                    f"Config file exists but is invalid: {str(e)}",
                    ""
                ))
        else:
            self.results.append(ValidationResult(
                "Configuration File",
                True,
                "Config file will be created on first run",
                f"Default location: {config_path}"
            ))
    
    def _check_write_permissions(self) -> None:
        """Check write permissions for config directory."""
        config_dir = Path.home() / ".vtt"
        
        try:
            # Try to create directory if it doesn't exist
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # Try to write a test file
            test_file = config_dir / ".test_write"
            test_file.write_text("test")
            test_file.unlink()
            
            self.results.append(ValidationResult(
                "Write Permissions",
                True,
                f"Can write to config directory: {config_dir}",
                ""
            ))
        except PermissionError:
            self.results.append(ValidationResult(
                "Write Permissions",
                False,
                f"No write permission for: {config_dir}",
                "Check directory permissions"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                "Write Permissions",
                False,
                f"Error checking permissions: {str(e)}",
                ""
            ))
    
    def print_report(self) -> None:
        """Print validation report."""
        print("\n" + "=" * 70)
        print("VTT Environment Validation Report")
        print("=" * 70)
        
        for result in self.results:
            status_icon = "✓" if result.status else "✗"
            status_text = "PASS" if result.status else "FAIL"
            
            print(f"\n{status_icon} [{status_text}] {result.name}")
            print(f"   {result.message}")
            if result.details:
                print(f"   Details: {result.details}")
        
        print("\n" + "=" * 70)
        
        # Summary
        passed = sum(1 for r in self.results if r.status)
        total = len(self.results)
        
        if passed == total:
            print(f"\n✓ All checks passed ({passed}/{total})")
            print("Environment is ready for VTT!")
        else:
            print(f"\n✗ {total - passed} check(s) failed ({passed}/{total} passed)")
            print("Please address the issues above before using VTT.")
        
        print("=" * 70 + "\n")
