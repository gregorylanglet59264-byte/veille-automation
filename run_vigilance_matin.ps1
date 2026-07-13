# -*- coding: utf-8 -*-
# run_vigilance_matin.ps1
# Runs the local Monsieur Météo Vigilance Matin (J0) pipeline.
# Executed daily at 6:30 AM.

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($null -eq $scriptDir) { $scriptDir = "C:\Users\grego\.gemini\antigravity\scratch\veille-automation" }
Set-Location $scriptDir

Write-Host "[LOG] $(Get-Date) - Starting Vigilance Matin..."
python generate_vigilance_twitter.py --period 0 --output vigilance_matin.jpg
python generate_vigilance_text.py --period 0 --output data/vigilance_matin_tweet.txt

if (Test-Path "vigilance_matin.jpg") {
    python send_tweet_by_email.py --image vigilance_matin.jpg --text-file data/vigilance_matin_tweet.txt --subject "⚠️ Monsieur Météo — Vigilance Matin (J0)"
    Write-Host "[LOG] $(Get-Date) - Vigilance Matin sent successfully."
} else {
    Write-Warning "[ERROR] vigilance_matin.jpg not found. Skipping email."
}
