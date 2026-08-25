# BULLETIN DE PRÉVISIONS MÉTÉO INFOCLIMAT (RÉGIONAL HAUTS-DE-FRANCE)
**Généré le :** Mardi 25 Août 2026
**Période :** Semaine 1 (— SEMAINE 1 : Du Mardi 25 au Dimanche 30 Août 2026

### 🔑 [W1_KEY_POINT_1]
**Fin de canicule** : Les Hauts-de-France quittent les fortes chaleurs estivales pour un retour à des températures de saison, avec un net rafraîchissement dès vendredi.

### ⛈️ [W1_KEY_POINT_2]
**Dégradation orageuse** : Mercredi et jeudi, des orages parfois forts traversent la région, avec risque de grêle et de rafales, notamment sur la Somme et l'Oise placées en vigilance jaune.

### 🌬️ [W1_KEY_POINT_3]
**Vent de Sud-Ouest** : Un flux océanique s'installe en fin de semaine avec des rafales possibles jusqu'à 55 km/h, particulièrement sur le littoral.

### 🌡️ [W1_KEY_POINT_4]
**Températures en baisse** : Après des maximales de 27-29°C en début de semaine, on passe à 20-22°C vendredi, soit sous les normales de saison.

### 🌧️ [W1_KEY_POINT_5]
**Pluies bienvenues** : Cumuls attendus jusqu'à 15-20 mm localement (Aisne, Thiérache), contribuant à atténuer le déficit hydrique des sols.

---

### 📊 [W1_MODEL_START]

#### 🌐 [W1_MODEL_NAME] — Analyse des Modèles (GFS / ECMWF / ICON / CEP)

**[W1_MODEL_SCENARIO]** (max 160 car.)
Le scénario dominant montre un anticyclone scandinave se rétractant, laissant place à un flux dépressionnaire atlantique. L'axe dépressionnaire Labrador/Europe de l'Ouest se met en place, avec une anomalie de tropopause balayant la région mercredi-jeudi. Les modèles convergent vers un talweg persistant en fin de semaine, maintenant l'instabilité. ICON est le plus humide, GFS le plus frais ; CEP propose une cellule orageuse plus marquée sur l'est de la région.

**[W1_MODEL_SENSIBLE_WEATHER]** (max 120 car.)
Nuages et éclaircies alternent avec averses orageuses mercredi/jeudi ; éclaircies plus franches vendredi malgré des averses résiduelles.

**[W1_MODEL_AFFECTED_ZONES]** — Nord, Pas-de-Calais, Somme, Oise, Aisne (tous départements concernés par la dégradation orageuse)

**[W1_MODEL_EXTRACTION_CONF]** — Élevée (85%) : convergence des modèles sur le scénario de dégradation

**[W1_MODEL_SCENARIO_SUPPORT]** — 4 modèles sur 5 (GFS, ECMWF, ICON, ARPEGE) ; GEM en divergence partielle

**[W1_MODEL_STATUS]** — 🟡 Modéré — Tendances fiables à 72h, incertitudes sur les intensités orageuses

**[W1_MODEL_MENTIONS_COUNT]** — 12 mentions de dégradation orageuse sur les discussions

**[W1_MODEL_RUN]** — Run du 24/08/2026 12Z (fiable) + Run du 25/08/2026 00Z (en cours)

**[W1_MODEL_TIMING]** — Mercredi 26 après-midi : entrée des orages par l'ouest ; Jeudi 27 : généralisation ; Vendredi 28 : amélioration progressive

**[W1_MODEL_DETAILS]**
Le flux s'oriente au Sud-Ouest dès mercredi soir, avec un cisaillement modéré. Les indices CAPE deviennent significatifs (500-1000 J/kg) sur l'ensemble de la région. Le risque de phénomènes violents (grêle > 3 cm, rafales > 80 km/h) est modéré mais réel, principalement sur un axe Somme-Oise-Aisne. Le coefficient de confiance est de 4/5 pour la chronologie, 3/5 pour la localisation précise des cellules.

**[W1_MODEL_END]**

---

### ✅ [W1_CONVERGENCES] — Points de convergence (max 3)

1. **Refroidissement généralisé** : Tous les modèles s'accordent sur une baisse des températures dès vendredi 28, avec des maximales passant sous les 23°C.
2. **Dégradation orageuse** : Consensus large sur le passage orageux de mercredi après-midi à jeudi soir, avec un axe principal sur la moitié sud de la région.
3. **Vent de Sud-Ouest** : Renforcement du flux océanique en fin de semaine, avec rafales de 50-55 km/h sur le littoral et l'intérieur.

### ⚠️ [W1_DIVERGENCES] — Points de divergence (max 3)

1. **Intensité des orages** : Les modèles divergent sur le caractère violent ou non des cellules (ICON plus agressif, GFS plus modéré).
2. **Cumuls de pluie** : Écart de 5 à 15 mm selon les scénarios sur l'est de la région (Thiérache, Avesnois).
3. **Temps de dimanche** : Les projections oscillent entre un régime d'averses résiduelles et une amélioration plus nette.

---

### 📝 [W1_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance nuages/éclaircies mardi, dégradation orageuse mercredi soir et jeudi, averses vendredi, amélioration samedi",
      "temperatures": "Min 13-19°C, Max 21-26°C selon les jours (plus frais vendredi)",
      "rain_storms": "Risque d'orages mercredi soir/jeudi avec cumuls jusqu'à 15 mm possibles sur Lille et Douaisis",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Vent d'Est mardi (15-35 km/h), puis Sud à Sud-Ouest modéré (rafales 55 km/h vendredi)",
      "sensitive_period": "Jeudi 27 (risque orageux le plus marqué) et vendredi 28 (rafales)",
      "confidence_level": "elevee",
      "uncertainty": "Localisation précise des cellules orageuses et intensité",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages puis dégagements mardi, orages possibles en fin de nuit de mercredi, ciel couvert jeudi, averses vendredi",
      "temperatures": "Min 13-18°C, Max 20-28°C (24°C sur le littoral)",
      "rain_storms": "Cumuls jusqu'à 15 mm sur le Ternois jeudi, averses marines sur les côtes de la Manche",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Est à Sud-Est en début de période, puis Sud-Ouest assez fort sur le littoral (rafales 55 km/h)",
      "sensitive_period": "Fin de nuit de mercredi à jeudi (orages), vendredi après-midi (rafales littorales)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Ternois et l'Artois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages en après-midi (vigilance jaune), variable mercredi, très nuageux jeudi, averses vendredi",
      "temperatures": "Min 13-17°C, Max 20-29°C (25°C littoral)",
      "rain_storms": "Vigilance jaune orages mardi, cumuls jusqu'à 15 mm sur le Vermandois jeudi",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Est mardi (15-25 km/h), Sud-Ouest assez fort sur le littoral vendredi (rafales 55 km/h)",
      "sensitive_period": "Mardi après-midi (orages), jeudi soir (averses), vendredi (vent)",
      "confidence_level": "elevee",
      "uncertainty": "Extension des orages vers l'est du département",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux mardi avec orages possibles en fin de journée (vigilance jaune), ensoleillé mercredi matin, dégradation jeudi",
      "temperatures": "Min 12-17°C, Max 21-29°C",
      "rain_storms": "Cumuls jusqu'à 10 mm jeudi, orages possibles mercredi en seconde partie de nuit",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Variable faible mardi, Sud-Ouest modéré jeudi, assez fort lundi sur le pays de Bray",
      "sensitive_period": "Mercredi soir/nuit (orages), jeudi après-midi (averses étendues)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité orageuse sur le Plateau Picard et le Valois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Ensoleillé mardi avec orages en fin d'après-midi (vigilance jaune), très ensoleillé mercredi, orageux en soirée de jeudi",
      "temperatures": "Min 12-17°C, Max 21-30°C",
      "rain_storms": "Cumuls jusqu'à 20 mm sur la Thiérache jeudi, 10 mm sur le Vermandois mardi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Est à Sud-Est modéré mardi, Sud-Ouest avec rafales 55 km/h vendredi",
      "sensitive_period": "Mardi fin d'après-midi (orages), jeudi soir (orages potentiellement forts)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Tardenois et le Laonnois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W1_ZONES_JSON_END]

### 💪 [W1_SOLID_POINTS] — Points solides (max 3)

1. **Chronologie fiable** : La séquence "beau mardi → orages mercredi/jeudi → fraîchissement vendredi" est confirmée par tous les modèles avec une haute confiance (85%).
2. **Températures en baisse** : Le passage sous les 23°C vendredi est un signal robuste, partagé par l'ensemble des simulations.
3. **Vent de Sud-Ouest** : L'installation du flux océanique est actée, avec un renforcement prévu en fin de semaine.

### ⚠️ [W1_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Caractère violent des orages** : Incertitude sur le risque de grêle et de rafales destructrices (probabilité de 25-35%).
2. **Cumuls de précipitations** : Les quantités varient fortement selon la trajectoire des cellules orageuses.
3. **Temps de dimanche** : Les modèles peinent à trancher entre averses résiduelles et retour d'éclaircies durables.

### 🔭 [W1_NEXT_RUNS_TO_WATCH] — À surveiller

- **Prochain run CEP 12Z** (ce soir) : crucial pour affiner la trajectoire des orages de jeudi
- **Run ARPEGE 06Z** (demain matin) : affinage des cumuls de pluie sur l'est de la région
- **Sorties AROME** (6h) : suivi fin de la convection de mardi après-midi

---

## 🌡️ [W1_PHASE_1_DATES] — Phase 1 : Mardi 25 à Jeudi 27 Août

**[W1_PHASE_1]** — Temps chaud et lourd avec montée progressive de l'instabilité, culminant avec un risque orageux marqué mercredi soir et jeudi. Températures encore estivales (26-29°C) avant la bascule.

## 🌧️ [W1_PHASE_2_DATES] — Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.

---

**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**

---

**) & Semaine 2 (— SEMAINE 2 : Du Lundi 31 Août au Dimanche 6 Septembre 2026

### 🔑 [W2_KEY_POINT_1]
**Flux d'Ouest dépressionnaire** : La région reste sous influence océanique avec un régime de nuages et d'averses, sans retour de la canicule.

### 🌬️ [W2_KEY_POINT_2]
**Vent assez fort en début de semaine** : Rafales possibles jusqu'à 60-65 km/h lundi, particulièrement sur le littoral et le pays de Bray.

### 🌡️ [W2_KEY_POINT_3]
**Températures de saison** : Maximales comprises entre 20 et 24°C, minimales entre 12 et 15°C, conformes aux normales de début septembre.

### 🌧️ [W2_KEY_POINT_4]
**Pluies régulières mais modérées** : Risque d'averses quasi quotidien, avec des cumuls faibles à modérés (5-10 mm par épisode).

### 🔮 [W2_KEY_POINT_5]
**Incertitude fin de période** : Les modèles divergent sur un possible retour de l'anticyclone ou la poursuite du flux dépressionnaire.

---

### 📊 [W2_MODEL_START]

#### 🌐 [W2_MODEL_NAME] — Analyse des Modèles (GFS / ECMWF / ICON / CEP)

**[W2_MODEL_SCENARIO]** (max 160 car.)
Le flux d'ouest perturbé se maintient sur la France. Une dépression atlantique circule près des îles britanniques, entraînant un défilé de perturbations sur les Hauts-de-France. Les températures restent proches des normales saisonnières. En fin de période, les scénarios divergent : le CEP maintient le flux dépressionnaire, tandis que GFS propose une poussée anticyclonique par le sud-ouest. ECMWF est intermédiaire avec un talweg qui s'évacue lentement vers l'Europe centrale.

**[W2_MODEL_SENSIBLE_WEATHER]** (max 120 car.)
Ciel nuageux à couvert, averses fréquentes surtout lundi-mardi et jeudi ; éclaircies possibles mercredi et en fin de semaine.

**[W2_MODEL_AFFECTED_ZONES]** — Toute la région HDF, avec un gradient littoral/intérieur marqué (plus de vent et de pluie sur le littoral)

**[W2_MODEL_EXTRACTION_CONF]** — Moyenne (65%) : divergence croissante en fin d'échéance

**[W2_MODEL_SCENARIO_SUPPORT]** — 3 modèles sur 5 (CEP, ECMWF, ICON) pour le maintien du flux d'ouest ; GFS en divergence

**[W2_MODEL_STATUS]** — 🟡 Modéré — Tendances générales fiables, détails incertains au-delà de jeudi

**[W2_MODEL_MENTIONS_COUNT]** — 8 mentions de flux d'ouest et d'incertitude sur les discussions

**[W2_MODEL_RUN]** — Run du 25/08/2026 00Z (vision d'ensemble)

**[W2_MODEL_TIMING]** — Lundi-mardi : perturbation active ; Mercredi : accalmie relative ; Jeudi : nouvelle dégradation ; Week-end : indécis

**[W2_MODEL_DETAILS]**
La position du jet stream est déterminante : si son axe se décale au nord (scénario GFS), la région bénéficie d'une amélioration ; s'il reste sur la France (scénario CEP), les averses persistent. Le signal ENSO et l'activité tropicale (cyclone potentiel) pourraient influencer cette évolution à 10-14 jours. Les températures resteront proches des normales dans tous les scénarios (± 1-2°C).

**[W2_MODEL_END]**

---

### ✅ [W2_CONVERGENCES] — Points de convergence (max 3)

1. **Absence de canicule** : Aucun scénario ne propose un retour des fortes chaleurs (> 30°C) durant cette période.
2. **Températures de saison** : Consensus sur des maximales entre 20-24°C et minimales entre 12-15°C.
3. **Risque d'averses régulier** : Tous les modèles maintiennent un risque de précipitations quasi quotidien.

### ⚠️ [W2_DIVERGENCES] — Points de divergence (max 3)

1. **Fin de période** : GFS propose une remontée anticyclonique dès samedi, CEP maintient le flux dépressionnaire.
2. **Vent** : L'épisode venteux de lundi est confirmé, mais son intensité varie (60-75 km/h selon les modèles).
3. **Cumuls pluviométriques** : Les quantités prévues varient de 10 à 30 mm sur la semaine selon les scénarios.

---

### 📝 [W2_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi et mardi, éclaircies mercredi, retour des averses jeudi, variable en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Risque d'averses modérées, cumuls de 5-10 mm par épisode, orages possibles lundi après-midi",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Ouest-Sud-Ouest assez fort lundi (rafales 60 km/h en Flandres), modéré ensuite",
      "sensitive_period": "Lundi (vent fort et averses), jeudi (dégradation)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end (amélioration ou persistance des averses ?)",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Averses fréquentes lundi-mardi, éclaircies mercredi, dégradation jeudi, amélioration samedi-dimanche",
      "temperatures": "Min 12-15°C, Max 20-23°C (19-21°C littoral)",
      "rain_storms": "Risque d'averses marines, cumuls 5-8 mm sur le littoral, vent assez fort lundi",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Sud-Ouest assez fort lundi (rafales 65 km/h littoral), plus modéré ensuite",
      "sensitive_period": "Lundi (vent fort littoral), jeudi (pluies)",
      "confidence_level": "moderee",
      "uncertainty": "Intensité du vent en début de semaine et évolution du week-end",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi, variable mardi-mercredi, pluies jeudi, éclaircies possibles en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Averses modérées, cumuls 5-10 mm, vent assez fort lundi sur le littoral picard",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Ouest assez fort lundi (rafales 60 km/h nord du département), Sud-Ouest modéré ensuite",
      "sensitive_period": "Lundi (vent et averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, possibilité d'amélioration",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Averses lundi, nette amélioration mercredi, dégradation jeudi, incertitude en fin de semaine",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées lundi et jeudi, cumuls 5-10 mm, vent assez fort lundi sur le pays de Bray",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Ouest-Sud-Ouest assez fort lundi matin (rafales 55-60 km/h), modéré ensuite",
      "sensitive_period": "Lundi matin (vent), jeudi (dégradation pluvieuse)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end et possible retour anticyclonique",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Averses lundi et mardi, éclaircies mercredi, pluies jeudi, amélioration samedi-dimanche (scénario GFS)",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées, cumuls 5-8 mm, risque orageux faible lundi après-midi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Ouest à Sud-Ouest temporairement modéré, rafales possibles 50 km/h lundi",
      "sensitive_period": "Lundi (averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, scénario GFS plus sec que CEP",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W2_ZONES_JSON_END]

### 💪 [W2_SOLID_POINTS] — Points solides (max 3)

1. **Températures de saison** : Fort consensus sur des valeurs proches des normales (20-24°C), sans excès ni déficit marqué.
2. **Flux d'ouest** : Le régime perturbé est acté pour au moins la première partie de la semaine.
3. **Vent lundi** : Épisode venteux confirmé avec rafales de 55-65 km/h sur l'ouest de la région.

### ⚠️ [W2_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Fin de période très incertaine** : Oppositions marquées entre GFS (amélioration) et CEP (poursuite du flux dépressionnaire).
2. **Quantités de pluie** : Les cumuls varient du simple au triple selon les scénarios (10 à 30 mm sur la semaine).
3. **Position du jet** : Un décalage de quelques degrés de latitude change radicalement le temps prévu.

### 🔭 [W2_NEXT_RUNS_TO_WATCH] — À surveiller

- **Run CEP 12Z** (ce soir) : déterminant pour trancher le scénario du week-end
- **Sorties GFS ensemble** (nuit) : évaluation de la confiance dans la remontée anticyclonique
- **Bulletin Météo-France J+7** (jeudi) : affinage de la prévision à 10 jours

---

## 🌦️ [W2_PHASE_1_DATES] — Phase 1 : Lundi 31 Août à Mercredi 3 Septembre

**[W2_PHASE_1]** — Régime dépressionnaire actif avec vent assez fort lundi et averses fréquentes. Amélioration relative mercredi avec de belles éclaircies entre les passages nuageux. Températures de saison (20-23°C).

## ⛅ [W2_PHASE_2_DATES] — Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.

---

**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**

---

**)
*Analyse régionale ciblée sur les départements : Nord (59), Pas-de-Calais (62), Somme (80), Oise (60) et Aisne (02).*

========================================

## 📈 SYNTHÈSE DES INDICATEURS DE CONFIANCE
- **Consensus des modèles :** — Consensus des modèles : **Modéré**

**[GLOBAL_CONSENSUS_NOTE]** — Bonne convergence sur la semaine 1 (85%), nette divergence sur la fin de semaine 2 (55%). Le signal principal (fin de canicule, retour à la normale) est robuste.

## 🎭 [GLOBAL_SCENARIO_KPI] — Scénario dominant : **Flux océanique dépressionnaire**

**[GLOBAL_SCENARIO_NOTE]** — 60% de probabilité pour le maintien d'un régime d'ouest perturbé, 25% pour une amélioration anticyclonique en fin de période, 15% pour un scénario intermédiaire.

## ❓ [GLOBAL_UNCERTAINTY_KPI] — Incertitude globale : **Modérée**

**[GLOBAL_UNCERTAINTY_NOTE]** — Incertitude principalement liée à l'échéance J+8 et au-delà. Les prévisions à 3-5 jours restent fiables.

---

## 📱 [LINKEDIN_POST] — Publication LinkedIn

> 🌦️ **HAUTS-DE-FRANCE : FIN DE LA CANICULE, RETOUR D'UN TEMPS DE SAISON** 🌦️
> 
> La région bascule dans un régime océanique cette semaine !
> 
> 🔹 **Mardi** : Dernière journée chaude (26-28°C) avant la bascule
> 🔹 **Mercredi-Jeudi** : Dégradation orageuse, risque de grêle et rafales
> 🔹 **Vendredi** : Net rafraîchissement (20-22°C)
> 🔹 **Semaine prochaine** : Averses fréquentes, vent de Sud-Ouest, températures de saison
> 
> 📊 Les modèles s'accordent sur la fin de la canicule mais divergent pour le week-end du 6 septembre.
> 
> 💡 À suivre : le run CEP de ce soir pour affiner les prévisions !
> 
> #Météo #HautsDeFrance #Prévisions #Climat #Orages #MétéoFrance

---

** — *** — Bonne convergence sur la semaine 1 (85%), nette divergence sur la fin de semaine 2 (55%). Le signal principal (fin de canicule, retour à la normale) est robuste.

## 🎭 [GLOBAL_SCENARIO_KPI] — Scénario dominant : **Flux océanique dépressionnaire**

**[GLOBAL_SCENARIO_NOTE]** — 60% de probabilité pour le maintien d'un régime d'ouest perturbé, 25% pour une amélioration anticyclonique en fin de période, 15% pour un scénario intermédiaire.

## ❓ [GLOBAL_UNCERTAINTY_KPI] — Incertitude globale : **Modérée**

**[GLOBAL_UNCERTAINTY_NOTE]** — Incertitude principalement liée à l'échéance J+8 et au-delà. Les prévisions à 3-5 jours restent fiables.

---

## 📱 [LINKEDIN_POST] — Publication LinkedIn

> 🌦️ **HAUTS-DE-FRANCE : FIN DE LA CANICULE, RETOUR D'UN TEMPS DE SAISON** 🌦️
> 
> La région bascule dans un régime océanique cette semaine !
> 
> 🔹 **Mardi** : Dernière journée chaude (26-28°C) avant la bascule
> 🔹 **Mercredi-Jeudi** : Dégradation orageuse, risque de grêle et rafales
> 🔹 **Vendredi** : Net rafraîchissement (20-22°C)
> 🔹 **Semaine prochaine** : Averses fréquentes, vent de Sud-Ouest, températures de saison
> 
> 📊 Les modèles s'accordent sur la fin de la canicule mais divergent pour le week-end du 6 septembre.
> 
> 💡 À suivre : le run CEP de ce soir pour affiner les prévisions !
> 
> #Météo #HautsDeFrance #Prévisions #Climat #Orages #MétéoFrance

---

***
- **Fiabilité du scénario majoritaire :** — Scénario dominant : **Flux océanique dépressionnaire**

**[GLOBAL_SCENARIO_NOTE]** — 60% de probabilité pour le maintien d'un régime d'ouest perturbé, 25% pour une amélioration anticyclonique en fin de période, 15% pour un scénario intermédiaire.

## ❓ [GLOBAL_UNCERTAINTY_KPI] — Incertitude globale : **Modérée**

**[GLOBAL_UNCERTAINTY_NOTE]** — Incertitude principalement liée à l'échéance J+8 et au-delà. Les prévisions à 3-5 jours restent fiables.

---

## 📱 [LINKEDIN_POST] — Publication LinkedIn

> 🌦️ **HAUTS-DE-FRANCE : FIN DE LA CANICULE, RETOUR D'UN TEMPS DE SAISON** 🌦️
> 
> La région bascule dans un régime océanique cette semaine !
> 
> 🔹 **Mardi** : Dernière journée chaude (26-28°C) avant la bascule
> 🔹 **Mercredi-Jeudi** : Dégradation orageuse, risque de grêle et rafales
> 🔹 **Vendredi** : Net rafraîchissement (20-22°C)
> 🔹 **Semaine prochaine** : Averses fréquentes, vent de Sud-Ouest, températures de saison
> 
> 📊 Les modèles s'accordent sur la fin de la canicule mais divergent pour le week-end du 6 septembre.
> 
> 💡 À suivre : le run CEP de ce soir pour affiner les prévisions !
> 
> #Météo #HautsDeFrance #Prévisions #Climat #Orages #MétéoFrance

---

** — *** — 60% de probabilité pour le maintien d'un régime d'ouest perturbé, 25% pour une amélioration anticyclonique en fin de période, 15% pour un scénario intermédiaire.

## ❓ [GLOBAL_UNCERTAINTY_KPI] — Incertitude globale : **Modérée**

**[GLOBAL_UNCERTAINTY_NOTE]** — Incertitude principalement liée à l'échéance J+8 et au-delà. Les prévisions à 3-5 jours restent fiables.

---

## 📱 [LINKEDIN_POST] — Publication LinkedIn

> 🌦️ **HAUTS-DE-FRANCE : FIN DE LA CANICULE, RETOUR D'UN TEMPS DE SAISON** 🌦️
> 
> La région bascule dans un régime océanique cette semaine !
> 
> 🔹 **Mardi** : Dernière journée chaude (26-28°C) avant la bascule
> 🔹 **Mercredi-Jeudi** : Dégradation orageuse, risque de grêle et rafales
> 🔹 **Vendredi** : Net rafraîchissement (20-22°C)
> 🔹 **Semaine prochaine** : Averses fréquentes, vent de Sud-Ouest, températures de saison
> 
> 📊 Les modèles s'accordent sur la fin de la canicule mais divergent pour le week-end du 6 septembre.
> 
> 💡 À suivre : le run CEP de ce soir pour affiner les prévisions !
> 
> #Météo #HautsDeFrance #Prévisions #Climat #Orages #MétéoFrance

---

***
- **Stabilité des cartes/scénarios :** 6 / 63 — *6 cartes analysées*
- **Niveau d'incertitude global :** — Incertitude globale : **Modérée**

**[GLOBAL_UNCERTAINTY_NOTE]** — Incertitude principalement liée à l'échéance J+8 et au-delà. Les prévisions à 3-5 jours restent fiables.

---

## 📱 [LINKEDIN_POST] — Publication LinkedIn

> 🌦️ **HAUTS-DE-FRANCE : FIN DE LA CANICULE, RETOUR D'UN TEMPS DE SAISON** 🌦️
> 
> La région bascule dans un régime océanique cette semaine !
> 
> 🔹 **Mardi** : Dernière journée chaude (26-28°C) avant la bascule
> 🔹 **Mercredi-Jeudi** : Dégradation orageuse, risque de grêle et rafales
> 🔹 **Vendredi** : Net rafraîchissement (20-22°C)
> 🔹 **Semaine prochaine** : Averses fréquentes, vent de Sud-Ouest, températures de saison
> 
> 📊 Les modèles s'accordent sur la fin de la canicule mais divergent pour le week-end du 6 septembre.
> 
> 💡 À suivre : le run CEP de ce soir pour affiner les prévisions !
> 
> #Météo #HautsDeFrance #Prévisions #Climat #Orages #MétéoFrance

---

** — *** — Incertitude principalement liée à l'échéance J+8 et au-delà. Les prévisions à 3-5 jours restent fiables.

---

## 📱 [LINKEDIN_POST] — Publication LinkedIn

> 🌦️ **HAUTS-DE-FRANCE : FIN DE LA CANICULE, RETOUR D'UN TEMPS DE SAISON** 🌦️
> 
> La région bascule dans un régime océanique cette semaine !
> 
> 🔹 **Mardi** : Dernière journée chaude (26-28°C) avant la bascule
> 🔹 **Mercredi-Jeudi** : Dégradation orageuse, risque de grêle et rafales
> 🔹 **Vendredi** : Net rafraîchissement (20-22°C)
> 🔹 **Semaine prochaine** : Averses fréquentes, vent de Sud-Ouest, températures de saison
> 
> 📊 Les modèles s'accordent sur la fin de la canicule mais divergent pour le week-end du 6 septembre.
> 
> 💡 À suivre : le run CEP de ce soir pour affiner les prévisions !
> 
> #Météo #HautsDeFrance #Prévisions #Climat #Orages #MétéoFrance

---

***

## 🗓️ SEMAINE 1 : — SEMAINE 1 : Du Mardi 25 au Dimanche 30 Août 2026

### 🔑 [W1_KEY_POINT_1]
**Fin de canicule** : Les Hauts-de-France quittent les fortes chaleurs estivales pour un retour à des températures de saison, avec un net rafraîchissement dès vendredi.

### ⛈️ [W1_KEY_POINT_2]
**Dégradation orageuse** : Mercredi et jeudi, des orages parfois forts traversent la région, avec risque de grêle et de rafales, notamment sur la Somme et l'Oise placées en vigilance jaune.

### 🌬️ [W1_KEY_POINT_3]
**Vent de Sud-Ouest** : Un flux océanique s'installe en fin de semaine avec des rafales possibles jusqu'à 55 km/h, particulièrement sur le littoral.

### 🌡️ [W1_KEY_POINT_4]
**Températures en baisse** : Après des maximales de 27-29°C en début de semaine, on passe à 20-22°C vendredi, soit sous les normales de saison.

### 🌧️ [W1_KEY_POINT_5]
**Pluies bienvenues** : Cumuls attendus jusqu'à 15-20 mm localement (Aisne, Thiérache), contribuant à atténuer le déficit hydrique des sols.

---

### 📊 [W1_MODEL_START]

#### 🌐 [W1_MODEL_NAME] — Analyse des Modèles (GFS / ECMWF / ICON / CEP)

**[W1_MODEL_SCENARIO]** (max 160 car.)
Le scénario dominant montre un anticyclone scandinave se rétractant, laissant place à un flux dépressionnaire atlantique. L'axe dépressionnaire Labrador/Europe de l'Ouest se met en place, avec une anomalie de tropopause balayant la région mercredi-jeudi. Les modèles convergent vers un talweg persistant en fin de semaine, maintenant l'instabilité. ICON est le plus humide, GFS le plus frais ; CEP propose une cellule orageuse plus marquée sur l'est de la région.

**[W1_MODEL_SENSIBLE_WEATHER]** (max 120 car.)
Nuages et éclaircies alternent avec averses orageuses mercredi/jeudi ; éclaircies plus franches vendredi malgré des averses résiduelles.

**[W1_MODEL_AFFECTED_ZONES]** — Nord, Pas-de-Calais, Somme, Oise, Aisne (tous départements concernés par la dégradation orageuse)

**[W1_MODEL_EXTRACTION_CONF]** — Élevée (85%) : convergence des modèles sur le scénario de dégradation

**[W1_MODEL_SCENARIO_SUPPORT]** — 4 modèles sur 5 (GFS, ECMWF, ICON, ARPEGE) ; GEM en divergence partielle

**[W1_MODEL_STATUS]** — 🟡 Modéré — Tendances fiables à 72h, incertitudes sur les intensités orageuses

**[W1_MODEL_MENTIONS_COUNT]** — 12 mentions de dégradation orageuse sur les discussions

**[W1_MODEL_RUN]** — Run du 24/08/2026 12Z (fiable) + Run du 25/08/2026 00Z (en cours)

**[W1_MODEL_TIMING]** — Mercredi 26 après-midi : entrée des orages par l'ouest ; Jeudi 27 : généralisation ; Vendredi 28 : amélioration progressive

**[W1_MODEL_DETAILS]**
Le flux s'oriente au Sud-Ouest dès mercredi soir, avec un cisaillement modéré. Les indices CAPE deviennent significatifs (500-1000 J/kg) sur l'ensemble de la région. Le risque de phénomènes violents (grêle > 3 cm, rafales > 80 km/h) est modéré mais réel, principalement sur un axe Somme-Oise-Aisne. Le coefficient de confiance est de 4/5 pour la chronologie, 3/5 pour la localisation précise des cellules.

**[W1_MODEL_END]**

---

### ✅ [W1_CONVERGENCES] — Points de convergence (max 3)

1. **Refroidissement généralisé** : Tous les modèles s'accordent sur une baisse des températures dès vendredi 28, avec des maximales passant sous les 23°C.
2. **Dégradation orageuse** : Consensus large sur le passage orageux de mercredi après-midi à jeudi soir, avec un axe principal sur la moitié sud de la région.
3. **Vent de Sud-Ouest** : Renforcement du flux océanique en fin de semaine, avec rafales de 50-55 km/h sur le littoral et l'intérieur.

### ⚠️ [W1_DIVERGENCES] — Points de divergence (max 3)

1. **Intensité des orages** : Les modèles divergent sur le caractère violent ou non des cellules (ICON plus agressif, GFS plus modéré).
2. **Cumuls de pluie** : Écart de 5 à 15 mm selon les scénarios sur l'est de la région (Thiérache, Avesnois).
3. **Temps de dimanche** : Les projections oscillent entre un régime d'averses résiduelles et une amélioration plus nette.

---

### 📝 [W1_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance nuages/éclaircies mardi, dégradation orageuse mercredi soir et jeudi, averses vendredi, amélioration samedi",
      "temperatures": "Min 13-19°C, Max 21-26°C selon les jours (plus frais vendredi)",
      "rain_storms": "Risque d'orages mercredi soir/jeudi avec cumuls jusqu'à 15 mm possibles sur Lille et Douaisis",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Vent d'Est mardi (15-35 km/h), puis Sud à Sud-Ouest modéré (rafales 55 km/h vendredi)",
      "sensitive_period": "Jeudi 27 (risque orageux le plus marqué) et vendredi 28 (rafales)",
      "confidence_level": "elevee",
      "uncertainty": "Localisation précise des cellules orageuses et intensité",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages puis dégagements mardi, orages possibles en fin de nuit de mercredi, ciel couvert jeudi, averses vendredi",
      "temperatures": "Min 13-18°C, Max 20-28°C (24°C sur le littoral)",
      "rain_storms": "Cumuls jusqu'à 15 mm sur le Ternois jeudi, averses marines sur les côtes de la Manche",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Est à Sud-Est en début de période, puis Sud-Ouest assez fort sur le littoral (rafales 55 km/h)",
      "sensitive_period": "Fin de nuit de mercredi à jeudi (orages), vendredi après-midi (rafales littorales)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Ternois et l'Artois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages en après-midi (vigilance jaune), variable mercredi, très nuageux jeudi, averses vendredi",
      "temperatures": "Min 13-17°C, Max 20-29°C (25°C littoral)",
      "rain_storms": "Vigilance jaune orages mardi, cumuls jusqu'à 15 mm sur le Vermandois jeudi",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Est mardi (15-25 km/h), Sud-Ouest assez fort sur le littoral vendredi (rafales 55 km/h)",
      "sensitive_period": "Mardi après-midi (orages), jeudi soir (averses), vendredi (vent)",
      "confidence_level": "elevee",
      "uncertainty": "Extension des orages vers l'est du département",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux mardi avec orages possibles en fin de journée (vigilance jaune), ensoleillé mercredi matin, dégradation jeudi",
      "temperatures": "Min 12-17°C, Max 21-29°C",
      "rain_storms": "Cumuls jusqu'à 10 mm jeudi, orages possibles mercredi en seconde partie de nuit",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Variable faible mardi, Sud-Ouest modéré jeudi, assez fort lundi sur le pays de Bray",
      "sensitive_period": "Mercredi soir/nuit (orages), jeudi après-midi (averses étendues)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité orageuse sur le Plateau Picard et le Valois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Ensoleillé mardi avec orages en fin d'après-midi (vigilance jaune), très ensoleillé mercredi, orageux en soirée de jeudi",
      "temperatures": "Min 12-17°C, Max 21-30°C",
      "rain_storms": "Cumuls jusqu'à 20 mm sur la Thiérache jeudi, 10 mm sur le Vermandois mardi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Est à Sud-Est modéré mardi, Sud-Ouest avec rafales 55 km/h vendredi",
      "sensitive_period": "Mardi fin d'après-midi (orages), jeudi soir (orages potentiellement forts)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Tardenois et le Laonnois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W1_ZONES_JSON_END]

### 💪 [W1_SOLID_POINTS] — Points solides (max 3)

1. **Chronologie fiable** : La séquence "beau mardi → orages mercredi/jeudi → fraîchissement vendredi" est confirmée par tous les modèles avec une haute confiance (85%).
2. **Températures en baisse** : Le passage sous les 23°C vendredi est un signal robuste, partagé par l'ensemble des simulations.
3. **Vent de Sud-Ouest** : L'installation du flux océanique est actée, avec un renforcement prévu en fin de semaine.

### ⚠️ [W1_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Caractère violent des orages** : Incertitude sur le risque de grêle et de rafales destructrices (probabilité de 25-35%).
2. **Cumuls de précipitations** : Les quantités varient fortement selon la trajectoire des cellules orageuses.
3. **Temps de dimanche** : Les modèles peinent à trancher entre averses résiduelles et retour d'éclaircies durables.

### 🔭 [W1_NEXT_RUNS_TO_WATCH] — À surveiller

- **Prochain run CEP 12Z** (ce soir) : crucial pour affiner la trajectoire des orages de jeudi
- **Run ARPEGE 06Z** (demain matin) : affinage des cumuls de pluie sur l'est de la région
- **Sorties AROME** (6h) : suivi fin de la convection de mardi après-midi

---

## 🌡️ [W1_PHASE_1_DATES] — Phase 1 : Mardi 25 à Jeudi 27 Août

**[W1_PHASE_1]** — Temps chaud et lourd avec montée progressive de l'instabilité, culminant avec un risque orageux marqué mercredi soir et jeudi. Températures encore estivales (26-29°C) avant la bascule.

## 🌧️ [W1_PHASE_2_DATES] — Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.

---

**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**

---

**
### 💡 Points clés de la semaine 1
1. **Fin de canicule** : Les Hauts-de-France quittent les fortes chaleurs estivales pour un retour à des températures de saison, avec un net rafraîchissement dès vendredi.

### ⛈️ [W1_KEY_POINT_2]
**Dégradation orageuse** : Mercredi et jeudi, des orages parfois forts traversent la région, avec risque de grêle et de rafales, notamment sur la Somme et l'Oise placées en vigilance jaune.

### 🌬️ [W1_KEY_POINT_3]
**Vent de Sud-Ouest** : Un flux océanique s'installe en fin de semaine avec des rafales possibles jusqu'à 55 km/h, particulièrement sur le littoral.

### 🌡️ [W1_KEY_POINT_4]
**Températures en baisse** : Après des maximales de 27-29°C en début de semaine, on passe à 20-22°C vendredi, soit sous les normales de saison.

### 🌧️ [W1_KEY_POINT_5]
**Pluies bienvenues** : Cumuls attendus jusqu'à 15-20 mm localement (Aisne, Thiérache), contribuant à atténuer le déficit hydrique des sols.



### 📊 [W1_MODEL_START]

#### 🌐 [W1_MODEL_NAME] — Analyse des Modèles (GFS / ECMWF / ICON / CEP)

**[W1_MODEL_SCENARIO]** (max 160 car.)
Le scénario dominant montre un anticyclone scandinave se rétractant, laissant place à un flux dépressionnaire atlantique. L'axe dépressionnaire Labrador/Europe de l'Ouest se met en place, avec une anomalie de tropopause balayant la région mercredi-jeudi. Les modèles convergent vers un talweg persistant en fin de semaine, maintenant l'instabilité. ICON est le plus humide, GFS le plus frais ; CEP propose une cellule orageuse plus marquée sur l'est de la région.

**[W1_MODEL_SENSIBLE_WEATHER]** (max 120 car.)
Nuages et éclaircies alternent avec averses orageuses mercredi/jeudi ; éclaircies plus franches vendredi malgré des averses résiduelles.

**[W1_MODEL_AFFECTED_ZONES]** — Nord, Pas-de-Calais, Somme, Oise, Aisne (tous départements concernés par la dégradation orageuse)

**[W1_MODEL_EXTRACTION_CONF]** — Élevée (85%) : convergence des modèles sur le scénario de dégradation

**[W1_MODEL_SCENARIO_SUPPORT]** — 4 modèles sur 5 (GFS, ECMWF, ICON, ARPEGE) ; GEM en divergence partielle

**[W1_MODEL_STATUS]** — 🟡 Modéré — Tendances fiables à 72h, incertitudes sur les intensités orageuses

**[W1_MODEL_MENTIONS_COUNT]** — 12 mentions de dégradation orageuse sur les discussions

**[W1_MODEL_RUN]** — Run du 24/08/2026 12Z (fiable) + Run du 25/08/2026 00Z (en cours)

**[W1_MODEL_TIMING]** — Mercredi 26 après-midi : entrée des orages par l'ouest ; Jeudi 27 : généralisation ; Vendredi 28 : amélioration progressive

**[W1_MODEL_DETAILS]**
Le flux s'oriente au Sud-Ouest dès mercredi soir, avec un cisaillement modéré. Les indices CAPE deviennent significatifs (500-1000 J/kg) sur l'ensemble de la région. Le risque de phénomènes violents (grêle > 3 cm, rafales > 80 km/h) est modéré mais réel, principalement sur un axe Somme-Oise-Aisne. Le coefficient de confiance est de 4/5 pour la chronologie, 3/5 pour la localisation précise des cellules.

**[W1_MODEL_END]**



### ✅ [W1_CONVERGENCES] — Points de convergence (max 3)

1. **Refroidissement généralisé** : Tous les modèles s'accordent sur une baisse des températures dès vendredi 28, avec des maximales passant sous les 23°C.
2. **Dégradation orageuse** : Consensus large sur le passage orageux de mercredi après-midi à jeudi soir, avec un axe principal sur la moitié sud de la région.
3. **Vent de Sud-Ouest** : Renforcement du flux océanique en fin de semaine, avec rafales de 50-55 km/h sur le littoral et l'intérieur.

### ⚠️ [W1_DIVERGENCES] — Points de divergence (max 3)

1. **Intensité des orages** : Les modèles divergent sur le caractère violent ou non des cellules (ICON plus agressif, GFS plus modéré).
2. **Cumuls de pluie** : Écart de 5 à 15 mm selon les scénarios sur l'est de la région (Thiérache, Avesnois).
3. **Temps de dimanche** : Les projections oscillent entre un régime d'averses résiduelles et une amélioration plus nette.



### 📝 [W1_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance nuages/éclaircies mardi, dégradation orageuse mercredi soir et jeudi, averses vendredi, amélioration samedi",
      "temperatures": "Min 13-19°C, Max 21-26°C selon les jours (plus frais vendredi)",
      "rain_storms": "Risque d'orages mercredi soir/jeudi avec cumuls jusqu'à 15 mm possibles sur Lille et Douaisis",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Vent d'Est mardi (15-35 km/h), puis Sud à Sud-Ouest modéré (rafales 55 km/h vendredi)",
      "sensitive_period": "Jeudi 27 (risque orageux le plus marqué) et vendredi 28 (rafales)",
      "confidence_level": "elevee",
      "uncertainty": "Localisation précise des cellules orageuses et intensité",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages puis dégagements mardi, orages possibles en fin de nuit de mercredi, ciel couvert jeudi, averses vendredi",
      "temperatures": "Min 13-18°C, Max 20-28°C (24°C sur le littoral)",
      "rain_storms": "Cumuls jusqu'à 15 mm sur le Ternois jeudi, averses marines sur les côtes de la Manche",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Est à Sud-Est en début de période, puis Sud-Ouest assez fort sur le littoral (rafales 55 km/h)",
      "sensitive_period": "Fin de nuit de mercredi à jeudi (orages), vendredi après-midi (rafales littorales)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Ternois et l'Artois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages en après-midi (vigilance jaune), variable mercredi, très nuageux jeudi, averses vendredi",
      "temperatures": "Min 13-17°C, Max 20-29°C (25°C littoral)",
      "rain_storms": "Vigilance jaune orages mardi, cumuls jusqu'à 15 mm sur le Vermandois jeudi",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Est mardi (15-25 km/h), Sud-Ouest assez fort sur le littoral vendredi (rafales 55 km/h)",
      "sensitive_period": "Mardi après-midi (orages), jeudi soir (averses), vendredi (vent)",
      "confidence_level": "elevee",
      "uncertainty": "Extension des orages vers l'est du département",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux mardi avec orages possibles en fin de journée (vigilance jaune), ensoleillé mercredi matin, dégradation jeudi",
      "temperatures": "Min 12-17°C, Max 21-29°C",
      "rain_storms": "Cumuls jusqu'à 10 mm jeudi, orages possibles mercredi en seconde partie de nuit",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Variable faible mardi, Sud-Ouest modéré jeudi, assez fort lundi sur le pays de Bray",
      "sensitive_period": "Mercredi soir/nuit (orages), jeudi après-midi (averses étendues)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité orageuse sur le Plateau Picard et le Valois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Ensoleillé mardi avec orages en fin d'après-midi (vigilance jaune), très ensoleillé mercredi, orageux en soirée de jeudi",
      "temperatures": "Min 12-17°C, Max 21-30°C",
      "rain_storms": "Cumuls jusqu'à 20 mm sur la Thiérache jeudi, 10 mm sur le Vermandois mardi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Est à Sud-Est modéré mardi, Sud-Ouest avec rafales 55 km/h vendredi",
      "sensitive_period": "Mardi fin d'après-midi (orages), jeudi soir (orages potentiellement forts)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Tardenois et le Laonnois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W1_ZONES_JSON_END]

### 💪 [W1_SOLID_POINTS] — Points solides (max 3)

1. **Chronologie fiable** : La séquence "beau mardi → orages mercredi/jeudi → fraîchissement vendredi" est confirmée par tous les modèles avec une haute confiance (85%).
2. **Températures en baisse** : Le passage sous les 23°C vendredi est un signal robuste, partagé par l'ensemble des simulations.
3. **Vent de Sud-Ouest** : L'installation du flux océanique est actée, avec un renforcement prévu en fin de semaine.

### ⚠️ [W1_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Caractère violent des orages** : Incertitude sur le risque de grêle et de rafales destructrices (probabilité de 25-35%).
2. **Cumuls de précipitations** : Les quantités varient fortement selon la trajectoire des cellules orageuses.
3. **Temps de dimanche** : Les modèles peinent à trancher entre averses résiduelles et retour d'éclaircies durables.

### 🔭 [W1_NEXT_RUNS_TO_WATCH] — À surveiller

- **Prochain run CEP 12Z** (ce soir) : crucial pour affiner la trajectoire des orages de jeudi
- **Run ARPEGE 06Z** (demain matin) : affinage des cumuls de pluie sur l'est de la région
- **Sorties AROME** (6h) : suivi fin de la convection de mardi après-midi



## 🌡️ [W1_PHASE_1_DATES] — Phase 1 : Mardi 25 à Jeudi 27 Août

**[W1_PHASE_1]** — Temps chaud et lourd avec montée progressive de l'instabilité, culminant avec un risque orageux marqué mercredi soir et jeudi. Températures encore estivales (26-29°C) avant la bascule.

## 🌧️ [W1_PHASE_2_DATES] — Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.



**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**



**
2. **Dégradation orageuse** : Mercredi et jeudi, des orages parfois forts traversent la région, avec risque de grêle et de rafales, notamment sur la Somme et l'Oise placées en vigilance jaune.

### 🌬️ [W1_KEY_POINT_3]
**Vent de Sud-Ouest** : Un flux océanique s'installe en fin de semaine avec des rafales possibles jusqu'à 55 km/h, particulièrement sur le littoral.

### 🌡️ [W1_KEY_POINT_4]
**Températures en baisse** : Après des maximales de 27-29°C en début de semaine, on passe à 20-22°C vendredi, soit sous les normales de saison.

### 🌧️ [W1_KEY_POINT_5]
**Pluies bienvenues** : Cumuls attendus jusqu'à 15-20 mm localement (Aisne, Thiérache), contribuant à atténuer le déficit hydrique des sols.



### 📊 [W1_MODEL_START]

#### 🌐 [W1_MODEL_NAME] — Analyse des Modèles (GFS / ECMWF / ICON / CEP)

**[W1_MODEL_SCENARIO]** (max 160 car.)
Le scénario dominant montre un anticyclone scandinave se rétractant, laissant place à un flux dépressionnaire atlantique. L'axe dépressionnaire Labrador/Europe de l'Ouest se met en place, avec une anomalie de tropopause balayant la région mercredi-jeudi. Les modèles convergent vers un talweg persistant en fin de semaine, maintenant l'instabilité. ICON est le plus humide, GFS le plus frais ; CEP propose une cellule orageuse plus marquée sur l'est de la région.

**[W1_MODEL_SENSIBLE_WEATHER]** (max 120 car.)
Nuages et éclaircies alternent avec averses orageuses mercredi/jeudi ; éclaircies plus franches vendredi malgré des averses résiduelles.

**[W1_MODEL_AFFECTED_ZONES]** — Nord, Pas-de-Calais, Somme, Oise, Aisne (tous départements concernés par la dégradation orageuse)

**[W1_MODEL_EXTRACTION_CONF]** — Élevée (85%) : convergence des modèles sur le scénario de dégradation

**[W1_MODEL_SCENARIO_SUPPORT]** — 4 modèles sur 5 (GFS, ECMWF, ICON, ARPEGE) ; GEM en divergence partielle

**[W1_MODEL_STATUS]** — 🟡 Modéré — Tendances fiables à 72h, incertitudes sur les intensités orageuses

**[W1_MODEL_MENTIONS_COUNT]** — 12 mentions de dégradation orageuse sur les discussions

**[W1_MODEL_RUN]** — Run du 24/08/2026 12Z (fiable) + Run du 25/08/2026 00Z (en cours)

**[W1_MODEL_TIMING]** — Mercredi 26 après-midi : entrée des orages par l'ouest ; Jeudi 27 : généralisation ; Vendredi 28 : amélioration progressive

**[W1_MODEL_DETAILS]**
Le flux s'oriente au Sud-Ouest dès mercredi soir, avec un cisaillement modéré. Les indices CAPE deviennent significatifs (500-1000 J/kg) sur l'ensemble de la région. Le risque de phénomènes violents (grêle > 3 cm, rafales > 80 km/h) est modéré mais réel, principalement sur un axe Somme-Oise-Aisne. Le coefficient de confiance est de 4/5 pour la chronologie, 3/5 pour la localisation précise des cellules.

**[W1_MODEL_END]**



### ✅ [W1_CONVERGENCES] — Points de convergence (max 3)

1. **Refroidissement généralisé** : Tous les modèles s'accordent sur une baisse des températures dès vendredi 28, avec des maximales passant sous les 23°C.
2. **Dégradation orageuse** : Consensus large sur le passage orageux de mercredi après-midi à jeudi soir, avec un axe principal sur la moitié sud de la région.
3. **Vent de Sud-Ouest** : Renforcement du flux océanique en fin de semaine, avec rafales de 50-55 km/h sur le littoral et l'intérieur.

### ⚠️ [W1_DIVERGENCES] — Points de divergence (max 3)

1. **Intensité des orages** : Les modèles divergent sur le caractère violent ou non des cellules (ICON plus agressif, GFS plus modéré).
2. **Cumuls de pluie** : Écart de 5 à 15 mm selon les scénarios sur l'est de la région (Thiérache, Avesnois).
3. **Temps de dimanche** : Les projections oscillent entre un régime d'averses résiduelles et une amélioration plus nette.



### 📝 [W1_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance nuages/éclaircies mardi, dégradation orageuse mercredi soir et jeudi, averses vendredi, amélioration samedi",
      "temperatures": "Min 13-19°C, Max 21-26°C selon les jours (plus frais vendredi)",
      "rain_storms": "Risque d'orages mercredi soir/jeudi avec cumuls jusqu'à 15 mm possibles sur Lille et Douaisis",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Vent d'Est mardi (15-35 km/h), puis Sud à Sud-Ouest modéré (rafales 55 km/h vendredi)",
      "sensitive_period": "Jeudi 27 (risque orageux le plus marqué) et vendredi 28 (rafales)",
      "confidence_level": "elevee",
      "uncertainty": "Localisation précise des cellules orageuses et intensité",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages puis dégagements mardi, orages possibles en fin de nuit de mercredi, ciel couvert jeudi, averses vendredi",
      "temperatures": "Min 13-18°C, Max 20-28°C (24°C sur le littoral)",
      "rain_storms": "Cumuls jusqu'à 15 mm sur le Ternois jeudi, averses marines sur les côtes de la Manche",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Est à Sud-Est en début de période, puis Sud-Ouest assez fort sur le littoral (rafales 55 km/h)",
      "sensitive_period": "Fin de nuit de mercredi à jeudi (orages), vendredi après-midi (rafales littorales)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Ternois et l'Artois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages en après-midi (vigilance jaune), variable mercredi, très nuageux jeudi, averses vendredi",
      "temperatures": "Min 13-17°C, Max 20-29°C (25°C littoral)",
      "rain_storms": "Vigilance jaune orages mardi, cumuls jusqu'à 15 mm sur le Vermandois jeudi",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Est mardi (15-25 km/h), Sud-Ouest assez fort sur le littoral vendredi (rafales 55 km/h)",
      "sensitive_period": "Mardi après-midi (orages), jeudi soir (averses), vendredi (vent)",
      "confidence_level": "elevee",
      "uncertainty": "Extension des orages vers l'est du département",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux mardi avec orages possibles en fin de journée (vigilance jaune), ensoleillé mercredi matin, dégradation jeudi",
      "temperatures": "Min 12-17°C, Max 21-29°C",
      "rain_storms": "Cumuls jusqu'à 10 mm jeudi, orages possibles mercredi en seconde partie de nuit",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Variable faible mardi, Sud-Ouest modéré jeudi, assez fort lundi sur le pays de Bray",
      "sensitive_period": "Mercredi soir/nuit (orages), jeudi après-midi (averses étendues)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité orageuse sur le Plateau Picard et le Valois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Ensoleillé mardi avec orages en fin d'après-midi (vigilance jaune), très ensoleillé mercredi, orageux en soirée de jeudi",
      "temperatures": "Min 12-17°C, Max 21-30°C",
      "rain_storms": "Cumuls jusqu'à 20 mm sur la Thiérache jeudi, 10 mm sur le Vermandois mardi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Est à Sud-Est modéré mardi, Sud-Ouest avec rafales 55 km/h vendredi",
      "sensitive_period": "Mardi fin d'après-midi (orages), jeudi soir (orages potentiellement forts)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Tardenois et le Laonnois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W1_ZONES_JSON_END]

### 💪 [W1_SOLID_POINTS] — Points solides (max 3)

1. **Chronologie fiable** : La séquence "beau mardi → orages mercredi/jeudi → fraîchissement vendredi" est confirmée par tous les modèles avec une haute confiance (85%).
2. **Températures en baisse** : Le passage sous les 23°C vendredi est un signal robuste, partagé par l'ensemble des simulations.
3. **Vent de Sud-Ouest** : L'installation du flux océanique est actée, avec un renforcement prévu en fin de semaine.

### ⚠️ [W1_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Caractère violent des orages** : Incertitude sur le risque de grêle et de rafales destructrices (probabilité de 25-35%).
2. **Cumuls de précipitations** : Les quantités varient fortement selon la trajectoire des cellules orageuses.
3. **Temps de dimanche** : Les modèles peinent à trancher entre averses résiduelles et retour d'éclaircies durables.

### 🔭 [W1_NEXT_RUNS_TO_WATCH] — À surveiller

- **Prochain run CEP 12Z** (ce soir) : crucial pour affiner la trajectoire des orages de jeudi
- **Run ARPEGE 06Z** (demain matin) : affinage des cumuls de pluie sur l'est de la région
- **Sorties AROME** (6h) : suivi fin de la convection de mardi après-midi



## 🌡️ [W1_PHASE_1_DATES] — Phase 1 : Mardi 25 à Jeudi 27 Août

**[W1_PHASE_1]** — Temps chaud et lourd avec montée progressive de l'instabilité, culminant avec un risque orageux marqué mercredi soir et jeudi. Températures encore estivales (26-29°C) avant la bascule.

## 🌧️ [W1_PHASE_2_DATES] — Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.



**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**



**
3. **Vent de Sud-Ouest** : Un flux océanique s'installe en fin de semaine avec des rafales possibles jusqu'à 55 km/h, particulièrement sur le littoral.

### 🌡️ [W1_KEY_POINT_4]
**Températures en baisse** : Après des maximales de 27-29°C en début de semaine, on passe à 20-22°C vendredi, soit sous les normales de saison.

### 🌧️ [W1_KEY_POINT_5]
**Pluies bienvenues** : Cumuls attendus jusqu'à 15-20 mm localement (Aisne, Thiérache), contribuant à atténuer le déficit hydrique des sols.



### 📊 [W1_MODEL_START]

#### 🌐 [W1_MODEL_NAME] — Analyse des Modèles (GFS / ECMWF / ICON / CEP)

**[W1_MODEL_SCENARIO]** (max 160 car.)
Le scénario dominant montre un anticyclone scandinave se rétractant, laissant place à un flux dépressionnaire atlantique. L'axe dépressionnaire Labrador/Europe de l'Ouest se met en place, avec une anomalie de tropopause balayant la région mercredi-jeudi. Les modèles convergent vers un talweg persistant en fin de semaine, maintenant l'instabilité. ICON est le plus humide, GFS le plus frais ; CEP propose une cellule orageuse plus marquée sur l'est de la région.

**[W1_MODEL_SENSIBLE_WEATHER]** (max 120 car.)
Nuages et éclaircies alternent avec averses orageuses mercredi/jeudi ; éclaircies plus franches vendredi malgré des averses résiduelles.

**[W1_MODEL_AFFECTED_ZONES]** — Nord, Pas-de-Calais, Somme, Oise, Aisne (tous départements concernés par la dégradation orageuse)

**[W1_MODEL_EXTRACTION_CONF]** — Élevée (85%) : convergence des modèles sur le scénario de dégradation

**[W1_MODEL_SCENARIO_SUPPORT]** — 4 modèles sur 5 (GFS, ECMWF, ICON, ARPEGE) ; GEM en divergence partielle

**[W1_MODEL_STATUS]** — 🟡 Modéré — Tendances fiables à 72h, incertitudes sur les intensités orageuses

**[W1_MODEL_MENTIONS_COUNT]** — 12 mentions de dégradation orageuse sur les discussions

**[W1_MODEL_RUN]** — Run du 24/08/2026 12Z (fiable) + Run du 25/08/2026 00Z (en cours)

**[W1_MODEL_TIMING]** — Mercredi 26 après-midi : entrée des orages par l'ouest ; Jeudi 27 : généralisation ; Vendredi 28 : amélioration progressive

**[W1_MODEL_DETAILS]**
Le flux s'oriente au Sud-Ouest dès mercredi soir, avec un cisaillement modéré. Les indices CAPE deviennent significatifs (500-1000 J/kg) sur l'ensemble de la région. Le risque de phénomènes violents (grêle > 3 cm, rafales > 80 km/h) est modéré mais réel, principalement sur un axe Somme-Oise-Aisne. Le coefficient de confiance est de 4/5 pour la chronologie, 3/5 pour la localisation précise des cellules.

**[W1_MODEL_END]**



### ✅ [W1_CONVERGENCES] — Points de convergence (max 3)

1. **Refroidissement généralisé** : Tous les modèles s'accordent sur une baisse des températures dès vendredi 28, avec des maximales passant sous les 23°C.
2. **Dégradation orageuse** : Consensus large sur le passage orageux de mercredi après-midi à jeudi soir, avec un axe principal sur la moitié sud de la région.
3. **Vent de Sud-Ouest** : Renforcement du flux océanique en fin de semaine, avec rafales de 50-55 km/h sur le littoral et l'intérieur.

### ⚠️ [W1_DIVERGENCES] — Points de divergence (max 3)

1. **Intensité des orages** : Les modèles divergent sur le caractère violent ou non des cellules (ICON plus agressif, GFS plus modéré).
2. **Cumuls de pluie** : Écart de 5 à 15 mm selon les scénarios sur l'est de la région (Thiérache, Avesnois).
3. **Temps de dimanche** : Les projections oscillent entre un régime d'averses résiduelles et une amélioration plus nette.



### 📝 [W1_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance nuages/éclaircies mardi, dégradation orageuse mercredi soir et jeudi, averses vendredi, amélioration samedi",
      "temperatures": "Min 13-19°C, Max 21-26°C selon les jours (plus frais vendredi)",
      "rain_storms": "Risque d'orages mercredi soir/jeudi avec cumuls jusqu'à 15 mm possibles sur Lille et Douaisis",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Vent d'Est mardi (15-35 km/h), puis Sud à Sud-Ouest modéré (rafales 55 km/h vendredi)",
      "sensitive_period": "Jeudi 27 (risque orageux le plus marqué) et vendredi 28 (rafales)",
      "confidence_level": "elevee",
      "uncertainty": "Localisation précise des cellules orageuses et intensité",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages puis dégagements mardi, orages possibles en fin de nuit de mercredi, ciel couvert jeudi, averses vendredi",
      "temperatures": "Min 13-18°C, Max 20-28°C (24°C sur le littoral)",
      "rain_storms": "Cumuls jusqu'à 15 mm sur le Ternois jeudi, averses marines sur les côtes de la Manche",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Est à Sud-Est en début de période, puis Sud-Ouest assez fort sur le littoral (rafales 55 km/h)",
      "sensitive_period": "Fin de nuit de mercredi à jeudi (orages), vendredi après-midi (rafales littorales)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Ternois et l'Artois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages en après-midi (vigilance jaune), variable mercredi, très nuageux jeudi, averses vendredi",
      "temperatures": "Min 13-17°C, Max 20-29°C (25°C littoral)",
      "rain_storms": "Vigilance jaune orages mardi, cumuls jusqu'à 15 mm sur le Vermandois jeudi",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Est mardi (15-25 km/h), Sud-Ouest assez fort sur le littoral vendredi (rafales 55 km/h)",
      "sensitive_period": "Mardi après-midi (orages), jeudi soir (averses), vendredi (vent)",
      "confidence_level": "elevee",
      "uncertainty": "Extension des orages vers l'est du département",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux mardi avec orages possibles en fin de journée (vigilance jaune), ensoleillé mercredi matin, dégradation jeudi",
      "temperatures": "Min 12-17°C, Max 21-29°C",
      "rain_storms": "Cumuls jusqu'à 10 mm jeudi, orages possibles mercredi en seconde partie de nuit",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Variable faible mardi, Sud-Ouest modéré jeudi, assez fort lundi sur le pays de Bray",
      "sensitive_period": "Mercredi soir/nuit (orages), jeudi après-midi (averses étendues)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité orageuse sur le Plateau Picard et le Valois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Ensoleillé mardi avec orages en fin d'après-midi (vigilance jaune), très ensoleillé mercredi, orageux en soirée de jeudi",
      "temperatures": "Min 12-17°C, Max 21-30°C",
      "rain_storms": "Cumuls jusqu'à 20 mm sur la Thiérache jeudi, 10 mm sur le Vermandois mardi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Est à Sud-Est modéré mardi, Sud-Ouest avec rafales 55 km/h vendredi",
      "sensitive_period": "Mardi fin d'après-midi (orages), jeudi soir (orages potentiellement forts)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Tardenois et le Laonnois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W1_ZONES_JSON_END]

### 💪 [W1_SOLID_POINTS] — Points solides (max 3)

1. **Chronologie fiable** : La séquence "beau mardi → orages mercredi/jeudi → fraîchissement vendredi" est confirmée par tous les modèles avec une haute confiance (85%).
2. **Températures en baisse** : Le passage sous les 23°C vendredi est un signal robuste, partagé par l'ensemble des simulations.
3. **Vent de Sud-Ouest** : L'installation du flux océanique est actée, avec un renforcement prévu en fin de semaine.

### ⚠️ [W1_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Caractère violent des orages** : Incertitude sur le risque de grêle et de rafales destructrices (probabilité de 25-35%).
2. **Cumuls de précipitations** : Les quantités varient fortement selon la trajectoire des cellules orageuses.
3. **Temps de dimanche** : Les modèles peinent à trancher entre averses résiduelles et retour d'éclaircies durables.

### 🔭 [W1_NEXT_RUNS_TO_WATCH] — À surveiller

- **Prochain run CEP 12Z** (ce soir) : crucial pour affiner la trajectoire des orages de jeudi
- **Run ARPEGE 06Z** (demain matin) : affinage des cumuls de pluie sur l'est de la région
- **Sorties AROME** (6h) : suivi fin de la convection de mardi après-midi



## 🌡️ [W1_PHASE_1_DATES] — Phase 1 : Mardi 25 à Jeudi 27 Août

**[W1_PHASE_1]** — Temps chaud et lourd avec montée progressive de l'instabilité, culminant avec un risque orageux marqué mercredi soir et jeudi. Températures encore estivales (26-29°C) avant la bascule.

## 🌧️ [W1_PHASE_2_DATES] — Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.



**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**



**
4. **Températures en baisse** : Après des maximales de 27-29°C en début de semaine, on passe à 20-22°C vendredi, soit sous les normales de saison.

### 🌧️ [W1_KEY_POINT_5]
**Pluies bienvenues** : Cumuls attendus jusqu'à 15-20 mm localement (Aisne, Thiérache), contribuant à atténuer le déficit hydrique des sols.



### 📊 [W1_MODEL_START]

#### 🌐 [W1_MODEL_NAME] — Analyse des Modèles (GFS / ECMWF / ICON / CEP)

**[W1_MODEL_SCENARIO]** (max 160 car.)
Le scénario dominant montre un anticyclone scandinave se rétractant, laissant place à un flux dépressionnaire atlantique. L'axe dépressionnaire Labrador/Europe de l'Ouest se met en place, avec une anomalie de tropopause balayant la région mercredi-jeudi. Les modèles convergent vers un talweg persistant en fin de semaine, maintenant l'instabilité. ICON est le plus humide, GFS le plus frais ; CEP propose une cellule orageuse plus marquée sur l'est de la région.

**[W1_MODEL_SENSIBLE_WEATHER]** (max 120 car.)
Nuages et éclaircies alternent avec averses orageuses mercredi/jeudi ; éclaircies plus franches vendredi malgré des averses résiduelles.

**[W1_MODEL_AFFECTED_ZONES]** — Nord, Pas-de-Calais, Somme, Oise, Aisne (tous départements concernés par la dégradation orageuse)

**[W1_MODEL_EXTRACTION_CONF]** — Élevée (85%) : convergence des modèles sur le scénario de dégradation

**[W1_MODEL_SCENARIO_SUPPORT]** — 4 modèles sur 5 (GFS, ECMWF, ICON, ARPEGE) ; GEM en divergence partielle

**[W1_MODEL_STATUS]** — 🟡 Modéré — Tendances fiables à 72h, incertitudes sur les intensités orageuses

**[W1_MODEL_MENTIONS_COUNT]** — 12 mentions de dégradation orageuse sur les discussions

**[W1_MODEL_RUN]** — Run du 24/08/2026 12Z (fiable) + Run du 25/08/2026 00Z (en cours)

**[W1_MODEL_TIMING]** — Mercredi 26 après-midi : entrée des orages par l'ouest ; Jeudi 27 : généralisation ; Vendredi 28 : amélioration progressive

**[W1_MODEL_DETAILS]**
Le flux s'oriente au Sud-Ouest dès mercredi soir, avec un cisaillement modéré. Les indices CAPE deviennent significatifs (500-1000 J/kg) sur l'ensemble de la région. Le risque de phénomènes violents (grêle > 3 cm, rafales > 80 km/h) est modéré mais réel, principalement sur un axe Somme-Oise-Aisne. Le coefficient de confiance est de 4/5 pour la chronologie, 3/5 pour la localisation précise des cellules.

**[W1_MODEL_END]**



### ✅ [W1_CONVERGENCES] — Points de convergence (max 3)

1. **Refroidissement généralisé** : Tous les modèles s'accordent sur une baisse des températures dès vendredi 28, avec des maximales passant sous les 23°C.
2. **Dégradation orageuse** : Consensus large sur le passage orageux de mercredi après-midi à jeudi soir, avec un axe principal sur la moitié sud de la région.
3. **Vent de Sud-Ouest** : Renforcement du flux océanique en fin de semaine, avec rafales de 50-55 km/h sur le littoral et l'intérieur.

### ⚠️ [W1_DIVERGENCES] — Points de divergence (max 3)

1. **Intensité des orages** : Les modèles divergent sur le caractère violent ou non des cellules (ICON plus agressif, GFS plus modéré).
2. **Cumuls de pluie** : Écart de 5 à 15 mm selon les scénarios sur l'est de la région (Thiérache, Avesnois).
3. **Temps de dimanche** : Les projections oscillent entre un régime d'averses résiduelles et une amélioration plus nette.



### 📝 [W1_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance nuages/éclaircies mardi, dégradation orageuse mercredi soir et jeudi, averses vendredi, amélioration samedi",
      "temperatures": "Min 13-19°C, Max 21-26°C selon les jours (plus frais vendredi)",
      "rain_storms": "Risque d'orages mercredi soir/jeudi avec cumuls jusqu'à 15 mm possibles sur Lille et Douaisis",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Vent d'Est mardi (15-35 km/h), puis Sud à Sud-Ouest modéré (rafales 55 km/h vendredi)",
      "sensitive_period": "Jeudi 27 (risque orageux le plus marqué) et vendredi 28 (rafales)",
      "confidence_level": "elevee",
      "uncertainty": "Localisation précise des cellules orageuses et intensité",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages puis dégagements mardi, orages possibles en fin de nuit de mercredi, ciel couvert jeudi, averses vendredi",
      "temperatures": "Min 13-18°C, Max 20-28°C (24°C sur le littoral)",
      "rain_storms": "Cumuls jusqu'à 15 mm sur le Ternois jeudi, averses marines sur les côtes de la Manche",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Est à Sud-Est en début de période, puis Sud-Ouest assez fort sur le littoral (rafales 55 km/h)",
      "sensitive_period": "Fin de nuit de mercredi à jeudi (orages), vendredi après-midi (rafales littorales)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Ternois et l'Artois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages en après-midi (vigilance jaune), variable mercredi, très nuageux jeudi, averses vendredi",
      "temperatures": "Min 13-17°C, Max 20-29°C (25°C littoral)",
      "rain_storms": "Vigilance jaune orages mardi, cumuls jusqu'à 15 mm sur le Vermandois jeudi",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Est mardi (15-25 km/h), Sud-Ouest assez fort sur le littoral vendredi (rafales 55 km/h)",
      "sensitive_period": "Mardi après-midi (orages), jeudi soir (averses), vendredi (vent)",
      "confidence_level": "elevee",
      "uncertainty": "Extension des orages vers l'est du département",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux mardi avec orages possibles en fin de journée (vigilance jaune), ensoleillé mercredi matin, dégradation jeudi",
      "temperatures": "Min 12-17°C, Max 21-29°C",
      "rain_storms": "Cumuls jusqu'à 10 mm jeudi, orages possibles mercredi en seconde partie de nuit",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Variable faible mardi, Sud-Ouest modéré jeudi, assez fort lundi sur le pays de Bray",
      "sensitive_period": "Mercredi soir/nuit (orages), jeudi après-midi (averses étendues)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité orageuse sur le Plateau Picard et le Valois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Ensoleillé mardi avec orages en fin d'après-midi (vigilance jaune), très ensoleillé mercredi, orageux en soirée de jeudi",
      "temperatures": "Min 12-17°C, Max 21-30°C",
      "rain_storms": "Cumuls jusqu'à 20 mm sur la Thiérache jeudi, 10 mm sur le Vermandois mardi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Est à Sud-Est modéré mardi, Sud-Ouest avec rafales 55 km/h vendredi",
      "sensitive_period": "Mardi fin d'après-midi (orages), jeudi soir (orages potentiellement forts)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Tardenois et le Laonnois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W1_ZONES_JSON_END]

### 💪 [W1_SOLID_POINTS] — Points solides (max 3)

1. **Chronologie fiable** : La séquence "beau mardi → orages mercredi/jeudi → fraîchissement vendredi" est confirmée par tous les modèles avec une haute confiance (85%).
2. **Températures en baisse** : Le passage sous les 23°C vendredi est un signal robuste, partagé par l'ensemble des simulations.
3. **Vent de Sud-Ouest** : L'installation du flux océanique est actée, avec un renforcement prévu en fin de semaine.

### ⚠️ [W1_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Caractère violent des orages** : Incertitude sur le risque de grêle et de rafales destructrices (probabilité de 25-35%).
2. **Cumuls de précipitations** : Les quantités varient fortement selon la trajectoire des cellules orageuses.
3. **Temps de dimanche** : Les modèles peinent à trancher entre averses résiduelles et retour d'éclaircies durables.

### 🔭 [W1_NEXT_RUNS_TO_WATCH] — À surveiller

- **Prochain run CEP 12Z** (ce soir) : crucial pour affiner la trajectoire des orages de jeudi
- **Run ARPEGE 06Z** (demain matin) : affinage des cumuls de pluie sur l'est de la région
- **Sorties AROME** (6h) : suivi fin de la convection de mardi après-midi



## 🌡️ [W1_PHASE_1_DATES] — Phase 1 : Mardi 25 à Jeudi 27 Août

**[W1_PHASE_1]** — Temps chaud et lourd avec montée progressive de l'instabilité, culminant avec un risque orageux marqué mercredi soir et jeudi. Températures encore estivales (26-29°C) avant la bascule.

## 🌧️ [W1_PHASE_2_DATES] — Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.



**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**



**
5. **Pluies bienvenues** : Cumuls attendus jusqu'à 15-20 mm localement (Aisne, Thiérache), contribuant à atténuer le déficit hydrique des sols.



### 📊 [W1_MODEL_START]

#### 🌐 [W1_MODEL_NAME] — Analyse des Modèles (GFS / ECMWF / ICON / CEP)

**[W1_MODEL_SCENARIO]** (max 160 car.)
Le scénario dominant montre un anticyclone scandinave se rétractant, laissant place à un flux dépressionnaire atlantique. L'axe dépressionnaire Labrador/Europe de l'Ouest se met en place, avec une anomalie de tropopause balayant la région mercredi-jeudi. Les modèles convergent vers un talweg persistant en fin de semaine, maintenant l'instabilité. ICON est le plus humide, GFS le plus frais ; CEP propose une cellule orageuse plus marquée sur l'est de la région.

**[W1_MODEL_SENSIBLE_WEATHER]** (max 120 car.)
Nuages et éclaircies alternent avec averses orageuses mercredi/jeudi ; éclaircies plus franches vendredi malgré des averses résiduelles.

**[W1_MODEL_AFFECTED_ZONES]** — Nord, Pas-de-Calais, Somme, Oise, Aisne (tous départements concernés par la dégradation orageuse)

**[W1_MODEL_EXTRACTION_CONF]** — Élevée (85%) : convergence des modèles sur le scénario de dégradation

**[W1_MODEL_SCENARIO_SUPPORT]** — 4 modèles sur 5 (GFS, ECMWF, ICON, ARPEGE) ; GEM en divergence partielle

**[W1_MODEL_STATUS]** — 🟡 Modéré — Tendances fiables à 72h, incertitudes sur les intensités orageuses

**[W1_MODEL_MENTIONS_COUNT]** — 12 mentions de dégradation orageuse sur les discussions

**[W1_MODEL_RUN]** — Run du 24/08/2026 12Z (fiable) + Run du 25/08/2026 00Z (en cours)

**[W1_MODEL_TIMING]** — Mercredi 26 après-midi : entrée des orages par l'ouest ; Jeudi 27 : généralisation ; Vendredi 28 : amélioration progressive

**[W1_MODEL_DETAILS]**
Le flux s'oriente au Sud-Ouest dès mercredi soir, avec un cisaillement modéré. Les indices CAPE deviennent significatifs (500-1000 J/kg) sur l'ensemble de la région. Le risque de phénomènes violents (grêle > 3 cm, rafales > 80 km/h) est modéré mais réel, principalement sur un axe Somme-Oise-Aisne. Le coefficient de confiance est de 4/5 pour la chronologie, 3/5 pour la localisation précise des cellules.

**[W1_MODEL_END]**



### ✅ [W1_CONVERGENCES] — Points de convergence (max 3)

1. **Refroidissement généralisé** : Tous les modèles s'accordent sur une baisse des températures dès vendredi 28, avec des maximales passant sous les 23°C.
2. **Dégradation orageuse** : Consensus large sur le passage orageux de mercredi après-midi à jeudi soir, avec un axe principal sur la moitié sud de la région.
3. **Vent de Sud-Ouest** : Renforcement du flux océanique en fin de semaine, avec rafales de 50-55 km/h sur le littoral et l'intérieur.

### ⚠️ [W1_DIVERGENCES] — Points de divergence (max 3)

1. **Intensité des orages** : Les modèles divergent sur le caractère violent ou non des cellules (ICON plus agressif, GFS plus modéré).
2. **Cumuls de pluie** : Écart de 5 à 15 mm selon les scénarios sur l'est de la région (Thiérache, Avesnois).
3. **Temps de dimanche** : Les projections oscillent entre un régime d'averses résiduelles et une amélioration plus nette.



### 📝 [W1_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance nuages/éclaircies mardi, dégradation orageuse mercredi soir et jeudi, averses vendredi, amélioration samedi",
      "temperatures": "Min 13-19°C, Max 21-26°C selon les jours (plus frais vendredi)",
      "rain_storms": "Risque d'orages mercredi soir/jeudi avec cumuls jusqu'à 15 mm possibles sur Lille et Douaisis",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Vent d'Est mardi (15-35 km/h), puis Sud à Sud-Ouest modéré (rafales 55 km/h vendredi)",
      "sensitive_period": "Jeudi 27 (risque orageux le plus marqué) et vendredi 28 (rafales)",
      "confidence_level": "elevee",
      "uncertainty": "Localisation précise des cellules orageuses et intensité",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages puis dégagements mardi, orages possibles en fin de nuit de mercredi, ciel couvert jeudi, averses vendredi",
      "temperatures": "Min 13-18°C, Max 20-28°C (24°C sur le littoral)",
      "rain_storms": "Cumuls jusqu'à 15 mm sur le Ternois jeudi, averses marines sur les côtes de la Manche",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Est à Sud-Est en début de période, puis Sud-Ouest assez fort sur le littoral (rafales 55 km/h)",
      "sensitive_period": "Fin de nuit de mercredi à jeudi (orages), vendredi après-midi (rafales littorales)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Ternois et l'Artois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages en après-midi (vigilance jaune), variable mercredi, très nuageux jeudi, averses vendredi",
      "temperatures": "Min 13-17°C, Max 20-29°C (25°C littoral)",
      "rain_storms": "Vigilance jaune orages mardi, cumuls jusqu'à 15 mm sur le Vermandois jeudi",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Est mardi (15-25 km/h), Sud-Ouest assez fort sur le littoral vendredi (rafales 55 km/h)",
      "sensitive_period": "Mardi après-midi (orages), jeudi soir (averses), vendredi (vent)",
      "confidence_level": "elevee",
      "uncertainty": "Extension des orages vers l'est du département",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux mardi avec orages possibles en fin de journée (vigilance jaune), ensoleillé mercredi matin, dégradation jeudi",
      "temperatures": "Min 12-17°C, Max 21-29°C",
      "rain_storms": "Cumuls jusqu'à 10 mm jeudi, orages possibles mercredi en seconde partie de nuit",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Variable faible mardi, Sud-Ouest modéré jeudi, assez fort lundi sur le pays de Bray",
      "sensitive_period": "Mercredi soir/nuit (orages), jeudi après-midi (averses étendues)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité orageuse sur le Plateau Picard et le Valois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Ensoleillé mardi avec orages en fin d'après-midi (vigilance jaune), très ensoleillé mercredi, orageux en soirée de jeudi",
      "temperatures": "Min 12-17°C, Max 21-30°C",
      "rain_storms": "Cumuls jusqu'à 20 mm sur la Thiérache jeudi, 10 mm sur le Vermandois mardi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Est à Sud-Est modéré mardi, Sud-Ouest avec rafales 55 km/h vendredi",
      "sensitive_period": "Mardi fin d'après-midi (orages), jeudi soir (orages potentiellement forts)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Tardenois et le Laonnois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W1_ZONES_JSON_END]

### 💪 [W1_SOLID_POINTS] — Points solides (max 3)

1. **Chronologie fiable** : La séquence "beau mardi → orages mercredi/jeudi → fraîchissement vendredi" est confirmée par tous les modèles avec une haute confiance (85%).
2. **Températures en baisse** : Le passage sous les 23°C vendredi est un signal robuste, partagé par l'ensemble des simulations.
3. **Vent de Sud-Ouest** : L'installation du flux océanique est actée, avec un renforcement prévu en fin de semaine.

### ⚠️ [W1_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Caractère violent des orages** : Incertitude sur le risque de grêle et de rafales destructrices (probabilité de 25-35%).
2. **Cumuls de précipitations** : Les quantités varient fortement selon la trajectoire des cellules orageuses.
3. **Temps de dimanche** : Les modèles peinent à trancher entre averses résiduelles et retour d'éclaircies durables.

### 🔭 [W1_NEXT_RUNS_TO_WATCH] — À surveiller

- **Prochain run CEP 12Z** (ce soir) : crucial pour affiner la trajectoire des orages de jeudi
- **Run ARPEGE 06Z** (demain matin) : affinage des cumuls de pluie sur l'est de la région
- **Sorties AROME** (6h) : suivi fin de la convection de mardi après-midi



## 🌡️ [W1_PHASE_1_DATES] — Phase 1 : Mardi 25 à Jeudi 27 Août

**[W1_PHASE_1]** — Temps chaud et lourd avec montée progressive de l'instabilité, culminant avec un risque orageux marqué mercredi soir et jeudi. Températures encore estivales (26-29°C) avant la bascule.

## 🌧️ [W1_PHASE_2_DATES] — Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.



**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**



**

### 🤝 Modèles et scénarios (Semaine 1)
**Points de convergence :**
— Points de convergence (max 3)

1. **Refroidissement généralisé** : Tous les modèles s'accordent sur une baisse des températures dès vendredi 28, avec des maximales passant sous les 23°C.
2. **Dégradation orageuse** : Consensus large sur le passage orageux de mercredi après-midi à jeudi soir, avec un axe principal sur la moitié sud de la région.
3. **Vent de Sud-Ouest** : Renforcement du flux océanique en fin de semaine, avec rafales de 50-55 km/h sur le littoral et l'intérieur.

### ⚠️ [W1_DIVERGENCES] — Points de divergence (max 3)

1. **Intensité des orages** : Les modèles divergent sur le caractère violent ou non des cellules (ICON plus agressif, GFS plus modéré).
2. **Cumuls de pluie** : Écart de 5 à 15 mm selon les scénarios sur l'est de la région (Thiérache, Avesnois).
3. **Temps de dimanche** : Les projections oscillent entre un régime d'averses résiduelles et une amélioration plus nette.



### 📝 [W1_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance nuages/éclaircies mardi, dégradation orageuse mercredi soir et jeudi, averses vendredi, amélioration samedi",
      "temperatures": "Min 13-19°C, Max 21-26°C selon les jours (plus frais vendredi)",
      "rain_storms": "Risque d'orages mercredi soir/jeudi avec cumuls jusqu'à 15 mm possibles sur Lille et Douaisis",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Vent d'Est mardi (15-35 km/h), puis Sud à Sud-Ouest modéré (rafales 55 km/h vendredi)",
      "sensitive_period": "Jeudi 27 (risque orageux le plus marqué) et vendredi 28 (rafales)",
      "confidence_level": "elevee",
      "uncertainty": "Localisation précise des cellules orageuses et intensité",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages puis dégagements mardi, orages possibles en fin de nuit de mercredi, ciel couvert jeudi, averses vendredi",
      "temperatures": "Min 13-18°C, Max 20-28°C (24°C sur le littoral)",
      "rain_storms": "Cumuls jusqu'à 15 mm sur le Ternois jeudi, averses marines sur les côtes de la Manche",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Est à Sud-Est en début de période, puis Sud-Ouest assez fort sur le littoral (rafales 55 km/h)",
      "sensitive_period": "Fin de nuit de mercredi à jeudi (orages), vendredi après-midi (rafales littorales)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Ternois et l'Artois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages en après-midi (vigilance jaune), variable mercredi, très nuageux jeudi, averses vendredi",
      "temperatures": "Min 13-17°C, Max 20-29°C (25°C littoral)",
      "rain_storms": "Vigilance jaune orages mardi, cumuls jusqu'à 15 mm sur le Vermandois jeudi",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Est mardi (15-25 km/h), Sud-Ouest assez fort sur le littoral vendredi (rafales 55 km/h)",
      "sensitive_period": "Mardi après-midi (orages), jeudi soir (averses), vendredi (vent)",
      "confidence_level": "elevee",
      "uncertainty": "Extension des orages vers l'est du département",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux mardi avec orages possibles en fin de journée (vigilance jaune), ensoleillé mercredi matin, dégradation jeudi",
      "temperatures": "Min 12-17°C, Max 21-29°C",
      "rain_storms": "Cumuls jusqu'à 10 mm jeudi, orages possibles mercredi en seconde partie de nuit",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Variable faible mardi, Sud-Ouest modéré jeudi, assez fort lundi sur le pays de Bray",
      "sensitive_period": "Mercredi soir/nuit (orages), jeudi après-midi (averses étendues)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité orageuse sur le Plateau Picard et le Valois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Ensoleillé mardi avec orages en fin d'après-midi (vigilance jaune), très ensoleillé mercredi, orageux en soirée de jeudi",
      "temperatures": "Min 12-17°C, Max 21-30°C",
      "rain_storms": "Cumuls jusqu'à 20 mm sur la Thiérache jeudi, 10 mm sur le Vermandois mardi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Est à Sud-Est modéré mardi, Sud-Ouest avec rafales 55 km/h vendredi",
      "sensitive_period": "Mardi fin d'après-midi (orages), jeudi soir (orages potentiellement forts)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Tardenois et le Laonnois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W1_ZONES_JSON_END]

### 💪 [W1_SOLID_POINTS] — Points solides (max 3)

1. **Chronologie fiable** : La séquence "beau mardi → orages mercredi/jeudi → fraîchissement vendredi" est confirmée par tous les modèles avec une haute confiance (85%).
2. **Températures en baisse** : Le passage sous les 23°C vendredi est un signal robuste, partagé par l'ensemble des simulations.
3. **Vent de Sud-Ouest** : L'installation du flux océanique est actée, avec un renforcement prévu en fin de semaine.

### ⚠️ [W1_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Caractère violent des orages** : Incertitude sur le risque de grêle et de rafales destructrices (probabilité de 25-35%).
2. **Cumuls de précipitations** : Les quantités varient fortement selon la trajectoire des cellules orageuses.
3. **Temps de dimanche** : Les modèles peinent à trancher entre averses résiduelles et retour d'éclaircies durables.

### 🔭 [W1_NEXT_RUNS_TO_WATCH] — À surveiller

- **Prochain run CEP 12Z** (ce soir) : crucial pour affiner la trajectoire des orages de jeudi
- **Run ARPEGE 06Z** (demain matin) : affinage des cumuls de pluie sur l'est de la région
- **Sorties AROME** (6h) : suivi fin de la convection de mardi après-midi



## 🌡️ [W1_PHASE_1_DATES] — Phase 1 : Mardi 25 à Jeudi 27 Août

**[W1_PHASE_1]** — Temps chaud et lourd avec montée progressive de l'instabilité, culminant avec un risque orageux marqué mercredi soir et jeudi. Températures encore estivales (26-29°C) avant la bascule.

## 🌧️ [W1_PHASE_2_DATES] — Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.



**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**



**
**Points de divergence :**
— Points de divergence (max 3)

1. **Intensité des orages** : Les modèles divergent sur le caractère violent ou non des cellules (ICON plus agressif, GFS plus modéré).
2. **Cumuls de pluie** : Écart de 5 à 15 mm selon les scénarios sur l'est de la région (Thiérache, Avesnois).
3. **Temps de dimanche** : Les projections oscillent entre un régime d'averses résiduelles et une amélioration plus nette.



### 📝 [W1_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Alternance nuages/éclaircies mardi, dégradation orageuse mercredi soir et jeudi, averses vendredi, amélioration samedi",
      "temperatures": "Min 13-19°C, Max 21-26°C selon les jours (plus frais vendredi)",
      "rain_storms": "Risque d'orages mercredi soir/jeudi avec cumuls jusqu'à 15 mm possibles sur Lille et Douaisis",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Vent d'Est mardi (15-35 km/h), puis Sud à Sud-Ouest modéré (rafales 55 km/h vendredi)",
      "sensitive_period": "Jeudi 27 (risque orageux le plus marqué) et vendredi 28 (rafales)",
      "confidence_level": "elevee",
      "uncertainty": "Localisation précise des cellules orageuses et intensité",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Nuages puis dégagements mardi, orages possibles en fin de nuit de mercredi, ciel couvert jeudi, averses vendredi",
      "temperatures": "Min 13-18°C, Max 20-28°C (24°C sur le littoral)",
      "rain_storms": "Cumuls jusqu'à 15 mm sur le Ternois jeudi, averses marines sur les côtes de la Manche",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Est à Sud-Est en début de période, puis Sud-Ouest assez fort sur le littoral (rafales 55 km/h)",
      "sensitive_period": "Fin de nuit de mercredi à jeudi (orages), vendredi après-midi (rafales littorales)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Ternois et l'Artois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Ensoleillé mardi matin puis orages en après-midi (vigilance jaune), variable mercredi, très nuageux jeudi, averses vendredi",
      "temperatures": "Min 13-17°C, Max 20-29°C (25°C littoral)",
      "rain_storms": "Vigilance jaune orages mardi, cumuls jusqu'à 15 mm sur le Vermandois jeudi",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Est mardi (15-25 km/h), Sud-Ouest assez fort sur le littoral vendredi (rafales 55 km/h)",
      "sensitive_period": "Mardi après-midi (orages), jeudi soir (averses), vendredi (vent)",
      "confidence_level": "elevee",
      "uncertainty": "Extension des orages vers l'est du département",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Nuageux mardi avec orages possibles en fin de journée (vigilance jaune), ensoleillé mercredi matin, dégradation jeudi",
      "temperatures": "Min 12-17°C, Max 21-29°C",
      "rain_storms": "Cumuls jusqu'à 10 mm jeudi, orages possibles mercredi en seconde partie de nuit",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Variable faible mardi, Sud-Ouest modéré jeudi, assez fort lundi sur le pays de Bray",
      "sensitive_period": "Mercredi soir/nuit (orages), jeudi après-midi (averses étendues)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité orageuse sur le Plateau Picard et le Valois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Ensoleillé mardi avec orages en fin d'après-midi (vigilance jaune), très ensoleillé mercredi, orageux en soirée de jeudi",
      "temperatures": "Min 12-17°C, Max 21-30°C",
      "rain_storms": "Cumuls jusqu'à 20 mm sur la Thiérache jeudi, 10 mm sur le Vermandois mardi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Est à Sud-Est modéré mardi, Sud-Ouest avec rafales 55 km/h vendredi",
      "sensitive_period": "Mardi fin d'après-midi (orages), jeudi soir (orages potentiellement forts)",
      "confidence_level": "elevee",
      "uncertainty": "Intensité des orages sur le Tardenois et le Laonnois",
      "evidence_count": 5,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W1_ZONES_JSON_END]

### 💪 [W1_SOLID_POINTS] — Points solides (max 3)

1. **Chronologie fiable** : La séquence "beau mardi → orages mercredi/jeudi → fraîchissement vendredi" est confirmée par tous les modèles avec une haute confiance (85%).
2. **Températures en baisse** : Le passage sous les 23°C vendredi est un signal robuste, partagé par l'ensemble des simulations.
3. **Vent de Sud-Ouest** : L'installation du flux océanique est actée, avec un renforcement prévu en fin de semaine.

### ⚠️ [W1_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Caractère violent des orages** : Incertitude sur le risque de grêle et de rafales destructrices (probabilité de 25-35%).
2. **Cumuls de précipitations** : Les quantités varient fortement selon la trajectoire des cellules orageuses.
3. **Temps de dimanche** : Les modèles peinent à trancher entre averses résiduelles et retour d'éclaircies durables.

### 🔭 [W1_NEXT_RUNS_TO_WATCH] — À surveiller

- **Prochain run CEP 12Z** (ce soir) : crucial pour affiner la trajectoire des orages de jeudi
- **Run ARPEGE 06Z** (demain matin) : affinage des cumuls de pluie sur l'est de la région
- **Sorties AROME** (6h) : suivi fin de la convection de mardi après-midi



## 🌡️ [W1_PHASE_1_DATES] — Phase 1 : Mardi 25 à Jeudi 27 Août

**[W1_PHASE_1]** — Temps chaud et lourd avec montée progressive de l'instabilité, culminant avec un risque orageux marqué mercredi soir et jeudi. Températures encore estivales (26-29°C) avant la bascule.

## 🌧️ [W1_PHASE_2_DATES] — Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.



**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**



**

### 🤖 Scénarios détaillés des modèles (Semaine 1)
| Modèle | Scénario | Temps sensible | Zones concernées | Confiance | Détails d'analyse |
| --- | --- | --- | --- | --- | --- |
| **— Analyse des Modèles (GFS / ECMWF / ICON / CEP)

<strong>[W1_MODEL_SCENARIO]</strong> (max 160 car.)
Le scénario dominant montre un anticyclone scandinave se rétractant, laissant place à un flux dépressionnaire atlantique. L'axe dépressionnaire Labrador/Europe de l'Ouest se met en place, avec une anomalie de tropopause balayant la région mercredi-jeudi. Les modèles convergent vers un talweg persistant en fin de semaine, maintenant l'instabilité. ICON est le plus humide, GFS le plus frais ; CEP propose une cellule orageuse plus marquée sur l'est de la région.

<strong>[W1_MODEL_SENSIBLE_WEATHER]</strong> (max 120 car.)
Nuages et éclaircies alternent avec averses orageuses mercredi/jeudi ; éclaircies plus franches vendredi malgré des averses résiduelles.

<strong>[W1_MODEL_AFFECTED_ZONES]</strong> — Nord, Pas-de-Calais, Somme, Oise, Aisne (tous départements concernés par la dégradation orageuse)

<strong>[W1_MODEL_EXTRACTION_CONF]</strong> — Élevée (85%) : convergence des modèles sur le scénario de dégradation

<strong>[W1_MODEL_SCENARIO_SUPPORT]</strong> — 4 modèles sur 5 (GFS, ECMWF, ICON, ARPEGE) ; GEM en divergence partielle

<strong>[W1_MODEL_STATUS]</strong> — 🟡 Modéré — Tendances fiables à 72h, incertitudes sur les intensités orageuses

<strong>[W1_MODEL_MENTIONS_COUNT]</strong> — 12 mentions de dégradation orageuse sur les discussions

<strong>[W1_MODEL_RUN]</strong> — Run du 24/08/2026 12Z (fiable) + Run du 25/08/2026 00Z (en cours)

<strong>[W1_MODEL_TIMING]</strong> — Mercredi 26 après-midi : entrée des orages par l'ouest ; Jeudi 27 : généralisation ; Vendredi 28 : amélioration progressive

<strong>[W1_MODEL_DETAILS]</strong>
Le flux s'oriente au Sud-Ouest dès mercredi soir, avec un cisaillement modéré. Les indices CAPE deviennent significatifs (500-1000 J/kg) sur l'ensemble de la région. Le risque de phénomènes violents (grêle > 3 cm, rafales > 80 km/h) est modéré mais réel, principalement sur un axe Somme-Oise-Aisne. Le coefficient de confiance est de 4/5 pour la chronologie, 3/5 pour la localisation précise des cellules.

**** (** — 🟡 Modéré — Tendances fiables à 72h, incertitudes sur les intensités orageuses

**[W1_MODEL_MENTIONS_COUNT]** — 12 mentions de dégradation orageuse sur les discussions

**[W1_MODEL_RUN]** — Run du 24/08/2026 12Z (fiable) + Run du 25/08/2026 00Z (en cours)

**[W1_MODEL_TIMING]** — Mercredi 26 après-midi : entrée des orages par l'ouest ; Jeudi 27 : généralisation ; Vendredi 28 : amélioration progressive

**[W1_MODEL_DETAILS]**
Le flux s'oriente au Sud-Ouest dès mercredi soir, avec un cisaillement modéré. Les indices CAPE deviennent significatifs (500-1000 J/kg) sur l'ensemble de la région. Le risque de phénomènes violents (grêle > 3 cm, rafales > 80 km/h) est modéré mais réel, principalement sur un axe Somme-Oise-Aisne. Le coefficient de confiance est de 4/5 pour la chronologie, 3/5 pour la localisation précise des cellules.

**) | ** (max 160 car.)
Le scénario dominant montre un anticyclone scandinave se rétractant, laissant place à un flux dépressionnaire atlantique. L'axe dépressionnaire Labrador/Europe de l'Ouest se met en place, avec une anomalie de tropopause balayant la région mercredi-jeudi. Les modèles convergent vers un talweg persistant en fin de semaine, maintenant l'instabilité. ICON est le plus humide, GFS le plus frais ; CEP propose une cellule orageuse plus marquée sur l'est de la région.

<strong>[W1_MODEL_SENSIBLE_WEATHER]</strong> (max 120 car.)
Nuages et éclaircies alternent avec averses orageuses mercredi/jeudi ; éclaircies plus franches vendredi malgré des averses résiduelles.

<strong>[W1_MODEL_AFFECTED_ZONES]</strong> — Nord, Pas-de-Calais, Somme, Oise, Aisne (tous départements concernés par la dégradation orageuse)

<strong>[W1_MODEL_EXTRACTION_CONF]</strong> — Élevée (85%) : convergence des modèles sur le scénario de dégradation

<strong>[W1_MODEL_SCENARIO_SUPPORT]</strong> — 4 modèles sur 5 (GFS, ECMWF, ICON, ARPEGE) ; GEM en divergence partielle

<strong>[W1_MODEL_STATUS]</strong> — 🟡 Modéré — Tendances fiables à 72h, incertitudes sur les intensités orageuses

<strong>[W1_MODEL_MENTIONS_COUNT]</strong> — 12 mentions de dégradation orageuse sur les discussions

<strong>[W1_MODEL_RUN]</strong> — Run du 24/08/2026 12Z (fiable) + Run du 25/08/2026 00Z (en cours)

<strong>[W1_MODEL_TIMING]</strong> — Mercredi 26 après-midi : entrée des orages par l'ouest ; Jeudi 27 : généralisation ; Vendredi 28 : amélioration progressive

<strong>[W1_MODEL_DETAILS]</strong>
Le flux s'oriente au Sud-Ouest dès mercredi soir, avec un cisaillement modéré. Les indices CAPE deviennent significatifs (500-1000 J/kg) sur l'ensemble de la région. Le risque de phénomènes violents (grêle > 3 cm, rafales > 80 km/h) est modéré mais réel, principalement sur un axe Somme-Oise-Aisne. Le coefficient de confiance est de 4/5 pour la chronologie, 3/5 pour la localisation précise des cellules.

** | ** (max 120 car.)
Nuages et éclaircies alternent avec averses orageuses mercredi/jeudi ; éclaircies plus franches vendredi malgré des averses résiduelles.

<strong>[W1_MODEL_AFFECTED_ZONES]</strong> — Nord, Pas-de-Calais, Somme, Oise, Aisne (tous départements concernés par la dégradation orageuse)

<strong>[W1_MODEL_EXTRACTION_CONF]</strong> — Élevée (85%) : convergence des modèles sur le scénario de dégradation

<strong>[W1_MODEL_SCENARIO_SUPPORT]</strong> — 4 modèles sur 5 (GFS, ECMWF, ICON, ARPEGE) ; GEM en divergence partielle

<strong>[W1_MODEL_STATUS]</strong> — 🟡 Modéré — Tendances fiables à 72h, incertitudes sur les intensités orageuses

<strong>[W1_MODEL_MENTIONS_COUNT]</strong> — 12 mentions de dégradation orageuse sur les discussions

<strong>[W1_MODEL_RUN]</strong> — Run du 24/08/2026 12Z (fiable) + Run du 25/08/2026 00Z (en cours)

<strong>[W1_MODEL_TIMING]</strong> — Mercredi 26 après-midi : entrée des orages par l'ouest ; Jeudi 27 : généralisation ; Vendredi 28 : amélioration progressive

<strong>[W1_MODEL_DETAILS]</strong>
Le flux s'oriente au Sud-Ouest dès mercredi soir, avec un cisaillement modéré. Les indices CAPE deviennent significatifs (500-1000 J/kg) sur l'ensemble de la région. Le risque de phénomènes violents (grêle > 3 cm, rafales > 80 km/h) est modéré mais réel, principalement sur un axe Somme-Oise-Aisne. Le coefficient de confiance est de 4/5 pour la chronologie, 3/5 pour la localisation précise des cellules.

** | ** — Nord, Pas-de-Calais, Somme, Oise, Aisne (tous départements concernés par la dégradation orageuse)

<strong>[W1_MODEL_EXTRACTION_CONF]</strong> — Élevée (85%) : convergence des modèles sur le scénario de dégradation

<strong>[W1_MODEL_SCENARIO_SUPPORT]</strong> — 4 modèles sur 5 (GFS, ECMWF, ICON, ARPEGE) ; GEM en divergence partielle

<strong>[W1_MODEL_STATUS]</strong> — 🟡 Modéré — Tendances fiables à 72h, incertitudes sur les intensités orageuses

<strong>[W1_MODEL_MENTIONS_COUNT]</strong> — 12 mentions de dégradation orageuse sur les discussions

<strong>[W1_MODEL_RUN]</strong> — Run du 24/08/2026 12Z (fiable) + Run du 25/08/2026 00Z (en cours)

<strong>[W1_MODEL_TIMING]</strong> — Mercredi 26 après-midi : entrée des orages par l'ouest ; Jeudi 27 : généralisation ; Vendredi 28 : amélioration progressive

<strong>[W1_MODEL_DETAILS]</strong>
Le flux s'oriente au Sud-Ouest dès mercredi soir, avec un cisaillement modéré. Les indices CAPE deviennent significatifs (500-1000 J/kg) sur l'ensemble de la région. Le risque de phénomènes violents (grêle > 3 cm, rafales > 80 km/h) est modéré mais réel, principalement sur un axe Somme-Oise-Aisne. Le coefficient de confiance est de 4/5 pour la chronologie, 3/5 pour la localisation précise des cellules.

** | ** — Élevée (85%) : convergence des modèles sur le scénario de dégradation

**[W1_MODEL_SCENARIO_SUPPORT]** — 4 modèles sur 5 (GFS, ECMWF, ICON, ARPEGE) ; GEM en divergence partielle

**[W1_MODEL_STATUS]** — 🟡 Modéré — Tendances fiables à 72h, incertitudes sur les intensités orageuses

**[W1_MODEL_MENTIONS_COUNT]** — 12 mentions de dégradation orageuse sur les discussions

**[W1_MODEL_RUN]** — Run du 24/08/2026 12Z (fiable) + Run du 25/08/2026 00Z (en cours)

**[W1_MODEL_TIMING]** — Mercredi 26 après-midi : entrée des orages par l'ouest ; Jeudi 27 : généralisation ; Vendredi 28 : amélioration progressive

**[W1_MODEL_DETAILS]**
Le flux s'oriente au Sud-Ouest dès mercredi soir, avec un cisaillement modéré. Les indices CAPE deviennent significatifs (500-1000 J/kg) sur l'ensemble de la région. Le risque de phénomènes violents (grêle > 3 cm, rafales > 80 km/h) est modéré mais réel, principalement sur un axe Somme-Oise-Aisne. Le coefficient de confiance est de 4/5 pour la chronologie, 3/5 pour la localisation précise des cellules.

** | ** Le flux s'oriente au Sud-Ouest dès mercredi soir, avec un cisaillement modéré. Les indices CAPE deviennent significatifs (500-1000 J/kg) sur l'ensemble de la région. Le risque de phénomènes violents (grêle > 3 cm, rafales > 80 km/h) est modéré mais réel, principalement sur un axe Somme-Oise-Aisne. Le coefficient de confiance est de 4/5 pour la chronologie, 3/5 pour la localisation précise des cellules.  ** |

### 📍 Synthèse par zones/départements (Semaine 1)
| Zone / Département | Temps sensible | Températures | Fiabilité | Modèles | Notes d'analyse |
| --- | --- | --- | --- | --- | --- |
| **Nord (59)** | Beau temps chaud | 26°C à 32°C | Élevée | Météo-France XML, ECMWF, GFS | Validé d'après bulletins XML Meteotel |
| **Pas-de-Calais (62)** | Beau temps chaud | 26°C à 32°C | Élevée | Météo-France XML, ECMWF, GFS | Validé d'après bulletins XML Meteotel |
| **Somme (80)** | Beau temps chaud | 26°C à 32°C | Élevée | Météo-France XML, ECMWF, GFS | Validé d'après bulletins XML Meteotel |
| **Oise (60)** | Beau temps chaud | 26°C à 32°C | Élevée | Météo-France XML, ECMWF, GFS | Validé d'après bulletins XML Meteotel |
| **Aisne (02)** | Beau temps chaud | 26°C à 32°C | Élevée | Météo-France XML, ECMWF, GFS | Validé d'après bulletins XML Meteotel |

### ⏳ Déroulé chronologique (Semaine 1)
- **— Phase 1 : Mardi 25 à Jeudi 27 Août

**[W1_PHASE_1]** — Temps chaud et lourd avec montée progressive de l'instabilité, culminant avec un risque orageux marqué mercredi soir et jeudi. Températures encore estivales (26-29°C) avant la bascule.

## 🌧️ [W1_PHASE_2_DATES] — Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.

---

**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**

---

**** : ** — Temps chaud et lourd avec montée progressive de l'instabilité, culminant avec un risque orageux marqué mercredi soir et jeudi. Températures encore estivales (26-29°C) avant la bascule.

## 🌧️ [W1_PHASE_2_DATES] — Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.



**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**



**
- **— Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.

---

**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**

---

**** : ** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.



**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**



**

**Points solides :**
— Points solides (max 3)

1. **Chronologie fiable** : La séquence "beau mardi → orages mercredi/jeudi → fraîchissement vendredi" est confirmée par tous les modèles avec une haute confiance (85%).
2. **Températures en baisse** : Le passage sous les 23°C vendredi est un signal robuste, partagé par l'ensemble des simulations.
3. **Vent de Sud-Ouest** : L'installation du flux océanique est actée, avec un renforcement prévu en fin de semaine.

### ⚠️ [W1_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Caractère violent des orages** : Incertitude sur le risque de grêle et de rafales destructrices (probabilité de 25-35%).
2. **Cumuls de précipitations** : Les quantités varient fortement selon la trajectoire des cellules orageuses.
3. **Temps de dimanche** : Les modèles peinent à trancher entre averses résiduelles et retour d'éclaircies durables.

### 🔭 [W1_NEXT_RUNS_TO_WATCH] — À surveiller

- **Prochain run CEP 12Z** (ce soir) : crucial pour affiner la trajectoire des orages de jeudi
- **Run ARPEGE 06Z** (demain matin) : affinage des cumuls de pluie sur l'est de la région
- **Sorties AROME** (6h) : suivi fin de la convection de mardi après-midi



## 🌡️ [W1_PHASE_1_DATES] — Phase 1 : Mardi 25 à Jeudi 27 Août

**[W1_PHASE_1]** — Temps chaud et lourd avec montée progressive de l'instabilité, culminant avec un risque orageux marqué mercredi soir et jeudi. Températures encore estivales (26-29°C) avant la bascule.

## 🌧️ [W1_PHASE_2_DATES] — Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.



**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**



**

**Points fragiles :**
— Points fragiles (max 3)

1. **Caractère violent des orages** : Incertitude sur le risque de grêle et de rafales destructrices (probabilité de 25-35%).
2. **Cumuls de précipitations** : Les quantités varient fortement selon la trajectoire des cellules orageuses.
3. **Temps de dimanche** : Les modèles peinent à trancher entre averses résiduelles et retour d'éclaircies durables.

### 🔭 [W1_NEXT_RUNS_TO_WATCH] — À surveiller

- **Prochain run CEP 12Z** (ce soir) : crucial pour affiner la trajectoire des orages de jeudi
- **Run ARPEGE 06Z** (demain matin) : affinage des cumuls de pluie sur l'est de la région
- **Sorties AROME** (6h) : suivi fin de la convection de mardi après-midi



## 🌡️ [W1_PHASE_1_DATES] — Phase 1 : Mardi 25 à Jeudi 27 Août

**[W1_PHASE_1]** — Temps chaud et lourd avec montée progressive de l'instabilité, culminant avec un risque orageux marqué mercredi soir et jeudi. Températures encore estivales (26-29°C) avant la bascule.

## 🌧️ [W1_PHASE_2_DATES] — Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.



**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**



**

**À surveiller (prochains runs) :**
— À surveiller

- **Prochain run CEP 12Z** (ce soir) : crucial pour affiner la trajectoire des orages de jeudi
- **Run ARPEGE 06Z** (demain matin) : affinage des cumuls de pluie sur l'est de la région
- **Sorties AROME** (6h) : suivi fin de la convection de mardi après-midi



## 🌡️ [W1_PHASE_1_DATES] — Phase 1 : Mardi 25 à Jeudi 27 Août

**[W1_PHASE_1]** — Temps chaud et lourd avec montée progressive de l'instabilité, culminant avec un risque orageux marqué mercredi soir et jeudi. Températures encore estivales (26-29°C) avant la bascule.

## 🌧️ [W1_PHASE_2_DATES] — Phase 2 : Vendredi 28 à Dimanche 30 Août

**[W1_PHASE_2]** — Net rafraîchissement avec des maximales qui chutent à 20-22°C, averses résiduelles vendredi puis amélioration progressive samedi et dimanche.



**[W1_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 1 (25-30 Août 2026)            │
│                                                         │
│  MARDI 25    ⛅→⛈ (orages SO)        26-28°C           │
│  MERCREDI 26 ⛅→🌦️ (orages nuit)     27-29°C           │
│  JEUDI 27    ☁️→⛈ (orages)           24-27°C           │
│  VENDREDI 28 🌧️ (averses)            20-22°C           │
│  SAMEDI 29   ⛅ (éclaircies)          22-24°C           │
│  DIMANCHE 30 ⛅ (variable)            22-24°C           │
│                                                         │
│  💨 Vent : E → SO (rafales 55 km/h vendredi)           │
│  🌡️ T° : Min 12-19°C / Max 20-30°C                     │
│  ⚠️ Vigilance jaune orages (62/80/60/02 mardi)         │
└─────────────────────────────────────────────────────────┘
```
**[W1_IMAGE_END]**



**


## 🗓️ SEMAINE 2 : — SEMAINE 2 : Du Lundi 31 Août au Dimanche 6 Septembre 2026

### 🔑 [W2_KEY_POINT_1]
**Flux d'Ouest dépressionnaire** : La région reste sous influence océanique avec un régime de nuages et d'averses, sans retour de la canicule.

### 🌬️ [W2_KEY_POINT_2]
**Vent assez fort en début de semaine** : Rafales possibles jusqu'à 60-65 km/h lundi, particulièrement sur le littoral et le pays de Bray.

### 🌡️ [W2_KEY_POINT_3]
**Températures de saison** : Maximales comprises entre 20 et 24°C, minimales entre 12 et 15°C, conformes aux normales de début septembre.

### 🌧️ [W2_KEY_POINT_4]
**Pluies régulières mais modérées** : Risque d'averses quasi quotidien, avec des cumuls faibles à modérés (5-10 mm par épisode).

### 🔮 [W2_KEY_POINT_5]
**Incertitude fin de période** : Les modèles divergent sur un possible retour de l'anticyclone ou la poursuite du flux dépressionnaire.

---

### 📊 [W2_MODEL_START]

#### 🌐 [W2_MODEL_NAME] — Analyse des Modèles (GFS / ECMWF / ICON / CEP)

**[W2_MODEL_SCENARIO]** (max 160 car.)
Le flux d'ouest perturbé se maintient sur la France. Une dépression atlantique circule près des îles britanniques, entraînant un défilé de perturbations sur les Hauts-de-France. Les températures restent proches des normales saisonnières. En fin de période, les scénarios divergent : le CEP maintient le flux dépressionnaire, tandis que GFS propose une poussée anticyclonique par le sud-ouest. ECMWF est intermédiaire avec un talweg qui s'évacue lentement vers l'Europe centrale.

**[W2_MODEL_SENSIBLE_WEATHER]** (max 120 car.)
Ciel nuageux à couvert, averses fréquentes surtout lundi-mardi et jeudi ; éclaircies possibles mercredi et en fin de semaine.

**[W2_MODEL_AFFECTED_ZONES]** — Toute la région HDF, avec un gradient littoral/intérieur marqué (plus de vent et de pluie sur le littoral)

**[W2_MODEL_EXTRACTION_CONF]** — Moyenne (65%) : divergence croissante en fin d'échéance

**[W2_MODEL_SCENARIO_SUPPORT]** — 3 modèles sur 5 (CEP, ECMWF, ICON) pour le maintien du flux d'ouest ; GFS en divergence

**[W2_MODEL_STATUS]** — 🟡 Modéré — Tendances générales fiables, détails incertains au-delà de jeudi

**[W2_MODEL_MENTIONS_COUNT]** — 8 mentions de flux d'ouest et d'incertitude sur les discussions

**[W2_MODEL_RUN]** — Run du 25/08/2026 00Z (vision d'ensemble)

**[W2_MODEL_TIMING]** — Lundi-mardi : perturbation active ; Mercredi : accalmie relative ; Jeudi : nouvelle dégradation ; Week-end : indécis

**[W2_MODEL_DETAILS]**
La position du jet stream est déterminante : si son axe se décale au nord (scénario GFS), la région bénéficie d'une amélioration ; s'il reste sur la France (scénario CEP), les averses persistent. Le signal ENSO et l'activité tropicale (cyclone potentiel) pourraient influencer cette évolution à 10-14 jours. Les températures resteront proches des normales dans tous les scénarios (± 1-2°C).

**[W2_MODEL_END]**

---

### ✅ [W2_CONVERGENCES] — Points de convergence (max 3)

1. **Absence de canicule** : Aucun scénario ne propose un retour des fortes chaleurs (> 30°C) durant cette période.
2. **Températures de saison** : Consensus sur des maximales entre 20-24°C et minimales entre 12-15°C.
3. **Risque d'averses régulier** : Tous les modèles maintiennent un risque de précipitations quasi quotidien.

### ⚠️ [W2_DIVERGENCES] — Points de divergence (max 3)

1. **Fin de période** : GFS propose une remontée anticyclonique dès samedi, CEP maintient le flux dépressionnaire.
2. **Vent** : L'épisode venteux de lundi est confirmé, mais son intensité varie (60-75 km/h selon les modèles).
3. **Cumuls pluviométriques** : Les quantités prévues varient de 10 à 30 mm sur la semaine selon les scénarios.

---

### 📝 [W2_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi et mardi, éclaircies mercredi, retour des averses jeudi, variable en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Risque d'averses modérées, cumuls de 5-10 mm par épisode, orages possibles lundi après-midi",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Ouest-Sud-Ouest assez fort lundi (rafales 60 km/h en Flandres), modéré ensuite",
      "sensitive_period": "Lundi (vent fort et averses), jeudi (dégradation)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end (amélioration ou persistance des averses ?)",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Averses fréquentes lundi-mardi, éclaircies mercredi, dégradation jeudi, amélioration samedi-dimanche",
      "temperatures": "Min 12-15°C, Max 20-23°C (19-21°C littoral)",
      "rain_storms": "Risque d'averses marines, cumuls 5-8 mm sur le littoral, vent assez fort lundi",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Sud-Ouest assez fort lundi (rafales 65 km/h littoral), plus modéré ensuite",
      "sensitive_period": "Lundi (vent fort littoral), jeudi (pluies)",
      "confidence_level": "moderee",
      "uncertainty": "Intensité du vent en début de semaine et évolution du week-end",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi, variable mardi-mercredi, pluies jeudi, éclaircies possibles en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Averses modérées, cumuls 5-10 mm, vent assez fort lundi sur le littoral picard",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Ouest assez fort lundi (rafales 60 km/h nord du département), Sud-Ouest modéré ensuite",
      "sensitive_period": "Lundi (vent et averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, possibilité d'amélioration",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Averses lundi, nette amélioration mercredi, dégradation jeudi, incertitude en fin de semaine",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées lundi et jeudi, cumuls 5-10 mm, vent assez fort lundi sur le pays de Bray",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Ouest-Sud-Ouest assez fort lundi matin (rafales 55-60 km/h), modéré ensuite",
      "sensitive_period": "Lundi matin (vent), jeudi (dégradation pluvieuse)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end et possible retour anticyclonique",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Averses lundi et mardi, éclaircies mercredi, pluies jeudi, amélioration samedi-dimanche (scénario GFS)",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées, cumuls 5-8 mm, risque orageux faible lundi après-midi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Ouest à Sud-Ouest temporairement modéré, rafales possibles 50 km/h lundi",
      "sensitive_period": "Lundi (averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, scénario GFS plus sec que CEP",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W2_ZONES_JSON_END]

### 💪 [W2_SOLID_POINTS] — Points solides (max 3)

1. **Températures de saison** : Fort consensus sur des valeurs proches des normales (20-24°C), sans excès ni déficit marqué.
2. **Flux d'ouest** : Le régime perturbé est acté pour au moins la première partie de la semaine.
3. **Vent lundi** : Épisode venteux confirmé avec rafales de 55-65 km/h sur l'ouest de la région.

### ⚠️ [W2_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Fin de période très incertaine** : Oppositions marquées entre GFS (amélioration) et CEP (poursuite du flux dépressionnaire).
2. **Quantités de pluie** : Les cumuls varient du simple au triple selon les scénarios (10 à 30 mm sur la semaine).
3. **Position du jet** : Un décalage de quelques degrés de latitude change radicalement le temps prévu.

### 🔭 [W2_NEXT_RUNS_TO_WATCH] — À surveiller

- **Run CEP 12Z** (ce soir) : déterminant pour trancher le scénario du week-end
- **Sorties GFS ensemble** (nuit) : évaluation de la confiance dans la remontée anticyclonique
- **Bulletin Météo-France J+7** (jeudi) : affinage de la prévision à 10 jours

---

## 🌦️ [W2_PHASE_1_DATES] — Phase 1 : Lundi 31 Août à Mercredi 3 Septembre

**[W2_PHASE_1]** — Régime dépressionnaire actif avec vent assez fort lundi et averses fréquentes. Amélioration relative mercredi avec de belles éclaircies entre les passages nuageux. Températures de saison (20-23°C).

## ⛅ [W2_PHASE_2_DATES] — Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.

---

**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**

---

**
### 💡 Points clés de la semaine 2
1. **Flux d'Ouest dépressionnaire** : La région reste sous influence océanique avec un régime de nuages et d'averses, sans retour de la canicule.

### 🌬️ [W2_KEY_POINT_2]
**Vent assez fort en début de semaine** : Rafales possibles jusqu'à 60-65 km/h lundi, particulièrement sur le littoral et le pays de Bray.

### 🌡️ [W2_KEY_POINT_3]
**Températures de saison** : Maximales comprises entre 20 et 24°C, minimales entre 12 et 15°C, conformes aux normales de début septembre.

### 🌧️ [W2_KEY_POINT_4]
**Pluies régulières mais modérées** : Risque d'averses quasi quotidien, avec des cumuls faibles à modérés (5-10 mm par épisode).

### 🔮 [W2_KEY_POINT_5]
**Incertitude fin de période** : Les modèles divergent sur un possible retour de l'anticyclone ou la poursuite du flux dépressionnaire.



### 📊 [W2_MODEL_START]

#### 🌐 [W2_MODEL_NAME] — Analyse des Modèles (GFS / ECMWF / ICON / CEP)

**[W2_MODEL_SCENARIO]** (max 160 car.)
Le flux d'ouest perturbé se maintient sur la France. Une dépression atlantique circule près des îles britanniques, entraînant un défilé de perturbations sur les Hauts-de-France. Les températures restent proches des normales saisonnières. En fin de période, les scénarios divergent : le CEP maintient le flux dépressionnaire, tandis que GFS propose une poussée anticyclonique par le sud-ouest. ECMWF est intermédiaire avec un talweg qui s'évacue lentement vers l'Europe centrale.

**[W2_MODEL_SENSIBLE_WEATHER]** (max 120 car.)
Ciel nuageux à couvert, averses fréquentes surtout lundi-mardi et jeudi ; éclaircies possibles mercredi et en fin de semaine.

**[W2_MODEL_AFFECTED_ZONES]** — Toute la région HDF, avec un gradient littoral/intérieur marqué (plus de vent et de pluie sur le littoral)

**[W2_MODEL_EXTRACTION_CONF]** — Moyenne (65%) : divergence croissante en fin d'échéance

**[W2_MODEL_SCENARIO_SUPPORT]** — 3 modèles sur 5 (CEP, ECMWF, ICON) pour le maintien du flux d'ouest ; GFS en divergence

**[W2_MODEL_STATUS]** — 🟡 Modéré — Tendances générales fiables, détails incertains au-delà de jeudi

**[W2_MODEL_MENTIONS_COUNT]** — 8 mentions de flux d'ouest et d'incertitude sur les discussions

**[W2_MODEL_RUN]** — Run du 25/08/2026 00Z (vision d'ensemble)

**[W2_MODEL_TIMING]** — Lundi-mardi : perturbation active ; Mercredi : accalmie relative ; Jeudi : nouvelle dégradation ; Week-end : indécis

**[W2_MODEL_DETAILS]**
La position du jet stream est déterminante : si son axe se décale au nord (scénario GFS), la région bénéficie d'une amélioration ; s'il reste sur la France (scénario CEP), les averses persistent. Le signal ENSO et l'activité tropicale (cyclone potentiel) pourraient influencer cette évolution à 10-14 jours. Les températures resteront proches des normales dans tous les scénarios (± 1-2°C).

**[W2_MODEL_END]**



### ✅ [W2_CONVERGENCES] — Points de convergence (max 3)

1. **Absence de canicule** : Aucun scénario ne propose un retour des fortes chaleurs (> 30°C) durant cette période.
2. **Températures de saison** : Consensus sur des maximales entre 20-24°C et minimales entre 12-15°C.
3. **Risque d'averses régulier** : Tous les modèles maintiennent un risque de précipitations quasi quotidien.

### ⚠️ [W2_DIVERGENCES] — Points de divergence (max 3)

1. **Fin de période** : GFS propose une remontée anticyclonique dès samedi, CEP maintient le flux dépressionnaire.
2. **Vent** : L'épisode venteux de lundi est confirmé, mais son intensité varie (60-75 km/h selon les modèles).
3. **Cumuls pluviométriques** : Les quantités prévues varient de 10 à 30 mm sur la semaine selon les scénarios.



### 📝 [W2_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi et mardi, éclaircies mercredi, retour des averses jeudi, variable en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Risque d'averses modérées, cumuls de 5-10 mm par épisode, orages possibles lundi après-midi",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Ouest-Sud-Ouest assez fort lundi (rafales 60 km/h en Flandres), modéré ensuite",
      "sensitive_period": "Lundi (vent fort et averses), jeudi (dégradation)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end (amélioration ou persistance des averses ?)",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Averses fréquentes lundi-mardi, éclaircies mercredi, dégradation jeudi, amélioration samedi-dimanche",
      "temperatures": "Min 12-15°C, Max 20-23°C (19-21°C littoral)",
      "rain_storms": "Risque d'averses marines, cumuls 5-8 mm sur le littoral, vent assez fort lundi",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Sud-Ouest assez fort lundi (rafales 65 km/h littoral), plus modéré ensuite",
      "sensitive_period": "Lundi (vent fort littoral), jeudi (pluies)",
      "confidence_level": "moderee",
      "uncertainty": "Intensité du vent en début de semaine et évolution du week-end",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi, variable mardi-mercredi, pluies jeudi, éclaircies possibles en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Averses modérées, cumuls 5-10 mm, vent assez fort lundi sur le littoral picard",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Ouest assez fort lundi (rafales 60 km/h nord du département), Sud-Ouest modéré ensuite",
      "sensitive_period": "Lundi (vent et averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, possibilité d'amélioration",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Averses lundi, nette amélioration mercredi, dégradation jeudi, incertitude en fin de semaine",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées lundi et jeudi, cumuls 5-10 mm, vent assez fort lundi sur le pays de Bray",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Ouest-Sud-Ouest assez fort lundi matin (rafales 55-60 km/h), modéré ensuite",
      "sensitive_period": "Lundi matin (vent), jeudi (dégradation pluvieuse)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end et possible retour anticyclonique",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Averses lundi et mardi, éclaircies mercredi, pluies jeudi, amélioration samedi-dimanche (scénario GFS)",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées, cumuls 5-8 mm, risque orageux faible lundi après-midi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Ouest à Sud-Ouest temporairement modéré, rafales possibles 50 km/h lundi",
      "sensitive_period": "Lundi (averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, scénario GFS plus sec que CEP",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W2_ZONES_JSON_END]

### 💪 [W2_SOLID_POINTS] — Points solides (max 3)

1. **Températures de saison** : Fort consensus sur des valeurs proches des normales (20-24°C), sans excès ni déficit marqué.
2. **Flux d'ouest** : Le régime perturbé est acté pour au moins la première partie de la semaine.
3. **Vent lundi** : Épisode venteux confirmé avec rafales de 55-65 km/h sur l'ouest de la région.

### ⚠️ [W2_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Fin de période très incertaine** : Oppositions marquées entre GFS (amélioration) et CEP (poursuite du flux dépressionnaire).
2. **Quantités de pluie** : Les cumuls varient du simple au triple selon les scénarios (10 à 30 mm sur la semaine).
3. **Position du jet** : Un décalage de quelques degrés de latitude change radicalement le temps prévu.

### 🔭 [W2_NEXT_RUNS_TO_WATCH] — À surveiller

- **Run CEP 12Z** (ce soir) : déterminant pour trancher le scénario du week-end
- **Sorties GFS ensemble** (nuit) : évaluation de la confiance dans la remontée anticyclonique
- **Bulletin Météo-France J+7** (jeudi) : affinage de la prévision à 10 jours



## 🌦️ [W2_PHASE_1_DATES] — Phase 1 : Lundi 31 Août à Mercredi 3 Septembre

**[W2_PHASE_1]** — Régime dépressionnaire actif avec vent assez fort lundi et averses fréquentes. Amélioration relative mercredi avec de belles éclaircies entre les passages nuageux. Températures de saison (20-23°C).

## ⛅ [W2_PHASE_2_DATES] — Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.



**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**



**
2. **Vent assez fort en début de semaine** : Rafales possibles jusqu'à 60-65 km/h lundi, particulièrement sur le littoral et le pays de Bray.

### 🌡️ [W2_KEY_POINT_3]
**Températures de saison** : Maximales comprises entre 20 et 24°C, minimales entre 12 et 15°C, conformes aux normales de début septembre.

### 🌧️ [W2_KEY_POINT_4]
**Pluies régulières mais modérées** : Risque d'averses quasi quotidien, avec des cumuls faibles à modérés (5-10 mm par épisode).

### 🔮 [W2_KEY_POINT_5]
**Incertitude fin de période** : Les modèles divergent sur un possible retour de l'anticyclone ou la poursuite du flux dépressionnaire.



### 📊 [W2_MODEL_START]

#### 🌐 [W2_MODEL_NAME] — Analyse des Modèles (GFS / ECMWF / ICON / CEP)

**[W2_MODEL_SCENARIO]** (max 160 car.)
Le flux d'ouest perturbé se maintient sur la France. Une dépression atlantique circule près des îles britanniques, entraînant un défilé de perturbations sur les Hauts-de-France. Les températures restent proches des normales saisonnières. En fin de période, les scénarios divergent : le CEP maintient le flux dépressionnaire, tandis que GFS propose une poussée anticyclonique par le sud-ouest. ECMWF est intermédiaire avec un talweg qui s'évacue lentement vers l'Europe centrale.

**[W2_MODEL_SENSIBLE_WEATHER]** (max 120 car.)
Ciel nuageux à couvert, averses fréquentes surtout lundi-mardi et jeudi ; éclaircies possibles mercredi et en fin de semaine.

**[W2_MODEL_AFFECTED_ZONES]** — Toute la région HDF, avec un gradient littoral/intérieur marqué (plus de vent et de pluie sur le littoral)

**[W2_MODEL_EXTRACTION_CONF]** — Moyenne (65%) : divergence croissante en fin d'échéance

**[W2_MODEL_SCENARIO_SUPPORT]** — 3 modèles sur 5 (CEP, ECMWF, ICON) pour le maintien du flux d'ouest ; GFS en divergence

**[W2_MODEL_STATUS]** — 🟡 Modéré — Tendances générales fiables, détails incertains au-delà de jeudi

**[W2_MODEL_MENTIONS_COUNT]** — 8 mentions de flux d'ouest et d'incertitude sur les discussions

**[W2_MODEL_RUN]** — Run du 25/08/2026 00Z (vision d'ensemble)

**[W2_MODEL_TIMING]** — Lundi-mardi : perturbation active ; Mercredi : accalmie relative ; Jeudi : nouvelle dégradation ; Week-end : indécis

**[W2_MODEL_DETAILS]**
La position du jet stream est déterminante : si son axe se décale au nord (scénario GFS), la région bénéficie d'une amélioration ; s'il reste sur la France (scénario CEP), les averses persistent. Le signal ENSO et l'activité tropicale (cyclone potentiel) pourraient influencer cette évolution à 10-14 jours. Les températures resteront proches des normales dans tous les scénarios (± 1-2°C).

**[W2_MODEL_END]**



### ✅ [W2_CONVERGENCES] — Points de convergence (max 3)

1. **Absence de canicule** : Aucun scénario ne propose un retour des fortes chaleurs (> 30°C) durant cette période.
2. **Températures de saison** : Consensus sur des maximales entre 20-24°C et minimales entre 12-15°C.
3. **Risque d'averses régulier** : Tous les modèles maintiennent un risque de précipitations quasi quotidien.

### ⚠️ [W2_DIVERGENCES] — Points de divergence (max 3)

1. **Fin de période** : GFS propose une remontée anticyclonique dès samedi, CEP maintient le flux dépressionnaire.
2. **Vent** : L'épisode venteux de lundi est confirmé, mais son intensité varie (60-75 km/h selon les modèles).
3. **Cumuls pluviométriques** : Les quantités prévues varient de 10 à 30 mm sur la semaine selon les scénarios.



### 📝 [W2_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi et mardi, éclaircies mercredi, retour des averses jeudi, variable en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Risque d'averses modérées, cumuls de 5-10 mm par épisode, orages possibles lundi après-midi",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Ouest-Sud-Ouest assez fort lundi (rafales 60 km/h en Flandres), modéré ensuite",
      "sensitive_period": "Lundi (vent fort et averses), jeudi (dégradation)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end (amélioration ou persistance des averses ?)",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Averses fréquentes lundi-mardi, éclaircies mercredi, dégradation jeudi, amélioration samedi-dimanche",
      "temperatures": "Min 12-15°C, Max 20-23°C (19-21°C littoral)",
      "rain_storms": "Risque d'averses marines, cumuls 5-8 mm sur le littoral, vent assez fort lundi",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Sud-Ouest assez fort lundi (rafales 65 km/h littoral), plus modéré ensuite",
      "sensitive_period": "Lundi (vent fort littoral), jeudi (pluies)",
      "confidence_level": "moderee",
      "uncertainty": "Intensité du vent en début de semaine et évolution du week-end",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi, variable mardi-mercredi, pluies jeudi, éclaircies possibles en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Averses modérées, cumuls 5-10 mm, vent assez fort lundi sur le littoral picard",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Ouest assez fort lundi (rafales 60 km/h nord du département), Sud-Ouest modéré ensuite",
      "sensitive_period": "Lundi (vent et averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, possibilité d'amélioration",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Averses lundi, nette amélioration mercredi, dégradation jeudi, incertitude en fin de semaine",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées lundi et jeudi, cumuls 5-10 mm, vent assez fort lundi sur le pays de Bray",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Ouest-Sud-Ouest assez fort lundi matin (rafales 55-60 km/h), modéré ensuite",
      "sensitive_period": "Lundi matin (vent), jeudi (dégradation pluvieuse)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end et possible retour anticyclonique",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Averses lundi et mardi, éclaircies mercredi, pluies jeudi, amélioration samedi-dimanche (scénario GFS)",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées, cumuls 5-8 mm, risque orageux faible lundi après-midi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Ouest à Sud-Ouest temporairement modéré, rafales possibles 50 km/h lundi",
      "sensitive_period": "Lundi (averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, scénario GFS plus sec que CEP",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W2_ZONES_JSON_END]

### 💪 [W2_SOLID_POINTS] — Points solides (max 3)

1. **Températures de saison** : Fort consensus sur des valeurs proches des normales (20-24°C), sans excès ni déficit marqué.
2. **Flux d'ouest** : Le régime perturbé est acté pour au moins la première partie de la semaine.
3. **Vent lundi** : Épisode venteux confirmé avec rafales de 55-65 km/h sur l'ouest de la région.

### ⚠️ [W2_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Fin de période très incertaine** : Oppositions marquées entre GFS (amélioration) et CEP (poursuite du flux dépressionnaire).
2. **Quantités de pluie** : Les cumuls varient du simple au triple selon les scénarios (10 à 30 mm sur la semaine).
3. **Position du jet** : Un décalage de quelques degrés de latitude change radicalement le temps prévu.

### 🔭 [W2_NEXT_RUNS_TO_WATCH] — À surveiller

- **Run CEP 12Z** (ce soir) : déterminant pour trancher le scénario du week-end
- **Sorties GFS ensemble** (nuit) : évaluation de la confiance dans la remontée anticyclonique
- **Bulletin Météo-France J+7** (jeudi) : affinage de la prévision à 10 jours



## 🌦️ [W2_PHASE_1_DATES] — Phase 1 : Lundi 31 Août à Mercredi 3 Septembre

**[W2_PHASE_1]** — Régime dépressionnaire actif avec vent assez fort lundi et averses fréquentes. Amélioration relative mercredi avec de belles éclaircies entre les passages nuageux. Températures de saison (20-23°C).

## ⛅ [W2_PHASE_2_DATES] — Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.



**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**



**
3. **Températures de saison** : Maximales comprises entre 20 et 24°C, minimales entre 12 et 15°C, conformes aux normales de début septembre.

### 🌧️ [W2_KEY_POINT_4]
**Pluies régulières mais modérées** : Risque d'averses quasi quotidien, avec des cumuls faibles à modérés (5-10 mm par épisode).

### 🔮 [W2_KEY_POINT_5]
**Incertitude fin de période** : Les modèles divergent sur un possible retour de l'anticyclone ou la poursuite du flux dépressionnaire.



### 📊 [W2_MODEL_START]

#### 🌐 [W2_MODEL_NAME] — Analyse des Modèles (GFS / ECMWF / ICON / CEP)

**[W2_MODEL_SCENARIO]** (max 160 car.)
Le flux d'ouest perturbé se maintient sur la France. Une dépression atlantique circule près des îles britanniques, entraînant un défilé de perturbations sur les Hauts-de-France. Les températures restent proches des normales saisonnières. En fin de période, les scénarios divergent : le CEP maintient le flux dépressionnaire, tandis que GFS propose une poussée anticyclonique par le sud-ouest. ECMWF est intermédiaire avec un talweg qui s'évacue lentement vers l'Europe centrale.

**[W2_MODEL_SENSIBLE_WEATHER]** (max 120 car.)
Ciel nuageux à couvert, averses fréquentes surtout lundi-mardi et jeudi ; éclaircies possibles mercredi et en fin de semaine.

**[W2_MODEL_AFFECTED_ZONES]** — Toute la région HDF, avec un gradient littoral/intérieur marqué (plus de vent et de pluie sur le littoral)

**[W2_MODEL_EXTRACTION_CONF]** — Moyenne (65%) : divergence croissante en fin d'échéance

**[W2_MODEL_SCENARIO_SUPPORT]** — 3 modèles sur 5 (CEP, ECMWF, ICON) pour le maintien du flux d'ouest ; GFS en divergence

**[W2_MODEL_STATUS]** — 🟡 Modéré — Tendances générales fiables, détails incertains au-delà de jeudi

**[W2_MODEL_MENTIONS_COUNT]** — 8 mentions de flux d'ouest et d'incertitude sur les discussions

**[W2_MODEL_RUN]** — Run du 25/08/2026 00Z (vision d'ensemble)

**[W2_MODEL_TIMING]** — Lundi-mardi : perturbation active ; Mercredi : accalmie relative ; Jeudi : nouvelle dégradation ; Week-end : indécis

**[W2_MODEL_DETAILS]**
La position du jet stream est déterminante : si son axe se décale au nord (scénario GFS), la région bénéficie d'une amélioration ; s'il reste sur la France (scénario CEP), les averses persistent. Le signal ENSO et l'activité tropicale (cyclone potentiel) pourraient influencer cette évolution à 10-14 jours. Les températures resteront proches des normales dans tous les scénarios (± 1-2°C).

**[W2_MODEL_END]**



### ✅ [W2_CONVERGENCES] — Points de convergence (max 3)

1. **Absence de canicule** : Aucun scénario ne propose un retour des fortes chaleurs (> 30°C) durant cette période.
2. **Températures de saison** : Consensus sur des maximales entre 20-24°C et minimales entre 12-15°C.
3. **Risque d'averses régulier** : Tous les modèles maintiennent un risque de précipitations quasi quotidien.

### ⚠️ [W2_DIVERGENCES] — Points de divergence (max 3)

1. **Fin de période** : GFS propose une remontée anticyclonique dès samedi, CEP maintient le flux dépressionnaire.
2. **Vent** : L'épisode venteux de lundi est confirmé, mais son intensité varie (60-75 km/h selon les modèles).
3. **Cumuls pluviométriques** : Les quantités prévues varient de 10 à 30 mm sur la semaine selon les scénarios.



### 📝 [W2_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi et mardi, éclaircies mercredi, retour des averses jeudi, variable en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Risque d'averses modérées, cumuls de 5-10 mm par épisode, orages possibles lundi après-midi",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Ouest-Sud-Ouest assez fort lundi (rafales 60 km/h en Flandres), modéré ensuite",
      "sensitive_period": "Lundi (vent fort et averses), jeudi (dégradation)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end (amélioration ou persistance des averses ?)",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Averses fréquentes lundi-mardi, éclaircies mercredi, dégradation jeudi, amélioration samedi-dimanche",
      "temperatures": "Min 12-15°C, Max 20-23°C (19-21°C littoral)",
      "rain_storms": "Risque d'averses marines, cumuls 5-8 mm sur le littoral, vent assez fort lundi",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Sud-Ouest assez fort lundi (rafales 65 km/h littoral), plus modéré ensuite",
      "sensitive_period": "Lundi (vent fort littoral), jeudi (pluies)",
      "confidence_level": "moderee",
      "uncertainty": "Intensité du vent en début de semaine et évolution du week-end",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi, variable mardi-mercredi, pluies jeudi, éclaircies possibles en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Averses modérées, cumuls 5-10 mm, vent assez fort lundi sur le littoral picard",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Ouest assez fort lundi (rafales 60 km/h nord du département), Sud-Ouest modéré ensuite",
      "sensitive_period": "Lundi (vent et averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, possibilité d'amélioration",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Averses lundi, nette amélioration mercredi, dégradation jeudi, incertitude en fin de semaine",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées lundi et jeudi, cumuls 5-10 mm, vent assez fort lundi sur le pays de Bray",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Ouest-Sud-Ouest assez fort lundi matin (rafales 55-60 km/h), modéré ensuite",
      "sensitive_period": "Lundi matin (vent), jeudi (dégradation pluvieuse)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end et possible retour anticyclonique",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Averses lundi et mardi, éclaircies mercredi, pluies jeudi, amélioration samedi-dimanche (scénario GFS)",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées, cumuls 5-8 mm, risque orageux faible lundi après-midi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Ouest à Sud-Ouest temporairement modéré, rafales possibles 50 km/h lundi",
      "sensitive_period": "Lundi (averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, scénario GFS plus sec que CEP",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W2_ZONES_JSON_END]

### 💪 [W2_SOLID_POINTS] — Points solides (max 3)

1. **Températures de saison** : Fort consensus sur des valeurs proches des normales (20-24°C), sans excès ni déficit marqué.
2. **Flux d'ouest** : Le régime perturbé est acté pour au moins la première partie de la semaine.
3. **Vent lundi** : Épisode venteux confirmé avec rafales de 55-65 km/h sur l'ouest de la région.

### ⚠️ [W2_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Fin de période très incertaine** : Oppositions marquées entre GFS (amélioration) et CEP (poursuite du flux dépressionnaire).
2. **Quantités de pluie** : Les cumuls varient du simple au triple selon les scénarios (10 à 30 mm sur la semaine).
3. **Position du jet** : Un décalage de quelques degrés de latitude change radicalement le temps prévu.

### 🔭 [W2_NEXT_RUNS_TO_WATCH] — À surveiller

- **Run CEP 12Z** (ce soir) : déterminant pour trancher le scénario du week-end
- **Sorties GFS ensemble** (nuit) : évaluation de la confiance dans la remontée anticyclonique
- **Bulletin Météo-France J+7** (jeudi) : affinage de la prévision à 10 jours



## 🌦️ [W2_PHASE_1_DATES] — Phase 1 : Lundi 31 Août à Mercredi 3 Septembre

**[W2_PHASE_1]** — Régime dépressionnaire actif avec vent assez fort lundi et averses fréquentes. Amélioration relative mercredi avec de belles éclaircies entre les passages nuageux. Températures de saison (20-23°C).

## ⛅ [W2_PHASE_2_DATES] — Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.



**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**



**
4. **Pluies régulières mais modérées** : Risque d'averses quasi quotidien, avec des cumuls faibles à modérés (5-10 mm par épisode).

### 🔮 [W2_KEY_POINT_5]
**Incertitude fin de période** : Les modèles divergent sur un possible retour de l'anticyclone ou la poursuite du flux dépressionnaire.



### 📊 [W2_MODEL_START]

#### 🌐 [W2_MODEL_NAME] — Analyse des Modèles (GFS / ECMWF / ICON / CEP)

**[W2_MODEL_SCENARIO]** (max 160 car.)
Le flux d'ouest perturbé se maintient sur la France. Une dépression atlantique circule près des îles britanniques, entraînant un défilé de perturbations sur les Hauts-de-France. Les températures restent proches des normales saisonnières. En fin de période, les scénarios divergent : le CEP maintient le flux dépressionnaire, tandis que GFS propose une poussée anticyclonique par le sud-ouest. ECMWF est intermédiaire avec un talweg qui s'évacue lentement vers l'Europe centrale.

**[W2_MODEL_SENSIBLE_WEATHER]** (max 120 car.)
Ciel nuageux à couvert, averses fréquentes surtout lundi-mardi et jeudi ; éclaircies possibles mercredi et en fin de semaine.

**[W2_MODEL_AFFECTED_ZONES]** — Toute la région HDF, avec un gradient littoral/intérieur marqué (plus de vent et de pluie sur le littoral)

**[W2_MODEL_EXTRACTION_CONF]** — Moyenne (65%) : divergence croissante en fin d'échéance

**[W2_MODEL_SCENARIO_SUPPORT]** — 3 modèles sur 5 (CEP, ECMWF, ICON) pour le maintien du flux d'ouest ; GFS en divergence

**[W2_MODEL_STATUS]** — 🟡 Modéré — Tendances générales fiables, détails incertains au-delà de jeudi

**[W2_MODEL_MENTIONS_COUNT]** — 8 mentions de flux d'ouest et d'incertitude sur les discussions

**[W2_MODEL_RUN]** — Run du 25/08/2026 00Z (vision d'ensemble)

**[W2_MODEL_TIMING]** — Lundi-mardi : perturbation active ; Mercredi : accalmie relative ; Jeudi : nouvelle dégradation ; Week-end : indécis

**[W2_MODEL_DETAILS]**
La position du jet stream est déterminante : si son axe se décale au nord (scénario GFS), la région bénéficie d'une amélioration ; s'il reste sur la France (scénario CEP), les averses persistent. Le signal ENSO et l'activité tropicale (cyclone potentiel) pourraient influencer cette évolution à 10-14 jours. Les températures resteront proches des normales dans tous les scénarios (± 1-2°C).

**[W2_MODEL_END]**



### ✅ [W2_CONVERGENCES] — Points de convergence (max 3)

1. **Absence de canicule** : Aucun scénario ne propose un retour des fortes chaleurs (> 30°C) durant cette période.
2. **Températures de saison** : Consensus sur des maximales entre 20-24°C et minimales entre 12-15°C.
3. **Risque d'averses régulier** : Tous les modèles maintiennent un risque de précipitations quasi quotidien.

### ⚠️ [W2_DIVERGENCES] — Points de divergence (max 3)

1. **Fin de période** : GFS propose une remontée anticyclonique dès samedi, CEP maintient le flux dépressionnaire.
2. **Vent** : L'épisode venteux de lundi est confirmé, mais son intensité varie (60-75 km/h selon les modèles).
3. **Cumuls pluviométriques** : Les quantités prévues varient de 10 à 30 mm sur la semaine selon les scénarios.



### 📝 [W2_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi et mardi, éclaircies mercredi, retour des averses jeudi, variable en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Risque d'averses modérées, cumuls de 5-10 mm par épisode, orages possibles lundi après-midi",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Ouest-Sud-Ouest assez fort lundi (rafales 60 km/h en Flandres), modéré ensuite",
      "sensitive_period": "Lundi (vent fort et averses), jeudi (dégradation)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end (amélioration ou persistance des averses ?)",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Averses fréquentes lundi-mardi, éclaircies mercredi, dégradation jeudi, amélioration samedi-dimanche",
      "temperatures": "Min 12-15°C, Max 20-23°C (19-21°C littoral)",
      "rain_storms": "Risque d'averses marines, cumuls 5-8 mm sur le littoral, vent assez fort lundi",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Sud-Ouest assez fort lundi (rafales 65 km/h littoral), plus modéré ensuite",
      "sensitive_period": "Lundi (vent fort littoral), jeudi (pluies)",
      "confidence_level": "moderee",
      "uncertainty": "Intensité du vent en début de semaine et évolution du week-end",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi, variable mardi-mercredi, pluies jeudi, éclaircies possibles en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Averses modérées, cumuls 5-10 mm, vent assez fort lundi sur le littoral picard",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Ouest assez fort lundi (rafales 60 km/h nord du département), Sud-Ouest modéré ensuite",
      "sensitive_period": "Lundi (vent et averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, possibilité d'amélioration",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Averses lundi, nette amélioration mercredi, dégradation jeudi, incertitude en fin de semaine",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées lundi et jeudi, cumuls 5-10 mm, vent assez fort lundi sur le pays de Bray",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Ouest-Sud-Ouest assez fort lundi matin (rafales 55-60 km/h), modéré ensuite",
      "sensitive_period": "Lundi matin (vent), jeudi (dégradation pluvieuse)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end et possible retour anticyclonique",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Averses lundi et mardi, éclaircies mercredi, pluies jeudi, amélioration samedi-dimanche (scénario GFS)",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées, cumuls 5-8 mm, risque orageux faible lundi après-midi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Ouest à Sud-Ouest temporairement modéré, rafales possibles 50 km/h lundi",
      "sensitive_period": "Lundi (averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, scénario GFS plus sec que CEP",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W2_ZONES_JSON_END]

### 💪 [W2_SOLID_POINTS] — Points solides (max 3)

1. **Températures de saison** : Fort consensus sur des valeurs proches des normales (20-24°C), sans excès ni déficit marqué.
2. **Flux d'ouest** : Le régime perturbé est acté pour au moins la première partie de la semaine.
3. **Vent lundi** : Épisode venteux confirmé avec rafales de 55-65 km/h sur l'ouest de la région.

### ⚠️ [W2_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Fin de période très incertaine** : Oppositions marquées entre GFS (amélioration) et CEP (poursuite du flux dépressionnaire).
2. **Quantités de pluie** : Les cumuls varient du simple au triple selon les scénarios (10 à 30 mm sur la semaine).
3. **Position du jet** : Un décalage de quelques degrés de latitude change radicalement le temps prévu.

### 🔭 [W2_NEXT_RUNS_TO_WATCH] — À surveiller

- **Run CEP 12Z** (ce soir) : déterminant pour trancher le scénario du week-end
- **Sorties GFS ensemble** (nuit) : évaluation de la confiance dans la remontée anticyclonique
- **Bulletin Météo-France J+7** (jeudi) : affinage de la prévision à 10 jours



## 🌦️ [W2_PHASE_1_DATES] — Phase 1 : Lundi 31 Août à Mercredi 3 Septembre

**[W2_PHASE_1]** — Régime dépressionnaire actif avec vent assez fort lundi et averses fréquentes. Amélioration relative mercredi avec de belles éclaircies entre les passages nuageux. Températures de saison (20-23°C).

## ⛅ [W2_PHASE_2_DATES] — Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.



**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**



**
5. **Incertitude fin de période** : Les modèles divergent sur un possible retour de l'anticyclone ou la poursuite du flux dépressionnaire.



### 📊 [W2_MODEL_START]

#### 🌐 [W2_MODEL_NAME] — Analyse des Modèles (GFS / ECMWF / ICON / CEP)

**[W2_MODEL_SCENARIO]** (max 160 car.)
Le flux d'ouest perturbé se maintient sur la France. Une dépression atlantique circule près des îles britanniques, entraînant un défilé de perturbations sur les Hauts-de-France. Les températures restent proches des normales saisonnières. En fin de période, les scénarios divergent : le CEP maintient le flux dépressionnaire, tandis que GFS propose une poussée anticyclonique par le sud-ouest. ECMWF est intermédiaire avec un talweg qui s'évacue lentement vers l'Europe centrale.

**[W2_MODEL_SENSIBLE_WEATHER]** (max 120 car.)
Ciel nuageux à couvert, averses fréquentes surtout lundi-mardi et jeudi ; éclaircies possibles mercredi et en fin de semaine.

**[W2_MODEL_AFFECTED_ZONES]** — Toute la région HDF, avec un gradient littoral/intérieur marqué (plus de vent et de pluie sur le littoral)

**[W2_MODEL_EXTRACTION_CONF]** — Moyenne (65%) : divergence croissante en fin d'échéance

**[W2_MODEL_SCENARIO_SUPPORT]** — 3 modèles sur 5 (CEP, ECMWF, ICON) pour le maintien du flux d'ouest ; GFS en divergence

**[W2_MODEL_STATUS]** — 🟡 Modéré — Tendances générales fiables, détails incertains au-delà de jeudi

**[W2_MODEL_MENTIONS_COUNT]** — 8 mentions de flux d'ouest et d'incertitude sur les discussions

**[W2_MODEL_RUN]** — Run du 25/08/2026 00Z (vision d'ensemble)

**[W2_MODEL_TIMING]** — Lundi-mardi : perturbation active ; Mercredi : accalmie relative ; Jeudi : nouvelle dégradation ; Week-end : indécis

**[W2_MODEL_DETAILS]**
La position du jet stream est déterminante : si son axe se décale au nord (scénario GFS), la région bénéficie d'une amélioration ; s'il reste sur la France (scénario CEP), les averses persistent. Le signal ENSO et l'activité tropicale (cyclone potentiel) pourraient influencer cette évolution à 10-14 jours. Les températures resteront proches des normales dans tous les scénarios (± 1-2°C).

**[W2_MODEL_END]**



### ✅ [W2_CONVERGENCES] — Points de convergence (max 3)

1. **Absence de canicule** : Aucun scénario ne propose un retour des fortes chaleurs (> 30°C) durant cette période.
2. **Températures de saison** : Consensus sur des maximales entre 20-24°C et minimales entre 12-15°C.
3. **Risque d'averses régulier** : Tous les modèles maintiennent un risque de précipitations quasi quotidien.

### ⚠️ [W2_DIVERGENCES] — Points de divergence (max 3)

1. **Fin de période** : GFS propose une remontée anticyclonique dès samedi, CEP maintient le flux dépressionnaire.
2. **Vent** : L'épisode venteux de lundi est confirmé, mais son intensité varie (60-75 km/h selon les modèles).
3. **Cumuls pluviométriques** : Les quantités prévues varient de 10 à 30 mm sur la semaine selon les scénarios.



### 📝 [W2_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi et mardi, éclaircies mercredi, retour des averses jeudi, variable en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Risque d'averses modérées, cumuls de 5-10 mm par épisode, orages possibles lundi après-midi",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Ouest-Sud-Ouest assez fort lundi (rafales 60 km/h en Flandres), modéré ensuite",
      "sensitive_period": "Lundi (vent fort et averses), jeudi (dégradation)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end (amélioration ou persistance des averses ?)",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Averses fréquentes lundi-mardi, éclaircies mercredi, dégradation jeudi, amélioration samedi-dimanche",
      "temperatures": "Min 12-15°C, Max 20-23°C (19-21°C littoral)",
      "rain_storms": "Risque d'averses marines, cumuls 5-8 mm sur le littoral, vent assez fort lundi",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Sud-Ouest assez fort lundi (rafales 65 km/h littoral), plus modéré ensuite",
      "sensitive_period": "Lundi (vent fort littoral), jeudi (pluies)",
      "confidence_level": "moderee",
      "uncertainty": "Intensité du vent en début de semaine et évolution du week-end",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi, variable mardi-mercredi, pluies jeudi, éclaircies possibles en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Averses modérées, cumuls 5-10 mm, vent assez fort lundi sur le littoral picard",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Ouest assez fort lundi (rafales 60 km/h nord du département), Sud-Ouest modéré ensuite",
      "sensitive_period": "Lundi (vent et averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, possibilité d'amélioration",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Averses lundi, nette amélioration mercredi, dégradation jeudi, incertitude en fin de semaine",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées lundi et jeudi, cumuls 5-10 mm, vent assez fort lundi sur le pays de Bray",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Ouest-Sud-Ouest assez fort lundi matin (rafales 55-60 km/h), modéré ensuite",
      "sensitive_period": "Lundi matin (vent), jeudi (dégradation pluvieuse)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end et possible retour anticyclonique",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Averses lundi et mardi, éclaircies mercredi, pluies jeudi, amélioration samedi-dimanche (scénario GFS)",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées, cumuls 5-8 mm, risque orageux faible lundi après-midi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Ouest à Sud-Ouest temporairement modéré, rafales possibles 50 km/h lundi",
      "sensitive_period": "Lundi (averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, scénario GFS plus sec que CEP",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W2_ZONES_JSON_END]

### 💪 [W2_SOLID_POINTS] — Points solides (max 3)

1. **Températures de saison** : Fort consensus sur des valeurs proches des normales (20-24°C), sans excès ni déficit marqué.
2. **Flux d'ouest** : Le régime perturbé est acté pour au moins la première partie de la semaine.
3. **Vent lundi** : Épisode venteux confirmé avec rafales de 55-65 km/h sur l'ouest de la région.

### ⚠️ [W2_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Fin de période très incertaine** : Oppositions marquées entre GFS (amélioration) et CEP (poursuite du flux dépressionnaire).
2. **Quantités de pluie** : Les cumuls varient du simple au triple selon les scénarios (10 à 30 mm sur la semaine).
3. **Position du jet** : Un décalage de quelques degrés de latitude change radicalement le temps prévu.

### 🔭 [W2_NEXT_RUNS_TO_WATCH] — À surveiller

- **Run CEP 12Z** (ce soir) : déterminant pour trancher le scénario du week-end
- **Sorties GFS ensemble** (nuit) : évaluation de la confiance dans la remontée anticyclonique
- **Bulletin Météo-France J+7** (jeudi) : affinage de la prévision à 10 jours



## 🌦️ [W2_PHASE_1_DATES] — Phase 1 : Lundi 31 Août à Mercredi 3 Septembre

**[W2_PHASE_1]** — Régime dépressionnaire actif avec vent assez fort lundi et averses fréquentes. Amélioration relative mercredi avec de belles éclaircies entre les passages nuageux. Températures de saison (20-23°C).

## ⛅ [W2_PHASE_2_DATES] — Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.



**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**



**

### 🤝 Modèles et scénarios (Semaine 2)
**Points de convergence :**
— Points de convergence (max 3)

1. **Absence de canicule** : Aucun scénario ne propose un retour des fortes chaleurs (> 30°C) durant cette période.
2. **Températures de saison** : Consensus sur des maximales entre 20-24°C et minimales entre 12-15°C.
3. **Risque d'averses régulier** : Tous les modèles maintiennent un risque de précipitations quasi quotidien.

### ⚠️ [W2_DIVERGENCES] — Points de divergence (max 3)

1. **Fin de période** : GFS propose une remontée anticyclonique dès samedi, CEP maintient le flux dépressionnaire.
2. **Vent** : L'épisode venteux de lundi est confirmé, mais son intensité varie (60-75 km/h selon les modèles).
3. **Cumuls pluviométriques** : Les quantités prévues varient de 10 à 30 mm sur la semaine selon les scénarios.



### 📝 [W2_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi et mardi, éclaircies mercredi, retour des averses jeudi, variable en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Risque d'averses modérées, cumuls de 5-10 mm par épisode, orages possibles lundi après-midi",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Ouest-Sud-Ouest assez fort lundi (rafales 60 km/h en Flandres), modéré ensuite",
      "sensitive_period": "Lundi (vent fort et averses), jeudi (dégradation)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end (amélioration ou persistance des averses ?)",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Averses fréquentes lundi-mardi, éclaircies mercredi, dégradation jeudi, amélioration samedi-dimanche",
      "temperatures": "Min 12-15°C, Max 20-23°C (19-21°C littoral)",
      "rain_storms": "Risque d'averses marines, cumuls 5-8 mm sur le littoral, vent assez fort lundi",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Sud-Ouest assez fort lundi (rafales 65 km/h littoral), plus modéré ensuite",
      "sensitive_period": "Lundi (vent fort littoral), jeudi (pluies)",
      "confidence_level": "moderee",
      "uncertainty": "Intensité du vent en début de semaine et évolution du week-end",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi, variable mardi-mercredi, pluies jeudi, éclaircies possibles en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Averses modérées, cumuls 5-10 mm, vent assez fort lundi sur le littoral picard",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Ouest assez fort lundi (rafales 60 km/h nord du département), Sud-Ouest modéré ensuite",
      "sensitive_period": "Lundi (vent et averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, possibilité d'amélioration",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Averses lundi, nette amélioration mercredi, dégradation jeudi, incertitude en fin de semaine",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées lundi et jeudi, cumuls 5-10 mm, vent assez fort lundi sur le pays de Bray",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Ouest-Sud-Ouest assez fort lundi matin (rafales 55-60 km/h), modéré ensuite",
      "sensitive_period": "Lundi matin (vent), jeudi (dégradation pluvieuse)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end et possible retour anticyclonique",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Averses lundi et mardi, éclaircies mercredi, pluies jeudi, amélioration samedi-dimanche (scénario GFS)",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées, cumuls 5-8 mm, risque orageux faible lundi après-midi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Ouest à Sud-Ouest temporairement modéré, rafales possibles 50 km/h lundi",
      "sensitive_period": "Lundi (averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, scénario GFS plus sec que CEP",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W2_ZONES_JSON_END]

### 💪 [W2_SOLID_POINTS] — Points solides (max 3)

1. **Températures de saison** : Fort consensus sur des valeurs proches des normales (20-24°C), sans excès ni déficit marqué.
2. **Flux d'ouest** : Le régime perturbé est acté pour au moins la première partie de la semaine.
3. **Vent lundi** : Épisode venteux confirmé avec rafales de 55-65 km/h sur l'ouest de la région.

### ⚠️ [W2_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Fin de période très incertaine** : Oppositions marquées entre GFS (amélioration) et CEP (poursuite du flux dépressionnaire).
2. **Quantités de pluie** : Les cumuls varient du simple au triple selon les scénarios (10 à 30 mm sur la semaine).
3. **Position du jet** : Un décalage de quelques degrés de latitude change radicalement le temps prévu.

### 🔭 [W2_NEXT_RUNS_TO_WATCH] — À surveiller

- **Run CEP 12Z** (ce soir) : déterminant pour trancher le scénario du week-end
- **Sorties GFS ensemble** (nuit) : évaluation de la confiance dans la remontée anticyclonique
- **Bulletin Météo-France J+7** (jeudi) : affinage de la prévision à 10 jours



## 🌦️ [W2_PHASE_1_DATES] — Phase 1 : Lundi 31 Août à Mercredi 3 Septembre

**[W2_PHASE_1]** — Régime dépressionnaire actif avec vent assez fort lundi et averses fréquentes. Amélioration relative mercredi avec de belles éclaircies entre les passages nuageux. Températures de saison (20-23°C).

## ⛅ [W2_PHASE_2_DATES] — Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.



**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**



**
**Points de divergence :**
— Points de divergence (max 3)

1. **Fin de période** : GFS propose une remontée anticyclonique dès samedi, CEP maintient le flux dépressionnaire.
2. **Vent** : L'épisode venteux de lundi est confirmé, mais son intensité varie (60-75 km/h selon les modèles).
3. **Cumuls pluviométriques** : Les quantités prévues varient de 10 à 30 mm sur la semaine selon les scénarios.



### 📝 [W2_ZONES_JSON_START]

```json
{
  "zones": {
    "nord": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi et mardi, éclaircies mercredi, retour des averses jeudi, variable en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Risque d'averses modérées, cumuls de 5-10 mm par épisode, orages possibles lundi après-midi",
      "spatial_scope": "regional",
      "location": "Lille, Dunkerque, Valenciennes, Douai, Avesnois",
      "wind": "Ouest-Sud-Ouest assez fort lundi (rafales 60 km/h en Flandres), modéré ensuite",
      "sensitive_period": "Lundi (vent fort et averses), jeudi (dégradation)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end (amélioration ou persistance des averses ?)",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "pas_de_calais": {
      "status": "documented",
      "weather": "Averses fréquentes lundi-mardi, éclaircies mercredi, dégradation jeudi, amélioration samedi-dimanche",
      "temperatures": "Min 12-15°C, Max 20-23°C (19-21°C littoral)",
      "rain_storms": "Risque d'averses marines, cumuls 5-8 mm sur le littoral, vent assez fort lundi",
      "spatial_scope": "regional",
      "location": "Arras, Boulogne, Calais, Lens, Saint-Omer",
      "wind": "Sud-Ouest assez fort lundi (rafales 65 km/h littoral), plus modéré ensuite",
      "sensitive_period": "Lundi (vent fort littoral), jeudi (pluies)",
      "confidence_level": "moderee",
      "uncertainty": "Intensité du vent en début de semaine et évolution du week-end",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "somme": {
      "status": "documented",
      "weather": "Nuageux avec averses lundi, variable mardi-mercredi, pluies jeudi, éclaircies possibles en fin de semaine",
      "temperatures": "Min 12-15°C, Max 20-23°C",
      "rain_storms": "Averses modérées, cumuls 5-10 mm, vent assez fort lundi sur le littoral picard",
      "spatial_scope": "regional",
      "location": "Amiens, Abbeville, Péronne, Cayeux-sur-Mer, Doullens",
      "wind": "Ouest assez fort lundi (rafales 60 km/h nord du département), Sud-Ouest modéré ensuite",
      "sensitive_period": "Lundi (vent et averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, possibilité d'amélioration",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "oise": {
      "status": "documented",
      "weather": "Averses lundi, nette amélioration mercredi, dégradation jeudi, incertitude en fin de semaine",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées lundi et jeudi, cumuls 5-10 mm, vent assez fort lundi sur le pays de Bray",
      "spatial_scope": "regional",
      "location": "Beauvais, Compiègne, Clermont, Creil, Senlis",
      "wind": "Ouest-Sud-Ouest assez fort lundi matin (rafales 55-60 km/h), modéré ensuite",
      "sensitive_period": "Lundi matin (vent), jeudi (dégradation pluvieuse)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end et possible retour anticyclonique",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    },
    "aisne": {
      "status": "documented",
      "weather": "Averses lundi et mardi, éclaircies mercredi, pluies jeudi, amélioration samedi-dimanche (scénario GFS)",
      "temperatures": "Min 11-14°C, Max 21-24°C",
      "rain_storms": "Averses modérées, cumuls 5-8 mm, risque orageux faible lundi après-midi",
      "spatial_scope": "regional",
      "location": "Laon, Saint-Quentin, Soissons, Château-Thierry, Thiérache",
      "wind": "Ouest à Sud-Ouest temporairement modéré, rafales possibles 50 km/h lundi",
      "sensitive_period": "Lundi (averses), jeudi (pluies plus régulières)",
      "confidence_level": "moderee",
      "uncertainty": "Évolution du week-end, scénario GFS plus sec que CEP",
      "evidence_count": 4,
      "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
    }
  }
}
```

### 📍 [W2_ZONES_JSON_END]

### 💪 [W2_SOLID_POINTS] — Points solides (max 3)

1. **Températures de saison** : Fort consensus sur des valeurs proches des normales (20-24°C), sans excès ni déficit marqué.
2. **Flux d'ouest** : Le régime perturbé est acté pour au moins la première partie de la semaine.
3. **Vent lundi** : Épisode venteux confirmé avec rafales de 55-65 km/h sur l'ouest de la région.

### ⚠️ [W2_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Fin de période très incertaine** : Oppositions marquées entre GFS (amélioration) et CEP (poursuite du flux dépressionnaire).
2. **Quantités de pluie** : Les cumuls varient du simple au triple selon les scénarios (10 à 30 mm sur la semaine).
3. **Position du jet** : Un décalage de quelques degrés de latitude change radicalement le temps prévu.

### 🔭 [W2_NEXT_RUNS_TO_WATCH] — À surveiller

- **Run CEP 12Z** (ce soir) : déterminant pour trancher le scénario du week-end
- **Sorties GFS ensemble** (nuit) : évaluation de la confiance dans la remontée anticyclonique
- **Bulletin Météo-France J+7** (jeudi) : affinage de la prévision à 10 jours



## 🌦️ [W2_PHASE_1_DATES] — Phase 1 : Lundi 31 Août à Mercredi 3 Septembre

**[W2_PHASE_1]** — Régime dépressionnaire actif avec vent assez fort lundi et averses fréquentes. Amélioration relative mercredi avec de belles éclaircies entre les passages nuageux. Températures de saison (20-23°C).

## ⛅ [W2_PHASE_2_DATES] — Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.



**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**



**

### 🤖 Scénarios détaillés des modèles (Semaine 2)
| Modèle | Scénario | Temps sensible | Zones concernées | Confiance | Détails d'analyse |
| --- | --- | --- | --- | --- | --- |
| **— Analyse des Modèles (GFS / ECMWF / ICON / CEP)

<strong>[W2_MODEL_SCENARIO]</strong> (max 160 car.)
Le flux d'ouest perturbé se maintient sur la France. Une dépression atlantique circule près des îles britanniques, entraînant un défilé de perturbations sur les Hauts-de-France. Les températures restent proches des normales saisonnières. En fin de période, les scénarios divergent : le CEP maintient le flux dépressionnaire, tandis que GFS propose une poussée anticyclonique par le sud-ouest. ECMWF est intermédiaire avec un talweg qui s'évacue lentement vers l'Europe centrale.

<strong>[W2_MODEL_SENSIBLE_WEATHER]</strong> (max 120 car.)
Ciel nuageux à couvert, averses fréquentes surtout lundi-mardi et jeudi ; éclaircies possibles mercredi et en fin de semaine.

<strong>[W2_MODEL_AFFECTED_ZONES]</strong> — Toute la région HDF, avec un gradient littoral/intérieur marqué (plus de vent et de pluie sur le littoral)

<strong>[W2_MODEL_EXTRACTION_CONF]</strong> — Moyenne (65%) : divergence croissante en fin d'échéance

<strong>[W2_MODEL_SCENARIO_SUPPORT]</strong> — 3 modèles sur 5 (CEP, ECMWF, ICON) pour le maintien du flux d'ouest ; GFS en divergence

<strong>[W2_MODEL_STATUS]</strong> — 🟡 Modéré — Tendances générales fiables, détails incertains au-delà de jeudi

<strong>[W2_MODEL_MENTIONS_COUNT]</strong> — 8 mentions de flux d'ouest et d'incertitude sur les discussions

<strong>[W2_MODEL_RUN]</strong> — Run du 25/08/2026 00Z (vision d'ensemble)

<strong>[W2_MODEL_TIMING]</strong> — Lundi-mardi : perturbation active ; Mercredi : accalmie relative ; Jeudi : nouvelle dégradation ; Week-end : indécis

<strong>[W2_MODEL_DETAILS]</strong>
La position du jet stream est déterminante : si son axe se décale au nord (scénario GFS), la région bénéficie d'une amélioration ; s'il reste sur la France (scénario CEP), les averses persistent. Le signal ENSO et l'activité tropicale (cyclone potentiel) pourraient influencer cette évolution à 10-14 jours. Les températures resteront proches des normales dans tous les scénarios (± 1-2°C).

**** (** — 🟡 Modéré — Tendances générales fiables, détails incertains au-delà de jeudi

**[W2_MODEL_MENTIONS_COUNT]** — 8 mentions de flux d'ouest et d'incertitude sur les discussions

**[W2_MODEL_RUN]** — Run du 25/08/2026 00Z (vision d'ensemble)

**[W2_MODEL_TIMING]** — Lundi-mardi : perturbation active ; Mercredi : accalmie relative ; Jeudi : nouvelle dégradation ; Week-end : indécis

**[W2_MODEL_DETAILS]**
La position du jet stream est déterminante : si son axe se décale au nord (scénario GFS), la région bénéficie d'une amélioration ; s'il reste sur la France (scénario CEP), les averses persistent. Le signal ENSO et l'activité tropicale (cyclone potentiel) pourraient influencer cette évolution à 10-14 jours. Les températures resteront proches des normales dans tous les scénarios (± 1-2°C).

**) | ** (max 160 car.)
Le flux d'ouest perturbé se maintient sur la France. Une dépression atlantique circule près des îles britanniques, entraînant un défilé de perturbations sur les Hauts-de-France. Les températures restent proches des normales saisonnières. En fin de période, les scénarios divergent : le CEP maintient le flux dépressionnaire, tandis que GFS propose une poussée anticyclonique par le sud-ouest. ECMWF est intermédiaire avec un talweg qui s'évacue lentement vers l'Europe centrale.

<strong>[W2_MODEL_SENSIBLE_WEATHER]</strong> (max 120 car.)
Ciel nuageux à couvert, averses fréquentes surtout lundi-mardi et jeudi ; éclaircies possibles mercredi et en fin de semaine.

<strong>[W2_MODEL_AFFECTED_ZONES]</strong> — Toute la région HDF, avec un gradient littoral/intérieur marqué (plus de vent et de pluie sur le littoral)

<strong>[W2_MODEL_EXTRACTION_CONF]</strong> — Moyenne (65%) : divergence croissante en fin d'échéance

<strong>[W2_MODEL_SCENARIO_SUPPORT]</strong> — 3 modèles sur 5 (CEP, ECMWF, ICON) pour le maintien du flux d'ouest ; GFS en divergence

<strong>[W2_MODEL_STATUS]</strong> — 🟡 Modéré — Tendances générales fiables, détails incertains au-delà de jeudi

<strong>[W2_MODEL_MENTIONS_COUNT]</strong> — 8 mentions de flux d'ouest et d'incertitude sur les discussions

<strong>[W2_MODEL_RUN]</strong> — Run du 25/08/2026 00Z (vision d'ensemble)

<strong>[W2_MODEL_TIMING]</strong> — Lundi-mardi : perturbation active ; Mercredi : accalmie relative ; Jeudi : nouvelle dégradation ; Week-end : indécis

<strong>[W2_MODEL_DETAILS]</strong>
La position du jet stream est déterminante : si son axe se décale au nord (scénario GFS), la région bénéficie d'une amélioration ; s'il reste sur la France (scénario CEP), les averses persistent. Le signal ENSO et l'activité tropicale (cyclone potentiel) pourraient influencer cette évolution à 10-14 jours. Les températures resteront proches des normales dans tous les scénarios (± 1-2°C).

** | ** (max 120 car.)
Ciel nuageux à couvert, averses fréquentes surtout lundi-mardi et jeudi ; éclaircies possibles mercredi et en fin de semaine.

<strong>[W2_MODEL_AFFECTED_ZONES]</strong> — Toute la région HDF, avec un gradient littoral/intérieur marqué (plus de vent et de pluie sur le littoral)

<strong>[W2_MODEL_EXTRACTION_CONF]</strong> — Moyenne (65%) : divergence croissante en fin d'échéance

<strong>[W2_MODEL_SCENARIO_SUPPORT]</strong> — 3 modèles sur 5 (CEP, ECMWF, ICON) pour le maintien du flux d'ouest ; GFS en divergence

<strong>[W2_MODEL_STATUS]</strong> — 🟡 Modéré — Tendances générales fiables, détails incertains au-delà de jeudi

<strong>[W2_MODEL_MENTIONS_COUNT]</strong> — 8 mentions de flux d'ouest et d'incertitude sur les discussions

<strong>[W2_MODEL_RUN]</strong> — Run du 25/08/2026 00Z (vision d'ensemble)

<strong>[W2_MODEL_TIMING]</strong> — Lundi-mardi : perturbation active ; Mercredi : accalmie relative ; Jeudi : nouvelle dégradation ; Week-end : indécis

<strong>[W2_MODEL_DETAILS]</strong>
La position du jet stream est déterminante : si son axe se décale au nord (scénario GFS), la région bénéficie d'une amélioration ; s'il reste sur la France (scénario CEP), les averses persistent. Le signal ENSO et l'activité tropicale (cyclone potentiel) pourraient influencer cette évolution à 10-14 jours. Les températures resteront proches des normales dans tous les scénarios (± 1-2°C).

** | ** — Toute la région HDF, avec un gradient littoral/intérieur marqué (plus de vent et de pluie sur le littoral)

<strong>[W2_MODEL_EXTRACTION_CONF]</strong> — Moyenne (65%) : divergence croissante en fin d'échéance

<strong>[W2_MODEL_SCENARIO_SUPPORT]</strong> — 3 modèles sur 5 (CEP, ECMWF, ICON) pour le maintien du flux d'ouest ; GFS en divergence

<strong>[W2_MODEL_STATUS]</strong> — 🟡 Modéré — Tendances générales fiables, détails incertains au-delà de jeudi

<strong>[W2_MODEL_MENTIONS_COUNT]</strong> — 8 mentions de flux d'ouest et d'incertitude sur les discussions

<strong>[W2_MODEL_RUN]</strong> — Run du 25/08/2026 00Z (vision d'ensemble)

<strong>[W2_MODEL_TIMING]</strong> — Lundi-mardi : perturbation active ; Mercredi : accalmie relative ; Jeudi : nouvelle dégradation ; Week-end : indécis

<strong>[W2_MODEL_DETAILS]</strong>
La position du jet stream est déterminante : si son axe se décale au nord (scénario GFS), la région bénéficie d'une amélioration ; s'il reste sur la France (scénario CEP), les averses persistent. Le signal ENSO et l'activité tropicale (cyclone potentiel) pourraient influencer cette évolution à 10-14 jours. Les températures resteront proches des normales dans tous les scénarios (± 1-2°C).

** | ** — Moyenne (65%) : divergence croissante en fin d'échéance

**[W2_MODEL_SCENARIO_SUPPORT]** — 3 modèles sur 5 (CEP, ECMWF, ICON) pour le maintien du flux d'ouest ; GFS en divergence

**[W2_MODEL_STATUS]** — 🟡 Modéré — Tendances générales fiables, détails incertains au-delà de jeudi

**[W2_MODEL_MENTIONS_COUNT]** — 8 mentions de flux d'ouest et d'incertitude sur les discussions

**[W2_MODEL_RUN]** — Run du 25/08/2026 00Z (vision d'ensemble)

**[W2_MODEL_TIMING]** — Lundi-mardi : perturbation active ; Mercredi : accalmie relative ; Jeudi : nouvelle dégradation ; Week-end : indécis

**[W2_MODEL_DETAILS]**
La position du jet stream est déterminante : si son axe se décale au nord (scénario GFS), la région bénéficie d'une amélioration ; s'il reste sur la France (scénario CEP), les averses persistent. Le signal ENSO et l'activité tropicale (cyclone potentiel) pourraient influencer cette évolution à 10-14 jours. Les températures resteront proches des normales dans tous les scénarios (± 1-2°C).

** | ** La position du jet stream est déterminante : si son axe se décale au nord (scénario GFS), la région bénéficie d'une amélioration ; s'il reste sur la France (scénario CEP), les averses persistent. Le signal ENSO et l'activité tropicale (cyclone potentiel) pourraient influencer cette évolution à 10-14 jours. Les températures resteront proches des normales dans tous les scénarios (± 1-2°C).  ** |

### 📍 Synthèse par zones/départements (Semaine 2)
| Zone / Département | Temps sensible | Températures | Fiabilité | Modèles | Notes d'analyse |
| --- | --- | --- | --- | --- | --- |
| **Nord (59)** | Chaleur d'été | 25°C à 30°C | Modérée | ECMWF, GFS, Guillaume Séchet | Incertitude habituelle J+14 |
| **Pas-de-Calais (62)** | Chaleur d'été | 25°C à 30°C | Modérée | ECMWF, GFS, Guillaume Séchet | Incertitude habituelle J+14 |
| **Somme (80)** | Chaleur d'été | 25°C à 30°C | Modérée | ECMWF, GFS, Guillaume Séchet | Incertitude habituelle J+14 |
| **Oise (60)** | Chaleur d'été | 25°C à 30°C | Modérée | ECMWF, GFS, Guillaume Séchet | Incertitude habituelle J+14 |
| **Aisne (02)** | Chaleur d'été | 25°C à 30°C | Modérée | ECMWF, GFS, Guillaume Séchet | Incertitude habituelle J+14 |

### ⏳ Déroulé chronologique (Semaine 2)
- **— Phase 1 : Lundi 31 Août à Mercredi 3 Septembre

**[W2_PHASE_1]** — Régime dépressionnaire actif avec vent assez fort lundi et averses fréquentes. Amélioration relative mercredi avec de belles éclaircies entre les passages nuageux. Températures de saison (20-23°C).

## ⛅ [W2_PHASE_2_DATES] — Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.

---

**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**

---

**** : ** — Régime dépressionnaire actif avec vent assez fort lundi et averses fréquentes. Amélioration relative mercredi avec de belles éclaircies entre les passages nuageux. Températures de saison (20-23°C).

## ⛅ [W2_PHASE_2_DATES] — Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.



**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**



**
- **— Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.

---

**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**

---

**** : ** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.



**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**



**

**Points solides :**
— Points solides (max 3)

1. **Températures de saison** : Fort consensus sur des valeurs proches des normales (20-24°C), sans excès ni déficit marqué.
2. **Flux d'ouest** : Le régime perturbé est acté pour au moins la première partie de la semaine.
3. **Vent lundi** : Épisode venteux confirmé avec rafales de 55-65 km/h sur l'ouest de la région.

### ⚠️ [W2_FRAGILE_POINTS] — Points fragiles (max 3)

1. **Fin de période très incertaine** : Oppositions marquées entre GFS (amélioration) et CEP (poursuite du flux dépressionnaire).
2. **Quantités de pluie** : Les cumuls varient du simple au triple selon les scénarios (10 à 30 mm sur la semaine).
3. **Position du jet** : Un décalage de quelques degrés de latitude change radicalement le temps prévu.

### 🔭 [W2_NEXT_RUNS_TO_WATCH] — À surveiller

- **Run CEP 12Z** (ce soir) : déterminant pour trancher le scénario du week-end
- **Sorties GFS ensemble** (nuit) : évaluation de la confiance dans la remontée anticyclonique
- **Bulletin Météo-France J+7** (jeudi) : affinage de la prévision à 10 jours



## 🌦️ [W2_PHASE_1_DATES] — Phase 1 : Lundi 31 Août à Mercredi 3 Septembre

**[W2_PHASE_1]** — Régime dépressionnaire actif avec vent assez fort lundi et averses fréquentes. Amélioration relative mercredi avec de belles éclaircies entre les passages nuageux. Températures de saison (20-23°C).

## ⛅ [W2_PHASE_2_DATES] — Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.



**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**



**

**Points fragiles :**
— Points fragiles (max 3)

1. **Fin de période très incertaine** : Oppositions marquées entre GFS (amélioration) et CEP (poursuite du flux dépressionnaire).
2. **Quantités de pluie** : Les cumuls varient du simple au triple selon les scénarios (10 à 30 mm sur la semaine).
3. **Position du jet** : Un décalage de quelques degrés de latitude change radicalement le temps prévu.

### 🔭 [W2_NEXT_RUNS_TO_WATCH] — À surveiller

- **Run CEP 12Z** (ce soir) : déterminant pour trancher le scénario du week-end
- **Sorties GFS ensemble** (nuit) : évaluation de la confiance dans la remontée anticyclonique
- **Bulletin Météo-France J+7** (jeudi) : affinage de la prévision à 10 jours



## 🌦️ [W2_PHASE_1_DATES] — Phase 1 : Lundi 31 Août à Mercredi 3 Septembre

**[W2_PHASE_1]** — Régime dépressionnaire actif avec vent assez fort lundi et averses fréquentes. Amélioration relative mercredi avec de belles éclaircies entre les passages nuageux. Températures de saison (20-23°C).

## ⛅ [W2_PHASE_2_DATES] — Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.



**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**



**

**À surveiller (prochains runs) :**
— À surveiller

- **Run CEP 12Z** (ce soir) : déterminant pour trancher le scénario du week-end
- **Sorties GFS ensemble** (nuit) : évaluation de la confiance dans la remontée anticyclonique
- **Bulletin Météo-France J+7** (jeudi) : affinage de la prévision à 10 jours



## 🌦️ [W2_PHASE_1_DATES] — Phase 1 : Lundi 31 Août à Mercredi 3 Septembre

**[W2_PHASE_1]** — Régime dépressionnaire actif avec vent assez fort lundi et averses fréquentes. Amélioration relative mercredi avec de belles éclaircies entre les passages nuageux. Températures de saison (20-23°C).

## ⛅ [W2_PHASE_2_DATES] — Phase 2 : Jeudi 4 à Dimanche 7 Septembre

**[W2_PHASE_2]** — Nouvelle dégradation pluvieuse jeudi, puis incertitude marquée pour le week-end : amélioration possible selon GFS, persistance des averses selon CEP. Températures stables autour de 21-23°C.



**[W2_IMAGE_START]**
```
┌─────────────────────────────────────────────────────────┐
│  📍 CARTE HDF — SEMAINE 2 (31 Août-6 Sept. 2026)       │
│                                                         │
│  LUNDI 31     🌧️💨 (averses + vent SO)   20-22°C       │
│  MARDI 1er    🌦️ (variable)               21-23°C       │
│  MERCREDI 2   ⛅ (éclaircies)             21-23°C       │
│  JEUDI 3      🌧️ (pluies)                 20-22°C       │
│  VENDREDI 4   ⛅ (amélioration ?)         21-24°C       │
│  SAMEDI 5     ⛅/🌦️ (incertain)           21-23°C       │
│  DIMANCHE 6   ⛅/🌦️ (incertain)           21-23°C       │
│                                                         │
│  💨 Vent : SO assez fort lundi (60 km/h)               │
│  🌡️ T° : Min 11-15°C / Max 20-24°C                    │
│  ❓ Fin de période : GFS sec vs CEP humide              │
└─────────────────────────────────────────────────────────┘
```
**[W2_IMAGE_END]**



**


========================================

## 🔮 TENDANCE GLOBALE À 15 JOURS ET DOUTES

### Tendance 15 jours
— Tendance globale sur 15 jours (25 Août - 8 Septembre 2026)

Les Hauts-de-France connaissent une **transition nette vers un temps de saison** après un été marqué par la canicule. La première semaine est dominée par une **dégradation orageuse** (mercredi 26 et jeudi 27) avec un risque de phénomènes localement violents, suivie d'un **rafraîchissement marqué** dès vendredi 28. La seconde semaine s'annonce **perturbée et océanique**, avec des températures conformes aux normales de début septembre. L'incertitude principale concerne la fin de période (à partir du 5-6 septembre) : retour anticyclonique ou persistance du flux dépressionnaire.



## 🎯 [MOST_RELIABLE_WEEK] — Semaine la plus fiable

**Semaine 1 (25-30 Août)** : Confiance élevée (80-85%) sur la chronologie et les températures. Les prévisions à 3-5 jours bénéficient d'une bonne convergence des modèles. La semaine 2 est nettement moins fiable (60-65%).



## ✅ [GLOBAL_SOLID_POINTS] — Points solides (max 3)

1. **Fin de la canicule** : Le changement de régime est acté, plus aucun scénario ne propose un retour des fortes chaleurs (> 30°C).
2. **Dégradation orageuse** : Épisode orageux mercredi-jeudi avec risque de grêle et rafales (probabilité 60-70%).
3. **Températures de saison** : Retour à des valeurs normales (20-24°C) pour les deux prochaines semaines.



## 🔄 [GLOBAL_RECURRING_PHENOMENA] — Phénomènes récurrents

- **Averses quotidiennes** : Le régime océanique maintient un risque de précipitations chaque jour
- **Vent de Sud-Ouest** : Flux dominant pendant toute la période, avec des renforcements réguliers
- **Améliorations temporaires** : Éclaircies entre les passages perturbés, principalement en deuxième partie de journée



## 📍 [GLOBAL_AFFECTED_ZONES] — Zones affectées

- **Littoral (Nord, Pas-de-Calais, Somme)** : Vent plus fort, averses marines fréquentes
- **Est (Aisne, est de l'Oise)** : Risque orageux plus marqué, cumuls potentiellement plus importants
- **Intérieur** : Variations thermiques plus amples, éclaircies plus nettes entre les perturbations



## ⚠️ [GLOBAL_MAJOR_UNCERTAINTIES] — Incertitudes majeures

1. **Fin de semaine 2** : Oppositions entre scénario anticyclonique (GFS) et maintien du flux d'ouest (CEP)
2. **Intensité orageuse** : Risque de phénomènes violents (grêle > 5 cm) impossible à localiser précisément à J+3
3. **Cumuls pluviométriques** : Variations de 10 à 30 mm selon la trajectoire des perturbations




## 📊 [GLOBAL_CONSENSUS_KPI] — Consensus des modèles : **Modéré**

**[GLOBAL_CONSENSUS_NOTE]** — Bonne convergence sur la semaine 1 (85%), nette divergence sur la fin de semaine 2 (55%). Le signal principal (fin de canicule, retour à la normale) est robuste.

## 🎭 [GLOBAL_SCENARIO_KPI] — Scénario dominant : **Flux océanique dépressionnaire**

**[GLOBAL_SCENARIO_NOTE]** — 60% de probabilité pour le maintien d'un régime d'ouest perturbé, 25% pour une amélioration anticyclonique en fin de période, 15% pour un scénario intermédiaire.

## ❓ [GLOBAL_UNCERTAINTY_KPI] — Incertitude globale : **Modérée**

**[GLOBAL_UNCERTAINTY_NOTE]** — Incertitude principalement liée à l'échéance J+8 et au-delà. Les prévisions à 3-5 jours restent fiables.



## 📱 [LINKEDIN_POST] — Publication LinkedIn

> 🌦️ **HAUTS-DE-FRANCE : FIN DE LA CANICULE, RETOUR D'UN TEMPS DE SAISON** 🌦️
> 
> La région bascule dans un régime océanique cette semaine !
> 
> 🔹 **Mardi** : Dernière journée chaude (26-28°C) avant la bascule
> 🔹 **Mercredi-Jeudi** : Dégradation orageuse, risque de grêle et rafales
> 🔹 **Vendredi** : Net rafraîchissement (20-22°C)
> 🔹 **Semaine prochaine** : Averses fréquentes, vent de Sud-Ouest, températures de saison
> 
> 📊 Les modèles s'accordent sur la fin de la canicule mais divergent pour le week-end du 6 septembre.
> 
> 💡 À suivre : le run CEP de ce soir pour affiner les prévisions !
> 
> #Météo #HautsDeFrance #Prévisions #Climat #Orages #MétéoFrance



**

### Période la plus fiable
— Semaine la plus fiable

**Semaine 1 (25-30 Août)** : Confiance élevée (80-85%) sur la chronologie et les températures. Les prévisions à 3-5 jours bénéficient d'une bonne convergence des modèles. La semaine 2 est nettement moins fiable (60-65%).



## ✅ [GLOBAL_SOLID_POINTS] — Points solides (max 3)

1. **Fin de la canicule** : Le changement de régime est acté, plus aucun scénario ne propose un retour des fortes chaleurs (> 30°C).
2. **Dégradation orageuse** : Épisode orageux mercredi-jeudi avec risque de grêle et rafales (probabilité 60-70%).
3. **Températures de saison** : Retour à des valeurs normales (20-24°C) pour les deux prochaines semaines.



## 🔄 [GLOBAL_RECURRING_PHENOMENA] — Phénomènes récurrents

- **Averses quotidiennes** : Le régime océanique maintient un risque de précipitations chaque jour
- **Vent de Sud-Ouest** : Flux dominant pendant toute la période, avec des renforcements réguliers
- **Améliorations temporaires** : Éclaircies entre les passages perturbés, principalement en deuxième partie de journée



## 📍 [GLOBAL_AFFECTED_ZONES] — Zones affectées

- **Littoral (Nord, Pas-de-Calais, Somme)** : Vent plus fort, averses marines fréquentes
- **Est (Aisne, est de l'Oise)** : Risque orageux plus marqué, cumuls potentiellement plus importants
- **Intérieur** : Variations thermiques plus amples, éclaircies plus nettes entre les perturbations



## ⚠️ [GLOBAL_MAJOR_UNCERTAINTIES] — Incertitudes majeures

1. **Fin de semaine 2** : Oppositions entre scénario anticyclonique (GFS) et maintien du flux d'ouest (CEP)
2. **Intensité orageuse** : Risque de phénomènes violents (grêle > 5 cm) impossible à localiser précisément à J+3
3. **Cumuls pluviométriques** : Variations de 10 à 30 mm selon la trajectoire des perturbations




## 📊 [GLOBAL_CONSENSUS_KPI] — Consensus des modèles : **Modéré**

**[GLOBAL_CONSENSUS_NOTE]** — Bonne convergence sur la semaine 1 (85%), nette divergence sur la fin de semaine 2 (55%). Le signal principal (fin de canicule, retour à la normale) est robuste.

## 🎭 [GLOBAL_SCENARIO_KPI] — Scénario dominant : **Flux océanique dépressionnaire**

**[GLOBAL_SCENARIO_NOTE]** — 60% de probabilité pour le maintien d'un régime d'ouest perturbé, 25% pour une amélioration anticyclonique en fin de période, 15% pour un scénario intermédiaire.

## ❓ [GLOBAL_UNCERTAINTY_KPI] — Incertitude globale : **Modérée**

**[GLOBAL_UNCERTAINTY_NOTE]** — Incertitude principalement liée à l'échéance J+8 et au-delà. Les prévisions à 3-5 jours restent fiables.



## 📱 [LINKEDIN_POST] — Publication LinkedIn

> 🌦️ **HAUTS-DE-FRANCE : FIN DE LA CANICULE, RETOUR D'UN TEMPS DE SAISON** 🌦️
> 
> La région bascule dans un régime océanique cette semaine !
> 
> 🔹 **Mardi** : Dernière journée chaude (26-28°C) avant la bascule
> 🔹 **Mercredi-Jeudi** : Dégradation orageuse, risque de grêle et rafales
> 🔹 **Vendredi** : Net rafraîchissement (20-22°C)
> 🔹 **Semaine prochaine** : Averses fréquentes, vent de Sud-Ouest, températures de saison
> 
> 📊 Les modèles s'accordent sur la fin de la canicule mais divergent pour le week-end du 6 septembre.
> 
> 💡 À suivre : le run CEP de ce soir pour affiner les prévisions !
> 
> #Météo #HautsDeFrance #Prévisions #Climat #Orages #MétéoFrance



**

### Phénomènes récurrents
— Phénomènes récurrents

- **Averses quotidiennes** : Le régime océanique maintient un risque de précipitations chaque jour
- **Vent de Sud-Ouest** : Flux dominant pendant toute la période, avec des renforcements réguliers
- **Améliorations temporaires** : Éclaircies entre les passages perturbés, principalement en deuxième partie de journée



## 📍 [GLOBAL_AFFECTED_ZONES] — Zones affectées

- **Littoral (Nord, Pas-de-Calais, Somme)** : Vent plus fort, averses marines fréquentes
- **Est (Aisne, est de l'Oise)** : Risque orageux plus marqué, cumuls potentiellement plus importants
- **Intérieur** : Variations thermiques plus amples, éclaircies plus nettes entre les perturbations



## ⚠️ [GLOBAL_MAJOR_UNCERTAINTIES] — Incertitudes majeures

1. **Fin de semaine 2** : Oppositions entre scénario anticyclonique (GFS) et maintien du flux d'ouest (CEP)
2. **Intensité orageuse** : Risque de phénomènes violents (grêle > 5 cm) impossible à localiser précisément à J+3
3. **Cumuls pluviométriques** : Variations de 10 à 30 mm selon la trajectoire des perturbations




## 📊 [GLOBAL_CONSENSUS_KPI] — Consensus des modèles : **Modéré**

**[GLOBAL_CONSENSUS_NOTE]** — Bonne convergence sur la semaine 1 (85%), nette divergence sur la fin de semaine 2 (55%). Le signal principal (fin de canicule, retour à la normale) est robuste.

## 🎭 [GLOBAL_SCENARIO_KPI] — Scénario dominant : **Flux océanique dépressionnaire**

**[GLOBAL_SCENARIO_NOTE]** — 60% de probabilité pour le maintien d'un régime d'ouest perturbé, 25% pour une amélioration anticyclonique en fin de période, 15% pour un scénario intermédiaire.

## ❓ [GLOBAL_UNCERTAINTY_KPI] — Incertitude globale : **Modérée**

**[GLOBAL_UNCERTAINTY_NOTE]** — Incertitude principalement liée à l'échéance J+8 et au-delà. Les prévisions à 3-5 jours restent fiables.



## 📱 [LINKEDIN_POST] — Publication LinkedIn

> 🌦️ **HAUTS-DE-FRANCE : FIN DE LA CANICULE, RETOUR D'UN TEMPS DE SAISON** 🌦️
> 
> La région bascule dans un régime océanique cette semaine !
> 
> 🔹 **Mardi** : Dernière journée chaude (26-28°C) avant la bascule
> 🔹 **Mercredi-Jeudi** : Dégradation orageuse, risque de grêle et rafales
> 🔹 **Vendredi** : Net rafraîchissement (20-22°C)
> 🔹 **Semaine prochaine** : Averses fréquentes, vent de Sud-Ouest, températures de saison
> 
> 📊 Les modèles s'accordent sur la fin de la canicule mais divergent pour le week-end du 6 septembre.
> 
> 💡 À suivre : le run CEP de ce soir pour affiner les prévisions !
> 
> #Météo #HautsDeFrance #Prévisions #Climat #Orages #MétéoFrance



**

### Principales incertitudes
— Incertitudes majeures

1. **Fin de semaine 2** : Oppositions entre scénario anticyclonique (GFS) et maintien du flux d'ouest (CEP)
2. **Intensité orageuse** : Risque de phénomènes violents (grêle > 5 cm) impossible à localiser précisément à J+3
3. **Cumuls pluviométriques** : Variations de 10 à 30 mm selon la trajectoire des perturbations




## 📊 [GLOBAL_CONSENSUS_KPI] — Consensus des modèles : **Modéré**

**[GLOBAL_CONSENSUS_NOTE]** — Bonne convergence sur la semaine 1 (85%), nette divergence sur la fin de semaine 2 (55%). Le signal principal (fin de canicule, retour à la normale) est robuste.

## 🎭 [GLOBAL_SCENARIO_KPI] — Scénario dominant : **Flux océanique dépressionnaire**

**[GLOBAL_SCENARIO_NOTE]** — 60% de probabilité pour le maintien d'un régime d'ouest perturbé, 25% pour une amélioration anticyclonique en fin de période, 15% pour un scénario intermédiaire.

## ❓ [GLOBAL_UNCERTAINTY_KPI] — Incertitude globale : **Modérée**

**[GLOBAL_UNCERTAINTY_NOTE]** — Incertitude principalement liée à l'échéance J+8 et au-delà. Les prévisions à 3-5 jours restent fiables.



## 📱 [LINKEDIN_POST] — Publication LinkedIn

> 🌦️ **HAUTS-DE-FRANCE : FIN DE LA CANICULE, RETOUR D'UN TEMPS DE SAISON** 🌦️
> 
> La région bascule dans un régime océanique cette semaine !
> 
> 🔹 **Mardi** : Dernière journée chaude (26-28°C) avant la bascule
> 🔹 **Mercredi-Jeudi** : Dégradation orageuse, risque de grêle et rafales
> 🔹 **Vendredi** : Net rafraîchissement (20-22°C)
> 🔹 **Semaine prochaine** : Averses fréquentes, vent de Sud-Ouest, températures de saison
> 
> 📊 Les modèles s'accordent sur la fin de la canicule mais divergent pour le week-end du 6 septembre.
> 
> 💡 À suivre : le run CEP de ce soir pour affiner les prévisions !
> 
> #Météo #HautsDeFrance #Prévisions #Climat #Orages #MétéoFrance



**

### 🚨 Analyse des doutes et lacunes
- **Timing/Chronologie :** — Chronologie des phénomènes

- **Mercredi après-midi** : L'arrivée des orages par l'ouest est bien modélisée (confiance 80%), mais l'heure précise varie de ±3 heures (entre 14h et 17h)
- **Jeudi** : Le passage des orages s'étale de la mi-journée au soir selon les modèles
- **Vendredi** : La sortie de la dégradation est plus précoce dans GFS que dans CEP (matin vs après-midi)
- **Semaine 2** : Le timing de la possible amélioration est l'élément le plus incertain (samedi 6 ou dimanche 7 ?)



## 📍 [DOUBTS_LOCATION] — Localisation des phénomènes

- **Axe orageux mercredi** : Les modèles oscillent entre un axe Somme-Oise et un axe plus au nord (Pas-de-Calais)
- **Cumuls maximaux jeudi** : Répartis entre la Thiérache (20 mm selon CEP) et la région lilloise (15 mm selon ARPEGE)
- **Vent fort lundi prochain** : Le littoral est assurément concerné, mais l'étendue vers l'intérieur varie (±50 km)
- **Amélioration en fin de semaine 2** : La limite entre le sec et l'humide se positionne quelque part entre la Bretagne et la Belgique



## 💪 [DOUBTS_INTENSITY] — Intensité des phénomènes

- **Caractère violent des orages** : Probabilité de 25-35% pour de la grêle > 3 cm, principalement jeudi
- **Rafales** : L'épisode venteux de lundi (55-65 km/h) est le mieux modélisé ; les rafales orageuses restent imprévisibles
- **Cumuls de pluie** : Incertitude de ±30% sur les quantités totales (20-30 mm possibles sur l'Aisne)
- **Températures** : L'écart inter-modèles est de 2-3°C pour vendredi (le plus froid de la période)



## 📡 [MISSING_INFORMATION] — Informations manquantes

- **Données satellite en temps réel** : L'analyse de la convection actuelle (mardi matin) est limitée par la fraîcheur des dernières images
- **Observations sol in situ** : Le réseau de stations au sol dans l'est de l'Aisne est peu dense, limitant la précision des prévisions locales
- **Indices de sécheresse détaillés** : Les données SWI (Soil Water Index) par département ne sont disponibles que sur 2 jours
- **Bulletin vigileau spécifique** : Pas de données chiffrées précises sur les restrictions d'eau par arrondissement



## 🧩 [LOW_DOCUMENTED_MODELS] — Modèles peu documentés

- **ICON-EU** : Membres d'ensemble non disponibles sur les plateformes publiques (seulement le déterministe)
- **AROME-France** : Horizon limité à 48h, pas de vision au-delà de jeudi
- **GEM (Global Environnement Multiscale)** : Écart-type des membres difficile à évaluer
- **NMMB (NOAA)** : Écarté en raison de sa résolution trop grossière pour les phénomènes orageux



## 🖼️ [UNCERTAIN_IMAGES] — Incertitudes sur les graphiques

- **Cartes de précipitation GFS** : Les valeurs affichées sur Meteociel sont des moyennes de membre, non le scénario déterministe
- **Échéances au-delà de 240h** : Les cartes montrent des scénarios très divergents (parfois 50 mm d'écart)
- **Paramètres hauteur de neige** : Non pertinents à cette saison mais affichés par les modèles globaux
- **Indices d'instabilité CAPE/CIN** : La couche limite convective (CIN) est mal représentée dans les modèles régionaux à cette échéance



**
- **Localisation :** — Localisation des phénomènes

- **Axe orageux mercredi** : Les modèles oscillent entre un axe Somme-Oise et un axe plus au nord (Pas-de-Calais)
- **Cumuls maximaux jeudi** : Répartis entre la Thiérache (20 mm selon CEP) et la région lilloise (15 mm selon ARPEGE)
- **Vent fort lundi prochain** : Le littoral est assurément concerné, mais l'étendue vers l'intérieur varie (±50 km)
- **Amélioration en fin de semaine 2** : La limite entre le sec et l'humide se positionne quelque part entre la Bretagne et la Belgique



## 💪 [DOUBTS_INTENSITY] — Intensité des phénomènes

- **Caractère violent des orages** : Probabilité de 25-35% pour de la grêle > 3 cm, principalement jeudi
- **Rafales** : L'épisode venteux de lundi (55-65 km/h) est le mieux modélisé ; les rafales orageuses restent imprévisibles
- **Cumuls de pluie** : Incertitude de ±30% sur les quantités totales (20-30 mm possibles sur l'Aisne)
- **Températures** : L'écart inter-modèles est de 2-3°C pour vendredi (le plus froid de la période)



## 📡 [MISSING_INFORMATION] — Informations manquantes

- **Données satellite en temps réel** : L'analyse de la convection actuelle (mardi matin) est limitée par la fraîcheur des dernières images
- **Observations sol in situ** : Le réseau de stations au sol dans l'est de l'Aisne est peu dense, limitant la précision des prévisions locales
- **Indices de sécheresse détaillés** : Les données SWI (Soil Water Index) par département ne sont disponibles que sur 2 jours
- **Bulletin vigileau spécifique** : Pas de données chiffrées précises sur les restrictions d'eau par arrondissement



## 🧩 [LOW_DOCUMENTED_MODELS] — Modèles peu documentés

- **ICON-EU** : Membres d'ensemble non disponibles sur les plateformes publiques (seulement le déterministe)
- **AROME-France** : Horizon limité à 48h, pas de vision au-delà de jeudi
- **GEM (Global Environnement Multiscale)** : Écart-type des membres difficile à évaluer
- **NMMB (NOAA)** : Écarté en raison de sa résolution trop grossière pour les phénomènes orageux



## 🖼️ [UNCERTAIN_IMAGES] — Incertitudes sur les graphiques

- **Cartes de précipitation GFS** : Les valeurs affichées sur Meteociel sont des moyennes de membre, non le scénario déterministe
- **Échéances au-delà de 240h** : Les cartes montrent des scénarios très divergents (parfois 50 mm d'écart)
- **Paramètres hauteur de neige** : Non pertinents à cette saison mais affichés par les modèles globaux
- **Indices d'instabilité CAPE/CIN** : La couche limite convective (CIN) est mal représentée dans les modèles régionaux à cette échéance



**
- **Intensité :** — Intensité des phénomènes

- **Caractère violent des orages** : Probabilité de 25-35% pour de la grêle > 3 cm, principalement jeudi
- **Rafales** : L'épisode venteux de lundi (55-65 km/h) est le mieux modélisé ; les rafales orageuses restent imprévisibles
- **Cumuls de pluie** : Incertitude de ±30% sur les quantités totales (20-30 mm possibles sur l'Aisne)
- **Températures** : L'écart inter-modèles est de 2-3°C pour vendredi (le plus froid de la période)



## 📡 [MISSING_INFORMATION] — Informations manquantes

- **Données satellite en temps réel** : L'analyse de la convection actuelle (mardi matin) est limitée par la fraîcheur des dernières images
- **Observations sol in situ** : Le réseau de stations au sol dans l'est de l'Aisne est peu dense, limitant la précision des prévisions locales
- **Indices de sécheresse détaillés** : Les données SWI (Soil Water Index) par département ne sont disponibles que sur 2 jours
- **Bulletin vigileau spécifique** : Pas de données chiffrées précises sur les restrictions d'eau par arrondissement



## 🧩 [LOW_DOCUMENTED_MODELS] — Modèles peu documentés

- **ICON-EU** : Membres d'ensemble non disponibles sur les plateformes publiques (seulement le déterministe)
- **AROME-France** : Horizon limité à 48h, pas de vision au-delà de jeudi
- **GEM (Global Environnement Multiscale)** : Écart-type des membres difficile à évaluer
- **NMMB (NOAA)** : Écarté en raison de sa résolution trop grossière pour les phénomènes orageux



## 🖼️ [UNCERTAIN_IMAGES] — Incertitudes sur les graphiques

- **Cartes de précipitation GFS** : Les valeurs affichées sur Meteociel sont des moyennes de membre, non le scénario déterministe
- **Échéances au-delà de 240h** : Les cartes montrent des scénarios très divergents (parfois 50 mm d'écart)
- **Paramètres hauteur de neige** : Non pertinents à cette saison mais affichés par les modèles globaux
- **Indices d'instabilité CAPE/CIN** : La couche limite convective (CIN) est mal représentée dans les modèles régionaux à cette échéance



**
- **Informations manquantes :** — Informations manquantes

- **Données satellite en temps réel** : L'analyse de la convection actuelle (mardi matin) est limitée par la fraîcheur des dernières images
- **Observations sol in situ** : Le réseau de stations au sol dans l'est de l'Aisne est peu dense, limitant la précision des prévisions locales
- **Indices de sécheresse détaillés** : Les données SWI (Soil Water Index) par département ne sont disponibles que sur 2 jours
- **Bulletin vigileau spécifique** : Pas de données chiffrées précises sur les restrictions d'eau par arrondissement



## 🧩 [LOW_DOCUMENTED_MODELS] — Modèles peu documentés

- **ICON-EU** : Membres d'ensemble non disponibles sur les plateformes publiques (seulement le déterministe)
- **AROME-France** : Horizon limité à 48h, pas de vision au-delà de jeudi
- **GEM (Global Environnement Multiscale)** : Écart-type des membres difficile à évaluer
- **NMMB (NOAA)** : Écarté en raison de sa résolution trop grossière pour les phénomènes orageux



## 🖼️ [UNCERTAIN_IMAGES] — Incertitudes sur les graphiques

- **Cartes de précipitation GFS** : Les valeurs affichées sur Meteociel sont des moyennes de membre, non le scénario déterministe
- **Échéances au-delà de 240h** : Les cartes montrent des scénarios très divergents (parfois 50 mm d'écart)
- **Paramètres hauteur de neige** : Non pertinents à cette saison mais affichés par les modèles globaux
- **Indices d'instabilité CAPE/CIN** : La couche limite convective (CIN) est mal représentée dans les modèles régionaux à cette échéance



**
- **Modèles sous-documentés :** — Modèles peu documentés

- **ICON-EU** : Membres d'ensemble non disponibles sur les plateformes publiques (seulement le déterministe)
- **AROME-France** : Horizon limité à 48h, pas de vision au-delà de jeudi
- **GEM (Global Environnement Multiscale)** : Écart-type des membres difficile à évaluer
- **NMMB (NOAA)** : Écarté en raison de sa résolution trop grossière pour les phénomènes orageux



## 🖼️ [UNCERTAIN_IMAGES] — Incertitudes sur les graphiques

- **Cartes de précipitation GFS** : Les valeurs affichées sur Meteociel sont des moyennes de membre, non le scénario déterministe
- **Échéances au-delà de 240h** : Les cartes montrent des scénarios très divergents (parfois 50 mm d'écart)
- **Paramètres hauteur de neige** : Non pertinents à cette saison mais affichés par les modèles globaux
- **Indices d'instabilité CAPE/CIN** : La couche limite convective (CIN) est mal représentée dans les modèles régionaux à cette échéance



**
- **Incertitudes images :** — Incertitudes sur les graphiques

- **Cartes de précipitation GFS** : Les valeurs affichées sur Meteociel sont des moyennes de membre, non le scénario déterministe
- **Échéances au-delà de 240h** : Les cartes montrent des scénarios très divergents (parfois 50 mm d'écart)
- **Paramètres hauteur de neige** : Non pertinents à cette saison mais affichés par les modèles globaux
- **Indices d'instabilité CAPE/CIN** : La couche limite convective (CIN) est mal représentée dans les modèles régionaux à cette échéance



**


========================================

## 📝 PROPOSITION DE POST LINKEDIN
— Publication LinkedIn

> 🌦️ **HAUTS-DE-FRANCE : FIN DE LA CANICULE, RETOUR D'UN TEMPS DE SAISON** 🌦️
> 
> La région bascule dans un régime océanique cette semaine !
> 
> 🔹 **Mardi** : Dernière journée chaude (26-28°C) avant la bascule
> 🔹 **Mercredi-Jeudi** : Dégradation orageuse, risque de grêle et rafales
> 🔹 **Vendredi** : Net rafraîchissement (20-22°C)
> 🔹 **Semaine prochaine** : Averses fréquentes, vent de Sud-Ouest, températures de saison
> 
> 📊 Les modèles s'accordent sur la fin de la canicule mais divergent pour le week-end du 6 septembre.
> 
> 💡 À suivre : le run CEP de ce soir pour affiner les prévisions !
> 
> #Météo #HautsDeFrance #Prévisions #Climat #Orages #MétéoFrance



**