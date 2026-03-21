# Tests et integration

Ce document couvre toutes les methodes pour tester le serveur MCP en local et
l'integrer avec un LLM dans le cloud.

## Outils disponibles

| Outil MCP | Description |
|---|---|
| `list_establishment_categories` | Liste toutes les categories supportees (EHPAD, IME, MAS…) |
| `geocode_address` | Convertit une adresse texte en coordonnees GPS (via Nominatim/OSM, sans cle) |
| `search_establishments` | Recherche des etablissements autour d'un point GPS par categorie |
| `get_establishment_by_finess` | Recupere un etablissement par son numero FINESS |

**Flux typique avec une adresse :**

```
utilisateur : "EHPAD autour du 10 rue de Rivoli, Paris"
       └─> geocode_address("10 rue de Rivoli, Paris")
              └─> { latitude: 48.855, longitude: 2.351 }
                     └─> search_establishments(lat, lon, radius_km=5, category="EHPAD")
```

Le LLM orchestre automatiquement ces deux appels en une seule requete utilisateur.

## Pre-requis

Une cle API ANS est necessaire pour les appels reels vers l'Annuaire Sante.
Les tests unitaires (pytest) n'en ont pas besoin car ils mockent l'API.

### Obtenir une cle API

1. Creer un compte sur le portail GRAVITEE de l'ANS :
   https://portal.api.esante.gouv.fr
2. Creer une application pour generer une cle.
3. Copier la valeur de la cle.

### Configurer le fichier .env

```bash
cp .env.example .env
# Editer .env
ESANTE_API_KEY=votre_cle_ici
```

---

## Tests en local

### Tests unitaires (sans cle API)

Les tests mockent toutes les requetes HTTP. Aucune cle reelle n'est necessaire.

```bash
ESANTE_API_KEY=dummy uv run pytest tests/ -v
```

Pour lancer uniquement un module de tests :

```bash
ESANTE_API_KEY=dummy uv run pytest tests/test_client.py -v
```

---

### Appel direct d'un outil depuis le terminal

La methode la plus rapide pour verifier qu'un outil fonctionne avec l'API reelle.
`fastmcp call` demarre le serveur, appelle l'outil et affiche le resultat.

```bash
# Lister les categories disponibles
ESANTE_API_KEY=votre_cle uv run fastmcp call \
  src/annuaire_mcp/main.py \
  --target list_establishment_categories

# Rechercher des EHPAD autour de Paris dans un rayon de 5 km
ESANTE_API_KEY=votre_cle uv run fastmcp call \
  src/annuaire_mcp/main.py \
  --target search_establishments \
  latitude=48.8566 longitude=2.3522 radius_km=5 category=EHPAD max_results=5

# Autres exemples de categories
ESANTE_API_KEY=votre_cle uv run fastmcp call \
  src/annuaire_mcp/main.py \
  --target search_establishments \
  latitude=45.7640 longitude=4.8357 radius_km=10 category=IME

# Geocoder une adresse (sans cle API ANS, Nominatim est public)
ESANTE_API_KEY=votre_cle uv run fastmcp call \
  src/annuaire_mcp/main.py \
  --target geocode_address \
  address="14 rue de la Paix, Paris"

# Rechercher un etablissement par son numero FINESS
ESANTE_API_KEY=votre_cle uv run fastmcp call \
  src/annuaire_mcp/main.py \
  --target get_establishment_by_finess \
  finess_id=750123456
```

Pour obtenir la reponse en JSON brut (utile pour deboguer ou scripter) :

```bash
ESANTE_API_KEY=votre_cle uv run fastmcp call \
  src/annuaire_mcp/main.py \
  --target search_establishments \
  --json \
  latitude=48.8566 longitude=2.3522 radius_km=5 category=EHPAD
```

---

### Inspecteur MCP interactif

FastMCP embarque le MCP Inspector, une interface web pour explorer les outils,
visualiser leurs schemas JSON et les appeler manuellement.

```bash
ESANTE_API_KEY=votre_cle uv run fastmcp dev inspector src/annuaire_mcp/main.py
```

L'URL `http://localhost:6274` s'ouvre automatiquement dans le navigateur.
On y trouve :

- la liste des outils avec leurs schemas de parametres
- un formulaire pour appeler chaque outil
- la reponse brute et formatee

---

### Via Docker en local

```bash
docker compose up --build
```

Pour envoyer une commande au conteneur depuis un autre terminal :

```bash
docker run -it --rm --env-file .env annuaire-mcp:latest
```

---

## Integration avec un LLM dans le cloud

### Cas A — Claude Desktop (client local, modele distant)

Claude Desktop tourne sur votre machine et se connecte au modele Claude via
l'API Anthropic. Le serveur MCP tourne aussi en local via stdio. C'est la
methode la plus simple pour un usage quotidien.

**Installation automatique :**

```bash
ESANTE_API_KEY=votre_cle uv run fastmcp install claude-desktop \
  src/annuaire_mcp/main.py \
  --name "annuaire-sante"
```

**Installation manuelle :**

Editer le fichier de configuration de Claude Desktop :

- macOS : `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows : `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "annuaire-sante": {
      "command": "uv",
      "args": [
        "--directory", "/chemin/absolu/vers/fastmcp-annuaire-gouv",
        "run", "python", "-m", "annuaire_mcp.main"
      ],
      "env": {
        "ESANTE_API_KEY": "votre_cle_ici"
      }
    }
  }
}
```

Redemarrer Claude Desktop. Le serveur apparait dans la liste des outils (icone
marteau). Exemples de requetes :

> "Trouve-moi tous les EHPAD dans un rayon de 10 km autour de Lyon."
>
> "Quels IME se trouvent a moins de 20 km de Bordeaux (44.8378, -0.5792) ?"
>
> "Donne-moi les informations sur l'etablissement FINESS 750123456."

---

### Cas B — Claude Code

```bash
ESANTE_API_KEY=votre_cle uv run fastmcp install claude-code \
  src/annuaire_mcp/main.py \
  --name "annuaire-sante"
```

Ou depuis Claude Code, utiliser la commande `/mcp` pour ajouter le serveur
manuellement avec la configuration stdio.

---

### Cas C — Cursor

```bash
ESANTE_API_KEY=votre_cle uv run fastmcp install cursor \
  src/annuaire_mcp/main.py \
  --name "annuaire-sante"
```

---

### Cas D — LM Studio (LLM local)

LM Studio permet de faire tourner un LLM en local (Llama, Mistral, Qwen, etc.)
et expose une API compatible OpenAI. Les versions recentes supportent le
protocole MCP via stdio, ce qui permet de brancher le serveur directement.

#### Etape 1 — Installer LM Studio

Telecharger LM Studio depuis https://lmstudio.ai et l'installer.
Choisir un modele avec une fenetre de contexte suffisamment grande (recommande :
32 k tokens minimum) et de bonnes capacites d'appel d'outils (tool use),
par exemple :

- `Qwen2.5-72B-Instruct` (GGUF Q4)
- `Mistral-Small-3.1-24B-Instruct-2503` (GGUF Q4)
- `Meta-Llama-3.3-70B-Instruct` (GGUF Q4)

#### Etape 2 — Activer le support MCP dans LM Studio

Dans LM Studio :

1. Aller dans **Settings > Developer**.
2. Activer **"Enable MCP support"**.
3. Cliquer sur **"Edit MCP config"** — cela ouvre un fichier JSON.

#### Etape 3 — Ajouter le serveur MCP

```json
{
  "mcpServers": {
    "annuaire-sante": {
      "command": "uv",
      "args": [
        "--directory", "/chemin/absolu/vers/fastmcp-annuaire-gouv",
        "run", "python", "-m", "annuaire_mcp.main"
      ],
      "env": {
        "ESANTE_API_KEY": "votre_cle_ici"
      }
    }
  }
}
```

Remplacer `/chemin/absolu/vers/fastmcp-annuaire-gouv` par le chemin reel,
par exemple `/home/alice/fastmcp-annuaire-gouv`.

#### Etape 4 — Tester

Redemarrer LM Studio. Dans le chat, selectionner le modele charge puis poser
une question qui necessite les outils :

> "Trouve-moi les EHPAD a moins de 5 km de Paris (48.8566, 2.3522)."

Le modele doit automatiquement appeler `search_establishments` et afficher
les resultats.

#### Conseils

- Certains modeles ne gerent pas bien le tool use avec des schemas complexes.
  Si le modele n'appelle pas les outils, essayer un modele plus grand ou
  mieux instruction-tune.
- LM Studio 0.3.x et superieur sont requis pour le support MCP.
- Surveiller les logs dans **Developer > MCP logs** en cas de probleme de
  connexion avec le serveur.

---

### Cas E — Claude.ai cloud via HTTP

Claude.ai (abonnement Pro ou Team) peut se connecter a un serveur MCP distant
via HTTP. Cela necessite d'exposer le serveur sur une URL publique.

#### Etape 1 — Activer le transport HTTP

Modifier `src/annuaire_mcp/main.py` pour supporter les deux transports :

```python
import os

def run() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))

    if transport == "http":
        mcp.run(transport="http", host=host, port=port)
    else:
        mcp.run()
```

Ajouter dans `.env` :

```bash
MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=8000
```

Demarrer le serveur :

```bash
uv run python -m annuaire_mcp.main
```

#### Etape 2 — Exposer le serveur publiquement (pour le developpement)

Avec Cloudflare Tunnel (gratuit, sans compte) :

```bash
cloudflared tunnel --url http://localhost:8000
# Retourne une URL du type : https://abc123.trycloudflare.com
```

Avec ngrok :

```bash
ngrok http 8000
# Retourne une URL du type : https://abc123.ngrok-free.app
```

#### Etape 3 — Ajouter le serveur dans Claude.ai

- Aller dans Parametres > Integrations > Ajouter un serveur MCP
- URL : `https://abc123.trycloudflare.com/mcp/`

#### Deploiement en production avec Docker

Pour une exposition permanente, lancer le conteneur avec le transport HTTP et
placer un reverse proxy (Caddy, Traefik, nginx) devant.

Exemple avec Caddy (`Caddyfile`) :

```
mcp.mondomaine.fr {
    reverse_proxy annuaire-mcp:8000
}
```

`docker-compose.yml` adapte :

```yaml
services:
  annuaire-mcp:
    image: ghcr.io/<owner>/fastmcp-annuaire-gouv:latest
    env_file: .env
    environment:
      MCP_TRANSPORT: http
      MCP_HOST: 0.0.0.0
      MCP_PORT: "8000"
    expose:
      - "8000"

  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data

volumes:
  caddy_data:
```

---

## Recap des methodes

| Methode | Cle API reelle | Complexite | Cas d'usage |
|---|---|---|---|
| `pytest` | Non | Minimale | CI, TDD, regression |
| `fastmcp call` | Oui | Minimale | Smoke test rapide en CLI |
| `fastmcp dev inspector` | Oui | Faible | Debug interactif, exploration |
| Claude Desktop (stdio) | Oui | Faible | Usage quotidien avec Claude |
| Claude Code | Oui | Faible | Usage en terminal |
| LM Studio (stdio local) | Oui | Faible | LLM open-source en local |
| Claude.ai + tunnel HTTP | Oui | Moyenne | Demo, test depuis le cloud |
| Docker + reverse proxy | Oui | Elevee | Production |
