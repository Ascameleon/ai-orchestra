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
| GStreamer — https://github.com/GStreamer/gstreamer | LGPL-2.1 vérifiée dans subprojects/gstreamer/COPYING et subprojects/gst-plugins-base/COPYING pour les composants concernés ; ne pas étendre cette licence à tous les plugins. HEAD observé b45c483edc7c7e4671d24a5ac4228835c7b029f3 (2026-11-17 04:42 UTC) ; release stable 1.28.9 (2026-11-06), version confirmée dans subprojects/gst-plugins-base/meson.build. Meson >=1.4 et Ninja ; le README précise que les bugs/merge requests sont suivis sur GitLab. | **DIFFÉRÉ, pas intégré au catalogue actif** : le cœur/default minimal est LGPL-2.1, mais les plugins optionnels peuvent être GPL ou soumis à des brevets/codecs ; vérifier gst-inspect-1.0 plugin par plugin. Le SDK Android publié sur la page officielle était encore 1.28.8 au contrôle du 2026-11-17, alors que la dernière release stable générale est 1.28.9 ; GStreamer >=1.28 cible Android API 24 et utilise NDK r25c. Le projet NIA n'a pas encore de besoin confirmé de capture/live-streaming ni de pipeline natif Android ; FFmpeg couvre mieux les traitements batch immédiats. Réévaluer seulement après spécification d'une fonction de streaming/capture ou d'un pipeline temps réel. |

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

## 11. Cycle 5 — tests Flutter, optimisation GLB et performance web (2026-11-17, 04:49 Africa/Algiers)

### 11.1 Diagnostics et état des projets relus avant la recherche

- Lecture du présent catalogue sur `main` avant toute recherche : effectuée. Les dépôts `leancodepl/patrol`, `zeux/meshoptimizer` et `GoogleChrome/lighthouse-ci` n'étaient pas déjà des entrées distinctes ; aucun doublon exact trouvé parmi les 22 entrées précédentes.
- Aucun rapport Cycle 1 plus récent n'a été retrouvé dans les issues GitHub consultables pendant cette exécution. Le dernier diagnostic Cycle 1 cité dans le catalogue reste celui du 2026-11-16 à 22:53:41 UTC ; il est ancien et n'est pas présenté comme un audit frais. Les états ci-dessous proviennent des branches et PR GitHub relues à 04:49.
- HEAD `main` relevés : `Torcscandz` `1c98135210eecb314ac67e526000d37ca3f99637` ; `ai-orchestra` `c6060145e20b4bfd3c6f52672fc2bb62fe84c1e9` ; `Tripradar` `7b36e7fbfc9afeafc9bfee32cec1f43640cea67b` ; `Blue-alert` `d700eeca20787fbe146f927b89ddd1272cefdc10` ; `Gameforge-3D` `83ff2cd33c6380a63843a39ee3bed882e9a3c11f` ; `Nia-studio-Ai` `029fb01e40fd784e62787a1b519880346ccf002a` ; `Callerid` `2c421c2efa038f80011a21b4874bb2105608ae04` ; `playwright-samsung` `842479e849ac6115500939702358b3d66a764e72` ; `ruflo` `056a11ece4ca3bd234aafd6221156d24b80a9544`.
- **Torcscandz** : README `main` confirme que les sources Flutter sont conservées dans `DzTorqscan_v1.4.0_complete.zip` et extraites par le workflow ; la racine n'a pas de `pubspec.yaml`. Le workflow documenté utilise Java 17 et Flutter 3.35.7. PR #5 reste ouverte et en brouillon ; la validation Samsung + adaptateur OBD2 reste une barrière physique.
- **BLUE ALERTS** : le workflow `openrts-build.yml` installe Playwright sans version fixe (`npm install --no-save --no-package-lock playwright`). PR #52 et #53 sont ouvertes et leurs critères demandent des captures fraîches du head exact ; la PR #52 précise que les captures de son prédécesseur avaient été jugées trop subtiles. Les captures 390×844 sont de l'émulation navigateur, pas un essai Samsung.
- **Gameforge-3D** : README `main` décrit 11 assets procéduraux, export GLB, runtime Three.js 0.160.1 local et usage navigateur sans backend. Il n'y a pas de `package.json` à la racine ; un optimiseur natif doit donc rester un outil de pipeline facultatif, pas une dépendance runtime.
- **TripBoost** : README `main` décrit une PWA map-first sans build frontend obligatoire ; le serveur API exige Node.js 24+ et des identifiants Amadeus pour les recherches live. Un audit Lighthouse local peut tester le shell statique sans clé Amadeus ni appel fournisseur.

### 11.2 Nouveaux outils qualifiés

| Outil | Dépôt / licence | Version ou commit exact | Fonction, coûts et exigences | Projet cible / verdict |
|---|---|---|---|---|
| **Patrol** | https://github.com/leancodepl/patrol — Apache-2.0 (`LICENSE` vérifiée) | HEAD `afd136cfd7f27458a5987b96f52711b3434a6f92` (2026-11-10) ; package `patrol` `4.11.0`, package CLI `patrol_cli` `4.9.0` dans les `pubspec.yaml` ; tags GitHub publiés le 2026-11-02 | Framework Flutter-first de tests UI/E2E avec interactions natives (permissions, notifications, WebView, paramètres système). Core utilisable localement, sans API ni cloud obligatoire ; services de support/valeur ajoutée du mainteneur séparés. Exige Flutter >=3.32.0, Dart >=3.8.0, Android SDK/JDK/ADB et émulateur ou appareil autorisé. | Torcscandz : **MAYBE — candidat prioritaire**. Le Flutter 3.35.7 déclaré par le workflow dépasse le minimum du package. Les sources étant archivées, l'intégration doit être faite dans l'arbre extrait par CI ou dans l'archive source après revue ; aucun `pubspec.yaml` racine n'existe. Patrol peut vérifier les flux de permissions et l'UI, mais ne prouve pas à lui seul le dialogue réel avec un ECU/ELM327. |
| **meshoptimizer / gltfpack** | https://github.com/zeux/meshoptimizer — MIT (`LICENSE.md` vérifiée) | Release stable `v1.3` publiée le 2026-09-25 ; HEAD `f0a684f11ead064e176775c9b796f82a55910e92` (2026-10-14). Archive Linux officielle `gltfpack-ubuntu.zip`, SHA-256 `0666d9dc40d60fe5b9a45f3fc24f8e6ca87112974bd5de9ca57152aa13d06017`. | Bibliothèque C/C++ d'optimisation de maillages et outil natif `gltfpack` pour optimiser les fichiers glTF/GLB, index/vertex buffers, simplification et compression. Pas de GPU ni d'API nécessaires ; compilation CMake ou binaire précompilé selon OS. Prévoir CPU et conserver les originaux : simplification/quantification peut modifier l'apparence ou les animations. | Gameforge-3D / BLUE ALERTS : **PASS comme outil de pipeline candidat** ; il complète mais chevauche partiellement glTF Transform. N'adopter qu'après comparaison A/B sur copies d'assets (taille, géométrie, matériaux, animations et rendu desktop/mobile). Ne pas l'ajouter au runtime navigateur. |
| **Lighthouse CI** | https://github.com/GoogleChrome/lighthouse-ci — Apache-2.0 (`LICENSE` vérifiée) | Release GitHub `v0.16.1` publiée le 2026-11-11 ; HEAD `99fc5efd774fcf85548a3b11ba019c3484ebe2a0` (2026-11-12). Le README recommande `@lhci/cli@0.16.x`. Le manifeste `packages/cli/package.json` du `main` consulté déclare `engines.node >=22.19.0` et une version interne `0.1.0` : vérifier le package publié/tag avant verrouillage de dépendance, cette différence de métadonnées mérite une vérification. | Collecte et assertions Lighthouse automatisées : performance, accessibilité, SEO, PWA/offline, budgets d'assets et régressions. CLI locale et GitHub Actions sans service payant requis. L'option d'upload `filesystem` garde les rapports dans `.lighthouseci/` ; éviter `temporary-public-storage` et le serveur partagé pour les données privées. Chrome/Chromium, Node >=22.19.0, CPU/RAM et espace pour navigateur requis ; pas de GPU obligatoire. | TripBoost / NIA Studio AI : **MAYBE — utile pour un audit de shell web local**. Le runtime de ce cycle est Node 22.16.0, donc inférieur au minimum actuel du manifeste ; un runner Node 24 est préférable. Commencer non bloquant et avec upload `filesystem` uniquement. |

### 11.3 Procédures reproductibles préparées — non exécutées

Patrol, dans le dossier Flutter extrait du ZIP Torcscandz, après vérification du `pubspec.yaml` et de la version Dart réellement extraite :

```bash
flutter pub add --dev patrol:^4.11.0
dart pub global activate patrol_cli 4.9.0
patrol test
```

meshoptimizer, en privilégiant le binaire Linux officiel épinglé et son checksum publié :

```bash
curl -L -o gltfpack-ubuntu.zip https://github.com/zeux/meshoptimizer/releases/download/v1.3/gltfpack-ubuntu.zip
echo '0666d9dc40d60fe5b9a45f3fc24f8e6ca87112974bd5de9ca57152aa13d06017  gltfpack-ubuntu.zip' | sha256sum -c -
unzip gltfpack-ubuntu.zip -d gltfpack-v1.3
./gltfpack-v1.3/gltfpack -i original.glb -o optimized.glb
```

Comparer ensuite les rapports d'inspection glTF, le nombre de primitives/triangles, les matériaux, animations, taille finale et captures identiques avant de promouvoir un asset optimisé.

Lighthouse CI, après lancement du shell TripBoost sur un port local (sans renseigner de secret Amadeus pour l'audit statique) :

```bash
npx --yes @lhci/cli@0.16.1 collect --url=http://127.0.0.1:4173/
npx --yes @lhci/cli@0.16.1 assert
npx --yes @lhci/cli@0.16.1 upload --target=filesystem
```

Le serveur LHCI, les tokens GitHub et les stockages publics ne sont pas nécessaires pour cette première évaluation. Épingler Node 24 sur le runner si le manifeste de la version publiée confirme le minimum Node 22.19.

### 11.4 Installation et tests réellement effectués pendant ce cycle

- Lecture du catalogue canonique sur `main` et comparaison des trois dépôts : effectuées ; aucun doublon distinct trouvé.
- Vérification GitHub des métadonnées, branches, commits, licences, README, versions de packages/releases et exigences techniques : effectuée pour les trois candidats.
- Inspection directe de `Torcscandz/README.md`, de la racine et du workflow de build documenté : confirme les sources Flutter en ZIP, Flutter 3.35.7 et Java 17. La récupération directe de `pubspec.yaml` à la racine a renvoyé 404, cohérente avec l'organisation en archives ; aucun fichier source embarqué n'a été modifié.
- Inspection directe de `Gameforge-3D/README.md` et de la racine : confirme le générateur procédural navigateur et l'export GLB ; aucun manifeste npm racine trouvé.
- Inspection directe du workflow BLUE ALERTS : confirme l'installation Playwright sans version épinglée dans le job de rendu navigateur.
- Environnement local contrôlé : Node.js `v22.16.0`, npm `10.9.2`, CMake `3.31.6`, Go `1.23.2` ; Flutter, Dart et ADB absents.
- Aucun outil nouveau installé. Aucun test d'import, de compilation Patrol, de traitement GLB avec gltfpack ou de collecte Lighthouse n'a été exécuté. Les commandes ci-dessus sont des procédures préparées, pas des tests réussis.
- Motif des blocages : absence de Flutter/Dart/ADB pour Patrol ; aucun checkout/asset GLB de projet disponible pour un benchmark meshoptimizer ; Node 22.16.0 inférieur au minimum 22.19.0 du manifeste Lighthouse CI. Aucun téléchargement de binaire ni script distant exécuté.
- Aucun code de production, workflow, lockfile, sous-module ou archive source Ascameleon modifié pendant ce cycle. Aucun secret lu ou utilisé, aucune API fournisseur payante appelée, aucune dépense.

### 11.5 Candidat examiné puis différé

- **KTX-Software** — https://github.com/KhronosGroup/KTX-Software — Apache-2.0 pour le cœur, avec notices et dépendances tierces à conserver. La release `v4.3.2` fournit les outils KTX2 et une voie Java/JNI, mais le pipeline actuel Gameforge/BLUE ALERTS ne documente pas encore de besoin confirmé de textures KTX2/Basis. Différé pour éviter d'ajouter un second pipeline de textures avant un benchmark ; ne pas confondre la licence du cœur avec celles des composants tiers et des codecs/actifs.

### 11.6 État du catalogue après ce cycle

- **25 entrées documentées** : 22 entrées précédentes + Patrol, meshoptimizer/gltfpack et Lighthouse CI. KTX-Software est différé et n'est pas compté comme entrée admise.
- Priorités proposées : (1) intégrer un test Patrol dans le workflow qui extrait TorcScan, d'abord sur émulateur, puis sur Samsung autorisé ; (2) comparer gltfpack v1.3 à glTF Transform sur des copies d'assets Gameforge/BLUE ALERTS ; (3) faire un audit Lighthouse CI local de TripBoost avec Node 24 et stockage filesystem.
- Le cycle suivant doit relire ce fichier sur `main`, actualiser les commits/licences et ne pas annoncer d'installation avant un smoke test réellement exécuté.

## 12. Cycle 6 — gestion reproductible des dépendances Python (2026-11-17, 05:43 Africa/Algiers)

### 12.1 Diagnostics et état des projets relus avant la recherche

- Le catalogue canonique a été lu sur `main` avant la recherche. `astral-sh/uv` n'y figurait pas : aucun doublon exact.
- Aucun nouveau rapport Cycle 1 n'a été retrouvé dans les issues recherchées d'`Ascameleon/ai-orchestra`. Le dernier diagnostic Cycle 1 documenté dans le catalogue reste celui du 2026-11-16 à 22:53:41 UTC ; il est ancien et n'est pas présenté comme un diagnostic frais.
- Dépôts existants contrôlés via GitHub : neuf dépôts accessibles, tous avec `main` comme branche par défaut. Les derniers heads documentés au cycle précédent restent les références de travail : ai-orchestra `9668220f8cdf7248ddb499bd123416c4bf2af60b`, BLUE ALERTS `d700eeca20787fbe146f927b89ddd1272cefdc10`, Torcscandz `1c98135210eecb314ac67e526000d37ca3f99637`, Tripradar `7b36e7fbfc9afeafc9bfee32cec1f43640cea67b`, Gameforge-3D `83ff2cd33c6380a63843a39ee3bed882e9a3c11f`, NIA Studio AI `029fb01e40fd784e62787a1b519880346ccf002a`, CallerID `2c421c2efa038f80011a21b4874bb2105608ae04`.
- **AI ORCHESTRA** : `pyproject.toml` définit des plages de versions compatibles (FastAPI, Uvicorn, Pydantic, Google GenAI, extras fournisseurs) et le dépôt ne contient pas de `uv.lock`. `.github/workflows/ci.yml`, `nightly-audit.yml` et `continuous-engineering.yml` installent les dépendances avec `pip install -e ".[dev]"` ; Docker utilise aussi pip. Il existe donc un besoin concret de reproductibilité, mais aucune migration de gestionnaire n'est autorisée par ce cycle.
- **BLUE ALERTS** : PR #65 est toujours ouverte sur la branche `fix/blue-alerts-pin-playwright-1.65.1-20261117`, commit `b54b7c90619f9bc9a17fad3cf8a7163f418265a3`. Le workflow exact-head #557 (run `44014390431`) est terminé avec succès : toutes les étapes, y compris le rendu 3D desktop/mobile, le build OpenRTS et les tests natifs sélection/déplacement/attaque, sont vertes. Cependant, le workflow de `main` relu sur `d700eec` installe encore Playwright sans version fixe ; la correction n'est pas intégrée tant que la PR reste ouverte.
- Aucun besoin neuf d'outil génératif local n'a été confirmé dans les autres dépôts pendant ce passage ; aucun outil image/vidéo/3D/Android supplémentaire n'est admis uniquement pour augmenter le nombre d'entrées.

### 12.2 Nouvel outil qualifié

| Outil | Dépôt / licence | Version ou commit exact | Fonction, coûts et exigences | Projet cible / verdict |
|---|---|---|---|---|
| **uv** | https://github.com/astral-sh/uv — dual licence MIT ou Apache-2.0 ; `LICENSE-MIT`, `LICENSE-APACHE` et champ `license = "MIT OR Apache-2.0"` vérifiés dans le manifeste du tag. | Release stable `0.13.8`, publiée le 2026-11-12 ; commit signé `3d97a6aad5ad989c1b4fc89406d54f0dce370b72`. `pyproject.toml` du tag confirme `version = "0.13.8"`. | Gestionnaire de projets/environnements Python écrit en Rust : résolution, lockfile universel `uv.lock`, synchronisation exacte, exécution, outils Python et export de lockfile. Utilisation locale sans API, crédit, abonnement ni cloud propriétaire. Les installations de paquets nécessitent un index réseau (PyPI ou miroir) et peuvent exécuter le code de build des distributions source ; examiner les sources et dépendances, éviter les index non fiables. Binaire précompilé pour Linux x86_64/ARM64, macOS et Windows ; aucun GPU requis, consommation CPU/RAM faible pour la gestion mais stockage et réseau proportionnels aux dépendances. Aucun support Android/Samsung natif revendiqué : outil de poste/CI, pas application mobile. | AI ORCHESTRA : **PASS comme candidat de reproductibilité CI/desktop**. Le dépôt possède déjà un `pyproject.toml` mais pas de lockfile ; évaluer d'abord une branche expérimentale ou un job CI non bloquant. Ne pas remplacer pip/Docker ou modifier les plages de dépendances avant comparaison complète des résolutions Python 3.11 et 3.12. |

### 12.3 Procédure d'installation et d'évaluation — non exécutée dans le dépôt

Installation d'une version Python publiée :

```bash
python -m pip install --user uv==0.13.8
uv --version
```

Alternative : télécharger l'archive binaire correspondant à l'architecture depuis la release GitHub `0.13.8`, vérifier le SHA-256 indiqué sur cette page avant extraction, puis placer le binaire `uv` dans un répertoire utilisateur. La release documente aussi la vérification d'attestation GitHub avec `gh attestation verify`. Pour compiler depuis la source, utiliser le tag exact `0.13.8` et une toolchain Rust compatible ; cette compilation n'a pas été nécessaire pour le smoke test.

Pour AI ORCHESTRA, procédure d'évaluation proposée dans une branche isolée (ne pas exécuter sur `main` sans revue) :

```bash
uv lock
uv lock --check
uv sync --locked --all-extras
uv run --locked --python 3.11 pytest
uv run --locked --python 3.12 pytest
```

Le dépôt possède plusieurs extras fournisseurs ; avant `--all-extras`, vérifier que leur résolution n'introduit pas de dépendance fournisseur inutilisée ou de contrainte incompatible. Le job de production doit rester sur son chemin pip actuel tant que les deux matrices Python et la construction Docker n'ont pas été comparées.

### 12.4 Installation et tests réellement effectués pendant ce cycle

- Lecture du catalogue sur `main) et comparaison anti-doublon : effectuées ; `uv` n'était pas présent.
- Vérification du dépôt original, README, manifestes `pyproject.toml`, `LICENSE-MIT`, `LICENSE-APACHE`, `SECURITY.md`, tag/release `0.13.8` et commit signé : effectuée.
- État du dépôt AI ORCHESTRA : `pyproject.toml` relu ; absence de `uv.lock` confirmée par réponse GitHub 404 ; usages de pip repérés dans README, Dockerfile et workflows CI/nightly/engineering.
- Environnement temporaire : un binaire préexistant `uv 0.10.0` a été trouvé. Il n'a pas été mis à jour ni remplacé. Un projet minimal sans dépendances, créé dans un répertoire temporaire puis supprimé, a passé `uv lock --offline`, `uv lock --check`, `uv sync --offline --no-install-project` et `uv run --offline python -c ...` ; sortie finale : `uv smoke test: ok`. Ce test valide seulement le binaire préexistant 0.10.0 et le flux minimal de lock/sync, pas la release 0.13.8 ni AI ORCHESTRA.
- Aucun téléchargement ou installation de `uv 0.13.8`, aucune création de `uv.lock` dans AI ORCHESTRA et aucune modification de dépendance ou de workflow Ascameleon n'ont été effectués.
- Aucun coût, aucune API payante, aucun secret et aucun changement de production.

### 12.5 État du catalogue et priorités suivantes

- **26 entrées documentées** : 25 entrées précédentes + `uv`. Aucun autre candidat n'a été ajouté pendant ce cycle.
- Le smoke test local de `uv 0.10.0` est consigné séparément du candidat `0.13.8` ; aucune installation nouvelle n'est revendiquée.
- Priorités :
  1. Cycle 2 : intégrer la PR BLUE ALERTS #65 seulement après contrôle final, car son exact-head workflow #557 est vert mais `main` utilise encore une installation Playwright flottante.
  2. Cycle 2 : évaluer `uv 0.13.8` dans une branche non bloquante d'AI ORCHESTRA ; générer le lockfile sans changer les contraintes, comparer les résolutions Python 3.11/3.12 et vérifier Docker.
  3. Cycle 1 : rafraîchir le diagnostic des dépôts, car le dernier rapport retrouvé est daté du 2026-11-16.

## 13. Cycle 7 — tests contractuels et fuzzing des API FastAPI (2026-11-17, 06:43 Africa/Algiers)

### 13.1 Diagnostics et état des projets relus avant la recherche

- Lecture du catalogue canonique sur `main` avant la recherche : effectuée. `schemathesis/schemathesis` ne figurait pas parmi les 26 entrées documentées ; aucun doublon exact trouvé.
- Recherche des diagnostics Cycle 1 : aucune issue ouverte ou résultat correspondant à « Cycle 1 » n'a été trouvé dans `Ascameleon/ai-orchestra`. Le dépôt ne contient pas de rapport Cycle 1 récent dans son arbre `docs` ; le diagnostic historique le plus récent documenté dans ce catalogue reste celui du 2026-11-16 à 22:53 UTC. Il est ancien et n'est pas présenté comme un audit actuel.
- État GitHub rafraîchi avant sélection : `ai-orchestra/main` = `c0123151e7e6b57d37e3a0de0b4dd248c2e64fde` ; PR ouvertes AI ORCHESTRA = aucune ; issues ouvertes AI ORCHESTRA = aucune. Les workflows Python CI et Continuous graduated engineering sur ce commit sont terminés avec succès (runs `44019425816` et `44019425831`).
- `Blue-alert/main` inclut maintenant le commit `e1b629197ee93435d1c8616927bb452ccfc2854d`. La PR #65 est fusionnée le 2026-11-17 à 04:57:38 UTC ; le workflow post-fusion `44020714781` est terminé avec succès.
- `Torcscandz/main` reste au commit `1c98135210eecb314ac67e526000d37ca3f99637`. PR #5 est toujours ouverte et en brouillon sur `421f03d334f8b98100986628fda51e025b1e2eb5`; l'essai Samsung + adaptateur ELM327 n'est pas remplacé par les tests de CI.
- `Gameforge-3D`, `Nia-studio-Ai` et `Callerid` ont des workflows récents terminés avec succès sur leurs derniers commits connus. Aucune issue ouverte n'a été trouvée dans les dépôts prioritaires consultés. Les succès CI ne démontrent pas l'inférence locale de NIA ni le fonctionnement sur un Samsung physique.

### 13.2 Nouvel outil qualifié

| Outil | Dépôt / licence | Version ou commit exact | Fonctions, dépendances, coûts et exigences | Projet cible / verdict |
|---|---|---|---|---|
| **Schemathesis** | https://github.com/schemathesis/schemathesis — MIT ; texte intégral de `LICENSE` vérifié sur le tag. | Release stable `v4.33.4`, publiée le 2026-11-12 ; tag annoté signé et vérifié ; commit cible `c570c690cdbfc70e9d79f04fac1025ecfb23711f`. `pyproject.toml` du tag confirme `version = 4.33.4` et `requires-python = >=3.11`. Dépôt actif : dernier push observé 2026-11-17T00:32:04Z. | Tests génératifs d'API à partir d'OpenAPI, GraphQL et gRPC ; génère des entrées limites, vérifie conformité des réponses et peut enchaîner des opérations stateful. CLI locale, plugin pytest, rapports HTML hors ligne et JUnit/JSON ; aucune API, clé, GPU, souscription ou cloud n'est nécessaire pour le moteur de base. Dépendances déclarées : Hypothesis, hypothesis_graphql, jsonschema_rs, pytest, requests, anyio, PyYAML et autres bibliothèques Python. Python >=3.11, donc compatible avec la matrice AI ORCHESTRA 3.11/3.12. CPU/RAM variables selon le schéma et le nombre d'exemples ; pas de GPU. La fonction de test envoie de vraies requêtes HTTP et peut créer, modifier ou supprimer des données : exécution uniquement sur une instance locale de test avec base jetable et données synthétiques. Les fonctions Schemathesis Cloud/SaaS sont distinctes et inutiles pour l'usage local. | AI ORCHESTRA : **PASS comme candidat de test contractuel local ; MAYBE pour intégration CI** tant qu'une allowlist d'opérations sans fournisseur payant, un serveur local isolé et un premier run reproductible n'ont pas été validés. Ne jamais cibler production. Ne pas exposer les secrets d'authentification dans les rapports. Hypothesis est une dépendance de Schemathesis et n'est pas compté comme une entrée séparée dans ce cycle. |

Preuves principales :
- Dépôt : https://github.com/schemathesis/schemathesis
- Release : https://github.com/schemathesis/schemathesis/releases/tag/v4.33.4
- Licence : https://github.com/schemathesis/schemathesis/blob/v4.33.4/LICENSE
- Manifeste et contraintes Python/dépendances : https://github.com/schemathesis/schemathesis/blob/v4.33.4/pyproject.toml
- Politique de sécurité : https://github.com/schemathesis/schemathesis/blob/v4.33.4/SECURITY.md
- Documentation : https://schemathesis.readthedocs.io/en/stable/

### 13.3 Procédure d'installation préparée — non exécutée

Installation épinglée dans un environnement isolé, jamais dans l'environnement de production :

```bash
python -m venv .venv-schemathesis
. .venv-schemathesis/bin/activate
python -m pip install "schemathesis==4.33.4"
st --version
```

Pour AI ORCHESTRA, lancer d'abord une instance de test sur `127.0.0.1`, sans clé fournisseur, sans secrets réels et avec une base de données jetable. Construire un schéma d'essai qui ne contient que les opérations déterministes et sans effet externe. Exclure au minimum les endpoints qui peuvent déclencher une dépense ou une requête réseau non souhaitée : `POST /v1/tasks`, `POST /v1/claims/assess-support` et `POST /v1/evidence/fetch`. Les endpoints mutateurs doivent être testés seulement si leurs effets sont isolés et réinitialisés entre les runs. Conserver les rapports localement ; ne pas utiliser de service cloud ou de stockage public.

Exemple CLI de base, à adapter à une instance locale de test et à une spécification filtrée :

```bash
st run http://127.0.0.1:8000/openapi.json --report junit --report-dir .artifacts/schemathesis
```

Avant de mettre le contrôle en CI, définir un budget d'exemples/durée et une liste explicite d'opérations autorisées ; les tests génératifs peuvent révéler des comportements coûteux ou mutateurs si le périmètre n'est pas limité.

### 13.4 Installation et tests réellement effectués pendant ce cycle

- Lecture du catalogue `main` et comparaison anti-doublon : effectuées ; Schemathesis n'était pas présent.
- Vérification du dépôt original, du README, du tag/release `v4.33.4`, du commit cible `c570c690cdbfc70e9d79f04fac1025ecfb23711f`, du manifeste `pyproject.toml`, du fichier `LICENSE`, de `SECURITY.md` et du changelog : effectuée.
- Contrôle de compatibilité : Python >=3.11 correspond à AI ORCHESTRA 3.11/3.12 ; la CLI peut fonctionner localement sans GPU ni service cloud.
- Tentative réelle d'installation isolée avec un venv temporaire et `pip install schemathesis==4.33.4` : échec avant téléchargement, DNS indisponible (`Temporary failure in name resolution`, accès à `pypi.org` impossible). Aucun paquet Schemathesis n'a été installé ; aucun import, `st --version` ou test API n'a réussi. Le venv temporaire a été créé mais n'a pas reçu le paquet.
- Aucun appel réseau n'a été fait depuis Schemathesis vers une API applicative ; aucun endpoint fournisseur n'a été sollicité.
- Aucun code de production, dépendance, lockfile ou workflow Ascameleon modifié pendant ce cycle. Aucun secret lu ou utilisé, aucune API payante appelée, aucune dépense.

### 13.5 État du catalogue et priorités suivantes

- **27 entrées documentées** : 26 entrées précédentes + Schemathesis. L'installation non réalisée est explicitement séparée de la qualification du dépôt.
- Priorités :
  1. Cycle 2 : tester Schemathesis dans un environnement local jetable sur un schéma filtré d'AI ORCHESTRA, sans endpoint fournisseur ni accès externe ; ne l'ajouter aux workflows qu'après validation et revue des opérations couvertes.
  2. Cycle 2 : TorcScan PR #5 reste bloquée sur la vérification Samsung/ELM327 physique ; les outils d'automatisation ne remplacent pas ce test matériel.
  3. Cycle 1 : produire un nouveau diagnostic à partir des derniers commits et workflows, car aucun rapport Cycle 1 récent n'a été trouvé dans les issues consultées.
  4. Cycle 3 : continuer la recherche seulement sur les besoins non couverts ; ne pas ajouter Hypothesis séparément, puisqu'il est déjà une dépendance centrale de Schemathesis.



## 14. Cycle 8 — mirroring et contrôle manuel d'appareils Android pour QA (2026-11-17, 07:45 Africa/Algiers)

### 14.1 Diagnostics et état des projets relus avant la recherche

- Le catalogue canonique a été relu sur `main` avant la recherche ; aucune entrée `Genymobile/scrcpy` n'existait. Les outils Appium, Maestro et Patrol sont déjà présents : scrcpy est un complément de capture/contrôle manuel, pas un doublon de framework de tests.
- Recherche des diagnostics Cycle 1 : aucun rapport récent autonome ni issue Cycle 1 ouverte n'a été retrouvé dans les dépôts accessibles. Le dernier diagnostic Cycle 1 explicitement documenté dans ce catalogue reste celui du 2026-11-16 à 22:53 UTC ; il est ancien et n'est pas présenté comme un audit frais.
- Heads `main` relus via GitHub : ai-orchestra `2c78d4a8752ced799eac43f5bd01fcf5cb95861e`, Torcscandz `1c98135210eecb314ac67e526000d37ca3f99637`, BLUE ALERTS `e1b629197ee93435d1c8616927bb452ccfc2854d`, Gameforge-3D `83ff2cd33c6380a63843a39ee3bed882e9a3c11f`, Tripradar `7b36e7fbfc9afeafc9bfee32cec1f43640cea67b`, CallerID `2c421c2efa038f80011a21b4874bb2105608ae04`, NIA Studio AI `c957672e70d4df34a9ced1912c3e4839d4face6c`.
- Torcscandz PR #5 est toujours ouverte et en brouillon, head `421f03d334f8b98100986628fda51e025b1e2eb5`. Son descriptif confirme que la validation finale dépend d'un Samsung physique et d'un adaptateur OBD2 appairé. Le besoin de capture/inspection manuelle est réel, mais le matériel et un hôte PC ne sont pas disponibles dans cet environnement.
- BLUE ALERTS PR #52 et #53 restent ouvertes en brouillon ; les commentaires de #52 signalent que la branche est très en retard et divergente. Elles ne sont pas considérées comme des validations récentes ni comme une autorisation de fusion.
- AI ORCHESTRA ne présente aucune issue ou PR ouverte dans les recherches courantes. Les autres dépôts prioritaires n'ont pas révélé de nouveau blocage d'outillage plus urgent que la validation physique Android.

### 14.2 Nouvel outil qualifié — scrcpy

| Champ | Qualification |
|---|---|
| Nom / catégorie | **scrcpy** — miroir d'écran, contrôle et enregistrement Android depuis un hôte |
| Dépôt officiel | https://github.com/Genymobile/scrcpy (le README indique explicitement que ce dépôt est la seule source officielle) |
| Licence | Apache-2.0 ; fichier `LICENSE` intégral relu. Le code source est public. |
| Version | Release stable `v5.0.1`, publiée le 2026-10-08 à 06:44:27 UTC ; tag annoncé comme signé et vérifié par GitHub. |
| Commit de tête observé | `a60891aea193d92e7e5c3942700eca63f9d19a5f`, 2026-10-08 06:41:27 UTC, message « Update links to 5.0.1 ». Le commit actualise les liens et SHA-256 des binaires de la release. |
| Fonctions | Mirroring vidéo/audio, saisie clavier/souris, enregistrement, presse-papiers, écran virtuel, caméra selon version Android, USB ou TCP/IP. Aucun root et aucune application permanente à installer sur le téléphone ; un serveur temporaire correspondant à la version du client est poussé via ADB. |
| Compatibilité Android | Android API 21+ ; transfert audio API 30+ (Android 11+). Le protocole de connexion exige ADB et l'autorisation de débogage USB ou sans fil. |
| Dépendances hôte | Client Linux/Windows/macOS ; ADB/platform-tools, FFmpeg, SDL3 et libusb selon la méthode d'installation. Les archives officielles Windows incluent les dépendances nécessaires ; les instructions Linux documentent un binaire statique x86_64. |
| Coût / réseau | Logiciel gratuit, sans compte, publicité, API ni service cloud. Le mirroring USB ne requiert pas Internet. Le mode TCP/IP utilise le réseau local ; le téléchargement initial de la release vient de GitHub. |
| Matériel | Hôte PC requis ; CPU et décodage vidéo influencent la fluidité. Le projet annonce 30–120 fps selon l'appareil et conseille de réduire la résolution (`--max-size=1024`) pour améliorer les performances. GPU utile pour certains chemins de décodage, mais aucun GPU dédié n'est une condition générale annoncée. Le stockage d'enregistrement dépend du codec, du débit et de la durée. |
| Sécurité | N'autoriser ADB que sur un hôte de confiance ; révoquer les autorisations de débogage et couper le débogage sans fil après la session. Télécharger uniquement depuis le dépôt officiel, vérifier SHA-256 et signature. Ne pas laisser ADB TCP/IP exposé sur un réseau non fiable. |
| Limites Samsung | Compatibilité générale Android ne garantit pas toutes les variantes Samsung. Issue upstream #7169 documente un crash scrcpy-server 5.0.1 sur Galaxy A50 / Android 11 / Exynos 9610 ; vérifier le modèle et la version Android exacts avant validation. |
| Installation épinglée | Windows x64 : télécharger `scrcpy-win64-v5.0.1.zip` depuis la release officielle, vérifier SHA-256 `b12a2c4ee8be317422451fc7dcf8ee20a71b5ea7ef9ad73ddd825a25316227a5`, extraire, puis utiliser `adb devices` et `scrcpy --serial=<serial>`. Linux x86_64 : archive `scrcpy-linux-x86_64-v5.0.1.tar.gz`, SHA-256 `9f969d30cc574816077edecda65719c1c70b0aee1df1ba5fa00779ac07b8fd6e`. Ne pas exécuter de script d'installation distant non inspecté. |
| Cible / verdict | Torcscandz et CallerID : **MAYBE** — bon complément pour filmer et inspecter manuellement les écrans pendant un test réel ; ne remplace pas Appium/Maestro/Patrol et ne produit pas de assertions automatisées. Pas utilisable directement comme application autonome sur Samsung. |

Preuves consultées :
- README et fonctionnalités : https://github.com/Genymobile/scrcpy
- Release officielle et tag signé : https://github.com/Genymobile/scrcpy/releases/tag/v5.0.1
- Documentation connexion USB/TCP-IP : https://github.com/Genymobile/scrcpy/blob/master/doc/connection.md
- Instructions de compilation et dépendances hôte : https://github.com/Genymobile/scrcpy/blob/master/doc/build.md
- Binaire Windows x64 et checksum officiel : https://github.com/Genymobile/scrcpy/releases/download/v5.0.1/scrcpy-win64-v5.0.1.zip
- Issue Samsung Galaxy A50 / Android 11 : https://github.com/Genymobile/scrcpy/issues/7169

### 14.3 Installation et tests réellement effectués

- Recherche GitHub de dépôts de mirroring Android et comparaison anti-doublon : effectuées.
- Vérification du dépôt officiel, README, licence Apache-2.0, documentation de connexion, instructions de compilation, release `v5.0.1`, tag signé, assets et checksums : effectuée.
- Contrôle d'activité : commit `a60891a...` daté du 2026-10-08 ; release publiée le même jour. Le dépôt n'est pas archivé.
- Contrôle d'issues Samsung : l'issue #7169 signale un crash sur un modèle précis (Galaxy A50, Android 11) ; cette limite est consignée et ne doit pas être généralisée à tous les Samsung.
- Aucun client scrcpy installé : un hôte PC Linux/Windows/macOS et ADB sont nécessaires ; aucun poste hôte ni appareil Samsung/OBD2 autorisé n'est présent dans cet environnement.
- Aucun test de connexion, de mirroring ou d'enregistrement n'a été exécuté. Aucun test physique Samsung n'est revendiqué.
- Aucun code, dépendance ou workflow de production Ascameleon modifié. Aucun coût, secret, appel API payant ou service cloud utilisé.

### 14.4 État du catalogue et priorités

- **28 entrées documentées** : 27 précédentes + scrcpy. L'entrée est classée MAYBE et son absence d'installation est explicite.
- Priorités :
  1. Torcscandz : utiliser scrcpy uniquement lorsqu'un hôte PC et le Samsung/ELM327 autorisés seront disponibles ; compléter par le test applicatif réel, sans confondre capture et test automatisé.
  2. CallerID : même usage éventuel pour inspection visuelle d'un appareil Android réel ; les tests de backend et de sécurité restent séparés.
  3. Ne pas ajouter un autre outil de mirroring tant qu'un besoin distinct n'est pas démontré ; Appium, Maestro et Patrol couvrent déjà l'automatisation UI.
  4. Cycle 1 : produire un nouveau diagnostic à partir des derniers commits et runs, car aucun rapport Cycle 1 frais n'a été retrouvé pendant ce passage.


## 15. Cycle 9 — réévaluation des pipelines média et état actuel des dépôts (2026-11-17, 08:46 Africa/Algiers)

### 15.1 Diagnostics Cycle 1 et dépôts relus avant recherche

- Lecture du catalogue canonique sur main avant recherche : commit du fichier 4473671efd9cf4ba3c3694745e34b5d7a7ac9b7a, 578 lignes. Les entrées FFmpeg, MoviePy, OpenTimelineIO, OpenTelemetry, glTF Transform, glTF Validator, Patrol, Appium, Maestro, scrcpy, etc. ont été comparées avant sélection ; aucun doublon n'est ajouté.
- Recherches GitHub d'issues org:Ascameleon is:issue is:open et org:Ascameleon "Cycle 1" : aucun résultat exploitable. Le dernier diagnostic Cycle 1 explicitement documenté dans ce catalogue reste celui du 2026-11-16 à 22:53 UTC ; il est ancien et n'est pas présenté comme un audit frais.
- Dépôts Ascameleon relus directement sur leur branche par défaut main : AI ORCHESTRA 897bc690a8c6a963c8eaf2e537b4d292fdf00aed, Torcscandz 1c98135210eecb314ac67e526000d37ca3f99637, BLUE ALERTS e1b629197ee93435d1c8616927bb452ccfc2854d, Gameforge-3D 83ff2cd33c6380a63843a39ee3bed882e9a3c11f, Tripradar 7b36e7fbfc9afeafc9bfee32cec1f43640cea67b, Callerid 2c421c2efa038f80011a21b4874bb2105608ae04, Nia-studio-Ai c957672e70d4df34a9ced1912c3e4839d4face6c, playwright-samsung 842479e849ac6115500939702358b3d66a764e72. Le nom GitHub réel du projet de voyage est Tripradar (README produit : TripBoost), pas TripBoost.
- PR ouvertes observées : Torcscandz #5 toujours en brouillon ; BLUE ALERTS #52 et #53 toujours en brouillon et mergeable=false, #51 toujours en brouillon. Ne pas assimiler ces PR à des changements intégrés à main.
- Besoins actuels : QA Android TorcScan encore dépendante d'un Samsung et d'un adaptateur ELM327 physiques ; assets GLB de Gameforge/BLUE ALERTS déjà couverts par glTF Transform, glTF Validator et meshoptimizer ; AI ORCHESTRA dispose déjà d'une entrée OpenTelemetry ; NIA Studio AI possède déjà FFmpeg/MoviePy/Whisper/Piper dans le catalogue, mais aucune fonction réelle de capture/live-streaming n'est spécifiée dans son README.

### 15.2 Réévaluation du candidat GStreamer — toujours différé

| Champ | Vérification |
|---|---|
| Dépôt officiel | https://github.com/GStreamer/gstreamer — dépôt public, non archivé. Le README indique que le suivi des bugs et merge requests est sur GitLab : GitHub ne constitue donc pas le tracker amont de référence. |
| Licence exacte | subprojects/gstreamer/COPYING et subprojects/gst-plugins-base/COPYING contiennent LGPL version 2.1. La documentation officielle précise que l'installation minimale est LGPL, mais que des plugins optionnels peuvent être GPL ou brevetés. Ne pas annoncer une licence unique pour tous les plugins ni redistribuer un bundle sans inventaire. |
| Version et activité | Release stable 1.28.9 publiée le 2026-11-06 ; version 1.28.9 confirmée dans subprojects/gst-plugins-base/meson.build. HEAD du dépôt observé : b45c483edc7c7e4671d24a5ac4228835c7b029f3, commit du 2026-11-17 à 04:42:03 UTC. |
| Fonctions | Framework de pipelines audio/vidéo : lecture, capture, conversion, filtres, streaming, WebRTC, synchronisation, édition et analytics. CLI gst-launch-1.0 et inspection gst-inspect-1.0. C'est un moteur local et non une API de génération hébergée. |
| Installation source | git clone --depth 1 --branch 1.28.9 https://github.com/GStreamer/gstreamer.git, puis meson setup builddir et meson compile -C builddir. Prérequis documentés : Python 3.8+, Meson >=1.4, Ninja, compilateur C et dépendances GLib ; la compilation complète est lourde. Préférer les SDK binaires officiels pour un simple usage. |
| Android / Samsung | La page de téléchargement consultée le 2026-11-17 publiait encore l'archive Android Universal 1.28.8, pas 1.28.9. Les binaires 1.28.x ciblent Android API 24+ et NDK r25c, avec armv7/arm64/x86/x86_64. L'intégration requiert SDK/NDK, JNI et choix précis des plugins ; ce n'est pas un paquet Flutter prêt à ajouter. Aucun test sur Samsung n'a été fait. |
| Coût et dépendances cachées | Aucun abonnement, crédit ou appel API requis pour l'usage local. Attention aux codecs brevetés selon pays et distribution, aux plugins GPL et aux dépendances optionnelles ; contrôler les licences effectives des plugins avec gst-inspect-1.0. |
| Matériel | CPU seul possible ; accélération matérielle facultative selon plateforme et codecs. Les résolutions élevées et pipelines multiples peuvent consommer beaucoup de RAM/CPU/disque. Aucun GPU dédié n'est une exigence générale. |
| Projet cible / verdict | NIA Studio AI : **MAYBE / DIFFÉRÉ**. Ne pas intégrer tant qu'une fonction réelle de capture, streaming, WebRTC ou pipeline temps réel n'est pas spécifiée. FFmpeg reste le choix existant pour les traitements batch et conversions simples. |

Preuves amont consultées :
- Dépôt et guide de build : https://github.com/GStreamer/gstreamer
- Documentation des licences et plugins : https://gstreamer.freedesktop.org/documentation/frequently-asked-questions/licensing.html
- Releases officielles : https://gstreamer.freedesktop.org/releases/
- Téléchargements et SDK Android : https://gstreamer.freedesktop.org/download/
- Prérequis Android / NDK : https://gstreamer.freedesktop.org/documentation/installing/for-android-development.html

### 15.3 Installation et tests réellement effectués

- Contrôle de l'environnement temporaire : Linux x86_64 ; ninja et cc présents ; gst-launch-1.0, gst-inspect-1.0, Meson, ADB, Flutter et Dart absents.
- Aucun clone, binaire ou SDK GStreamer installé. Aucun pipeline audio/vidéo ni test d'import exécuté. Aucun test Android/Samsung revendiqué.
- Aucun nouvel outil admis dans le catalogue pendant ce passage ; GStreamer reste une entrée différée, et sa version/licence/statut ont été actualisés ci-dessus.
- Aucun code, dépendance, sous-module ou workflow de production Ascameleon n'a été modifié pour GStreamer. Aucun coût, secret, service cloud ou API payante utilisé.

### 15.4 Changement séparé sur la branche de travail Torcscandz

- Sur la PR existante #5 uniquement, un défaut de cohérence du finaliseur a été corrigé : le script écrivait le manifeste avant de valider complètement torqscan-patch-report.json. Un rapport mal formé ou sans hash valide pouvait donc laisser un manifeste modifié malgré l'échec du finaliseur.
- Commit aa06c10afc3d42f4354a92da0acfb4c91e513a25 : validation du rapport et du SHA-256 avant écriture du manifeste.
- Commit a227e6940241424b2eb2fe4cbfe2dfa9df1d985b : tests de non-régression pour JSON invalide, hash manquant et hash mal formé ; ils vérifient que le manifeste et le rapport restent inchangés en cas de rejet.
- Les deux workflows sur ce head sont terminés avec succès : Android APK Build run 44042628651 (#196) et TorqScan PR validation run 44042628636 (#61). L'APK de test est construite et vérifiée par la CI ; cela ne prouve pas la connexion physique à un ELM327.
- La branche PR #5 est toujours en brouillon, 47 commits en avance et 2 en retard sur main au dernier compare ; aucun merge n'a été effectué. La validation Samsung + ELM327/ECU reste obligatoire.

### 15.5 Résultat et priorités

- **0 nouvel outil admis** ; 1 candidat déjà différé (GStreamer) requalifié avec release, HEAD, licence, statut Android et preuves actualisés.
- **0 installation GStreamer** ; **0 smoke test GStreamer** ; aucun coût.
- Priorités : (1) actualiser le diagnostic Cycle 1 sur les derniers commits/runs ; (2) conserver TorcScan #5 en brouillon jusqu'au test matériel et synchroniser sa branche avec main avant toute fusion ; (3) ne réévaluer GStreamer que si NIA Studio AI ajoute une exigence réelle de capture/streaming temps réel.


## 16. Cycle 10 — contrôle sécurité Go et état actuel des dépôts (2026-11-17, 09:10 Africa/Algiers)

### 16.1 Diagnostics Cycle 1 et dépôts relus avant recherche

- Lecture du catalogue canonique `main` avant toute nouvelle recherche : blob `9d7fbea9cb256850c05983c0226b81d56efc1b5b`, 631 lignes. Vérification anti-doublon : `govulncheck`, `detekt` et `Trivy` ne figuraient pas parmi les entrées qualifiées.
- Recherche GitHub `org:Ascameleon is:open is:issue` et `org:Ascameleon cycle 1` : aucun rapport Cycle 1 ni issue ouverte exploitable retrouvé. Le dernier diagnostic Cycle 1 explicitement documenté reste celui du 2026-11-16 à 22:53 UTC ; il est ancien et n'est pas présenté comme un audit frais.
- Heads `main` vérifiés par recherche des derniers commits :
  - AI ORCHESTRA : `c988760145979138e555cc2506b17727e697de24` (2026-11-17 08:05 UTC).
  - Torcscandz : `1c98135210eecb314ac67e526000d37ca3f99637` (2026-11-16 19:18 UTC).
  - BLUE ALERTS : `e1b629197ee93435d1c8616927bb452ccfc2854d` (2026-11-17 04:57 UTC).
  - Gameforge-3D : `83ff2cd33c6380a63843a39ee3bed882e9a3c11f` (2026-11-16 19:10 UTC).
  - Tripradar (produit TripBoost) : `7b36e7fbfc9afeafc9bfee32cec1f43640cea67b` (2026-11-17 01:58 UTC).
  - CallerID : `2c421c2efa038f80011a21b4874bb2105608ae04` (2026-11-16 20:27 UTC).
  - NIA Studio AI : `c957672e70d4df34a9ced1912c3e4839d4face6c` (2026-11-17 06:08 UTC).
- PR ouvertes importantes revérifiées :
  - Tripradar #22, non-draft, head `7f89a4a2334ba62ca7fc2c35fc68e4baf5fefc85`, workflow `44045155589` terminé avec succès. La PR annule le fan-out Amadeus quand le client HTTP se déconnecte, avec fetch stubs uniquement ; aucune connexion fournisseur réelle ni clé utilisée.
  - Torcscandz #5, draft, head `a227e6940241424b2eb2fe4cbfe2dfa9df1d985b`. Les deux workflows `44042628636` et `44042628651` sont réussis, mais la branche est divergente : 47 commits en avance et 2 en retard sur `main`. Le test Samsung + adaptateur ELM327/ECU reste nécessaire ; aucun merge.
  - BLUE ALERTS #52 et #53 restent en draft et `mergeable=false`. #52 est divergente de 28 commits en avance et 40 en retard sur `main`. #51 reste en draft. PR #65 est déjà fusionnée : Playwright 1.65.1 est désormais épinglé sur `main`.
- Le besoin outillage le plus concret non couvert est un contrôle de vulnérabilités atteignables dans le backend Go de CallerID : son workflow reconstruit `callerid/`, utilise Go `1.22.x`, puis lance `go test ./...` et `go vet ./...`. Les outils de test Android et d'observabilité sont déjà documentés ; aucun nouvel outil de mirroring ou GLB n'est ajouté.

### 16.2 Nouvel outil qualifié — govulncheck (MAYBE)

| Champ | Qualification |
|---|---|
| Nom / catégorie | **govulncheck** — analyse de vulnérabilités Go avec analyse statique des chemins d'appel |
| Dépôt GitHub | https://github.com/golang/vuln — miroir GitHub du projet Go ; source canonique : https://go.googlesource.com/vuln ; module officiel : `golang.org/x/vuln` |
| Licence | BSD-3-Clause pour le code source (`LICENSE` vérifiée). Les entrées de la base de vulnérabilités sont sous CC-BY 4.0 ; conserver l'attribution si elles sont redistribuées. |
| Version épinglable | Dernière release stable publiée affichée : `v1.1.4`, tag commit `d1f380186385b4f64e00313f31743df8e4b89a77`. Le `go.mod` du tag déclare `go 1.22.0`. |
| État upstream | HEAD du miroir observé : `e672cbe8fbc8c76e28fcb6db0efd9ce354e0dac5` (2026-10-11). Le `go.mod` actuel de la branche principale déclare `go 1.26.0` : ne pas installer `@latest` dans le workflow CallerID Go 1.22.x. La release stable v1.1.4 est l'option compatible à tester, mais elle est ancienne par rapport au HEAD actuel. |
| Fonctions | Analyse des modules, packages et binaires ; relie les vulnérabilités connues aux fonctions effectivement atteignables, ce qui réduit les faux positifs par rapport à une simple liste de versions. Rapports texte/JSON/SARIF selon la version. |
| Installation épinglée | `go install golang.org/x/vuln/cmd/govulncheck@v1.1.4`, puis depuis le module extrait `cd callerid && govulncheck ./...`. Ne pas utiliser `@latest` tant que la toolchain du projet reste Go 1.22.x. |
| Dépendances / coûts | Go 1.22+ pour la version taggée ; pas de GPU, cloud, compte, abonnement ou API payante. Le scanner interroge normalement `https://vuln.go.dev` pour actualiser/consulter la base ; la documentation précise que les requêtes transmettent des chemins de modules concernés, pas le code source. Une exécution hors ligne nécessite une base locale préalablement fournie et maintenue à jour. |
| Matériel / Android | Charge CPU et mémoire modérée, dépend du graphe de dépendances et de la taille du module. À exécuter sur le runner CI ou un hôte de développement ; ce n'est pas un composant embarqué dans l'APK et ne remplace pas les tests Samsung. |
| Projet cible / verdict | CallerID backend Go : **MAYBE** — compatibilité de la release v1.1.4 avec Go 1.22 vérifiée dans son manifeste, mais ancienneté de la release et divergence entre tag stable et HEAD Go 1.26 imposent un essai isolé avant ajout au workflow. |

Preuves amont :
- Dépôt miroir et procédure officielle : https://github.com/golang/vuln
- Release stable v1.1.4 : https://github.com/golang/vuln/releases
- Commit du tag : https://github.com/golang/vuln/commit/d1f380186385b4f64e00313f31743df8e4b89a77
- `go.mod` v1.1.4 : https://github.com/golang/vuln/blob/v1.1.4/go.mod
- Confidentialité des requêtes à la base : https://vuln.go.dev/privacy

### 16.3 Candidats examinés mais non admis

| Candidat | Vérification | Décision |
|---|---|---|
| Detekt | Dépôt https://github.com/detekt/detekt, Apache-2.0 vérifiée. La release stable 1.23.8 documente Gradle 6.8.3+ mais sa matrice recommandée cible Gradle 8.12.1, Kotlin 2.0.21 et AGP 8.8.1 ; CallerID est en Gradle 8.9, Kotlin 1.9.24 et AGP 8.7.3. La branche 2.0 consultée est pré-release et cible une toolchain nettement plus récente. | **MAYBE / différé** : ne pas ajouter au build Android avant un essai sur la combinaison exacte ou une mise à niveau volontaire des versions Kotlin/AGP. |
| Trivy | Dépôt actif et non archivé https://github.com/aquasecurity/trivy ; licence Apache-2.0 vérifiée ; HEAD observé `00b73947fd14332e6648b0b38edbb1ca5380a222` (2026-11-17 07:27 UTC). Le GitHub Security Advisory critique GHSA-69fq-xp46-6x23 documente la compromission de Trivy v0.69.4, des tags `trivy-action` et `setup-trivy`, puis des images Docker v0.69.5/v0.69.6 en mars 2026. | **FAIL pour intégration dans ce cycle** : aucun besoin imposant Trivy et historique de compromission de chaîne d'approvisionnement. Ne pas utiliser d'action tierce par tag mutable ni de conteneur avec socket Docker monté. Réévaluer uniquement après vérification d'une release immuable, de sa signature et de son checksum. |

Preuve de sécurité Trivy : https://github.com/advisories/GHSA-69fq-xp46-6x23

### 16.4 Installation et tests réellement effectués

- Environnement contrôlé : Linux x86_64, Go `1.23.2`, Python `3.13.5`, Node `22.16.0`. Aucun binaire `govulncheck` préinstallé.
- Tentative réelle d'installation isolée dans un GOPATH/GOBIN temporaire : `go install golang.org/x/vuln/cmd/govulncheck@v1.1.4`.
- Échec avant téléchargement : résolution DNS de `proxy.golang.org` refusée (`lookup proxy.golang.org ... connection refused`). Aucun module téléchargé, aucun binaire installé, aucun `govulncheck -version`, scan ou test d'import réussi.
- Aucun paquet ajouté au dépôt CallerID ; aucun workflow, lockfile ou source de production modifié.
- Detekt et Trivy non installés ; aucun test d'exécution revendiqué.
- Aucun secret lu, aucun fournisseur appelé, aucun service cloud ou API payante utilisé ; coût : 0 €.

### 16.5 État du catalogue et priorités suivantes

- **29 outils qualifiés ou conditionnels documentés** : 28 précédents + govulncheck (MAYBE). Detekt est différé et Trivy n'est pas admis ; ils ne sont pas comptés comme outils qualifiés.
- Priorités :
  1. Refaire le test isolé govulncheck v1.1.4 quand le réseau DNS/Go proxy est disponible ; n'ajouter au workflow CallerID qu'après un résultat sur le module extrait exact et un examen des findings.
  2. Torcscandz #5 : synchroniser la branche avec `main` dans une opération contrôlée, puis revalider ; garder la PR en draft jusqu'au test Samsung/ELM327 physique.
  3. Tripradar #22 : conserver les tests injectés et vérifier le workflow exact-head avant toute fusion ; aucune clé Amadeus ne doit être requise pour ces tests.
  4. BLUE ALERTS #52/#53 : ne pas fusionner tant que les branches restent divergentes et que les critères visuels documentés ne sont pas satisfaits.
  5. Cycle 1 : générer un diagnostic récent depuis les derniers commits et workflows ; aucun rapport Cycle 1 frais n'a été retrouvé dans les issues consultées pendant ce passage.


## 17. Cycle 11 — qualification des tests d'intégration Redis et de l'analyse de sécurité Go (2026-11-17, 09:41 Africa/Algiers)

### 17.1 État et besoins vérifiés avant recherche

- Catalogue canonique relu sur `main` avant recherche : blob `d4a7193f64f2a1d69c67444a4f1050e058f41781`. Contrôle anti-doublon : ni `testcontainers/testcontainers-python` ni `securego/gosec` ne figuraient dans les entrées antérieures.
- Recherche des issues ouvertes `org:Ascameleon is:open` et `repo:Ascameleon/ai-orchestra is:open` : aucun rapport Cycle 1 récent exploitable retrouvé. Le dernier diagnostic Cycle 1 explicitement documenté dans le catalogue reste celui du 2026-11-16 à 22:53 UTC ; il est ancien et n'est pas présenté comme un audit actuel.
- Heads `main` relus par recherche de commits récents :
  - AI ORCHESTRA : `062b0f0c5475517cd89632a8d8eb437424ce6a28` (2026-11-17 08:23:18 UTC).
  - Torcscandz : `1c98135210eecb314ac67e526000d37ca3f99637` (2026-11-16 19:18:35 UTC).
  - BLUE ALERTS : `e1b629197ee93435d1c8616927bb452ccfc2854d` (2026-11-17 04:57:38 UTC).
  - Gameforge-3D : `83ff2cd33c6380a63843a39ee3bed882e9a3c11f` (2026-11-16 19:10:37 UTC).
  - Tripradar / produit TripBoost : `7b36e7fbfc9afeafc9bfee32cec1f43640cea67b` (2026-11-17 01:58:14 UTC).
  - CallerID : `2c421c2efa038f80011a21b4874bb2105608ae04` (2026-11-16 20:27:25 UTC).
  - NIA Studio AI : `c957672e70d4df34a9ced1912c3e4839d4face6c` (2026-11-17 06:08:29 UTC).
- AI ORCHESTRA : `src/orchestra/guardrails.py` implémente `RedisDailyCostGuard` avec un script Lua `EVAL` atomique (GET/INCR/TTL/EXPIRE). `tests/test_guardrails.py` vérifie aujourd'hui ce chemin avec un `FakeRedis` maison qui simule le script ; il ne lance pas un serveur Redis réel. C'est un besoin concret de test d'intégration, mais le backend Redis reste optionnel et n'est pas nécessaire au mode SQLite local.
- CallerID : le workflow de backend utilise Go `1.22.x` et exécute déjà `go test ./...` et `go vet ./...`. `govulncheck` est déjà au catalogue en MAYBE ; son installation précédente a échoué avant téléchargement à cause du DNS Go Proxy.
- Torcscandz PR #5 est toujours ouverte et son descriptif exige un essai Samsung + adaptateur OBD2 physique ; Tripradar PR #22 est ouverte et sa validation utilise des fetch stubs. Aucun outil de mirroring ou de génération GLB supplémentaire n'est ajouté : scrcpy, Appium, Maestro, Patrol, glTF Transform, glTF Validator et meshoptimizer couvrent déjà ces domaines.

### 17.2 Candidat — Testcontainers Python (MAYBE / différé, non installé)

| Champ | Qualification |
|---|---|
| Nom / catégorie | **Testcontainers Python** — tests d'intégration avec services jetables en conteneurs |
| Dépôt GitHub | https://github.com/testcontainers/testcontainers-python |
| Licence exacte | Apache-2.0 ; `LICENSE.txt` vérifiée dans le tag `testcontainers-v4.15.0` (blob observé `141e73f8f5fa18ec834d6e827fc7549acc0190e2`). |
| Version / snapshot | Release `4.15.0`, publiée le 2026-07-24 ; commit exact du tag `04267b35bdcf79ee9d2efbfdd61b2512dab0bdac`. Un commit récent observé dans l'historique consulté : `6146aa1170f415fcc825ed9bddc4eacbeb937a12` (2026-10-07). Le dépôt n'est pas archivé. |
| Compatibilité Python | `pyproject.toml` du tag : version 4.15.0, `requires-python >=3.10` ; compatible avec Python 3.11/3.12 d'AI ORCHESTRA. |
| Fonctions | Lance des services temporaires pour tests fonctionnels/intégration ; modules PostgreSQL et Redis, ou conteneur générique. Pour AI ORCHESTRA, permettrait de vérifier le vrai script Lua de `RedisDailyCostGuard`, la réservation concurrente et la readiness contre un serveur Redis réel au lieu d'un faux client. |
| Dépendances | Base : Docker SDK Python, urllib3, wrapt, typing-extensions, python-dotenv. L'extra `redis` du tag exige `redis>=7`, alors que le projet AI ORCHESTRA déclare `redis>=5,<7` : **ne pas installer l'extra `[redis]` dans l'environnement du projet**. Si réévalué, isoler le paquet et utiliser le client Redis déjà compatible avec le projet, après vérification de l'API du module choisi. |
| Coûts / réseau | Pas d'abonnement ni d'API payante ; nécessite un daemon Docker et le téléchargement d'images OCI. Les téléchargements consomment réseau, stockage et temps CI ; aucun coût cloud intrinsèque si exécuté sur un runner local/CI déjà disponible. |
| Sécurité / maintenance | Accès au socket Docker équivaut à un contrôle élevé du daemon ; exécuter seulement sur un runner isolé, sans monter le socket dans l'application, avec images officielles épinglées par digest. Plusieurs issues ouvertes sur la release 4.15.0 signalent des risques de nettoyage et de readiness : #1140 (Ryuk tué avant son délai de réaper, conteneurs de session laissés actifs), #1143 (prédicat HTTP ignoré pour certains statuts acceptés), #1138 et #1137 (comportement des stratégies d'attente). La release 4.15.0 date de juillet 2026 et ces défauts imposent de différer l'adoption. |
| Matériel / Android | CPU/RAM/disque selon les images lancées ; Docker Engine/Desktop et accès réseau aux registres requis. Pas de GPU. Outil hôte/CI, **pas Android/Samsung**. L'environnement de ce cycle n'a ni binaire Docker ni socket `/var/run/docker.sock`. |
| Installation préparée | Dans un environnement de test séparé uniquement : `python -m pip install "testcontainers==4.15.0"`. Ne pas ajouter au `pyproject.toml` d'AI ORCHESTRA avant correction/validation du nettoyage Ryuk et un smoke test avec Redis épinglé par digest. |
| Projet cible / verdict | AI ORCHESTRA : **MAYBE / DIFFÉRÉ**. Utilité réelle pour valider le chemin Redis, mais risques connus de fuite de conteneurs, contrainte Docker élevée et conflit de version de l'extra Redis. Aucun déploiement ou ajout de dépendance autorisé à ce stade. |

Preuves amont :
- README et exemple PostgreSQL : https://github.com/testcontainers/testcontainers-python
- Licence et manifeste de la release : https://github.com/testcontainers/testcontainers-python/tree/testcontainers-v4.15.0
- Release 4.15.0 : https://github.com/testcontainers/testcontainers-python/releases/tag/testcontainers-v4.15.0
- Issue nettoyage Ryuk #1140 : https://github.com/testcontainers/testcontainers-python/issues/1140
- Issue prédicat HTTP #1143 : https://github.com/testcontainers/testcontainers-python/issues/1143
- Package metadata / Python / Apache-2.0 : https://pypi.org/project/testcontainers/4.15.0/

### 17.3 Candidat — gosec (MAYBE / incompatible avec la toolchain actuelle)

| Champ | Qualification |
|---|---|
| Nom / catégorie | **gosec** — analyse statique de sécurité Go (AST, SSA et flux de données) |
| Dépôt GitHub | https://github.com/securego/gosec |
| Licence exacte | Apache-2.0, déclarée dans le README du dépôt et dans les en-têtes de code vérifiés. |
| Version / snapshot | Release `v2.30.0`, tag commit `5eb1d104ef85ff2c905c877eb600e8c1dee33a22`, publiée le 2026-10-23 selon la version publiée référencée par pkg.go.dev. |
| Fonctions | Règles de sécurité sur le code Go : secrets codés en dur, injections, commandes, traversée de chemins, SSRF, TLS/crypto et autres erreurs de sécurité. Analyse locale ; sortie texte, JSON ou SARIF. Complémentaire de `go vet` et de `govulncheck`, qui analyse plutôt les vulnérabilités connues des dépendances et leur atteignabilité. |
| Compatibilité | Le README de la release indique Go >=1.25 ; le `go.mod` du tag déclare `go 1.26.0`. CallerID est encore sur Go 1.22.x ; l'environnement de ce cycle est Go 1.23.2. L'installation `go install` de cette version n'est donc pas compatible avec la toolchain disponible ni avec la matrice CI actuelle. |
| Dépendances / coûts | Le `go.mod` du tag contient notamment des SDK Anthropic, OpenAI et Google GenAI en dépendances directes, en plus de nombreuses dépendances d'analyse. Le scan statique standard ne nécessite pas de clé ni d'appel fournisseur ; ne jamais activer de fonction de correction assistée distante sans audit distinct. Compilation et analyse locales, sans GPU ni abonnement. |
| Matériel / Android | Binaire destiné à l'hôte Linux/Windows/macOS ou runner CI ; CPU/RAM selon taille du module. Ce n'est pas un outil embarqué dans l'APK et ne valide pas un appareil Samsung. |
| Installation préparée | Commande documentée mais non exécutée : `go install github.com/securego/gosec/v2/cmd/gosec@v2.30.0`. Ne pas remplacer la toolchain Go de CallerID pour ce seul outil. Une éventuelle utilisation d'un binaire précompilé devra être épinglée par checksum/signature et testée séparément avec le module Go 1.22 réel. |
| Projet cible / verdict | CallerID backend Go : **MAYBE / DIFFÉRÉ**. Les règles sont pertinentes pour les endpoints OTP, les entrées HTTP et le traitement des données, mais la version actuelle exige Go 1.25/1.26 ; aucune intégration au workflow Go 1.22 n'est autorisée. |

Preuves amont :
- Dépôt et règles : https://github.com/securego/gosec
- Release v2.30.0 : https://github.com/securego/gosec/releases/tag/v2.30.0
- Commit du tag : https://github.com/securego/gosec/commit/5eb1d104ef85ff2c905c877eb600e8c1dee33a22
- README (Go >=1.25) : https://github.com/securego/gosec/blob/v2.30.0/README.md
- go.mod (Go 1.26.0) : https://github.com/securego/gosec/blob/v2.30.0/go.mod

### 17.4 Installation et tests réellement effectués

- Environnement contrôlé : Linux x86_64, Python 3.13.5, pip 25.1.1, Go 1.23.2. Aucun binaire Docker, aucun socket Docker `/var/run/docker.sock`, aucun module Python `testcontainers`, aucun binaire `gosec`.
- Testcontainers : **aucune installation, aucun import et aucun smoke test**. Motif : absence de Docker et issues amont ouvertes sur le nettoyage Ryuk/readiness de la version 4.15.0. L'absence du daemon est un blocage matériel/runtime confirmé.
- gosec : **aucune installation ni scan**. Motif : la version v2.30.0 exige Go >=1.25 et son `go.mod` déclare 1.26.0 ; l'environnement est Go 1.23.2 et CallerID CI Go 1.22.x.
- Aucun outil ajouté à une application, aucun fichier de production, workflow, lockfile ou dépendance Ascameleon modifié. Aucun test de projet revendiqué pour ces deux candidats.
- Aucun secret lu, aucun fournisseur appelé, aucun service cloud ni API payante utilisé ; coût : 0 €.

### 17.5 Décisions et priorités suivantes

1. AI ORCHESTRA : garder le test Redis simulé existant ; préférer, si un test réel devient nécessaire, un service Redis épinglé dans GitHub Actions ou Docker Compose sur un runner isolé, plutôt que d'adopter Testcontainers 4.15.0 tant que l'issue de nettoyage Ryuk #1140 n'est pas résolue et re-testée.
2. CallerID : conserver `go test`, `go vet` et le candidat `govulncheck` déjà documenté ; réévaluer gosec lorsqu'une version officiellement compatible avec Go 1.22.x est disponible, ou après une mise à niveau Go décidée et testée séparément.
3. Torcscandz #5 : ne pas confondre les validations APK CI avec la connexion Samsung/ELM327 physique ; conserver le brouillon jusqu'au test matériel.
4. Cycle 1 : produire un diagnostic récent ; aucun rapport récent n'a été trouvé dans les issues ouvertes consultées.

**Résultat de ce cycle :** 0 nouvel outil admis PASS ; 2 nouveaux candidats examinés et documentés en MAYBE/différé ; 0 installation ; 0 smoke test d'outil réussi ; aucun changement de production ; coût 0 €.


## 18. Cycle 12 — audit de sécurité et de conformité des workflows GitHub Actions (2026-11-17, 10:41 Africa/Algiers)

### 18.1 Diagnostics Cycle 1 et état des dépôts relus avant recherche

- Catalogue canonique relu sur `main` avant la recherche : blob `1319aa19614db7b1e9b0ecea83934ee25e09dfc7`, 785 lignes. Contrôle anti-doublon : `jactionlint`, `zizmor` et le fork `kjanat/actionlint` ne figuraient pas comme entrées distinctes. Le catalogue contient déjà les outils de QA applicative et de détection de secrets ; le besoin non couvert est une analyse cohérente des workflows GitHub Actions (syntaxe, expressions, sécurité et règles de politique).
- Recherche GitHub des issues ouvertes `org:Ascameleon is:open` et des issues contenant `"Cycle 1"` : aucune issue/rapport Cycle 1 récent exploitable retrouvé. La recherche de fichiers ne révèle pas de nouveau rapport Cycle 1 ; le dernier diagnostic explicitement daté reste celui du 2026-11-16 à 22:53 UTC, déjà signalé comme ancien. Ne pas le présenter comme un audit frais.
- Heads `main` les plus récents vérifiés par historique GitHub au 2026-11-17 10:41 (heure locale) :
  - AI ORCHESTRA : `8a4d9242b096f4e53dd246ed85b58ebe085f6903` (2026-11-17 08:46:38 UTC).
  - Torcscandz : `1c98135210eecb314ac67e526000d37ca3f99637` (2026-11-16 19:18:35 UTC).
  - BLUE ALERTS : `e1b629197ee93435d1c8616927bb452ccfc2854d` (2026-11-17 04:57:38 UTC).
  - Gameforge-3D : `83ff2cd33c6380a63843a39ee3bed882e9a3c11f` (2026-11-16 19:10:37 UTC).
  - Tripradar / produit TripBoost : `c63b52ac27a56ad97393f61d36fb8968ccce0c53` (2026-11-17 08:58:26 UTC ; commit de fusion de la PR #22).
  - CallerID : `2c421c2efa038f80011a21b4874bb2105608ae04` (2026-11-16 20:27:25 UTC).
  - NIA Studio AI : `c957672e70d4df34a9ced1912c3e4839d4face6c` (2026-11-17 06:08:29 UTC ; fusion de la PR #13).
  - ruflo : `056a11ece4ca3bd234aafd6221156d24b80a9544` (2026-10-21 21:56:09 UTC).
  - playwright-samsung : `842479e849ac6115500939702358b3d66a764e72` (2026-11-16 22:08:02 UTC).
- PR ouvertes observées :
  - Torcscandz #5 : encore ouverte et annoncée comme brouillon dans sa description ; l'essai Samsung + adaptateur OBD2 physique reste un critère de fusion. Les validations CI ne remplacent pas cet essai.
  - BLUE ALERTS #51 : le smoke test MCP Qwen/Blender sur le poste cible reste explicitement en attente.
  - BLUE ALERTS #52 et #53 : les descriptions exigent encore l'inspection de captures visuelles fraîches et la validation du head exact ; ne pas fusionner sur la seule base de captures historiques.
  - Tripradar #22 est fusionnée dans `main` (commit ci-dessus) ; NIA Studio AI #13 est fusionnée dans `main`.
- Les statuts combinés de commit retournés par l'API GitHub pour les heads `main` contrôlés étaient vides dans cette consultation ; aucun nouveau statut CI vert/rouge n'est revendiqué sur cette seule base.
- Besoin retenu : audit hors ligne des workflows des dépôts Ascameleon, sans modifier les fichiers, sans télécharger d'action, sans activer de contrôle en ligne et sans exécuter les workflows.

### 18.2 Nouvel outil — jactionlint (MAYBE, candidat d'audit hors ligne)

| Champ | Qualification |
|---|---|
| Nom / catégorie | **jactionlint** — linter GitHub Actions : syntaxe, expressions, sécurité et politiques CI/CD |
| Dépôt GitHub exact | https://github.com/jdx/jactionlint |
| Source et licence | Code source public ; `LICENSE.txt` du tag v2.6.0 vérifié : MIT. `NOTICE.md` conserve l'attribution à rhysd/actionlint et documente les sources de règles (dont zizmor, CodeQL, poutine et ghalint). Conserver ces deux fichiers avec toute redistribution. |
| Version stable épinglable | Release `v2.6.0`, publiée le 2026-11-12 ; commit de release `72c00452809bcca05b8bc12acdcf15dd7a9c1c5e`. HEAD amont observé `2964d0e78d7f0c50d9d213a771ff4e96687d9a52` (2026-11-15 15:59:59 UTC). Ne pas utiliser `latest` dans une installation reproductible. |
| Fonctions vérifiées | Validation de la syntaxe YAML Actions, types et propriétés des expressions `${{ }}`, inputs/outputs d'actions, contrats des reusable workflows, dépendances `needs`, cron et globs ; analyses de scripts shell et Python ; détection de script injection, permissions excessives, triggers dangereux, cache poisoning, credentials persistants, actions non épinglées et règles de timeout/concurrency. Baselines et profils permettent une adoption progressive. |
| Mode réseau / confidentialité | Le README indique « no network unless you ask » : les contrôles GitHub distants ne s'activent qu'avec `--online` (ou `JACTIONLINT_ONLINE`). Le mode local par défaut peut auditer les fichiers déjà présents sans envoyer le code. Pour les dépôts privés, utiliser seulement le checkout local ; ne pas fournir `GH_TOKEN`, `JACTIONLINT_TOKEN` ou autre secret pour ce cycle. |
| Dépendances / toolchain | Le `go.mod` du tag v2.6.0 déclare `go 1.26.0` et `toolchain go1.27.4`; dépendances Go épinglées dans le manifeste, dont `mvdan.cc/sh/v3`. La compilation depuis les sources n'est pas compatible avec le Go 1.23.2 de l'environnement temporaire. Le README documente aussi une distribution PyPI (`uvx`) et des binaires de release ; utiliser un artefact précompilé versionné plutôt que compiler avec une toolchain plus ancienne. Les intégrations ShellCheck/Pyflakes sont documentées ; l'image Docker officielle les inclut, mais Docker n'est pas requis pour le lint local de base. |
| Installation préparée | Après vérification de la provenance et du hash du paquet : `uvx --from "jactionlint==2.6.0" jactionlint --version`, puis depuis une copie locale du dépôt : `jactionlint --no-online`. Alternative source, non compatible avec le Go actuel : `go install github.com/jdx/jactionlint/v2/cmd/jactionlint@v2.6.0` avec Go 1.26+ et toolchain 1.27.4. |
| Coûts / dépendances propriétaires | MIT, gratuit en local ; aucun abonnement, crédit, GPU ou API fournisseur. Les contrôles en ligne solliciteraient GitHub et nécessiteraient un token pour certaines fonctions privées : ils restent désactivés. Les téléchargements de release/PyPI nécessitent un accès réseau et consomment du trafic/disque. |
| Matériel / plateformes | CLI hôte Linux/macOS/Windows via wheels ou binaires publiés ; charge CPU/RAM modérée pour des fichiers YAML/JSON et scripts, aucun GPU. Ce n'est pas un outil Android et il ne pilote pas directement un Samsung. Pour la compilation depuis source, Go 1.26+ et toolchain 1.27.4 ; pour la distribution binaire, vérifier l'architecture et la compatibilité libc de l'artefact exact. |
| Limites / garde-fous | La version 2.6.0 ajoute des règles qui peuvent faire apparaître des findings auparavant absents ; commencer par un audit informatif et un baseline, sans bloquer la CI. Ne pas exécuter `--fix`, `update --apply` ni `run` dans les dépôts existants pendant la qualification : ces modes peuvent modifier les workflows, changer des références d'actions ou exécuter des étapes de workflow. Le mode `run` doit faire l'objet d'un audit sandbox séparé. |
| Projets cibles / verdict | Tous les dépôts Ascameleon avec `.github/workflows`, priorité AI ORCHESTRA, Torcscandz, BLUE ALERTS, Gameforge-3D, Tripradar, CallerID et NIA Studio AI. **MAYBE** : source, licence, release et utilité confirmées ; installation et smoke test bloqués par DNS, et binaire/checksum de v2.6.0 non vérifiés dans cet environnement. Aucun ajout de workflow ni de dépendance projet autorisé à ce stade. |

Preuves amont :
- Dépôt et README : https://github.com/jdx/jactionlint
- Licence MIT du tag : https://github.com/jdx/jactionlint/blob/v2.6.0/LICENSE.txt
- NOTICE et provenance des règles : https://github.com/jdx/jactionlint/blob/v2.6.0/NOTICE.md
- Release v2.6.0 / commit : https://github.com/jdx/jactionlint/commit/72c00452809bcca05b8bc12acdcf15dd7a9c1c5e
- Dernier commit amont observé : https://github.com/jdx/jactionlint/commit/2964d0e78d7f0c50d9d213a771ff4e96687d9a52
- Documentation d'installation et vérification des binaires : https://jactionlint.jdx.dev/install

### 18.3 Alternatives examinées mais non ajoutées comme entrées séparées

| Candidat | Éléments vérifiés | Décision |
|---|---|---|
| zizmor | https://github.com/zizmorcore/zizmor ; MIT ; release v1.32.0, commit `21bd300700d43d9ba04b0c1fce72a89391ac80b4` ; HEAD `7d0f219e13696b02e593f9544ffd620fcd97741f` observé le 2026-11-17 02:01 UTC ; rust-toolchain du tag `1.97.0`. Audit statique GitHub Actions, offline natif, mais toolchain source plus récente et recouvrement important avec les règles sécurité intégrées à jactionlint. | **Non ajouté séparément** pour éviter de doubler la même couverture ; reste une alternative autonome si l'on choisit ultérieurement un scanner sécurité pur. |
| rhysd/actionlint (upstream original) | MIT ; dernière release stable affichée v1.7.12 (2026-03-30), commit de release court `914e7df` ; `go.mod` de ce tag exige Go 1.25.0. Issue ouverte #719 (2026-08-06) rapporte l'inactivité du mainteneur ; activité upstream observée jusqu'au 2026-04-19 seulement. | **FAIL pour adoption directe dans ce cycle** : maintenance amont incertaine et retard sur les nouvelles syntaxes GitHub Actions. Ne pas utiliser `@latest` ni une action tierce mutable. |
| kjanat/actionlint (fork maintenu) | MIT indiqué par pkg.go.dev ; v1.17.1 publié le 2026-11-09 ; HEAD observé le 2026-11-17 ; `go.mod` du tag exige Go 1.26 et toolchain 1.27.3. | **MAYBE / non retenu** : fork actif et pertinent, mais jactionlint offre une couverture combinée syntaxe/sécurité/politique et une distribution documentée ; ne pas compiler ce fork avec Go 1.23.2. |

### 18.4 Installation et tests réellement effectués

- Environnement temporaire contrôlé : Python 3.13.5, uv présent, Go 1.23.2, Node 22.16.0 ; aucun binaire `jactionlint`, `zizmor`, `actionlint`, aucun Rust/Cargo, aucun Docker.
- Tentative réelle et isolée : `UV_CACHE_DIR=/tmp/ascameleon-jactionlint-uv-cache uvx --from 'jactionlint==2.6.0' jactionlint --version`.
- Résultat : échec avant téléchargement, résolution DNS de `pypi.org` impossible (`Temporary failure in name resolution`). Aucun paquet ni binaire installé ; aucun `--version`, import ou scan des dépôts réussi.
- Le même environnement ne peut pas compiler jactionlint v2.6.0 depuis le tag : Go 1.23.2 est inférieur à Go 1.26.0 et au toolchain 1.27.4 déclaré. Aucun contournement par mise à niveau de toolchain n'a été effectué.
- Aucun workflow, fichier source, lockfile, action ou dépendance Ascameleon modifié. Aucun audit de workflow exécuté ; aucun finding de sécurité revendiqué.
- Aucun token GitHub, secret, fournisseur, API payante ou service cloud utilisé ; coût : 0 €.

### 18.5 Décisions et priorités suivantes

1. Quand le DNS/PyPI ou les assets GitHub sont accessibles, récupérer jactionlint v2.6.0 dans un répertoire temporaire, vérifier signature/provenance et SHA-256 de l'artefact exact, puis exécuter uniquement `jactionlint --no-online` sur une copie locale des workflows.
2. Commencer par un rapport informatif et un baseline ; ne pas ajouter de job bloquant avant tri manuel des findings existants. Ne pas utiliser `--fix`, `update --apply`, `--online` ou `run` pendant le premier audit.
3. Si jactionlint révèle des findings réels, corriger uniquement les workflows concernés sur une branche séparée et ajouter une validation non régressive ; vérifier les faux positifs avant toute PR.
4. Torcscandz #5 : maintenir la PR en brouillon jusqu'à la mise à jour de branche et l'essai Samsung + ELM327 physique.
5. BLUE ALERTS #51/#52/#53 : ne pas fusionner sans smoke test MCP réel et preuves visuelles fraîches sur les heads exacts.
6. Cycle 1 : générer un diagnostic actuel à partir des commits/workflows récents ; aucun rapport Cycle 1 récent n'a été retrouvé dans les issues consultées.

**Résultat du cycle 12 :** 1 nouvel outil documenté en MAYBE (jactionlint) ; 2 alternatives comparées/non ajoutées séparément (zizmor et actionlint forks/upstream) ; 0 installation ; 0 smoke test réussi ; aucun changement de production ; catalogue mis à jour uniquement sur `main` ; coût 0 €.


---

## 19. Nouvel outil examiné — cycle du 2026-11-17 (11:42, Africa/Algiers)

### 19.1 Trimesh — précontrôle géométrique local GLB/GLTF (MAYBE)

| Champ | Qualification |
|---|---|
| Nom / catégorie | **Trimesh** — bibliothèque Python de chargement, export, inspection et analyse de maillages triangulaires et scènes 3D |
| Dépôt GitHub exact | https://github.com/mikedh/trimesh |
| Source et licence | Source complète publique ; licence MIT confirmée dans `LICENSE.md` du tag 5.2.1 (blob `d0571124dc68ee63553001f17f043d19250159cc`). Conserver le copyright et le texte MIT lors d'une redistribution. |
| Version / commit épinglé | Release `5.2.1`, publiée le 2026-11-12 à 17:37 UTC. Le tag `5.2.1` pointe directement sur le commit `7fe4ac4405ba5af02756c2db729da6822510304c`. Dernier commit principal observé : ce même commit, daté 2026-11-12 17:09 UTC ; métadonnées du dépôt actualisées le 2026-11-17. |
| Fonctions utiles vérifiées | Import/export GLB et glTF, OBJ, STL et PLY ; lecture de scènes avec plusieurs nœuds/instances ; nombre de sommets et faces, dimensions et bounding boxes, composants connectés, orientation, volume et propriété watertight ; génération de maillages procéduraux et round-trip local GLB. |
| Installation reproductible depuis GitHub | Dans un environnement isolé Python 3.10+ : `python -m venv .venv-trimesh`, activer l'environnement, puis `python -m pip install "numpy>=1.21" "setuptools>=61" wheel`, enfin `python -m pip install --no-deps --no-build-isolation "git+https://github.com/mikedh/trimesh.git@7fe4ac4405ba5af02756c2db729da6822510304c"`. Vérifier ensuite `python -c "import trimesh; print(trimesh.__version__)"`. Ne pas installer l'extra `[all]` : il ajoute de nombreuses dépendances facultatives non nécessaires au contrôle GLB de base. |
| Dépendances | Dépendance dure du tag : `numpy>=1.21`. Build : `setuptools>=61` et `wheel`. Extras optionnels séparés (par exemple scipy, networkx, shapely, rtree, pillow, lxml, pyglet, manifold3d) ; ne pas les ajouter au projet sans besoin identifié. Le README indique que le cœur peut charger GLB/glTF avec NumPy seul. |
| Coûts / services propriétaires | MIT, exécution locale gratuite ; aucun compte, abonnement, crédit, GPU cloud ou appel API. L'installation depuis GitHub nécessite le réseau uniquement au téléchargement ; le contrôle d'un fichier GLB local n'en nécessite pas. |
| Matériel / plateformes | Python 3.10+ sur Linux/macOS/Windows ; CPU et RAM proportionnels à la taille du maillage et de la scène ; aucun GPU requis pour les statistiques de géométrie de base. Pas une application Android/Samsung et pas une dépendance navigateur/Three.js. À utiliser comme outil QA hôte séparé. |
| Compatibilité projet | **Gameforge-3D** et **BLUE ALERTS** : candidat pour précontrôler les GLB exportés (chargement, dimensions, nombre de primitives/sommets/faces, composants, volumes et round-trip). Peut être lancé dans une étape QA Python séparée sans modifier le runtime JavaScript. Aucun branchement CI ou dépendance applicative ajouté pendant ce cycle. |
| Limites / sécurité | Ce n'est ni un moteur de rendu ni un validateur complet de fidélité PBR. Des issues amont ouvertes signalent des cas à ne pas utiliser comme critères d'acceptation sans tests dédiés : normalisation de couleurs glTF `COLOR_0` (#2669), normales de sommets sur triangles très fins (#2680) et lissage de normales à travers des plis éloignés (#2682). Ne pas lui confier la validation visuelle des couleurs, textures, normales ou du rendu final ; garder glTF-Validator et les captures Playwright pour ces contrôles. Pour les fichiers non fiables, n'autoriser que des GLB produits localement, limiter les tailles et ne pas activer de résolution d'URI distante. |
| Verdict / cible | **MAYBE** pour un outil QA local de géométrie uniquement. Utile à Gameforge-3D et BLUE ALERTS ; ne pas l'intégrer au runtime ni l'utiliser seul pour accepter un asset PBR. Installation de la version épinglée 5.2.1 non réalisée à cause du DNS ; le smoke test ci-dessous porte uniquement sur la version 4.11.1 déjà présente dans l'environnement. |

Preuves amont :
- Dépôt / README : https://github.com/mikedh/trimesh
- Release 5.2.1 : https://github.com/mikedh/trimesh/releases/tag/5.2.1
- Référence exacte du tag : https://github.com/mikedh/trimesh/tree/5.2.1
- Commit du tag : https://github.com/mikedh/trimesh/commit/7fe4ac4405ba5af02756c2db729da6822510304c
- Manifeste de dépendances et Python minimum : https://github.com/mikedh/trimesh/blob/5.2.1/pyproject.toml
- Licence MIT : https://github.com/mikedh/trimesh/blob/5.2.1/LICENSE.md
- Issue couleurs normalisées : https://github.com/mikedh/trimesh/issues/2669
- Issue normales de sommets : https://github.com/mikedh/trimesh/issues/2680
- Issue lissage : https://github.com/mikedh/trimesh/issues/2682

### 19.2 Installation et smoke test réellement effectués

- Environnement hôte contrôlé : Python 3.13.5, NumPy 2.3.5, Git 2.47.3.
- Une version **déjà présente dans l'image d'exécution**, `trimesh 4.11.1`, a été importée ; elle n'a pas été installée pendant ce cycle.
- Smoke test local réussi sur cette version préinstallée : création d'une boîte 1×2×3, export GLB (960 octets), rechargement, vérification de 8 sommets, 12 faces, dimensions [1, 2, 3] et maillage watertight. Résultat : PASS pour le round-trip élémentaire de la version 4.11.1 uniquement.
- Tentative d'installation du commit exact 5.2.1 avec `pip install --no-deps --target /tmp/asc-trimesh git+https://github.com/mikedh/trimesh.git@7fe4ac4405ba5af02756c2db729da6822510304c` : échec avant téléchargement, DNS de `github.com` non résolu. Aucun code source téléchargé, aucune version 5.2.1 installée, aucun import ou test de cette version revendiqué.
- Aucun fichier de production, workflow, lockfile ou dépendance de Gameforge-3D / BLUE ALERTS modifié. Aucun asset du dépôt n'a été modifié ou accepté sur la base de ce smoke test.

### 19.3 Alternative examinée mais non retenue — gltfjsx (FAIL pour les dépôts actuels)

| Champ | Résultat |
|---|---|
| Dépôt | https://github.com/pmndrs/gltfjsx |
| Licence | MIT confirmée dans `LICENSE` |
| Dernier commit source observé | `f4fbfa2a19ffa7c05b1a93745da7b4a7abd497f4`, 2024-11-04 16:51 UTC |
| Release | Aucune release GitHub publiée détectée pendant ce contrôle |
| Fonction | Convertit les fichiers GLTF en composants JSX destinés à React Three Fiber |
| Verdict | **FAIL pour l'adoption dans Gameforge-3D et BLUE ALERTS actuels** : ces runtimes utilisent Three.js direct et non React/React Three Fiber ; le générateur JSX n'apporte pas de bénéfice sans migration d'architecture, qui n'est pas autorisée. Le dépôt n'est pas déclaré globalement abandonné ; son adéquation aux stacks actuelles est insuffisante. |

### 19.4 Comparaison avec le catalogue existant et décisions suivantes

- Aucun doublon Trimesh détecté avant recherche. Les entrées existantes `glTF-Validator`, `glTF-Transform` et `meshoptimizer` restent complémentaires : validation du format, transformation/optimisation et inspection géométrique ne sont pas interchangeables.
- `gltfjsx` n'est pas ajouté comme outil réutilisable ; son rejet d'adéquation est conservé ci-dessus.
- Si le DNS redevient disponible, installer Trimesh 5.2.1 dans un environnement jetable, vérifier le commit et le numéro de version, puis exécuter le même round-trip GLB et des fixtures géométriques contrôlées. Avant tout ajout CI, définir des seuils de taille/triangles et comparer les résultats au validateur glTF et aux captures browser.
- Ne pas activer les extras optionnels et ne pas modifier le runtime Three.js. Ne pas utiliser les résultats de Trimesh pour certifier la fidélité des matériaux, couleurs, textures ou normales.
- Diagnostics Cycle 1 : aucune issue ouverte ou note de diagnostic dédiée n'a été retrouvée dans les recherches GitHub effectuées. Les états courants des branches et PR sont utilisés comme signaux opérationnels, sans les présenter comme un rapport Cycle 1 formel.
- Projets contrôlés : AI ORCHESTRA `f49ba2a9d409c866642b350ecc32aedbf2b53901`, TorcScan `1c98135210eecb314ac67e526000d37ca3f99637`, BLUE ALERTS `e1b629197ee93435d1c8616927bb452ccfc2854d`, Gameforge-3D `83ff2cd33c6380a63843a39ee3bed882e9a3c11f`, TripBoost `c63b52ac27a56ad97393f61d36fb8968ccce0c53`, CallerID `2c421c2efa038f80011a21b4874bb2105608ae04`, NIA Studio AI `c957672e70d4df34a9ced1912c3e4839d4face6c`, Ruflo `056a11ece4ca3bd234aafd6221156d24b80a9544`, Playwright-Samsung `842479e849ac6115500939702358b3d66a764e72`.
- PR ouvertes revérifiées : TorcScan #5 ouverte, brouillon, mergeable mais validation Samsung/OBD2 requise ; BLUE ALERTS #51 ouverte et brouillon, test MCP local en attente ; #52 et #53 ouvertes, brouillons et non mergeables, preuves visuelles exact-head encore requises. TripBoost #22 et NIA Studio AI #13 sont déjà fusionnées.
- Statuts combinés des sept commits principaux consultés : aucun statut n'a été renvoyé par l'endpoint de statuts pour ces SHA ; cela ne vaut pas preuve d'échec ni de réussite des workflows. Ne pas annoncer ces commits comme CI verts sur cette seule base.

**Résultat du cycle du 2026-11-17 :** 1 nouvel outil qualifié MAYBE (Trimesh 5.2.1) ; 1 alternative non retenue pour incompatibilité de stack (gltfjsx) ; 0 installation de la version candidate ; 1 smoke test réussi sur la version préinstallée 4.11.1 ; aucun changement applicatif ; catalogue actualisé sur `main` ; coût 0 €.


---

## 20. Cycle 14 — analyse statique locale des APK Android (2026-11-17, 12:48 Africa/Algiers)

### 20.1 Diagnostics Cycle 1 et état des dépôts avant recherche

- Catalogue canonique relu sur `main` avant la recherche : blob `e72fd919d5432f94da48aeca0d781939918ad22d`, 121 819 caractères. Comparaison anti-doublon effectuée : aucune entrée Androguard, MobSF ou apktool existante. Les outils Android déjà documentés (Appium, Maestro, Patrol, scrcpy et Playwright-Samsung) couvrent l'automatisation et l'observation runtime, mais ne remplacent pas une inspection statique d'un APK construit.
- Recherche des issues ouvertes de l'organisation Ascameleon : aucune issue ouverte ne constitue un rapport Cycle 1 récent. Recherche des fichiers/termes « Cycle 1 » dans AI ORCHESTRA : aucun diagnostic exploitable retrouvé. Le dernier diagnostic formel conservé dans le catalogue reste ancien ; ne pas le présenter comme un audit frais.
- Heads `main` revérifiés via l'historique GitHub :
  - AI ORCHESTRA : `c6168e44d40ad58283376a8a3220cc8c89d18764`
  - Torcscandz : `1c98135210eecb314ac67e526000d37ca3f99637`
  - BLUE ALERTS : `e1b629197ee93435d1c8616927bb452ccfc2854d`
  - Gameforge-3D : `83ff2cd33c6380a63843a39ee3bed882e9a3c11f`
  - Tripradar / TripBoost : `c63b52ac27a56ad97393f61d36fb8968ccce0c53`
  - CallerID : `2c421c2efa038f80011a21b4874bb2105608ae04`
  - NIA Studio AI : `2bb0e3ba8330350721e31c0bee4c3999eaab4552`
  - Ruflo : `056a11ece4ca3bd234aafd6221156d24b80a9544`
  - playwright-samsung : `842479e849ac6115500939702358b3d66a764e72`
- PR opérationnelles revérifiées :
  - Torcscandz #5 : ouverte, brouillon, 47 commits, 7 fichiers modifiés, mergeable=true ; head mis à jour le 2026-11-17 07:56:50 UTC. L'essai Samsung + ELM327 physique reste un critère indépendant de la CI.
  - BLUE ALERTS #51 : ouverte, brouillon, mergeable=true ; 5 commits / 4 fichiers. Le smoke test Qwen/Blender sur le poste cible reste non effectué.
  - BLUE ALERTS #52 : ouverte, brouillon, non mergeable ; 28 commits / 5 fichiers. Captures exact-head et inspection visuelle restent requises.
  - BLUE ALERTS #53 : ouverte, brouillon, non mergeable ; 78 commits / 12 fichiers. La validation exacte et les captures fraîches restent requises.
- Les branches principales ne montrent pas de nouveau diagnostic Cycle 1 ; les états PR sont des signaux opérationnels, pas un substitut à l'audit.

### 20.2 Androguard 4.1.4 — inspection statique d'APK/DEX (MAYBE)

| Champ | Qualification |
|---|---|
| Nom / catégorie | **Androguard** — outil Python local d'analyse statique et de rétro-ingénierie Android (APK, DEX, AXML, ressources) |
| Dépôt GitHub canonique | https://github.com/androguard/androguard |
| Code source / licence | Sources publiques ; licence **Apache-2.0** explicitée dans le README du tag et fournie par `LICENCE-2.0` (texte intégral vérifié). La métadonnée de la release déclare également « Apache Licence, Version 2.0 ». Conserver le fichier de licence et les notices lors d'une redistribution. |
| Version stable retenue | Release GitHub `v4.1.4`, publiée le **2026-06-05** ; commit exact du tag `d594fd39beb934e438a5bf8089b206d5800d81e0`. Pyproject du tag confirme `version = 4.1.4`. Release consultée : https://github.com/androguard/androguard/releases/tag/v4.1.4 |
| État amont actuel | Dépôt non archivé. HEAD `master` observé : `581f7a3251545a97f66ee92b674dd810ee380a00`, commit du **2026-10-25 09:40:24 UTC**. Attention : le `master` actuel déclare déjà `5.0.0` et un état Beta ; ce n'est pas la release stable v4.1.4. Ne pas installer le HEAD 5.0.0 par inadvertance. |
| Fonctions utiles | Lecture de l'APK, métadonnées package/version, permissions, AndroidManifest binaire, ressources, DEX/ODEX, classes, méthodes et chaînes ; désassemblage/décompilation en options ; recherche de références et détection de certains motifs vulnérables. CLI `androguard` et API Python. |
| Installation reproductible | Dans un environnement hôte isolé Python 3.10–3.13 : `python -m venv .venv-android-audit`, activation, puis `python -m pip install "androguard==4.1.4"`. Contrôles préparés : `androguard --help` et `python -c "from androguard.core.apk import APK; print('Androguard APK API import OK')"`. Vérifier le numéro de version, les hashes des wheels et le lockfile avant de réutiliser le venv. Ne pas utiliser `pip install git+...@master` ni `androguard[full]` pour cette première évaluation. |
| Dépendances | Le pyproject v4.1.4 déclare Python `>3.9.0, !=3.9.1, <4.0`, Pygments, lxml, colorama, asn1crypto, click, pydot, IPython, mutf8, dataset, loguru, apkInspector, networkx, PyYAML et cryptography >=46.0.6. Cela représente une empreinte plus lourde qu'un simple parseur de manifeste. Frida et matplotlib sont optionnels dans les évolutions récentes ; ne pas ajouter d'extras inutiles. |
| Coûts / réseau / dépendances propriétaires | Apache-2.0, gratuit en local ; aucune clé, API, crédit, abonnement ou GPU requis pour l'analyse de base. Le téléchargement initial des paquets nécessite PyPI. Les fonctions MCP/LLM sont optionnelles et ne sont pas nécessaires ; ne pas les activer dans ce cycle. |
| Matériel / compatibilité | Outil hôte Python sur Linux/macOS/Windows ; CPU/RAM variables selon taille APK, nombre de DEX et décompilation. Pas besoin de GPU. Compatible avec une chaîne de build Python 3.11/3.12 sur le plan de la version déclarée. Ce n'est **pas** une application Android/Samsung et ne teste pas le comportement runtime du téléphone ; copier l'APK vers un hôte autorisé avant l'analyse. |
| Cibles Ascameleon | Torcscandz/TorcScan et CallerID : contrôle pré-release des permissions manifest, package/version, SDK cible, composants et éléments DEX/strings sur l'APK produit par CI. Peut fournir une vérification indépendante de l'artefact sans modifier le code de production. |
| Limites / sécurité | Le README du HEAD signale que la documentation est en cours de mise à jour. La branche master 5.0.0 est une réorganisation majeure utilisant plusieurs dépendances Rust installées depuis des dépôts Git distincts ; ne pas la confondre avec v4.1.4 ni avec le package PyPI. Issue ouverte #1184 (2026-11-05) : certains APK valides avec ressources localisées peuvent échouer lors de l'extraction de `android:label` ; en cas d'erreur, utiliser `aapt dump badging`/Android SDK comme contrôle indépendant. L'outil n'est pas une preuve d'absence de vulnérabilité et ne remplace ni Play Integrity, ni tests dynamiques, ni test Samsung/OBD2. N'analyser que des APK détenus ou explicitement autorisés. |
| Verdict | **MAYBE** — pertinent comme étape QA statique indépendante pour TorcScan et CallerID, mais installation et test bloqués par DNS dans cet environnement. Ne pas ajouter comme dépendance runtime ni bloquer la release avant un essai sur un APK de test autorisé. |

Preuves amont :
- Dépôt et README : https://github.com/androguard/androguard
- Release stable v4.1.4 : https://github.com/androguard/androguard/releases/tag/v4.1.4
- Commit exact du tag : https://github.com/androguard/androguard/commit/d594fd39beb934e438a5bf8089b206d5800d81e0
- Licence Apache-2.0 du tag : https://github.com/androguard/androguard/blob/v4.1.4/LICENCE-2.0
- Manifeste v4.1.4 : https://github.com/androguard/androguard/blob/v4.1.4/pyproject.toml
- README v4.1.4 : https://github.com/androguard/androguard/blob/v4.1.4/README.md
- HEAD master observé : https://github.com/androguard/androguard/commit/581f7a3251545a97f66ee92b674dd810ee380a00
- Issue de parsing des labels localisées : https://github.com/androguard/androguard/issues/1184

### 20.3 Alternative examinée — MobSF (non admise séparément dans ce cycle)

- Dépôt : https://github.com/MobSF/Mobile-Security-Framework-MobSF
- Candidat plus large de sécurité mobile (analyse statique/dynamique, rapports), mais empreinte opérationnelle nettement supérieure et dépendances de service/VM ou Docker selon le mode.
- Pas de version, commit, licence exacte et procédure complète qualifiés pendant ce passage ; aucune entrée PASS/MAYBE n'est créée sur une simple recherche par nom. À réévaluer si un besoin d'audit de sécurité Android complet est confirmé, après qualification de sa licence et de ses composants embarqués.

### 20.4 Installation et tests réellement effectués

- Environnement hôte contrôlé : Python 3.13.5, pip 25.1.1 ; module `androguard` absent avant tentative.
- Tentative réelle et isolée : `python -m pip install --disable-pip-version-check --no-cache-dir --target /tmp/ascameleon-androguard-4.1.4 "androguard==4.1.4"`.
- Résultat : échec avant téléchargement, résolution DNS de `pypi.org` impossible (`Temporary failure in name resolution`). Aucun paquet installé, aucun import, `androguard --help` ou scan APK réussi.
- Aucune APK de Torcscandz/CallerID n'a été téléchargée ni analysée dans ce cycle. Aucun fichier de production, workflow, lockfile ou dépendance projet modifié.
- Aucune clé, aucun service externe payant, aucun appel IA/API, aucune dépense : **0 €**.

### 20.5 Décisions et priorités suivantes

1. Quand PyPI est accessible, installer exactement `androguard==4.1.4` dans un venv temporaire, vérifier version et hashes, puis importer `androguard.core.apk.APK`.
2. Utiliser un APK de test appartenant au projet ou explicitement autorisé ; produire un rapport limité au package, versionCode/versionName, min/target SDK, permissions, composants exportés, signature et présence des DEX. Masquer les chaînes potentiellement sensibles.
3. Comparer les permissions extraites avec les permissions attendues dans le manifeste source ; toute différence doit être revue manuellement, pas corrigée automatiquement.
4. Tester le cas de labels localisés signalé par l'issue #1184 ; si l'analyse échoue, consigner le défaut et utiliser `aapt dump badging` comme contrôle secondaire.
5. Ne pas intégrer Androguard 5.0.0 depuis `master` tant que sa sortie stable, ses dépendances Git/Rust et sa compatibilité complète n'ont pas été qualifiées.
6. Torcscandz #5 : maintenir le brouillon jusqu'à la synchronisation de branche et au test Samsung + ELM327. BLUE ALERTS #51/#52/#53 : garder les critères MCP et captures exact-head ; aucun changement n'est justifié par l'ajout d'Androguard.

**Résultat du cycle 14 :** 1 nouvel outil qualifié MAYBE (Androguard v4.1.4) ; 1 alternative non admise faute de qualification suffisante (MobSF) ; 0 installation ; 0 smoke test réussi ; aucun changement de production ; catalogue mis à jour sur `main` ; coût 0 €.


---

## 21. Cycle 15 — inventaire de vulnérabilités multi-écosystèmes avec OSV-Scanner (2026-11-17, 13:40 Africa/Algiers)

### 21.1 Diagnostics Cycle 1 et état des projets relus avant recherche

- Catalogue canonique relu sur `main` avant toute recherche : blob `7be428dcb310902fa50e2372c28dd0c03a7b1e3b`, 132 247 caractères. Comparaison anti-doublon effectuée : aucune entrée OSV-Scanner ou google/osv-scanner existante. Les entrées `govulncheck`, `gosec`, `Trivy` (candidat rejeté dans un cycle antérieur), `uv`, ainsi que les outils de QA déjà répertoriés restent distincts. OSV-Scanner apporte une analyse multi-écosystèmes des manifests/lockfiles et une base OSV locale ; il ne remplace pas govulncheck pour l'analyse de reachability Go.
- Recherche GitHub des issues ouvertes de l'organisation Ascameleon : **aucune issue ouverte retournée**. Recherche de « Cycle 1 diagnostic audit report » dans AI ORCHESTRA : seul le présent catalogue a été retrouvé ; aucun rapport Cycle 1 autonome plus récent n'est disponible. Le dernier diagnostic formel conservé dans ce catalogue reste daté du 2026-11-16 à 22:53 UTC ; il n'est pas présenté comme un audit frais.
- Heads `main` les plus récents retournés par la recherche GitHub :
  - AI ORCHESTRA : `36c29474bd2c2d5262b26cb26f01b35d2455a78d` (mise à jour du catalogue, 2026-11-17 11:57:52 UTC).
  - Torcscandz : `1c98135210eecb314ac67e526000d37ca3f99637`.
  - BLUE ALERTS : `e1b629197ee93435d1c8616927bb452ccfc2854d`.
  - Gameforge-3D : `83ff2cd33c6380a63843a39ee3bed882e9a3c11f`.
  - Tripradar/TripBoost : `c63b52ac27a56ad97393f61d36fb8968ccce0c53`.
  - CallerID/Callerid : `2c421c2efa038f80011a21b4874bb2105608ae04`.
  - NIA Studio AI : `2bb0e3ba8330350721e31c0bee4c3999eaab4552`.
- PR opérationnelles relues :
  - TripBoost #23 est ouverte, non fusionnée. Son head est `86ac011647dabb42591d54a4b85553d99ca69d24`; le workflow exact-head #209 (run `44080984916`) est terminé avec succès. La description de la PR rapporte 57 tests JavaScript réussis, des tests Python et validations Docker réussis ; aucun appel Amadeus réel n'est revendiqué.
  - Torcscandz #5 est ouverte et en brouillon ; 7 fichiers modifiés. Elle exige toujours un test physique Samsung + adaptateur OBD2 avant fusion.
  - BLUE ALERTS #51 est ouverte et en brouillon (4 fichiers) ; le pont Qwen/Blender attend un smoke test sur le poste cible. #52 et #53 restent des travaux artistiques en brouillon, avec validation visuelle exacte-head non acquise.
- Besoin retenu : disposer d'un scanner local en lecture seule qui couvre les modules Go extraits dans le workflow CallerID et puisse ensuite être réutilisé sur les lockfiles Python/Node/Dart lorsqu'ils seront réellement présents. Le workflow CallerID reconstruit et extrait l'archive source dans `callerid`, utilise Go `1.22.x`, puis exécute `go test ./...` et `go vet ./...`. Le dépôt racine ne contient pas de `callerid/go.mod` avant cette étape d'extraction : ne pas prétendre qu'un scan direct du dépôt courant a déjà été effectué.
- AI ORCHESTRA possède un `pyproject.toml` avec des plages de versions mais aucun `uv.lock` constaté dans le diagnostic du catalogue ; ne pas supposer que le scanner peut analyser ce fichier seul. NIA Studio AI restaure des `requirements.txt` depuis une archive, mais plusieurs exigences sont des plages non verrouillées ; l'issue OSV-Scanner #3262 signale précisément une limite sur les exigences Python non épinglées. Le premier cas d'usage reste donc le `go.mod` extrait de CallerID.

### 21.2 OSV-Scanner v2.7.1 — analyse de vulnérabilités des dépendances (MAYBE)

| Champ | Qualification |
|---|---|
| Nom / catégorie | **OSV-Scanner** — scanner CLI open source de vulnérabilités de dépendances, manifests, lockfiles, SBOM et images de conteneurs |
| Dépôt GitHub exact | https://github.com/google/osv-scanner |
| Source / licence | Code source public ; fichier `LICENSE` du tag v2.7.1 vérifié : **Apache-2.0**. Conserver le fichier de licence et les notices lors de redistribution. |
| Version stable épinglée | Release GitHub **v2.7.1**, publiée le **2026-11-09**. Commit de release exact et signature GitHub vérifiée : `02f96a40691c2d155fdda799af436e111231e365`. URL : https://github.com/google/osv-scanner/releases/tag/v2.7.1 |
| Activité amont | HEAD `main` observé : `5979c1de2800bd53c02f6bac7c9db4dc18d73fa3`, commit du **2026-11-17 03:06:34 UTC**. Le dépôt est actif ; la release v2.7.1 reste le tag stable retenu, ne pas suivre `main` ni `latest` dans un pipeline reproductible. |
| Fonctions utiles | Analyse des dépendances Go, Python, Java, JavaScript, Dart, Rust, PHP, Ruby, C/C++ et d'autres écosystèmes ; lecture de lockfiles/manifests supportés ; détection de vulnérabilités depuis la base OSV ; rapports JSON, table, HTML, SARIF, SPDX et CycloneDX ; mode hors ligne avec base locale ; analyse de licences et recommandations de correction (cette dernière fonction n'est pas autorisée dans le premier essai). |
| Installation reproductible | Préférer le binaire officiel précompilé de la release v2.7.1 pour Linux x86_64, macOS ou Windows. Exemple Linux amd64 : télécharger `https://github.com/google/osv-scanner/releases/download/v2.7.1/osv-scanner_linux_amd64`, enregistrer sous `osv-scanner_linux_amd64`, puis `chmod +x osv-scanner_linux_amd64`. Télécharger aussi `multiple.intoto.jsonl` depuis la même release et vérifier le binaire avec `slsa-verifier verify-artifact ./osv-scanner_linux_amd64 --provenance-path multiple.intoto.jsonl --source-uri github.com/google/osv-scanner --source-tag v2.7.1`. Les binaires de release sont annoncés SLSA Level 3 par la documentation officielle. |
| Compilation depuis les sources | Le `go.mod` du tag v2.7.1 déclare `go 1.27.3`. L'environnement de ce cycle dispose de Go 1.23.2 : **ne pas compiler depuis les sources ici**. La page d'installation générique indique Go 1.26.2+, mais le manifeste du tag épinglé est la référence conservatrice pour cette version. Le binaire précompilé évite de modifier la toolchain des projets. |
| Dépendances | Implémentation Go ; le manifeste v2.7.1 inclut notamment `google/osv-scalibr`, bindings OSV, gRPC/protobuf et bibliothèques de parsing. Les binaires officiels évitent d'installer ces dépendances dans les projets. Aucun module à ajouter à CallerID ou AI ORCHESTRA pour utiliser le CLI. |
| Coûts / réseau / confidentialité | Le code et le scanner sont gratuits ; aucun abonnement, crédit, GPU, clé secrète ou API commerciale n'est nécessaire. Le mode en ligne interroge OSV.dev et transmet les identifiants/version des dépendances ; ne pas l'utiliser pour le premier test si l'on veut éviter toute transmission. Le mode `--offline` consulte une base OSV locale et n'envoie aucun nom de projet/dépendance ; la base doit être téléchargée une première fois depuis les fichiers publics OSV (GCS/HTTPS), puis peut être utilisée sans réseau. Le téléchargement initial est gratuit mais consomme réseau et disque. |
| Base hors ligne | La documentation officielle décrit `OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY` et la structure `<cache>/osv-scalibr/<ecosystem>/all.zip`. Pour CallerID, ne télécharger que la base Go nécessaire : `https://osv-vulnerabilities.storage.googleapis.com/Go/all.zip`, puis la placer sous `<cache>/osv-scalibr/Go/all.zip`. Vérifier l'intégrité du ZIP et sa date de mise à jour avant chaque campagne. L'option `--offline` ne télécharge ni ne rafraîchit la base pendant le scan. |
| Commande d'évaluation CallerID — préparée, non exécutée | Après reconstruction et extraction par le workflow CallerID : `./osv-scanner_linux_amd64 scan source --lockfile ./callerid/go.mod --offline --no-call-analysis=go --no-resolve --format=json --output-file osv-callerid.json`. `--no-call-analysis=go` évite le chemin govulncheck qui peut télécharger des modules et remplir le cache Go ; `--no-resolve` évite la résolution transitive via un service externe ; JSON évite les formats de rapport affectés par l'issue #3256. Cette commande ne corrige ni ne modifie les dépendances. |
| Matériel / compatibilité | Binaire hôte Linux/macOS/Windows, CPU généraliste ; aucun GPU et aucun service cloud requis pour l'analyse hors ligne. RAM/temps/disque varient avec le nombre de lockfiles, paquets et taille de la base locale ; mesurer avant de fixer un budget CI. Pas une application Android/Samsung : exécuter sur runner/ordinateur, après extraction de l'archive source. Compatible avec le module CallerID Go 1.22 en mode lecture de lockfile via binaire ; ne pas activer l'analyse d'appels Go lors du premier essai. |
| Cibles Ascameleon | Priorité **CallerID** après extraction de `CallerID-v2.3-source-patched.zip` dans le workflow de build ; potentiel ultérieur pour AI ORCHESTRA si un lockfile Python réel est ajouté, NIA Studio AI si ses dépendances sont verrouillées, TorcScan si un `pubspec.lock` est effectivement présent, et TripBoost/BLUE ALERTS/Gameforge-3D si des lockfiles pris en charge sont confirmés. Ne pas prétendre qu'un scan de ces dépôts a déjà été effectué. |
| Issues / limites amont à prendre en compte | #3273 : l'analyse d'appels Go peut télécharger des modules et écrire dans les caches Go ; la désactiver au premier essai. #3262 : exigences `requirements.txt` non épinglées/compoundées susceptibles d'être perdues avant résolution ; ne pas utiliser ce scanner comme preuve exhaustive sur les requirements non verrouillés. #3256 : certains reporters table/vertical/Markdown/CycloneDX peuvent masquer des erreurs d'écriture ; préférer JSON. #3261 : les scans récursifs peuvent ignorer des lockfiles suivis si un motif `.gitignore` les couvre ; passer le chemin explicite `--lockfile`. #3299 concerne la classification HTML de certains OS de conteneurs, non le scan Go source retenu. Le scanner n'est pas une preuve d'absence de vulnérabilité et ne remplace pas govulncheck ni les audits de code. |
| Sécurité d'utilisation | Utiliser uniquement le binaire signé/provenancé de la release, épingler la version, vérifier SLSA avant exécution, analyser uniquement les sources autorisées. Premier essai strictement en lecture seule : ne pas utiliser `fix`, `--apply`, résolution réseau, analyse d'image ou MCP. Le dépôt documente des protections de traversée de chemins et de taille d'archives, mais tout scanner de fichiers non fiables doit rester isolé. |
| Verdict | **MAYBE** — bon complément multi-écosystèmes pour un futur contrôle de dépendances, avec mode hors ligne et provenance SLSA ; pas encore installé ni testé ici. Le premier usage raisonnable est un scan Go explicite du répertoire CallerID extrait, en JSON et sans call-analysis. |

Preuves officielles consultées :
- Dépôt : https://github.com/google/osv-scanner
- Licence Apache-2.0 du tag : https://github.com/google/osv-scanner/blob/v2.7.1/LICENSE
- `go.mod` v2.7.1 : https://github.com/google/osv-scanner/blob/v2.7.1/go.mod
- Release et commit signé : https://github.com/google/osv-scanner/releases/tag/v2.7.1 et https://github.com/google/osv-scanner/commit/02f96a40691c2d155fdda799af436e111231e365
- Dernier commit amont observé : https://github.com/google/osv-scanner/commit/5979c1de2800bd53c02f6bac7c9db4dc18d73fa3
- Installation / provenance SLSA : https://google.github.io/osv-scanner/installation/
- Scan source et call-analysis : https://google.github.io/osv-scanner/usage/scan-source/
- Mode hors ligne : https://google.github.io/osv-scanner/usage/offline-mode/
- Lockfiles supportés : https://google.github.io/osv-scanner/supported-languages-and-lockfiles/
- Issues : https://github.com/google/osv-scanner/issues/3273 ; https://github.com/google/osv-scanner/issues/3262 ; https://github.com/google/osv-scanner/issues/3256 ; https://github.com/google/osv-scanner/issues/3261 ; https://github.com/google/osv-scanner/issues/3299

### 21.3 Installation et tests réellement effectués

- Environnement hôte vérifié : Linux x86_64, Go 1.23.2, Python 3.13.5, Node 22.16.0. `command -v osv-scanner` n'a retourné aucun binaire préinstallé.
- Tentative de téléchargement du binaire officiel v2.7.1 depuis GitHub avec `curl -I --connect-timeout 8 --max-time 15 -L https://github.com/google/osv-scanner/releases/download/v2.7.1/osv-scanner_linux_amd64` : échec DNS `Could not resolve host: github.com`.
- Aucun binaire téléchargé, aucune installation, aucune vérification SLSA locale, aucun scan de dépendances exécuté. Aucun fichier de production, workflow, lockfile ou dépendance des dépôts Ascameleon modifié.
- La tentative de compilation depuis les sources n'a pas été lancée : le `go.mod` v2.7.1 requiert Go 1.27.3, supérieur au Go 1.23.2 de l'environnement.
- Aucun accès OSV.dev ni appel deps.dev n'a été effectué ; aucune clé, API payante, dépense ou abonnement : **0 €**.

### 21.4 Comparaison et décisions

- `govulncheck` reste le candidat Go spécialisé déjà documenté ; OSV-Scanner est retenu comme complément multi-écosystèmes, pas comme remplacement.
- `Trivy` reste non retenu dans les conditions de sécurité documentées au cycle antérieur ; ne pas le réintroduire par simple commodité.
- Ne pas installer OSV-Scanner dans l'image runtime ni ajouter une dépendance à CallerID. L'intégration éventuelle doit être une étape CI non bloquante initiale, épinglée sur le binaire v2.7.1, avec provenance SLSA vérifiée, base locale datée, scan explicite du `go.mod` extrait et rapport JSON conservé comme artefact.
- Si le DNS reste indisponible, fournir le binaire et la base OSV depuis une source pré-téléchargée et vérifiée ; ne pas contourner la vérification de provenance ni utiliser un binaire tiers non officiel.
- Conserver les PR opérationnelles en l'état : TripBoost #23 attend la revue/fusion ; TorcScan #5 attend le test Samsung/OBD2 ; BLUE ALERTS #51 attend le smoke test MCP local et #52/#53 leurs validations visuelles exact-head.

**Résultat du cycle 15 :** 1 nouvel outil qualifié MAYBE (OSV-Scanner v2.7.1) ; 0 installation ; 0 import/smoke test réussi ; 0 scan de projet ; aucun changement applicatif ; catalogue actualisé sur `main` ; coût 0 €.
