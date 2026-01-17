"""Configuration loading module for YAML files."""

import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List


class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass


def load_inherits_yaml(path: Path) -> Dict[str, Any]:
    """
    Load and parse the inherits.yaml file.
    
    Args:
        path: Path to .agent/inherits.yaml file
    
    Returns:
        Parsed YAML configuration dict
    
    Raises:
        ConfigError: If file doesn't exist or is invalid
    """
    if not path.exists():
        raise ConfigError(f"Inherits file not found: {path}")
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, dict):
            raise ConfigError(f"Invalid inherits.yaml: expected dict, got {type(config)}")
        
        return config
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in inherits.yaml: {e}")
    except Exception as e:
        raise ConfigError(f"Error reading inherits.yaml: {e}")


def load_memory_manifest(path: Path) -> Optional[Dict[str, Any]]:
    """
    Load the optional memory manifest.yaml file.
    
    Args:
        path: Path to .agent/memory/manifest.yaml file
    
    Returns:
        Parsed manifest dict, or None if file doesn't exist
    """
    if not path.exists():
        return None
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
        
        if not isinstance(manifest, dict):
            return None
        
        return manifest
    except (yaml.YAMLError, Exception):
        return None


def load_targets_yaml(path: Path) -> Dict[str, str]:
    """
    Load the targets.yaml file for IDE mappings.
    
    Args:
        path: Path to .agent/toolkit/targets.yaml file
    
    Returns:
        Dict mapping target names to filenames, or empty dict if file doesn't exist
    """
    if not path.exists():
        return {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, dict):
            return {}
        
        targets = config.get("targets", {})
        if not isinstance(targets, dict):
            return {}
        
        return targets
    except (yaml.YAMLError, Exception):
        return {}


def validate_inherits_structure(config: Dict[str, Any]) -> List[str]:
    """
    Validate the structure of inherits.yaml configuration.
    
    Args:
        config: Parsed inherits.yaml dict
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Check required fields
    if "org_root" not in config:
        errors.append("Missing required field: org_root")
    
    if "skills" not in config:
        errors.append("Missing required field: skills")
    elif isinstance(config["skills"], dict):
        if "universal" not in config["skills"]:
            errors.append("Missing required field: skills.universal")
        elif not isinstance(config["skills"]["universal"], list):
            errors.append("skills.universal must be a list")
        
        if "languages" in config["skills"]:
            if not isinstance(config["skills"]["languages"], dict):
                errors.append("skills.languages must be a dict")
    else:
        errors.append("skills must be a dict")
    
    if "personas" not in config:
        errors.append("Missing required field: personas")
    elif not isinstance(config["personas"], list):
        errors.append("personas must be a list")
    
    if "target_agents" in config:
        if not isinstance(config["target_agents"], list):
            errors.append("target_agents must be a list")
    
    # Check for forbidden absolute paths
    if "org_root" in config:
        org_root = config["org_root"]
        if isinstance(org_root, str) and Path(org_root).is_absolute():
            errors.append("org_root must be a relative path (absolute paths are forbidden)")
    
    return errors


def get_skills_from_config(config: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Extract skills configuration from inherits.yaml.
    
    Args:
        config: Parsed inherits.yaml dict
    
    Returns:
        Dict with 'universal' and 'languages' keys
    """
    skills = config.get("skills", {})
    
    result = {
        "universal": skills.get("universal", []),
        "languages": skills.get("languages", {})
    }
    
    return result


def get_personas_from_config(config: Dict[str, Any]) -> List[str]:
    """
    Extract personas list from inherits.yaml.
    
    Args:
        config: Parsed inherits.yaml dict
    
    Returns:
        List of persona names
    """
    return config.get("personas", [])


def get_teams_from_config(config: Dict[str, Any]) -> List[str]:
    """
    Extract teams list from inherits.yaml.
    
    Args:
        config: Parsed inherits.yaml dict
    
    Returns:
        List of team names (empty if not specified)
    """
    return config.get("teams", [])


def get_target_agents_from_config(config: Dict[str, Any]) -> List[str]:
    """
    Extract target_agents list from inherits.yaml.
    
    Args:
        config: Parsed inherits.yaml dict
    
    Returns:
        List of target agent names (empty if not specified)
    """
    return config.get("target_agents", [])
