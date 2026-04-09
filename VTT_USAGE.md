# VTT Usage Instructions

## Quick Start Guide

### 1. Installation & Setup

**Using `uv run` (Recommended - automatically manages dependencies):**
```bash
# Navigate to the nuclei directory
cd /Users/leland/git/nuclei

# Run directly - uv will install dependencies automatically
uv run python -m vtt.main --help

# Or use the script entry point
uv run vtt --help
```

**Traditional Installation:**
```bash
# Navigate to the nuclei directory
cd /Users/leland/git/nuclei

# Install Python dependencies
uv pip install -r requirements.txt

# Verify Nuclei is installed and accessible
nuclei -version

# Test VTT help
python -m vtt.main --help
```

### 2. First Run

**Option A: Interactive Mode (Recommended for first-time users)**

```bash
python -m vtt.main
```

This will display an interactive menu with all available options.

**Option B: Command Line Mode**

```bash
# Scan a single target
python -m vtt.main -t example.com

# Scan from targets.txt file
python -m vtt.main -l targets.txt
```

## Detailed Usage

### Interactive Mode

When you run `python -m vtt.main` without arguments, you'll see:

```
╔═══════════════════════════════════════════════════════════╗
║   Vulnerability Triage Tool (VTT)                        ║
║   Security Architecture and Engineering                   ║
╚═══════════════════════════════════════════════════════════╝

============================================================
VTT Main Menu
============================================================
1. Scan targets from targets.txt
2. Scan single target (manual input)
3. Manage Templates
4. Configuration
5. Exit
============================================================
```

#### Option 1: Scan from targets.txt

1. Create a `targets.txt` file in the current directory:
   ```
   example.com
   192.168.1.1
   https://test.example.com
   ```

2. Select option `1` from the menu
3. VTT will scan each target and display results

**Example targets.txt format:**
```
# Comments start with #
example.com
192.168.1.1
https://test.example.com
# Empty lines are ignored
```

#### Option 2: Scan Single Target

1. Select option `2` from the menu
2. Enter a target when prompted:
   - FQDN: `example.com`
   - IP address: `192.168.1.1`
   - URL: `https://example.com`
3. VTT will scan and display results

#### Option 3: Manage Templates

Template management submenu provides:

- **List installed templates**: View all installed Nuclei templates
  - Optional: Filter by category (e.g., `ssl`, `exposures`)
  
- **Search templates**: Search by:
  - Query (searches name, description, ID)
  - Severity level
  - Author
  - Tags

- **Browse online repositories**: View known template repositories
  - Official: `projectdiscovery/nuclei-templates`

- **Install/Update templates**: Update templates using Nuclei's built-in mechanism
  - Equivalent to running `nuclei -update-templates`

- **Install from GitHub repository**: Install custom templates
  - Format: `owner/repo` (e.g., `projectdiscovery/nuclei-templates`)
  - Optional: Specify branch (default: `main`)

- **List template categories**: View available categories
  - Examples: `ssl`, `exposures`, `misconfiguration`, `network/`

#### Option 4: Configuration

- **Nuclei binary path**: Set path to Nuclei executable
  - Default: `/opt/homebrew/bin/nuclei`
  
- **Template directory**: Set template directory path
  - Auto-detected from Nuclei config if not set

- **View default template categories**: See which categories are scanned by default

#### Option 5: Validate Environment

Runs comprehensive environment validation to check:
- Python version (3.8+ required)
- Required Python packages (pyyaml, requests)
- Nuclei binary existence and version
- Template directory and templates availability
- Configuration file status
- Write permissions

This is useful for:
- Initial setup verification
- Troubleshooting issues
- Pre-flight checks before scanning

### Command Line Mode

#### Basic Usage

```bash
# Scan single target
python -m vtt.main -t example.com

# Scan from file
python -m vtt.main -l targets.txt

# Interactive mode (explicit)
python -m vtt.main --interactive

# Suppress banner
python -m vtt.main --no-banner -t example.com
```

#### Command Line Options

```
-t, --target TARGET     Single target to scan (FQDN, IP, or URL)
-l, --list FILE         File containing targets (one per line)
--interactive           Run in interactive mode
--validate              Run environment validation and exit
--no-banner             Don't print banner
-h, --help              Show help message
```

#### Validate Environment (Command Line)

```bash
# Run validation and exit
python -m vtt.main --validate

# Exit code: 0 if all checks pass, 1 if issues found
# Useful for scripts and automation
```

## Understanding Output

### OK Result

When no significant vulnerabilities are found:

```
[OK] - example.com: No significant security risks detected. Approval recommended.
```

This means:
- No Critical, High, or Medium severity findings
- Target is safe for approval
- Low, Info, and Unknown findings are ignored

### DENIED Result

When significant vulnerabilities are detected:

```
--------------------------------------------------
DECISION: DENIED
RESPONDER: SAE (Security Architecture and Engineering)
FINDINGS:
- [Critical] SSL Certificate Expired: The SSL certificate has expired and needs renewal
- [High] Weak Cipher Suite: Server supports weak SSL/TLS cipher suites
- [Medium] TLS 1.0 Enabled: Server supports deprecated TLS 1.0 protocol

REMEDIATION:
Please review the host configuration and address the identified vulnerabilities. 
For further guidance on corporate security standards, refer to the IT Policies:
[https://revvity.sharepoint.com/...](link)
--------------------------------------------------
```

This means:
- Critical, High, or Medium severity findings detected
- Target requires remediation before approval
- Copy the entire block for ServiceNow ticket

### Summary Report

After scanning, you may see a summary:

```
Scan Summary for example.com
Total Findings: 5
Significant Findings (Critical/High/Medium): 3

Breakdown by Severity:
  Critical: 1
  High: 1
  Medium: 1
  Low: 2
```

## Common Workflows

### Workflow 1: Initial Security Vetting

**Scenario**: New bypass request for SSL exception

```bash
# 1. Create targets.txt with the requested host
echo "newhost.example.com" > targets.txt

# 2. Run scan
python -m vtt.main -l targets.txt

# 3. Review output
# - If OK: Approve request
# - If DENIED: Copy findings to ServiceNow ticket
```

### Workflow 2: Batch Processing

**Scenario**: Multiple hosts to vet

```bash
# 1. Prepare targets.txt with all hosts
cat > targets.txt << EOF
host1.example.com
host2.example.com
192.168.1.100
https://host3.example.com
EOF

# 2. Run batch scan
python -m vtt.main -l targets.txt

# 3. Review each result individually
```

### Workflow 3: Template Management

**Scenario**: Need to update templates or add custom ones

```bash
# 1. Enter interactive mode
python -m vtt.main

# 2. Select option 3 (Manage Templates)

# 3. Update official templates
#    → Select option 4 (Install/Update templates)

# 4. Or install from custom repo
#    → Select option 5 (Install from GitHub repository)
#    → Enter: owner/repo-name
```

### Workflow 4: Quick Single Target Check

```bash
# Quick check without interactive mode
python -m vtt.main -t scanme.nmap.org
```

## Configuration

### Config File Location

VTT configuration is stored in: `~/.vtt/config.json`

### Default Settings

```json
{
  "nuclei_binary_path": "/opt/homebrew/bin/nuclei",
  "template_directory": null,
  "default_template_categories": [
    "ssl",
    "exposures",
    "misconfiguration",
    "default-login",
    "network/"
  ],
  "known_repositories": [
    {
      "name": "Official Nuclei Templates",
      "repo": "projectdiscovery/nuclei-templates",
      "source": "github",
      "description": "Official templates repository maintained by ProjectDiscovery"
    }
  ]
}
```

### Modifying Configuration

**Method 1: Via Interactive Menu**
```bash
python -m vtt.main
# Select option 4 (Configuration)
# Modify settings as needed
```

**Method 2: Direct Edit**
```bash
# Edit config file
nano ~/.vtt/config.json

# Restart VTT for changes to take effect
```

## Troubleshooting

### Issue: "Nuclei binary not found"

**Solution:**
```bash
# 1. Verify Nuclei is installed
which nuclei

# 2. If installed elsewhere, update config
python -m vtt.main
# → Option 4 (Configuration)
# → Option 1 (Nuclei binary path)
# → Enter correct path
```

### Issue: "Templates not found"

**Solution:**
```bash
# 1. Update templates via Nuclei
nuclei -update-templates

# 2. Or via VTT
python -m vtt.main
# → Option 3 (Manage Templates)
# → Option 4 (Install/Update templates)
```

### Issue: "Targets file not found"

**Solution:**
```bash
# Ensure targets.txt is in current directory
ls -la targets.txt

# Or specify full path
python -m vtt.main -l /full/path/to/targets.txt
```

### Issue: "Scan timeout"

**Solution:**
- Large scans may take time (default timeout: 5 minutes)
- For very large target lists, split into multiple files
- Check network connectivity
- Verify target is reachable

### Issue: "Import errors"

**Solution:**
```bash
# Reinstall dependencies
uv pip install -r requirements.txt

# Verify Python version (3.8+ required)
python3 --version
```

## Best Practices

1. **Always verify targets.txt format**
   - One target per line
   - No trailing spaces
   - Comments start with `#`

2. **Update templates regularly**
   - Run template updates weekly
   - Check for new vulnerability templates

3. **Review findings carefully**
   - Not all findings may be relevant
   - Consider false positives
   - Verify critical findings manually

4. **Keep configuration updated**
   - Verify Nuclei path after system updates
   - Update template directory if changed

5. **Document exceptions**
   - If a finding is a false positive, document it
   - Update ServiceNow with context

## Integration with ServiceNow

### Copying Results

1. When DENIED result appears, copy the entire block:
   ```
   --------------------------------------------------
   DECISION: DENIED
   ...
   --------------------------------------------------
   ```

2. Paste into ServiceNow ticket description or comments

3. Include additional context if needed:
   - Scan timestamp
   - Target details
   - Any manual verification results

### Example ServiceNow Entry

```
Subject: Security Vetting - DENIED: example.com

Description:
[Paste VTT DENIED output here]

Additional Notes:
- Scan performed on 2024-01-15
- Target: example.com
- Manual verification pending
```

## Advanced Usage

### Custom Template Categories

To scan only specific categories:

1. Edit `~/.vtt/config.json`
2. Modify `default_template_categories`:
   ```json
   "default_template_categories": [
     "ssl",
     "network/"
   ]
   ```

### Scripting Integration

VTT can be integrated into scripts:

```bash
#!/bin/bash
# Example automation script

TARGETS_FILE="targets.txt"
OUTPUT_FILE="scan_results.txt"

python -m vtt.main -l "$TARGETS_FILE" > "$OUTPUT_FILE" 2>&1

# Check for DENIED results
if grep -q "DECISION: DENIED" "$OUTPUT_FILE"; then
    echo "Security issues detected!"
    # Send notification, create ticket, etc.
fi
```

### Environment Variables

VTT respects Nuclei environment variables:
- `NUCLEI_TEMPLATES_DIR`: Template directory
- `NUCLEI_CONFIG_DIR`: Config directory

## Support & Resources

- **Nuclei Documentation**: https://docs.projectdiscovery.io/tools/nuclei
- **Template Repository**: https://github.com/projectdiscovery/nuclei-templates
- **VTT README**: See `README_VTT.md` for detailed documentation

## Quick Reference

| Task | Command |
|------|---------|
| Scan single target | `python -m vtt.main -t example.com` |
| Scan from file | `python -m vtt.main -l targets.txt` |
| Interactive mode | `python -m vtt.main` |
| Update templates | `python -m vtt.main` → Option 3 → Option 4 |
| View config | `python -m vtt.main` → Option 4 |
| Help | `python -m vtt.main --help` |
