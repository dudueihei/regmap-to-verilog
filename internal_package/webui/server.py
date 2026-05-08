#!/usr/bin/env python3
from __future__ import annotations

import cgi
import html
import json
import os
import sys
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "internal_package" / "core"))

from regmap_codegen import emit_module, emit_vh, parse_model, write_text  # noqa: E402


HOST = "127.0.0.1"
PORT = 8765
DEFAULT_OUTPUT_DIR = REPO_ROOT / "user_package" / "output"


def derive_module_name(spec: Path) -> str:
    module_name = spec.stem.lower()
    if module_name.endswith("_regmap_compact"):
        module_name = module_name[: -len("_regmap_compact")]
    elif module_name.endswith("_regmap"):
        module_name = module_name[: -len("_regmap")]
    return module_name


def render_index() -> str:
    default_output = html.escape(str(DEFAULT_OUTPUT_DIR))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Excel 转 Verilog</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --card: #fffdf7;
      --ink: #1f2a2e;
      --muted: #687074;
      --accent: #0b7a75;
      --accent-2: #f2a65a;
      --border: #d8d0bf;
      --ok: #2d7d46;
      --err: #b43f3f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(242,166,90,.18), transparent 32%),
        radial-gradient(circle at bottom right, rgba(11,122,117,.18), transparent 30%),
        var(--bg);
      min-height: 100vh;
    }}
    .wrap {{
      max-width: 920px;
      margin: 0 auto;
      padding: 40px 20px 60px;
    }}
    .hero {{
      margin-bottom: 24px;
    }}
    .hero h1 {{
      margin: 0 0 10px;
      font-size: 34px;
      line-height: 1.1;
    }}
    .hero p {{
      margin: 0;
      color: var(--muted);
      font-size: 16px;
    }}
    .hero-grid {{
      display: grid;
      grid-template-columns: 1.3fr .9fr;
      gap: 18px;
      align-items: stretch;
      margin-bottom: 24px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 22px;
      box-shadow: 0 14px 36px rgba(31,42,46,.08);
    }}
    .grid {{
      display: grid;
      gap: 18px;
    }}
    .dropzone {{
      border: 2px dashed #9cb2af;
      border-radius: 16px;
      min-height: 210px;
      padding: 24px;
      display: grid;
      place-items: center;
      text-align: center;
      background: linear-gradient(180deg, rgba(11,122,117,.04), rgba(242,166,90,.05));
      transition: .2s ease;
      cursor: pointer;
    }}
    .dropzone.dragover {{
      border-color: var(--accent);
      background: linear-gradient(180deg, rgba(11,122,117,.10), rgba(242,166,90,.08));
      transform: translateY(-1px);
    }}
    .dropzone strong {{
      display: block;
      font-size: 22px;
      margin-bottom: 8px;
    }}
    .dropzone span {{
      color: var(--muted);
      display: block;
      margin-bottom: 12px;
    }}
    .pill {{
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      background: #eef6f5;
      color: var(--accent);
      font-size: 13px;
      border: 1px solid #cfe3e1;
    }}
    label {{
      display: block;
      font-weight: 600;
      margin-bottom: 8px;
    }}
    input[type="text"] {{
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 14px;
      font-size: 15px;
      background: #fff;
    }}
    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
    }}
    button {{
      border: 0;
      border-radius: 12px;
      padding: 12px 18px;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
      background: var(--accent);
      color: #fff;
    }}
    button.secondary {{
      background: #e8ecec;
      color: var(--ink);
    }}
    button:disabled {{
      opacity: .55;
      cursor: not-allowed;
    }}
    .status {{
      min-height: 52px;
      border-radius: 12px;
      padding: 14px 16px;
      background: #f6f7f3;
      border: 1px solid var(--border);
      white-space: pre-wrap;
      line-height: 1.5;
    }}
    .status.ok {{ border-color: #b4dfbf; background: #f3fbf5; color: var(--ok); }}
    .status.err {{ border-color: #e6b4b4; background: #fff6f6; color: var(--err); }}
    .tips {{
      color: var(--muted);
      font-size: 14px;
      line-height: 1.7;
    }}
    .steps {{
      display: grid;
      gap: 12px;
      align-content: start;
    }}
    .step {{
      padding: 14px;
      border: 1px solid var(--border);
      border-radius: 14px;
      background: rgba(255,255,255,.72);
    }}
    .step strong {{
      display: inline-block;
      margin-bottom: 6px;
      color: var(--accent);
    }}
    .mono {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      background: #f7f7f4;
      border: 1px solid #e2ddd1;
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 13px;
      white-space: pre-wrap;
      line-height: 1.55;
    }}
    .subtle {{
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 640px) {{
      .hero h1 {{ font-size: 28px; }}
      .card {{ padding: 16px; }}
    }}
    @media (max-width: 820px) {{
      .hero-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero-grid">
      <div class="hero card">
        <h1>拖 Excel，直接生成 Verilog</h1>
        <p>给非开发同学用的本地网页工具。把 <code>.xlsx</code> 拖进来，填一个输出目录，点一下就生成 <code>.vh</code> 和 <code>.v</code>。</p>
      </div>
      <div class="card steps">
        <div class="step">
          <strong>第 1 步</strong>
          <div>拖入一个 <code>.xlsx</code> 寄存器表。</div>
        </div>
        <div class="step">
          <strong>第 2 步</strong>
          <div>填写输出目录，例如项目源码目录或交付目录。</div>
        </div>
        <div class="step">
          <strong>第 3 步</strong>
          <div>点击“生成 Verilog”，工具会自动创建 <code>include/</code> 和 <code>rtl/</code>。</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="grid">
        <div id="dropzone" class="dropzone">
          <div>
            <strong>把 Excel 文件拖到这里</strong>
            <span>支持 .xlsx，也可以点击这里手动选择文件</span>
            <div class="pill" id="fileLabel">当前未选择文件</div>
          </div>
        </div>

        <div>
          <label for="outputDir">输出目录</label>
          <input id="outputDir" type="text" value="{default_output}" />
        </div>

        <div class="actions">
          <button id="generateBtn" disabled>生成 Verilog</button>
          <button id="resetBtn" class="secondary" type="button">清空选择</button>
          <span class="tips">生成后会在输出目录下自动创建 <code>include/</code> 和 <code>rtl/</code></span>
        </div>

        <div id="status" class="status">等待上传 Excel 文件</div>

        <div class="tips">
          建议表头使用：<code>偏移地址 / 寄存器名 / 字段名 / 位段 / 属性 / 复位值 / 描述</code><br>
          例如输出目录填：<code>{default_output}</code>
        </div>

        <div class="mono">生成后的目录结构示例
输出目录/
├── include/
│   └── se_top_regs.vh
└── rtl/
    └── se_top_regfile.v</div>

        <div class="subtle">
          说明：浏览器本身不能直接弹出系统目录选择器，所以输出目录需要手动输入路径。建议提前新建好一个空目录，专门存放生成结果。
        </div>
      </div>
    </div>
  </div>

  <input id="fileInput" type="file" accept=".xlsx" hidden>

  <script>
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const fileLabel = document.getElementById('fileLabel');
    const outputDir = document.getElementById('outputDir');
    const statusBox = document.getElementById('status');
    const generateBtn = document.getElementById('generateBtn');
    const resetBtn = document.getElementById('resetBtn');

    let selectedFile = null;

    function setStatus(text, kind = '') {{
      statusBox.textContent = text;
      statusBox.className = 'status' + (kind ? ' ' + kind : '');
    }}

    function updateFile(file) {{
      selectedFile = file;
      if (file) {{
        fileLabel.textContent = `已选择：${{file.name}}`;
        generateBtn.disabled = false;
        setStatus('文件已就绪，点击“生成 Verilog”即可开始。');
      }} else {{
        fileLabel.textContent = '当前未选择文件';
        generateBtn.disabled = true;
        setStatus('等待上传 Excel 文件');
      }}
    }}

    dropzone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {{
      const file = fileInput.files[0];
      updateFile(file || null);
    }});

    ['dragenter', 'dragover'].forEach(evt => {{
      dropzone.addEventListener(evt, e => {{
        e.preventDefault();
        dropzone.classList.add('dragover');
      }});
    }});

    ['dragleave', 'drop'].forEach(evt => {{
      dropzone.addEventListener(evt, e => {{
        e.preventDefault();
        dropzone.classList.remove('dragover');
      }});
    }});

    dropzone.addEventListener('drop', e => {{
      const file = e.dataTransfer.files[0];
      if (!file) return;
      if (!file.name.toLowerCase().endsWith('.xlsx')) {{
        setStatus('只支持 .xlsx 文件', 'err');
        return;
      }}
      updateFile(file);
    }});

    resetBtn.addEventListener('click', () => {{
      fileInput.value = '';
      updateFile(null);
    }});

    generateBtn.addEventListener('click', async () => {{
      if (!selectedFile) {{
        setStatus('请先选择 Excel 文件', 'err');
        return;
      }}
      if (!outputDir.value.trim()) {{
        setStatus('请填写输出目录', 'err');
        return;
      }}

      const formData = new FormData();
      formData.append('excel', selectedFile);
      formData.append('output_dir', outputDir.value.trim());

      generateBtn.disabled = true;
      setStatus('正在生成，请稍候...');

      try {{
        const res = await fetch('/api/generate', {{
          method: 'POST',
          body: formData
        }});
        const data = await res.json();
        if (!res.ok || !data.ok) {{
          throw new Error(data.error || '生成失败');
        }}
        setStatus(
          `生成成功\\n\\n输入文件：${{data.input_file}}\\n头文件：${{data.output_vh}}\\nRTL：${{data.output_v}}`,
          'ok'
        );
      }} catch (err) {{
        setStatus(`生成失败\\n\\n${{err.message}}`, 'err');
      }} finally {{
        generateBtn.disabled = false;
      }}
    }});
  </script>
</body>
</html>"""


class RegmapHandler(BaseHTTPRequestHandler):
    server_version = "regmap-web/1.0"

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, body: str, status: int = 200) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._send_html(render_index())
            return
        if parsed.path == "/healthz":
            self._send_json({"ok": True})
            return
        self._send_html("<h1>404</h1>", status=404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/generate":
            self._send_json({"ok": False, "error": "Not found"}, status=404)
            return

        try:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                },
            )
            file_item = form["excel"] if "excel" in form else None
            output_dir_raw = form.getfirst("output_dir", "").strip()
            if file_item is None or not getattr(file_item, "filename", ""):
                raise ValueError("没有收到 Excel 文件")
            if not output_dir_raw:
                raise ValueError("输出目录不能为空")

            filename = Path(file_item.filename).name
            if not filename.lower().endswith(".xlsx"):
                raise ValueError("只支持 .xlsx 文件")

            output_root = Path(output_dir_raw).expanduser()
            if not output_root.is_absolute():
                output_root = (REPO_ROOT / output_root).resolve()

            include_dir = output_root / "include"
            rtl_dir = output_root / "rtl"
            include_dir.mkdir(parents=True, exist_ok=True)
            rtl_dir.mkdir(parents=True, exist_ok=True)

            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp.write(file_item.file.read())
                tmp_path = Path(tmp.name)

            try:
                model = parse_model(tmp_path)
                module_name = derive_module_name(Path(filename))
                if module_name:
                    model.module_name = module_name

                out_vh = include_dir / f"{model.module_name}_regs.vh"
                out_v = rtl_dir / f"{model.module_name}_regfile.v"
                write_text(out_vh, emit_vh(model))
                write_text(out_v, emit_module(model))
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

            self._send_json(
                {
                    "ok": True,
                    "input_file": filename,
                    "output_vh": str(out_vh),
                    "output_v": str(out_v),
                }
            )
        except Exception as exc:  # pragma: no cover
            self._send_json(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )


def main() -> int:
    server = ThreadingHTTPServer((HOST, PORT), RegmapHandler)
    print(f"[INFO] 打开浏览器访问: http://{HOST}:{PORT}")
    print(f"[INFO] 默认输出目录: {DEFAULT_OUTPUT_DIR}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
