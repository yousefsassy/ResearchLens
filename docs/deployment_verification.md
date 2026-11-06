# Deployment preparation verification — 2 November 2026

Scope: local x86_64 preparation from `445ac2107cf87546bccfa23219b8d571a1df2ba1`
on `feature/deployment`. No Oracle VM/hostname exists; nothing was deployed.
No benchmark was rerun and no OpenAI inference was called for this work.

| Check | Result |
|---|---|
| Full offline suite | **388 passed** in 9.80 s; original 362 remain passing |
| New deployment regressions | 14 auth/budget/client/passcode tests + 12 artifact tests |
| Backend environment `pip check` | No broken requirements |
| Clean frontend | Fresh Python 3.11.17 venv, installed only `app/requirements.txt`; `pip check` clean |
| Frontend dependency isolation | torch, sentence-transformers, OpenAI SDK, PyMuPDF and FastAPI absent; blocked backend imports while exercising Streamlit AppTest + real HTTP adapter with mocked transport |
| Frontend behavior | Ask/abstention rendered, POST token forwarded server-side, no debug curl panel; existing tests cover filters, comparisons, quotations, states and feedback |
| Real Uvicorn startup | New loopback process warmed the actual 1,001-chunk index/model; health 200, eight papers; unauthenticated ask 401, authenticated invalid ask 422, authenticated feedback 200 into temporary file; no inference |
| Artifact round trip | Pack → trusted-SHA verify → restore to fresh directory → canonical index validation and filtered offline P002 hybrid retrieval passed |
| Read-only artifact loading | Repeated retrieval with restored files/directories read-only and `HOME=/nonexistent`; passed on x86 |
| ARM wheel metadata | All 57 pinned backend distributions have compatible CPython-3.11 ARM64/universal wheels; exact torch 2.15.0+cpu ARM wheel present in official CPU index |
| Shell syntax | `bash -n scripts/setup_oracle_backend.sh` passed; script not executed on x86 |
| Caddy | Temporary official 2.11.7 x86 binary, release SHA512 verified; `caddy validate --config deploy/Caddyfile --adapter caddyfile` passed; no server started/certificate requested |
| systemd | Original template reports the expected missing `/srv/ResearchLens/.venv/bin/python`; a temporary copy substituting the existing local Python passed `systemd-analyze verify`. Target executable/user/path permissions and sandbox operation remain VM checks |
| Whitespace | `git diff --check` clean |

## Prepared local artifact

`tmp/researchlens-runtime.tar.gz` (~76 MiB, ignored/uncommitted) contains 14 runtime
files plus the manifest. Complete pinned BGE snapshot included; cache symlinks
were dereferenced. Outer SHA256:

```text
2ece5bf14990e4ab0189180161f4d0b031cc5c9b9f45e77caeafafd840650dc2
```

Corpus fingerprint:
`3bd5c264d591d8c386c7859fc61c4cfe127e0b288c3c6622bcd738d4c3980c83`.
Index `(1001, 384)`; BGE revision
`5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`.
A new packaging run may produce a different outer archive hash due to archive
metadata/timestamps; record the newly printed hash rather than reusing this one.
The per-file manifest validates content. The bundle is on the laptop, not GitHub.

## Remaining acceptance gates

Actual ARM dependency resolution/installation, offline model/index loading under
the systemd sandbox, measured RAM/latency, OCI free capacity/account limits, guest
firewall, DNS/TLS and public Streamlit connectivity have **not** been verified.
The configured demo budget limits question admissions, not dollars. Use a modest
allowance, private attendee passcode and manual billing checks before public use.
See [the runbook](deployment.md) for manual provisioning and future live checks.
