$msg = "para produccion ejecutar uv remove psycopg y psycopg2"
$instruction = "al agregar dependencias espesificas para el desarrollo espesificar arriba"

$width = $Host.UI.RawUI.WindowSize.Width

$pad = $width - $msg.Length

$left = "-" * [math]::Floor($pad/2)
$right = "-" * [math]::Ceiling($pad/2)

Write-Host "$left$msg$right"
Write-Host "$left$instruction$right"
uvicorn.exe myweb.asgi:application --host 127.0.0.1 --port 8080 --reload