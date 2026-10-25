# Corpus Notes

## Scope

Hallucinations in text-based large language models:
detection, evaluation, and mitigation.

## Selection criteria

- English research papers
- Relevant to the scope
- Text-based PDFs
- No duplicate versions
- Source and license information recorded

## Extraction problems

Record damaged tables, incorrect reading order, and missing text here.

## Cleaning decisions

Record what is removed or changed and why.

## Chunking decisions

### Chunking strategy

The cleaned research papers are divided into smaller text chunks for downstream retrieval-augmented generation (RAG).

**Implementation:** `src/ingestion/chunk.py`

**Configuration:**

- Target chunk size: 1,500 characters
- Overlap: approximately 200 characters
- Splitting strategy: paragraph-aware, with sentence-based splitting for oversized paragraphs
- Page boundaries: preserved
- Output: `data/processed/chunks.jsonl`

**Design decisions:**

1. Paragraph boundaries are preferred to preserve semantic coherence.
2. Overlap helps retain context between adjacent chunks.
3. Each chunk retains its paper ID, PDF filename, and PDF page number to support traceable citations.
4. Cleaning review flags are propagated to chunks so potentially problematic source pages can be identified during retrieval.
5. Original extracted and cleaned page files remain unchanged.

**Validation results:**

- Input: 156 cleaned PDF pages across 5 research papers
- Output: 612 chunks
- Invalid records: 0
- Duplicate chunk IDs: 0
- Empty chunks: 0
- Chunks exceeding 1,800 characters: 0
- Chunks carrying page-level review flags: 245

Chunking is structurally validated. Manual inspection of short chunks and flagged source regions remains necessary before treating all chunks as reliable evidence.

**Post-chunking cleanup:**

Manual inspection of short chunks identified PDF formatting artifacts.
Four targeted corrections were applied during the cleaning stage:

- P001, pages 31, 50, and 53: removed repeated running headers.
- P003, page 24: removed a page-number footer (`12099`).

After regeneration, the total number of chunks decreased from 615 to 612.
Legitimate short passages, figure captions, and section headings were preserved.

The pipeline is structurally validated. However, flagged source regions
still require manual verification before being used as reliable evidence.

## P002 — SelfCheckGPT extraction inspection

- PDF pages: 14.
- Extracted page markers: 14, in order.
- Checked prose in the conclusions and limitations is readable.
- Page 1: figure and footnote content interrupts introduction text.
- Page 3: equations contain corrupted mathematical symbols.
- Page 9, Table 4: two model columns are merged.
- Page 12: appendix text has a column-order problem.
- Page 13, Table 5: table headers are fragmented.
- Printed page numbers and figure-text fragments remain.

### Processing decisions

- Preserve the original extraction.
- Write cleaned content to a separate file.
- Preserve paper IDs and PDF page references.
- Flag damaged equations, tables, and reading-order regions.
- Do not use unverified damaged regions as answer evidence.
- Retain useful figure captions.
