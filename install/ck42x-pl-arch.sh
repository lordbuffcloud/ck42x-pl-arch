#!/usr/bin/env bash
# CK42X Payload Lab Architect — installer
# Usage: curl -fsSL https://www.ck42x.com/install/ck42x-pl-arch.sh | bash
set -euo pipefail

CK42X_PL_ARCH_VERSION="${CK42X_PL_ARCH_VERSION:-0.1.0}"
INSTALL_ROOT="${CK42X_PL_ARCH_HOME:-${HOME}/.local/share/ck42x-pl-arch}"
BIN_DIR="${HOME}/.local/bin"
SRC_TARBALL="${CK42X_PL_ARCH_URL:-https://www.ck42x.com/downloads/ck42x-pl-arch/ck42x-pl-arch-${CK42X_PL_ARCH_VERSION}.tar.gz}"

echo ""
echo "  CK42X Payload Lab Architect installer"
echo "  AUTHORIZED LABS ONLY"
echo ""

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "error: '$1' is required but not installed." >&2
    exit 1
  }
}

need_cmd python3
need_cmd curl

PY_MINOR="$(python3 -c 'import sys; print(sys.version_info.minor)')"
PY_MAJOR="$(python3 -c 'import sys; print(sys.version_info.major)')"
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  echo "error: Python 3.10+ required (found $(python3 --version))." >&2
  exit 1
fi

mkdir -p "$INSTALL_ROOT" "$BIN_DIR"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "-> Downloading ck42x-pl-arch ${CK42X_PL_ARCH_VERSION}..."
if ! curl -fsSL "$SRC_TARBALL" -o "$TMP/pkg.tar.gz" 2>/dev/null; then
  echo "-> Tarball not on CDN yet; using embedded minimal install via pip & git fallback..."
  need_cmd pip3
  pip3 install --user --upgrade "textual>=0.79" "httpx>=0.27" "rich>=13.7" 2>/dev/null || true
  if [ -d "$INSTALL_ROOT/src" ]; then
    echo "-> Existing source install found at $INSTALL_ROOT"
  else
    GH_FALLBACK="https://github.com/lordbuffcloud/ck42x-pl-arch/archive/refs/heads/main.tar.gz"
  echo "-> Trying GitHub source fallback..."
  if curl -fsSL "$GH_FALLBACK" -o "$TMP/pkg.tar.gz" 2>/dev/null; then
    tar -xzf "$TMP/pkg.tar.gz" -C "$TMP"
    PKG_DIR="$(find "$TMP" -maxdepth 1 -type d -name 'ck42x-pl-arch*' | head -1)"
    if [ -z "$PKG_DIR" ] && [ -f "$TMP/pyproject.toml" ]; then
      PKG_DIR="$TMP"
    fi
    if [ -n "$PKG_DIR" ]; then
      rm -rf "$INSTALL_ROOT"
      mkdir -p "$INSTALL_ROOT"
      cp -a "$PKG_DIR/." "$INSTALL_ROOT/"
    else
      echo "error: invalid GitHub tarball layout" >&2
      exit 1
    fi
  else
    echo "error: Could not download package. Clone https://github.com/lordbuffcloud/ck42x-pl-arch" >&2
    exit 1
  fi
  fi
else
  tar -xzf "$TMP/pkg.tar.gz" -C "$TMP"
  PKG_DIR="$(find "$TMP" -maxdepth 1 -type d -name 'ck42x-pl-arch*' | head -1)"
  if [ -z "$PKG_DIR" ] && [ -f "$TMP/pyproject.toml" ]; then
    PKG_DIR="$TMP"
  fi
  if [ -z "$PKG_DIR" ]; then
    echo "error: invalid tarball layout" >&2
    exit 1
  fi
  rm -rf "$INSTALL_ROOT"
  mkdir -p "$INSTALL_ROOT"
  cp -a "$PKG_DIR/." "$INSTALL_ROOT/"
fi

echo "-> Installing Python package..."
python3 -m pip install --user --upgrade "$INSTALL_ROOT" 2>/dev/null \
  || python3 -m pip install --user --upgrade -e "$INSTALL_ROOT"

for name in ck42x ck42x-pl-arch; do
  WRAPPER="$BIN_DIR/$name"
  cat >"$WRAPPER" <<EOF
#!/usr/bin/env bash
exec python3 -m ck42x_pl_arch "\$@"
EOF
  chmod +x "$WRAPPER"
done

if ! echo ":$PATH:" | grep -q ":$BIN_DIR:"; then
  echo ""
  echo "  Add to PATH:  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "  [ok] Installed Payload Lab Architect"
echo "  Run: ck42x"
echo ""
