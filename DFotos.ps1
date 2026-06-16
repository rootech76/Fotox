#Procesamiento de fotos duplicadas

$Fotos = Get-ChildItem -Path 'R:\Midia\Fotos' -Recurse -file | Where-Object { $_.FullName -notlike '*CUARENTENA*' }
$Diccionario = @{}

if (-not (Test-Path R:\Midia\Fotos\CUARENTENA)){

	New-Item -ItemType Directory -Path  R:\Midia\Fotos -Name CUARENTENA 

}



# Almacenando Rutas y Hashes en el diccionario

for ($i = 0 ; $i -lt $Fotos.Count ; $i++){

	Write-Progress -Activity "Analizando Fotos" -Status "$($i+1) de $($Fotos.Count)" -PercentComplete (($i / $Fotos.Count) * 100)
	$Diccionario[$Fotos[$i].FullName] = (Get-FileHash $Fotos[$i] -Algorithm MD5).hash


}



for ($i = 0 ; $i -lt $Fotos.Count ; $i++){

	for ($c = $i + 1 ; $c -lt $Fotos.Count ; $c++){

		if ($Diccionario[$Fotos[$i].FullName] -eq $Diccionario[$Fotos[$c].FullName]){

		}

	}


}
