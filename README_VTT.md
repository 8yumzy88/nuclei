# Vulnerability Triage Tool (VTT)

A Python-based tool for automating security vetting of enterprise bypass requests (SSL, IDPS, Firewall, and Geo-locking) by wrapping the Nuclei scanner. Built for the Security Architecture and Engineering (SAE) group.

## Features

- **Automated Scanning**: Scan targets from file or manual input
- **Security Triage**: Automated decision-making based on vulnerability severity
- **ServiceNow Integration**: Formatted reports ready for ServiceNow tickets
- **Template Management**: Browse, install, update, and manage Nuclei templates
- **Multiple Input Methods**: Support for targets.txt file or single target input

## Installation

### Prerequisites

- Python 3.8 or higher
- Nuclei scanner installed at `/opt/homebrew/bin/nuclei` (or configured path)
- Git (for template repository cloning)

### Setup

**Option 1: Using `uv run` (Recommended)**

1. Install dependencies and run:
```bash
uv run python -m vtt.main
```

Or use the script entry point (after first run):
```bash
uv run vtt
```

**Option 2: Traditional Installation**

1. Install Python dependencies:
```bash
uv pip install -r requirements.txt
```

2. Verify Nuclei is installed:
```bash
nuclei -version
```

3. Run VTT:
```bash
python -m vtt.main
```

## Usage

### Interactive Mode

Run VTT without arguments to enter interactive mode:

```bash
python -m vtt.main
```

The interactive menu provides options for:
- Scanning targets from `targets.txt`
- Scanning a single target manually
- Managing templates
- Configuration settings

### Command Line Mode

#### Scan Single Target

```bash
python -m vtt.main -t example.com
python -m vtt.main -t 192.168.1.1
python -m vtt.main -t https://example.com
```

#### Scan from File

```bash
python -m vtt.main -l targets.txt
```

#### Interactive Mode (Explicit)

```bash
python -m vtt.main --interactive
```

#### Validate Environment

```bash
python -m vtt.main --validate
```

This runs comprehensive environment checks and exits with status code 0 (success) or 1 (issues found).

## Input Methods

### Option 1: Scan from targets.txt

Create a `targets.txt` file in the current directory with one target per line:

```
example.com
192.168.1.1
https://test.example.com
```

Then select option 1 from the menu or use:
```bash
python -m vtt.main -l targets.txt
```

### Option 2: Manual Input

Enter a single FQDN, IP address, or URL when prompted, or use:
```bash
python -m vtt.main -t example.com
```

## Scanning Profiles

VTT uses the following Nuclei template categories by default:
- `ssl` - SSL/TLS configuration checks
- `exposures` - Information disclosure vulnerabilities
- `misconfiguration` - Configuration issues
- `default-login` - Default credential checks
- `network/` - Network service checks (RDP, SSH, etc.)

These can be customized in the configuration.

## Reporting

### OK Outcome

If no Critical, High, or Medium findings are detected:

```
[OK] - example.com: No significant security risks detected. Approval recommended.
```

### DENIED Outcome

If significant vulnerabilities are found, a formatted ServiceNow report is generated:

```
--------------------------------------------------
DECISION: DENIED
RESPONDER: SAE (Security Architecture and Engineering)
FINDINGS:
- [Critical] SSL Certificate Expired: The SSL certificate has expired
- [High] Weak Cipher Suite: Server supports weak cipher suites

REMEDIATION:
Please review the host configuration and address the identified vulnerabilities. 
For further guidance on corporate security standards, refer to the IT Policies:
[https://revvity.sharepoint.com/...](link)
--------------------------------------------------
```

### Severity Levels

Only findings with severity **Critical**, **High**, or **Medium** trigger a DENIED decision. Findings with severity **Low**, **Info**, or **Unknown** are ignored for decision-making purposes.

## Template Management

VTT includes comprehensive template management capabilities:

### List Installed Templates

From the interactive menu, select "Manage Templates" → "List installed templates"

You can filter by category (e.g., `ssl`, `exposures`)

### Search Templates

Search templates by:
- Name or description
- Severity level
- Author
- Tags

### Browse Online Repositories

View known template repositories:
- **Official Nuclei Templates**: `projectdiscovery/nuclei-templates` (GitHub)

### Install/Update Templates

Update templates using Nuclei's built-in update mechanism:
- Select "Manage Templates" → "Install/Update templates"

### Install from GitHub Repository

Install templates from custom GitHub repositories:
- Select "Manage Templates" → "Install from GitHub repository"
- Enter repository in format: `owner/repo`
- Optionally specify branch (default: `main`)

### Template Categories

View available template categories:
- Select "Manage Templates" → "List template categories"

## Configuration

VTT configuration is stored in `~/.vtt/config.json`

### Configuration Options

- **Nuclei Binary Path**: Default `/opt/homebrew/bin/nuclei`
- **Template Directory**: Auto-detected from Nuclei config or defaults to `~/.nuclei-templates`
- **Default Template Categories**: SSL, exposures, misconfiguration, default-login, network/
- **Known Repositories**: List of template repositories

### Modifying Configuration

1. Via Interactive Menu:
   - Select "Configuration" from main menu
   - Modify settings as needed

2. Via Config File:
   - Edit `~/.vtt/config.json` directly
   - Restart VTT for changes to take effect

## Examples

### Example 1: Scan Single Target

```bash
$ python -m vtt.main -t scanme.nmap.org

Scanning: scanme.nmap.org
============================================================
[OK] - scanme.nmap.org: No significant security risks detected. Approval recommended.
```

### Example 2: Scan Multiple Targets from File

```bash
$ cat targets.txt
example.com
192.168.1.1
test.example.com

$ python -m vtt.main -l targets.txt

Found 3 target(s) in targets.txt
============================================================

Scanning: example.com
------------------------------------------------------------
[OK] - example.com: No significant security risks detected. Approval recommended.

Scanning: 192.168.1.1
------------------------------------------------------------
--------------------------------------------------
DECISION: DENIED
RESPONDER: SAE (Security Architecture and Engineering)
FINDINGS:
- [High] Open SSH Port: SSH service detected on port 22
- [Medium] Weak TLS Version: Server supports TLS 1.0

REMEDIATION:
Please review the host configuration and address the identified vulnerabilities. 
For further guidance on corporate security standards, refer to the IT Policies:
[https://revvity.sharepoint.com/...](link)
--------------------------------------------------
```

### Example 3: Template Management

```bash
$ python -m vtt.main
# Select option 3 (Manage Templates)
# Select option 1 (List installed templates)
# Filter by category: ssl

Found 45 template(s):

1. [HIGH] SSL Certificate Expired
   ID: ssl-cert-expired
   Path: ssl/ssl-cert-expired.yaml
   Description: Detects expired SSL certificates...

2. [MEDIUM] Weak Cipher Suite
   ID: ssl-weak-cipher
   Path: ssl/ssl-weak-cipher.yaml
   Description: Detects weak SSL cipher suites...
```

## Environment Validation

VTT includes a built-in environment validator that checks all requirements:

### Via Interactive Menu

```bash
python -m vtt.main
# Select: 5 (Validate Environment)
```

### Via Command Line

```bash
python -m vtt.main --validate
```

### What It Checks

- ✅ Python version (3.8+ required)
- ✅ Required Python packages (pyyaml, requests)
- ✅ Nuclei binary existence and version
- ✅ Template directory and templates availability
- ✅ Configuration file status
- ✅ Write permissions

The validator provides:
- Clear pass/fail status for each check
- Detailed error messages
- Recommendations for fixing issues

## Troubleshooting

### Run Validation First

Before troubleshooting, run environment validation:

```bash
python -m vtt.main --validate
```

This will identify all issues and provide specific fixes.

### Nuclei Binary Not Found

If you see an error about Nuclei not being found:

1. Verify Nuclei is installed:
   ```bash
   which nuclei
   ```

2. Update configuration:
   - Run VTT in interactive mode
   - Select "Configuration" → "1" (Nuclei binary path)
   - Enter the correct path

### Templates Not Found

If templates are not detected:

1. Install/update templates:
   - Select "Manage Templates" → "Install/Update templates"

2. Check template directory:
   - Select "Configuration" → "2" (Template directory)
   - Verify the path is correct

3. Verify Nuclei templates are installed:
   ```bash
   nuclei -update-templates
   ```

### Scan Timeout

If scans timeout:

- Large scans may take time
- Default timeout is 300 seconds (5 minutes)
- For very large target lists, consider splitting into multiple files

## Architecture

VTT consists of the following modules:

- **main.py**: CLI entry point and interactive menu
- **scanner.py**: Nuclei execution wrapper
- **parser.py**: JSONL output parsing and severity analysis
- **reporter.py**: ServiceNow report generation
- **template_manager.py**: Template browsing, installation, and management
- **config.py**: Configuration management
- **utils.py**: Helper functions (validation, path checking, etc.)

## Contributing

When adding new features:

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Update this README with new features
4. Test with sample targets before submitting

## License

This tool is part of the Nuclei project. See LICENSE.md for details.

## Support

For issues or questions:
- Check Nuclei documentation: https://docs.projectdiscovery.io/tools/nuclei
- Review template documentation: https://github.com/projectdiscovery/nuclei-templates
