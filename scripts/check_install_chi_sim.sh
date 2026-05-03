#!/usr/bin/env bash
set -euo pipefail

echo "[chi_sim installer] Checking Tesseract and tessdata for chi_sim..."

# Determine tessdata directory
get_tessdata_dir() {
  local tpd=""
  if command -v tesseract >/dev/null 2>&1; then
    if command -v brew >/dev/null 2>&1; then
      tpd="$(brew --prefix tesseract)/share/tessdata"
    fi
  fi
  if [ -z "$tpd" ]; then
    # Common fallbacks
    if [ -d "/usr/local/share/tessdata" ]; then
      tpd="/usr/local/share/tessdata"
    elif [ -d "/usr/share/tessdata" ]; then
      tpd="/usr/share/tessdata"
    elif [ -d "/opt/homebrew/share/tessdata" ]; then
      tpd="/opt/homebrew/share/tessdata"
    elif compgen -G '/**/tessdata' > /dev/null; then
      tpd="$(dirname $(realpath $(command -v tesseract || echo '')))"/../../share/tessdata
    else
      tpd="$PWD/tessdata"
    fi
  fi
  echo "$tpd"
}

DEST_TESSDATA_DIR="$(get_tessdata_dir)"
mkdir -p "$DEST_TESSDATA_DIR"

CHI_SIM_PATH="$DEST_TESSDATA_DIR/chi_sim.traineddata"
if [ -f "$CHI_SIM_PATH" ]; then
  echo "[OK] chi_sim.traineddata found at $CHI_SIM_PATH"
  exit 0
fi

echo "[INFO] chi_sim not found. Attempting installation via Homebrew..."

# Try to install language packs via Homebrew
if command -v brew >/dev/null 2>&1; then
  if brew ls --versions tesseract >/dev/null 2>&1; then
    echo "[BREW] tesseract installed. Installing language data..."
    # Try common language data formulae
    if brew ls --versions tesseract-lang-all >/dev/null 2>&1; then
      brew install tesseract-lang-all
    elif brew ls --versions tesseract-lang >/dev/null 2>&1; then
      brew install tesseract-lang
    else
      echo "[BREW] Language package formula not found. Falling back to manual download."
    fi
  else
    echo "[BREW] tesseract not found. Installing tesseract with languages..."
    brew install tesseract
  fi
fi

sleep 1
if [ ! -f "$CHI_SIM_PATH" ]; then
  echo "[WARN] chi_sim not installed via brew; attempting manual download..."
  mkdir -p "$DEST_TESSDATA_DIR"
  # Attempt to download chi_sim.traineddata from tessdata_best (or tessdata)
  if command -v curl >/dev/null 2>&1; then
    URLS=(
      "https://github.com/tesseract-ocr/tessdata_best/raw/master/chi_sim.traineddata"
      "https://github.com/tesseract-ocr/tessdata_best/raw/master/chi_sim.traineddata?raw=1"
    )
    for url in "${URLS[@]}"; do
      echo "[DOWNLOAD] Trying $url"
      if curl -fsSL --output "$CHI_SIM_PATH" "$url"; then
        echo "[OK] chi_sim.traineddata downloaded to $CHI_SIM_PATH"
        break
      fi
    done
  fi
fi

if [ -f "$CHI_SIM_PATH" ]; then
  echo "[SUCCESS] chi_sim.traineddata is available at $CHI_SIM_PATH"
  exit 0
else
  echo "[FAILED] chi_sim.traineddata could not be installed automatically."
  echo "Please install Tesseract language data manually from tessdata (chi_sim) and place it at: $DEST_TESSDATA_DIR/chi_sim.traineddata"
  exit 1
fi
