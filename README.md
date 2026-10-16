# ExpenseTracker — DevOps Final Capstone

> **Submission guide:** See [PROJECT_SUBMISSION.md](PROJECT_SUBMISSION.md). It maps each `GRADING.md` module to its evidence and screenshots.
> **Demo:** The presentation video and slide deck are in [`demo/`](demo/).

## 1. Project description

ExpenseTracker is a personal expense tracker. A user records each expense with a title, amount, category (`FOOD`, `TRANSPORT`, `BILLS`, `OTHER`), date and an optional note. The dashboard shows the total spent, the number of entries, the food and transport totals, and the three newest expenses. The user can filter the table by category, change an expense's category, and delete an expense.

The project also shows the DevOps path for this application. A commit runs tests, builds and scans container images, and publishes them to a registry. Terraform defines the AWS network and cluster. Helm deploys the app to Kubernetes. Prometheus and Grafana monitor it.

## 2. Architecture

```text
Developer
   |  git push (main)
   v
GitHub Actions
   |-- test:             pytest, frontend build
   `-- build-scan-push:  Docker build -> Trivy scan -> push to GHCR (tag = commit SHA)
   |
   v
GHCR  (expense-tracker-backend, expense-tracker-frontend)
   |
   v
Kubernetes (namespace: expense-tracker, installed with Helm)

  Browser
    |
  Ingress (nginx)
    |-- /      -> frontend Service (port 80)  -> nginx serving the React build
    `-- /api   -> backend Service  (port 8000) -> FastAPI
                                                   |
                                                   v
                                         PostgreSQL (in-cluster, PVC)

  Prometheus (kube-prometheus-stack) --scrapes /metrics--> backend
  Grafana    --queries--> Prometheus
```

Local development uses Docker Compose with the same three services: `postgres`, `backend`, and `frontend`.

AWS infrastructure is defined with Terraform. It creates a VPC and an EKS cluster in `ap-south-1`.

## 3. Tech stack

| Area | Tools |
|------|-------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2, Uvicorn |
| Frontend | React 18+, Vite, plain CSS, nginx (`nginx-unprivileged`) |
| Database | PostgreSQL 16 (`psycopg` driver) |
| Testing | Pytest, FastAPI `TestClient`, SQLite test database |
| Containers | Docker, Docker Compose |
| CI/CD | GitHub Actions, GitHub Container Registry (GHCR) |
| Security | Trivy (HIGH and CRITICAL gate) |
| Infrastructure | Terraform, AWS VPC, AWS EKS (Kubernetes 1.31) |
| Orchestration | Kubernetes, Helm, Ingress (nginx), HPA |
| Observability | Prometheus, Grafana, kube-prometheus-stack, prometheus-fastapi-instrumentator |

## 4. Repository layout

```text
.
├── backend/                  FastAPI app
│   ├── app/                  config, db, models, schemas, main (routes)
│   ├── alembic/              migrations (0001_create_expenses)
│   ├── tests/                pytest suite (test_api.py)
│   ├── Dockerfile            non-root, runs migrations then Uvicorn
│   └── requirements.txt
├── frontend/                 React dashboard (src/main.jsx, styles.css)
│   ├── Dockerfile            Node build stage, nginx runtime stage
│   └── default.conf.template nginx config, proxies /api to the backend
├── docker-compose.yml        local stack: postgres, backend, frontend
├── helm/expense-tracker/     Helm chart (templates, values, values-dev, values-prod)
├── k8s/namespace.yaml        namespace manifest
├── monitoring/               kube-prometheus-stack values
├── terraform/                VPC + EKS (main.tf, variables.tf, outputs.tf, versions.tf)
├── .github/workflows/        ci-cd.yml
├── scripts/load-test.sh      sends traffic to /api/expenses
├── troubleshooting/          two broken manifests for practice
├── demo/                     presentation video and slide deck
└── PROJECT_SUBMISSION.md     evidence map for the grader
```

## 5. Run locally (Docker Compose)

Requirements: Docker Desktop (or Docker Engine with Compose).

```bash
docker compose up --build
```

Open:

| URL | What |
|-----|------|
| `http://localhost:3000` | Dashboard |
| `http://localhost:8000/docs` | FastAPI Swagger UI |
| `http://localhost:8000/health` | Liveness check |
| `http://localhost:8000/metrics` | Prometheus metrics |

Stop the stack:

```bash
docker compose down        # keep the database volume
docker compose down -v     # also delete the database volume
```

### Run the backend without Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL='postgresql+psycopg://expense_tracker:expense_tracker@localhost:5432/expense_tracker'
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Run the tests

```bash
cd backend
pytest -v
```

The tests use SQLite (`backend/test.db`). They never touch PostgreSQL.

## 6. API

| Method | Path | Purpose | Success |
|--------|------|---------|---------|
| GET | `/` | Service name and version | 200 |
| GET | `/health` | Liveness | 200 `{"status":"UP"}` |
| GET | `/ready` | Readiness (database query) | 200 `{"status":"READY"}` |
| GET | `/metrics` | Prometheus metrics | 200 |
| GET | `/api/expenses` | List, newest first | 200 |
| GET | `/api/expenses/stats` | Totals and per-category sums | 200 |
| GET | `/api/expenses/{id}` | One expense | 200, 404 |
| POST | `/api/expenses` | Create | 201, 422 |
| PUT | `/api/expenses/{id}` | Update (all fields optional) | 200, 404, 422 |
| DELETE | `/api/expenses/{id}` | Delete | 204, 404 |

`amount` must be greater than 0. `category` must be one of the four values above.

## 7. Database

Table `expenses`, created by the Alembic migration `backend/alembic/versions/0001_create_expenses.py`:

| Column | Type | Notes |
|--------|------|-------|
| `id` | integer | primary key |
| `title` | varchar(200) | required |
| `amount` | numeric(10,2) | required, stored exactly, returned as a float |
| `category` | varchar(20) | default `OTHER` |
| `spent_on` | date | default today |
| `note` | text | default empty |
| `created_at` | timestamptz | set on insert |

The backend container runs `alembic upgrade head` before it starts Uvicorn.

## 8. CI/CD pipeline

Workflow: `.github/workflows/ci-cd.yml`. It runs on every push and pull request to `main`.

| Job | Steps |
|-----|-------|
| `test` | Install backend requirements, run `pytest`, install frontend packages, run `npm run build` |
| `build-scan-push` (needs `test`) | Log in to GHCR, build both images, scan each with Trivy (`HIGH,CRITICAL`, `ignore-unfixed`, exit code 1 on findings), push both images tagged with `${{ github.sha }}` |

A failing test or a HIGH or CRITICAL finding stops the pipeline before any image is pushed.

**Deployment is manual in this project.** The deploy job was removed. To deploy a pushed commit to a cluster, run `helm upgrade` with the SHA tag (see section 10).

### Trivy fixes made during the build

- Backend: pinned `starlette==1.3.1`, `fastapi==0.136.0`, and `prometheus-fastapi-instrumentator==8.1.0` to clear Starlette CVEs.
- Frontend: moved the runtime image to `nginx-unprivileged:1.29-alpine` and ran `apk upgrade` to clear OpenSSL and c-ares CVEs.

## 9. Terraform (AWS)

Directory: `terraform/`. Region: `ap-south-1`. Terraform 1.x with the AWS provider.

What it creates:

- **VPC** `expense-tracker-vpc` (module `terraform-aws-modules/vpc/aws` 5.8.1): CIDR `10.20.0.0/16`, 2 availability zones (`ap-south-1a`, `ap-south-1b`), 2 public subnets and 2 private subnets, one NAT gateway.
- **EKS cluster** `expense-tracker-eks` (module `terraform-aws-modules/eks/aws` 20.37.1): Kubernetes 1.31, public API endpoint, private worker subnets.
- **Managed node group** `main`: 2 × `t3.medium`, scales from 2 to 4.

Commands:

```bash
cd terraform
terraform init
terraform plan  -var-file="terraform.tfvars.example"
terraform apply -var-file="terraform.tfvars.example"
terraform destroy -var-file="terraform.tfvars.example"
```

`terraform.tfvars.example` holds placeholder values only. Keep real values in a `terraform.tfvars` file that Git ignores.

Connect `kubectl` to the cluster:

```bash
aws eks update-kubeconfig --region ap-south-1 --name expense-tracker-eks
```

Destroy the stack after use. The EKS control plane and NAT gateway cost money while they run.

## 10. Kubernetes and Helm

Namespace: `k8s/namespace.yaml` (`expense-tracker`).

Chart: `helm/expense-tracker/`.

| Resource | Details |
|----------|---------|
| Backend Deployment and Service | Port 8000, probes on `/ready` and `/health`, 2 replicas by default |
| Frontend Deployment and Service | Port 8080 in the container, Service port 80, 2 replicas by default |
| PostgreSQL Deployment, Service, PVC | Single replica, 5 GiB volume, credentials in a Secret |
| Ingress | `/api` → backend 8000, `/` → frontend 80, class `nginx` |
| HPA | Backend, 2 to 6 replicas, 60% CPU target (disabled in `values-dev.yaml`) |
| ServiceMonitor | Scrapes `/metrics` on the backend |

Deploy a commit to a cluster (replace `<SHA>` with the commit's full SHA):

```bash
kubectl apply -f k8s/namespace.yaml
helm upgrade --install expense-tracker ./helm/expense-tracker \
  -n expense-tracker \
  -f helm/expense-tracker/values-dev.yaml \
  --set backend.image=ghcr.io/rishi-harti768/expense-tracker-backend --set backend.tag=<SHA> \
  --set frontend.image=ghcr.io/rishi-harti768/expense-tracker-frontend --set frontend.tag=<SHA> \
  --wait
```

Check the release:

```bash
helm list -n expense-tracker
kubectl get pods -n expense-tracker
kubectl get svc -n expense-tracker
kubectl get hpa -n expense-tracker
```

Dev values use the host `expense-tracker.local`. On a local cluster, map that name to the Ingress address in your hosts file. On EKS, pass the load balancer hostname with `--set ingress.host=<HOST>` and enable the ServiceMonitor only if the Prometheus CRDs are installed.

Local test cluster used for this project: minikube with the `ingress-nginx` addon.

## 11. Observability

- The backend exports Prometheus metrics at `/metrics` using `prometheus-fastapi-instrumentator`.
- `monitoring/prometheus-values.yaml` configures `kube-prometheus-stack`. Install it:

  ```bash
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
    -n monitoring --create-namespace -f monitoring/prometheus-values.yaml --wait
  ```

- The chart's ServiceMonitor tells Prometheus to scrape the backend every 15 seconds.
- Grafana has a dashboard named **ExpenseTracker HTTP** with two panels: requests per second, and requests per second by handler. The queries are:

  ```text
  sum(rate(http_requests_total{namespace="expense-tracker"}[2m]))
  sum by (handler) (rate(http_requests_total{namespace="expense-tracker"}[2m]))
  ```

  The dashboard was created in the running Grafana instance. It is not stored as a file in this repository.

Access the tools with port-forwards:

```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80
```

## 12. Verified results

| Area | Result |
|------|--------|
| Backend tests | 7 of 7 pass (Python 3.12 container) |
| Docker Compose | `postgres`, `backend` and `frontend` start. Migration runs. CRUD works through port 3000. |
| CI | `test` and `build-scan-push` jobs pass on `main` |
| Trivy | Backend and frontend images pass with no HIGH or CRITICAL fixable findings |
| Terraform | `plan` shows 54 resources. `apply` creates the VPC and EKS cluster. Both nodes reach Ready. `destroy` completes. |
| Helm | `helm lint` passes. The release deploys to minikube, and all pods run. |
| Prometheus | Both backend pods are `UP` as targets |
| Grafana | Both dashboard panels show live request data |

## 13. Known issues and limitations

- **No automated deployment.** The deploy job was removed from the pipeline. Deployment is a manual `helm upgrade`. ArgoCD (GitOps) is not set up.
- **Secrets in values.** The PostgreSQL password is a plain value in `values.yaml`. It is acceptable for a classroom demo and must not be reused anywhere else.
- **Single PostgreSQL replica.** The database runs in the cluster with one replica and one volume. There is no backup or failover.
- **Backend restarts on first start.** If PostgreSQL is not ready, the backend exits and Kubernetes restarts it. It recovers on the next attempt. An init container that waits for PostgreSQL would remove the restarts.
- **Grafana dashboard is not in the repo.** Recreate it from the queries in section 11.
- **Local hostname.** `expense-tracker.local` must be mapped to the cluster address on your machine.
- **Test database file.** `backend/test.db` is kept between runs. The stats test uses before and after values, so it does not depend on a clean file.
- **Single NAT gateway.** Lower cost, but one Availability Zone failure removes outbound internet access for private subnets.

## 14. Contributing and branches

Work on `main`. Commit with a short description of the change. Each push runs the pipeline.
