# run_jupyter.ps1
# Lance Jupyter Notebook depuis la racine du projet Colab_files.
# Peut être exécuté depuis n'importe quel emplacement.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── 1. Résoudre la racine du projet (dossier parent de scripts/) ──────────────
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
Write-Host ""
Write-Host "Racine du projet : $projectRoot" -ForegroundColor Cyan

# ── 2. Vérifier requirements.txt ─────────────────────────────────────────────
if (-not (Test-Path "requirements.txt")) {
    Write-Host ""
    Write-Host "[ERREUR] requirements.txt introuvable dans $projectRoot" -ForegroundColor Red
    Write-Host "         Assurez-vous d'être dans le bon dossier." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] requirements.txt trouvé." -ForegroundColor Green

# ── 3. Vérifier le dossier notebooks/ ────────────────────────────────────────
if (-not (Test-Path "notebooks" -PathType Container)) {
    Write-Host ""
    Write-Host "[ERREUR] Le dossier notebooks/ est introuvable." -ForegroundColor Red
    Write-Host "         Créez-le ou vérifiez la structure du projet." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Dossier notebooks/ trouvé." -ForegroundColor Green

# ── 4. Vérifier .env ─────────────────────────────────────────────────────────
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "[ATTENTION] Fichier .env introuvable." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Copiez .env.example vers .env puis renseignez GEMINI_API_KEY :" -ForegroundColor Yellow
    Write-Host "  Copy-Item .env.example .env" -ForegroundColor White
    Write-Host ""
    Write-Host "  Jupyter va démarrer, mais les notebooks utilisant GEMINI_API_KEY" -ForegroundColor Yellow
    Write-Host "  échoueront sans cette clé configurée." -ForegroundColor Yellow
    Write-Host ""
}
else {
    Write-Host "[OK] Fichier .env trouvé." -ForegroundColor Green
}

# ── 5. Installer les dépendances ──────────────────────────────────────────────
Write-Host ""
Write-Host "Installation des dépendances (pip install -r requirements.txt)..." -ForegroundColor Cyan
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERREUR] L'installation des dépendances a échoué." -ForegroundColor Red
    Write-Host "         Vérifiez que Python et pip sont installés et accessibles." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Dépendances installées." -ForegroundColor Green

# ── 6. Lancer Jupyter Notebook ────────────────────────────────────────────────
Write-Host ""
Write-Host "Lancement de Jupyter Notebook sur notebooks/..." -ForegroundColor Cyan
Write-Host "(Appuyez sur Ctrl+C pour arrêter)" -ForegroundColor DarkGray
Write-Host ""
jupyter notebook notebooks/
