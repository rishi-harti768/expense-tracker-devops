# Screenshot Guide: Remaining Items

This guide covers the screenshots still missing from `PROJECT_SUBMISSION.md`. Use minikube for all Kubernetes evidence. The AWS stack is destroyed, so do not apply Terraform again for these shots.

Save every image in `docs/screenshots/` with the file name shown.

## 0. Current state

| Module | Screenshot | Status |
|--------|-----------|--------|
| M1 | `m1-app-browser.png` | Done |
| M2 | `m2-pytest.png` | Done |
| M3 | `m3-commits.png`, `m3-commits-github.png` | `m3-commits.png` done. `m3-commits-github.png` pending. |
| M4 | `m4-compose-up.png`, `m4-browser-3000.png` | Done |
| M5 | `m5-actions-green.png` | **Pending.** The deploy job is red. See section 4. |
| M5 | `m5-ghcr-packages.png` | Done |
| M6 | `m6-trivy.png` | Done |
| M7 | `m7-plan.png`, `m7-console-vpc-eks.png`, `m7-destroy.png` | Done |
| M8 | `m8-get-pods.png`, `m8-get-svc.png`, `m8-helm-list.png`, `m8-browser-ingress.png` | **Pending.** Section 2. |
| M9 | `m9-metrics.png`, `m9-prometheus-targets.png`, `m9-grafana.png` | **Pending.** Section 3. |
| M10 | `m10-demo-pipeline.png`, `m10-demo-updated.png` | Pending. Needs the deploy path. Section 5. |

## 1. Preflight

Run these checks in PowerShell:

```powershell
cd X:\repos\expense-tracker
minikube status
kubectl config use-context minikube
kubectl get nodes
helm list -n expense-tracker
kubectl get pods -n expense-tracker
kubectl get pods -n monitoring
```

Expected:

- `host: Running`, `apiserver: Running`.
- The node `minikube` shows `Ready`.
- The `expense-tracker` release shows `deployed`.
- All 5 app pods show `Running`.

If a check fails, stop and fix it before you take any screenshot.

## 2. M8 — Kubernetes and Helm

**Files:** `m8-helm-list.png`, `m8-get-pods.png`, `m8-get-svc.png`, `m8-browser-ingress.png`

### 2.1 Helm release

```powershell
helm list -n expense-tracker
```

Capture the terminal. Save it as `m8-helm-list.png`.

### 2.2 Pods, Deployments and Services

```powershell
kubectl get pods -n expense-tracker
kubectl get deploy -n expense-tracker
kubectl get svc -n expense-tracker
```

- `m8-get-pods.png`: capture the pods output. All pods must show `Running`.
- `m8-get-svc.png`: capture the Services output. The Services must show `ClusterIP`.
- The Deployments must show `2/2` for the backend and the frontend. If you capture only the pods, include the Deployments in the same screenshot.

### 2.3 Ingress in the browser

1. Open a new PowerShell window and keep it open:

   ```powershell
   kubectl -n ingress-nginx port-forward svc/ingress-nginx-controller 8080:80
   ```

2. Add a hosts-file entry. Open Notepad as Administrator. Open `C:\Windows\System32\drivers\etc\hosts`. Add this line at the end:

   ```text
   127.0.0.1 expense-tracker.local
   ```

3. Open `http://expense-tracker.local:8080` in the browser.
4. Add one expense through the form. Capture the page with the new row. Save it as `m8-browser-ingress.png`.
5. Remove the hosts-file line when you finish. Close the port-forward window.

Use the browser address bar in the screenshot. It must show `expense-tracker.local:8080`.

## 3. M9 — Prometheus and Grafana

**Files:** `m9-metrics.png`, `m9-prometheus-targets.png`, `m9-grafana.png`

### 3.1 Generate traffic

Run this with the ingress port-forward from section 2.3 still open:

```powershell
1..50 | ForEach-Object { curl.exe -s -o NUL -H "Host: expense-tracker.local" http://localhost:8080/api/expenses }
```

### 3.2 Metrics endpoint

1. Open a new PowerShell window and keep it open:

   ```powershell
   kubectl -n expense-tracker port-forward svc/expense-tracker-backend 8000:8000
   ```

2. In another PowerShell window:

   ```powershell
   curl.exe http://localhost:8000/metrics | Select-Object -First 30
   ```

3. Capture the terminal. The output must show `http_requests_total` lines. Save it as `m9-metrics.png`.

### 3.3 Prometheus targets

1. Open a new PowerShell window and keep it open:

   ```powershell
   kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
   ```

2. Open `http://localhost:9090/targets` in the browser.
3. Search for `expense-tracker`. Both backend targets must show `UP`.
4. Capture the page. Save it as `m9-prometheus-targets.png`.

### 3.4 Grafana dashboard

1. Open a new PowerShell window and keep it open:

   ```powershell
   kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80
   ```

2. Get the admin password. It is stored base64 encoded:

   ```powershell
   kubectl -n monitoring get secret kube-prometheus-stack-grafana -o jsonpath="{.data.admin-password}"
   ```

3. Decode it. Paste the value from step 2 in place of `<VALUE>`:

   ```powershell
   [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("<VALUE>"))
   ```

4. Open `http://localhost:3001`. Log in as `admin` with the decoded password.
5. Open the dashboard **ExpenseTracker HTTP**. It has two panels: requests per second, and requests per second by handler.
6. Run the traffic command from section 3.1 again. Wait 30 seconds.
7. Capture the dashboard with both panels showing data. Save it as `m9-grafana.png`.

If the dashboard is missing, the cluster was rebuilt. Create a new dashboard with this query in a time-series panel:

```text
sum(rate(http_requests_total{namespace="expense-tracker"}[2m]))
```

## 4. M5 — GitHub Actions green run

**File:** `m5-actions-green.png`

The latest run is red. The deploy job fails because the repo has no `KUBE_CONFIG_DATA` secret and no live cluster. The `test` and `build-scan-push` jobs pass. You must choose one path before you take this screenshot.

**Option A — Remove the deploy job (recommended for a clean green run).** The workflow then has two jobs. Both pass. The M5 green screenshot is clean. You lose the M10 "deployment update" step from the pipeline. You can still show `helm upgrade` by hand on minikube.

**Option B — Keep the deploy job.** The run stays red unless you add cluster access and a live cluster for the runner. Capture the red run and explain it in `PROJECT_SUBMISSION.md`. This is not a full M5 green.

After you choose and push, wait for the run to finish. Then:

1. Open `https://github.com/rishi-harti768/expense-tracker-devops/actions`.
2. Open the latest run on `main`.
3. Capture the run summary. Save it as `m5-actions-green.png`.

Also capture `m3-commits-github.png` from the GitHub commits page while you are on GitHub.

## 5. M10 — Live demo (optional for screenshots)

Only do this after section 4 uses Option B. Skip it with Option A.

1. Make a small visible change. For example, change a subtitle in `frontend/src/main.jsx`.
2. Commit and push.
3. Capture the Actions run as it starts. Save it as `m10-demo-pipeline.png`.
4. After the deploy job finishes, capture the changed page. Save it as `m10-demo-updated.png`.

## 6. Finish

1. Confirm the new files exist:

   ```powershell
   Get-ChildItem docs/screenshots
   ```

2. In `PROJECT_SUBMISSION.md`, replace each remaining placeholder with `![caption](docs/screenshots/<file>)`. Each placeholder looks like `> [SCREENSHOT PLACEHOLDER: ...]`.
3. Commit the screenshots and the updated submission file together.

## Notes

- Do not commit the Grafana password, AWS keys, or `terraform.tfvars`.
- Do not commit `terraform/tfplan`.
- Stop the port-forward windows when you finish.
