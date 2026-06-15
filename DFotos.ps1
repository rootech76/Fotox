#Elimina fotos duplicadas

$Fotos = Get-ChildItem -Path 'R:\Midia\Fotos' -Recurse -file

for ($i = 0 ; $i -lt $Fotos.Count ; $i++){
	Write-Progress -Activity "Analizando Fotos" -Status "$($i+1) de $($Fotos.Count)" -PercentComplete (($i / $Fotos.Count) * 100)

}
