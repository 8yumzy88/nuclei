# Running VTT with `uv run`

## Quick Start

The easiest way to run VTT is using `uv run`, which automatically manages dependencies:

```bash
# Interactive mode
uv run python -m vtt.main

# Scan single target
uv run python -m vtt.main -t example.com

# Scan from file
uv run python -m vtt.main -l targets.txt

# Validate environment
uv run python -m vtt.main --validate
```

## How It Works

`uv run` will:
1. Automatically create a virtual environment if needed
2. Install dependencies from `pyproject.toml` or `requirements.txt`
3. Run the command in that environment
4. Cache the environment for future runs

## Benefits

- **No manual setup**: Dependencies are installed automatically
- **Isolated environment**: Each project gets its own environment
- **Fast**: `uv` is very fast at dependency resolution
- **Consistent**: Same environment every time

## Examples

### Basic Usage

```bash
# Interactive menu
uv run python -m vtt.main

# Single target scan
uv run python -m vtt.main -t scanme.nmap.org

# Batch scan
uv run python -m vtt.main -l targets.txt

# Environment validation
uv run python -m vtt.main --validate
```

### With Options

```bash
# No banner
uv run python -m vtt.main --no-banner -t example.com

# Explicit interactive mode
uv run python -m vtt.main --interactive
```

## Alternative: Traditional Installation

If you prefer to manage the environment yourself:

```bash
# Install dependencies once
uv pip install -r requirements.txt

# Then run normally
python -m vtt.main -t example.com
```

## Troubleshooting

**First run is slow?**
- Normal - `uv` is installing dependencies
- Subsequent runs will be fast (cached)

**Dependencies not updating?**
- `uv` caches aggressively
- Force reinstall: `uv run --refresh python -m vtt.main`

**Want to see what's installed?**
```bash
uv pip list
```
