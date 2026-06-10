param(
  [string]$SonarHostUrl = "http://localhost:9000",
  [string]$ProjectKey = "StudyPDF"
)

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

if (-not $env:SONAR_TOKEN) {
  Write-Error "Defina SONAR_TOKEN antes de rodar. Exemplo: `$env:SONAR_TOKEN='seu-token'"
}

$scanner = Join-Path $PSScriptRoot "..\.venv\Scripts\pysonar.exe"
if (-not (Test-Path $scanner)) {
  Write-Error "pysonar nao encontrado em .venv. Rode: .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt"
}

$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  Write-Error "Python da .venv nao encontrado. Rode: python -m venv .venv"
}

& $python -m pytest

& $scanner `
  --sonar-host-url=$SonarHostUrl `
  --sonar-token=$env:SONAR_TOKEN `
  --sonar-project-key=$ProjectKey `
  --sonar-project-name=$ProjectKey `
  --sonar-sources=studypdf,app.py `
  --sonar-tests=tests `
  --sonar-python-coverage-report-paths=coverage.xml `
  --sonar-python-version=3.14 `
  --sonar-qualitygate-wait
