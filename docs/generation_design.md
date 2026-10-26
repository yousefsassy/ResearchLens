# Phase 3: grounded local generation

Phase 3 uses the already installed **Qwen `qwen3:8b` through local Ollama**.
OpenRouter is no longer used. No API key, cloud model, automatic model download,
or hosted fallback is required. The source-selection, grounded prompt, claim-level
citation checks, structured responses, and generation evaluator remain in place.
Ingestion and retrieval implementations are unchanged.

## Setup and configuration

Use Python 3.11 and install the project requirements in a virtual environment.
Ollama is a separate local service. Check it before running generation:

```bash
ollama list
ollama ps
```

The current development machine has `qwen3:8b` installed and serves Ollama on
port 11434. The client checks `/api/tags` and requires installed GGUF weights.
It never calls a pull endpoint or selects another model. Start `ollama serve`
only if the Ollama service is not already running.

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
```

If `.env` already exists, update the settings below instead of overwriting it.
On Windows use `.venv\Scripts\python.exe` in place of `.venv/bin/python`.

```dotenv
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:8b
OLLAMA_NUM_CTX=8192
OLLAMA_TIMEOUT_SECONDS=180
RESEARCHLENS_MAX_TOKENS=2048
RESEARCHLENS_CONTEXT_CHARS=12000
```

`GenerationConfig.from_env()` reads the repository-root `.env` explicitly; real
process environment variables override its values. Old `OPENROUTER_*` settings
are ignored, and credentials are not part of the configuration/response schema.
Importing `src.generation` never reads `.env`, initializes retrieval, or loads weights.

The URL must be loopback (`127.0.0.1`, `localhost`, or `::1`). The built-in client
ignores HTTP proxy variables and does not follow redirects. Cloud-backed tags
are rejected. No public model catalog is contacted. Tests use mocked HTTP transport;
normal generation contacts only local Ollama.

## Retrieval prerequisites

Real hybrid retrieval still requires the agreed `data/processed/chunks.jsonl`,
matching `data/indexes/`, retrieval dependencies, and cached BGE model. Obtain these
artifacts from the team; do not regenerate them casually. Generation does not
replace BGE with Qwen or change the retrieval index.

The documented 638-chunk corpus fingerprint is
`817fa270d2b7842bd86dbdb0a5d5f89d08170eb3c5937a184851098f4cab1713`.
The original 612-chunk outputs remain unavailable. Corpus/index/label versions must
match. Missing artifacts return `retrieval_unavailable` before generation.

For mocked tests without PDF/neural libraries:

```bash
.venv/bin/python -m pip install httpx pydantic python-dotenv numpy rank-bm25 'pytest>=8,<9'
.venv/bin/python -m pytest tests/ -q
```

The real-corpus test skips if processed chunks are absent. Passing mocked tests
is not evidence of live retrieval or model accuracy.

On 2026-10-26 a real local `qwen3:8b` call answered the SelfCheckGPT detection
question using a preserved draft passage: **three claims with three structurally
validated citations**, 1,371 input tokens, 293 output tokens, and about 59.6 seconds
for generation. The report is `eval/results/local_qwen_smoke.json` (ignored by Git).
This verifies actual local inference and the citation path for one supplied
passage; it does not verify full-corpus retrieval or establish benchmark quality.
An earlier smoke failed quote checks because Qwen changed Markdown spacing and
punctuation. Prompt version 1.1 requests concise answers and short verbatim spans;
the strict quote validator remains unchanged and rejects those alterations.
The real local abstention smoke also passed: with only SelfCheckGPT evidence,
Qwen declined an unrelated lunar-vehicle question, returned zero claims, and
explained the missing evidence in about 21.3 seconds. Its report is
`eval/results/local_qwen_abstention_smoke.json`. These are developer smoke checks,
not human-approved evaluation results.

## Public interface and CLI

```python
from src.generation import GenerationConfig, ResearchGenerator

generator = ResearchGenerator(config=GenerationConfig.from_env())
try:
    result = generator.answer(
        'What limitations do the SelfCheckGPT authors identify?',
        paper_ids=['P002'],
        answer_type='auto',
    )
    response_json = result.model_dump(mode='json')
finally:
    generator.close()
```

The default transport is `OllamaClient`, exported from `src.generation`. The former
`OpenRouterClient` and API-key configuration have been removed. Inject an existing
`ResearchRetriever` and/or a client implementing
`complete(messages) -> (ModelAnswer, Metrics)` for integration or testing. Without
injection, retrieval is constructed lazily. Reuse instances for serial requests;
parallel use is outside this version's contract.

```bash
.venv/bin/python scripts/ask_researchlens.py --live \
  --question 'How does SelfCheckGPT detect hallucinations?' --paper-ids P002
.venv/bin/python scripts/ask_researchlens.py --live \
  --question 'Compare the methodologies of SelfCheckGPT and FActScore.' \
  --paper-ids P002 P003 --answer-type comparison
```

`--live` explicitly enables real **local** inference. Library `answer()` calls can
also trigger local inference when evidence is available. Ambiguous paper scope and
empty usable retrieval do not invoke Qwen. The CLI requires real retrieval artifacts.
For fixed-evidence model tests use the evaluator or inject `FixedEvidenceRetriever`.

## Evidence and citation contract

`data/papers_generation.json` contains display titles checked against each local
PDF's first page. It is separate from the teammate-owned manifest. Exact paper IDs
and explicit aliases resolve deterministically. Unknown/vague references and
conflicting scopes require clarification. Two-paper comparisons are supported;
"this paper" needs an application-supplied ID. This is a simple alias resolver,
not exhaustive named-entity recognition.

QA calls Phase 2 with `top_k=8`, `mode="hybrid"`, `rerank=False`, and
`exclude_flagged=True`, then retains up to six unique passages. Comparisons query
methods/findings/limitations independently per paper (only requested aspects for
narrow comparisons), retaining two passages per aspect and six per paper at most.
Repeated IDs and duplicate text within a paper merge. Identical text from different
papers retains its separate provenance.

Whole passages are selected round-robin across papers within 12,000 text characters.
The smaller local budget limits RAM/context usage. Budget exclusions are recorded,
and known evidence gaps force partial answers. Source IDs are assigned after final
selection. No RRF confidence threshold is invented. Flagged evidence is excluded
without fallback; unflagged text can still contain extraction errors.

The prompt requires claims based only on supplied evidence, explicit attribution
of contradictory findings, and separation of reported facts from synthesis. It
forbids invented bibliographic details, unreported results, and rankings based on
incompatible experimental tasks/metrics. The question and passages are untrusted
data, including any embedded instructions. Unsupported components produce partial
answers or abstention, never answers from model memory.

Local validation checks the output schema, required citations on every claim,
source IDs, whitespace-normalized quote occurrence, and both-paper citations for
comparison synthesis. Local code attaches original paper/page/chunk metadata and
renders `[C1]` citation markers. Invalid output is withheld in full. No automatic
repair call is made. These checks establish structural integrity, **not semantic
entailment**; a real quote can be misinterpreted. Human faithfulness review remains
necessary, especially with an 8B model and damaged scientific text.

## Structured response

The JSON response retains `schema_version: "1.0"` and these fields:

- `question`, `answer_type`, `paper_ids`: original question and resolved scope.
- `status`: `complete`, `partial`, `abstained`, `needs_clarification`, or `error`.
- `answer`, `claims`, `citations`, `evidence`: rendered text, cited atomic claims,
  trusted citation metadata, and complete selected passages.
- `abstained`, `limitations`: evidence abstention and missing-component warnings.
- `clarification`, `error`: nullable clarification and sanitized error objects.
- `metrics`: model/provider, attempts, stage latency, native tokens, and API cost.

Claim kinds are `reported`/`synthesis`. Citation IDs and claim indices are one-based.
Citations contain source ID/quote, paper ID, filename/title, PDF position, and chunk
ID. Pages are **one-based PDF positions**, not printed page labels. UI code can
look up each `source_id` in `evidence`; render strings as text rather than trusted
HTML. API/runtime failures are distinct from evidence-based abstention.

## Local runtime and failures

Requests use Ollama's `/api/chat` with `stream: false`, `think: false`, temperature
zero, and `ModelAnswer.model_json_schema()` in `format`. The same schema is supplied
in the prompt. Output must finish with `done: true`, `done_reason: "stop"`, the
configured model, and valid JSON before citation validation. Length-truncated,
empty, or invalid output is withheld.

Defaults suit the detected 16 GiB development machine: 8,192 context tokens,
2,048 maximum generated tokens, and a 12,000-character evidence budget. Character
budgeting is not exact tokenization: reduce context or increase `OLLAMA_NUM_CTX`
when unusual text or long questions need more room. Larger context windows consume
more RAM. Generation keeps Qwen loaded for five minutes to reduce warm latency.
No extra model weights are downloaded.

Connection timeout is five seconds; network read timeout defaults to 180 seconds.
Loading/inference can take longer on CPU. A timeout returns `request_timeout`
without automatically starting a duplicate expensive job. Connection failures return
`ollama_unavailable`, absent weights return `model_not_installed`, and cloud tags
return `local_model_required`. Runtime/memory errors return `ollama_error` without
exposing raw service details. One attempt is the default; explicitly configured
server-error retries are bounded to two. The shared client cap is 25 attempts.

Metrics map `prompt_eval_count`/`eval_count` to input/output tokens and identify
provider `ollama`. There is no hosted API charge (`cost_usd: 0`); hardware/electricity
cost is not measured. Missing token counts remain null with incomplete accounting.
Thinking is disabled. Stage timings include model loading when applicable; compare
cold and warm latencies separately.

Official references:
[chat API](https://docs.ollama.com/api/chat),
[structured output](https://docs.ollama.com/capabilities/structured-outputs),
[thinking controls](https://docs.ollama.com/capabilities/thinking).

## Evaluation

The 20 cases in `eval/generation_questions.draft.jsonl` remain **unapproved drafts**:
4 general, 5 scoped, 4 comparison, 4 insufficient-evidence, and 3 extraction-sensitive.
Some preserved fixed passages come from unapproved retrieval labels; missing contexts
and reference rubrics require human review. Do not fabricate text/IDs to make a case
runnable. The intentionally incomplete comparison and three damaged-context cases
are fixed-track-only. Use topical non-answering contexts for semantic abstention
tests, not only empty evidence.

Freeze a separate approved dataset with real reviewer metadata before benchmarking.
`--allow-draft` is a debugging exception, not approval. Fixed track injects supplied
passages without neural retrieval; end-to-end uses the real pipeline.

```bash
.venv/bin/python eval/generation_eval.py run --live --track fixed \
  --dataset eval/generation_questions.approved.jsonl \
  --output eval/results/generation.fixed.json
.venv/bin/python eval/generation_eval.py run --live --track end-to-end \
  --dataset eval/generation_questions.approved.jsonl \
  --output eval/results/generation.e2e.json
```

Each completed response is saved with dataset hash, prompt version, configuration,
and response hash. Existing reports are not overwritten. Model/service/cap errors
stop the runner; `run_complete` marks whether every planned case was processed.
End-to-end captures retrieval status/fingerprint when available. Reports and smoke
results are under ignored `eval/results/`.

Score offline with an independently human-authored JSON mapping:

```json
{
  "GEN-001": {
    "human_verified": true,
    "reviewer": "actual reviewer name",
    "response_sha256": "copy from the captured response row",
    "supported_claim_indices": [1],
    "supported_citation_ids": ["C1"],
    "adequately_cited_claim_indices": [1],
    "correct_component_ids": ["C1"],
    "notes": "Explain judgments and failures here."
  }
}
```

Component IDs refer to the case rubric, distinct from citation IDs. Credit genuinely
correct/supported items only; review errors too. Response hashes reject stale reviews.

```bash
.venv/bin/python eval/generation_eval.py score \
  --report eval/results/generation.fixed.json --reviews /path/to/human_reviews.json
```

Metrics cover correctness, faithfulness, citation accuracy/coverage, comparison
completeness, abstention precision/recall, status accuracy, structural validity,
success rate, native tokens, and p50/p95 latency with explicit denominators. Missing
human judgments cannot earn automatic semantic credit. Runtime errors are failures,
not correct abstentions. Quality gates require a complete, approved, fully reviewed
run, structural validity throughout, .90 faithfulness/citation accuracy, .80 correctness,
and no factual answers or failed abstentions on intentionally unsupported cases.

One live fixed-evidence smoke is not a completed pilot or full retrieval test.
The 120-case assignment target (40 development/80 held-out: 25 general, 45 scoped,
25 comparison, 15 insufficient, 10 extraction-sensitive) still needs human annotation
with Member 4. Next week's optimization can target 50% p95 latency reduction with
at most two accuracy points lost on frozen labels. UI/service/deployment, parallel
requests, and automated semantic verifiers remain future work.
