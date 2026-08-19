$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$certificate = Join-Path $projectRoot ".local-certs\turfiq.crt"
$privateKey = Join-Path $projectRoot ".local-certs\turfiq.key"

if (-not (Test-Path -LiteralPath $certificate) -or -not (Test-Path -LiteralPath $privateKey)) {
    New-Item -ItemType Directory -Force (Join-Path $projectRoot ".local-certs") | Out-Null
    Write-Host "Creating a local self-signed HTTPS certificate..."
}

Write-Host "TurfIQ is available at https://127.0.0.1:8000/"
python manage.py runserver_plus 127.0.0.1:8000 --cert-file $certificate --key-file $privateKey
