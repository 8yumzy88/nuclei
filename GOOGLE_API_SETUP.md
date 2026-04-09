# Google API Configuration Guide

## Error: GOOGLE_API_KEY exists but GOOGLE_API_CX does not

This error occurs when `GOOGLE_API_KEY` is set but `GOOGLE_API_CX` (Custom Search Engine ID) is missing.

## Resolution Options

### Option 1: Set GOOGLE_API_CX (If Using Google Custom Search)

If you need Google Custom Search functionality:

1. **Create a Custom Search Engine:**
   - Go to https://programmablesearchengine.google.com/
   - Click "Add" to create a new search engine
   - Configure your search engine settings
   - Copy the "Search engine ID" (this is your CX)

2. **Set the environment variable:**
   ```bash
   export GOOGLE_API_CX="your-custom-search-engine-id"
   ```

3. **Or add to your `.env` file:**
   ```
   GOOGLE_API_KEY=your-api-key
   GOOGLE_API_CX=your-custom-search-engine-id
   ```

### Option 2: Unset GOOGLE_API_KEY (If Not Using Google Custom Search)

If you don't need Google Custom Search functionality:

```bash
# Remove the environment variable
unset GOOGLE_API_KEY

# Or remove from .env file
# Delete or comment out the GOOGLE_API_KEY line
```

### Option 3: Use Google Gemini Instead (For AI Features)

If you're using Google APIs for AI features (like in `test_assets.py`), use Google Gemini API instead:

1. **Get Gemini API Key:**
   - Go to https://makersuite.google.com/app/apikey
   - Create an API key

2. **Set only GOOGLE_API_KEY:**
   ```bash
   export GOOGLE_API_KEY="your-gemini-api-key"
   ```

3. **Note:** Gemini API doesn't require GOOGLE_API_CX

## Environment Variable Setup

### For macOS/Linux (Bash/Zsh)

**Temporary (current session only):**
```bash
export GOOGLE_API_KEY="your-api-key"
export GOOGLE_API_CX="your-cx-id"  # Only if using Custom Search
```

**Permanent (add to ~/.zshrc or ~/.bashrc):**
```bash
echo 'export GOOGLE_API_KEY="your-api-key"' >> ~/.zshrc
echo 'export GOOGLE_API_CX="your-cx-id"' >> ~/.zshrc  # Only if needed
source ~/.zshrc
```

### Using .env File

Create a `.env` file in your project directory:

```bash
# .env file
GOOGLE_API_KEY=your-api-key-here
GOOGLE_API_CX=your-cx-id-here  # Only if using Custom Search
```

Then load it:
```bash
# If using python-dotenv
source .env  # Or use: export $(cat .env | xargs)
```

## Verification

Check if variables are set:
```bash
echo $GOOGLE_API_KEY
echo $GOOGLE_API_CX  # Should be set if using Custom Search
```

## Common Use Cases

### For VTT/Nuclei Scanning
- **Not required** - VTT doesn't use Google APIs
- This error is likely from another tool or integration

### For AI Analysis (test_assets.py)
- Use **GOOGLE_API_KEY** for Gemini API
- **GOOGLE_API_CX not needed** for Gemini

### For Custom Search Integration
- Requires **both** GOOGLE_API_KEY and GOOGLE_API_CX
- Used for web search functionality in some tools

## Troubleshooting

**Error persists after setting variables?**
- Restart your terminal/shell
- Verify variables with `echo $GOOGLE_API_KEY`
- Check for typos in variable names
- Ensure no spaces around the `=` sign

**Don't need Google Custom Search?**
- Simply unset GOOGLE_API_KEY if not using any Google APIs
- Or set GOOGLE_API_CX to empty string: `export GOOGLE_API_CX=""`
