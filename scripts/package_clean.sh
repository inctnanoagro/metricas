#!/bin/bash
#
# Clean packaging script for metricas project
# Creates a tarball WITHOUT macOS metadata, virtual environments, and cache files
#
# Usage:
#   ./scripts/package_clean.sh [output_name]
#
# Output: metricas-clean-YYYYMMDD.tar.gz (or custom name)
#

set -e

# Get project root (parent of scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"
OUTPUT_DIR="$HOME/Downloads"

# Default output name with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_NAME="${1:-inct-metricas-${TIMESTAMP}}"

echo "=================================="
echo "Clean Package Creator"
echo "=================================="
echo "Project: $PROJECT_NAME"
echo "Root: $PROJECT_ROOT"
echo "Output: ${OUTPUT_DIR}/${OUTPUT_NAME}.tar.gz"
echo

# Create temporary directory for clean copy
TEMP_DIR=$(mktemp -d)
CLEAN_DIR="${TEMP_DIR}/${PROJECT_NAME}"

echo "1. Creating clean copy..."
mkdir -p "$CLEAN_DIR"

# Copy files using rsync with precise exclusions
rsync -av \
  --exclude='.DS_Store' \
  --exclude='._*' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.pyo' \
  --exclude='*.pyd' \
  --exclude='*.so' \
  --exclude='.pytest_cache' \
  --exclude='htmlcov' \
  --exclude='.coverage' \
  --exclude='*.egg-info' \
  --exclude='dist' \
  --exclude='build' \
  --exclude='.venv' \
  --exclude='.direnv' \
  --exclude='env' \
  --exclude='.env' \
  --exclude='ENV' \
  --exclude='data' \
  --exclude='outputs' \
  --exclude='__MACOSX' \
  --exclude='.git' \
  --exclude='.idea' \
  --exclude='.vscode' \
  "$PROJECT_ROOT/" "$CLEAN_DIR/"

echo "2. Aggressively removing AppleDouble and macOS metadata..."
# Find and delete ALL AppleDouble files
find "$CLEAN_DIR" -name '._*' -type f -delete 2>/dev/null || true
find "$CLEAN_DIR" -name '.DS_Store' -type f -delete 2>/dev/null || true
find "$CLEAN_DIR" -name '__MACOSX' -type d -exec rm -rf {} + 2>/dev/null || true

# Remove any extended attributes (macOS only)
if command -v xattr &> /dev/null; then
    echo "3. Removing extended attributes..."
    find "$CLEAN_DIR" -type f -exec xattr -c {} \; 2>/dev/null || true
fi

echo "4. Creating tarball..."
cd "$TEMP_DIR"

# CRITICAL: Disable macOS resource forks and metadata
export COPYFILE_DISABLE=1

# Detect tar flavor and use appropriate flags
if tar --version 2>&1 | grep -q "GNU tar"; then
    # GNU tar
    echo "   Using GNU tar..."
    tar --no-xattrs \
        --no-acls \
        --exclude='._*' \
        --exclude='.DS_Store' \
        --exclude='__MACOSX' \
        -czf "${OUTPUT_DIR}/${OUTPUT_NAME}.tar.gz" \
        "$PROJECT_NAME"
else
    # BSD tar (macOS default)
    echo "   Using BSD tar..."
    tar --no-xattrs \
        --no-mac-metadata \
        --exclude='._*' \
        --exclude='.DS_Store' \
        --exclude='__MACOSX' \
        -czf "${OUTPUT_DIR}/${OUTPUT_NAME}.tar.gz" \
        "$PROJECT_NAME"
fi

echo "5. Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

# Show results
OUTPUT_FILE="${OUTPUT_DIR}/${OUTPUT_NAME}.tar.gz"
OUTPUT_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)

echo
echo "=================================="
echo "✓ Package created!"
echo "=================================="
echo "File: ${OUTPUT_NAME}.tar.gz"
echo "Size: $OUTPUT_SIZE"
echo "Location: $OUTPUT_FILE"
echo

# VALIDATION: Check for unwanted files
echo "=================================="
echo "VALIDATION"
echo "=================================="

APPLEDOUBLE_COUNT=$(tar -tzf "$OUTPUT_FILE" | grep '/_\.' | wc -l | tr -d ' ' || echo "0")
DS_STORE_COUNT=$(tar -tzf "$OUTPUT_FILE" | grep '\.DS_Store' | wc -l | tr -d ' ' || echo "0")
PYCACHE_COUNT=$(tar -tzf "$OUTPUT_FILE" | grep '__pycache__' | wc -l | tr -d ' ' || echo "0")
VENV_COUNT=$(tar -tzf "$OUTPUT_FILE" | grep '/\.venv/' | wc -l | tr -d ' ' || echo "0")
DIRENV_COUNT=$(tar -tzf "$OUTPUT_FILE" | grep '/\.direnv/' | wc -l | tr -d ' ' || echo "0")
MACOSX_COUNT=$(tar -tzf "$OUTPUT_FILE" | grep '__MACOSX' | wc -l | tr -d ' ' || echo "0")

TOTAL_UNWANTED=$((APPLEDOUBLE_COUNT + DS_STORE_COUNT + PYCACHE_COUNT + VENV_COUNT + DIRENV_COUNT + MACOSX_COUNT))

if [ "$TOTAL_UNWANTED" -eq 0 ]; then
    echo "✓ OK: 0 AppleDouble files"
    echo "✓ OK: 0 .DS_Store files"
    echo "✓ OK: 0 __pycache__ directories"
    echo "✓ OK: 0 .venv directories"
    echo "✓ OK: 0 .direnv directories"
    echo "✓ OK: 0 __MACOSX directories"
    echo
    echo "✓✓✓ PACKAGE IS CLEAN! ✓✓✓"
else
    echo "✗ WARNING: Found unwanted files:"
    [ "$APPLEDOUBLE_COUNT" -gt 0 ] && echo "  - AppleDouble (._*): $APPLEDOUBLE_COUNT"
    [ "$DS_STORE_COUNT" -gt 0 ] && echo "  - .DS_Store: $DS_STORE_COUNT"
    [ "$PYCACHE_COUNT" -gt 0 ] && echo "  - __pycache__: $PYCACHE_COUNT"
    [ "$VENV_COUNT" -gt 0 ] && echo "  - .venv/: $VENV_COUNT"
    [ "$DIRENV_COUNT" -gt 0 ] && echo "  - .direnv/: $DIRENV_COUNT"
    [ "$MACOSX_COUNT" -gt 0 ] && echo "  - __MACOSX: $MACOSX_COUNT"
    echo
    echo "First 10 unwanted files:"
    tar -tzf "$OUTPUT_FILE" | grep -E '(\._|\.DS_Store|__pycache__|/\.venv/|/\.direnv/|__MACOSX)' | head -10
    echo
    echo "✗✗✗ PACKAGE MAY HAVE ISSUES ✗✗✗"
    exit 1
fi

echo
echo "Archive contents summary:"
TOTAL_FILES=$(tar -tzf "$OUTPUT_FILE" | wc -l)
echo "  Total files: $TOTAL_FILES"
echo

echo "Sample files (first 15):"
tar -tzf "$OUTPUT_FILE" | head -15

echo
echo "To extract:"
echo "  tar -xzf ${OUTPUT_NAME}.tar.gz"
echo
