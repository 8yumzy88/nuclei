#!/bin/bash
# Setup script for Google API environment variables

# Extract CX from the HTML you received
GOOGLE_API_CX="f2414f15e21f9409a"

# Your existing API key (already set)
# GOOGLE_API_KEY is already set in your environment

# Set the CX variable
export GOOGLE_API_CX="$GOOGLE_API_CX"

# Verify both are set
echo "✓ Google API Configuration:"
echo "  GOOGLE_API_KEY: ${GOOGLE_API_KEY:0:20}..."
echo "  GOOGLE_API_CX:  $GOOGLE_API_CX"
echo ""
echo "To make this permanent, add to your ~/.zshrc:"
echo "  export GOOGLE_API_CX=\"$GOOGLE_API_CX\""
