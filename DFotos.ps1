#Procesamiento de fotos duplicadas
$Fotos = Get-ChildItem -Path 'R:\Midia\Fotos' -Recurse -file | Where-Object { $_.FullName -notlike '*CUARENTENA*' }
$Diccionario = @{}
$RutaCUARENTENA = 'R:\Midia\Fotos\CUARENTENA'
$RutaScript = 'R:\WorkStation\Scripts\Nuevo Depurador de Fotos'
$ArchivoRestantes = Join-Path $RutaScript 'fotos_restantes.txt'
$ArchivoSimilares = Join-Path $RutaScript 'similares.txt'

if (-not (Test-Path $RutaCUARENTENA)){
    New-Item -ItemType Directory -Path $RutaCUARENTENA
}

# Fase 1 - Calcular MD5
$FotosRestantes = [System.Collections.Generic.List[string]]::new()
for ($i = 0 ; $i -lt $Fotos.Count ; $i++){
    Write-Progress -Activity "Cargando el Directorio" -Status "$($i+1) de $($Fotos.Count)" -PercentComplete (($i / $Fotos.Count) * 100)
    $Diccionario[$Fotos[$i].FullName] = (Get-FileHash $Fotos[$i] -Algorithm MD5).Hash
}

# Fase 2 - Comparar MD5 y mover duplicados exactos
$FotosMovidas = @{}
for ($i = 0 ; $i -lt $Fotos.Count ; $i++){
    Write-Progress -Activity "Comparando MD5" -Status "$($i+1) de $($Fotos.Count)" -PercentComplete (($i / $Fotos.Count) * 100)
    
    if ($FotosMovidas[$Fotos[$i].FullName]){ continue }
    
    $ContCoincidencias = 0
    $HuboCoincidencias = $False

    for ($c = $i + 1 ; $c -lt $Fotos.Count ; $c++){
        if ($FotosMovidas[$Fotos[$c].FullName]){ continue }
        
        if ($Diccionario[$Fotos[$i].FullName] -eq $Diccionario[$Fotos[$c].FullName]){
            $ContCoincidencias++
            $HuboCoincidencias = $True
            if (Test-Path $Fotos[$c].FullName){
                $Destino = Join-Path $RutaCUARENTENA "$($i)-$($ContCoincidencias)$($Fotos[$c].Extension)"
                Move-Item -Path $Fotos[$c].FullName -Destination $Destino
                $FotosMovidas[$Fotos[$c].FullName] = $True
            }
        }
    }
    if ($HuboCoincidencias){
        if (Test-Path $Fotos[$i].FullName){
            $Destino = Join-Path $RutaCUARENTENA "$($i)$($Fotos[$i].Extension)"
            Move-Item -Path $Fotos[$i].FullName -Destination $Destino
            $FotosMovidas[$Fotos[$i].FullName] = $True
        }
    } else {
        $FotosRestantes.Add($Fotos[$i].FullName)
    }
}

# Escribir fotos restantes para Python
$FotosRestantes | Set-Content $ArchivoRestantes

# Fase 3 - Comparar con pHash via Python
Write-Host "Iniciando comparación visual con pHash..."
python (Join-Path $RutaScript 'Compara_phash.py') $ArchivoRestantes $ArchivoSimilares

# Fase 4 - Mover similares detectados por pHash
if (Test-Path $ArchivoSimilares){
    $Similares = Get-Content $ArchivoSimilares
    $ContSimilar = 0
    foreach ($ruta in $Similares){
        if (Test-Path $ruta){
            $archivo = Get-Item $ruta
            $ContSimilar++
            $Destino = Join-Path $RutaCUARENTENA "phash-$($ContSimilar)$($archivo.Extension)"
            Move-Item -Path $ruta -Destination $Destino
        }
    }
    Remove-Item $ArchivoSimilares
}

Remove-Item $ArchivoRestantes
Write-Host "¡Proceso completado!"
