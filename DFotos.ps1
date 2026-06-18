
#Fotox - Procesamiento de fotos duplicadas
#$RutaFotos = Read-Host "Ruta del directorio de fotos"
#$RutaCUARENTENA = Read-Host "Ruta para la carpeta CUARENTENA"

$RutaCUARENTENA = 'R:\Midia\Fotos\CUARENTENA'
$RutaScript = 'R:\WorkStation\Scripts\Fotox'

$Fotos = Get-ChildItem -Path $RutaFotos -Recurse -file | Where-Object { $_.FullName -notlike '*CUARENTENA*' }
$Diccionario = @{}
$RutaScript = 'R:\WorkStation\Scripts\Fotox'
$ArchivoRestantes = Join-Path $RutaScript 'fotos_restantes.txt'
$ArchivoSimilares = Join-Path $RutaScript 'similares.txt'

if (-not (Test-Path $RutaCUARENTENA)){
    New-Item -ItemType Directory -Path $RutaCUARENTENA
}

# Fase 1 - Calcular MD5
for ($i = 0 ; $i -lt $Fotos.Count ; $i++){
    Write-Progress -Activity "Fase 1 - Cargando hashes MD5" -Status "$($i+1) de $($Fotos.Count)" -PercentComplete (($i / $Fotos.Count) * 100)
    $Diccionario[$Fotos[$i].FullName] = (Get-FileHash $Fotos[$i] -Algorithm MD5).Hash
}
Write-Progress -Activity "Fase 1 - Cargando hashes MD5" -Completed

# Fase 2 - Comparar MD5 y mover duplicados exactos
$FotosMovidas = @{}
$FotosRestantes = [System.Collections.Generic.List[string]]::new()
$GrupoActual = 0

for ($i = 0 ; $i -lt $Fotos.Count ; $i++){
    Write-Progress -Activity "Fase 2 - Comparando MD5" -Status "$($i+1) de $($Fotos.Count)" -PercentComplete (($i / $Fotos.Count) * 100)

    if ($FotosMovidas[$Fotos[$i].FullName]){ continue }

    $ContCoincidencias = 0
    $HuboCoincidencias = $False

    for ($c = $i + 1 ; $c -lt $Fotos.Count ; $c++){
        if ($FotosMovidas[$Fotos[$c].FullName]){ continue }

        if ($Diccionario[$Fotos[$i].FullName] -eq $Diccionario[$Fotos[$c].FullName]){
            if (-not $HuboCoincidencias){
                $GrupoActual++
            }
            $ContCoincidencias++
            $HuboCoincidencias = $True
            if (Test-Path $Fotos[$c].FullName){
                $timestamp = Get-Date -Format "ddMMyyyyyHHmmssfff"
                $Destino = Join-Path $RutaCUARENTENA "md5-$($GrupoActual)-$($ContCoincidencias)_$($timestamp)$($Fotos[$c].Extension)"
                Move-Item -Path $Fotos[$c].FullName -Destination $Destino
                $FotosMovidas[$Fotos[$c].FullName] = $True
            }
        }
    }
    if ($HuboCoincidencias){
        if (Test-Path $Fotos[$i].FullName){
            $timestamp = Get-Date -Format "ddMMyyyyyHHmmssfff"
            $Destino = Join-Path $RutaCUARENTENA "md5-$($GrupoActual)_$($timestamp)$($Fotos[$i].Extension)"
            Move-Item -Path $Fotos[$i].FullName -Destination $Destino
            $FotosMovidas[$Fotos[$i].FullName] = $True
        }
    } else {
        $FotosRestantes.Add($Fotos[$i].FullName)
    }
}
Write-Progress -Activity "Fase 2 - Comparando MD5" -Completed

Write-Host "Duplicados exactos encontrados: $GrupoActual grupos"

# Escribir fotos restantes para Python
$FotosRestantes | Set-Content $ArchivoRestantes

# Fase 3 - Comparar con pHash via Python
Write-Host "Iniciando comparación visual con pHash..."
python (Join-Path $RutaScript 'Compara_phash.py') $ArchivoRestantes $ArchivoSimilares

# Fase 4 - Mover similares detectados por pHash
if (Test-Path $ArchivoSimilares){
    $Similares = Get-Content $ArchivoSimilares
    foreach ($linea in $Similares){
        $partes = $linea -split '\|'
        $grupo = $partes[0]
        $tipo = $partes[1]
        $ruta = $partes[2]
        if (Test-Path $ruta){
            $archivo = Get-Item $ruta
            $timestamp = Get-Date -Format "ddMMyyyyyHHmmssfff"
            $Destino = Join-Path $RutaCUARENTENA "phash-$($grupo)$($tipo)_$($timestamp)$($archivo.Extension)"
            Move-Item -Path $ruta -Destination $Destino
        }
    }
    Remove-Item $ArchivoSimilares
}

Remove-Item $ArchivoRestantes
Write-Host "¡Proceso completado!"
