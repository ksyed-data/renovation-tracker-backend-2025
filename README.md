# Introduction

This repo contains the source code for the back-end of the 2025 CoStar VCU Capstone Project

## Package Management

This project uses [`uv`](https://github.com/astral-sh/uv) for package management

### Installation

```sh
pip install uv
```

### Setup Environment

Use this command to sync your environment with all dependencies in pyproject.toml file.

```sh
uv sync
```

### Install Packages

Use these commands to add or remove packages from the project

```sh
uv add pillow
uv remove pillow
```

## Resources

- [uv Documentation](https://docs.astral.sh/uv/)

## Pull Requests
### 1. Create a branch off of main with your new feature
use the naming convention: {first initial}{last name} /new-feature. For example: amarlett/add-nav-menu
### 2. Make changes, commit as you go
Use commit messages that make sense and describe your changes. Make small commits. If your computer was lost or broke, is your branch committed and up to date?
### 3. Make your PR
You want PR's to be small, digestable, and functional. Each PR needs to be reviewed by a member of your team (or CoStar sponsors). Reviewer should leave comments with suggestions and give merge approval.
