$ErrorActionPreference = "Stop"
$exeName = "$([char]0x6587)$([char]0x732E)$([char]0x667A)$([char]0x6790)Qwen.exe"

Add-Type `
  -TypeDefinition (Get-Content -LiteralPath ".\windows_gui_launcher.cs" -Raw) `
  -ReferencedAssemblies "System.Windows.Forms" `
  -OutputAssembly ".\$exeName" `
  -OutputType WindowsApplication

Write-Host "Launcher exe created: $exeName"
