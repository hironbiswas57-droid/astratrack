[CmdletBinding()]
param([switch]$Force)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pemPath = Join-Path $projectRoot 'certs\local_ca.crt'
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pemPath)) { throw "Local certificate not found: $pemPath. Run commands\setup.bat first." }
if (-not (Test-Path -LiteralPath $python)) { $python = (Get-Command python.exe -ErrorAction Stop).Source }

$derPath = Join-Path $env:TEMP "astratrack-local-https-$PID.cer"
try {
  $fingerprint = & $python -c "import sys; from pathlib import Path; from cryptography import x509; from cryptography.hazmat.primitives import hashes, serialization; c=x509.load_pem_x509_certificate(Path(sys.argv[1]).read_bytes()); Path(sys.argv[2]).write_bytes(c.public_bytes(serialization.Encoding.DER)); print(c.fingerprint(hashes.SHA256()).hex().upper())" $pemPath $derPath
  if ($LASTEXITCODE -ne 0) { throw 'Could not read the local certificate.' }
  Write-Host "Trust this local development certificate for the current Windows user only?"
  Write-Host "SHA-256: $fingerprint"
  Write-Host 'It trusts the local AstraTrack development CA, which signs the localhost HTTPS certificate.'
  if (-not $Force) {
    $answer = Read-Host 'Type TRUST to continue'
    if ($answer -cne 'TRUST') { Write-Host 'No certificate store changes made.'; exit 0 }
  }

  $certificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($derPath)
  $oldRoots = Get-ChildItem Cert:\CurrentUser\Root | Where-Object {
    $_.Subject -like '*CN=AstraTrack Local HTTPS Root*' -and
    $_.Subject -like '*O=AstraTrack Local Development*' -and
    $_.Thumbprint -ne $certificate.Thumbprint
  }
  foreach ($oldRoot in $oldRoots) { Remove-Item -LiteralPath $oldRoot.PSPath -Force }
  $alreadyTrusted = Get-ChildItem Cert:\CurrentUser\Root | Where-Object Thumbprint -eq $certificate.Thumbprint
  if (-not $alreadyTrusted) { Import-Certificate -FilePath $derPath -CertStoreLocation Cert:\CurrentUser\Root | Out-Null }
  else { Write-Host 'This certificate is already trusted for the current user.' }
  $verifiedTrust = Get-ChildItem Cert:\CurrentUser\Root | Where-Object Thumbprint -eq $certificate.Thumbprint
  if (-not $verifiedTrust) { throw 'The certificate store did not return the installed AstraTrack root.' }
  Write-Host 'Installed in CurrentUser\Root. Restart the browser before opening https://localhost:8000.'
}
finally {
  Remove-Item -LiteralPath $derPath -Force -ErrorAction SilentlyContinue
}
