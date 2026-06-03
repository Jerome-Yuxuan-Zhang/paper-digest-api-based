$ErrorActionPreference = "Stop"
$exeName = "PaperDigestApiBased.exe"

Add-Type `
  -TypeDefinition (Get-Content -LiteralPath ".\windows_gui_launcher.cs" -Raw) `
  -ReferencedAssemblies "System.Windows.Forms" `
  -OutputAssembly ".\$exeName" `
  -OutputType WindowsApplication

Write-Host "Launcher exe created: $exeName"
