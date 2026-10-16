# Screenshot Runbook

This runbook gives the steps to produce each screenshot in `PROJECT_SUBMISSION.md`. Follow the order. Save each image to `docs/screenshots/` with the file name shown. Then replace the matching placeholder in `PROJECT_SUBMISSION.md`.

## 0. Before you start

Check these items first.

| Check | Command | Expected |
|-------|---------|----------|
| Docker Desktop runs | `docker info` | Server version is shown |
| Repo is clean | `git status` | Nothing to commit |
| Latest commits are pushed | `git log origin/main..main` | No output |
| minikube runs | `minikube status` | `host: Running`, `apiserver: Running` |
| kubectl uses minikube | `kubectl config use-context minikube` | `Switched to context "minikube"` |

Create the screenshot folder:

```powershell
New-Item -ItemType Directory -Force docs/screenshots
```

Use the Windows Snipping Tool (Win + Shift + S) for browser shots. Use a full terminal window for command output.

**Port-forward rule:** A port-forward command stays in the foreground. Open a new terminal for each one. Close it with Ctrl+C when you finish.

---

## Part 1 — Local screenshots (no AWS needed)

### M1 — Running application in the browser

**File:** `m1-app-browser.png`

1. Start the stack:

   ```powershell
   docker compose down -v
   docker compose up --build -d
   docker compose ps
   ```

2. Wait until `postgres` shows `healthy`.
3. Open `http://localhost:3000`.
4. Click **New expense**. Add one entry. For example: title `Groceries`, amount `42.50`, category `FOOD`.
5. Capture the dashboard. The stat cards and the table must show the entry.

### M2 — Pytest output

**File:** `m2-pytest.png`

Run the tests in the Python 3.12 container. Your local Python 3.14 cannot install the pinned `psycopg-binary`.

```powershell
docker run --rm -v "${PWD}/backend:/app" -w /app -e PYTHONDONTWRITEBYTECODE=1 python:3.12-slim sh -c "pip install -q -r requirements.txt && rm -f test.db && pytest -v"
```

Capture the terminal. It must show `7 passed` and the test names.

### M3 — Commit history

**File:** `m3-commits.png`

Run this in the repo:

```powershell
git log --oneline --decorate -n 20
```

Capture the terminal. It must show at least 10 commits. Then open the GitHub repository commits page in the browser and capture it too. Save it as `m3-commits-github.png`.

### M4 — Docker Compose and browser

**Files:** `m4-compose-up.png`, `m4-browser-3000.png`

1. Capture the terminal output of `docker compose up --build`. Use a fresh stack from Part 1, step M1. The output must show the three services being built and started.
2. Capture `docker compose ps`. It must show `postgres`, `backend`, and `frontend` as running.
3. Capture the browser at `http://localhost:3000` with the application loaded. Save it as `m4-browser-3000.png`.

### M6 — Trivy scan output

**File:** `m6-trivy.png`

Trivy output comes from a pipeline run, so use Part 2, step M5.

Locally, you can also capture the scan:

```powershell
docker build -t expense-tracker-backend:scan ./backend
docker run --rm -v //var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 expense-tracker-backend:scan
echo "trivy exit=$LASTEXITCODE"
```

Run each line on its own. Do not paste the lines as one line. Expected result: `trivy exit=0`.

Capture the output. The exit code must be 0. Use the GitHub run for the official evidence.

---

## Part 2 — GitHub screenshots

### M5 — Green pipeline run and GHCR packages

**Files:** `m5-actions-green.png`, `m5-ghcr-packages.png`, `m6-trivy.png`

1. Open `https://github.com/rishi-harti768/expense-tracker-devops/actions`.
2. Open the latest run on `main`.
3. Capture the run summary. The `test` and `build-scan-push` jobs must show green checks. Save it as `m5-actions-green.png`.
4. Open the `build-scan-push` job. Expand **Scan backend** and **Scan frontend**. Capture the Trivy output. Save it as `m6-trivy.png`.
5. Open `https://github.com/users?tab=packages` (or your profile, then **Packages**). Open `expense-tracker-backend` and `expense-tracker-frontend`. Capture the tags list. The tags must show commit SHAs. Save it as `m5-ghcr-packages.png`.

**Important:** The `deploy` job is part of the same run. If it is red, the summary is not all green. Decide before you capture (see Part 3).

### M10 — Live demo recording (also needs Part 3)

**File:** `m10-demo-pipeline.png` (optional)

Make a small visible change, commit it, and push it. Capture the Actions run as it starts. Then capture the deployment update. See Part 3, step 4.

---

## Part 3 — Minikube screenshots for M8 and M9

These screenshots use the minikube cluster. The chart is already installed there.

### M8 — Kubernetes and Helm

**Files:** `m8-get-pods.png`, `m8-get-svc.png`, `m8-helm-list.png`, `m8-browser-ingress.png`

1. Check the release:

   ```powershell
   kubectl config use-context minikube
   helm list -n expense-tracker
   ```

   Capture `helm list`. Save it as `m8-helm-list.png`.

2. Capture the pods and Services:

   ```powershell
   kubectl get pods -n expense-tracker
   kubectl get deploy -n expense-tracker
   kubectl get svc -n expense-tracker
   ```

   - `m8-get-pods.png`: all pods must show `Running`.
   - `m8-get-svc.png`: the Services must show ClusterIP.
   - The Deployments must show `2/2` for the backend and the frontend.

3. Open the Ingress through a port-forward. Run this in its own terminal:

   ```powershell
   kubectl -n ingress-nginx port-forward svc/ingress-nginx-controller 8080:80
   ```

4. Add a hosts-file entry. Open Notepad as Administrator and edit `C:\Windows\System32\drivers\etc\hosts`. Add this line:

   ```text
   127.0.0.1 expense-tracker.local
   ```

5. Open `http://expense-tracker.local:8080` in the browser. Create an expense. Capture the page. Save it as `m8-browser-ingress.png`.

6. Remove the hosts-file line when you finish.

### M9 — Prometheus and Grafana

**Files:** `m9-metrics.png`, `m9-prometheus-targets.png`, `m9-grafana.png`

1. Generate traffic. Run this after the port-forward in step M8.3 is active:

   ```powershell
   1..50 | ForEach-Object { curl.exe -s -o NUL -H "Host: expense-tracker.local" http://localhost:8080/api/expenses }
   ```

2. Capture the metrics. Open a port-forward for the backend in its own terminal:

   ```powershell
   kubectl -n expense-tracker port-forward svc/expense-tracker-backend 8000:8000
   ```

   In another terminal:

   ```powershell
   curl.exe http://localhost:8000/metrics | Select-Object -First 30
   ```

   Capture the terminal. Save it as `m9-metrics.png`. The output must show `http_requests_total` lines.

3. Capture Prometheus targets. Open a port-forward:

   ```powershell
   kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
   ```

   Open `http://localhost:9090/targets`. Search for `expense-tracker`. Both backend targets must show `UP`. Capture the page. Save it as `m9-prometheus-targets.png`.

4. Capture the Grafana dashboard. Open a port-forward:

   ```powershell
   kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80
   ```

   Get the admin password:

   ```powershell
   kubectl -n monitoring get secret kube-prometheus-stack-grafana -o jsonpath="{.data.admin-password}"
   ```

   Decode it. In PowerShell:

   ```powershell
   [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("<paste value here>"))
   ```

   Open `http://localhost:3001`. Log in as `admin` with the decoded password. Open the dashboard **ExpenseTracker HTTP**. Generate more traffic (step 1). Wait 30 seconds. Capture the dashboard. Save it as `m9-grafana.png`.

   The dashboard was created with the Grafana API. It is not in the repo. If you recreate minikube, you must create it again.

---

## Part 4 — AWS screenshots (M7, and M8 on EKS)

Use this part only if you choose the AWS path. Each step costs money until you run `terraform destroy`.

**Order:** Apply, screenshot, then destroy.

### M7 — Terraform plan, console, and destroy

**Files:** `m7-plan.png`, `m7-console-vpc-eks.png`, `m7-destroy.png`

1. Refresh AWS access:

   ```powershell
   aws login
   ```

2. Plan, then capture the output. Save it as `m7-plan.png`:

   ```powershell
   cd terraform
   terraform init
   terraform plan -var-file=terraform.tfvars.example
   ```

   The output must end with `Plan: 54 to add, 0 to change, 0 to destroy`.

3. Apply:

   ```powershell
   terraform apply -var-file=terraform.tfvars.example
   ```

   Type `yes` when asked. The apply takes about 20 to 25 minutes.

4. Capture the AWS Console. Open the **VPC** service in region `ap-south-1` and show the `expense-tracker-vpc`. Then open **EKS**, select `expense-tracker-eks`, and show `Active`. Save it as `m7-console-vpc-eks.png`.

5. Run the M8 steps on EKS (below). Capture them before you destroy.

6. Destroy and capture:

   ```powershell
   terraform destroy -var-file=terraform.tfvars.example
   ```

   Type `yes` when asked. Capture the final line that says `Destroy complete!`. Save it as `m7-destroy.png`.

### M8 on EKS — Ingress through the cluster load balancer

Run this after the apply in Part 4, step 3. This step gives the strongest M8 evidence.

1. Connect kubectl to the cluster:

   ```powershell
   aws eks update-kubeconfig --region ap-south-1 --name expense-tracker-eks --alias expense-tracker-eks
   kubectl config use-context expense-tracker-eks
   kubectl get nodes
   ```

   Both nodes must show `Ready`.

2. Install the Ingress controller:

   ```powershell
   helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
   helm repo update
   helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace --wait
   ```

3. Get the load balancer hostname. It can take a few minutes:

   ```powershell
   kubectl -n ingress-nginx get svc ingress-nginx-controller
   ```

   Copy the value under `EXTERNAL-IP`.

4. Deploy the chart. Replace the image tag with the commit SHA of the image that CI pushed. Replace the host with the load balancer hostname:

   ```powershell
   helm upgrade --install expense-tracker ./helm/expense-tracker -n expense-tracker --create-namespace -f helm/expense-tracker/values-dev.yaml --set backend.image=ghcr.io/rishi-harti768/expense-tracker-backend --set backend.tag=<SHA> --set frontend.image=ghcr.io/rishi-harti768/expense-tracker-frontend --set frontend.tag=<SHA> --set ingress.host=<EXTERNAL-IP> --set monitoring.serviceMonitor.enabled=false --wait --timeout 8m
   ```

   The images must exist in GHCR. Check the tags in the M5 GHCR screenshot.

5. Capture the M8 evidence on EKS. Use the same captures as Part 3, step M8.2 and `helm list`. Save them with the same file names.

6. Capture the browser at `http://<EXTERNAL-IP>/`. Save it as `m8-browser-ingress.png`. Use the same file name as Part 3 for the final version, or keep both.

### M9 on EKS (optional)

M9 is complete on minikube. If you want M9 evidence on the same cluster as M8, install the Prometheus stack on EKS:

```powershell
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack -n monitoring --create-namespace -f monitoring/prometheus-values.yaml --wait --timeout 15m
helm upgrade expense-tracker ./helm/expense-tracker -n expense-tracker -f helm/expense-tracker/values-dev.yaml --set backend.image=ghcr.io/rishi-harti768/expense-tracker-backend --set backend.tag=<SHA> --set frontend.image=ghcr.io/rishi-harti768/expense-tracker-frontend --set frontend.tag=<SHA> --set ingress.host=<EXTERNAL-IP> --wait
```

Then repeat the Part 3, M9 steps.

---

## Part 5 — Live demo (M10, needs a deploy path)

The deploy job runs `helm upgrade --install` with cluster credentials. It fails without the `KUBE_CONFIG_DATA` secret. Choose one path before the demo.

**Option A: Remove the deploy job.** Then the pipeline is green. You lose the 3 points for "see the deployment update" in the pipeline. You can still show a manual `helm upgrade`.

**Option B: Keep the deploy job.** Create the secret and runner access before the demo. Then run the steps below.

Demo steps:

1. Make a small visible change. For example, change the subtitle text in `frontend/src/main.jsx`.
2. Commit and push:

   ```powershell
   git add frontend/src/main.jsx
   git commit -m "feat: update dashboard subtitle"
   git push origin main
   ```

3. Open the Actions run. Capture the `test`, `build-scan-push`, and `deploy` jobs. Save it as `m10-demo-pipeline.png`.
4. After the deploy job finishes, reload the application URL. Capture the changed text. Save it as `m10-demo-updated.png`.

---

## Final checklist

Check each file in `docs/screenshots/` before you submit.

| File | Module | Source |
|------|--------|--------|
| `m1-app-browser.png` | M1 | Part 1, M1 |
| `m2-pytest.png` | M2 | Part 1, M2 |
| `m3-commits.png` | M3 | Part 1, M3 |
| `m3-commits-github.png` | M3 | Part 1, M3 |
| `m4-compose-up.png` | M4 | Part 1, M4 |
| `m4-browser-3000.png` | M4 | Part 1, M4 |
| `m5-actions-green.png` | M5 | Part 2, M5 |
| `m5-ghcr-packages.png` | M5 | Part 2, M5 |
| `m6-trivy.png` | M6 | Part 2, M5 |
| `m7-plan.png` | M7 | Part 4 |
| `m7-console-vpc-eks.png` | M7 | Part 4 |
| `m7-destroy.png` | M7 | Part 4 |
| `m8-get-pods.png` | M8 | Part 3 or Part 4 |
| `m8-get-svc.png` | M8 | Part 3 or Part 4 |
| `m8-helm-list.png` | M8 | Part 3 or Part 4 |
| `m8-browser-ingress.png` | M8 | Part 3 or Part 4 |
| `m9-metrics.png` | M9 | Part 3 |
| `m9-prometheus-targets.png` | M9 | Part 3 |
| `m9-grafana.png` | M9 | Part 3 |
| `m10-demo-pipeline.png` | M10 | Part 5 |
| `m10-demo-updated.png` | M10 | Part 5 |

After you save the files, update `PROJECT_SUBMISSION.md`. Replace each placeholder with `![caption](docs/screenshots/<file>)`.

## Notes

- Do not commit `terraform.tfvars` or any AWS keys.
- Do not commit the Grafana password.
- Destroy the AWS stack as soon as you finish Part 4.
