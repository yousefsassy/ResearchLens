# Local verification and generation reliability

Work starts from `emna` commit `38e0040f24ddc4c7baffa2db33c05241dd51b6ea`.
Generation changes are on `feature/generation-reliability`; `emna` is not committed
or advanced. No PDF, manifest, metadata-filter implementation, embedding model,
generation model, benchmark/judge framework, backend, or frontend was changed.

## Verified local setup

- Python 3.11.17 in the project `.venv`; no system/global package changes.
- Requirements installed, with CPU PyTorch 2.15.0+cpu. `pip check` passes.
- PyMuPDF 1.28.2 and PyMuPDF4LLM 0.3.4 reproduce the expected corpus. The existing
  legacy extraction warns that it ignores `use_ocr`; this behavior was not changed.
- Eight papers, 250 pages, 1,001 nonempty unique chunks, all with the expected
  paper metadata. Counts: P001 290, P002 54, P003 96, P004 106, P005 92, P006 251,
  P007 61, P008 51. There are 104 flagged chunks across 32 pages.
- Corpus fingerprint:
  `3bd5c264d591d8c386c7859fc61c4cfe127e0b288c3c6622bcd738d4c3980c83`.
- Index rebuilt with unchanged `BAAI/bge-small-en-v1.5`, pinned revision
  `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`: 1,001 x 384 normalized float32 vectors.
  `load_index()` validates fingerprint, IDs, checksum, settings, shape and norms.
- Hybrid retrieval succeeds without filters, with combined paper/year/author/section
  filters, and for new papers P007/P008. A year with no matches returns no evidence.
- Original offline suite: 220 passed after artifact restoration.
- Exactly one hosted generation request was made, using `gpt-5.4-nano`, an output
  cap of 768, SDK retries disabled, and a shared attempt cap of one (no paid repair).
  It returned a complete SelfCheckGPT answer with seven validated citations. This
  live check preceded the reliability edits; final edits are verified offline only.
  The ignored record is `eval/results/local_setup_smoke.json`.

The filesystem initially had only 481 MB free. At the user's request, large ML
packages live in `/tmp/researchlens-ml-deps`, added to `.venv` by
`researchlens_ram_deps.pth`. `.cache/huggingface` points to
`/tmp/researchlens-model-cache`. **These packages and model weights are temporary
and must be restored after a reboot.** Processed JSONL and the checked vector index
are ordinary ignored project files and persist on disk. No user files were removed.

## Configuration fix

`OpenAIClient` loads the project-root `.env` with `override=False` only when using
the real SDK. Existing process variables take precedence. Injected clients remain
inert, no key is added to public configuration, and the `.env` file is never rewritten.
Missing keys produce a structured `missing_api_key` response without a provider
request. Authentication and insufficient-quota failures do not trigger retries.
The configured model remains `gpt-5.4-nano`.

The current runtime is OpenAI; older Qwen/Ollama instructions in
`generation_design.md` describe a prior implementation.

## Reproduced problems and fixes

1. **Unrequested comparison dimensions.** External-knowledge, factual-recall,
   evaluation-unit and related comparison questions could default to all three
   dimensions, creating unnecessary gaps. `papers.interpret()` now recognizes
   these methodological scopes; broad methods/findings/limitations requests
   retain all three dimensions.
2. **Backend errors reported as abstention.** If retrieval threw and no usable
   evidence was selected, the swallowed failure appeared as a knowledge gap.
   `select_evidence()` now raises a sanitized failure so `answer()` returns
   `retrieval_unavailable`. Legitimate zero matches still abstain without an LLM.
3. **Neighbor recovery bypassed section filters.** A numeric passage could pull
   in the preceding chunk from another section. Recovery now uses the existing
   `candidate_indices()` rules. Optional filters and their AND semantics remain
   unchanged; no category filtering was added.
4. **The first answer reconstructed quotes unnecessarily.** Literal quote candidates
   were previously supplied only during repair. Both requests now receive source-derived
   excerpts, with the same strict quote validator. Candidates are suggestions, not
   proof of relevance. No punctuation correction, fuzzy matching or quote snapping
   was introduced. This adds prompt content; no cost/latency improvement is claimed.
5. **A bad repaired claim discarded valid siblings.** After the single completed
   repair, a mixed valid/invalid answer may retain only claims that independently
   pass the unchanged validator. It is always marked `partial`, with an omission
   warning and any missing-paper warning. Citation numbering/provenance are rebuilt
   by the same renderer. If nothing validates, it remains an error. API and schema
   failures remain errors, never successful partial answers or abstentions.

## Verification and interface

```bash
.venv/bin/python -m pytest tests/test_generation_reliability.py -q
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m pip check
```

Focused tests cover scoped and broad comparisons, a missing paper, empty filtered
results, retrieval errors, citation provenance, malformed repair, API errors, and
root-dotenv loading without network calls. The full suite includes the existing
strict quotation and source-ID regression tests.

The unchanged public method is:

```python
result = generator.answer(
    question,
    paper_ids=None,
    answer_type="auto",
    year=None,
    author=None,
    section=None,
)
payload = result.model_dump(mode="json")
```

Real hybrid retrieval was also connected to a mocked generator to verify ordinary
QA, filtered QA, both-paper comparison provenance, and no-match abstention without
additional hosted requests. The public response schema remains version 1.0.

## Limits

An exact quote proves provenance, not semantic entailment. These changes do not
guarantee that every accepted claim is correct, that selected evidence covers every
requested detail, or that a model's abstention/status decision is justified.
Section and aspect inference remain heuristic. The post-edit comparison/repair
changes need human assessment and a future controlled live evaluation; no additional
paid call or 117-question benchmark was run. Judge reliability and API dollar-cost
tracking were deliberately left for a separate session.

## Final review and abstention checks

Final review preserves the model's specific missing-component limitations when
salvaging a validated subset after repair. Previously that path retained retrieval
gaps and a generic omission warning but dropped the model's original qualifications.

Empty/flagged evidence and filters with zero matches abstain without inference.
An unknown paper requests clarification. Nonempty but irrelevant passages can
produce a model-directed abstention, with no claims or citations; partial answers
retain supported claims and explicit missing-component explanations. Missing-paper
comparisons cannot become complete, and synthesis still requires both papers.
Retrieval/API failures remain explicit errors (usable evidence after a partial
retrieval failure may yield a qualified partial answer).

There is **no reliable local semantic relevance or entailment detector**. A regression
fixture deliberately demonstrates that a fabricated claim with a real but unrelated
quote passes reference-integrity validation. Tests of model-directed abstention
verify orchestration, not that a live model always chooses abstention correctly.
Existing prompts already require abstention for unrelated evidence; no arbitrary
similarity cutoff or additional model call was introduced. Human-reviewed unsupported
cases remain a release requirement.
