# OAT Changelog

All notable changes to this project will be documented in this file.

> The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Automatic version bumping in CI/CD pipeline when pushing to main branch
  - Version bump type determined by commit message tags: `[MAJOR]`, `[MINOR]`, or default `patch`
  - Version automatically updated in `pyproject.toml` and committed back to repository
