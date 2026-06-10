param(
  [string]$SonarHostUrl = "http://localhost:9000",
  [string]$ProjectKey = "StudyPDF"
)

$ErrorActionPreference = "Stop"

if (-not $env:SONAR_TOKEN) {
  Write-Error "Defina SONAR_TOKEN antes de rodar. Exemplo: `$env:SONAR_TOKEN='seu-token'"
}

$scanner = Join-Path $PSScriptRoot "..\.venv\Scripts\pysonar.exe"
if (-not (Test-Path $scanner)) {
  Write-Error "pysonar nao encontrado em .venv. Rode: .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt"
}

& $scanner `
  --sonar-host-url=$SonarHostUrl `
  --sonar-token=$env:SONAR_TOKEN `
  --sonar-project-key=$ProjectKey `
  --sonar-project-name=$ProjectKey `
  --sonar-sources=. `
  --sonar-python-version=3.14 `
  --sonar-qualitygate-wait
