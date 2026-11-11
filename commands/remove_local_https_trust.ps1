$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pemPath = Join-Path $projectRoot 'certs\local_ca.crt'
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pemPath)) { throw "Local certificate not found: $pemPath" }
if (-not (Test-Path -LiteralPath $python)) { $python = (Get-Command python.exe -ErrorAction Stop).Source }

$derPath = Join-Path $env:TEMP "astratrack-local-https-$PID.cer"
try {
  & $python -c "import sys; from pathlib import Path; from cryptography import x509; from cryptography.hazmat.primitives import serialization; c=x509.load_pem_x509_certificate(Path(sys.argv[1]).read_bytes()); Path(sys.argv[2]).write_bytes(c.public_bytes(serialization.Encoding.DER))" $pemPath $derPath
  if ($LASTEXITCODE -ne 0) { throw 'Could not read the local certificate.' }
  $trusted = Get-ChildItem Cert:\CurrentUser\Root | Where-Object {
    $_.Subject -like '*CN=AstraTrack Local HTTPS Root*' -and
    $_.Subject -like '*O=AstraTrack Local Development*'
  }
  if (-not $trusted) { Write-Host 'This AstraTrack certificate is not installed in CurrentUser\Root.'; exit 0 }
  foreach ($certificate in $trusted) { Remove-Item -LiteralPath $certificate.PSPath -Confirm }
  Write-Host 'Removed AstraTrack local HTTPS certificates from the current user trust store.'
}
finally {
  Remove-Item -LiteralPath $derPath -Force -ErrorAction SilentlyContinue
}
