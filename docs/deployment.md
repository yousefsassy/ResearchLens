# Oracle ARM + Streamlit deployment runbook

This remains the alternative two-service hosting mode. For standalone Community
Cloud without an Oracle account, see [the standalone guide](streamlit_cloud.md).

Prepared on `feature/deployment`, 2 November 2026. **No VM, DNS record, certificate,
public endpoint or cloud deployment has been created.** All values in angle brackets
must be supplied by the administrator. Commands below are manual future steps.

Architecture: browser → Streamlit Community Cloud → HTTPS/Caddy → loopback FastAPI
(one Uvicorn worker/systemd) → unchanged BM25 + BGE + NumPy/RRF → OpenAI.
The frontend never loads BGE or OpenAI credentials. Hosting may be free; generation
is billable. The old readiness assessment is background; use this runbook and the
checked-in deployment scripts for provisioning.

## 1. Oracle requirements and console steps

- Home-region **VM.Standard.A1.Flex**, Ubuntu 24.04 LTS **aarch64**, **2 OCPUs,
  4 GB RAM**, a 50 GB boot volume, public IPv4. Keep total tenancy usage within the
  current Always Free allowance. This is a proposed allocation, not a measured ARM
  capacity guarantee. Do not select x86 E2 or a paid shape as an automatic fallback.
- [Oracle's current Always Free allowance](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
  is 1,500 OCPU hours and 9,000 GB hours monthly (2 OCPUs/12 GB for Always Free
  tenancies); aggregate boot/block storage is limited too. Check the console's free
  labels and your existing allocations. Capacity is not guaranteed; idle VMs may
  be reclaimed. Retain the artifact archive and feedback backups on your laptop.
- In OCI: Compute → Instances → Create; select the home region/compartment, Ubuntu
  ARM image and A1 Flex shape above. Choose/create a VCN, public subnet, internet
  gateway and route `0.0.0.0/0` to that gateway; assign a public IP. Upload your SSH
  **public** key; keep the private key on the laptop.
- In the VM's network security group or subnet security list, allow TCP 22 only
  from `<YOUR_PUBLIC_IP>/32`; allow TCP 80 and 443 from the internet. Do **not** add
  ingress for 8000 or 8501. Preserve stateful egress for DNS, HTTPS package downloads
  and OpenAI. If enabling IPv6, configure equivalent rules or omit the DNS AAAA.
- Obtain a DNS name `<API_HOSTNAME>` you control and point its A record at
  `<ORACLE_PUBLIC_IP>`. Avoid stale AAAA records. A hostname/domain is not supplied
  by this repository; DNS and reachable ports 80/443 are prerequisites for TLS.

Native dependencies have CPython 3.11-compatible ARM wheels (57-package metadata
check, CPU torch checked separately). That does not prove an ARM installation.
The server checks below remain mandatory. Local warm retrieval previously used
about 617 MiB RSS on x86; allow extra room for tokenizer/startup/concurrent HTTP.
Keep one worker and serialized generation. Do not copy the laptop virtualenv.

## 2. Laptop: freeze and transfer runtime artifacts

Use the working repository with the agreed corpus/index and cached BGE snapshot:

```bash
cd /home/asma/Documents/ResearchLens
git switch feature/deployment
git pull --ff-only origin feature/deployment
.venv/bin/python scripts/runtime_artifacts.py check
# Choose a fresh archive name; pack refuses to overwrite an existing archive.
.venv/bin/python scripts/runtime_artifacts.py pack --archive tmp/researchlens-runtime-v1.tar.gz
cat tmp/researchlens-runtime-v1.tar.gz.sha256
ssh -i '<SSH_PRIVATE_KEY_PATH>' ubuntu@<ORACLE_PUBLIC_IP>
# Verify the SSH host key using the OCI instance/console details before accepting.
# Back in the laptop terminal:
scp -i '<SSH_PRIVATE_KEY_PATH>' tmp/researchlens-runtime-v1.tar.gz ubuntu@<ORACLE_PUBLIC_IP>:/tmp/
```

Record the SHA256 printed by `pack` in a trusted location. Checksums detect damage;
SSH authenticates transfer. Do not trust a checksum fetched from an untrusted
location alongside a replacement archive. The `.sha256` sidecar is informational;
restore explicitly requires the trusted hash.

The bundle whitelists only these paths, plus `MANIFEST.json` with per-file SHA256:

```text
data/processed/chunks.jsonl
data/indexes/embeddings.npy
data/indexes/index_metadata.json
.cache/huggingface/models--BAAI--bge-small-en-v1.5/
```

The actual laptop `.cache/huggingface` points into RAM. Packaging follows that
outer link and dereferences snapshot-to-blob file links into regular archive
members. Internal directory links and escaping links are rejected. Only the pinned
snapshot and cache refs/blobs are allowed. No `.env`, credentials, venv, Git data,
PDFs, feedback or benchmark runs are included. Paper metadata comes from Git.
The archive is ignored under `tmp/`; it is not committed or pushed to GitHub.

Identity: 1,001 × 384 normalized float32 index, corpus fingerprint
`3bd5c264d591d8c386c7859fc61c4cfe127e0b288c3c6622bcd738d4c3980c83`,
model `BAAI/bge-small-en-v1.5`, revision
`5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`.
NumPy [NPY files are portable data](https://numpy.org/doc/stable/reference/generated/numpy.lib.format.html),
as are model Safetensors/tokenizer files; native wheels must match ARM.

## 3. Oracle SSH: OS, user, Git and Python dependencies

Run the following on the **future Oracle VM**, logged in as `ubuntu`:

```bash
uname -m                         # must report aarch64
sudo apt-get update
sudo apt-get install -y git curl ca-certificates libgomp1 python3-venv ufw \
  debian-keyring debian-archive-keyring apt-transport-https gnupg
sudo useradd --system --create-home --home-dir /var/lib/researchlens \
  --shell /bin/bash researchlens
sudo install -d -o researchlens -g researchlens -m 0755 /srv/ResearchLens
sudo install -d -o researchlens -g researchlens -m 0750 /var/lib/researchlens
sudo install -d -o root -g root -m 0700 /etc/researchlens
sudo -u researchlens -H git clone --branch feature/deployment --single-branch \
  https://github.com/yousefsassy/ResearchLens.git /srv/ResearchLens
```

If the repository is private, configure a **read-only GitHub deploy key** for the
application user and clone via SSH instead; never copy your personal private key
to the VM or embed tokens in clone URLs. `/srv/ResearchLens` must be empty for clone.
The system user may already exist on a repeat provisioning; inspect rather than
recreate/overwrite it. Record the deployed commit with `git rev-parse HEAD`.

Ubuntu 24.04 may not provide Python 3.11 in its default repositories. Install
pinned `uv` as an isolated bootstrap tool (not part of application requirements):

```bash
sudo python3 -m venv /opt/researchlens-bootstrap
sudo /opt/researchlens-bootstrap/bin/pip install 'uv==0.13.6'
sudo ln -s /opt/researchlens-bootstrap/bin/uv /usr/local/bin/uv
sudo -u researchlens -H bash -c 'cd /srv/ResearchLens && bash scripts/setup_oracle_backend.sh'
```

The script requires ARM/non-root, refuses an existing `.venv`, uses managed **3.11.17** (downloaded if absent) in
`/srv/ResearchLens/.python`, creates
`.venv`, installs pinned CPU torch from the official CPU index, then the pinned
backend runtime closure, verifies imports and runs `pip check`. Managed Python is
kept outside `/home` so systemd's `ProtectHome` does not hide its executable.
See [uv Python provisioning](https://docs.astral.sh/uv/guides/install-python/) and
the [official CPU torch index](https://download.pytorch.org/whl/cpu/torch/).
No source builds, CUDA packages, index regeneration or OpenAI calls are requested.
If any wheel is missing, stop and review the exact resolver error rather than
substituting an unpinned model or GPU torch. Keep `pip freeze` for the server record.

## 4. Oracle SSH: verify and restore the artifact bundle

```bash
cd /srv/ResearchLens
# Substitute the full 64-character SHA256 recorded on your laptop.
# Verification/restore use stdlib only and do not load OpenAI.
sudo -u researchlens .venv/bin/python scripts/runtime_artifacts.py verify \
  --archive /tmp/researchlens-runtime-v1.tar.gz --sha256 <TRUSTED_ARCHIVE_SHA256>
sudo -u researchlens .venv/bin/python scripts/runtime_artifacts.py restore \
  --archive /tmp/researchlens-runtime-v1.tar.gz --sha256 <TRUSTED_ARCHIVE_SHA256>
sudo -u researchlens env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=2 \
  .venv/bin/python scripts/runtime_artifacts.py check
.venv/bin/python -m pip check
```

Restore validates the outer archive hash, allowed paths, regular-file types,
required model files and every file hash **before extraction**. It refuses
symlink destinations and differing existing artifacts; matching restores are
idempotent. For updates, stop the backend and back up the old bundle/artifacts
before restoring a coherent new set. Do not overwrite a live mixed corpus/index.
`check` verifies the canonical fingerprint, index's embedded checksums/model/
ordered IDs, loads the cached model offline and runs filtered hybrid retrieval.
It must pass on **ARM** before continuing. It never calls OpenAI or builds vectors.
The x86 transfer/restore check passed locally; target ARM remains unexecuted.

Artifacts live on persistent boot/block storage, not `/tmp` or RAM. Only the upload
archive is staged in `/tmp`. Startup loads these prebuilt files, warms BGE once and
builds BM25 in memory once. It does not rebuild embeddings or download the model.
If you mount a separate volume at `/srv` or `/var/lib/researchlens`, configure its
mount in `/etc/fstab` before enabling services and back it up.

## 5. Secrets, budget and systemd

Generate a strong shared API token on the laptop without putting it in shell
history (display locally only, store it in a password manager):

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Choose a **different** attendee demo passcode. Do not reuse the OpenAI key as either
secret. The shared token stays between the Streamlit server and Oracle, never in a
browser URL/header. Only the attendee passcode is entered in the browser.

On Oracle:

```bash
sudo install -m 0600 -o root -g root deploy/backend.env.example /etc/researchlens/backend.env
sudoedit /etc/researchlens/backend.env
# Fill OPENAI_API_KEY and RESEARCHLENS_API_TOKEN (at least 32 characters).
# Keep REQUIRE_AUTH=true and persistent /var/lib/researchlens paths.
sudo install -m 0644 deploy/researchlens.service /etc/systemd/system/researchlens.service
sudo systemd-analyze verify /etc/systemd/system/researchlens.service
sudo systemctl daemon-reload
sudo systemctl enable --now researchlens
sudo systemctl status researchlens --no-pager
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/papers
# Expected 401; no generation is called:
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' -d '{"question":"How does SelfCheckGPT work?"}'
```

systemd loads the root-owned environment file before changing to the non-root
application user. The service is loopback-only, one worker, auto-restarting, with
read-only system/app files and writable `/var/lib/researchlens`; offline model
settings and two CPU threads are explicit. `--no-access-log` avoids question URL
logging; no auth values or raw provider errors are logged by the added code.
Do not enable request-body/header debug logging at Caddy or the application.

Demo controls apply globally to all visitors:

- `/health` and `/papers` are public and free of provider inference.
- `/ask` and `/feedback` require a constant-time checked Bearer token. Invalid or
  missing production configuration fails closed. Local development remains open
  when both `REQUIRE_AUTH` and the token are unset. Export these settings for local
  auth testing; the guard reads process environment, not a frontend `.env` file.
- Default **5 ask requests/minute** and **20 feedback requests/minute**, no Redis.
  Time-window counters reset on restart; the cumulative question budget does not.
- **100 admitted ask requests total**, persisted atomically mode 0600 in
  `/var/lib/researchlens/demo-budget.json`; invalid/failed/busy admitted requests
  can consume allowance. No refunds, automatic resets or automatic POST retries.
  Corrupt/unwritable budget state returns sanitized 503 and blocks generation.
- The unchanged service allows **at most 2 inference attempts per question**
  (initial plus bounded citation repair), so 100 admissions bound generation at
  200 attempts. **This is not a dollar cap or a credit-balance check**. Set a smaller
  allowance if needed, monitor actual provider billing, and use a dedicated project
  API key. No particular question count is guaranteed to fit $20.
- All visitors share these limits. Set `RESEARCHLENS_DEMO_PASSWORD` on Streamlit to
  gate access before any backend request; share it privately with attendees. This
  supplements, rather than replaces, the backend budget. Passcode guesses are not
  billed. UI sessions last until restart/session loss; this is demo access control,
  not per-user authentication. Unauthenticated health/catalog traffic remains public.
- Single Uvicorn worker is required for the in-process lock/rate counters. Do not
  run another API process against the same budget file. Threaded admissions are
  serialized. Generation remains serialized by the existing service lock.

To extend the demo allowance, edit `RESEARCHLENS_MAX_QUESTIONS` in the protected env
file and restart. Consumed questions remain recorded. To explicitly reset for a
new event, stop the service, back up the state, remove/reset it as administrator,
then restart. Never reset automatically on startup. Back up feedback JSONL and
budget state to your laptop; feedback contains user-provided text. Local VM files
survive process restarts but not deletion/reclamation of their volume.

## 6. Caddy and HTTPS

On the future VM, follow the [official Caddy Ubuntu repository installation](https://caddyserver.com/docs/install#debian-ubuntu-raspbian):

```bash
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
  | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
  | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
sudo chmod o+r /etc/apt/sources.list.d/caddy-stable.list
sudo apt-get update
sudo apt-get install -y caddy
sudo install -m 0644 deploy/Caddyfile /etc/caddy/Caddyfile
sudoedit /etc/caddy/Caddyfile
# Replace REPLACE_WITH_API_HOSTNAME.invalid with your actual <API_HOSTNAME>.
sudo caddy fmt --overwrite /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
```

The package may start Caddy's default site; configure it before considering the
endpoint ready. Check the image's existing firewall; if using UFW, preserve SSH
before enabling it:

```bash
sudo ufw allow from <YOUR_PUBLIC_IP>/32 to any port 22 proto tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
sudo systemctl reload caddy
sudo systemctl enable caddy
```

OCI images may also have pre-existing iptables/nftables rules. Inspect with
`sudo iptables -S` / `sudo nft list ruleset`; ensure 80/443 reach Caddy before any
terminal REJECT. Do not flush the image firewall or assume UFW overrides it. OCI
NSG/security lists and guest firewall must both permit traffic. Never open 8000.

With real DNS and reachable ports, Caddy obtains/renews certificates automatically;
see [automatic HTTPS](https://caddyserver.com/docs/automatic-https). No certificate
can be claimed for this template's `.invalid` hostname. The proxy permits 400-second
response-header/read waits for the existing generation+repair timeout envelope;
see [transport timeouts](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy).
There is no proxy POST retry. Do not add a short proxy timeout that causes users to
retry while a billable question continues. Payloads are capped at 16 KB.

## 7. Streamlit Community Cloud

1. Sign in to Community Cloud, connect GitHub, choose this repository,
   **branch `feature/deployment`**, entrypoint **`app/streamlit_app.py`**.
2. Advanced settings: **Python 3.11**. The entrypoint-adjacent
   `app/requirements.txt` takes precedence over the root backend requirements;
   see [Community Cloud dependency discovery](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).
   Only Streamlit/httpx/pydantic are direct frontend dependencies. Streamlit still
   brings its own NumPy/pandas/Arrow transitive dependencies; no torch,
   sentence-transformers, OpenAI SDK, PDF packages or model weights are needed.
3. Paste `deploy/streamlit-secrets.toml.example` into Advanced settings → Secrets.
   Fill real HTTPS `RESEARCHLENS_API_URL`, the **same** Oracle API token, and the
   **different** attendee `RESEARCHLENS_DEMO_PASSWORD`. Do not include OpenAI keys.
   [Root-level secret keys become server environment variables](https://docs.streamlit.io/develop/concepts/connections/secrets-management).
4. Deploy and record the assigned `<STREAMLIT_PUBLIC_URL>`. Enter the passcode and
   check the paper selector (eight papers). Keep the demo passcode private.
   After token rotation, update both services and reboot Streamlit to evict cached
   clients. API tokens are server-side only and never shown in rendered widgets.

No browser CORS rule is required: HTTP requests originate on the Streamlit server.
Feedback is written on Oracle's persistent `/var/lib/researchlens` path, not the
Cloud frontend. If someone later uses local/ephemeral backend storage, feedback
can be lost on redeployment; there is no new database.

## 8. Public verification and troubleshooting

First run **non-billable** checks from your laptop:

```bash
curl --fail https://<API_HOSTNAME>/health   # 200, status ok, 1001 chunks, index_valid true
curl --fail https://<API_HOSTNAME>/papers   # eight papers
curl -s -o /dev/null -w '%{http_code}\n' -X POST https://<API_HOSTNAME>/ask \
  -H 'Content-Type: application/json' -d '{"question":"How does SelfCheckGPT work?"}'
# Must be 401. Repeat /feedback without auth: also 401.
```

With the budget/key configured and explicit demo spending approval, manually ask
one general question, one paper-specific/filter question, one two-paper comparison
and one unsupported question through Streamlit. Confirm citation/page/quote display,
complete/partial/clarification/abstention/error states and both feedback ratings.
These are **future live checks**, not tests performed in preparation. Do not rerun
the 117-case benchmark just to validate hosting. Browser requests should show only
Streamlit traffic; the backend token must not appear in browser developer tools.

| Symptom | Action |
|---|---|
| No free A1 capacity | Try another availability domain in the home region or wait; do not silently select a paid shape. |
| ARM wheel/install failure | Check `uname -m`, Python 3.11 and glibc >=2.28; keep CPU index and pins. Save resolver errors; do not copy x86 `.venv`. |
| Model attempts download | Run the artifact `check` offline; verify the full pinned snapshot, modules and tokenizer. Do not enable automatic rebuild/download at startup. |
| Fingerprint/hash mismatch | Re-transfer the coherent trusted archive; stop service and back up existing artifacts. Do not combine labels/indexes/corpora. |
| systemd permission/execute error | Check `/srv/ResearchLens/.venv/bin/python`, managed `.python` location, app ownership and environment file. `ProtectHome` hides `/home`; no RAM dependencies belong here. |
| Health 503 | `sudo journalctl -u researchlens -n 60 --no-pager`; check index/cache, OpenAI configuration and auth token length. Do not paste secrets/logged prompts publicly. |
| Ask 401 | Match the Streamlit/Oracle API tokens; keep the Bearer header server-side; restart services after rotation. |
| Ask 429 | Wait 60 seconds for rate limit; if cumulative allowance is exhausted, administrator reviews billing and raises allowance explicitly. No auto-retry. |
| Ask 503, health ok | Check budget JSON validity/permissions and `/var/lib/researchlens` ownership; or service is busy. Corrupt budget fails closed. |
| TLS/connection failure | Check DNS A/AAAA, OCI ingress, guest firewall, `sudo journalctl -u caddy`; 80/443 public, 8000 loopback. |
| Provider 502/504 | Check provider/key/billing availability; retained evidence/errors are safe; do not blindly retry a potentially billed question. |
| Frontend tries installing torch | Confirm branch, entrypoint and `app/requirements.txt` discovery; redeploy with Python 3.11. |
| Feedback missing | Check protected backend feedback path and ownership; back up the volume, not Cloud's ephemeral frontend filesystem. |

For an update: back up state, stop `researchlens`, pull the reviewed deployment
commit as the app user, update dependencies only when pins change, restore changed
artifacts once if required, run offline checks, restart and verify health. Do not
install/rebuild/download on every startup. No resource/server has been configured
by this preparation work.
