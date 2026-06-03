$ErrorActionPreference = "Stop"

python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name "文献智析Qwen" `
  --paths "src" `
  "gui_launcher.py"

Write-Host "已生成：dist\文献智析Qwen\文献智析Qwen.exe"

