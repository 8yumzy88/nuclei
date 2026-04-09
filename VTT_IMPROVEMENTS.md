# VTT Improvements Summary

## New Features Implemented

### 1. Device Fingerprinting ✓

**Module**: `vtt/fingerprint.py`

- Uses Nuclei's automatic scan mode (`-as`) with Wappalyzer technology detection
- Identifies:
  - Technologies (web frameworks, CMS, etc.)
  - Services (HTTP, SSH, FTP, etc.)
  - Operating System information
  - Server software versions

**Usage**: Automatically runs during scans to identify devices

### 2. Armis API Integration ✓

**Module**: `vtt/armis_client.py`

- Integrates with Armis API to lookup asset information
- Supports both Armis Python library and REST API
- Retrieves:
  - Device name
  - Device type
  - Manufacturer and model
  - Operating System
  - Risk level
  - Tags
  - Last seen timestamp

**Configuration**:
- Set via environment variables: `ARMIS_API_KEY`, `ARMIS_BASE_URL`
- Or configure via VTT Configuration menu (Option 4 → Options 3 & 4)

### 3. Improved Output Formatting ✓

**Module**: `vtt/reporter.py` (completely rewritten)

#### Key Improvements:

1. **Simplified OK Reports**
   - Before: 3 lines of verbose text
   - After: Single line: `✓ OK  192.168.1.1 - Device Name`
   - Shows device identification when available

2. **Table-Based DENIED Reports**
   - Findings displayed in clean grid tables
   - Includes device information (from fingerprinting/Armis)
   - Removed SharePoint link from remediation text
   - Better organized sections

3. **Batch Reporting**
   - Groups OK and DENIED results separately
   - Summary table with counts
   - OK targets in simple table format
   - DENIED targets with full details

#### Example Output:

**OK Target (Simplified)**:
```
✓ OK  192.168.1.1 - Apache/2.4 (Linux)
```

**DENIED Target (Table Format)**:
```
======================================================================
DECISION: DENIED
RESPONDER: SAE (Security Architecture and Engineering)
======================================================================
Target: 192.168.1.1
Device Name: Server-01
Device Type: Server
OS: Linux

FINDINGS:
+------------+-------------------------+--------------------------------------------+
| Severity   | Issue                   | Description                                |
+============+=========================+============================================+
| HIGH       | SSL Certificate Expired | The SSL certificate has expired            |
| MEDIUM     | Weak Cipher Suite       | Server supports weak SSL/TLS cipher suites |
+------------+-------------------------+--------------------------------------------+

REMEDIATION:
Please review the host configuration and address the identified vulnerabilities.
For further guidance on corporate security standards, refer to the IT Policies.
======================================================================
```

**Batch Report**:
```
======================================================================
VTT BATCH SCAN RESULTS
======================================================================

+-----------------+---------+
| Status          |   Count |
+=================+=========+
| Total Scanned   |       5 |
+-----------------+---------+
| ✓ Approved (OK) |       3 |
+-----------------+---------+
| ✗ Denied        |       2 |
+-----------------+---------+

======================================================================
APPROVED TARGETS (3)
======================================================================
Target       Device
-----------  ----------
192.168.1.1  Apache/2.4
192.168.1.2  Server-01
192.168.1.3  Unknown

======================================================================
DENIED TARGETS (2)
======================================================================
[Full DENIED reports for each target...]
```

## Configuration

### Armis API Setup

**Option 1: Environment Variables**
```bash
export ARMIS_API_KEY="your-api-key"
export ARMIS_BASE_URL="https://your-armis-instance.com"
```

**Option 2: VTT Configuration Menu**
```bash
python -m vtt.main
# Select: 4 (Configuration)
# Select: 3 (Armis API key)
# Select: 4 (Armis base URL)
```

## Dependencies Added

- `tabulate>=0.9.0` - For table formatting
- `armis` - Armis Python library (optional, falls back to REST API)

## Files Modified/Created

### New Files:
- `vtt/fingerprint.py` - Device fingerprinting
- `vtt/armis_client.py` - Armis API integration

### Modified Files:
- `vtt/reporter.py` - Complete rewrite with tables and batch reporting
- `vtt/main.py` - Integrated fingerprinting and Armis lookup
- `vtt/config.py` - Added Armis configuration options
- `requirements.txt` - Added tabulate and armis

## Usage

### Single Target Scan
```bash
uv run python -m vtt.main -t example.com
```

**Output includes**:
1. Device fingerprinting (technologies, OS, server)
2. Armis lookup (if configured)
3. Security scan results
4. Formatted report (OK or DENIED with table)

### Batch Scan
```bash
uv run python -m vtt.main -l targets.txt
```

**Output includes**:
1. Summary table
2. Grouped OK targets (simplified)
3. Grouped DENIED targets (detailed with tables)

## Benefits

1. **Better Readability**: Tables make findings easy to scan
2. **Less Noise**: OK targets are one line instead of three
3. **Device Context**: Know what you're scanning (fingerprinting + Armis)
4. **Batch Efficiency**: Quickly see approved vs denied in batch scans
5. **Professional Format**: Clean, organized output ready for ServiceNow

## Next Steps

To use Armis integration:
1. Get Armis API credentials
2. Configure via environment variables or VTT config menu
3. Run scans - Armis lookup happens automatically for IP addresses
