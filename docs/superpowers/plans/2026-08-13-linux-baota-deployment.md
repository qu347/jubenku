# Linux Baota Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tested Linux production launcher, systemd service, Linux environment template, and first-time Baota deployment guide that preserve the existing SQLite database and material files.

**Architecture:** Nginx exposes only ports 80/443 and proxies to a single-worker FastAPI process on `127.0.0.1:8100`. A strict Bash launcher delegates configuration validation to a focused Python module, runs Alembic and the existing read-only data audit, then replaces itself with Uvicorn so systemd owns the real server process.

**Tech Stack:** Bash, Python 3.11, Pydantic Settings, SQLAlchemy SQLite URL parsing, Alembic, Uvicorn, systemd, pytest, Git Bash, Vue/Vite, Baota Nginx.

## Global Constraints

- Keep all existing Windows `.bat` files and Windows deployment behavior unchanged.
- Code lives at `/www/wwwroot/jubenku`; production data lives at `/www/server/data/jubenku` and must never be placed inside the code checkout.
- Bind FastAPI to `127.0.0.1`; use port `8100` in the provided template; do not open `8100` in the cloud security group or Baota firewall.
- Expose only Nginx ports `80` and `443` publicly.
- Use the existing database and `storage/materials`; never create or overwrite a production database from the startup path.
- Fix SQLite production execution at one Uvicorn worker.
- Read production settings only through `backend/.env.production`; do not source or echo the file from Bash.
- Fail closed when configuration, migration, attachment audit, frontend build, permissions, or port checks fail.
- Do not commit `.env.production`, SQLite files, user uploads, generated backups, `.venv`, or `node_modules`.
- Retain the current security warning: this application has no authentication and must have a Baota access restriction, IP allowlist, or equivalent external access control.

---

## File Structure

- Create `backend/app/tools/check_linux_environment.py`: pure Linux production validation plus a small CLI that emits the validated server binding.
- Create `backend/tests/test_linux_deployment.py`: Python validator tests, real Bash launcher behavior tests, environment-template tests, and systemd-unit contract tests.
- Create `deploy/linux/start_production.sh`: strict production lifecycle orchestration; no duplicated configuration parser.
- Create `deploy/linux/jubenku.service`: systemd service that runs the launcher as the Baota `www` account.
- Create `backend/.env.production.linux.example`: safe Linux production values with `/www` paths and loopback port 8100.
- Create `docs/LINUX_DEPLOYMENT.md`: first-time installation, data migration, Baota reverse proxy, service management, update, backup, and troubleshooting steps.
- Modify `README.md`: link to the Linux/Baota deployment guide without rewriting the Windows guide.

---

### Task 1: Linux Production Environment Validator

**Files:**
- Create: `backend/app/tools/check_linux_environment.py`
- Create: `backend/tests/test_linux_deployment.py`

**Interfaces:**
- Consumes: `app.core.config.Settings`, `app.core.runtime.sqlite_database_path`, standard `pathlib` and `socket`.
- Produces: `LinuxEnvironmentError`, `ServerBinding(host: str, port: int)`, `validate_linux_environment(config: Settings, project_root: Path, *, check_port: bool = True) -> ServerBinding`, and CLI `main(argv: list[str] | None = None) -> int`.
- CLI success output: exactly one machine-readable line in `host|port` form; diagnostics go to stderr and never contain `.env.production` contents.

- [ ] **Step 1: Write the validator fixture and happy-path test**

Add a helper that creates sibling code and data roots. Build a real SQLite file, all writable directories, and `frontend/dist/index.html`, then instantiate `Settings` with explicit production values:

```python
def make_linux_runtime(tmp_path: Path, **overrides: object) -> tuple[Settings, Path]:
    project_root = tmp_path / "jubenku"
    data_root = tmp_path / "jubenku-data"
    frontend_dist = project_root / "frontend" / "dist"
    frontend_dist.mkdir(parents=True)
    (frontend_dist / "index.html").write_text("<!doctype html>", encoding="utf-8")
    for name in ("database", "storage/materials", "logs", "backups", "temp"):
        (data_root / name).mkdir(parents=True, exist_ok=True)
    database = data_root / "database" / "script_materials.db"
    database.write_bytes(b"sqlite-placeholder")
    values: dict[str, object] = {
        "app_env": "production",
        "app_host": "127.0.0.1",
        "app_port": 8100,
        "debug": False,
        "database_url": f"sqlite:///{database.as_posix()}",
        "storage_root": data_root / "storage",
        "log_dir": data_root / "logs",
        "backup_root": data_root / "backups",
        "temp_root": data_root / "temp",
        "serve_frontend": True,
        "frontend_dist": frontend_dist,
        "cors_allowed_origins": "",
    }
    values.update(overrides)
    return Settings(**values), project_root


def test_linux_environment_accepts_isolated_loopback_production(tmp_path: Path) -> None:
    config, project_root = make_linux_runtime(tmp_path)
    assert validate_linux_environment(config, project_root, check_port=False) == ServerBinding(
        "127.0.0.1", 8100
    )
```

- [ ] **Step 2: Run the happy-path test and verify RED**

Run:

```powershell
cd D:\文档存储\backend
.\.venv\Scripts\python.exe -m pytest -q tests/test_linux_deployment.py::test_linux_environment_accepts_isolated_loopback_production -p no:cacheprovider
```

Expected: collection fails because `app.tools.check_linux_environment` does not exist.

- [ ] **Step 3: Add failing security and data-integrity cases**

Add parameterized tests that mutate one production contract at a time and assert a stable error category:

```python
@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"app_env": "development"}, "production"),
        ({"debug": True}, "DEBUG"),
        ({"app_host": "0.0.0.0"}, "127.0.0.1"),
        ({"serve_frontend": False}, "frontend"),
    ],
)
def test_linux_environment_rejects_unsafe_runtime_values(
    tmp_path: Path, overrides: dict[str, object], message: str
) -> None:
    config, project_root = make_linux_runtime(tmp_path, **overrides)
    with pytest.raises(LinuxEnvironmentError, match=message):
        validate_linux_environment(config, project_root, check_port=False)
```

Add separate tests for a missing database, missing `index.html`, relative paths, `material_storage_path` not equal to `storage_root/materials`, a top-level data directory nested inside another, and any data directory below `project_root`.

- [ ] **Step 4: Implement the minimal validator**

Implement the public contract with these checks in order:

```python
@dataclass(frozen=True)
class ServerBinding:
    host: str
    port: int


class LinuxEnvironmentError(RuntimeError):
    pass


def validate_linux_environment(
    config: Settings,
    project_root: Path,
    *,
    check_port: bool = True,
) -> ServerBinding:
    # Validate production/debug/host/API/frontend flags.
    # Require file-backed SQLite and absolute configured paths.
    # Require database, storage, logs, backups, and temp as isolated siblings
    # outside the resolved project root; storage/materials is the sole allowed nesting.
    # Require the database file and frontend/dist/index.html to exist.
    # Probe write access using a uniquely named zero-byte file removed in finally.
    # Bind a temporary socket to the configured host/port when check_port=True.
    return ServerBinding(config.app_host, config.app_port)
```

Use `sqlalchemy.engine.make_url` or the existing `sqlite_database_path()` helper; do not split a SQLite URL manually. Never include absolute data paths in public-facing error text.

- [ ] **Step 5: Add the CLI entry point**

The CLI accepts `--project-root` and `--skip-port-check`, loads `get_settings()`, prints only `host|port` on success, prints a `Linux 生产环境检查失败：` prefix plus the validated error category to stderr on failure, and returns `1`:

```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--skip-port-check", action="store_true")
    args = parser.parse_args(argv)
    try:
        binding = validate_linux_environment(
            get_settings(), args.project_root, check_port=not args.skip_port_check
        )
    except LinuxEnvironmentError as exc:
        print(f"Linux 生产环境检查失败：{exc}", file=sys.stderr)
        return 1
    print(f"{binding.host}|{binding.port}")
    return 0
```

- [ ] **Step 6: Run validator tests and verify GREEN**

Run:

```powershell
cd D:\文档存储\backend
.\.venv\Scripts\python.exe -m pytest -q tests/test_linux_deployment.py -p no:cacheprovider
```

Expected: all validator tests pass.

- [ ] **Step 7: Commit the validator**

```powershell
git add backend/app/tools/check_linux_environment.py backend/tests/test_linux_deployment.py
git commit -m "feat: validate Linux production environment"
```

---

### Task 2: Strict Linux Production Launcher

**Files:**
- Create: `deploy/linux/start_production.sh`
- Modify: `backend/tests/test_linux_deployment.py`

**Interfaces:**
- Consumes: validator CLI from Task 1, `backend/.venv/bin/python`, `backend/.venv/bin/alembic`, `backend/.env.production`, `frontend/dist/index.html`.
- Produces: executable Bash entry point with no arguments; with the provided template, the successful final process is `python -m uvicorn app.main:app --host 127.0.0.1 --port 8100 --workers 1`.

- [ ] **Step 1: Add a cross-platform Bash locator and fake-project fixture**

In the pytest file, locate Bash in this order: `shutil.which("bash")`, `C:/Program Files/Git/bin/bash.exe`, then `/bin/bash`. Fail the test with an explicit message if none exists. Create a temporary `deploy/linux` layout, copy the launcher under test, and add executable fake files at `.venv/bin/python` and `.venv/bin/alembic` that append commands to `TRACE_FILE`.

The fake Python must emit `127.0.0.1|8100` only for `app.tools.check_linux_environment`, return `VALIDATION_EXIT` for that module, return `AUDIT_EXIT` for `app.tools.audit_data`, and record the exact Uvicorn arguments. The fake Alembic must return `UPGRADE_EXIT` or `CHECK_EXIT` for the matching subcommand. `run_launcher()` sets all four variables to `0` unless a test explicitly overrides one.

- [ ] **Step 2: Write the successful lifecycle test**

```python
def test_linux_launcher_runs_checks_in_order_and_execs_one_worker(tmp_path: Path) -> None:
    project, trace = make_launcher_fixture(tmp_path)
    completed = run_launcher(project, cwd=tmp_path.parent)
    assert completed.returncode == 0, completed.stderr
    assert trace.read_text(encoding="utf-8").splitlines() == [
        "python -m app.tools.check_linux_environment --project-root " + project.as_posix(),
        "alembic upgrade head",
        "alembic check",
        "python -m app.tools.audit_data --fail-on-missing",
        "python -m uvicorn app.main:app --host 127.0.0.1 --port 8100 --workers 1",
    ]
```

- [ ] **Step 3: Run launcher test and verify RED**

Run the single pytest node. Expected: FAIL because `deploy/linux/start_production.sh` does not exist.

- [ ] **Step 4: Add failure-path tests**

Add parameterized tests for missing `.venv/bin/python`, missing Alembic, missing `.env.production`, and missing `frontend/dist/index.html`. Add one test per lifecycle failure variable (`VALIDATION_EXIT`, `UPGRADE_EXIT`, `CHECK_EXIT`, `AUDIT_EXIT`) and assert later commands, especially Uvicorn, never appear in the trace.

- [ ] **Step 5: Implement the minimal launcher**

Create a UTF-8, LF-only script with this control flow:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
BACKEND_DIR="$PROJECT_ROOT/backend"
PYTHON_EXE="$BACKEND_DIR/.venv/bin/python"
ALEMBIC_EXE="$BACKEND_DIR/.venv/bin/alembic"
PRODUCTION_ENV="$BACKEND_DIR/.env.production"

unset APP_HOST APP_PORT API_PREFIX DEBUG DATABASE_URL STORAGE_ROOT \
  MATERIAL_STORAGE_PATH LOG_DIR BACKUP_ROOT TEMP_ROOT MAX_UPLOAD_MB \
  BACKUP_RETENTION_DAYS SQLITE_BUSY_TIMEOUT_MS SQLITE_WAL_ENABLED \
  SERVE_FRONTEND FRONTEND_DIST CORS_ALLOWED_ORIGINS CORS_ORIGINS \
  LOG_MAX_BYTES LOG_BACKUP_COUNT PYTHONOPTIMIZE || true
export APP_ENV=production
export SETTINGS_ENV_FILE="$PRODUCTION_ENV"
```

Check required files with a `require_file` or `require_executable` helper, change to `backend`, capture validator output, split it with `IFS='|' read -r`, then run migration, migration check, audit, and:

```bash
exec "$PYTHON_EXE" -m uvicorn app.main:app \
  --host "$UVICORN_HOST" \
  --port "$UVICORN_PORT" \
  --workers 1
```

Do not use `eval`, `source`, `nohup`, `&`, PID files, or Shell parsing of `.env.production`.

- [ ] **Step 6: Mark the launcher executable and verify Bash syntax**

```powershell
git update-index --add --chmod=+x deploy/linux/start_production.sh
& 'C:\Program Files\Git\bin\bash.exe' -n deploy/linux/start_production.sh
```

Expected: Bash exits `0` with no output.

- [ ] **Step 7: Run launcher behavior tests and verify GREEN**

Run the launcher tests through pytest. Expected: successful path and every fail-closed path pass.

- [ ] **Step 8: Commit the launcher**

```powershell
git add deploy/linux/start_production.sh backend/tests/test_linux_deployment.py
git commit -m "feat: add Linux production launcher"
```

---

### Task 3: Linux Configuration Template and systemd Service

**Files:**
- Create: `backend/.env.production.linux.example`
- Create: `deploy/linux/jubenku.service`
- Modify: `backend/tests/test_linux_deployment.py`

**Interfaces:**
- Consumes: fixed `/www/wwwroot/jubenku` code path, `/www/server/data/jubenku` data path, launcher from Task 2.
- Produces: settings template consumed by `Settings` after copying to `.env.production`; systemd unit named `jubenku.service`.

- [ ] **Step 1: Write the environment-template consumption test**

Set `SETTINGS_ENV_FILE` to the example file, clear conflicting environment variables with `monkeypatch.delenv`, instantiate `Settings()`, and assert these parsed values:

```python
assert config.app_env == "production"
assert config.app_host == "127.0.0.1"
assert config.app_port == 8100
assert config.database_url == "sqlite:////www/server/data/jubenku/database/script_materials.db"
assert config.storage_root == Path("/www/server/data/jubenku/storage")
assert config.material_storage_path == Path("/www/server/data/jubenku/storage/materials")
assert config.frontend_dist == Path("/www/wwwroot/jubenku/frontend/dist")
assert config.serve_frontend is True
assert config.cors_origin_list == []
```

- [ ] **Step 2: Write the systemd-unit contract test**

Parse the unit with `configparser.ConfigParser(interpolation=None, strict=True)` and assert:

```python
assert service["Service"]["User"] == "www"
assert service["Service"]["Group"] == "www"
assert service["Service"]["WorkingDirectory"] == "/www/wwwroot/jubenku/backend"
assert service["Service"]["ExecStart"] == "/www/wwwroot/jubenku/deploy/linux/start_production.sh"
assert service["Service"]["Restart"] == "on-failure"
assert service["Install"]["WantedBy"] == "multi-user.target"
```

- [ ] **Step 3: Run both tests and verify RED**

Expected: both fail because the template and service file do not exist.

- [ ] **Step 4: Create the Linux environment template**

Copy the capacity, retention, SQLite, and logging values from `.env.production.example`, replace every Windows path, set `APP_HOST=127.0.0.1`, `APP_PORT=8100`, and keep `CORS_ALLOWED_ORIGINS=` empty. Include a first-line warning to copy it to `.env.production` and never commit the real file.

- [ ] **Step 5: Create the systemd unit**

Use these sections and values:

```ini
[Unit]
Description=Jubenku material library
After=network.target

[Service]
Type=simple
User=www
Group=www
WorkingDirectory=/www/wwwroot/jubenku/backend
ExecStart=/www/wwwroot/jubenku/deploy/linux/start_production.sh
Restart=on-failure
RestartSec=5
TimeoutStartSec=180
TimeoutStopSec=30
KillSignal=SIGTERM
UMask=0077
Environment=PYTHONUNBUFFERED=1
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=/www/server/data/jubenku

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 6: Run template and unit tests and verify GREEN**

Run the full `test_linux_deployment.py`. On a Linux host with systemd, additionally copy the unit to a temporary path and run `systemd-analyze verify`; local Windows verification is limited to strict INI parsing and contract checks.

- [ ] **Step 7: Commit configuration and service files**

```powershell
git add backend/.env.production.linux.example deploy/linux/jubenku.service backend/tests/test_linux_deployment.py
git commit -m "feat: add Linux service configuration"
```

---

### Task 4: First-Time Baota and Existing-Data Deployment Guide

**Files:**
- Create: `docs/LINUX_DEPLOYMENT.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: launcher, template, and service from Tasks 2-3; existing `app.tools.backup` and `app.tools.verify_backup` CLIs.
- Produces: an ordered operator runbook with explicit stop points and verification results.

- [ ] **Step 1: Write the local migration section**

Document that the authoritative source is `.runtime/portable`, require stopping the local process first, and provide exact PowerShell commands using the existing backup tool:

```powershell
cd D:\文档存储\backend
.\.venv\Scripts\python.exe -m app.tools.backup `
  --database-url sqlite:///D:/文档存储/.runtime/portable/database/script_materials.db `
  --materials-root D:\文档存储\.runtime\portable\storage\materials `
  --backup-root D:\文档存储\outputs\linux_migration `
  --retention-days 30

$backupDirectory = Get-ChildItem D:\文档存储\outputs\linux_migration -Directory |
  Sort-Object LastWriteTime |
  Select-Object -Last 1
if ($null -eq $backupDirectory) { throw '没有找到迁移备份目录' }

.\.venv\Scripts\python.exe -m app.tools.verify_backup $backupDirectory.FullName
if ($LASTEXITCODE -ne 0) { throw '迁移备份验证失败，禁止上传' }

$archive = "$($backupDirectory.FullName).zip"
Compress-Archive -LiteralPath $backupDirectory.FullName -DestinationPath $archive -Force
Write-Output $archive
```

Explain how to upload the printed ZIP path with Baota File Manager and preserve the timestamp directory when extracting it on the server.

- [ ] **Step 2: Write first-time server preparation and code-build sections**

Include exact Alibaba Cloud Linux commands for:

```bash
cd /www/wwwroot
git clone https://github.com/qu347/jubenku.git jubenku
cd /www/wwwroot/jubenku/backend
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

corepack enable
corepack prepare pnpm@10 --activate
cd /www/wwwroot/jubenku/frontend
pnpm install --frozen-lockfile
pnpm run type-check
pnpm run test:unit
pnpm run build
```

Check versions first and state the Node requirement as `^20.19.0 || >=22.12.0`; the observed server Node `22.23.0` satisfies it.

- [ ] **Step 3: Write safe restore and permission sections**

Use a temporary extraction directory, run `app.tools.verify_backup` against the uploaded directory, refuse overwrite when `/www/server/data/jubenku/database/script_materials.db` already exists, then copy the database and `storage/materials`. Create the five sibling data directories and set ownership to `www:www`; apply directory mode `750`, database/file mode `640`, and `.env.production` mode `600`.

Require post-restore checks for Alembic `20260812_0009`, 84 materials, 3 projects, 47 tags, 12 upload platforms, 17 attachment references, 17 files, and zero missing files.

- [ ] **Step 4: Write service and Baota Nginx sections**

Document:

```bash
cp deploy/linux/jubenku.service /etc/systemd/system/jubenku.service
systemd-analyze verify /etc/systemd/system/jubenku.service
systemctl daemon-reload
systemctl enable --now jubenku
systemctl status jubenku --no-pager
curl --fail http://127.0.0.1:8100/api/health/ready
```

In Baota, create or select the domain site, configure a reverse proxy to `http://127.0.0.1:8100`, enable HTTPS, set `client_max_body_size 110m`, preserve `Host`, `X-Real-IP`, and `X-Forwarded-For`, set proxy connect/read/send timeouts to 300 seconds, and apply an access restriction because the application has no login. State that cloud and Baota firewalls open only `80/443`, not `8100`.

- [ ] **Step 5: Write operations and troubleshooting sections**

Include exact commands for `systemctl restart/stop/status`, `journalctl -u jubenku`, application logs, port checks, Git-based updates preceded by a verified backup, and 502/readiness/permission/database/attachment troubleshooting. State that code rollback does not imply database downgrade and that database recovery must use a verified backup.

- [ ] **Step 6: Add the README link and verify references**

Add a short `Linux / 宝塔生产部署` subsection next to the Windows deployment section. Run:

```powershell
Test-Path docs/LINUX_DEPLOYMENT.md
rg -n "LINUX_DEPLOYMENT|start_production.sh|jubenku.service|127.0.0.1:8100" README.md docs/LINUX_DEPLOYMENT.md
git diff --check
```

Expected: document exists, all deployed artifacts are referenced, and diff check is clean.

- [ ] **Step 7: Commit the runbook**

```powershell
git add docs/LINUX_DEPLOYMENT.md README.md
git commit -m "docs: add Linux Baota deployment guide"
```

---

### Task 5: Full Verification and Deployment Handoff

**Files:**
- Verify only; modify implementation files only if a verification failure exposes a defect.

**Interfaces:**
- Consumes: all artifacts from Tasks 1-4.
- Produces: fresh evidence for backend behavior, Bash syntax, frontend compatibility, Git file mode, and operator handoff.

- [ ] **Step 1: Run focused Linux deployment tests**

```powershell
cd D:\文档存储\backend
.\.venv\Scripts\python.exe -m pytest -q tests/test_linux_deployment.py -p no:cacheprovider
```

Expected: all Linux validator, launcher, environment, and systemd tests pass.

- [ ] **Step 2: Run Bash syntax verification**

```powershell
cd D:\文档存储
& 'C:\Program Files\Git\bin\bash.exe' -n deploy/linux/start_production.sh
```

Expected: exit `0`, no output.

- [ ] **Step 3: Run the complete backend suite**

```powershell
cd D:\文档存储\backend
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

Expected: zero failures.

- [ ] **Step 4: Run all frontend checks**

```powershell
cd D:\文档存储\frontend
npm.cmd run type-check
npm.cmd run test:unit
npm.cmd run build
```

Expected: type checking, all unit tests, and production build exit `0`.

- [ ] **Step 5: Verify repository scope and executable bit**

```powershell
cd D:\文档存储
git diff --check
git status -sb
git ls-files --stage deploy/linux/start_production.sh
```

Expected: no whitespace errors, only intended files changed, and launcher mode is `100755`.

- [ ] **Step 6: Review requirements against the approved design**

Confirm line by line: loopback-only binding, port 8100 template, one worker, no automatic database creation, isolated `/www/server/data/jubenku`, migration then check then audit, systemd restart behavior, existing-data runbook, no Windows regressions, no secrets, and no `8100` firewall rule.

- [ ] **Step 7: Commit any verification-only correction, if needed**

If verification required a correction, stage only the affected implementation and test files and commit with a message describing the corrected contract. If no correction was needed, do not create an empty commit.

- [ ] **Step 8: Hand off the first server command**

After all checks pass and the implementation is published, guide the user interactively. The first server action is a collision-safe clone check under `/www/wwwroot`; do not ask the user to paste the entire runbook at once. Stop after each numbered server step, read the output, and only then provide the next command.
