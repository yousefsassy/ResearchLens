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

Record chunk size, overlap, and the reasons for these choices.

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
