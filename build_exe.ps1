$ErrorActionPreference = "Stop"

# ============================================================
# 打包为单个免依赖 exe（目标电脑无需安装 Python 或任何依赖）
# 用法：powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
# 输出：dist\PaperDigestApiBased.exe
# ============================================================

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name "PaperDigestApiBased" `
  --paths "src" `
  --collect-all "pdfminer" `
  --collect-all "fitz" `
  "gui_launcher.py"

Write-Host ""
Write-Host "打包完成：dist\PaperDigestApiBased.exe"
Write-Host "该 exe 已内置 Python 运行时与全部依赖，可拷贝到其它 Windows 电脑直接双击运行。"
