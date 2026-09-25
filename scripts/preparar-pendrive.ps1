# Formata SOMENTE o pendrive confirmado pelo usuario (identificado pelo numero de serie),
# seguindo o metodo do Dortania para Windows: GPT + particao FAT32.
# Precisa rodar como administrador. Grava log em pendrive-log.txt na pasta de trabalho.
# Exemplo: .\preparar-pendrive.ps1 -Serial ABCD1234 -TamanhoGB 58
#   Serial e tamanho: veja com  Get-Disk | Select Number,FriendlyName,BusType,SerialNumber,Size
param(
    [Parameter(Mandatory = $true)][string]$Serial,     # numero de serie do pendrive (Get-Disk)
    [Parameter(Mandatory = $true)][double]$TamanhoGB,  # tamanho que o Windows mostra (ex.: 58 para um de "64 GB")
    [int]$ParticaoGB = 16            # o Windows nao formata FAT32 acima de 32 GB; 16 GB sobra para EFI + recovery
)
$ErrorActionPreference = 'Stop'
$log = Join-Path (Split-Path $PSScriptRoot -Parent) 'pendrive-log.txt'
function Log($m) { $l = "$(Get-Date -Format 'HH:mm:ss') $m"; Write-Host $l; Add-Content -Path $log -Value $l -Encoding UTF8 }

try {
    Log "=== Preparando pendrive (serial $Serial) ==="
    $alvo = @(Get-Disk | Where-Object { $_.SerialNumber -and $_.SerialNumber.Trim() -eq $Serial })
    if ($alvo.Count -ne 1) { throw "Esperava 1 disco com serial $Serial, achei $($alvo.Count). Nada foi feito." }
    $d = $alvo[0]
    $gb = [math]::Round($d.Size / 1GB, 2)
    Log "Alvo: Disco $($d.Number) | $($d.FriendlyName) | $($d.BusType) | $gb GB"
    # Travas de seguranca: tem que ser USB, nao pode ser disco de boot/sistema, tamanho de pendrive de 64 GB
    if ($d.BusType -ne 'USB') { throw "Disco nao e USB ($($d.BusType)). Abortado." }
    if ($d.IsBoot -or $d.IsSystem) { throw "Disco marcado como boot/sistema. Abortado." }
    if ([math]::Abs($gb - $TamanhoGB) -gt ($TamanhoGB * 0.1)) { throw "Tamanho inesperado ($gb GB, esperado ~$TamanhoGB GB). Abortado." }

    Log "Limpando o disco $($d.Number)..."
    Clear-Disk -Number $d.Number -RemoveData -RemoveOEM -Confirm:$false
    # Em alguns pendrives o Clear-Disk ja deixa o disco inicializado; so inicializa se ficou RAW
    $estilo = (Get-Disk -Number $d.Number).PartitionStyle
    if ($estilo -eq 'RAW') { Log "Inicializando como GPT..."; Initialize-Disk -Number $d.Number -PartitionStyle GPT }
    elseif ($estilo -ne 'GPT') { Log "Convertendo $estilo para GPT..."; Set-Disk -Number $d.Number -PartitionStyle GPT }
    else { Log "Disco ja esta em GPT (vazio)." }
    Log "Criando particao de $ParticaoGB GB e formatando FAT32 (rotulo EFI)..."
    $p = New-Partition -DiskNumber $d.Number -Size ($ParticaoGB * 1GB) -AssignDriveLetter
    $v = Format-Volume -Partition $p -FileSystem FAT32 -NewFileSystemLabel 'EFI' -Confirm:$false
    $p = Get-Partition -DiskNumber $d.Number -PartitionNumber $p.PartitionNumber
    Log "OK: letra $($p.DriveLetter): | $($v.FileSystem) | $([math]::Round($v.Size/1GB,2)) GB | rotulo $($v.FileSystemLabel)"
    Log "=== Concluido ==="
}
catch {
    Log "ERRO: $($_.Exception.Message)"
}
Start-Sleep -Seconds 4
