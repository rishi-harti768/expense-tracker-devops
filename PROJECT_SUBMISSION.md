# ExpenseTracker — DevOps Final Capstone Submission

**Student:** Rishi Harti
**Repository:** https://github.com/rishi-harti768/expense-tracker-devops
**Application:** ExpenseTracker, a personal expense tracker (FastAPI, React, PostgreSQL)

This file maps each module in `GRADING.md` to the evidence in this repository. Screenshot placeholders are empty. Replace each placeholder with the real image before you submit.

## Status

| Module | Topic | Status |
|--------|-------|--------|
| M1 | Application | Done |
| M2 | Testing | Done |
| M3 | Git and GitHub | Done |
| M4 | Docker | Done (screenshots pending) |
| M5 | CI/CD | Done (deploy job needs a live cluster and secret) |
| M6 | Trivy | Done |
| M7 | Terraform | Done (screenshots pending) |
| M8 | Kubernetes + Helm | Chart done. Deployed to minikube. EKS deploy pending. |
| M9 | Observability | Pending |
| M10 | README and demo | README done. Live demo pending. |

---

## M1 — Application (Frontend + Backend + Database)

**Endpoints** (`backend/app/main.py`, prefix `/api/expenses`):

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness check |
| GET | `/ready` | Readiness check (database access) |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/expenses` | List expenses, newest first |
| GET | `/api/expenses/stats` | Totals by category |
| GET | `/api/expenses/{id}` | Read one expense |
| POST | `/api/expenses` | Create an expense |
| PUT | `/api/expenses/{id}` | Update an expense |
| DELETE | `/api/expenses/{id}` | Delete an expense |

**Database:** Table `expenses`, managed by Alembic. Migration: `backend/alembic/versions/0001_create_expenses.py`.

**Frontend:** React dashboard in `frontend/src/main.jsx`. It shows KPI cards, a category filter, a table with category cycling and delete, a create modal, and the three newest expenses.

**Submitted files:** `backend/app/`, `backend/alembic/versions/`, `backend/requirements.txt`, `frontend/`, `docker-compose.yml`.

**Screenshot: running application in the browser**

> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m1-app-browser.png`]

---

## M2 — Testing (Pytest)

**Tests:** `backend/tests/test_api.py` has 7 tests. They cover `/health`, `/`, POST, zero-amount validation (422), GET of a missing id (404), PUT and DELETE, and stats.

**Config:** `backend/pytest.ini`.

**Test database:** SQLite `test.db` through `DATABASE_URL`, not the production PostgreSQL database.

**Result (local, Python 3.12 container):** `7 passed`.

**Screenshot: `pytest -v` output**

> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m2-pytest.png`]

---

## M3 — Git and GitHub

**Repository:** https://github.com/rishi-harti768/expense-tracker-devops

**`.gitignore`** excludes `.env`, `__pycache__/`, `node_modules/`, `.venv/`, `*.db`, and Terraform state.

**Commit history:** Show at least 10 commits.

**Screenshot: commit history**

> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m3-commits.png`]

---

## M4 — Docker

| Item | File | Result |
|------|------|--------|
| Backend image | `backend/Dockerfile` | Builds. Runs as UID 10001. |
| Frontend image | `frontend/Dockerfile` | Multi-stage: Node build, then nginx runtime. Runs as UID 101. |
| Compose | `docker-compose.yml` | Three services: `postgres`, `backend`, `frontend` |

**Verified:** `docker compose up --build` starts all three services. Logs show Alembic running the migration, Uvicorn starting, and nginx starting. CRUD and stats work through the frontend proxy on port 3000.

**Screenshot: `docker compose up --build` output**

> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m4-compose-up.png`]

**Screenshot: browser at `http://localhost:3000`**

> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m4-browser-3000.png`]

---

## M5 — CI/CD (GitHub Actions)

**Workflow:** `.github/workflows/ci-cd.yml`

- Trigger: push to `main`.
- Job `test`: installs the backend requirements, runs `pytest`, and builds the frontend.
- Job `build-scan-push`: builds both images, scans them with Trivy, and pushes them to GHCR. Image tags use the commit SHA (`${{ github.sha }}`).
- Job `deploy`: runs `helm upgrade --install` against the cluster in the `KUBE_CONFIG_DATA` secret.

**Green run:** https://github.com/rishi-harti768/expense-tracker-devops/actions/runs/38890889517 (`test` and `build-scan-push` passed).

**Deploy job:** Needs a live cluster and the `KUBE_CONFIG_DATA` secret. Status: pending.

**Screenshot: green GitHub Actions run**

> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m5-actions-green.png`]

**Screenshot: GHCR packages with SHA tags**

> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m5-ghcr-packages.png`]

---

## M6 — DevSecOps (Trivy)

**Scan:** Trivy runs on both images in `build-scan-push`, with `severity: HIGH,CRITICAL`, `ignore-unfixed: true`, and `exit-code: '1'`. A HIGH or CRITICAL finding fails the build.

**Findings fixed during the build:**

- Backend: Starlette CVEs fixed by `starlette==1.3.1`, `fastapi==0.136.0`, and `prometheus-fastapi-instrumentator==8.1.0`.
- Frontend: OpenSSL and c-ares CVEs in the Alpine base. Fixed by moving to `nginx-unprivileged:1.29-alpine` and running `apk upgrade`.

**Result:** Both images pass the scan (exit 0 when scanned locally).

**Explanation (write in your own words):** Trivy scans each container image for known CVEs in OS packages and language packages. The scan gates the pipeline, so an image with a HIGH or CRITICAL fixable CVE is never pushed.

**Screenshot: Trivy output from a pipeline run**

> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m6-trivy.png`]

---

## M7 — Terraform (AWS VPC and EKS)

**Files:** `terraform/main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`. Example variables: `terraform/terraform.tfvars.example` (placeholder values only, no credentials).

**Provisioned resources:**

- VPC `expense-tracker-vpc` with 2 public and 2 private subnets, one NAT gateway
- EKS cluster `expense-tracker-eks` (Kubernetes 1.31)
- Managed node group `main` with 2 `t3.medium` nodes (scales 2 to 4)

**Verified:**

- `terraform init` and `terraform validate` pass.
- `terraform plan` gives 54 resources to add.
- `terraform apply` created the VPC and EKS cluster. The cluster reached `ACTIVE`. Both nodes reached `Ready`.
- `terraform destroy` completed. The Terraform state is empty.

**Screenshots:**

> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m7-plan.png`] — `terraform plan` output
> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m7-console-vpc-eks.png`] — AWS Console: VPC and EKS in `ap-south-1`
> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m7-destroy.png`] — `terraform destroy` completion

---

## M8 — Kubernetes and Helm

**Files:**

- `k8s/namespace.yaml` (namespace `expense-tracker`)
- `helm/expense-tracker/` (chart with `Chart.yaml`, `values*.yaml`, and templates for the backend, frontend, Postgres, Ingress, HPA and ServiceMonitor)

**Ingress:** `/api` routes to the backend Service on port 8000. `/` routes to the frontend Service on port 80.

**Verified (minikube):**

- `helm lint` passes.
- `helm upgrade --install` succeeds. All five pods are `Running`.
- Through the Ingress: `/api/expenses` creates and reads data, and the stats endpoint returns totals.

**Not verified on EKS:** The Helm deploy to EKS. It needs the cluster and the deploy secret.

**Screenshots:**

> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m8-get-pods.png`] — `kubectl get pods -n expense-tracker`, all `Running`
> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m8-get-svc.png`] — `kubectl get svc -n expense-tracker`
> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m8-helm-list.png`] — `helm list -n expense-tracker`
> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m8-browser-ingress.png`] — application through the Ingress hostname

---

## M9 — Observability (Prometheus and Grafana)

**Files:** `monitoring/prometheus-values.yaml`. The backend exposes `/metrics`. The chart includes a ServiceMonitor, which turns on when the Prometheus Operator CRD is installed.

**Status:** Pending. Install `kube-prometheus-stack`, enable the ServiceMonitor, and create a Grafana panel.

**Screenshots:**

> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m9-metrics.png`] — `curl <backend>/metrics`
> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m9-prometheus-targets.png`] — Prometheus Targets, application `UP`
> [SCREENSHOT PLACEHOLDER: `docs/screenshots/m9-grafana.png`] — Grafana dashboard with live data

---

## M10 — Documentation and Live Demo

**README:** `README.md` describes the application, its architecture, and how to run it.

**Live demo steps:**

1. Commit a visible change to `main`.
2. Watch the GitHub Actions run, including the deploy job.
3. Show the updated deployment in the cluster.

**Status:** Pending. It needs the cluster running at demo time.

---

## Submission checklist

- [x] Repository URL
- [x] `docker compose up --build` runs three services
- [x] At least 4 REST endpoints (9 implemented)
- [x] Alembic migration file present
- [x] Pytest passes (7 tests)
- [x] Backend and frontend Dockerfiles build, as non-root users
- [x] GitHub Actions workflow on push to `main`
- [x] Pytest runs in the pipeline
- [x] Images pushed to GHCR with SHA tags
- [x] Trivy scan in the pipeline
- [x] No secrets committed to Git
- [x] Terraform plan, apply and destroy (VPC and EKS)
- [ ] `kubectl get pods` screenshot (all Running)
- [ ] `helm list` screenshot
- [ ] Application accessible through the Ingress (EKS)
- [ ] `/metrics` screenshot
- [ ] Prometheus Targets screenshot (UP)
- [ ] Grafana dashboard screenshot
- [x] README present
- [ ] Live demo or recording
