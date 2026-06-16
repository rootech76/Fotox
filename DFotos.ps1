#Procesamiento de fotos duplicadas

$Fotos = Get-ChildItem -Path 'R:\Midia\Fotos' -Recurse -file | Where-Object { $_.FullName -notlike '*CUARENTENA*' }
$Diccionario = @{}
$RutaCUARENTENA = 'R:\Midia\Fotos\CUARENTENA'

if (-not (Test-Path $RutaCUARENTENA)){

	New-Item -ItemType Directory -Path $RutaCUARENTENA   

}



# Almacenando Rutas y Hashes en el diccionario

for ($i = 0 ; $i -lt $Fotos.Count ; $i++){

	Write-Progress -Activity "Cargando el Directorio" -Status "$($i+1) de $($Fotos.Count)" -PercentComplete (($i / $Fotos.Count) * 100)

	$Diccionario[$Fotos[$i].FullName] = (Get-FileHash $Fotos[$i] -Algorithm MD5).hash



}


#Comparar y Mover fotos duplucadas a cuarentena

for ($i = 0 ; $i -lt $Fotos.Count ; $i++){

	Write-Progress -Activity "Comparando Fotos" -Status "$($i+1) de $($Fotos.Count)" -PercentComplete (($i / $Fotos.Count) * 100)

	$ContCoincidencias = 0
	$HuboCoincidencias = $False


	for ($c = $i + 1 ; $c -lt $Fotos.Count ; $c++){

		if ($Diccionario[$Fotos[$i].FullName] -eq $Diccionario[$Fotos[$c].FullName]){

			$ContCoincidencias++
			$HuboCoincidencias = $True


			if (Test-Path $Fotos[$c].FullName){
				
				$Destino = Join-Path -Path $RutaCUARENTENA  -ChildPath "$($i)-$($ContCoincidencias)$($Fotos[$i].Extension)"
				Move-Item -Path $Fotos[$c].FullName -Destination $Destino

			}




		}

	}

	if ($HuboCoincidencias){
		if (Test-Path $Fotos[$i].FullName){
			
			$Destino = Join-Path -Path $RutaCUARENTENA  -ChildPath "$($i)$($Fotos[$i].Extension)"
			Move-Item -Path $Fotos[$i].FullName -Destination $Destino


		}

	
	}


}
