$MODES      = @('platform', 'virtual', 'async')
$VUS_LEVELS = @(10, 100, 500)
$BASE_URL   = 'http://localhost:8081'
$SCRIPT_DIR = $PSScriptRoot

$K6 = 'C:\Windows\k6-v2.3.0-windows-amd64\k6.exe'
if (-not (Test-Path $K6)) { $K6 = 'k6' }

Set-Location $SCRIPT_DIR

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PPC -- Benchmark de Modelos de Concorrencia" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[CHECK] A verificar se o agregador esta a correr..." -ForegroundColor Yellow
try {
    $null = Invoke-RestMethod -Uri "$BASE_URL/aggregate/platform" -TimeoutSec 5
    Write-Host "[OK]    Agregador em $BASE_URL acessivel." -ForegroundColor Green
} catch {
    Write-Host "[ERRO]  Nao foi possivel aceder a $BASE_URL/aggregate/platform" -ForegroundColor Red
    Write-Host "        Garante que o stub (:8080) e o aggregate (:8081) estao a correr." -ForegroundColor Red
    exit 1
}

$modeList = $MODES -join ', '
$vusList  = $VUS_LEVELS -join ', '
$total    = $MODES.Count * $VUS_LEVELS.Count
$minutes  = [int]($total * 47 / 60)

Write-Host ""
Write-Host "[INFO]  Modos           : $modeList"
Write-Host "[INFO]  Concorrencias   : $vusList VUs"
Write-Host "[INFO]  Duracao por teste: ~45s (10s warm-up + 30s medicao + 5s descida)"
Write-Host "[INFO]  Total de testes : $total (~$minutes minutos no total)"
Write-Host ""

$completed = 0

foreach ($mode in $MODES) {
    foreach ($vus in $VUS_LEVELS) {

        Write-Host "--------------------------------------------" -ForegroundColor DarkGray
        Write-Host ">> Modo: $mode | Concorrencia: $vus VUs" -ForegroundColor White
        Write-Host "--------------------------------------------" -ForegroundColor DarkGray

        $args = @(
            'run',
            '--env', "MODE=$mode",
            '--env', "VUS=$vus",
            '--env', "BASE_URL=$BASE_URL",
            '--quiet',
            'benchmark.js'
        )
        & $K6 @args

        $completed++
        Write-Host "[PROGRESSO] $completed/$total testes concluidos" -ForegroundColor Green
        Write-Host ""

        if ($completed -lt $total) {
            Start-Sleep -Seconds 3
        }
    }
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Benchmark concluido!" -ForegroundColor Cyan
Write-Host "  Resultados em: results\raw\" -ForegroundColor Cyan
Write-Host "  Corre agora:   python plot_results.py" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
