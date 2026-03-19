#!/bin/bash
set -e

INSTALL_DIR="$HOME/.auto-research"
SKILL_DIR="$HOME/.claude/skills/init-auto-research"
BIN_DIR="$HOME/.local/bin"

echo "=== Auto-Scientist Installer ==="
echo

# Ask for Python runner
echo "Which Python runner do you use?"
echo "  1) uv (recommended)"
echo "  2) python"
read -p "Choose [1/2]: " choice

case $choice in
  1) RUNNER="uv run --project \"$INSTALL_DIR\"" ;;
  2) RUNNER="python" ;;
  *) echo "Invalid choice"; exit 1 ;;
esac

# Clone or update
if [ -d "$INSTALL_DIR" ]; then
  echo "Updating existing installation..."
  git -C "$INSTALL_DIR" pull
else
  echo "Installing to $INSTALL_DIR..."
  git clone https://github.com/Zhangyanbo/auto-scientists.git "$INSTALL_DIR"
fi

# Install Python dependencies
echo "Installing dependencies..."
if [ "$choice" = "1" ]; then
  (cd "$INSTALL_DIR" && uv sync)
else
  pip install -r "$INSTALL_DIR/requirements.txt"
fi

# Install init-auto-research as a global Claude Code skill
echo "Installing Claude Code skill..."
mkdir -p "$SKILL_DIR"
cp "$INSTALL_DIR/skills/init-auto-research/SKILL.md" "$SKILL_DIR/SKILL.md"

# Create CLI wrapper
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/auto-research" << EOF
#!/bin/bash
$RUNNER "$INSTALL_DIR/run.py" "\$@"
EOF
chmod +x "$BIN_DIR/auto-research"

echo
echo "Done. Make sure $BIN_DIR is in your PATH."
echo
echo "Usage:"
echo "  1. Open Claude Code in your project, type /init-auto-research"
echo "  2. Run: auto-research --rounds 10"
echo
