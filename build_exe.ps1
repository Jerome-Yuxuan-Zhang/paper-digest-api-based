$ErrorActionPreference = "Stop"

python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name "PaperDigestApiBased" `
  --paths "src" `
  "gui_launcher.py"

Write-Host "已生成：dist\PaperDigestApiBased\PaperDigestApiBased.exe"
