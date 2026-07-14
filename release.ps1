# Legge VERSION_LAUNCHER dal sorgente e crea il tag git corrispondente
$match = Select-String -Path "HUB Tool - All-in-one.pyw" -Pattern 'VERSION_LAUNCHER\s*=\s*"(.+?)"'
if (-not $match) {
    Write-Error "VERSION_LAUNCHER non trovato nel sorgente."
    exit 1
}

$version = $match.Matches[0].Groups[1].Value
$tag = "v$version"

# Verifica che il tag non esista già
$existing = git tag --list $tag
if ($existing) {
    Write-Error "Il tag $tag esiste già. Aggiorna VERSION_LAUNCHER prima di rilasciare."
    exit 1
}

Write-Host "Versione rilevata: $version"
Write-Host "Creazione tag $tag ..."

git tag $tag
git push origin $tag

Write-Host "Tag $tag pushato. GitHub Actions creerà la release automaticamente."
