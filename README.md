# Introduction

This repo contains the source code for the back-end of the 2025 CoStar VCU Capstone Project


## **Installation Prerequisites**

### **Podman**

The project uses podman to manage containers, follow the installation guide found here:

https://github.com/containers/podman/blob/main/docs%2Ftutorials%2Fpodman-for-windows.md


### Package Management

This project uses [`uv`](https://github.com/astral-sh/uv) for package management

**Install uv with this command:**

```sh
pip install uv
```

## Setup Environment

Use this command to sync your environment with all dependencies in pyproject.toml file.

```sh
uv sync
```

## Install Packages

Use these commands to add or remove packages from the project

```sh
uv add pillow
uv remove pillow
```

## Spin up mySQL server

### Start Podman machine

```sh
podman machine start
```

### Spin up DB container

```sh
podman compose up -d mysql
```

## Run FastAPI

### Run launch config with VC Code

Open Run & Debug: Ctrl + Shift + D

Press F5 to start the server

### Access API

Open your browser and visit host http://127.0.0.1:8000 to access the API



## Resources

- [uv Documentation](https://docs.astral.sh/uv/)

## Pull Requests
### 1. Create a branch off of main with your new feature
use the naming convention: {first initial}{last name} /new-feature. For example: amarlett/add-nav-menu
### 2. Make changes, commit as you go
Use commit messages that make sense and describe your changes. Make small commits. If your computer was lost or broke, is your branch committed and up to date?
### 3. Make your PR
You want PR's to be small, digestable, and functional. Each PR needs to be reviewed by a member of your team (or CoStar sponsors). Reviewer should leave comments with suggestions and give merge approval.

## Run fastAPI

- Navigate to file root
- Use these commands to build into installable package (should only have to do once unless dependencies change)

uv build
uv sync

- Run with command

uv run uvicorn renovation_tracker.main:api