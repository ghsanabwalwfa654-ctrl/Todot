#!/usr/bin/env python3
"""Todot v0.3 - tiny Arabic-friendly multi-target transpiler for Termux."""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "0.3.0"
TOKEN_RE = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\d+(?:\.\d+)?|[^\W\d]\w*|==|!=|<=|>=|[()+\-*/%<>]', re.UNICODE)
ASSIGN_RE = re.compile(r'^([^\W\d]\w*)\s*=\s*(.+)$', re.UNICODE)
PRINT_RE = re.compile(r'^(?:اطبع|اكتب)\s+(.+)$', re.UNICODE)
HEADER_TARGETS = {"#p": "python", "#c": "cpp", "#j": "javascript"}

class TodotError(Exception):
    pass

class Compiler:
    def __init__(self, target):
        self.target = target
        self.variables = {}
        self.lines = []

    def expression(self, text):
        tokens, pos = [], 0
        while pos < len(text):
            if text[pos].isspace():
                pos += 1
                continue
            m = TOKEN_RE.match(text, pos)
            if not m:
                raise TodotError(f"رمز غير معروف في التعبير قرب: {text[pos:]}")
            tok = m.group(0)
            pos = m.end()
            if tok.startswith(('"', "'")) or tok[0].isdigit():
                tokens.append(tok)
            elif tok[0].isalpha() or tok[0] == "_":
                if tok in ("صحيح", "true", "True"):
                    tokens.append("true" if self.target == "javascript" else ("True" if self.target == "python" else "true"))
                elif tok in ("خطأ", "false", "False"):
                    tokens.append("false" if self.target == "javascript" else ("False" if self.target == "python" else "false"))
                elif tok in self.variables:
                    tokens.append(self.variables[tok])
                else:
                    raise TodotError(f"المتغير '{tok}' غير معرّف")
            else:
                tokens.append(tok)
        if not tokens:
            raise TodotError("التعبير فارغ")
        return " ".join(tokens)

    def compile_line(self, raw, n):
        line = raw.strip()
        if not line or line.startswith("#"):
            return
        m = PRINT_RE.fullmatch(line)
        if m:
            e = self.expression(m.group(1))
            if self.target == "python": self.lines.append(f"print({e})")
            elif self.target == "javascript": self.lines.append(f"console.log({e});")
            else: self.lines.append(f"std::cout << ({e}) << '\\n';")
            return
        m = ASSIGN_RE.fullmatch(line)
        if m:
            name, val = m.groups()
            e = self.expression(val)
            if name not in self.variables:
                outname = f"_td_{len(self.variables)}"
                self.variables[name] = outname
                if self.target == "python": self.lines.append(f"{outname} = {e}")
                elif self.target == "javascript": self.lines.append(f"let {outname} = {e};")
                else: self.lines.append(f"auto {outname} = {e};")
            else:
                outname = self.variables[name]
                self.lines.append(f"{outname} = {e}" + (";" if self.target != "python" else ""))
            return
        raise TodotError(f"السطر {n}: أمر غير معروف: {line}")

    def compile(self, source):
        lines = source.splitlines()
        target = self.target
        # Header is optional when an explicit target is supplied; otherwise it picks the target.
        if target is None:
            target = "python"
            for raw in lines:
                s = raw.strip()
                if s in HEADER_TARGETS:
                    target = HEADER_TARGETS[s]
                    break
                if s and not s.startswith("#"):
                    break
            self.target = target
        for n, raw in enumerate(lines, 1):
            if raw.strip() in HEADER_TARGETS:
                continue
            try: self.compile_line(raw, n)
            except TodotError as e: raise TodotError(str(e)) from e
        if self.target == "python": return "\n".join(self.lines) + "\n"
        if self.target == "javascript": return '"use strict";\n' + "\n".join(self.lines) + "\n"
        body = "\n".join("    " + x for x in self.lines)
        return "#include <iostream>\nint main() {\n" + body + "\n    return 0;\n}\n"

def main():
    p = argparse.ArgumentParser(prog="todot", description="مترجم Todot التجريبي")
    p.add_argument("source", nargs="?", help="ملف Todot بامتداد .td")
    p.add_argument("--target", choices=["python", "cpp", "javascript"], help="تجاوز اللغة المحددة داخل الملف")
    p.add_argument("--emit", action="store_true", help="توليد ملف اللغة فقط دون تشغيله")
    p.add_argument("--version", action="version", version=f"Todot {VERSION}")
    args = p.parse_args()
    if not args.source:
        p.print_help(); return 0
    src = Path(args.source)
    if not src.is_file():
        print(f"Todot: الملف غير موجود: {src}", file=sys.stderr); return 2
    try:
        source = src.read_text(encoding="utf-8")
        compiler = Compiler(args.target)
        generated = compiler.compile(source)
        target = compiler.target
        suffix = {"python": ".py", "cpp": ".cpp", "javascript": ".js"}[target]
        out = src.with_suffix(suffix)
        if args.emit:
            out.write_text(generated, encoding="utf-8")
            print(f"تم التحويل بنجاح: {out} [{target}]")
            return 0
        with tempfile.TemporaryDirectory(prefix="todot-") as td:
            tmp = Path(td) / ("main" + suffix)
            tmp.write_text(generated, encoding="utf-8")
            if target == "python":
                cmd = [sys.executable, str(tmp)]
            elif target == "javascript":
                if not shutil.which("node"):
                    raise TodotError("لتشغيل #j ثبّت Node.js بالأمر: pkg install nodejs")
                cmd = ["node", str(tmp)]
            else:
                cc = shutil.which("clang++") or shutil.which("g++")
                if not cc:
                    raise TodotError("لتشغيل #c ثبّت مترجم C++ بالأمر: pkg install clang")
                binary = Path(td) / "todot_program"
                build = subprocess.run([cc, "-std=c++17", "-O2", str(tmp), "-o", str(binary)], text=True)
                if build.returncode: return build.returncode
                cmd = [str(binary)]
            result = subprocess.run(cmd)
            return result.returncode
    except (OSError, TodotError) as e:
        print(f"خطأ Todot: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
