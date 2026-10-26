# Phase 3: grounded hosted generation

`src.generation` adds a synchronous Python interface and CLI around the existing
retrieval API. Ingestion, retrieval, their tests, and retrieval metrics are unchanged.
Generation imports do not load retrieval, model weights, `.env`, or credentials.
`GenerationConfig.from_env()` explicitly loads configuration; environment variables
override the repository-root `.env` file.

## Setup and actual verification

Use Python 3.11. From the project root:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

On Windows, use `.venv\Scripts\python.exe` instead. Add your own OpenRouter key to
the ignored `.env`; do not publish it. `.env.example` deliberately has no key.

For development without PDF/neural libraries, the mocked test suite needs only:

```bash
.venv/bin/python -m pip install httpx pydantic python-dotenv numpy rank-bm25 'pytest>=8,<9'
.venv/bin/python -m pytest tests/ -q
```

Real hybrid retrieval additionally requires the agreed `data/processed/chunks.jsonl`,
matching `data/indexes/`, and cached BGE model. Obtain the agreed artifacts from the
team. Do not regenerate them casually: changing extraction/chunking invalidates
indexes and labels. The documented 638-chunk handoff fingerprint is
`817fa270d2b7842bd86dbdb0a5d5f89d08170eb3c5937a184851098f4cab1713`.
The earlier 612-chunk outputs remain unavailable. This implementation does not
resolve that historical discrepancy or certify the current corpus.

At implementation time Python 3.11 was provisioned in `.venv`, with the minimal
mock-test dependencies above. No PDF/neural packages or model weights were
downloaded. The original suite produced **61 passed, 1 skipped**: the real-corpus
BM25 test skips because the agreed chunks are absent. Live retrieval, live
generation, and semantic quality remain unverified until artifacts and a key
are supplied. Do not interpret mocked passing tests as real-model accuracy.

## Public interface

```python
from src.generation import GenerationConfig, ResearchGenerator

config = GenerationConfig.from_env()
generator = ResearchGenerator(config=config)
try:
    result = generator.answer(
        'What limitations do the SelfCheckGPT authors identify?',
        paper_ids=['P002'],
        answer_type='auto',
    )
    response = result.model_dump(mode='json')
finally:
    generator.close()
```

For integration, inject an existing `ResearchRetriever` and/or a client implementing
`complete(messages) -> (ModelAnswer, Metrics)`. The generator otherwise constructs
the retriever lazily on the first answer requiring evidence. Reuse instances for
serial requests; concurrency is outside this version's contract. A client owns a
shared maximum of 25 inference attempts, including failures and retries.

```bash
.venv/bin/python scripts/ask_researchlens.py --live \
  --question 'How does SelfCheckGPT detect hallucinations?' --paper-ids P002
.venv/bin/python scripts/ask_researchlens.py --live \
  --question 'Compare the methodologies of SelfCheckGPT and FActScore.' \
  --paper-ids P002 P003 --answer-type comparison
```

The CLI requires `--live` before it can send inference requests. Library callers
invoke `answer()` explicitly; that may call OpenRouter when evidence is available.
Input/configuration errors are distinct from missing evidence. Questions requiring
clarification and empty usable retrieval make no hosted inference calls.

The response is versioned JSON (`schema_version: "1.0"`) with `question`,
`answer_type`, `status`, `answer`, `claims`, `citations`, `evidence`, `paper_ids`,
`abstained`, `limitations`, `clarification`, `error`, and `metrics`.
`status` is `complete`, `partial`, `abstained`, `needs_clarification`, or `error`.
`error` and `clarification` are nullable objects. Titles and unavailable usage
fields are nullable. API failures never count as evidence abstention.

Each claim has `text`, `kind` (`reported`/`synthesis`), and source/quote citations.
Each resolved citation includes a deterministic `C1`-style ID, one-based claim
index, source ID, quote, paper ID, PDF filename/title, one-based PDF position,
and chunk ID. Pages are **PDF positions**, not printed page labels. The UI can
look up `source_id` in `evidence` and display the complete supporting passage.
Render returned strings as text, not trusted HTML.

## Paper scope and retrieval

`data/papers_generation.json` is generation-owned. Its display titles were checked
against the first page of each local PDF. No authors/year/license fields are guessed,
and the teammate-owned manifest is untouched. IDs and aliases resolve deterministically.
An unresolved named paper, vague "this paper", or incomplete paper comparison
returns clarification; explicit paper IDs resolve vague references. Conflicting
named and supplied scopes require clarification. Two-paper comparisons are the
maximum for this version. Alias matching is intentionally simple, not an exhaustive
named-entity recognizer; application-selected IDs provide the most reliable scope.

General/single-paper QA calls the existing `search` with `top_k=8`, `mode="hybrid"`,
`rerank=False`, `paper_ids=scope`, `exclude_flagged=True`, and retains six unique
passages. Broad comparisons make three aspect queries (methods, findings,
limitations) independently for each paper, retaining two unique passages per
aspect, six per paper at most. Narrow comparisons query the named aspects only.
Exact duplicates within a paper and repeated IDs merge. Identical statements
from different papers retain separate attribution.

Whole passages are selected round-robin across papers under a 24,000-character
text budget. This is not a tokenizer limit; the prompt adds metadata/instructions,
well within the verified free endpoints' advertised context sizes. Source IDs are
assigned only after selection. Source text and citation identity remain intact.
Unexpected scope/filename/metadata failures stop generation.

Flagged evidence is excluded without automatic fallback. Flags are incomplete.
Missing paper/aspect evidence and context-budget exclusions are explicit limitations.
There is no fabricated RRF confidence threshold. A high ranking or nonempty result
does not establish semantic sufficiency. The generator assesses missing components
in its one answer call, and known local gaps force a partial status when claims
are otherwise available.

## Grounding and citation boundaries

The versioned prompt requests atomic claims using supplied evidence only,
separates reported findings from synthesis, and treats question/passages as untrusted
data. It forbids invented references, unsupported numerical findings, and ranking
studies with incompatible tasks/datasets/metrics. Conflicting findings must remain
attributed with their experimental context. Missing components produce partial
answers; no support produces abstention.

The LLM supplies only source IDs and quotes, not authoritative bibliographic fields.
Local validation checks schema, required claim citations, source membership,
whitespace-normalized quote occurrence, and both-paper citations for comparison
synthesis. Local code attaches paper/page/chunk metadata and renders `[C1]` markers.
Invalid output is withheld in full while evidence and usage remain available.
There is no automatic repair call.

These are **structural checks, not semantic entailment proofs**. A real quote can
be misinterpreted, contradictory evidence can be overlooked, and reported/synthesis
labels can be misused. Human claim-level evaluation remains required. The model's
limitations are uncertainty text, not independently verified factual statements.

## OpenRouter policy and failures

The default is `nvidia/nemotron-3-super-120b-a12b:free`. Before each answer call the
client reads the public model catalog, requires an exact `:free` ID and zero listed
pricing, and sends provider price caps of zero. Catalog/network/price verification
failure prevents inference. No automatic model or paid fallback is configured.

Schema-capable models receive JSON Schema with `strict: true` and
`provider.require_parameters: true`. An explicitly selected JSON-only alternative
(e.g. `google/gemma-4-31b-it:free`) receives JSON-object mode plus the same local
validator and schema in the prompt. An unsupported schema request is an error,
never a silent second request with weaker guarantees. Another evaluation candidate
is `nvidia/nemotron-3.5-super-vl:free`. Availability must be verified live; no
ResearchLens quality ranking between these models has been established.

Defaults: non-streaming, 4096 output tokens, low reasoning effort where supported,
5-second connection and 60-second network timeouts, two inference attempts maximum.
Reasoning may consume output tokens; truncation/refusal fails validation. HTTP timeouts
bound network operations, not a strict end-to-end deadline. Free services have no
guaranteed latency/availability. Only public paper passages/questions should be sent;
the NVIDIA endpoint documents provider-side logging.

Missing keys, permanent request/authentication/model errors, and credit errors
return sanitized errors. Short transient rate limits/server failures/timeouts get
one retry; daily quota and waits exceeding 30 seconds stop promptly. HTTP-200 error
bodies are checked. Raw provider bodies/headers and API keys are never included in
returned errors. Code does not log credentials. Caller-enabled HTTP debug logging
is outside this module.

Metrics record interpretation/retrieval/generation/validation/total elapsed time,
configured model, latest provider/request ID, attempts, and reported usage/cost.
All known attempt usage is summed. Unknown values remain null; accounting completeness
is false when an attempt's usage is missing. Known subtotals do not imply complete
billing knowledge. No paid API calls are needed to test these behaviors.

References checked during implementation:
[structured output](https://openrouter.ai/docs/guides/features/structured-outputs),
[errors](https://openrouter.ai/docs/api/reference/errors-and-debugging),
[usage](https://openrouter.ai/docs/cookbook/administration/usage-accounting).

## Generation evaluation

The 20-case `eval/generation_questions.draft.jsonl` is **not human approved**.
Its 4 general, 5 paper-specific, 4 comparison, 4 insufficient-evidence, and 3
extraction-sensitive cases include draft rubrics and source references. Some fixed
contexts come from the existing unapproved draft's preserved supporting passages;
others must be supplied and checked by humans. No source evidence is fabricated
to make a missing case runnable. A comparison with deliberately missing evidence
and the three damaged-context cases are fixed-track-only; their constrained
contexts must not be confused with full-corpus retrieval.

Before benchmarking, review reference components, add missing fixed evidence,
verify expected status, record a reviewer, and freeze a separate approved dataset.
Abstention tests should include unrelated/topical passages, not just empty input.
For flagged-only stress tests supply real flagged chunk records from the agreed
corpus; do not invent their text or IDs. Human approval is enforced by the runner;
`--allow-draft` is an explicit debugging exception and never enables final claims.

```bash
.venv/bin/python eval/generation_eval.py run --live --track fixed \
  --dataset eval/generation_questions.approved.jsonl \
  --output eval/results/generation.fixed.json
.venv/bin/python eval/generation_eval.py run --live --track end-to-end \
  --dataset eval/generation_questions.approved.jsonl \
  --output eval/results/generation.e2e.json
```

Fixed track injects supplied evidence without neural retrieval. End-to-end uses
the real pipeline. Both save each completed case, preserve configuration/dataset
hash/prompt version, and share a 25-attempt cap. Existing reports are not overwritten.
Daily quota/key/attempt-cap failures stop the run; `run_complete` identifies whether
all planned cases ran. End-to-end records retrieval status/fingerprint metadata
when available. Results are under ignored `eval/results/`.

Score offline using an independently human-authored JSON mapping from question ID
to a review. For each response use its captured `response_sha256` to prevent stale
reviews from being applied to a different run:

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

Claim indices are one-based. Component IDs refer to the case rubric, not citation
IDs, despite both examples using `C1`. Only credit genuinely correct/supported
items, and review failures too (with empty supported lists when appropriate).

```bash
.venv/bin/python eval/generation_eval.py score \
  --report eval/results/generation.fixed.json --reviews /path/to/human_reviews.json
```

The scorer reports component correctness, claim faithfulness, citation support and
coverage, comparison completeness, abstention precision/recall (excluding partial
and clarification targets), status accuracy, structural validity, success rate,
p50/p95 latencies, known usage subtotals, and denominators. Missing human judgments
yield incomplete/provisional scores, never automatic semantic credit. API errors
are failures, not correct abstentions. Final quality gates require a complete,
approved, fully reviewed run, structural validity throughout, at least .90 faithfulness
and citation accuracy, .80 correctness, and no factual answers or failed abstentions
on intentionally unsupported cases. Passing a tiny fixture is not a 20-case pilot;
report actual sample size.

The initial live pilot remains pending artifacts, credentials, and human approval.
The assignment's 120-case target (40 development/80 held-out: 25 general, 45 scoped,
25 comparison, 15 insufficient, 10 extraction-sensitive) also requires real human
annotation with Member 4. This implementation supplies the tools, not fabricated
approved judgments or a claimed completed benchmark.

Next week's optimization should target a 50% p95 latency reduction with at most
two accuracy points lost on frozen labels. A zero-dollar inference baseline cannot
show a meaningful 50% cost reduction. UI/service/deployment, parallel requests,
semantic verifier models, and automatic model selection remain Phase 4/future work.
