#Elimina fotos duplicadas

$Fotos = Get-ChildItem -Path 'R:\Midia\Fotos' -Recurse -file
$Diccionario = @{}
for ($i = 0 ; $i -lt $Fotos.Count ; $i++){

	Write-Progress -Activity "Analizando Fotos" -Status "$($i+1) de $($Fotos.Count)" -PercentComplete (($i / $Fotos.Count) * 100)
	$Diccionario[$Fotos[$i].FullName] = (Get-FileHash $Fotos[$i] -Algorithm MD5).hash


}
