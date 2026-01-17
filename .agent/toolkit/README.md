# Org Agentic Toolkit

This directory contains the toolkit infrastructure for the Org Agentic Toolkit (OAT).

## Directory Structure

```
toolkit/
├── README.md              # This file
├── targets.yaml           # IDE target mappings
├── schemas/               # JSON schemas for validation
│   ├── inherits.schema.json
│   └── manifest.schema.json
└── templates/             # Project initialization templates
    ├── AGENTS.md.template
    ├── inherits.yaml.template
    └── project.md.template
```

## Files

### targets.yaml
Maps target names to IDE-specific configuration file paths. Used by `oat compile --target <name>` to write compiled output to the appropriate location.

### schemas/
JSON Schema files for validating YAML configuration files:
- `inherits.schema.json`: Validates `.agent/inherits.yaml`
- `manifest.schema.json`: Validates `.agent/memory/manifest.yaml`

### templates/
Template files used by `oat init project` to create new project structures:
- `AGENTS.md.template`: Entry point template
- `inherits.yaml.template`: Inherits configuration template
- `project.md.template`: Project-specific rules template

## Usage

### Compiling to IDE Targets
```bash
# Compile to Cursor IDE
oat compile --target cursor

# Compile to VS Code
oat compile --target vscode

# Compile to default markdown
oat compile --target default
```

### Initializing New Projects
```bash
# Initialize project with templates
oat init project

# Initialize with suggestions based on project files
oat init project --suggest
```

## Extending the Toolkit

### Adding New IDE Targets
Edit `targets.yaml` to add new target mappings:
```yaml
targets:
  my-ide:
    path: .my-ide/config
    description: My IDE configuration
```

### Adding New Templates
Add template files to `templates/` directory. Templates are used by `oat init project` to create new project structures.
