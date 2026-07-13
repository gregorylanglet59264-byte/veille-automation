# -*- coding: utf-8 -*-
# run_vigilance_soir.ps1
# Runs the local Monsieur Météo Vigilance Soir (J+1) pipeline.
# Executed daily at 4:30 PM.

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($null -eq $scriptDir) { $scriptDir = "C:\Users\grego\.gemini\antigravity\scratch\veille-automation" }
Set-Location $scriptDir

Write-Host "[LOG] $(Get-Date) - Starting Vigilance Soir..."
python generate_vigilance_twitter.py --period 1 --output vigilance_soir.jpg
python generate_vigilance_text.py --period 1 --output data/vigilance_soir_tweet.txt

if (Test-Path "vigilance_soir.jpg") {
    python send_tweet_by_email.py --image vigilance_soir.jpg --text-file data/vigilance_soir_tweet.txt --subject "⚠️ Monsieur Météo — Vigilance Soir (J+1)"
    Write-Host "[LOG] $(Get-Date) - Vigilance Soir sent successfully."
} else {
    Write-Warning "[ERROR] vigilance_soir.jpg not found. Skipping email."
}
