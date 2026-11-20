$MODES = @('platform', 'virtual', 'async')
$VUS_LEVELS = @(10, 100, 500, 1000, 2000)
$REPETITIONS = 10
$WARMUP_SECONDS = 10
$MEASUREMENT_SECONDS = 30
$PAUSE_BETWEEN_RUNS_SECONDS = 3
$STUB_DELAY_MS = 1000
$TOMCAT_MAX_THREADS = 200

# Change this if the Mac's LAN address changes. Do not add a trailing slash.
$BASE_URL = 'http://192.168.1.48:8081'
$BASE_URL = $BASE_URL.TrimEnd('/')

$RESULTS_RELATIVE = 'results/raw_rq1'
$SCRIPT_DIR = $PSScriptRoot
$RESULTS_PATH = Join-Path $SCRIPT_DIR ($RESULTS_RELATIVE -replace '/', '\')

$K6 = 'C:\Windows\k6-v2.3.0-windows-amd64\k6.exe'
if (-not (Test-Path -LiteralPath $K6)) {
    $k6Command = Get-Command 'k6' -ErrorAction SilentlyContinue
    if ($null -eq $k6Command) {
        Write-Host '[ERRO] k6 não foi encontrado. Instala-o ou adiciona-o ao PATH.' -ForegroundColor Red
        exit 1
    }
    $K6 = $k6Command.Source
}

Set-Location $SCRIPT_DIR
New-Item -ItemType Directory -Path $RESULTS_PATH -Force | Out-Null

Write-Host '============================================' -ForegroundColor Cyan
Write-Host '  PPC -- Benchmark de Modelos de Concorrencia' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''

Write-Host '[CHECK] A verificar se o agregador está acessível...' -ForegroundColor Yellow
try {
    $null = Invoke-RestMethod -Uri "$BASE_URL/aggregate/platform" -TimeoutSec 15
    Write-Host "[OK]    Agregador em $BASE_URL acessível." -ForegroundColor Green
} catch {
    Write-Host "[ERRO] Não foi possível aceder a $BASE_URL/aggregate/platform" -ForegroundColor Red
    Write-Host "        $($_.Exception.Message)" -ForegroundColor DarkRed
    Write-Host '        Confirma que o stub e o agregador estão a correr no Mac.' -ForegroundColor Red
    exit 1
}

# Build the full experiment matrix, then randomize the order of all conditions.
$cases = @()
foreach ($repetition in 1..$REPETITIONS) {
    foreach ($mode in $MODES) {
        foreach ($vus in $VUS_LEVELS) {
            $cases += [pscustomobject]@{
                mode = $mode
                vus = $vus
                repetition = $repetition
            }
        }
    }
}

$orderedCases = @(Get-Random -InputObject $cases -Count $cases.Count)
$sessionId = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$orderLog = @()
for ($index = 0; $index -lt $orderedCases.Count; $index++) {
    $case = $orderedCases[$index]
    $case | Add-Member -NotePropertyName position -NotePropertyValue ($index + 1)
    $case | Add-Member -NotePropertyName run_id -NotePropertyValue ("{0}_run{1:D3}" -f $sessionId, ($index + 1))
    $orderLog += [pscustomobject]@{
        position = $case.position
        run_id = $case.run_id
        repetition = $case.repetition
        mode = $case.mode
        vus = $case.vus
    }
}

$orderFile = Join-Path $RESULTS_PATH "run_order_$sessionId.csv"
$orderLog | Export-Csv -Path $orderFile -NoTypeInformation -Encoding UTF8

$total = $orderedCases.Count
$totalSeconds = ($total * ($WARMUP_SECONDS + $MEASUREMENT_SECONDS)) + ([Math]::Max(0, $total - 1) * $PAUSE_BETWEEN_RUNS_SECONDS)
$estimatedMinutes = [Math]::Ceiling($totalSeconds / 60)

Write-Host ''
Write-Host "[INFO] Modos: $($MODES -join ', ')"
Write-Host "[INFO] VUs: $($VUS_LEVELS -join ', ')"
Write-Host "[INFO] Repetições por condição: $REPETITIONS"
Write-Host "[INFO] Total: $total medições (~$estimatedMinutes minutos, incluindo aquecimento)"
Write-Host "[INFO] Aquecimento: $WARMUP_SECONDS s; medição estável: $MEASUREMENT_SECONDS s"
Write-Host "[INFO] Ordem aleatória guardada em: $orderFile"
Write-Host "[INFO] Resultados guardados em: $RESULTS_PATH"
Write-Host ''

$completed = 0
foreach ($case in $orderedCases) {
    Write-Host '--------------------------------------------' -ForegroundColor DarkGray
    Write-Host ">> $($case.position)/$total | $($case.mode) | $($case.vus) VUs | repetição $($case.repetition)" -ForegroundColor White
    Write-Host '--------------------------------------------' -ForegroundColor DarkGray

    $sharedArgs = @(
        '--env', "MODE=$($case.mode)",
        '--env', "VUS=$($case.vus)",
        '--env', "BASE_URL=$BASE_URL",
        '--env', "RUN_ID=$($case.run_id)",
        '--env', "REPETITION=$($case.repetition)",
        '--env', "STUB_DELAY_MS=$STUB_DELAY_MS",
        '--env', "TOMCAT_MAX_THREADS=$TOMCAT_MAX_THREADS",
        '--env', "RESULTS_DIR=$RESULTS_RELATIVE",
        '--quiet'
    )

    $warmupArgs = @('run') + $sharedArgs + @('--env', 'WARMUP=true', 'benchmark.js')
    & $K6 @warmupArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "O aquecimento terminou com código $LASTEXITCODE; vou continuar para guardar a medição."
    }

    $measurementArgs = @('run') + $sharedArgs + @('--env', 'WARMUP=false', 'benchmark.js')
    & $K6 @measurementArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "O k6 terminou com código $LASTEXITCODE. Verifica o JSON desta execução e continua a série."
    }

    $completed++
    Write-Host "[PROGRESSO] $completed/$total medições concluídas" -ForegroundColor Green

    if ($completed -lt $total) {
        Start-Sleep -Seconds $PAUSE_BETWEEN_RUNS_SECONDS
    }
}

Write-Host '============================================' -ForegroundColor Cyan
Write-Host '  Série de medições concluída!' -ForegroundColor Cyan
Write-Host "  Dados por execução: $RESULTS_PATH" -ForegroundColor Cyan
Write-Host "  Ordem: $orderFile" -ForegroundColor Cyan
Write-Host '  Para resumir e gerar gráficos: python plot_results.py' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan
