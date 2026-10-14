#!/data/data/com.termux/files/usr/bin/bash
set -e

REPO="https://raw.githubusercontent.com/ghsanabwalwfa654-ctrl/Todot/main"

echo "Welcome to Todot Programming Language!"
echo "أهلًا بك في لغة تودوت"
echo "هيا نبدأ البرمجة!"
echo

pkg install -y python curl

mkdir -p "$HOME/.todot" "$HOME/.local/bin"

curl -fsSL "$REPO/todot.py" \
  -o "$HOME/.todot/todot.py"

cat > "$HOME/.local/bin/todot" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
exec python "$HOME/.todot/todot.py" "$@"
EOF

chmod +x "$HOME/.local/bin/todot"

PROFILE="$HOME/.bashrc"
touch "$PROFILE"

if ! grep -q 'HOME/.local/bin' "$PROFILE"; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$PROFILE"
fi

export PATH="$HOME/.local/bin:$PATH"

echo "Todot installed successfully!"
echo "تم تثبيت Todot بنجاح!"
todot --version
