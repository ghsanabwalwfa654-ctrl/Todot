#!/data/data/com.termux/files/usr/bin/bash
set -e
pkg update -y
pkg install -y python
mkdir -p "$HOME/.local/bin" "$HOME/.todot"
cp "$(dirname "$0")/todot.py" "$HOME/.todot/todot.py"
cat > "$HOME/.local/bin/todot" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
exec python "$HOME/.todot/todot.py" "$@"
EOF
chmod +x "$HOME/.local/bin/todot" "$HOME/.todot/todot.py"
PROFILE="$HOME/.bashrc"
touch "$PROFILE"
if ! grep -q 'HOME/.local/bin' "$PROFILE"; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$PROFILE"
fi
export PATH="$HOME/.local/bin:$PATH"
echo
echo 'تم تثبيت Todot مبدئيًا.'
echo 'لتفعيل الأمر في الجلسة الحالية نفّذ: export PATH="$HOME/.local/bin:$PATH"'
echo 'لاستخدام #c ثبّت لاحقًا: pkg install clang'
echo 'لاستخدام #j ثبّت لاحقًا: pkg install nodejs'
echo 'اختبر: todot --version'
