# VTT Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: First Run (with uv)
```bash
cd /Users/leland/git/nuclei

# uv will automatically install dependencies and run
uv run python -m vtt.main -t scanme.nmap.org
```

### Step 2: Verify Nuclei
```bash
nuclei -version
# Should show Nuclei version
```

### Alternative: Traditional Setup
```bash
# Install dependencies first
uv pip install -r requirements.txt

# Then run normally
python -m vtt.main -t scanme.nmap.org
```

## 📋 Common Tasks

### Scan a Single Target
```bash
python -m vtt.main -t example.com
```

### Scan Multiple Targets
```bash
# Create targets.txt
echo "example.com" > targets.txt
echo "192.168.1.1" >> targets.txt

# Run scan
python -m vtt.main -l targets.txt
```

### Interactive Mode
```bash
python -m vtt.main
# Follow the menu prompts
```

### Update Templates
```bash
python -m vtt.main
# Select: 3 (Manage Templates) → 4 (Install/Update templates)
```

### Validate Environment
```bash
python -m vtt.main
# Select: 5 (Validate Environment)
# Checks all requirements and configuration
```

## 📊 Understanding Results

### ✅ OK Result
```
[OK] - example.com: No significant security risks detected. Approval recommended.
```
→ **Action**: Approve the request

### ❌ DENIED Result
```
--------------------------------------------------
DECISION: DENIED
RESPONDER: SAE (Security Architecture and Engineering)
FINDINGS:
- [High] Issue Name: Description
...
--------------------------------------------------
```
→ **Action**: Copy entire block to ServiceNow ticket

## 🔧 Configuration

Config file: `~/.vtt/config.json`

Default settings work out of the box. To customize:
```bash
python -m vtt.main
# Select: 4 (Configuration)
```

## 📚 Full Documentation

- **Detailed Usage**: See `VTT_USAGE.md`
- **QA Report**: See `VTT_QA_REPORT.md`
- **Tool README**: See `README_VTT.md`

## ⚡ Quick Reference

| Task | Command |
|------|---------|
| Single scan | `python -m vtt.main -t TARGET` |
| File scan | `python -m vtt.main -l targets.txt` |
| Interactive | `python -m vtt.main` |
| Help | `python -m vtt.main --help` |

## 🆘 Troubleshooting

**First, run environment validation:**
```bash
python -m vtt.main
# Select: 5 (Validate Environment)
# This will show all issues and how to fix them
```

**Common fixes:**
- **Nuclei not found?** → Select: 4 → 1 → Enter path to nuclei
- **Templates missing?** → Run: `nuclei -update-templates`
- **Import errors?** → Run: `uv pip install -r requirements.txt`

---

**Ready to use!** Start with `python -m vtt.main` for interactive mode.
