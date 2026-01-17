# Org Agentic Toolkit (OAT) – Updated Specification

> **Scope:** Governance infrastructure that compiles and validates **organization-level agent rules** for all projects in an org.  
> This toolkit lives inside an **org root**, is used by all **repos in that org**, and is **clonable** to bootstrap other orgs.

---

## 1. Purpose & Goals

The Org Agentic Toolkit (OAT) defines, compiles, and distributes the **authoritative agent rules** for all projects within an organization.

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

### 2.1 Conceptual Model

The toolkit organizes agent knowledge into three layers:

| Layer          | Purpose                            | Contains                                                     |
| -------------- | ---------------------------------- | ------------------------------------------------------------ |
| **Sub-Agents** | WHO does it + WHAT steps to follow | backend-developer, frontend-developer, tech-lead, qa, devops |
| **Skills**     | HOW to do atomic tasks             | git, test, db, review-checklist                              |
| **Memory**     | Context: rules and team knowledge  | constitution, general-context, teams/\*                       |

### 2.2 Organization Constitution (Mandatory)
- Canonical set of rules governing all agents in the org.
- Stored in `.agent/memory/constitution.md` inside the org root.
- Versioned (SemVer).
- Required for every project.

### 2.3 Project Declaration (Mandatory)
- Each project repo must explicitly declare how to locate the org root.
- Missing declaration is a **hard error**.

### 2.4 Personal Overlay (Optional)
- Developer-specific preferences and red lines.
- May be absent.
- Lowest precedence and must not weaken org constraints (enforced by linting over time).

### 2.5 The Inheritance Chain (Precedence)
The compiled document is ordered as follows, from highest to lowest authority:
1.  **Org Memory (Mandatory)**: Constitution, general-context, and team knowledge.
2.  **Org Skills (Mandatory)**: Reusable atomic knowledge modules.
3.  **Org Sub-Agents (Mandatory)**: Specialized personas and workflows.
4.  **Project Declaration (Mandatory)**: Project-specific context and terminology.
5.  **Personal Overlay (Optional)**: Developer-specific style or redlines.

### 2.6 Root Discovery
The toolkit uses a "walk-up" logic to find relevant paths:
* **Repo Root**: Found by walking up from the current working directory until a `.git/` directory or `.agent/inherits.yaml` file is located.
* **Org Root**: Resolved via the relative path in `.agent/inherits.yaml`. 
    * *Refinement*: If a `.oat-root` marker file exists, it serves as the definitive anchor for the toolkit.

---

## 3. Repo Skeleton

### 3.1 Org Root Layout (Required)

The org root directory name follows the pattern `$ORGNAME-agentic-toolkit`, where `$ORGNAME` is configurable via an environment variable.

**Environment Variables:**
- `OAT_ROOT`: Explicitly sets the Org Root path.
- `ORG_AGENTIC_TOOLKIT_ROOT_NAME`: Controls the org root directory naming pattern. Defaults to `$ORGNAME-agentic-toolkit` if `ORGNAME` is set, otherwise uses the literal directory name. The toolkit should respect this variable when resolving or initializing org roots.
- `AGENT_PERSONAL_FOLDER`: Path to the personal overlay directory. Defaults to `~/.agent` if not set. The toolkit must respect this variable when resolving personal overlay paths.

```
$ORG_AGENTIC_TOOLKIT_ROOT_NAME/
  .oat-root                       # Discovery marker
  AGENTS.md                        # Entry point — agents read this first
  .agent/
    memory/                        # Long-term context and governance
      constitution.md             # Immutable rules: tech stack, code standards
      general-context.md           # Shared context for ALL teams
      teams/                       # Team-specific domain knowledge
        _template.md               # Copy and rename for each team
        platform.md                # Example: platform team context
        product.md                 # Example: product team context
    skills/                        # Atomic knowledge modules (HOW-TO)
      git.md                       # Version control: commits, branches, conventions
      test.md                      # Testing: commands, coverage requirements
      db.md                        # Database: migrations, queries, safety rules
      review-checklist.md          # Code review: correctness, style, security
      python/                      # Language/stack specific skills
        django.md                 # Django framework patterns
        fastapi.md                # FastAPI patterns
        pytest.md                # Python testing with pytest
      javascript/                  # Language/stack specific skills
        react.md                  # React patterns and best practices
        nodejs.md                 # Node.js patterns
        jest.md                   # JavaScript testing with Jest
      typescript/                 # Language/stack specific skills
        angular.md                # Angular patterns
        nestjs.md                # NestJS patterns
      go/                         # Language/stack specific skills
        gin.md                    # Gin framework patterns
        testing.md                # Go testing patterns
      rust/                       # Language/stack specific skills
        cargo.md                  # Cargo and project structure
        testing.md                # Rust testing patterns
      java/                       # Language/stack specific skills
        spring.md                 # Spring framework patterns
        maven.md                  # Maven build patterns
    sub-agents/                    # Specialized personas (WHO + WHAT)
      backend-developer.md         # Backend: APIs, services, database logic
      frontend-developer.md        # Frontend: UI components, pages, client logic
      tech-lead.md                 # Reviews code: fetch → review → approve/reject
      qa.md                        # Tests & debugs: reproduce → isolate → fix → verify
      devops.md                    # Deploys: lint → build → test → ship
    toolkit/
      README.md
      oat                          # CLI entry (wrapper)
      oat.py                       # implementation (reference)
      targets.yaml                 # IDE target mappings (see Vendor Reference)
      schemas/
        manifest.schema.json
        inherits.schema.json
      templates/
        project/.agent/
          inherits.yaml
          project.md
          AGENTS.md                # Project entry point template
      tests/
        test_compile.py
        test_validate.py
  repos/
    <project-a>/
    <project-b>/
```

Rules:
- Memory (constitution, context, teams) MUST live in `.agent/memory/`.
- Skills MUST live in `.agent/skills/`.
- Sub-agents MUST live in `.agent/sub-agents/`.
- Toolkit MUST live in `.agent/toolkit/`.
- `AGENTS.md` serves as the entry point that agents read first.
- Toolkit must not depend on repo names or paths outside `<org-root>`.
- Org root naming pattern is configurable via `ORG_AGENTIC_TOOLKIT_ROOT_NAME` environment variable.

### 3.2 Memory Structure (Required)

**Constitution** (`<org-root>/.agent/memory/constitution.md`):
- Immutable rules: tech stack, code standards, security policies.
- Versioned (SemVer) via header comment or metadata.
- Required for every project.

**General Context** (`<org-root>/.agent/memory/general-context.md`):
- Shared context applicable to ALL teams.
- Optional but recommended for org-wide knowledge.

**Teams** (`<org-root>/.agent/memory/teams/`):
- Team-specific domain knowledge files.
- Each team has its own markdown file (e.g., `platform.md`, `product.md`).
- Teams are referenced by name in project declarations or sub-agent definitions.

**Memory Manifest** (`<org-root>/.agent/memory/manifest.yaml` - Optional):

```yaml
name: supervaize
version: 1.3.0
constitution: constitution.md
general-context: general-context.md
teams:
  - platform.md
  - product.md
```

Requirements:
- `constitution.md` must exist and be readable.
- `general-context.md` is optional.
- Team files are optional but must exist if listed in manifest.
- `version` must follow SemVer (`MAJOR.MINOR.PATCH`).
- If manifest is absent, toolkit assumes `constitution.md` exists and loads it.

### 3.3 Skills Structure (Required)

Skills are atomic knowledge modules stored in `<org-root>/.agent/skills/`:
- **Universal skills**: Markdown files directly in `skills/` (e.g., `git.md`, `test.md`, `db.md`).
  - Must be explicitly listed in project manifest to be included.
- **Language/stack specific skills**: Organized in subdirectories by language or stack (e.g., `python/`, `javascript/`, `typescript/`, `go/`, `rust/`, `java/`).
  - Only included when explicitly listed in project manifest `inherits.yaml` `skills.languages` section.
  - Each subdirectory contains markdown files for that language/stack (e.g., `python/django.md`, `javascript/react.md`).
- Skills define HOW to perform specific tasks.
- Skills are referenced by sub-agents and can be included in compiled output.
- **Critical**: Skills are NOT automatically discovered. Only skills explicitly listed in `<repo>/.agent/inherits.yaml` `skills` section are included in compilation.
- Project manifest must explicitly declare which universal and language-specific skills are relevant for that project.

### 3.4 Sub-Agents Structure (Required)

Sub-agents are specialized personas stored in `<org-root>/.agent/sub-agents/`:
- Each sub-agent is a markdown file (e.g., `backend-developer.md`, `tech-lead.md`).
- Sub-agents define WHO does it + WHAT steps to follow.
- Sub-agents can reference skills and team contexts.
- **Critical**: Sub-agents are NOT automatically discovered. Only sub-agents explicitly listed in `<repo>/.agent/inherits.yaml` `sub_agents` section are included in compilation.
- Project manifest must explicitly declare which sub-agents are relevant for that project.

### 3.5 Project Contract (Required)

Every project repo MUST contain:

```
<repo>/
  AGENTS.md                        # Entry point (agents read this first)
  .agent/
    inherits.yaml
    project.md
```

`AGENTS.md` (required):
- Entry point that agents read first.
- Should contain: `> CRITICAL: Read AGENTS.md first.` or similar directive.
- Can reference specific sub-agents, skills, or team contexts.
- Template provided by toolkit.

`.agent/inherits.yaml` (required):

```yaml
org_root: ../..
# Required: Explicitly declare which skills are relevant for this project
skills:
  universal:                  # Universal skills (apply to all projects)
    - git
    - test
    - db
    - review-checklist
  languages:                  # Language/stack specific skills
    python:
      - django
      - fastapi
      - pytest
    javascript:
      - react
      - nodejs
      - jest
# Required: Explicitly declare which sub-agents are relevant for this project
sub_agents:
  - backend-developer
  - frontend-developer
  - tech-lead
# Optional: Declare which teams are relevant (for team-specific memory)
teams:
  - platform
  - product
```

Rules:
- `org_root` MUST be a **relative path** from repo root to org root.
- Absolute paths are forbidden.
- Missing `.agent/inherits.yaml` is a hard failure.
- `skills` section is **required** and must explicitly list:
  - `universal`: List of universal skill names (without `.md` extension) from `skills/` root
  - `languages`: Map of language/stack names to lists of skill names (without `.md` extension) from `skills/<language>/`
- `sub_agents` section is **required** and must explicitly list sub-agent names (without `.md` extension) from `sub-agents/`
- `teams` section is optional and lists team names (without `.md` extension) from `memory/teams/`
- Only the specified skills, sub-agents, and teams are included in compilation.
- Skill and sub-agent names must match existing files (validation will fail if they don't exist).

`.agent/project.md` (required):
- Markdown file containing only the project delta (terminology, local constraints, exceptions with explicit rationale).

### 3.6 Personal Overlay (Optional)

If present, developers may maintain:

```
<personal-folder>/
  .agent/
    memory/
      personal-context.md
    skills/
      personal-git.md              # Personal git preferences
    sub-agents/
      me.md                        # User identity: team membership (gitignored)
```

`<personal-folder>/.agent/sub-agents/me.md` (optional):
- Declares developer's team membership and personal preferences.
- Format: `team: [TEAM_NAME]`
- This file is gitignored and never committed.

Notes:
- Personal overlay is OPTIONAL. If absent, compilation still works.
- Personal overlay is never referenced from repos (no home-paths in git).
- Personal folder path is configurable via `AGENT_PERSONAL_FOLDER` environment variable (default: `~/.agent`).
- Personal overlay follows the same structure as org root (memory/, skills/, sub-agents/).

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
- Org memory (constitution, general-context, teams) (mandatory)
- Org skills (mandatory)
- Org sub-agents (mandatory)
- Project rules (mandatory)
- Personal overlay (optional)

Behavior:
- Resolve repo root (walk up from CWD until `.git/` or `.agent/inherits.yaml` found).
- Load `<repo>/AGENTS.md` as entry point (if exists, otherwise use default).
- Load `.agent/inherits.yaml`, resolve `org_root`.
- Validate that all specified skills and sub-agents exist (fail if any are missing).
- Load `<org-root>/.agent/memory/constitution.md` (required).
- Load `<org-root>/.agent/memory/general-context.md` (if exists).
- Load team files from `<org-root>/.agent/memory/teams/`:
  - Only load teams specified in `inherits.yaml` `teams` field (if present).
  - If `teams` not specified, load based on personal context from `me.md` (if available).
- Load universal skills:
  - Only load skills specified in `inherits.yaml` `skills.universal` list.
  - Load from `<org-root>/.agent/skills/<skill-name>.md` in the order specified.
- Load language/stack specific skills:
  - For each language/stack in `inherits.yaml` `skills.languages`, load only the specified skills.
  - Load from `<org-root>/.agent/skills/<language>/<skill-name>.md` in the order specified.
- Load sub-agents:
  - Only load sub-agents specified in `inherits.yaml` `sub_agents` list.
  - Load from `<org-root>/.agent/sub-agents/<sub-agent-name>.md` in the order specified.
- Load `<repo>/.agent/project.md`.
- If `<personal-folder>/.agent/` exists (where `<personal-folder>` is `$AGENT_PERSONAL_FOLDER` or `~/.agent` by default):
  - Load personal memory, skills, and sub-agents (if present).
  - Load `<personal-folder>/.agent/sub-agents/me.md` to determine team context.
  - Personal overlay skills/sub-agents are appended if present.

Output:
- Write a single Markdown document (default: `<repo>/AGENTS.compiled.md` or target-specific file).
- Include headers that clearly indicate sources and versions.
- If `--target <name>` is provided, the output is written to the filename defined in `targets.yaml`.

Governance:
- Throws an error if a Project file attempts to modify a section in the Org Constitution marked with immutable markers.

Flags:
- `--out <path>`: override output path
- `--target <name>`: Compile for a specific IDE/Agent (e.g., `cursor`, `windsurf`). Output is written to the filename defined in `targets.yaml`.
- `--watch`: Re-compile automatically when source files change.
- `--no-personal`: ignore personal overlay even if present
- `--print`: print compiled content to stdout (still validates)
- `--hash`: print content hash (and optionally embed it in output header)
- `--diff`: Show what changed since the last compilation.
- `--strict`: treat missing `project.md` as error (default: strict)
- `--include-skill <name>`: Additionally include a skill not in manifest (e.g., `--include-skill git`)
- `--include-sub-agent <name>`: Additionally include a sub-agent not in manifest (e.g., `--include-sub-agent qa`)
- `--exclude-skill <name>`: Exclude a skill from manifest (e.g., `--exclude-skill db`)
- `--exclude-sub-agent <name>`: Exclude a sub-agent from manifest (e.g., `--exclude-sub-agent devops`)

Example:
- `oat compile`
- `oat compile --out ~/AGENTS.compiled.md --hash`
- `oat compile --no-personal --print`
- `oat compile --target cursor --watch`
- `oat compile --include-skill db --exclude-sub-agent devops`

#### 4.3.2 `oat validate`
**Purpose:** Validate constitution + project wiring without compiling output.

Checks (minimum):
- `AGENTS.md` exists in repo root (or warn if missing)
- `.agent/inherits.yaml` exists and is valid
- `org_root` resolves and contains `.agent/memory/constitution.md`
- Constitution file exists and is readable
- `skills` section exists in `inherits.yaml` (required)
- `sub_agents` section exists in `inherits.yaml` (required)
- All universal skills listed in `skills.universal` exist in `<org-root>/.agent/skills/`
- All language/stack specific skills listed in `skills.languages` exist in their respective directories
- All sub-agents listed in `sub_agents` exist in `<org-root>/.agent/sub-agents/`
- All teams listed in `teams` (if present) exist in `<org-root>/.agent/memory/teams/`
- All specified skill and sub-agent files are valid markdown
- `.agent/project.md` exists (or warn depending on mode)
- No forbidden constructs:
  - Absolute paths in inherits
  - References to non-existent skills, sub-agents, or teams
  - Invalid skill or sub-agent names
- Validates SemVer compliance if version metadata present in constitution

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
- Entry point (`AGENTS.md`) detected
- Constitution file path and version
- Memory files (constitution, general-context, teams from manifest)
- Universal skills from manifest (count and list)
- Language/stack specific skills from manifest (grouped by language/stack, count and list)
- Sub-agents from manifest (count and list)
- Teams from manifest (if specified)
- Project rules file path
- Personal overlay detected (yes/no)
- Effective compile order
- Available but not included: list of skills/sub-agents in org root that are not in manifest

Flags:
- `--json` for structured output

Example:
- `oat doctor`

#### 4.3.4 `oat init project`
**Purpose:** Scaffold `.agent/` in a repo to make it compliant.

Behavior:
- Create `<repo>/AGENTS.md` with entry point template
- Create `<repo>/.agent/inherits.yaml` with:
  - Best-effort computed relative `org_root`
  - Empty `skills` section with placeholder structure
  - Empty `sub_agents` section
  - Optional `teams` section
- Create `<repo>/.agent/project.md` with template sections
- Optionally scan project files to suggest relevant skills/sub-agents (if `--suggest` flag used)
- Refuse to overwrite existing files unless `--force`

Flags:
- `--org-root <path>`: explicitly provide org root
- `--force`: overwrite
- `--suggest`: scan project files and suggest relevant skills/sub-agents based on detected languages/stacks

Example:
- `oat init project --org-root ../..`

---

## 5. Compile Semantics (Normative)

### 5.1 Order of precedence in compiled output
The compiled document MUST be ordered as:

1) **Entry Point** (`AGENTS.md` from repo, if exists)
2) **Org Memory** (constitution, general-context, teams from manifest) (mandatory, highest authority)
3) **Universal Skills** (only skills specified in `inherits.yaml` `skills.universal`, in specified order)
4) **Language/Stack Specific Skills** (only skills specified in `inherits.yaml` `skills.languages`, grouped by language/stack, in specified order)
5) **Org Sub-Agents** (only sub-agents specified in `inherits.yaml` `sub_agents`, in specified order)
6) **Project Rules** (project.md)
7) **Personal Overlay** (personal memory, skills, sub-agents) (optional, lowest authority)

**Critical**: Only the skills, sub-agents, and teams explicitly declared in the project manifest are included. This ensures each project only gets relevant instructions for its stack.

### 5.2 Determinism
- Same inputs produce the same output byte-for-byte.
- Ordering comes only from manifests, never filesystem enumeration.

### 5.3 Traceability
Compiled output MUST include:
- Entry point source (`AGENTS.md` if used)
- Constitution name + version
- Memory files loaded (constitution, general-context, teams from manifest)
- Universal skills included (count and list from manifest)
- Language/stack specific skills included (grouped by language/stack, from manifest)
- Sub-agents included (count and list from manifest)
- Manifest source (`inherits.yaml` path)
- Repo name/path
- Timestamp optional (if included, must be clearly marked as non-deterministic metadata)
- Content hash (recommended)

---

## 6. Validation Rules (Phase 1)

Minimum enforcement:
- Missing `AGENTS.md` in repo => warning (recommended but not required)
- Missing `.agent/inherits.yaml` => error
- Missing `skills` section in `inherits.yaml` => error
- Missing `sub_agents` section in `inherits.yaml` => error
- Org constitution file missing => error
- Universal skills listed in manifest but file missing => error
- Language/stack specific skills listed in manifest but file missing => error
- Sub-agents listed in manifest but file missing => error
- Teams listed in manifest but file missing => error
- Personal overlay missing => not an error
- Project rules missing => error (strict default)

---

## 7. Portability & Cloning

The toolkit must:
- Work on macOS and Linux
- Require no hardcoded usernames or absolute paths in repos
- Avoid dependencies on a specific LLM vendor or IDE
- Be clonable: copy the `.agent/` tree to a new org and edit constitution files + manifest
- Moving the entire org directory structure does not break functionality due to relative pathing

---

## 8. Security & Trust Boundaries

- Toolkit must not execute project code.
- Toolkit must not fetch remote content.
- Toolkit must not modify anything outside its outputs unless explicitly requested (`oat init`).
- Org constitution is the trust anchor. Project rules are subordinate. Personal overlay is optional and lowest precedence.

---

## 9. Acceptance Criteria

- AC1: Running `oat compile` in any compliant repo produces a merged markdown file containing only the skills, sub-agents, and teams explicitly declared in `inherits.yaml`, along with org memory, project rules, and optionally personal overlay, with strict hierarchy enforcement.
- AC2: `oat validate` fails if `.agent/inherits.yaml` is missing, `skills` or `sub_agents` sections are missing, `org_root` cannot be resolved, `constitution.md` is missing, or any specified skills/sub-agents/teams reference non-existent files.
- AC3: `oat doctor` clearly prints the resolved org root, memory files, skills and sub-agents from manifest, and accurately traces the file inheritance path, including which items are available but not included.
- AC4: Projects remain portable: cloning the org directory elsewhere does not break `org_root` resolution (relative paths).
- AC5: Toolkit can be copied to a new org root and works after updating constitution and memory files.
- AC6: The toolkit correctly maps outputs to IDE-specific files via `--target` using `targets.yaml`.
- AC7: `AGENTS.md` entry point is properly included in compiled output when present.
- AC8: Only skills and sub-agents explicitly listed in the manifest are included in compilation.
- AC9: Compilation order follows the order specified in the manifest (not alphabetical).
- AC10: `oat init project --suggest` can scan project files and suggest relevant skills/sub-agents based on detected languages/stacks.

---

## 10. Vendor Reference

The `targets.yaml` file maps IDE/Agent names to their configuration file names:

```yaml
targets:
  cursor: .cursorrules
  windsurf: .windsurfrules
  roo: .clinerules
  copilot: .github/copilot-instructions.md
  claude: CLAUDE.md
  gemini: GEMINI.md
  amazon-q: AMAZON_Q.md
  auggie: .auggie.md
  codebuddy: .codebuddy
  qoder: .qoder/context.md
  opencode: .opencode
  amp: .amp.md
  kilo: .kilo
  qwen: .qwen
  bob: .bob/config
  jules: .jules
  shai: .shai
  codex: CODEX.md
```

When using `--target <name>`, the compiled output is written to the corresponding file in the repo root.

### 10.1 Vendor Configuration Files

Each vendor's configuration file should contain:

> CRITICAL: Read AGENTS.md first.

This ensures agents always start with the entry point before reading compiled rules.

## 11. Templates

### 11.1 `AGENTS.md` template (required in repo root)

```markdown
# Agent Instructions

> CRITICAL: Read AGENTS.md first.

This project follows the organization's agentic toolkit standards.

## Usage

Reference specific sub-agents when requesting work:
- "As a **backend-developer**, implement feature X"
- "As a **frontend-developer**, implement feature Y"
- "As a **tech-lead**, review my changes"
```

### 11.2 `inherits.yaml` template

```yaml
org_root: ../..
# Required: Explicitly declare which skills are relevant for this project
skills:
  universal:
    - git
    - test
    - db
    - review-checklist
  languages:
    python:
      - django
      - fastapi
      - pytest
    javascript:
      - react
      - nodejs
      - jest
# Required: Explicitly declare which sub-agents are relevant for this project
sub_agents:
  - backend-developer
  - frontend-developer
  - tech-lead
# Optional: Declare which teams are relevant (for team-specific memory)
teams:
  - platform
```

**Important**: Only skills and sub-agents listed here will be included in compilation. Use `oat init project --suggest` to get recommendations based on your project files.

### 11.3 `project.md` template (recommended)
- Project overview (1–2 paragraphs)
- Local glossary / terminology
- Data sensitivity notes
- Allowed / forbidden actions specific to project
- Exceptions to org defaults (must include rationale + ticket reference)
- Team context (which team owns this project)
- Language/stack context (which languages/frameworks are used, if not declared in inherits.yaml)

---

## 12. Future Enhancements (Not required for v1)
- Rule IDs + conflict linting (e.g. deny project files containing "OVERRIDE" without explicit allowlist)
- Signing / checksum enforcement for constitution
- Pre-commit hook integration
- CI job that runs `oat validate` across all repos in the org
