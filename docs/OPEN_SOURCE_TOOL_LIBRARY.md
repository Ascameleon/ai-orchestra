# Bibliothèque centrale d'outils open source — Ascameleon

**État de qualification : 2026-11-17**  
**Dépôt de référence :** https://github.com/Ascameleon/ai-orchestra  
**Fichier :** docs/OPEN_SOURCE_TOOL_LIBRARY.md  
**But :** fournir aux cycles d'audit et de développement un catalogue versionné d'outils réutilisables, sans remplacer les applications existantes.

## 1. Règles d'admission

- PASS : dépôt public, code source et licence identifiés, fonction utile et procédure documentée.
- MAYBE : outil intéressant, mais dépendance matérielle, licence de modèles/voix, maintenance ou test d'intégration encore à confirmer.
- FAIL : licence absente/non vérifiée, dépôt trop risqué, exigences incompatibles ou utilité insuffisante pour le périmètre actuel.
- Une licence de code ne couvre pas automatiquement les poids des modèles, datasets, voix, plugins ou assets.
- « Open source » ne signifie pas « inférence gratuite sur le cloud » : les API, crédits et abonnements restent hors du périmètre.
- Aucun outil ci-dessous n'est déclaré installé dans un projet de production. Les SHA indiqués sont des instantanés de commits observés sur GitHub le 2026-11-17 ; les versions doivent être repinnées avant toute intégration.
- Installer un outil séparément, conserver ses notices et tester un exemple minimal avant de l'ajouter à une application.

## 2. État des projets Ascameleon pris en compte

| Projet | État observé dans le README de main | Besoin auquel la bibliothèque peut répondre |
|---|---|---|
| AI ORCHESTRA | API Python 3.11/3.12, adaptateurs fournisseurs optionnels, passerelle FreeLLMAPI locale configurable | Inférence locale, fournisseur OpenAI-compatible, outils de développement |
| Torcscandz / TorqScan | Sources Flutter restaurées en archives ; workflow Android avec Java 17 et Flutter 3.35.7 | Tests Android reproductibles et automatisation UI |
| BLUE ALERTS | Prototype HTML/Three.js et sous-module OpenRTS Java/jMonkeyEngine distincts | Optimisation des assets GLB, création 3D et tests |
| Tripradar / TripBoost | Comparateur de tarifs, interface map-first, redirection vers les sources | Outils web et QA ; aucun besoin de modèle génératif identifié dans le README |
| Gameforge-3D | Générateur procédural web, export GLB, sans génération IA prompt-to-3D | Inspection, compression et validation des GLB |
| NIA Studio AI | Source MIT 0.6.4 restaurée ; aucune inférence image/vidéo réelle démontrée ; ComfyUI reste un service externe optionnel | Backend local image/vidéo, transcription et voix |
| CallerID | Application Kotlin Android et services Go | Tests Android natifs et tests de régression |
| playwright-samsung | Dépôt documentaire ; Playwright Android expérimental et dépendant d'un hôte ADB | Complément de tests, sans prétendre au pilotage direct depuis le téléphone |
| ruflo | Harness d'agents de code | Références d'orchestration, à comparer avec les outils actifs |

## 3. Catalogue qualifié

### 3.1 Inférence locale et IA

| Outil | Dépôt / licence | Snapshot GitHub vérifié | Usage et dépendances | Cible / verdict |
|---|---|---|---|---|
| llama.cpp | https://github.com/ggml-org/llama.cpp — MIT | 9581154a2250cc9e6948e4c2a2fc4b4e19d1a57e | Moteur C/C++ pour exécuter des LLM localement ; serveur REST compatible OpenAI ; documentation de compilation Android. Pas d'API payante, mais les fichiers GGUF et leurs licences sont distincts. RAM, stockage, chauffe et vitesse dépendent du modèle et de la quantification. | AI ORCHESTRA : **PASS comme candidat d'adaptateur local**. Samsung : **MAYBE**, à mesurer sur l'appareil et un petit modèle. |
| ComfyUI | https://github.com/Comfy-Org/ComfyUI — GPL-3.0 | a308f3f1d2c49deb22e177af8f406c2607878db8 | Interface/API locale à graphes pour workflows de diffusion image et vidéo. Python 3.13 bien pris en charge dans le README consulté, PyTorch requis ; GPU fortement préférable, mode CPU possible mais lent. Les poids, LoRA, VAE et custom nodes ont leurs propres licences et dépendances. | NIA Studio AI : **PASS comme backend externe à étudier** ; matériel actuel : **MAYBE**, pas d'installation Android revendiquée. |
| whisper.cpp | https://github.com/ggml-org/whisper.cpp — MIT | aba02defd6bb6ff5de63721c21e3456645c153e2 | Reconnaissance vocale locale, CPU-only possible, quantification, Android et WebAssembly documentés. Les modèles sont téléchargés séparément ; vérifier leur provenance et licence. | NIA Studio AI : **PASS pour transcription/sous-titres** ; Samsung : **MAYBE**, benchmark nécessaire. |
| Cline | https://github.com/cline/cline — Apache-2.0 | 146894b6a42a7a554c6ff37f7bb33fe5122cc33d | Agent de code CLI/IDE/SDK ; accepte des fournisseurs hébergés et des modèles locaux via Ollama ou LM Studio. Le logiciel est libre, mais aucun modèle ni quota gratuit n'est inclus. Node.js et un hôte de développement sont nécessaires. | AI ORCHESTRA et développement : **MAYBE** ; ne pas le présenter comme une IA gratuite sans moteur local opérationnel. |
| OpenHands Agent Canvas | https://github.com/OpenHands/OpenHands — MIT | Version Docker documentée dans le README consulté : 1.41.0 | Centre de contrôle auto-hébergé pour agents et automatisations. Node.js 24+ et uv ; Docker recommandé pour isoler les agents. Les fournisseurs/modèles peuvent avoir leurs propres coûts. L'option sans sandbox donne à l'agent accès au système de fichiers : ne pas l'utiliser sans isolation. | Orchestration de développement : **MAYBE** ; nécessite un serveur/PC, pas un outil Samsung autonome. |

### 3.2 3D, jeux et assets

| Outil | Dépôt / licence | Snapshot GitHub vérifié | Usage et dépendances | Cible / verdict |
|---|---|---|---|---|
| glTF Transform | https://github.com/donmccurdy/glTF-Transform — MIT | 8e2a94a2616d293c4b503d0fb6a4b42e6ec7c62f ; CLI documentée : 4.5.1 | CLI Node.js pour inspecter et optimiser GLB/glTF, compresser géométrie et textures. Pas de GPU ni d'API nécessaires. Node.js LTS et npm. | Gameforge-3D et assets BLUE ALERTS : **PASS pour pipeline CI/desktop** ; pas une application Android. |
| Blender | https://github.com/blender/blender — GPL-3.0 | fa8c9b11b2ee5cc8691e6a22ee848762965027f0 | Suite complète de modélisation, rigging, animation, simulation, rendu, compositing et montage vidéo. Application desktop lourde ; GPU utile selon scènes. | Gameforge-3D / BLUE ALERTS : **PASS sur poste desktop**, **MAYBE** dans le contexte matériel actuel. |
| Godot Engine | https://github.com/godotengine/godot — MIT | 203bf0a23fd7d90a860917e66de08e20d2596244 | Moteur 2D/3D open source multi-plateforme ; export Android. Un moteur alternatif, pas une bibliothèque à injecter dans le prototype Three.js ou OpenRTS. | Nouveaux prototypes de jeu : **MAYBE** ; aucune migration des projets existants sans étude et validation séparées. |

### 3.3 Tests Android et production audiovisuelle

| Outil | Dépôt / licence | Snapshot GitHub vérifié | Usage et dépendances | Cible / verdict |
|---|---|---|---|---|
| Appium | https://github.com/appium/appium — Apache-2.0 | 51cfc7b292ab834a4155525927139a62e1e67aec | Automatisation native, hybride et mobile web via WebDriver. Serveur Node.js, driver UiAutomator2, JDK, Android SDK, ADB et appareil ou émulateur. Utilisation locale possible sans cloud. | Torcscandz et CallerID : **PASS comme candidat de test** ; validation physique bloquée tant qu'un hôte ADB/appareil autorisé n'est pas disponible. |
| Shotcut | https://github.com/mltframework/shotcut — GPLv3 | a95318e778bb1552118c0e7087012b24cae7bddc | Montage vidéo desktop ; dépend de Qt, MLT et bibliothèques multimédia. Le dépôt GitHub est exploitable, mais une compilation depuis les sources est destinée aux contributeurs ; privilégier les releases officielles. | Production NIA/PixiPop : **MAYBE**, desktop uniquement, pas une solution de montage sur Samsung. |
| Piper | https://github.com/OHF-Voice/piper1-gpl — GPL-3.0-or-later | d76f335d9eb5dea5ef6d7d70b2d6114e6303fa08 | Synthèse vocale locale Python/C++. Le moteur est GPL ; chaque voix possède une MODEL_CARD et une licence de données distincte. Le projet recherche des mainteneurs. | NIA/PixiPop : **MAYBE** ; vérifier voix, qualité, attribution et compatibilité avant toute utilisation ou redistribution. |

## 4. Procédures d'installation reproductibles

Les commandes suivantes sont des instructions préparées, pas des installations déjà exécutées dans les dépôts Ascameleon.

### glTF Transform — optimiser les modèles Gameforge

    npm install --global @gltf-transform/cli@4.5.1
    gltf-transform inspect input.glb
    gltf-transform optimize input.glb output.optimized.glb --texture-compress webp

Conserver le GLB original. Comparer taille, matériaux, animations et rendu avant de remplacer un asset.

### llama.cpp — préparer un backend local pour AI ORCHESTRA

    git clone https://github.com/ggml-org/llama.cpp.git
    cd llama.cpp
    cmake -B build
    cmake --build build --config Release -j

Utiliser ensuite un binaire/server compatible et un modèle GGUF dont la licence est contrôlée. Le README documente aussi un serveur REST compatible OpenAI. Avant de brancher AI ORCHESTRA, tester le endpoint local et vérifier qu'aucune requête ne sort vers un fournisseur payant.

### whisper.cpp — transcription locale pour NIA

    git clone https://github.com/ggml-org/whisper.cpp.git
    cd whisper.cpp
    cmake -B build
    cmake --build build -j

Télécharger un modèle adapté à la mémoire disponible, puis utiliser whisper-cli sur un WAV 16 kHz mono. Pour Android, suivre le dossier examples/whisper.android et les instructions NDK ; ne pas supposer que la compilation desktop produit un APK.

### ComfyUI — backend externe NIA

    git clone https://github.com/Comfy-Org/ComfyUI.git
    cd ComfyUI
    pip install -r requirements.txt
    python main.py

Avant le lancement, installer la variante PyTorch adaptée au GPU/CPU. Ajouter les poids uniquement après examen de leur licence individuelle. Ne pas incorporer tous les modèles dans l'archive NIA.

### Appium — tests Android

    npm install --global appium
    appium driver install uiautomator2
    appium driver list --installed
    appium

Configurer ensuite Java, Android SDK, ADB et les capacités de l'appareil. Pour un test Samsung, adb devices doit afficher l'appareil comme autorisé. Le serveur Appium s'exécute sur un hôte, pas automatiquement dans le navigateur du téléphone.

### Piper — voix locale

    python -m pip install piper-tts

Télécharger une voix seulement après lecture de sa MODEL_CARD et de la documentation de licence. Ne jamais déduire la licence d'une voix à partir de celle du moteur.

## 5. Outils non admis ou en attente

| Candidat | Motif de non-admission actuelle |
|---|---|
| Termux (termux/termux-app) | Compatibilité Android confirmée et version README v0.118.3 ; installation annoncée dès Android 7, environ 180 MB, avec avertissement de processus tués par Android 12+. La licence exacte n'a pas été confirmée dans ce cycle : ne pas le classer PASS avant vérification du fichier de licence. |
| moodpatcher/mesh-generator | Le README annonce NVIDIA GPU et Docker Desktop ; la licence propre du dépôt n'a pas été vérifiée. Les licences des modèles cités ne remplacent pas celle du dépôt. |
| senacula/senacula-shapestudio | Code annoncé Apache-2.0 et composants/poids à licences distinctes ; les tests décrits utilisent un moteur simulé et ne prouvent pas encore une génération complète sur GPU. À réévaluer après preuve d'une inférence réelle. |
| Kdenlive GitHub mirror | Le dépôt GitHub précise que le développement principal et les contributions se font sur KDE Invent. Ne pas traiter le miroir GitHub comme source canonique d'intégration. |
| SprocketVideo/Sprocket | État alpha ; licence et stabilité d'intégration à revalider avant admission. |

## 6. Ordre d'intégration recommandé

1. **Gameforge-3D :** tester glTF Transform sur une copie d'un GLB existant ; mesurer taille et rendu, puis envisager un job CI non destructif.
2. **AI ORCHESTRA :** évaluer llama.cpp comme fournisseur local OpenAI-compatible ; ne pas remplacer les adaptateurs existants.
3. **NIA Studio AI :** évaluer whisper.cpp pour transcription hors ligne ; conserver ComfyUI comme service optionnel, non embarqué.
4. **Torcscandz / CallerID :** préparer des tests Appium sur émulateur puis sur Samsung réel ; ne pas déclarer la validation matérielle sans appareil autorisé.
5. **BLUE ALERTS / Gameforge :** étudier Blender pour les assets ; Godot reste une piste de nouveau moteur, pas une migration.
6. **NIA / PixiPop :** comparer Shotcut et Piper sur un poste desktop ; contrôler la licence de chaque voix.

## 7. Résultat de ce cycle

- Dépôts Ascameleon relus : README des neuf dépôts principaux.
- Outils retenus : 11 entrées qualifiées ou conditionnelles.
- Licences contrôlées directement ou via la page officielle : MIT, Apache-2.0, GPL-3.0, GPL-3.0-or-later.
- Snapshots de commits enregistrés pour les dépôts avec commit récent identifié.
- Aucun code de production, dépendance de projet, sous-module ou workflow Ascameleon modifié.
- Aucune installation persistante confirmée. Un essai de lancement de glTF Transform via npx dans l'environnement temporaire a expiré sans résultat : il ne compte pas comme installation ni comme test réussi.
- L'environnement temporaire de ce cycle ne dispose pas de GPU NVIDIA détecté et ne remplace pas un poste desktop ni le Samsung réel.

**Règle pour les prochains cycles :** consulter ce catalogue avant d'ajouter une dépendance ; mettre à jour les commits/licences au moment de l'intégration ; conserver un test de non-régression ; ne jamais confondre interface open source, poids open-weight et inférence sans coût.
