# -*- coding: utf-8 -*-
import os
import json
import urllib.request

openrouter_key = os.environ.get("OPENROUTER_API_KEY", "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")
print("Clé utilisée :", openrouter_key[:15] + "...")

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {openrouter_key}"
}
payload = {
    "model": "deepseek/deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": "Tu es un assistant utile."},
        {"role": "user", "content": "Dis bonjour courtement."}
    ]
}

try:
    print("Envoi de la requête à OpenRouter...")
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=20) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        print("Réponse reçue :")
        print(json.dumps(res_data, indent=2))
except Exception as e:
    print("Erreur :", e)
