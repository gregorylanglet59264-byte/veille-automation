# -*- coding: utf-8 -*-
# run_debrief.ps1
# Runs the local Monsieur Météo Twitter list debrief pipeline.
# Executed every 2 hours.

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($null -eq $scriptDir) { $scriptDir = "C:\Users\grego\.gemini\antigravity\scratch\veille-automation" }
Set-Location $scriptDir

Write-Host "[LOG] $(Get-Date) - Starting Twitter List Debrief..."
python fetch_tweets.py --hours 2 --limit 100
python capture_debrief.py

if (Test-Path "debrief_twitter.jpg") {
    python send_tweet_by_email.py --image debrief_twitter.jpg --text-file data/debrief_tweet.txt --subject "🌤️ Monsieur Météo — Débriefing Twitter"
    Write-Host "[LOG] $(Get-Date) - Debrief sent successfully."
} else {
    Write-Warning "[ERROR] debrief_twitter.jpg not found. Skipping email."
}
