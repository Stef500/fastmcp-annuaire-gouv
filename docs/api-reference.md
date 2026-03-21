# API reference

## MCP tools

### `list_establishment_categories`

Returns the complete list of supported establishment categories.

**Parameters:** none

**Returns:** a mapping of category keys to their code and French label.

```json
{
  "EHPAD": { "code": "500", "label": "Etablissement d'Hebergement pour Personnes Agees Dependantes" },
  "IME":   { "code": "182", "label": "Institut Medico-Educatif" },
  ...
}
```

---

### `search_establishments`

Search for health establishments near a geographic point.

> **Note — geographic approximation**: the ANS FHIR v2 API does not support
> radius-based (`_near`) search on `Organization` resources. Geographic
> filtering is approximated using a reverse-geocoded postal code:
>
> | `radius_km` | Search scope |
> |---|---|
> | ≤ 10 km | exact postal code (commune / arrondissement) |
> | > 10 km | department prefix (e.g. `75` for all Paris) |
>
> If the exact postal code returns 0 results, the tool automatically widens
> the search to the department prefix.

**Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `latitude` | float | yes | - | WGS-84 latitude of the center point |
| `longitude` | float | yes | - | WGS-84 longitude of the center point |
| `radius_km` | float | yes | - | Approximate radius — controls postal granularity (see note above) |
| `category` | string | yes | - | Category key, e.g. `"EHPAD"` |
| `max_results` | int | no | 20 | Maximum results to return (capped at `MAX_RESULTS`) |
| `active_only` | bool | no | true | Return only active establishments |

**Returns:** `SearchResult`

```json
{
  "total": 42,
  "count": 20,
  "establishments": [
    {
      "finess_id": "750123456",
      "name": "EHPAD Les Pins",
      "category_code": "500",
      "category_label": "Etablissement d'Hebergement pour Personnes Agees Dependantes",
      "active": true,
      "address": {
        "line": ["10 rue des Pins"],
        "city": "Paris",
        "postal_code": "75001",
        "country": "FR"
      },
      "telecoms": [{ "system": "phone", "value": "0101020304", "use": "work" }],
      "latitude": 48.8566,
      "longitude": 2.3522
    }
  ]
}
```

---

### `get_establishment_by_finess`

Retrieve a single establishment by its FINESS number.

**Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `finess_id` | string | yes | 9-digit FINESS geographic entity identifier |

**Returns:** An `Establishment` object, or `{"error": "..."}` if not found.

---

## Category codes (TRE-R66-CategorieEtablissement)

| Key | Code | Label |
|---|---|---|
| `EHPAD` | 500 | Etablissement d'Hebergement pour Personnes Agees Dependantes |
| `RESIDENCE_AUTONOMIE` | 202 | Residence Autonomie |
| `EEAP` | 183 | Etablissement pour Enfants et Adolescents Polyhandicapes |
| `IME` | 182 | Institut Medico-Educatif |
| `MAS` | 437 | Maison d'Accueil Specialisee |
| `SSIAD` | 460 | Service de Soins Infirmiers A Domicile |
| `CSAPA` | 604 | Centre de Soins d'Accompagnement et de Prevention en Addictologie |
| `CAMSP` | 189 | Centre d'Action Medico-Sociale Precoce |
| `CMPP` | 190 | Centre Medico-Psycho-Pedagogique |
| `ESAT` | 249 | Etablissement et Service d'Aide par le Travail |
| `FOYER_VIE` | 252 | Foyer de Vie / Foyer Occupationnel |
| `FOYER_HEBERGEMENT` | 253 | Foyer d'Hebergement pour Adultes Handicapes |
| `SAVS` | 445 | Service d'Accompagnement a la Vie Sociale |
| `SAMSAH` | 446 | Service d'Accompagnement Medico-Social pour Adultes Handicapes |
| `SESSAD` | 184 | Service d'Education Speciale et de Soins a Domicile |
| `FAM` | 255 | Foyer d'Accueil Medicalise pour Adultes Handicapes |

---

## Upstream API

The server wraps the **ANS FHIR v2 API**.

- Base URL: `https://gateway.api.esante.gouv.fr/fhir/v2`
- Resource used: `Organization`
- Auth header: `ESANTE-API-KEY`
- Geographic search: `address-postalcode=<code>` (prefix match — `_near` not supported by this API)
- Category filter: `type=<system>|<code>` (system: `TRE_R66-CategorieEtablissement`)

Official documentation: https://ansforge.github.io/annuaire-sante-fhir-documentation/
