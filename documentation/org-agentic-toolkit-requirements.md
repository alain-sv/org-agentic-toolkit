# Org Agentic Toolkit (OAT) – Requirements

> Scope: governance infrastructure that compiles and validates **organization-level agent rules** for all projects in an org.  
> This toolkit is designed to live **inside an org root**, be used by **all repos in that org**, and be **clonable** to bootstrap other orgs.

---

## 1. Purpose

The Org Agentic Toolkit defines, compiles, and distributes the **authoritative agent rules** for all projects within an organization.

Goals:
- Enforce a **single org-wide agentic constitution**
- Ensure every project **inherits org rules by construction**
- Allow **optional personal overlays** without weakening org authority
- Produce **deterministic, auditable agent instructions**
- Be **clonable and reusable** across organizations

Non-goals:
- Executing agents / running LLM calls
- Workflow orchestration (n8n, queues, etc.)
- Prompt experimentation playgrounds

---

## 2. Core Concepts

### 2.1 Organization Constitution (Mandatory)
- Canonical set of rules governing all agents in the org.
- Stored at a stable path inside the org root.
- Versioned (SemVer).
- Required for every project.

### 2.2 Project Declaration (Mandatory)
- Each project repo must explicitly declare how to locate the org root.
- Missing declaration is a **hard error**.

### 2.3 Personal Overlay (Optional)
- Developer-specific preferences and red lines.
- May be absent.
- Lowest precedence and must not weaken org constraints (enforced by linting over time).

---

## 3. Repo Skeleton

### 3.1 Org Root Layout (Required)

The org root directory name follows the pattern `$ORGNAME-agentic-toolkit`, where `$ORGNAME` is configurable via an environment variable.

**Environment Variables:**
- `ORG_AGENTIC_TOOLKIT_ROOT_NAME`: Controls the org root directory naming pattern. Defaults to `$ORGNAME-agentic-toolkit` if `ORGNAME` is set, otherwise uses the literal directory name. The toolkit should respect this variable when resolving or initializing org roots.

```
$ORG_AGENTIC_TOOLKIT_ROOT_NAME/
  .agent/
    constitution/
      manifest.yaml
      00-security.md
      10-compliance.md
      20-engineering.md
    toolkit/
      README.md
      oat                     # CLI entry (wrapper)
      oat.py                  # implementation (reference)
      schemas/
        manifest.schema.json
        inherits.schema.json
      templates/
        project/.agent/
          inherits.yaml
          project.md
      tests/
        test_compile.py
        test_validate.py
  repos/
    <project-a>/
    <project-b>/
```

Rules:
- Constitution MUST live in `.agent/constitution/`.
- Toolkit MUST live in `.agent/toolkit/`.
- Toolkit must not depend on repo names or paths outside `<org-root>`.
- Org root naming pattern is configurable via `ORG_AGENTIC_TOOLKIT_ROOT_NAME` environment variable.

### 3.2 Constitution Manifest (Required)

`<org-root>/.agent/constitution/manifest.yaml`

```yaml
name: supervaize
version: 1.3.0
include:
  - 00-security.md
  - 10-compliance.md
  - 20-engineering.md
```

Requirements:
- Explicit ordering; no globbing.
- Every listed file must exist and be readable.
- `version` must follow SemVer (`MAJOR.MINOR.PATCH`).

### 3.3 Project Contract (Required)

Every project repo MUST contain:

```
<repo>/
  .agent/
    inherits.yaml
    project.md
```

`.agent/inherits.yaml` (required):

```yaml
org_root: ../..
```

Rules:
- `org_root` MUST be a **relative path** from repo root to org root.
- Absolute paths are forbidden.
- Missing `.agent/inherits.yaml` is a hard failure.

`.agent/project.md` (required):
- Markdown file containing only the project delta (terminology, local constraints, exceptions with explicit rationale).

### 3.4 Personal Overlay (Optional)

If present, developers may maintain:

```
<personal-folder>/
  personal/
    manifest.yaml
    00-redlines.md
    10-style.md
    20-defaults.md
  registry.yaml   # optional pointer map for convenience
```

**Environment Variables:**
- `AGENT_PERSONAL_FOLDER`: Path to the personal overlay directory. Defaults to `~/.agent` if not set. The toolkit must respect this variable when resolving personal overlay paths.

`<personal-folder>/personal/manifest.yaml`:

```yaml
name: personal
version: 1.0.0
include:
  - 00-redlines.md
  - 10-style.md
  - 20-defaults.md
```

Notes:
- Personal overlay is OPTIONAL. If absent, compilation still works.
- Personal overlay is never referenced from repos (no home-paths in git).
- Personal folder path is configurable via `AGENT_PERSONAL_FOLDER` environment variable (default: `~/.agent`).

---

## 4. Toolkit CLI (Required)

### 4.1 Command name
The toolkit CLI command is `oat`.

It must support:
- Running from **any directory inside a project repo**
- Running from repo root
- Running with explicit `--repo <path>`

### 4.2 Global CLI conventions
- Exit code `0` on success; non-zero on failure.
- All commands must support `--json` to output machine-readable results.
- All commands must support `--quiet` to suppress non-errors.
- All commands must support `--version`.

### 4.3 Commands

#### 4.3.1 `oat compile`
**Purpose:** Produce the authoritative, merged instruction document for the current repo.

Inputs:
- Org constitution (mandatory)
- Project rules (mandatory)
- Personal overlay (optional)

Behavior:
- Resolve repo root (walk up from CWD until `.git/` or `.agent/inherits.yaml` found).
- Load `.agent/inherits.yaml`, resolve `org_root`.
- Load `<org-root>/.agent/constitution/manifest.yaml` and included files in order.
- Load `<repo>/.agent/project.md`.
- If `<personal-folder>/personal/manifest.yaml` exists (where `<personal-folder>` is `$AGENT_PERSONAL_FOLDER` or `~/.agent` by default), load it and append.

Output:
- Write a single Markdown document (default: `<repo>/.agent/AGENTS.compiled.md`).
- Include headers that clearly indicate sources and versions.

Flags:
- `--out <path>`: override output path
- `--no-personal`: ignore personal overlay even if present
- `--print`: print compiled content to stdout (still validates)
- `--hash`: print content hash (and optionally embed it in output header)
- `--strict`: treat missing `project.md` as error (default: strict)

Example:
- `oat compile`
- `oat compile --out ~/AGENTS.compiled.md --hash`
- `oat compile --no-personal --print`

#### 4.3.2 `oat validate`
**Purpose:** Validate constitution + project wiring without compiling output.

Checks (minimum):
- `.agent/inherits.yaml` exists and is valid
- `org_root` resolves and contains `.agent/constitution/manifest.yaml`
- Constitution manifest is valid (name, version, include list)
- All included files exist and are readable
- `.agent/project.md` exists (or warn depending on mode)
- No forbidden constructs:
  - Absolute paths in inherits
  - Manifest includes outside constitution dir

Flags:
- `--repo <path>`: validate another repo
- `--strict`: fail on warnings
- `--json`: output structured report

Example:
- `oat validate`
- `oat validate --strict --json`

#### 4.3.3 `oat doctor`
**Purpose:** Explain what rules apply here and why (debugging / onboarding).

Outputs (human-readable by default):
- Repo root detected
- Org root resolved
- Constitution name/version
- Included constitution files (in order)
- Project rules file path
- Personal overlay detected (yes/no)
- Effective compile order

Flags:
- `--json` for structured output

Example:
- `oat doctor`

#### 4.3.4 `oat init project`
**Purpose:** Scaffold `.agent/` in a repo to make it compliant.

Behavior:
- Create `<repo>/.agent/inherits.yaml` with a best-effort computed relative `org_root`
- Create `<repo>/.agent/project.md` with template sections
- Refuse to overwrite existing files unless `--force`

Flags:
- `--org-root <path>`: explicitly provide org root
- `--force`: overwrite

Example:
- `oat init project --org-root ../..`

---

## 5. Compile Semantics (Normative)

### 5.1 Order of precedence in compiled output
The compiled document MUST be ordered as:

1) **Org Constitution** (mandatory, highest authority)  
2) **Project Rules**  
3) **Personal Overlay** (optional, lowest authority)

### 5.2 Determinism
- Same inputs produce the same output byte-for-byte.
- Ordering comes only from manifests, never filesystem enumeration.

### 5.3 Traceability
Compiled output MUST include:
- Constitution name + version
- List of included constitution files (in order)
- Repo name/path
- Timestamp optional (if included, must be clearly marked as non-deterministic metadata)
- Content hash (recommended)

---

## 6. Validation Rules (Phase 1)

Minimum enforcement:
- Missing `.agent/inherits.yaml` => error
- Org constitution manifest missing => error
- Any included constitution file missing => error
- Personal overlay missing => not an error
- Project rules missing => error (strict default)

---

## 7. Portability & Cloning

The toolkit must:
- Work on macOS and Linux
- Require no hardcoded usernames or absolute paths in repos
- Avoid dependencies on a specific LLM vendor or IDE
- Be clonable: copy the `.agent/` tree to a new org and edit constitution files + manifest

---

## 8. Security & Trust Boundaries

- Toolkit must not execute project code.
- Toolkit must not fetch remote content.
- Toolkit must not modify anything outside its outputs unless explicitly requested (`oat init`).
- Org constitution is the trust anchor. Project rules are subordinate. Personal overlay is optional and lowest precedence.

---

## 9. Acceptance Criteria

- AC1: Running `oat compile` in any compliant repo produces a merged markdown file containing the org constitution and project rules, and optionally personal overlay.
- AC2: `oat validate` fails if `.agent/inherits.yaml` is missing or `org_root` cannot be resolved.
- AC3: `oat doctor` clearly prints the resolved org root and the list of constitution files in order.
- AC4: Projects remain portable: cloning the org directory elsewhere does not break `org_root` resolution (relative paths).
- AC5: Toolkit can be copied to a new org root and works after updating constitution manifest + files.

---

## 10. Templates

### 10.1 `project.md` template (recommended)
- Project overview (1–2 paragraphs)
- Local glossary / terminology
- Data sensitivity notes
- Allowed / forbidden actions specific to project
- Exceptions to org defaults (must include rationale + ticket reference)

---

## 11. Future Enhancements (Not required for v1)
- Rule IDs + conflict linting (e.g. deny project files containing “OVERRIDE” without explicit allowlist)
- Signing / checksum enforcement for constitution
- Pre-commit hook integration
- CI job that runs `oat validate` across all repos in the org
