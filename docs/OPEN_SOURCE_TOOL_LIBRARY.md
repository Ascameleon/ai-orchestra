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


## 8. Nouveaux candidats examinés — cycle du 2026-11-17 (01:46, Africa/Algiers)

Comparaison effectuée avec les 11 entrées déjà présentes : les cinq dépôts ci-dessous n'étaient pas répertoriés. Ils complètent les outils existants sans les remplacer. Les SHA sont les derniers commits renvoyés par GitHub lors de cette vérification ; ils ne constituent pas une installation.

**Contexte projet relu avant sélection :** le dernier diagnostic Cycle 1 disponible dans l'historique consulté date du 2026-11-16 à 22:53 UTC ; le dernier résultat Cycle 2 disponible a démarré le 2026-11-17 à 00:04 UTC. Contrôle GitHub direct effectué pendant ce cycle : BLUE ALERTS PR #64 est toujours ouverte sur le head `0ee5d6727b86a0cf80e38db314263632b485ceca` ; le workflow #555 (run `43984743843`) présente un job `build` terminé avec succès et toutes les étapes rapportées réussies. Cela ne fusionne pas la PR et ne remplace pas un nouveau diagnostic Cycle 1. Ce contrôle confirme que les prochains besoins d'outillage prioritaires restent les tests Android reproductibles, la validation d'assets GLB, l'observabilité d'AI ORCHESTRA et la composition audiovisuelle de NIA.


| Outil | Dépôt / licence | Commit / version vérifiés | Fonction et conditions réelles | Projet cible / verdict |
|---|---|---|---|---|
| Maestro CLI | https://github.com/mobile-dev-inc/Maestro — Apache-2.0 (fichier LICENSE vérifié) | Commit `0ccf5a9c5b1c48d4cb6211d9060d537e04745107` (2026-11-13) ; release CLI `cli-2.12.1` publiée le 2026-11-02 | Tests UI/E2E Android, iOS et web par flux YAML ; CLI locale, Java 17+, émulateur ou appareil Android physique et hôte avec ADB autorisé. La release expose `maestro.zip` et `checksums_sha256.txt` : vérifier le SHA-256 avant exécution. Le script d'installation distant `curl | bash` n'a pas été exécuté. Maestro Studio est gratuit mais propriétaire/non open source ; Maestro Cloud est un service payant distinct. | Torcscandz / CallerID : **MAYBE — alternative légère à Appium à comparer sur un runner et un Samsung autorisé**. Ne remplace pas Appium sans benchmark. |
| fastlane | https://github.com/fastlane/fastlane — MIT (LICENSE vérifiée) | Commit `600714a2db5383e9e10fbfee271ba6d887c35c83` (2026-11-16) ; release `2.242.0` publiée le 2026-11-16 | Automatisation des builds, captures, métadonnées et releases Android/iOS. Installation recommandée via Bundler/Gemfile, Ruby >= 3.2 pour la version 2.242.0. Les builds locaux ne requièrent pas de service fastlane payant ; la publication Play Store nécessite compte, keystore et identifiants de service appropriés. Ne jamais stocker ces secrets dans le dépôt. Runner CI/PC requis ; pas une installation autonome sur Samsung. | Torcscandz / CallerID : **MAYBE — utile pour fiabiliser les builds et préparer les releases, publication bloquée sans secrets autorisés**. |
| Khronos glTF Validator | https://github.com/KhronosGroup/glTF-Validator — Apache-2.0 (LICENSE vérifiée) | Commit `602c54043ba66856b2e68c40fdf2bced975cdb8a` (2026-10-06) ; package npm observé `gltf-validator@2.0.0-dev.3.10`. Aucun endpoint GitHub `releases/latest` disponible lors de la vérification. | Valide la conformité glTF 2.0/GLB et produit un rapport JSON ; contrôle références, buffers, accessors, animations, images et extensions. API Node précompilée : `npm install --save-dev gltf-validator@2.0.0-dev.3.10`, puis `validateBytes(new Uint8Array(bytes))`. Aucun GPU nécessaire. Attention : reconstruire le CLI Dart depuis la source a une contrainte SDK `>=2.11.99 <3.0.0` dans `pubspec.yaml` ; préférer le package Node précompilé ou vérifier la toolchain Dart 2.x avant compilation. | Gameforge-3D / BLUE ALERTS : **MAYBE — complément de glTF Transform (validation de conformité, pas optimisation)** ; faire un essai sur une copie d'asset avant ajout CI. |
| OpenTelemetry Python API/SDK | https://github.com/open-telemetry/opentelemetry-python — Apache-2.0 (LICENSE vérifiée) | Commit `b4dff8c663110a866a5f263016679da25bd02f33` (2026-11-15) ; release `v1.45.2` publiée le 2026-10-29 | Traces et métriques déclarées stables dans le README ; signal logs encore en développement. Python >=3.10. Installation ciblée : `pip install opentelemetry-api==1.45.2 opentelemetry-sdk==1.45.2`. Aucun cloud requis si export local/console ; un exporter SaaS peut transmettre des données et générer des coûts. Instrumenter les agents, appels d'outils, latences et budgets sans enregistrer prompts, clés, données personnelles ou contenu sensible. | AI ORCHESTRA : **MAYBE — forte valeur pour observabilité, à intégrer seulement avec politique de redaction et test local**. Le dépôt contrib d'instrumentation reste séparé et ses packages sont annoncés beta ; ne pas le confondre avec le SDK de base. |
| MoviePy | https://github.com/Zulko/moviepy — MIT (LICENCE.txt vérifiée) | Commit `211e4b15f6ce4f34a6a9efbfff40590e43a68f77` (2026-08-26) ; `pyproject.toml` annonce `2.2.0` | Montage programmatique Python : découpe, concaténation, titres, compositing, effets, audio et export. Python >=3.9 ; dépendances NumPy, Pillow, OpenCV headless, imageio/imageio-ffmpeg et FFmpeg. Installation candidate : `pip install moviepy==2.2.0`. Fonctionne CPU mais les frames en tableaux NumPy peuvent consommer beaucoup de RAM et être plus lentes qu'un appel FFmpeg direct. La licence/configuration du binaire FFmpeg reste distincte. Le README signale que les mainteneurs recherchent de l'aide : surveiller la maintenance. | NIA Studio AI / production PixiPop : **MAYBE — montage/assemblage automatisé, pas génération IA ; benchmark mémoire/temps avant adoption**. |



**Complément de test exécuté après qualification :** une tentative d'installation isolée de `gltf-validator@2.0.0-dev.3.10` dans `/tmp/ascameleon-gltf-validator-smoke`, avec `npm install --ignore-scripts --no-audit --no-fund --save-exact`, a expiré après 120 secondes. `npm ls` a ensuite confirmé qu'aucun paquet n'était installé. Aucun smoke test Node n'a donc pu être exécuté. L'environnement temporaire dispose de Node 22.16.0 et Java 21, mais ne dispose ni d'ADB, ni du SDK Dart, ni de `nvidia-smi`. Cela bloque un essai Maestro sur appareil et la compilation Dart du CLI glTF dans cet environnement ; cela ne prouve pas une incompatibilité du paquet Node précompilé.

### 8.1 Installation et tests — statut exact de ce cycle

- Lecture du catalogue canonique sur `main` avant recherche : effectuée ; aucun doublon exact parmi ces cinq dépôts.
- Métadonnées GitHub, README, fichiers de licence et derniers commits consultés pour les cinq candidats.
- Releases vérifiées via GitHub pour Maestro, fastlane et OpenTelemetry ; aucun dernier release GitHub disponible pour glTF Validator.
- Aucun clone, binaire, paquet Python/Ruby/npm ou modèle n'a été installé dans un environnement de projet pendant ce cycle.
- Aucun smoke test d'exécution n'a été effectué. Les commandes ci-dessus sont des procédures préparées, pas des installations ni des tests réussis.
- Aucun code de production, workflow, dépendance ou sous-module Ascameleon n'a été modifié.
- Aucun coût, appel API payant ou secret utilisé.

### 8.2 Ordre de validation proposé aux cycles de développement

1. Gameforge-3D : exécuter glTF Validator sur une copie d'un GLB existant et conserver le rapport JSON ; comparer avec glTF Transform sans remplacer l'asset source.
2. Torcscandz / CallerID : comparer Maestro et Appium sur les mêmes scénarios UI, d'abord émulateur CI puis appareil Samsung autorisé.
3. AI ORCHESTRA : ajouter une instrumentation OTel minimale derrière configuration désactivable ; vérifier redaction et absence de sortie réseau non voulue.
4. NIA Studio AI : évaluer MoviePy sur un clip court, mesurer RAM, durée et synchronisation audio avant tout branchement.

Le catalogue compte désormais **16 entrées documentées** (11 précédentes + 5 candidats examinés). Les nouveaux statuts restent MAYBE jusqu'aux tests d'intégration.

## 9. Nouveaux outils examinés — cycle du 2026-11-17 (02:47, Africa/Algiers)

### Contexte des projets et diagnostics relus avant recherche

Le dernier résultat Cycle 1 disponible dans l'automatisation est encore celui du 2026-11-16 à 22:53 UTC ; il est donc antérieur aux derniers changements et ne doit pas être présenté comme un audit frais. Contrôle GitHub direct effectué pour actualiser les points bloquants :

- **AI ORCHESTRA — PR #57** reste ouverte sur `docs/clarify-provider-request-cap-not-spend-20261117`, head `3aef7144f446cc42e148392ee9828cd3d40a8d2e`. Les workflows « Continuous graduated engineering » #1107 et « Python CI » #1138 sont maintenant terminés avec succès : lint, tests sans appels fournisseurs, distributions, image conteneur, smoke test sans secrets et audit de dépendances. La PR n'est pas fusionnée.
- **BLUE ALERTS — PR #64** est fermée et fusionnée ; les PR artistiques #49 à #53 restent ouvertes. Ne pas confondre leur statut avec la validation du gameplay de chaque branche.
- **Torcscandz — PR #5** reste ouverte/brouillon ; le workflow Android APK #190 et le workflow de validation #55 sont réussis, y compris extraction de l'archive, préflight, permissions manifest et tests Dart. La validation réelle sur Samsung avec adaptateur ELM327 reste un contrôle physique séparé.
- Le catalogue canonique a été relu avant de retenir les candidats ci-dessous ; aucun des trois dépôts n'était déjà enregistré comme entrée distincte.

### 9.1 Nouveaux candidats qualifiés

| Outil | Dépôt / licence | Version ou snapshot vérifié | Utilité, dépendances et coûts | Cible / verdict |
|---|---|---|---|---|
| **FFmpeg** | https://github.com/FFmpeg/FFmpeg — code principalement LGPL-2.1-or-later ; certains composants optionnels GPL-2-or-later et quelques fichiers sous licences tierces. Le dépôt GitHub est un miroir du dépôt officiel ; les PR GitHub sont explicitement ignorées par les mainteneurs. | Snapshot miroir consulté : `82d767e969d30f9f6db24ef67576890cf3f487ba`. Release stable officielle consultée : `9.0.2`, publiée le 2026-09-18. Source canonique : https://git.ffmpeg.org/ffmpeg.git. | Outils `ffmpeg`, `ffprobe`, `ffplay` et bibliothèques de traitement/transcodage, extraction, muxing, sous-titres, filtres et audio. CPU utilisable ; accélération matérielle facultative. Pas d'API, de crédits ni d'abonnement requis. La configuration de compilation change les obligations : `--enable-gpl` active des composants GPL ; codecs, bibliothèques externes, brevets et conditions de redistribution doivent être contrôlés séparément. | NIA Studio AI / PixiPop : **PASS comme moteur local de traitement média isolé** ; **MAYBE pour l'embarquer ou redistribuer un binaire**, tant que sa configuration et les codecs ne sont pas audités. Ne remplace pas MoviePy : FFmpeg est le moteur bas niveau, MoviePy une API Python de composition. |
| **OpenTimelineIO** | https://github.com/AcademySoftwareFoundation/OpenTimelineIO — Apache-2.0, fichier `LICENSE.txt` vérifié. | Snapshot main : `bad7ab5a40ac1a95d9d78a87c95a688d8b57cf28`. Version stable documentée : `v0.18.0` ; `v0.18.1` est une pré-version publiée le 2026-11-09, non retenue comme version stable. | Modèle/API d'échange de timelines de montage : ordre, durée et références vers des médias externes ; ce n'est ni un conteneur média ni un moteur de rendu. README annonce Python 3.9 à 3.15. Installation candidate : `python -m pip install OpenTimelineIO==0.18.0`. Depuis v0.16, plusieurs adaptateurs (AAF, EDL, FCP XML, etc.) sont séparés dans `OpenTimelineIO-Plugins` et des dépôts distincts. Aucun service cloud ou GPU requis ; construction native C++ possible si aucun wheel adapté. | NIA Studio AI : **MAYBE** — intéressant si NIA reçoit un éditeur de timeline multi-format ; pas de besoin de timeline non linéaire confirmé aujourd'hui. Ne réalise pas l'encodage : associer à FFmpeg uniquement si une fonctionnalité de montage est réellement développée. |
| **ONNX Runtime** | https://github.com/microsoft/onnxruntime — MIT, fichier `LICENSE` vérifié. | Snapshot main : `01713b72cf4f929ea9c5d7ca4addcfe25e24a313`. Release GitHub affichée lors de la consultation : `v1.30.0`. | Moteur d'inférence local multiplateforme pour modèles au format ONNX. CPU par défaut ; providers d'exécution optionnels selon matériel. Android : package `onnxruntime-android` publié sur Maven ; NNAPI demande Android 8.1+ (Android 9+ recommandé), XNNPACK est aussi disponible dans le package Android. Pas d'API cloud obligatoire. Les poids ONNX et datasets ont leurs propres licences ; modèle, RAM, taille de l'AAR et support des opérateurs doivent être validés individuellement. | NIA Studio AI / futurs composants Android : **MAYBE** — utile pour exécuter localement des modèles ONNX légers (vision, classification, détection ou audio), mais ne remplace pas llama.cpp pour les modèles GGUF et ne rend pas automatiquement disponibles des modèles génératifs. Mesurer sur Samsung avant décision. |

### 9.2 Candidat étudié mais différé

| Candidat | Licence / snapshot | Décision et motif |
|---|---|---|
| GStreamer — https://github.com/GStreamer/gstreamer | LGPL-2.1-or-later pour le cœur ; snapshot consulté `ac94d5ab7eb9b9210bdd5fcaa1907f336c6b63a1`. Le README exige Meson >=1.4 et Ninja ; plusieurs plugins ont des dépendances et licences propres, certains plugins dépendent de composants GPL/AGPL activés explicitement. | **DIFFÉRÉ, pas intégré au catalogue actif** : excellent framework de pipelines temps réel et streaming, mais aucun besoin actuel de capture/live-streaming n'a été confirmé dans NIA ou les autres projets. FFmpeg couvre mieux les besoins batch immédiats avec moins de complexité. Réévaluer seulement si une vraie fonction streaming/capture apparaît. |

### 9.3 Installations et tests réellement effectués dans ce cycle

- **FFmpeg** était déjà présent dans l'environnement de travail sous forme de binaire système Debian : `ffmpeg 7.1.5-0+deb13u1`, avec `ffprobe` disponible. Test synthétique non destructif exécuté : génération d'une mire noire de 16×16 pendant 0,25 s via lavfi et sortie `null` ; résultat **PASS**. Ce n'est pas une installation depuis GitHub, ni une intégration à NIA. Attention : `ffmpeg -buildconf` révèle `--enable-gpl` et de nombreuses bibliothèques externes ; ne pas redistribuer ce binaire comme une build LGPL sans audit.
- **OpenTimelineIO 0.18.0** : tentative d'installation isolée avec `pip --target /tmp/ascameleon-otio-smoke` échouée avant téléchargement, à cause d'une résolution DNS indisponible dans l'environnement. Import Python ensuite absent. Statut : **NON INSTALLÉ, aucun smoke test**.
- **ONNX Runtime** : import Python contrôlé ; paquet absent. Aucune installation ni test d'inférence effectué.
- Aucun dépôt tiers n'a été cloné dans un dépôt de production ; aucun modèle, poids, binaire, clé ou service payant n'a été utilisé. Aucune dépendance Ascameleon ni aucun workflow n'a été modifié.

### 9.4 Commandes préparées — non exécutées sur les projets

FFmpeg (source officielle, compilation séparée ; choisir explicitement la politique de licence et auditer les codecs avant toute redistribution) :

```bash
git clone https://git.ffmpeg.org/ffmpeg.git
cd ffmpeg
./configure --disable-gpl --disable-nonfree
make -j2
```

OpenTimelineIO (environnement virtuel isolé ; les adaptateurs additionnels sont séparés) :

```bash
python -m venv .venv-otio
. .venv-otio/bin/activate
python -m pip install 'OpenTimelineIO==0.18.0'
python -c 'import opentimelineio as otio; print(otio.__version__)'
```

ONNX Runtime Python :

```bash
python -m pip install 'onnxruntime==1.30.0'
python -c 'import onnxruntime as ort; print(ort.__version__, ort.get_available_providers())'
```

Pour Android, utiliser le package Maven `com.microsoft.onnxruntime:onnxruntime-android` avec la version alignée sur le SDK retenu ; ne pas ajouter de dépendance Gradle à TorcScan ou CallerID avant un cas d'usage ONNX concret et un test de taille/performance.

### 9.5 État de la bibliothèque après ce cycle

- 16 entrées actives précédentes + **3 nouvelles entrées qualifiées ou conditionnelles** = **19 entrées documentées**.
- GStreamer examiné puis différé, sans être compté comme outil admis.
- Un smoke test FFmpeg réussi sur le binaire déjà présent ; aucune installation tierce persistante confirmée.
- Le cycle suivant doit comparer tout nouvel outil à ces 19 entrées et ne pas présenter FFmpeg comme fraîchement installé.


## 10. Cycle 4 — QA, accessibilité et sécurité (2026-11-17, 03:40 Africa/Algiers)

### 10.1 Diagnostics et état des projets relus avant la recherche

- Dernier résultat Cycle 1 disponible : exécution planifiée le 2026-11-16 à 22:53:41 UTC, terminée à 22:56:17 UTC. Aucun résultat Cycle 1 plus récent n'était disponible à 03:40 ; ce diagnostic est donc ancien et n'est pas présenté comme un audit frais.
- Inventaire GitHub actuel : neuf dépôts Ascameleon accessibles, tous avec branche par défaut `main`.
- **Torcscandz PR #5** : toujours ouverte et en brouillon. Le périmètre porte sur les permissions Bluetooth et le préflight Android ; la validation réelle sur Samsung avec adaptateur ELM327 reste nécessaire.
- **BLUE ALERTS** : plusieurs PR visuelles restent ouvertes (#45, #47, #48, #50, #52, #53). Leurs descriptions exigent des validations exact-head desktop/mobile et une inspection des captures ; les tests browser ne valent pas essai Samsung physique.
- **AI ORCHESTRA issue #46** : toujours ouverte dans l'API GitHub, mais son texte référence un ancien commit et un ancien workflow de lint. Elle est conservée comme signal historique à réexaminer, pas comme preuve d'un échec actuel.
- **Constat technique directement relu sur BLUE ALERTS main** : `.github/workflows/openrts-build.yml` utilise Node 22 et installe Playwright avec `npm install --no-save --no-package-lock playwright`, sans version explicite. `scripts/validate_v94_browser.mjs` importe `chromium` depuis `playwright`. Playwright est donc déjà utilisé par le pipeline, mais sa version n'est pas épinglée dans cette étape.

### 10.2 Nouveaux outils ajoutés au catalogue

| Outil | Dépôt / licence | Version ou commit exact | Fonctions, coûts et exigences | Projet cible / verdict |
|---|---|---|---|---|
| **Playwright** | https://github.com/microsoft/playwright — Apache-2.0 (fichier LICENSE vérifié) | Release stable `v1.65.0`, commit `a1f35e1955976e84411f9c10358228a80b763ebe`, publiée le 2026-11-05. Le `main` observé est déjà en `1.66.0-next` ; ne pas utiliser cette pré-version comme référence de production. | Automatisation navigateur Chromium/Firefox/WebKit, assertions web, traces, captures et scripts pour agents. Node.js 22/24/26 recommandé par les notes de release ; le package de la release déclare Node >=20. Aucun appel IA, crédit ou abonnement requis. Les navigateurs et dépendances système doivent être téléchargés séparément ; prévoir disque, RAM et CPU sur le runner. WebGL peut dépendre du backend graphique disponible. | BLUE ALERTS / TripBoost / NIA web : **PASS comme outil QA déjà utilisé dans BLUE ALERTS**. Épingler la version dans le workflow pour éviter que le dernier `latest` change entre deux exécutions. La simulation viewport 390×844 n'est pas un test sur Samsung physique. |
| **axe-core** | https://github.com/dequelabs/axe-core — MPL-2.0 (LICENSE vérifiée) | Release stable `v4.14.0`, commit `e797173108eadfa4355fe06af331791734e1757f`, publiée le 2026-10-05. Le package `v4.14.0` déclare `axe-core@4.14.0`. Le fichier `LICENSE-3RD-PARTY.txt` doit être conservé avec les notices MIT/ISC et autres composants tiers. | Moteur JavaScript d'audit accessibilité WCAG/ARIA pour pages HTML ; intégrable dans les tests Playwright. Aucun GPU, API ou abonnement nécessaire pour le cœur open source. L'outil ne trouve pas toutes les violations : le README annonce une moyenne d'environ 57 % de problèmes WCAG détectés automatiquement ; une revue manuelle reste indispensable. Les règles DOM ne peuvent pas auditer le contenu interne d'un canvas WebGL. Les extensions et offres Deque avancées sont distinctes et peuvent être payantes. | TripBoost et BLUE ALERTS HUD : **PASS comme candidat d'audit automatisé**, intégration et résultats projet encore à tester. Priorité aux formulaires, boutons, labels, focus clavier, contrastes et HUD HTML ; ne pas prétendre auditer la scène 3D elle-même. |
| **Betterleaks** | https://github.com/betterleaks/betterleaks — MIT (LICENSE vérifiée) | HEAD observé `7d3d40bb411a708a525c00f2fe8f0932f255c9c4` (2026-11-16). Le README indique que `main` porte le développement v2 ; la branche `v1.x` reste en maintenance. Le guide de migration présente encore `v2.0.0-rc.1` comme une release candidate à publier, sans version stable v2 confirmée pendant ce cycle. | Scanner de secrets configurable pour fichiers et historiques Git. En mode détection local par défaut, pas de requête fournisseur ; les options `--validate` / `--analyze` font des appels HTTP et doivent rester désactivées dans le cadre zéro dépense. Le code Go du snapshot main et de la branche v1.x déclare Go 1.26.0. Les scans de sources GitHub distantes nécessitent réseau et peuvent nécessiter des accès ; préférer d'abord un clone local. | AI ORCHESTRA et tous les dépôts : **MAYBE** — intérêt élevé pour prévenir les fuites de secrets, mais toolchain Go actuelle de cet environnement (1.23.2) incompatible et v2 non stabilisée. Ne pas installer ni activer de validation réseau avant une version stable et un runner compatible. |

### 10.3 Candidat examiné puis non retenu

- **Gitleaks** — https://github.com/gitleaks/gitleaks, licence MIT. Son README officiel annonce explicitement que le projet est « feature complete », que les évolutions fonctionnelles sont arrêtées et que les prochaines versions seront limitées aux correctifs de sécurité, l'auteur se concentrant sur Betterleaks. Le `go.mod` actuel déclare Go 1.24.11, supérieur au Go 1.23.2 disponible dans l'environnement de ce cycle. Décision : **non retenu comme nouvelle intégration** ; préférer réévaluer Betterleaks après stabilisation de v2. Cela ne signifie pas que les installations Gitleaks existantes cessent de fonctionner.

### 10.4 Procédures préparées — non exécutées dans les projets

Playwright, version stable exacte utilisée par le workflow BLUE ALERTS :

```bash
npm install --no-save --no-package-lock playwright@1.65.0
npx playwright install --with-deps chromium
```

Pour un projet qui possède un manifeste npm et un lockfile, préférer une dépendance de développement exacte et committer le lockfile plutôt que l'installation flottante actuelle.

axe-core, installation de développement exacte :

```bash
npm install --save-dev --save-exact axe-core@4.14.0
```

Exemple d'intégration dans un test Playwright existant, sans dépendance MCP ni service cloud :

```js
await page.addScriptTag({ path: require.resolve('axe-core') });
const accessibility = await page.evaluate(async () => axe.run(document));
if (accessibility.violations.length) {
  throw new Error(JSON.stringify(accessibility.violations));
}
```

Betterleaks : aucune commande d'installation n'est recommandée pour l'environnement courant. Avant toute adoption, obtenir un binaire/release stable dont le checksum est vérifié, ou un runner Go >=1.26 ; lancer exclusivement un scan local en mode détection, sans `--validate` ni `--analyze`.

### 10.5 Installation et tests réellement effectués pendant ce cycle

- Lecture du catalogue canonique sur `main` avant toute recherche : effectuée ; aucun des trois nouveaux dépôts n'était déjà une entrée distincte.
- Licence, README et manifeste vérifiés pour Playwright, axe-core et Betterleaks ; version stable Playwright et tag stable axe-core vérifiés séparément du HEAD de développement.
- État local de l'environnement : Node.js `v22.16.0`, npm `10.9.2`, Go `1.23.2`.
- Playwright et axe-core n'étaient pas installés dans l'environnement temporaire. Betterleaks/Gitleaks n'étaient pas installés.
- Tentative de résolution npm pour `axe-core@4.14.0` : échec réseau `EAI_AGAIN registry.npmjs.org`. Aucun paquet téléchargé ; aucun import ni test axe-core réussi.
- Aucun binaire Betterleaks/Gitleaks téléchargé ou exécuté. Aucun secret, token ou appel de validation fournisseur utilisé.
- Playwright a été confirmé comme dépendance installée à l'exécution dans le workflow GitHub BLUE ALERTS, mais aucune installation locale supplémentaire n'a été effectuée pendant ce cycle.
- Aucun code de production, workflow, lockfile, dépendance ou sous-module Ascameleon modifié pendant ce cycle.

### 10.6 État courant du catalogue

Le catalogue comprend maintenant **22 entrées documentées** : les 19 entrées des cycles précédents, plus Playwright, axe-core et Betterleaks. Gitleaks est documenté comme candidat non retenu, sans être compté dans les entrées admises.

Priorités proposées aux cycles suivants :
1. Épingler Playwright à une version stable exacte dans le workflow BLUE ALERTS, après validation par le Cycle 2.
2. Ajouter un audit axe-core non bloquant initialement sur les écrans HTML de TripBoost et le HUD BLUE ALERTS ; traiter les violations confirmées sans appliquer aveuglément toutes les règles.
3. Réévaluer Betterleaks seulement après disponibilité d'une release stable compatible avec un runner Go >=1.26 ; conserver les scans en détection locale sans validation réseau.
