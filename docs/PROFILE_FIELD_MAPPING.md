# Profile Field Mapping Specification: JSON/YAML to Relational Data Model

**Specification Version:** 1.0.0  
**Status:** Approved for Ingestion & Validation  
**Target Architecture:** PostgreSQL 16 / SQLAlchemy 2.x Foundation

---

## 1. Architectural Overview & Ingestion Strategy

The AI Resume Builder platform manages candidate profiles stored on disk across three primary file formats:
1. `registry.json`: Global catalog of candidate profiles, active statuses, and schema versions.
2. `master_profile.json`: Core candidate demographics, education, skills, experience, achievements, and certifications.
3. `projects.json`: Array of verified projects with metrics, bullet points, links, and fixed-position rules.
4. `profile_config.yaml`: Tailoring rules, headline/summary rules, prohibited terms, and project selection weights.

The target relational schema decomposes these files into 8 normalized tables with foreign keys and cascade rules:
- `candidate_profiles`
- `educations`
- `experiences`
- `skills`
- `projects`
- `certifications`
- `achievements`
- `professional_developments`

---

## 2. Comprehensive Field Mapping Matrix

### 2.1 `candidate_profiles` Table
**Source Files:** `master_profile.json`, `profile_config.yaml`, `registry.json`

| Source File | Source Field | Destination Column | Data Type Conversion | Default / Normalization Rule | Optional? | Special Handling |
|---|---|---|---|---|---|---|
| `registry.json` / Directory | `profile_id` | `slug` | `VARCHAR(100)` | Unique constraint; lowercased, validated regex `^[a-z0-9_-]+$` | No | Natural identifier matching folder name |
| `master_profile.json` | `personal_info.full_name` | `full_name` | `VARCHAR(255)` | Strip leading/trailing whitespace | No | Primary candidate name |
| `master_profile.json` | `personal_info.display_name` | `display_name` | `VARCHAR(255)` | Fallback to `full_name` if missing | No | Header presentation name |
| `master_profile.json` | `personal_info.email` | `email` | `VARCHAR(255)` | Lowercased, stripped whitespace | Yes | Sanitized during AI transmission |
| `master_profile.json` | `personal_info.phone` | `phone` | `VARCHAR(100)` | Stripped whitespace | Yes | Sanitized during AI transmission |
| `master_profile.json` | `personal_info.location` | `location` | `VARCHAR(255)` | Stripped whitespace | Yes | Geographic location |
| `master_profile.json` | `personal_info.open_to_relocate` | `open_to_relocate` | `BOOLEAN` | Coerce to boolean; default `True` | No | Availability flag |
| `master_profile.json` | `personal_info.immediate_joiner` | `immediate_joiner` | `BOOLEAN` | Coerce to boolean; default `True` | No | Availability flag |
| `profile_config.yaml` | `headline_rule.permanent_headline` | `professional_headline` | `VARCHAR(500)` | Fallback to first headline in `headlines` | Yes | Active resume headline |
| `profile_config.yaml` | `summary_rule.permanent_summary` | `professional_summary` | `TEXT` | Fallback to `summaries["general"]` or `summaries["master"]` | Yes | Active resume summary |
| `master_profile.json` | `headlines` | `headlines` | `JSONB` / `JSON` | Dict mapping mode to headline string | No | Retains multiple candidate headlines |
| `master_profile.json` | `summaries` | `summaries` | `JSONB` / `JSON` | Dict mapping variant to summary text | No | Retains multiple candidate summaries |
| `master_profile.json` | `links` | `links` | `JSONB` / `JSON` | Dict of `{linkedin, github, portfolio}` with `url` and `display` | No | Structured candidate web links |
| `profile_config.yaml` + `master_profile.json` | Combined configurations | `config_rules` | `JSONB` / `JSON` | Stores `prohibited_terms`, `project_selection`, `sections_order`, `theme`, `research_publications`, `reconciliation_metadata`, and `_notice` | No | **Full preservation of non-relational configurations & research data** |
| `profile_config.yaml` | `is_synthetic` | `is_synthetic` | `BOOLEAN` | Coerce to boolean; default `False` | No | Distinguishes demo candidate from real data |

---

### 2.2 `educations` Table
**Source File:** `master_profile.json` -> `education` (array)

| Source Field | Destination Column | Data Type Conversion | Default / Normalization Rule | Optional? | Special Handling |
|---|---|---|---|---|---|
| (Generated) | `id` | `UUID` | UUID v4 | No | Primary key |
| (Parent) | `profile_id` | `UUID` | Foreign Key to `candidate_profiles.id` | No | `ON DELETE CASCADE` |
| `degree` | `degree` | `VARCHAR(255)` | Stripped whitespace | No | Academic degree name |
| `institution` | `institution` | `VARCHAR(255)` | Stripped whitespace | No | College / University name |
| `duration` | `duration` | `VARCHAR(100)` | Normalize dash characters (`–` to `-`) | Yes | Display duration |
| `start_year` | `start_year` | `INTEGER` | Integer conversion | Yes | Chronological sorting |
| `end_year` | `end_year` | `INTEGER` | Integer conversion | Yes | Graduation year |
| `cgpa` | `cgpa` | `VARCHAR(50)` | Normalize e.g. "8.23 / 10" or "8.50/10" | Yes | Direct display string |
| `score` | `score` | `VARCHAR(50)` | Numeric string | Yes | Score component |
| `scale` | `scale` | `VARCHAR(50)` | Numeric string (e.g. "10") | Yes | Grading scale |
| `source` | `source` | `VARCHAR(100)` | Default `"verified_both"` | No | Verification provenance |
| (List Index) | `display_order` | `INTEGER` | 0-indexed position in array | No | Ordering in resume |

---

### 2.3 `experiences` Table
**Source File:** `master_profile.json` -> `leadership_and_experience` (array)

| Source Field | Destination Column | Data Type Conversion | Default / Normalization Rule | Optional? | Special Handling |
|---|---|---|---|---|---|
| (Generated) | `id` | `UUID` | UUID v4 | No | Primary key |
| (Parent) | `profile_id` | `UUID` | Foreign Key to `candidate_profiles.id` | No | `ON DELETE CASCADE` |
| `role` | `role` | `VARCHAR(255)` | Stripped whitespace | No | Job title / leadership position |
| `organization` | `organization` | `VARCHAR(255)` | Stripped whitespace | No | Company / Institution |
| `duration` | `duration` | `VARCHAR(100)` | Normalize dashes | Yes | Experience timeframe |
| `metrics` | `metrics` | `VARCHAR(255)` | Stripped whitespace | Yes | High-level impact metric |
| `description` | `description` | `TEXT` | Stripped whitespace | Yes | Narrative description |
| `bullets` | `bullets` | `JSONB` / `JSON` | List of string achievement bullets | No | Core resume bullet points |
| `source` | `source` | `VARCHAR(100)` | Default `"verified_both"` | No | Provenance marker |
| (List Index) | `display_order` | `INTEGER` | 0-indexed position in array | No | Section ordering |
| `id` | (Preserved in config_rules) | — | Stored in `config_rules["source_entity_ids"]["experiences"]` | Yes | Source slug e.g. `"cstpo_placement"` |

---

### 2.4 `skills` Table
**Source File:** `master_profile.json` -> `technical_skills` (object with 7 category arrays)

| Source Field | Destination Column | Data Type Conversion | Default / Normalization Rule | Optional? | Special Handling |
|---|---|---|---|---|---|
| (Generated) | `id` | `UUID` | UUID v4 | No | Primary key |
| (Parent) | `profile_id` | `UUID` | Foreign Key to `candidate_profiles.id` | No | `ON DELETE CASCADE` |
| Category Key | `category` | `VARCHAR(100)` | Standard 7 categories (`languages`, `backend_and_java`, etc.) | No | Indexed column |
| Array Element | `skill_name` | `VARCHAR(100)` | Stripped whitespace | No | Canonical skill term |
| Element Index | `display_order` | `INTEGER` | 0-indexed position in category list | No | Rendering order |

---

### 2.5 `projects` Table
**Source File:** `projects.json` (array of objects)

| Source Field | Destination Column | Data Type Conversion | Default / Normalization Rule | Optional? | Special Handling |
|---|---|---|---|---|---|
| (Generated) | `id` | `UUID` | UUID v4 | No | Primary key |
| (Parent) | `profile_id` | `UUID` | Foreign Key to `candidate_profiles.id` | No | `ON DELETE CASCADE` |
| `id` | `slug` | `VARCHAR(100)` | Validated project slug (e.g. `bearing_fault_diagnosis`) | No | Indexed; must match `fixed_project.id` |
| `title` | `title` | `VARCHAR(255)` | Stripped whitespace | No | Project heading |
| `subtitle` | `subtitle` | `VARCHAR(255)` | Tech stack summary line | Yes | Displayed in resume header |
| `notice` | `notice` | `VARCHAR(500)` | Synthetic/demonstration disclaimer | Yes | Synthetic notice |
| `is_fixed_project` | `is_fixed_project` | `BOOLEAN` | Default `False` | No | Safeguard pinning flag |
| `fixed_position` | `fixed_position` | `INTEGER` | e.g. `2` for position 2 safeguard | Yes | 1-indexed target position |
| (Array Index) | `display_order` | `INTEGER` | 0-indexed position in file | No | Default candidate preference |
| `categories` | `categories` | `JSONB` / `JSON` | List of string domain categories | No | Used for matching algorithms |
| `skills` | `skills` | `JSONB` / `JSON` | List of specific technical skills | No | Used for JD keyword overlap |
| `links` | `links` | `JSONB` / `JSON` | List of `{label: str, url: str}` | No | Rendered as active hyperlinks |
| `bullets` | `bullets` | `JSONB` / `JSON` | List of achievement statements | No | Main resume bullets |
| `metrics` | `metrics` | `JSONB` / `JSON` | List of quantified outcome strings | No | Highlighted metrics |
| `evidence_source` | `evidence_source` | `TEXT` | File name or verification code | Yes | Verification trail |
| `verification_status` | `verification_status`| `VARCHAR(50)` | Default `"verified"` | No | Integrity status |

---

### 2.6 `certifications` Table
**Source File:** `master_profile.json` -> `certifications` (array of strings)

| Source Field | Destination Column | Data Type Conversion | Default / Normalization Rule | Optional? | Special Handling |
|---|---|---|---|---|---|
| (Generated) | `id` | `UUID` | UUID v4 | No | Primary key |
| (Parent) | `profile_id` | `UUID` | Foreign Key to `candidate_profiles.id` | No | `ON DELETE CASCADE` |
| Array String | `name` | `VARCHAR(255)` | Stripped whitespace (e.g. full certification title) | No | Direct certification title |
| Parsed Issuer | `issuer` | `VARCHAR(255)` | Extracted if `"Issuer: Name"` pattern exists; else `None` | Yes | Optional metadata |
| Parsed Date | `issue_date` | `VARCHAR(100)` | Extracted if year/date pattern found; else `None` | Yes | Optional metadata |
| Array Index | `display_order` | `INTEGER` | 0-indexed position in list | No | Ordering in resume |

---

### 2.7 `achievements` Table
**Source File:** `master_profile.json` -> `achievements` (array)

| Source Field | Destination Column | Data Type Conversion | Default / Normalization Rule | Optional? | Special Handling |
|---|---|---|---|---|---|
| (Generated) | `id` | `UUID` | UUID v4 | No | Primary key |
| (Parent) | `profile_id` | `UUID` | Foreign Key to `candidate_profiles.id` | No | `ON DELETE CASCADE` |
| `title` | `title` | `VARCHAR(255)` | Stripped whitespace | No | Achievement heading |
| `description` | `description` | `TEXT` | Detailed context | Yes | Optional context |
| `bullets` | `bullets` | `JSONB` / `JSON` | List of accomplishment bullets | No | Resume bullets |
| `source` | `source` | `VARCHAR(100)` | Default `"verified_both"` | No | Provenance marker |
| (Array Index) | `display_order` | `INTEGER` | 0-indexed position | No | Ordering |
| `id` | (Preserved in config_rules) | — | Stored in `config_rules["source_entity_ids"]["achievements"]` | Yes | Source slug |

---

### 2.8 `professional_developments` Table
**Source File:** `master_profile.json` -> `professional_development` (array)

| Source Field | Destination Column | Data Type Conversion | Default / Normalization Rule | Optional? | Special Handling |
|---|---|---|---|---|---|
| (Generated) | `id` | `UUID` | UUID v4 | No | Primary key |
| (Parent) | `profile_id` | `UUID` | Foreign Key to `candidate_profiles.id` | No | `ON DELETE CASCADE` |
| `title` | `title` | `VARCHAR(255)` | Course or workshop name | No | Course title |
| `organization` | `organization` | `VARCHAR(255)` | Training provider / Platform | No | Provider |
| `date` | `date` | `VARCHAR(100)` | Stripped whitespace | Yes | Completion date |
| `bullets` | `bullets` | `JSONB` / `JSON` | List of key learnings | No | Learning bullets |
| `source` | `source` | `VARCHAR(100)` | Provenance PDF or marker | Yes | Source file |
| `conflict_note` | `conflict_note` | `TEXT` | Reconciliation documentation | Yes | Notes |
| (Array Index) | `display_order` | `INTEGER` | 0-indexed position | No | Ordering |
| `id` | (Preserved in config_rules) | — | Stored in `config_rules["source_entity_ids"]["professional_developments"]` | Yes | Source slug |

---

## 3. Preservation of Custom & Non-Relational Fields

To satisfy strict data preservation without losing any candidate information, fields that do not map to standard relational columns are systematically captured inside `candidate_profiles.config_rules`:

1. **`research_publications`:** Stored in `config_rules["research_publications"]` as an array of structured objects (`title`, `venue`, `year`, `doi`, `doi_url`).
2. **`reconciliation_metadata`:** Stored in `config_rules["reconciliation_metadata"]` containing `sources_inspected`, `reconciliation_date`, and `reconciled_conflicts`.
3. **`registry_entry`:** Stored in `config_rules["registry_entry"]` containing `source_status`, `is_active`, and `schema_version`.
4. **`_notice`:** Stored in `config_rules["_notice"]` for synthetic demonstration profiles.
5. **Entity ID slugs:** Source IDs on `experiences`, `achievements`, and `professional_developments` are preserved under `config_rules["source_entity_ids"]`.

---

## 4. Identified Schema Mismatches & Technical Resolutions

| Source Field / Nuance | Schema Nuance | Technical Resolution |
|---|---|---|
| String Certifications | `master_profile.json` stores certifications as strings (`List[str]`), while the DB table has `name`, `issuer`, `issue_date`. | The ingestion parser populates `certifications.name` with the full string, preserving 100% of the content while leaving optional `issuer`/`issue_date` nullable. |
| Research Publications | Present in `sujal/master_profile.json` (2 publications) but Milestone 2A has no `research_publications` table. | Encapsulated cleanly in `candidate_profiles.config_rules["research_publications"]` so no scientific publication metadata is dropped. |
| Component Entity String IDs | `leadership_and_experience[].id`, `achievements[].id`, and `professional_development[].id` have string slugs, while DB tables use UUID primary keys. | Relational tables use UUIDs for DB keys; original source slugs are preserved in `config_rules["source_entity_ids"]`. |
| Project Links | Project links in `projects.json` are objects with `label` and `url`. | Mapped to `projects.links` as JSONB array, allowing dynamic link counts with full label/URL fidelity. |
| Fixed Project Pinning Rules | Pinning rules reside both in `profile_config.yaml` (`fixed_project`) and `projects.json` (`is_fixed_project: true, fixed_position: 2`). | Validated for cross-file consistency during ingestion: `projects.is_fixed_project` and `fixed_position` are stored on the project, and the global selection rule is stored in `config_rules["project_selection"]`. |
