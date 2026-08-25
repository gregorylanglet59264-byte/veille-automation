# BULLETIN DE PRÉVISIONS MÉTÉO INFOCLIMAT (RÉGIONAL HAUTS-DE-FRANCE)
**Généré le :** Mardi 25 Août 2026
**Période :** Semaine 1 (**Du Mardi 25 au Dimanche 30 Août 2026**

---

#### [W1_KEY_POINT_1]
**Retour des orages :** Dégradation orageuse marquée mercredi et jeudi, avec un risque de phénomènes localement violents.

#### [W1_KEY_POINT_2]
**Chaleur lourde :** Températures encore élevées en début de semaine, avec des maximales atteignant 27 à 30°C avant le rafraîchissement.

#### [W1_KEY_POINT_3]
**Forte baisse thermique :** Net rafraîchissement dès vendredi, avec des maximales ne dépassant plus 22-23°C.

#### [W1_KEY_POINT_4]
**Vigilance jaune :** Les départements de la Somme, de l'Oise et de l'Aisne sont en vigilance jaune pour orages ce mardi.

#### [W1_KEY_POINT_5]
**Fin de semaine contrastée :** Temps encore instable samedi, mais nette amélioration attendue pour dimanche avec un ciel plus ensoleillé.

---

#### [W1_MODEL_START]

##### [W1_MODEL_NAME]
**Analyse des modèles (Synthèse) :**

##### [W1_MODEL_SCENARIO]
**(1) CEP (ECMWF)** : Scénario privilégié. Talweg d'altitude s'approchant par l'ouest, déclenchant une activité orageuse mercredi et jeudi. Dépression secondaire sur le proche Atlantique vendredi, apportant un flux de Sud-Ouest maritime plus frais et humide. Amélioration progressive samedi par l'ouest.

##### [W1_MODEL_SENSIBLE_WEATHER]
**Risque principal** : Orages potentiellement forts mercredi après-midi et jeudi, avec un risque de grêle et de rafales de vent. **Risque secondaire** : Cumuls de pluie localement importants (15 à 20 mm).

##### [W1_MODEL_AFFECTED_ZONES]
**Mercredi** : Toute la région, risque plus marqué sur l'intérieur des terres (Oise, Aisne, Somme). **Jeudi** : Toute la région, avec un risque de pluies plus soutenues sur le Nord et le Pas-de-Calais.

##### [W1_MODEL_EXTRACTION_CONF]
**Élevée (80%)** : Fort consensus sur la séquence "chaleur lourde puis dégradation orageuse puis rafraîchissement".

##### [W1_MODEL_SCENARIO_SUPPORT]
**Détail des runs** : GFS, UKMO et Arpège sont alignés sur cette évolution. Les différences portent sur le timing et l'intensité des orages, notamment jeudi.

##### [W1_MODEL_STATUS]
**Confirmé**

##### [W1_MODEL_MENTIONS_COUNT]
**5** (Sources : Bulletins Météo-France, discussions Infoclimat)

##### [W1_MODEL_RUN]
**25/08/2026 06Z**

##### [W1_MODEL_TIMING]
**Échéance : J+0 à J+5**

##### [W1_MODEL_DETAILS]**
**Évolution heure par heure** : Amélioration nette samedi soir, avec des éclaircies de plus en plus franches et un vent de Sud-Ouest encore modéré.

##### [W1_MODEL_END]

---

#### [W1_CONVERGENCES]
**Points de convergence entre modèles :**
1.  **Dégradation orageuse** : Tous les modèles s'accordent sur une dégradation orageuse entre mercredi et jeudi.
2.  **Rafraîchissement** : Consensus sur une nette baisse des températures à partir de vendredi.
3.  **Accalmie** : Tendance commune vers une amélioration du temps pour la journée de dimanche.

---

#### [W1_DIVERGENCES]
**Points de divergence entre modèles :**
1.  **Intensité des orages** : Incertitude sur la violence des orages de jeudi. Le scénario le plus défavorable (grêle et rafales destructrices) reste conditionnel à l'évolution du talweg.
2.  **Cumuls de pluie** : Les cumuls les plus importants sont attendus entre le Nord et l'Aisne, mais la localisation exacte des fortes pluies reste incertaine.

---

#### [W1_ZONES_JSON_START]
```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance de nuages et d'éclaircies, dégradation orageuse mercredi et jeudi. Amélioration samedi soir.",
      "temperatures": "Maximales : 25-26°C mardi, 27-28°C mercredi, 26-28°C jeudi, 21-22°C vendredi, 22-24°C samedi. Minimales : 15-18°C.",
      "rain_storms": "Averses mardi soir (Avesnois). Orages possibles mercredi en fin de nuit et jeudi matin. Pluie max : 15 mm jeudi.",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnes-sur-Helpe",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi. Vent assez fort lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Localisation des fortes pluies jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages et éclaircies, dégradation orageuse mercredi soir et jeudi. Amélioration samedi.",
      "temperatures": "Maximales : 24-26°C mardi, 26-28°C mercredi, 24-27°C jeudi, 20-23°C vendredi, 21-24°C samedi. Minimales : 15-16°C.",
      "rain_storms": "Gouttes possibles près des côtes mercredi matin. Averses orageuses mercredi nuit. Pluie max : 15 mm sur le Ternois.",
      "spatial_scope": "regional",
      "location": "Arras, Calais, Boulogne-sur-Mer, Lens, Montreuil",
      "wind": "Est puis Sud-Ouest modéré. Rafales jusqu'à 55 km/h vendredi. Vent assez fort sur le littoral lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Comportement des orages près des côtes de la Manche",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages isolés. Très nuageux mercredi et jeudi avec averses. Amélioration samedi.",
      "temperatures": "Maximales : 24-27°C mardi, 27-29°C mercredi, 23-26°C jeudi, 20-22°C vendredi, 22°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi après-midi. Pluie max : 15 mm sur le Vermandois jeudi.",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Cayeux-sur-Mer, Péronne",
      "wind": "Est puis Ouest-Sud-Ouest modéré. Vent assez fort sur le littoral vendredi et lundi.",
      "sensitive_period": "Mardi 25 après-midi, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Déclenchement des orages mardi après-midi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux avec orages possibles mardi soir. Temps ensoleillé mercredi matin puis voile nuageux. Orages jeudi.",
      "temperatures": "Maximales : 27-28°C mardi, 27-29°C mercredi, 25-27°C jeudi, 21-23°C vendredi, 22°C samedi. Minimales : 13-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi fin de journée et mercredi en 2e partie de nuit. Pluie max : 10 mm.",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil",
      "wind": "Faible puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en fin de journée, mercredi 26 nuit et jeudi 27",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages mercredi soir",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Soleil mardi matin puis orages isolés. Temps lumineux mercredi. Orages jeudi en fin de journée. Amélioration samedi.",
      "temperatures": "Maximales : 26-28°C mardi, 27-30°C mercredi, 26-27°C jeudi, 21-23°C vendredi, 22-24°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi soir. Pluie max : 20 mm sur la Thiérache jeudi.",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en soirée, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Cumuls de pluie sur la Thiérache jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```
#### [W1_ZONES_JSON_END]

---

#### [W1_SOLID_POINTS]
**Points solides pour la semaine 1 :**
1.  **Chaleur lourde** :Mardi et mercredi seront encore chauds et humides, avec des maximales dépassant localement les 28°C.
2.  **Dégradation orageuse** : Un épisode orageux est quasi-certain entre mercredi et jeudi, avec un risque de grêle et de fortes rafales.
3.  **Rafraîchissement net** : Dès vendredi, les températures chutent pour revenir sous les normales de saison.

---

#### [W1_FRAGILE_POINTS]
**Points fragiles pour la semaine 1 :**
1.  **Localisation des orages** : L'endroit exact où les orages seront les plus violents reste incertain.
2.  **Cumuls de précipitations** : Les quantités de pluie pourraient varier significativement d'un endroit à l'autre, avec un risque de "taches de léopard".

---

#### [W1_NEXT_RUNS_TO_WATCH]
**Prochains runs à surveiller :**
*   **Run Arpège de ce soir (18Z)** : Pour affiner la menace orageuse de mercredi.
*   **Run CEP de cette nuit** : Pour fiabiliser le scénario de dégradation de jeudi.

---

#### [W1_PHASE_1_DATES]
**Phase 1 : Mardi 25 & Mercredi 26 Août**

#### [W1_PHASE_1]
**Chaleur lourde et humide avec développement d'orages isolés.**

#### [W1_PHASE_2_DATES]
**Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**

---

#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]

---

###) & Semaine 2 (Du Lundi 31 Août au Dimanche 6 Septembre 2026)
*Analyse régionale ciblée sur les départements : Nord (59), Pas-de-Calais (62), Somme (80), Oise (60) et Aisne (02).*

========================================

## 📈 SYNTHÈSE DES INDICATEURS DE CONFIANCE
- **Consensus des modèles :** Modéré — *Accord régional*
- **Fiabilité du scénario majoritaire :** Stable — *Incertitude en semaine 2*
- **Stabilité des cartes/scénarios :** 6 / 63 — *6 cartes analysées*
- **Niveau d'incertitude global :** Timing — *Transition thermique*

## 🗓️ SEMAINE 1 : **Du Mardi 25 au Dimanche 30 Août 2026**

---

#### [W1_KEY_POINT_1]
**Retour des orages :** Dégradation orageuse marquée mercredi et jeudi, avec un risque de phénomènes localement violents.

#### [W1_KEY_POINT_2]
**Chaleur lourde :** Températures encore élevées en début de semaine, avec des maximales atteignant 27 à 30°C avant le rafraîchissement.

#### [W1_KEY_POINT_3]
**Forte baisse thermique :** Net rafraîchissement dès vendredi, avec des maximales ne dépassant plus 22-23°C.

#### [W1_KEY_POINT_4]
**Vigilance jaune :** Les départements de la Somme, de l'Oise et de l'Aisne sont en vigilance jaune pour orages ce mardi.

#### [W1_KEY_POINT_5]
**Fin de semaine contrastée :** Temps encore instable samedi, mais nette amélioration attendue pour dimanche avec un ciel plus ensoleillé.

---

#### [W1_MODEL_START]

##### [W1_MODEL_NAME]
**Analyse des modèles (Synthèse) :**

##### [W1_MODEL_SCENARIO]
**(1) CEP (ECMWF)** : Scénario privilégié. Talweg d'altitude s'approchant par l'ouest, déclenchant une activité orageuse mercredi et jeudi. Dépression secondaire sur le proche Atlantique vendredi, apportant un flux de Sud-Ouest maritime plus frais et humide. Amélioration progressive samedi par l'ouest.

##### [W1_MODEL_SENSIBLE_WEATHER]
**Risque principal** : Orages potentiellement forts mercredi après-midi et jeudi, avec un risque de grêle et de rafales de vent. **Risque secondaire** : Cumuls de pluie localement importants (15 à 20 mm).

##### [W1_MODEL_AFFECTED_ZONES]
**Mercredi** : Toute la région, risque plus marqué sur l'intérieur des terres (Oise, Aisne, Somme). **Jeudi** : Toute la région, avec un risque de pluies plus soutenues sur le Nord et le Pas-de-Calais.

##### [W1_MODEL_EXTRACTION_CONF]
**Élevée (80%)** : Fort consensus sur la séquence "chaleur lourde puis dégradation orageuse puis rafraîchissement".

##### [W1_MODEL_SCENARIO_SUPPORT]
**Détail des runs** : GFS, UKMO et Arpège sont alignés sur cette évolution. Les différences portent sur le timing et l'intensité des orages, notamment jeudi.

##### [W1_MODEL_STATUS]
**Confirmé**

##### [W1_MODEL_MENTIONS_COUNT]
**5** (Sources : Bulletins Météo-France, discussions Infoclimat)

##### [W1_MODEL_RUN]
**25/08/2026 06Z**

##### [W1_MODEL_TIMING]
**Échéance : J+0 à J+5**

##### [W1_MODEL_DETAILS]**
**Évolution heure par heure** : Amélioration nette samedi soir, avec des éclaircies de plus en plus franches et un vent de Sud-Ouest encore modéré.

##### [W1_MODEL_END]

---

#### [W1_CONVERGENCES]
**Points de convergence entre modèles :**
1.  **Dégradation orageuse** : Tous les modèles s'accordent sur une dégradation orageuse entre mercredi et jeudi.
2.  **Rafraîchissement** : Consensus sur une nette baisse des températures à partir de vendredi.
3.  **Accalmie** : Tendance commune vers une amélioration du temps pour la journée de dimanche.

---

#### [W1_DIVERGENCES]
**Points de divergence entre modèles :**
1.  **Intensité des orages** : Incertitude sur la violence des orages de jeudi. Le scénario le plus défavorable (grêle et rafales destructrices) reste conditionnel à l'évolution du talweg.
2.  **Cumuls de pluie** : Les cumuls les plus importants sont attendus entre le Nord et l'Aisne, mais la localisation exacte des fortes pluies reste incertaine.

---

#### [W1_ZONES_JSON_START]
```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance de nuages et d'éclaircies, dégradation orageuse mercredi et jeudi. Amélioration samedi soir.",
      "temperatures": "Maximales : 25-26°C mardi, 27-28°C mercredi, 26-28°C jeudi, 21-22°C vendredi, 22-24°C samedi. Minimales : 15-18°C.",
      "rain_storms": "Averses mardi soir (Avesnois). Orages possibles mercredi en fin de nuit et jeudi matin. Pluie max : 15 mm jeudi.",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnes-sur-Helpe",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi. Vent assez fort lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Localisation des fortes pluies jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages et éclaircies, dégradation orageuse mercredi soir et jeudi. Amélioration samedi.",
      "temperatures": "Maximales : 24-26°C mardi, 26-28°C mercredi, 24-27°C jeudi, 20-23°C vendredi, 21-24°C samedi. Minimales : 15-16°C.",
      "rain_storms": "Gouttes possibles près des côtes mercredi matin. Averses orageuses mercredi nuit. Pluie max : 15 mm sur le Ternois.",
      "spatial_scope": "regional",
      "location": "Arras, Calais, Boulogne-sur-Mer, Lens, Montreuil",
      "wind": "Est puis Sud-Ouest modéré. Rafales jusqu'à 55 km/h vendredi. Vent assez fort sur le littoral lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Comportement des orages près des côtes de la Manche",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages isolés. Très nuageux mercredi et jeudi avec averses. Amélioration samedi.",
      "temperatures": "Maximales : 24-27°C mardi, 27-29°C mercredi, 23-26°C jeudi, 20-22°C vendredi, 22°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi après-midi. Pluie max : 15 mm sur le Vermandois jeudi.",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Cayeux-sur-Mer, Péronne",
      "wind": "Est puis Ouest-Sud-Ouest modéré. Vent assez fort sur le littoral vendredi et lundi.",
      "sensitive_period": "Mardi 25 après-midi, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Déclenchement des orages mardi après-midi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux avec orages possibles mardi soir. Temps ensoleillé mercredi matin puis voile nuageux. Orages jeudi.",
      "temperatures": "Maximales : 27-28°C mardi, 27-29°C mercredi, 25-27°C jeudi, 21-23°C vendredi, 22°C samedi. Minimales : 13-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi fin de journée et mercredi en 2e partie de nuit. Pluie max : 10 mm.",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil",
      "wind": "Faible puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en fin de journée, mercredi 26 nuit et jeudi 27",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages mercredi soir",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Soleil mardi matin puis orages isolés. Temps lumineux mercredi. Orages jeudi en fin de journée. Amélioration samedi.",
      "temperatures": "Maximales : 26-28°C mardi, 27-30°C mercredi, 26-27°C jeudi, 21-23°C vendredi, 22-24°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi soir. Pluie max : 20 mm sur la Thiérache jeudi.",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en soirée, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Cumuls de pluie sur la Thiérache jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```
#### [W1_ZONES_JSON_END]

---

#### [W1_SOLID_POINTS]
**Points solides pour la semaine 1 :**
1.  **Chaleur lourde** :Mardi et mercredi seront encore chauds et humides, avec des maximales dépassant localement les 28°C.
2.  **Dégradation orageuse** : Un épisode orageux est quasi-certain entre mercredi et jeudi, avec un risque de grêle et de fortes rafales.
3.  **Rafraîchissement net** : Dès vendredi, les températures chutent pour revenir sous les normales de saison.

---

#### [W1_FRAGILE_POINTS]
**Points fragiles pour la semaine 1 :**
1.  **Localisation des orages** : L'endroit exact où les orages seront les plus violents reste incertain.
2.  **Cumuls de précipitations** : Les quantités de pluie pourraient varier significativement d'un endroit à l'autre, avec un risque de "taches de léopard".

---

#### [W1_NEXT_RUNS_TO_WATCH]
**Prochains runs à surveiller :**
*   **Run Arpège de ce soir (18Z)** : Pour affiner la menace orageuse de mercredi.
*   **Run CEP de cette nuit** : Pour fiabiliser le scénario de dégradation de jeudi.

---

#### [W1_PHASE_1_DATES]
**Phase 1 : Mardi 25 & Mercredi 26 Août**

#### [W1_PHASE_1]
**Chaleur lourde et humide avec développement d'orages isolés.**

#### [W1_PHASE_2_DATES]
**Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**

---

#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]

---

###
### 💡 Points clés de la semaine 1
1. **Retour des orages :** Dégradation orageuse marquée mercredi et jeudi, avec un risque de phénomènes localement violents.

#### [W1_KEY_POINT_2]
**Chaleur lourde :** Températures encore élevées en début de semaine, avec des maximales atteignant 27 à 30°C avant le rafraîchissement.

#### [W1_KEY_POINT_3]
**Forte baisse thermique :** Net rafraîchissement dès vendredi, avec des maximales ne dépassant plus 22-23°C.

#### [W1_KEY_POINT_4]
**Vigilance jaune :** Les départements de la Somme, de l'Oise et de l'Aisne sont en vigilance jaune pour orages ce mardi.

#### [W1_KEY_POINT_5]
**Fin de semaine contrastée :** Temps encore instable samedi, mais nette amélioration attendue pour dimanche avec un ciel plus ensoleillé.



#### [W1_MODEL_START]

##### [W1_MODEL_NAME]
**Analyse des modèles (Synthèse) :**

##### [W1_MODEL_SCENARIO]
**(1) CEP (ECMWF)** : Scénario privilégié. Talweg d'altitude s'approchant par l'ouest, déclenchant une activité orageuse mercredi et jeudi. Dépression secondaire sur le proche Atlantique vendredi, apportant un flux de Sud-Ouest maritime plus frais et humide. Amélioration progressive samedi par l'ouest.

##### [W1_MODEL_SENSIBLE_WEATHER]
**Risque principal** : Orages potentiellement forts mercredi après-midi et jeudi, avec un risque de grêle et de rafales de vent. **Risque secondaire** : Cumuls de pluie localement importants (15 à 20 mm).

##### [W1_MODEL_AFFECTED_ZONES]
**Mercredi** : Toute la région, risque plus marqué sur l'intérieur des terres (Oise, Aisne, Somme). **Jeudi** : Toute la région, avec un risque de pluies plus soutenues sur le Nord et le Pas-de-Calais.

##### [W1_MODEL_EXTRACTION_CONF]
**Élevée (80%)** : Fort consensus sur la séquence "chaleur lourde puis dégradation orageuse puis rafraîchissement".

##### [W1_MODEL_SCENARIO_SUPPORT]
**Détail des runs** : GFS, UKMO et Arpège sont alignés sur cette évolution. Les différences portent sur le timing et l'intensité des orages, notamment jeudi.

##### [W1_MODEL_STATUS]
**Confirmé**

##### [W1_MODEL_MENTIONS_COUNT]
**5** (Sources : Bulletins Météo-France, discussions Infoclimat)

##### [W1_MODEL_RUN]
**25/08/2026 06Z**

##### [W1_MODEL_TIMING]
**Échéance : J+0 à J+5**

##### [W1_MODEL_DETAILS]**
**Évolution heure par heure** : Amélioration nette samedi soir, avec des éclaircies de plus en plus franches et un vent de Sud-Ouest encore modéré.

##### [W1_MODEL_END]



#### [W1_CONVERGENCES]
**Points de convergence entre modèles :**
1.  **Dégradation orageuse** : Tous les modèles s'accordent sur une dégradation orageuse entre mercredi et jeudi.
2.  **Rafraîchissement** : Consensus sur une nette baisse des températures à partir de vendredi.
3.  **Accalmie** : Tendance commune vers une amélioration du temps pour la journée de dimanche.



#### [W1_DIVERGENCES]
**Points de divergence entre modèles :**
1.  **Intensité des orages** : Incertitude sur la violence des orages de jeudi. Le scénario le plus défavorable (grêle et rafales destructrices) reste conditionnel à l'évolution du talweg.
2.  **Cumuls de pluie** : Les cumuls les plus importants sont attendus entre le Nord et l'Aisne, mais la localisation exacte des fortes pluies reste incertaine.



#### [W1_ZONES_JSON_START]
```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance de nuages et d'éclaircies, dégradation orageuse mercredi et jeudi. Amélioration samedi soir.",
      "temperatures": "Maximales : 25-26°C mardi, 27-28°C mercredi, 26-28°C jeudi, 21-22°C vendredi, 22-24°C samedi. Minimales : 15-18°C.",
      "rain_storms": "Averses mardi soir (Avesnois). Orages possibles mercredi en fin de nuit et jeudi matin. Pluie max : 15 mm jeudi.",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnes-sur-Helpe",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi. Vent assez fort lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Localisation des fortes pluies jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages et éclaircies, dégradation orageuse mercredi soir et jeudi. Amélioration samedi.",
      "temperatures": "Maximales : 24-26°C mardi, 26-28°C mercredi, 24-27°C jeudi, 20-23°C vendredi, 21-24°C samedi. Minimales : 15-16°C.",
      "rain_storms": "Gouttes possibles près des côtes mercredi matin. Averses orageuses mercredi nuit. Pluie max : 15 mm sur le Ternois.",
      "spatial_scope": "regional",
      "location": "Arras, Calais, Boulogne-sur-Mer, Lens, Montreuil",
      "wind": "Est puis Sud-Ouest modéré. Rafales jusqu'à 55 km/h vendredi. Vent assez fort sur le littoral lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Comportement des orages près des côtes de la Manche",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages isolés. Très nuageux mercredi et jeudi avec averses. Amélioration samedi.",
      "temperatures": "Maximales : 24-27°C mardi, 27-29°C mercredi, 23-26°C jeudi, 20-22°C vendredi, 22°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi après-midi. Pluie max : 15 mm sur le Vermandois jeudi.",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Cayeux-sur-Mer, Péronne",
      "wind": "Est puis Ouest-Sud-Ouest modéré. Vent assez fort sur le littoral vendredi et lundi.",
      "sensitive_period": "Mardi 25 après-midi, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Déclenchement des orages mardi après-midi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux avec orages possibles mardi soir. Temps ensoleillé mercredi matin puis voile nuageux. Orages jeudi.",
      "temperatures": "Maximales : 27-28°C mardi, 27-29°C mercredi, 25-27°C jeudi, 21-23°C vendredi, 22°C samedi. Minimales : 13-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi fin de journée et mercredi en 2e partie de nuit. Pluie max : 10 mm.",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil",
      "wind": "Faible puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en fin de journée, mercredi 26 nuit et jeudi 27",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages mercredi soir",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Soleil mardi matin puis orages isolés. Temps lumineux mercredi. Orages jeudi en fin de journée. Amélioration samedi.",
      "temperatures": "Maximales : 26-28°C mardi, 27-30°C mercredi, 26-27°C jeudi, 21-23°C vendredi, 22-24°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi soir. Pluie max : 20 mm sur la Thiérache jeudi.",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en soirée, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Cumuls de pluie sur la Thiérache jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```
#### [W1_ZONES_JSON_END]



#### [W1_SOLID_POINTS]
**Points solides pour la semaine 1 :**
1.  **Chaleur lourde** :Mardi et mercredi seront encore chauds et humides, avec des maximales dépassant localement les 28°C.
2.  **Dégradation orageuse** : Un épisode orageux est quasi-certain entre mercredi et jeudi, avec un risque de grêle et de fortes rafales.
3.  **Rafraîchissement net** : Dès vendredi, les températures chutent pour revenir sous les normales de saison.



#### [W1_FRAGILE_POINTS]
**Points fragiles pour la semaine 1 :**
1.  **Localisation des orages** : L'endroit exact où les orages seront les plus violents reste incertain.
2.  **Cumuls de précipitations** : Les quantités de pluie pourraient varier significativement d'un endroit à l'autre, avec un risque de "taches de léopard".



#### [W1_NEXT_RUNS_TO_WATCH]
**Prochains runs à surveiller :**
*   **Run Arpège de ce soir (18Z)** : Pour affiner la menace orageuse de mercredi.
*   **Run CEP de cette nuit** : Pour fiabiliser le scénario de dégradation de jeudi.



#### [W1_PHASE_1_DATES]
**Phase 1 : Mardi 25 & Mercredi 26 Août**

#### [W1_PHASE_1]
**Chaleur lourde et humide avec développement d'orages isolés.**

#### [W1_PHASE_2_DATES]
**Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**



#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]



###
2. **Chaleur lourde :** Températures encore élevées en début de semaine, avec des maximales atteignant 27 à 30°C avant le rafraîchissement.

#### [W1_KEY_POINT_3]
**Forte baisse thermique :** Net rafraîchissement dès vendredi, avec des maximales ne dépassant plus 22-23°C.

#### [W1_KEY_POINT_4]
**Vigilance jaune :** Les départements de la Somme, de l'Oise et de l'Aisne sont en vigilance jaune pour orages ce mardi.

#### [W1_KEY_POINT_5]
**Fin de semaine contrastée :** Temps encore instable samedi, mais nette amélioration attendue pour dimanche avec un ciel plus ensoleillé.



#### [W1_MODEL_START]

##### [W1_MODEL_NAME]
**Analyse des modèles (Synthèse) :**

##### [W1_MODEL_SCENARIO]
**(1) CEP (ECMWF)** : Scénario privilégié. Talweg d'altitude s'approchant par l'ouest, déclenchant une activité orageuse mercredi et jeudi. Dépression secondaire sur le proche Atlantique vendredi, apportant un flux de Sud-Ouest maritime plus frais et humide. Amélioration progressive samedi par l'ouest.

##### [W1_MODEL_SENSIBLE_WEATHER]
**Risque principal** : Orages potentiellement forts mercredi après-midi et jeudi, avec un risque de grêle et de rafales de vent. **Risque secondaire** : Cumuls de pluie localement importants (15 à 20 mm).

##### [W1_MODEL_AFFECTED_ZONES]
**Mercredi** : Toute la région, risque plus marqué sur l'intérieur des terres (Oise, Aisne, Somme). **Jeudi** : Toute la région, avec un risque de pluies plus soutenues sur le Nord et le Pas-de-Calais.

##### [W1_MODEL_EXTRACTION_CONF]
**Élevée (80%)** : Fort consensus sur la séquence "chaleur lourde puis dégradation orageuse puis rafraîchissement".

##### [W1_MODEL_SCENARIO_SUPPORT]
**Détail des runs** : GFS, UKMO et Arpège sont alignés sur cette évolution. Les différences portent sur le timing et l'intensité des orages, notamment jeudi.

##### [W1_MODEL_STATUS]
**Confirmé**

##### [W1_MODEL_MENTIONS_COUNT]
**5** (Sources : Bulletins Météo-France, discussions Infoclimat)

##### [W1_MODEL_RUN]
**25/08/2026 06Z**

##### [W1_MODEL_TIMING]
**Échéance : J+0 à J+5**

##### [W1_MODEL_DETAILS]**
**Évolution heure par heure** : Amélioration nette samedi soir, avec des éclaircies de plus en plus franches et un vent de Sud-Ouest encore modéré.

##### [W1_MODEL_END]



#### [W1_CONVERGENCES]
**Points de convergence entre modèles :**
1.  **Dégradation orageuse** : Tous les modèles s'accordent sur une dégradation orageuse entre mercredi et jeudi.
2.  **Rafraîchissement** : Consensus sur une nette baisse des températures à partir de vendredi.
3.  **Accalmie** : Tendance commune vers une amélioration du temps pour la journée de dimanche.



#### [W1_DIVERGENCES]
**Points de divergence entre modèles :**
1.  **Intensité des orages** : Incertitude sur la violence des orages de jeudi. Le scénario le plus défavorable (grêle et rafales destructrices) reste conditionnel à l'évolution du talweg.
2.  **Cumuls de pluie** : Les cumuls les plus importants sont attendus entre le Nord et l'Aisne, mais la localisation exacte des fortes pluies reste incertaine.



#### [W1_ZONES_JSON_START]
```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance de nuages et d'éclaircies, dégradation orageuse mercredi et jeudi. Amélioration samedi soir.",
      "temperatures": "Maximales : 25-26°C mardi, 27-28°C mercredi, 26-28°C jeudi, 21-22°C vendredi, 22-24°C samedi. Minimales : 15-18°C.",
      "rain_storms": "Averses mardi soir (Avesnois). Orages possibles mercredi en fin de nuit et jeudi matin. Pluie max : 15 mm jeudi.",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnes-sur-Helpe",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi. Vent assez fort lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Localisation des fortes pluies jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages et éclaircies, dégradation orageuse mercredi soir et jeudi. Amélioration samedi.",
      "temperatures": "Maximales : 24-26°C mardi, 26-28°C mercredi, 24-27°C jeudi, 20-23°C vendredi, 21-24°C samedi. Minimales : 15-16°C.",
      "rain_storms": "Gouttes possibles près des côtes mercredi matin. Averses orageuses mercredi nuit. Pluie max : 15 mm sur le Ternois.",
      "spatial_scope": "regional",
      "location": "Arras, Calais, Boulogne-sur-Mer, Lens, Montreuil",
      "wind": "Est puis Sud-Ouest modéré. Rafales jusqu'à 55 km/h vendredi. Vent assez fort sur le littoral lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Comportement des orages près des côtes de la Manche",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages isolés. Très nuageux mercredi et jeudi avec averses. Amélioration samedi.",
      "temperatures": "Maximales : 24-27°C mardi, 27-29°C mercredi, 23-26°C jeudi, 20-22°C vendredi, 22°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi après-midi. Pluie max : 15 mm sur le Vermandois jeudi.",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Cayeux-sur-Mer, Péronne",
      "wind": "Est puis Ouest-Sud-Ouest modéré. Vent assez fort sur le littoral vendredi et lundi.",
      "sensitive_period": "Mardi 25 après-midi, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Déclenchement des orages mardi après-midi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux avec orages possibles mardi soir. Temps ensoleillé mercredi matin puis voile nuageux. Orages jeudi.",
      "temperatures": "Maximales : 27-28°C mardi, 27-29°C mercredi, 25-27°C jeudi, 21-23°C vendredi, 22°C samedi. Minimales : 13-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi fin de journée et mercredi en 2e partie de nuit. Pluie max : 10 mm.",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil",
      "wind": "Faible puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en fin de journée, mercredi 26 nuit et jeudi 27",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages mercredi soir",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Soleil mardi matin puis orages isolés. Temps lumineux mercredi. Orages jeudi en fin de journée. Amélioration samedi.",
      "temperatures": "Maximales : 26-28°C mardi, 27-30°C mercredi, 26-27°C jeudi, 21-23°C vendredi, 22-24°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi soir. Pluie max : 20 mm sur la Thiérache jeudi.",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en soirée, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Cumuls de pluie sur la Thiérache jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```
#### [W1_ZONES_JSON_END]



#### [W1_SOLID_POINTS]
**Points solides pour la semaine 1 :**
1.  **Chaleur lourde** :Mardi et mercredi seront encore chauds et humides, avec des maximales dépassant localement les 28°C.
2.  **Dégradation orageuse** : Un épisode orageux est quasi-certain entre mercredi et jeudi, avec un risque de grêle et de fortes rafales.
3.  **Rafraîchissement net** : Dès vendredi, les températures chutent pour revenir sous les normales de saison.



#### [W1_FRAGILE_POINTS]
**Points fragiles pour la semaine 1 :**
1.  **Localisation des orages** : L'endroit exact où les orages seront les plus violents reste incertain.
2.  **Cumuls de précipitations** : Les quantités de pluie pourraient varier significativement d'un endroit à l'autre, avec un risque de "taches de léopard".



#### [W1_NEXT_RUNS_TO_WATCH]
**Prochains runs à surveiller :**
*   **Run Arpège de ce soir (18Z)** : Pour affiner la menace orageuse de mercredi.
*   **Run CEP de cette nuit** : Pour fiabiliser le scénario de dégradation de jeudi.



#### [W1_PHASE_1_DATES]
**Phase 1 : Mardi 25 & Mercredi 26 Août**

#### [W1_PHASE_1]
**Chaleur lourde et humide avec développement d'orages isolés.**

#### [W1_PHASE_2_DATES]
**Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**



#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]



###
3. **Forte baisse thermique :** Net rafraîchissement dès vendredi, avec des maximales ne dépassant plus 22-23°C.

#### [W1_KEY_POINT_4]
**Vigilance jaune :** Les départements de la Somme, de l'Oise et de l'Aisne sont en vigilance jaune pour orages ce mardi.

#### [W1_KEY_POINT_5]
**Fin de semaine contrastée :** Temps encore instable samedi, mais nette amélioration attendue pour dimanche avec un ciel plus ensoleillé.



#### [W1_MODEL_START]

##### [W1_MODEL_NAME]
**Analyse des modèles (Synthèse) :**

##### [W1_MODEL_SCENARIO]
**(1) CEP (ECMWF)** : Scénario privilégié. Talweg d'altitude s'approchant par l'ouest, déclenchant une activité orageuse mercredi et jeudi. Dépression secondaire sur le proche Atlantique vendredi, apportant un flux de Sud-Ouest maritime plus frais et humide. Amélioration progressive samedi par l'ouest.

##### [W1_MODEL_SENSIBLE_WEATHER]
**Risque principal** : Orages potentiellement forts mercredi après-midi et jeudi, avec un risque de grêle et de rafales de vent. **Risque secondaire** : Cumuls de pluie localement importants (15 à 20 mm).

##### [W1_MODEL_AFFECTED_ZONES]
**Mercredi** : Toute la région, risque plus marqué sur l'intérieur des terres (Oise, Aisne, Somme). **Jeudi** : Toute la région, avec un risque de pluies plus soutenues sur le Nord et le Pas-de-Calais.

##### [W1_MODEL_EXTRACTION_CONF]
**Élevée (80%)** : Fort consensus sur la séquence "chaleur lourde puis dégradation orageuse puis rafraîchissement".

##### [W1_MODEL_SCENARIO_SUPPORT]
**Détail des runs** : GFS, UKMO et Arpège sont alignés sur cette évolution. Les différences portent sur le timing et l'intensité des orages, notamment jeudi.

##### [W1_MODEL_STATUS]
**Confirmé**

##### [W1_MODEL_MENTIONS_COUNT]
**5** (Sources : Bulletins Météo-France, discussions Infoclimat)

##### [W1_MODEL_RUN]
**25/08/2026 06Z**

##### [W1_MODEL_TIMING]
**Échéance : J+0 à J+5**

##### [W1_MODEL_DETAILS]**
**Évolution heure par heure** : Amélioration nette samedi soir, avec des éclaircies de plus en plus franches et un vent de Sud-Ouest encore modéré.

##### [W1_MODEL_END]



#### [W1_CONVERGENCES]
**Points de convergence entre modèles :**
1.  **Dégradation orageuse** : Tous les modèles s'accordent sur une dégradation orageuse entre mercredi et jeudi.
2.  **Rafraîchissement** : Consensus sur une nette baisse des températures à partir de vendredi.
3.  **Accalmie** : Tendance commune vers une amélioration du temps pour la journée de dimanche.



#### [W1_DIVERGENCES]
**Points de divergence entre modèles :**
1.  **Intensité des orages** : Incertitude sur la violence des orages de jeudi. Le scénario le plus défavorable (grêle et rafales destructrices) reste conditionnel à l'évolution du talweg.
2.  **Cumuls de pluie** : Les cumuls les plus importants sont attendus entre le Nord et l'Aisne, mais la localisation exacte des fortes pluies reste incertaine.



#### [W1_ZONES_JSON_START]
```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance de nuages et d'éclaircies, dégradation orageuse mercredi et jeudi. Amélioration samedi soir.",
      "temperatures": "Maximales : 25-26°C mardi, 27-28°C mercredi, 26-28°C jeudi, 21-22°C vendredi, 22-24°C samedi. Minimales : 15-18°C.",
      "rain_storms": "Averses mardi soir (Avesnois). Orages possibles mercredi en fin de nuit et jeudi matin. Pluie max : 15 mm jeudi.",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnes-sur-Helpe",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi. Vent assez fort lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Localisation des fortes pluies jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages et éclaircies, dégradation orageuse mercredi soir et jeudi. Amélioration samedi.",
      "temperatures": "Maximales : 24-26°C mardi, 26-28°C mercredi, 24-27°C jeudi, 20-23°C vendredi, 21-24°C samedi. Minimales : 15-16°C.",
      "rain_storms": "Gouttes possibles près des côtes mercredi matin. Averses orageuses mercredi nuit. Pluie max : 15 mm sur le Ternois.",
      "spatial_scope": "regional",
      "location": "Arras, Calais, Boulogne-sur-Mer, Lens, Montreuil",
      "wind": "Est puis Sud-Ouest modéré. Rafales jusqu'à 55 km/h vendredi. Vent assez fort sur le littoral lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Comportement des orages près des côtes de la Manche",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages isolés. Très nuageux mercredi et jeudi avec averses. Amélioration samedi.",
      "temperatures": "Maximales : 24-27°C mardi, 27-29°C mercredi, 23-26°C jeudi, 20-22°C vendredi, 22°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi après-midi. Pluie max : 15 mm sur le Vermandois jeudi.",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Cayeux-sur-Mer, Péronne",
      "wind": "Est puis Ouest-Sud-Ouest modéré. Vent assez fort sur le littoral vendredi et lundi.",
      "sensitive_period": "Mardi 25 après-midi, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Déclenchement des orages mardi après-midi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux avec orages possibles mardi soir. Temps ensoleillé mercredi matin puis voile nuageux. Orages jeudi.",
      "temperatures": "Maximales : 27-28°C mardi, 27-29°C mercredi, 25-27°C jeudi, 21-23°C vendredi, 22°C samedi. Minimales : 13-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi fin de journée et mercredi en 2e partie de nuit. Pluie max : 10 mm.",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil",
      "wind": "Faible puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en fin de journée, mercredi 26 nuit et jeudi 27",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages mercredi soir",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Soleil mardi matin puis orages isolés. Temps lumineux mercredi. Orages jeudi en fin de journée. Amélioration samedi.",
      "temperatures": "Maximales : 26-28°C mardi, 27-30°C mercredi, 26-27°C jeudi, 21-23°C vendredi, 22-24°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi soir. Pluie max : 20 mm sur la Thiérache jeudi.",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en soirée, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Cumuls de pluie sur la Thiérache jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```
#### [W1_ZONES_JSON_END]



#### [W1_SOLID_POINTS]
**Points solides pour la semaine 1 :**
1.  **Chaleur lourde** :Mardi et mercredi seront encore chauds et humides, avec des maximales dépassant localement les 28°C.
2.  **Dégradation orageuse** : Un épisode orageux est quasi-certain entre mercredi et jeudi, avec un risque de grêle et de fortes rafales.
3.  **Rafraîchissement net** : Dès vendredi, les températures chutent pour revenir sous les normales de saison.



#### [W1_FRAGILE_POINTS]
**Points fragiles pour la semaine 1 :**
1.  **Localisation des orages** : L'endroit exact où les orages seront les plus violents reste incertain.
2.  **Cumuls de précipitations** : Les quantités de pluie pourraient varier significativement d'un endroit à l'autre, avec un risque de "taches de léopard".



#### [W1_NEXT_RUNS_TO_WATCH]
**Prochains runs à surveiller :**
*   **Run Arpège de ce soir (18Z)** : Pour affiner la menace orageuse de mercredi.
*   **Run CEP de cette nuit** : Pour fiabiliser le scénario de dégradation de jeudi.



#### [W1_PHASE_1_DATES]
**Phase 1 : Mardi 25 & Mercredi 26 Août**

#### [W1_PHASE_1]
**Chaleur lourde et humide avec développement d'orages isolés.**

#### [W1_PHASE_2_DATES]
**Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**



#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]



###
4. **Vigilance jaune :** Les départements de la Somme, de l'Oise et de l'Aisne sont en vigilance jaune pour orages ce mardi.

#### [W1_KEY_POINT_5]
**Fin de semaine contrastée :** Temps encore instable samedi, mais nette amélioration attendue pour dimanche avec un ciel plus ensoleillé.



#### [W1_MODEL_START]

##### [W1_MODEL_NAME]
**Analyse des modèles (Synthèse) :**

##### [W1_MODEL_SCENARIO]
**(1) CEP (ECMWF)** : Scénario privilégié. Talweg d'altitude s'approchant par l'ouest, déclenchant une activité orageuse mercredi et jeudi. Dépression secondaire sur le proche Atlantique vendredi, apportant un flux de Sud-Ouest maritime plus frais et humide. Amélioration progressive samedi par l'ouest.

##### [W1_MODEL_SENSIBLE_WEATHER]
**Risque principal** : Orages potentiellement forts mercredi après-midi et jeudi, avec un risque de grêle et de rafales de vent. **Risque secondaire** : Cumuls de pluie localement importants (15 à 20 mm).

##### [W1_MODEL_AFFECTED_ZONES]
**Mercredi** : Toute la région, risque plus marqué sur l'intérieur des terres (Oise, Aisne, Somme). **Jeudi** : Toute la région, avec un risque de pluies plus soutenues sur le Nord et le Pas-de-Calais.

##### [W1_MODEL_EXTRACTION_CONF]
**Élevée (80%)** : Fort consensus sur la séquence "chaleur lourde puis dégradation orageuse puis rafraîchissement".

##### [W1_MODEL_SCENARIO_SUPPORT]
**Détail des runs** : GFS, UKMO et Arpège sont alignés sur cette évolution. Les différences portent sur le timing et l'intensité des orages, notamment jeudi.

##### [W1_MODEL_STATUS]
**Confirmé**

##### [W1_MODEL_MENTIONS_COUNT]
**5** (Sources : Bulletins Météo-France, discussions Infoclimat)

##### [W1_MODEL_RUN]
**25/08/2026 06Z**

##### [W1_MODEL_TIMING]
**Échéance : J+0 à J+5**

##### [W1_MODEL_DETAILS]**
**Évolution heure par heure** : Amélioration nette samedi soir, avec des éclaircies de plus en plus franches et un vent de Sud-Ouest encore modéré.

##### [W1_MODEL_END]



#### [W1_CONVERGENCES]
**Points de convergence entre modèles :**
1.  **Dégradation orageuse** : Tous les modèles s'accordent sur une dégradation orageuse entre mercredi et jeudi.
2.  **Rafraîchissement** : Consensus sur une nette baisse des températures à partir de vendredi.
3.  **Accalmie** : Tendance commune vers une amélioration du temps pour la journée de dimanche.



#### [W1_DIVERGENCES]
**Points de divergence entre modèles :**
1.  **Intensité des orages** : Incertitude sur la violence des orages de jeudi. Le scénario le plus défavorable (grêle et rafales destructrices) reste conditionnel à l'évolution du talweg.
2.  **Cumuls de pluie** : Les cumuls les plus importants sont attendus entre le Nord et l'Aisne, mais la localisation exacte des fortes pluies reste incertaine.



#### [W1_ZONES_JSON_START]
```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance de nuages et d'éclaircies, dégradation orageuse mercredi et jeudi. Amélioration samedi soir.",
      "temperatures": "Maximales : 25-26°C mardi, 27-28°C mercredi, 26-28°C jeudi, 21-22°C vendredi, 22-24°C samedi. Minimales : 15-18°C.",
      "rain_storms": "Averses mardi soir (Avesnois). Orages possibles mercredi en fin de nuit et jeudi matin. Pluie max : 15 mm jeudi.",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnes-sur-Helpe",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi. Vent assez fort lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Localisation des fortes pluies jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages et éclaircies, dégradation orageuse mercredi soir et jeudi. Amélioration samedi.",
      "temperatures": "Maximales : 24-26°C mardi, 26-28°C mercredi, 24-27°C jeudi, 20-23°C vendredi, 21-24°C samedi. Minimales : 15-16°C.",
      "rain_storms": "Gouttes possibles près des côtes mercredi matin. Averses orageuses mercredi nuit. Pluie max : 15 mm sur le Ternois.",
      "spatial_scope": "regional",
      "location": "Arras, Calais, Boulogne-sur-Mer, Lens, Montreuil",
      "wind": "Est puis Sud-Ouest modéré. Rafales jusqu'à 55 km/h vendredi. Vent assez fort sur le littoral lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Comportement des orages près des côtes de la Manche",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages isolés. Très nuageux mercredi et jeudi avec averses. Amélioration samedi.",
      "temperatures": "Maximales : 24-27°C mardi, 27-29°C mercredi, 23-26°C jeudi, 20-22°C vendredi, 22°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi après-midi. Pluie max : 15 mm sur le Vermandois jeudi.",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Cayeux-sur-Mer, Péronne",
      "wind": "Est puis Ouest-Sud-Ouest modéré. Vent assez fort sur le littoral vendredi et lundi.",
      "sensitive_period": "Mardi 25 après-midi, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Déclenchement des orages mardi après-midi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux avec orages possibles mardi soir. Temps ensoleillé mercredi matin puis voile nuageux. Orages jeudi.",
      "temperatures": "Maximales : 27-28°C mardi, 27-29°C mercredi, 25-27°C jeudi, 21-23°C vendredi, 22°C samedi. Minimales : 13-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi fin de journée et mercredi en 2e partie de nuit. Pluie max : 10 mm.",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil",
      "wind": "Faible puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en fin de journée, mercredi 26 nuit et jeudi 27",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages mercredi soir",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Soleil mardi matin puis orages isolés. Temps lumineux mercredi. Orages jeudi en fin de journée. Amélioration samedi.",
      "temperatures": "Maximales : 26-28°C mardi, 27-30°C mercredi, 26-27°C jeudi, 21-23°C vendredi, 22-24°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi soir. Pluie max : 20 mm sur la Thiérache jeudi.",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en soirée, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Cumuls de pluie sur la Thiérache jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```
#### [W1_ZONES_JSON_END]



#### [W1_SOLID_POINTS]
**Points solides pour la semaine 1 :**
1.  **Chaleur lourde** :Mardi et mercredi seront encore chauds et humides, avec des maximales dépassant localement les 28°C.
2.  **Dégradation orageuse** : Un épisode orageux est quasi-certain entre mercredi et jeudi, avec un risque de grêle et de fortes rafales.
3.  **Rafraîchissement net** : Dès vendredi, les températures chutent pour revenir sous les normales de saison.



#### [W1_FRAGILE_POINTS]
**Points fragiles pour la semaine 1 :**
1.  **Localisation des orages** : L'endroit exact où les orages seront les plus violents reste incertain.
2.  **Cumuls de précipitations** : Les quantités de pluie pourraient varier significativement d'un endroit à l'autre, avec un risque de "taches de léopard".



#### [W1_NEXT_RUNS_TO_WATCH]
**Prochains runs à surveiller :**
*   **Run Arpège de ce soir (18Z)** : Pour affiner la menace orageuse de mercredi.
*   **Run CEP de cette nuit** : Pour fiabiliser le scénario de dégradation de jeudi.



#### [W1_PHASE_1_DATES]
**Phase 1 : Mardi 25 & Mercredi 26 Août**

#### [W1_PHASE_1]
**Chaleur lourde et humide avec développement d'orages isolés.**

#### [W1_PHASE_2_DATES]
**Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**



#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]



###
5. **Fin de semaine contrastée :** Temps encore instable samedi, mais nette amélioration attendue pour dimanche avec un ciel plus ensoleillé.



#### [W1_MODEL_START]

##### [W1_MODEL_NAME]
**Analyse des modèles (Synthèse) :**

##### [W1_MODEL_SCENARIO]
**(1) CEP (ECMWF)** : Scénario privilégié. Talweg d'altitude s'approchant par l'ouest, déclenchant une activité orageuse mercredi et jeudi. Dépression secondaire sur le proche Atlantique vendredi, apportant un flux de Sud-Ouest maritime plus frais et humide. Amélioration progressive samedi par l'ouest.

##### [W1_MODEL_SENSIBLE_WEATHER]
**Risque principal** : Orages potentiellement forts mercredi après-midi et jeudi, avec un risque de grêle et de rafales de vent. **Risque secondaire** : Cumuls de pluie localement importants (15 à 20 mm).

##### [W1_MODEL_AFFECTED_ZONES]
**Mercredi** : Toute la région, risque plus marqué sur l'intérieur des terres (Oise, Aisne, Somme). **Jeudi** : Toute la région, avec un risque de pluies plus soutenues sur le Nord et le Pas-de-Calais.

##### [W1_MODEL_EXTRACTION_CONF]
**Élevée (80%)** : Fort consensus sur la séquence "chaleur lourde puis dégradation orageuse puis rafraîchissement".

##### [W1_MODEL_SCENARIO_SUPPORT]
**Détail des runs** : GFS, UKMO et Arpège sont alignés sur cette évolution. Les différences portent sur le timing et l'intensité des orages, notamment jeudi.

##### [W1_MODEL_STATUS]
**Confirmé**

##### [W1_MODEL_MENTIONS_COUNT]
**5** (Sources : Bulletins Météo-France, discussions Infoclimat)

##### [W1_MODEL_RUN]
**25/08/2026 06Z**

##### [W1_MODEL_TIMING]
**Échéance : J+0 à J+5**

##### [W1_MODEL_DETAILS]**
**Évolution heure par heure** : Amélioration nette samedi soir, avec des éclaircies de plus en plus franches et un vent de Sud-Ouest encore modéré.

##### [W1_MODEL_END]



#### [W1_CONVERGENCES]
**Points de convergence entre modèles :**
1.  **Dégradation orageuse** : Tous les modèles s'accordent sur une dégradation orageuse entre mercredi et jeudi.
2.  **Rafraîchissement** : Consensus sur une nette baisse des températures à partir de vendredi.
3.  **Accalmie** : Tendance commune vers une amélioration du temps pour la journée de dimanche.



#### [W1_DIVERGENCES]
**Points de divergence entre modèles :**
1.  **Intensité des orages** : Incertitude sur la violence des orages de jeudi. Le scénario le plus défavorable (grêle et rafales destructrices) reste conditionnel à l'évolution du talweg.
2.  **Cumuls de pluie** : Les cumuls les plus importants sont attendus entre le Nord et l'Aisne, mais la localisation exacte des fortes pluies reste incertaine.



#### [W1_ZONES_JSON_START]
```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance de nuages et d'éclaircies, dégradation orageuse mercredi et jeudi. Amélioration samedi soir.",
      "temperatures": "Maximales : 25-26°C mardi, 27-28°C mercredi, 26-28°C jeudi, 21-22°C vendredi, 22-24°C samedi. Minimales : 15-18°C.",
      "rain_storms": "Averses mardi soir (Avesnois). Orages possibles mercredi en fin de nuit et jeudi matin. Pluie max : 15 mm jeudi.",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnes-sur-Helpe",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi. Vent assez fort lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Localisation des fortes pluies jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages et éclaircies, dégradation orageuse mercredi soir et jeudi. Amélioration samedi.",
      "temperatures": "Maximales : 24-26°C mardi, 26-28°C mercredi, 24-27°C jeudi, 20-23°C vendredi, 21-24°C samedi. Minimales : 15-16°C.",
      "rain_storms": "Gouttes possibles près des côtes mercredi matin. Averses orageuses mercredi nuit. Pluie max : 15 mm sur le Ternois.",
      "spatial_scope": "regional",
      "location": "Arras, Calais, Boulogne-sur-Mer, Lens, Montreuil",
      "wind": "Est puis Sud-Ouest modéré. Rafales jusqu'à 55 km/h vendredi. Vent assez fort sur le littoral lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Comportement des orages près des côtes de la Manche",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages isolés. Très nuageux mercredi et jeudi avec averses. Amélioration samedi.",
      "temperatures": "Maximales : 24-27°C mardi, 27-29°C mercredi, 23-26°C jeudi, 20-22°C vendredi, 22°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi après-midi. Pluie max : 15 mm sur le Vermandois jeudi.",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Cayeux-sur-Mer, Péronne",
      "wind": "Est puis Ouest-Sud-Ouest modéré. Vent assez fort sur le littoral vendredi et lundi.",
      "sensitive_period": "Mardi 25 après-midi, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Déclenchement des orages mardi après-midi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux avec orages possibles mardi soir. Temps ensoleillé mercredi matin puis voile nuageux. Orages jeudi.",
      "temperatures": "Maximales : 27-28°C mardi, 27-29°C mercredi, 25-27°C jeudi, 21-23°C vendredi, 22°C samedi. Minimales : 13-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi fin de journée et mercredi en 2e partie de nuit. Pluie max : 10 mm.",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil",
      "wind": "Faible puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en fin de journée, mercredi 26 nuit et jeudi 27",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages mercredi soir",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Soleil mardi matin puis orages isolés. Temps lumineux mercredi. Orages jeudi en fin de journée. Amélioration samedi.",
      "temperatures": "Maximales : 26-28°C mardi, 27-30°C mercredi, 26-27°C jeudi, 21-23°C vendredi, 22-24°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi soir. Pluie max : 20 mm sur la Thiérache jeudi.",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en soirée, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Cumuls de pluie sur la Thiérache jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```
#### [W1_ZONES_JSON_END]



#### [W1_SOLID_POINTS]
**Points solides pour la semaine 1 :**
1.  **Chaleur lourde** :Mardi et mercredi seront encore chauds et humides, avec des maximales dépassant localement les 28°C.
2.  **Dégradation orageuse** : Un épisode orageux est quasi-certain entre mercredi et jeudi, avec un risque de grêle et de fortes rafales.
3.  **Rafraîchissement net** : Dès vendredi, les températures chutent pour revenir sous les normales de saison.



#### [W1_FRAGILE_POINTS]
**Points fragiles pour la semaine 1 :**
1.  **Localisation des orages** : L'endroit exact où les orages seront les plus violents reste incertain.
2.  **Cumuls de précipitations** : Les quantités de pluie pourraient varier significativement d'un endroit à l'autre, avec un risque de "taches de léopard".



#### [W1_NEXT_RUNS_TO_WATCH]
**Prochains runs à surveiller :**
*   **Run Arpège de ce soir (18Z)** : Pour affiner la menace orageuse de mercredi.
*   **Run CEP de cette nuit** : Pour fiabiliser le scénario de dégradation de jeudi.



#### [W1_PHASE_1_DATES]
**Phase 1 : Mardi 25 & Mercredi 26 Août**

#### [W1_PHASE_1]
**Chaleur lourde et humide avec développement d'orages isolés.**

#### [W1_PHASE_2_DATES]
**Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**



#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]



###

### 🤝 Modèles et scénarios (Semaine 1)
**Points de convergence :**
**Points de convergence entre modèles :**
1.  **Dégradation orageuse** : Tous les modèles s'accordent sur une dégradation orageuse entre mercredi et jeudi.
2.  **Rafraîchissement** : Consensus sur une nette baisse des températures à partir de vendredi.
3.  **Accalmie** : Tendance commune vers une amélioration du temps pour la journée de dimanche.



#### [W1_DIVERGENCES]
**Points de divergence entre modèles :**
1.  **Intensité des orages** : Incertitude sur la violence des orages de jeudi. Le scénario le plus défavorable (grêle et rafales destructrices) reste conditionnel à l'évolution du talweg.
2.  **Cumuls de pluie** : Les cumuls les plus importants sont attendus entre le Nord et l'Aisne, mais la localisation exacte des fortes pluies reste incertaine.



#### [W1_ZONES_JSON_START]
```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance de nuages et d'éclaircies, dégradation orageuse mercredi et jeudi. Amélioration samedi soir.",
      "temperatures": "Maximales : 25-26°C mardi, 27-28°C mercredi, 26-28°C jeudi, 21-22°C vendredi, 22-24°C samedi. Minimales : 15-18°C.",
      "rain_storms": "Averses mardi soir (Avesnois). Orages possibles mercredi en fin de nuit et jeudi matin. Pluie max : 15 mm jeudi.",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnes-sur-Helpe",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi. Vent assez fort lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Localisation des fortes pluies jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages et éclaircies, dégradation orageuse mercredi soir et jeudi. Amélioration samedi.",
      "temperatures": "Maximales : 24-26°C mardi, 26-28°C mercredi, 24-27°C jeudi, 20-23°C vendredi, 21-24°C samedi. Minimales : 15-16°C.",
      "rain_storms": "Gouttes possibles près des côtes mercredi matin. Averses orageuses mercredi nuit. Pluie max : 15 mm sur le Ternois.",
      "spatial_scope": "regional",
      "location": "Arras, Calais, Boulogne-sur-Mer, Lens, Montreuil",
      "wind": "Est puis Sud-Ouest modéré. Rafales jusqu'à 55 km/h vendredi. Vent assez fort sur le littoral lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Comportement des orages près des côtes de la Manche",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages isolés. Très nuageux mercredi et jeudi avec averses. Amélioration samedi.",
      "temperatures": "Maximales : 24-27°C mardi, 27-29°C mercredi, 23-26°C jeudi, 20-22°C vendredi, 22°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi après-midi. Pluie max : 15 mm sur le Vermandois jeudi.",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Cayeux-sur-Mer, Péronne",
      "wind": "Est puis Ouest-Sud-Ouest modéré. Vent assez fort sur le littoral vendredi et lundi.",
      "sensitive_period": "Mardi 25 après-midi, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Déclenchement des orages mardi après-midi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux avec orages possibles mardi soir. Temps ensoleillé mercredi matin puis voile nuageux. Orages jeudi.",
      "temperatures": "Maximales : 27-28°C mardi, 27-29°C mercredi, 25-27°C jeudi, 21-23°C vendredi, 22°C samedi. Minimales : 13-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi fin de journée et mercredi en 2e partie de nuit. Pluie max : 10 mm.",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil",
      "wind": "Faible puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en fin de journée, mercredi 26 nuit et jeudi 27",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages mercredi soir",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Soleil mardi matin puis orages isolés. Temps lumineux mercredi. Orages jeudi en fin de journée. Amélioration samedi.",
      "temperatures": "Maximales : 26-28°C mardi, 27-30°C mercredi, 26-27°C jeudi, 21-23°C vendredi, 22-24°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi soir. Pluie max : 20 mm sur la Thiérache jeudi.",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en soirée, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Cumuls de pluie sur la Thiérache jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```
#### [W1_ZONES_JSON_END]



#### [W1_SOLID_POINTS]
**Points solides pour la semaine 1 :**
1.  **Chaleur lourde** :Mardi et mercredi seront encore chauds et humides, avec des maximales dépassant localement les 28°C.
2.  **Dégradation orageuse** : Un épisode orageux est quasi-certain entre mercredi et jeudi, avec un risque de grêle et de fortes rafales.
3.  **Rafraîchissement net** : Dès vendredi, les températures chutent pour revenir sous les normales de saison.



#### [W1_FRAGILE_POINTS]
**Points fragiles pour la semaine 1 :**
1.  **Localisation des orages** : L'endroit exact où les orages seront les plus violents reste incertain.
2.  **Cumuls de précipitations** : Les quantités de pluie pourraient varier significativement d'un endroit à l'autre, avec un risque de "taches de léopard".



#### [W1_NEXT_RUNS_TO_WATCH]
**Prochains runs à surveiller :**
*   **Run Arpège de ce soir (18Z)** : Pour affiner la menace orageuse de mercredi.
*   **Run CEP de cette nuit** : Pour fiabiliser le scénario de dégradation de jeudi.



#### [W1_PHASE_1_DATES]
**Phase 1 : Mardi 25 & Mercredi 26 Août**

#### [W1_PHASE_1]
**Chaleur lourde et humide avec développement d'orages isolés.**

#### [W1_PHASE_2_DATES]
**Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**



#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]



###
**Points de divergence :**
**Points de divergence entre modèles :**
1.  **Intensité des orages** : Incertitude sur la violence des orages de jeudi. Le scénario le plus défavorable (grêle et rafales destructrices) reste conditionnel à l'évolution du talweg.
2.  **Cumuls de pluie** : Les cumuls les plus importants sont attendus entre le Nord et l'Aisne, mais la localisation exacte des fortes pluies reste incertaine.



#### [W1_ZONES_JSON_START]
```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance de nuages et d'éclaircies, dégradation orageuse mercredi et jeudi. Amélioration samedi soir.",
      "temperatures": "Maximales : 25-26°C mardi, 27-28°C mercredi, 26-28°C jeudi, 21-22°C vendredi, 22-24°C samedi. Minimales : 15-18°C.",
      "rain_storms": "Averses mardi soir (Avesnois). Orages possibles mercredi en fin de nuit et jeudi matin. Pluie max : 15 mm jeudi.",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnes-sur-Helpe",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi. Vent assez fort lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Localisation des fortes pluies jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages et éclaircies, dégradation orageuse mercredi soir et jeudi. Amélioration samedi.",
      "temperatures": "Maximales : 24-26°C mardi, 26-28°C mercredi, 24-27°C jeudi, 20-23°C vendredi, 21-24°C samedi. Minimales : 15-16°C.",
      "rain_storms": "Gouttes possibles près des côtes mercredi matin. Averses orageuses mercredi nuit. Pluie max : 15 mm sur le Ternois.",
      "spatial_scope": "regional",
      "location": "Arras, Calais, Boulogne-sur-Mer, Lens, Montreuil",
      "wind": "Est puis Sud-Ouest modéré. Rafales jusqu'à 55 km/h vendredi. Vent assez fort sur le littoral lundi.",
      "sensitive_period": "Jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Comportement des orages près des côtes de la Manche",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages isolés. Très nuageux mercredi et jeudi avec averses. Amélioration samedi.",
      "temperatures": "Maximales : 24-27°C mardi, 27-29°C mercredi, 23-26°C jeudi, 20-22°C vendredi, 22°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi après-midi. Pluie max : 15 mm sur le Vermandois jeudi.",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Cayeux-sur-Mer, Péronne",
      "wind": "Est puis Ouest-Sud-Ouest modéré. Vent assez fort sur le littoral vendredi et lundi.",
      "sensitive_period": "Mardi 25 après-midi, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Déclenchement des orages mardi après-midi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux avec orages possibles mardi soir. Temps ensoleillé mercredi matin puis voile nuageux. Orages jeudi.",
      "temperatures": "Maximales : 27-28°C mardi, 27-29°C mercredi, 25-27°C jeudi, 21-23°C vendredi, 22°C samedi. Minimales : 13-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi fin de journée et mercredi en 2e partie de nuit. Pluie max : 10 mm.",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil",
      "wind": "Faible puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en fin de journée, mercredi 26 nuit et jeudi 27",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages mercredi soir",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Soleil mardi matin puis orages isolés. Temps lumineux mercredi. Orages jeudi en fin de journée. Amélioration samedi.",
      "temperatures": "Maximales : 26-28°C mardi, 27-30°C mercredi, 26-27°C jeudi, 21-23°C vendredi, 22-24°C samedi. Minimales : 14-16°C.",
      "rain_storms": "Vigilance jaune orages mardi. Orages possibles mardi soir. Pluie max : 20 mm sur la Thiérache jeudi.",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry",
      "wind": "Est puis Sud-Ouest modéré. Rafales possibles jusqu'à 55 km/h vendredi.",
      "sensitive_period": "Mardi 25 en soirée, jeudi 27 et vendredi 28 août",
      "confidence_level": "elevee",
      "uncertainty": "Cumuls de pluie sur la Thiérache jeudi",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```
#### [W1_ZONES_JSON_END]



#### [W1_SOLID_POINTS]
**Points solides pour la semaine 1 :**
1.  **Chaleur lourde** :Mardi et mercredi seront encore chauds et humides, avec des maximales dépassant localement les 28°C.
2.  **Dégradation orageuse** : Un épisode orageux est quasi-certain entre mercredi et jeudi, avec un risque de grêle et de fortes rafales.
3.  **Rafraîchissement net** : Dès vendredi, les températures chutent pour revenir sous les normales de saison.



#### [W1_FRAGILE_POINTS]
**Points fragiles pour la semaine 1 :**
1.  **Localisation des orages** : L'endroit exact où les orages seront les plus violents reste incertain.
2.  **Cumuls de précipitations** : Les quantités de pluie pourraient varier significativement d'un endroit à l'autre, avec un risque de "taches de léopard".



#### [W1_NEXT_RUNS_TO_WATCH]
**Prochains runs à surveiller :**
*   **Run Arpège de ce soir (18Z)** : Pour affiner la menace orageuse de mercredi.
*   **Run CEP de cette nuit** : Pour fiabiliser le scénario de dégradation de jeudi.



#### [W1_PHASE_1_DATES]
**Phase 1 : Mardi 25 & Mercredi 26 Août**

#### [W1_PHASE_1]
**Chaleur lourde et humide avec développement d'orages isolés.**

#### [W1_PHASE_2_DATES]
**Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**



#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]



###

### 🤖 Scénarios détaillés des modèles (Semaine 1)
| Modèle | Scénario | Temps sensible | Zones concernées | Confiance | Détails d'analyse |
| --- | --- | --- | --- | --- | --- |
| **<strong>Analyse des modèles (Synthèse) :</strong>

##### [W1_MODEL_SCENARIO]
<strong>(1) CEP (ECMWF)</strong> : Scénario privilégié. Talweg d'altitude s'approchant par l'ouest, déclenchant une activité orageuse mercredi et jeudi. Dépression secondaire sur le proche Atlantique vendredi, apportant un flux de Sud-Ouest maritime plus frais et humide. Amélioration progressive samedi par l'ouest.

##### [W1_MODEL_SENSIBLE_WEATHER]
<strong>Risque principal</strong> : Orages potentiellement forts mercredi après-midi et jeudi, avec un risque de grêle et de rafales de vent. <strong>Risque secondaire</strong> : Cumuls de pluie localement importants (15 à 20 mm).

##### [W1_MODEL_AFFECTED_ZONES]
<strong>Mercredi</strong> : Toute la région, risque plus marqué sur l'intérieur des terres (Oise, Aisne, Somme). <strong>Jeudi</strong> : Toute la région, avec un risque de pluies plus soutenues sur le Nord et le Pas-de-Calais.

##### [W1_MODEL_EXTRACTION_CONF]
<strong>Élevée (80%)</strong> : Fort consensus sur la séquence "chaleur lourde puis dégradation orageuse puis rafraîchissement".

##### [W1_MODEL_SCENARIO_SUPPORT]
<strong>Détail des runs</strong> : GFS, UKMO et Arpège sont alignés sur cette évolution. Les différences portent sur le timing et l'intensité des orages, notamment jeudi.

##### [W1_MODEL_STATUS]
<strong>Confirmé</strong>

##### [W1_MODEL_MENTIONS_COUNT]
<strong>5</strong> (Sources : Bulletins Météo-France, discussions Infoclimat)

##### [W1_MODEL_RUN]
<strong>25/08/2026 06Z</strong>

##### [W1_MODEL_TIMING]
<strong>Échéance : J+0 à J+5</strong>

##### [W1_MODEL_DETAILS]**
<strong>Évolution heure par heure</strong> : Amélioration nette samedi soir, avec des éclaircies de plus en plus franches et un vent de Sud-Ouest encore modéré.

#####** (**Confirmé**

##### [W1_MODEL_MENTIONS_COUNT]
**5** (Sources : Bulletins Météo-France, discussions Infoclimat)

##### [W1_MODEL_RUN]
**25/08/2026 06Z**

##### [W1_MODEL_TIMING]
**Échéance : J+0 à J+5**

##### [W1_MODEL_DETAILS]**
**Évolution heure par heure** : Amélioration nette samedi soir, avec des éclaircies de plus en plus franches et un vent de Sud-Ouest encore modéré.

#####) | <strong>(1) CEP (ECMWF)</strong> : Scénario privilégié. Talweg d'altitude s'approchant par l'ouest, déclenchant une activité orageuse mercredi et jeudi. Dépression secondaire sur le proche Atlantique vendredi, apportant un flux de Sud-Ouest maritime plus frais et humide. Amélioration progressive samedi par l'ouest.

##### [W1_MODEL_SENSIBLE_WEATHER]
<strong>Risque principal</strong> : Orages potentiellement forts mercredi après-midi et jeudi, avec un risque de grêle et de rafales de vent. <strong>Risque secondaire</strong> : Cumuls de pluie localement importants (15 à 20 mm).

##### [W1_MODEL_AFFECTED_ZONES]
<strong>Mercredi</strong> : Toute la région, risque plus marqué sur l'intérieur des terres (Oise, Aisne, Somme). <strong>Jeudi</strong> : Toute la région, avec un risque de pluies plus soutenues sur le Nord et le Pas-de-Calais.

##### [W1_MODEL_EXTRACTION_CONF]
<strong>Élevée (80%)</strong> : Fort consensus sur la séquence "chaleur lourde puis dégradation orageuse puis rafraîchissement".

##### [W1_MODEL_SCENARIO_SUPPORT]
<strong>Détail des runs</strong> : GFS, UKMO et Arpège sont alignés sur cette évolution. Les différences portent sur le timing et l'intensité des orages, notamment jeudi.

##### [W1_MODEL_STATUS]
<strong>Confirmé</strong>

##### [W1_MODEL_MENTIONS_COUNT]
<strong>5</strong> (Sources : Bulletins Météo-France, discussions Infoclimat)

##### [W1_MODEL_RUN]
<strong>25/08/2026 06Z</strong>

##### [W1_MODEL_TIMING]
<strong>Échéance : J+0 à J+5</strong>

##### [W1_MODEL_DETAILS]**
<strong>Évolution heure par heure</strong> : Amélioration nette samedi soir, avec des éclaircies de plus en plus franches et un vent de Sud-Ouest encore modéré.

##### | <strong>Risque principal</strong> : Orages potentiellement forts mercredi après-midi et jeudi, avec un risque de grêle et de rafales de vent. <strong>Risque secondaire</strong> : Cumuls de pluie localement importants (15 à 20 mm).

##### [W1_MODEL_AFFECTED_ZONES]
<strong>Mercredi</strong> : Toute la région, risque plus marqué sur l'intérieur des terres (Oise, Aisne, Somme). <strong>Jeudi</strong> : Toute la région, avec un risque de pluies plus soutenues sur le Nord et le Pas-de-Calais.

##### [W1_MODEL_EXTRACTION_CONF]
<strong>Élevée (80%)</strong> : Fort consensus sur la séquence "chaleur lourde puis dégradation orageuse puis rafraîchissement".

##### [W1_MODEL_SCENARIO_SUPPORT]
<strong>Détail des runs</strong> : GFS, UKMO et Arpège sont alignés sur cette évolution. Les différences portent sur le timing et l'intensité des orages, notamment jeudi.

##### [W1_MODEL_STATUS]
<strong>Confirmé</strong>

##### [W1_MODEL_MENTIONS_COUNT]
<strong>5</strong> (Sources : Bulletins Météo-France, discussions Infoclimat)

##### [W1_MODEL_RUN]
<strong>25/08/2026 06Z</strong>

##### [W1_MODEL_TIMING]
<strong>Échéance : J+0 à J+5</strong>

##### [W1_MODEL_DETAILS]**
<strong>Évolution heure par heure</strong> : Amélioration nette samedi soir, avec des éclaircies de plus en plus franches et un vent de Sud-Ouest encore modéré.

##### | <strong>Mercredi</strong> : Toute la région, risque plus marqué sur l'intérieur des terres (Oise, Aisne, Somme). <strong>Jeudi</strong> : Toute la région, avec un risque de pluies plus soutenues sur le Nord et le Pas-de-Calais.

##### [W1_MODEL_EXTRACTION_CONF]
<strong>Élevée (80%)</strong> : Fort consensus sur la séquence "chaleur lourde puis dégradation orageuse puis rafraîchissement".

##### [W1_MODEL_SCENARIO_SUPPORT]
<strong>Détail des runs</strong> : GFS, UKMO et Arpège sont alignés sur cette évolution. Les différences portent sur le timing et l'intensité des orages, notamment jeudi.

##### [W1_MODEL_STATUS]
<strong>Confirmé</strong>

##### [W1_MODEL_MENTIONS_COUNT]
<strong>5</strong> (Sources : Bulletins Météo-France, discussions Infoclimat)

##### [W1_MODEL_RUN]
<strong>25/08/2026 06Z</strong>

##### [W1_MODEL_TIMING]
<strong>Échéance : J+0 à J+5</strong>

##### [W1_MODEL_DETAILS]**
<strong>Évolution heure par heure</strong> : Amélioration nette samedi soir, avec des éclaircies de plus en plus franches et un vent de Sud-Ouest encore modéré.

##### | **Élevée (80%)** : Fort consensus sur la séquence "chaleur lourde puis dégradation orageuse puis rafraîchissement".

##### [W1_MODEL_SCENARIO_SUPPORT]
**Détail des runs** : GFS, UKMO et Arpège sont alignés sur cette évolution. Les différences portent sur le timing et l'intensité des orages, notamment jeudi.

##### [W1_MODEL_STATUS]
**Confirmé**

##### [W1_MODEL_MENTIONS_COUNT]
**5** (Sources : Bulletins Météo-France, discussions Infoclimat)

##### [W1_MODEL_RUN]
**25/08/2026 06Z**

##### [W1_MODEL_TIMING]
**Échéance : J+0 à J+5**

##### [W1_MODEL_DETAILS]**
**Évolution heure par heure** : Amélioration nette samedi soir, avec des éclaircies de plus en plus franches et un vent de Sud-Ouest encore modéré.

##### | ** <strong>Évolution heure par heure</strong> : Amélioration nette samedi soir, avec des éclaircies de plus en plus franches et un vent de Sud-Ouest encore modéré.  ##### |

### 📍 Synthèse par zones/départements (Semaine 1)
| Zone / Département | Temps sensible | Températures | Fiabilité | Modèles | Notes d'analyse |
| --- | --- | --- | --- | --- | --- |
| **Nord (59)** | Beau temps chaud | 26°C à 32°C | Élevée | Météo-France XML, ECMWF, GFS | Validé d'après bulletins XML Meteotel |
| **Pas-de-Calais (62)** | Beau temps chaud | 26°C à 32°C | Élevée | Météo-France XML, ECMWF, GFS | Validé d'après bulletins XML Meteotel |
| **Somme (80)** | Beau temps chaud | 26°C à 32°C | Élevée | Météo-France XML, ECMWF, GFS | Validé d'après bulletins XML Meteotel |
| **Oise (60)** | Beau temps chaud | 26°C à 32°C | Élevée | Météo-France XML, ECMWF, GFS | Validé d'après bulletins XML Meteotel |
| **Aisne (02)** | Beau temps chaud | 26°C à 32°C | Élevée | Météo-France XML, ECMWF, GFS | Validé d'après bulletins XML Meteotel |

### ⏳ Déroulé chronologique (Semaine 1)
- ****Phase 1 : Mardi 25 & Mercredi 26 Août**

#### [W1_PHASE_1]
**Chaleur lourde et humide avec développement d'orages isolés.**

#### [W1_PHASE_2_DATES]
**Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**

---

#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]

---

###** : **Chaleur lourde et humide avec développement d'orages isolés.**

#### [W1_PHASE_2_DATES]
**Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**



#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]



###
- ****Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**

---

#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]

---

###** : **Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**



#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]



###
- ****Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**

---

#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]

---

###** : **Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**



#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]



###
- ****Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**

---

#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]

---

###** : **Amélioration progressive avec retour d'éclaircies.**



#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]



###

**Points solides :**
**Points solides pour la semaine 1 :**
1.  **Chaleur lourde** :Mardi et mercredi seront encore chauds et humides, avec des maximales dépassant localement les 28°C.
2.  **Dégradation orageuse** : Un épisode orageux est quasi-certain entre mercredi et jeudi, avec un risque de grêle et de fortes rafales.
3.  **Rafraîchissement net** : Dès vendredi, les températures chutent pour revenir sous les normales de saison.



#### [W1_FRAGILE_POINTS]
**Points fragiles pour la semaine 1 :**
1.  **Localisation des orages** : L'endroit exact où les orages seront les plus violents reste incertain.
2.  **Cumuls de précipitations** : Les quantités de pluie pourraient varier significativement d'un endroit à l'autre, avec un risque de "taches de léopard".



#### [W1_NEXT_RUNS_TO_WATCH]
**Prochains runs à surveiller :**
*   **Run Arpège de ce soir (18Z)** : Pour affiner la menace orageuse de mercredi.
*   **Run CEP de cette nuit** : Pour fiabiliser le scénario de dégradation de jeudi.



#### [W1_PHASE_1_DATES]
**Phase 1 : Mardi 25 & Mercredi 26 Août**

#### [W1_PHASE_1]
**Chaleur lourde et humide avec développement d'orages isolés.**

#### [W1_PHASE_2_DATES]
**Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**



#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]



###

**Points fragiles :**
**Points fragiles pour la semaine 1 :**
1.  **Localisation des orages** : L'endroit exact où les orages seront les plus violents reste incertain.
2.  **Cumuls de précipitations** : Les quantités de pluie pourraient varier significativement d'un endroit à l'autre, avec un risque de "taches de léopard".



#### [W1_NEXT_RUNS_TO_WATCH]
**Prochains runs à surveiller :**
*   **Run Arpège de ce soir (18Z)** : Pour affiner la menace orageuse de mercredi.
*   **Run CEP de cette nuit** : Pour fiabiliser le scénario de dégradation de jeudi.



#### [W1_PHASE_1_DATES]
**Phase 1 : Mardi 25 & Mercredi 26 Août**

#### [W1_PHASE_1]
**Chaleur lourde et humide avec développement d'orages isolés.**

#### [W1_PHASE_2_DATES]
**Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**



#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]



###

**À surveiller (prochains runs) :**
**Prochains runs à surveiller :**
*   **Run Arpège de ce soir (18Z)** : Pour affiner la menace orageuse de mercredi.
*   **Run CEP de cette nuit** : Pour fiabiliser le scénario de dégradation de jeudi.



#### [W1_PHASE_1_DATES]
**Phase 1 : Mardi 25 & Mercredi 26 Août**

#### [W1_PHASE_1]
**Chaleur lourde et humide avec développement d'orages isolés.**

#### [W1_PHASE_2_DATES]
**Phase 2 : Jeudi 27 Août**

#### [W1_PHASE_2]
**Dégradation orageuse marquée, risque de phénomènes violents.**

#### [W1_PHASE_3_DATES]
**Phase 3 : Vendredi 28 & Samedi 29 Août**

#### [W1_PHASE_3]
**Temps plus frais et humide avec des averses résiduelles.**

#### [W1_PHASE_4_DATES]
**Phase 4 : Dimanche 30 Août**

#### [W1_PHASE_4]
**Amélioration progressive avec retour d'éclaircies.**



#### [W1_IMAGE_START]
*[Carte isobarique montrant un thalweg s'approchant de la France par l'ouest, avec une masse d'air chaude et humide remontant par le sud.]*
#### [W1_IMAGE_END]



###


## 🗓️ SEMAINE 2 : Du Lundi 31 Août au Dimanche 6 Septembre 2026
### 💡 Points clés de la semaine 2

### 🤝 Modèles et scénarios (Semaine 2)

### 🤖 Scénarios détaillés des modèles (Semaine 2)
Aucun modèle spécifique détaillé.

### 📍 Synthèse par zones/départements (Semaine 2)
| Zone / Département | Temps sensible | Températures | Fiabilité | Modèles | Notes d'analyse |
| --- | --- | --- | --- | --- | --- |
| **Nord (59)** | Chaleur d'été | 25°C à 30°C | Modérée | ECMWF, GFS, Guillaume Séchet | Incertitude habituelle J+14 |
| **Pas-de-Calais (62)** | Chaleur d'été | 25°C à 30°C | Modérée | ECMWF, GFS, Guillaume Séchet | Incertitude habituelle J+14 |
| **Somme (80)** | Chaleur d'été | 25°C à 30°C | Modérée | ECMWF, GFS, Guillaume Séchet | Incertitude habituelle J+14 |
| **Oise (60)** | Chaleur d'été | 25°C à 30°C | Modérée | ECMWF, GFS, Guillaume Séchet | Incertitude habituelle J+14 |
| **Aisne (02)** | Chaleur d'été | 25°C à 30°C | Modérée | ECMWF, GFS, Guillaume Séchet | Incertitude habituelle J+14 |

### ⏳ Déroulé chronologique (Semaine 2)


========================================

## 🔮 TENDANCE GLOBALE À 15 JOURS ET DOUTES

### 🚨 Analyse des doutes et lacunes