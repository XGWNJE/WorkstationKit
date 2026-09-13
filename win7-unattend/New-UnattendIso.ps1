[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$OutputIso,
    [Parameter(Mandatory)][string]$Kb4490628,
    [Parameter(Mandatory)][string]$Kb4474419,
    [string]$WorkstationDirectory = 'C:\Program Files\VMware\VMware Workstation'
)

$ErrorActionPreference = 'Stop'
$sourceDirectory = $PSScriptRoot
$mkisofs = Join-Path $WorkstationDirectory 'mkisofs.exe'
if (-not (Test-Path -LiteralPath $mkisofs)) { throw "mkisofs.exe not found: $mkisofs" }

$expected = @{
    $Kb4490628 = 'D3DE52D6987F7C8BDC2C015DCA69EAC96047C76E'
    $Kb4474419 = 'B5614C6CEA5CB4E198717789633DCA16308EF79C'
}
foreach ($item in $expected.GetEnumerator()) {
    $actual = (Get-FileHash -LiteralPath $item.Key -Algorithm SHA1).Hash
    if ($actual -ne $item.Value) { throw "SHA1 mismatch: $($item.Key)" }
}

$stage = Join-Path ([System.IO.Path]::GetTempPath()) ("workstationkit-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage | Out-Null
try {
    $temporaryPassword = 'W7-' + [guid]::NewGuid().ToString('N') + '!'
    $xml = [System.IO.File]::ReadAllText((Join-Path $sourceDirectory 'Autounattend.xml'), [Text.Encoding]::UTF8)
    if (($xml.Split('REPLACE_WITH_YOUR_PASSWORD').Count - 1) -ne 2) {
        throw 'Autounattend.xml must contain exactly two password placeholders.'
    }
    $xml = $xml.Replace('REPLACE_WITH_YOUR_PASSWORD', $temporaryPassword)
    [System.IO.File]::WriteAllText((Join-Path $stage 'Autounattend.xml'), $xml, (New-Object Text.UTF8Encoding($false)))

    $payload = [System.IO.File]::ReadAllText((Join-Path $sourceDirectory 'w7payload.cmd'), [Text.Encoding]::UTF8)
    $payload = $payload -replace '\r?\n', [Environment]::NewLine
    [System.IO.File]::WriteAllText((Join-Path $stage 'w7payload.cmd'), $payload, (New-Object Text.UTF8Encoding($false)))

    Copy-Item -LiteralPath $Kb4490628 -Destination (Join-Path $stage 'kb4490628-x64.msu')
    Copy-Item -LiteralPath $Kb4474419 -Destination (Join-Path $stage 'kb4474419-v3-x64.msu')

    $bytes = [System.IO.File]::ReadAllBytes((Join-Path $stage 'w7payload.cmd'))
    $lf = 0
    $crlf = 0
    for ($i = 0; $i -lt $bytes.Length; $i++) {
        if ($bytes[$i] -eq 10) {
            $lf++
            if ($i -gt 0 -and $bytes[$i - 1] -eq 13) { $crlf++ }
        }
    }
    if ($lf -ne $crlf) { throw 'w7payload.cmd is not pure CRLF.' }

    & $mkisofs -J -joliet-long -R -l -V UNATTEND -o $OutputIso $stage
    if ($LASTEXITCODE -ne 0) { throw "mkisofs.exe exited with $LASTEXITCODE" }
    Get-Item -LiteralPath $OutputIso
}
finally {
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
}
