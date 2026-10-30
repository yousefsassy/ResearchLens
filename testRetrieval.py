
from src.retrieval import ResearchRetriever

retriever = ResearchRetriever()

queries = [
    "What is SelfCheckGPT and how does it detect hallucinations?",
    "SelfCheckGPT sampling multiple responses consistency factual hallucinations",
    "SelfCheckGPT proposed method methodology how it works",
]

for query in queries:
    print("\n" + "=" * 70)
    print("QUERY:", query)

    results = retriever.search(
        question=query,
        top_k=8,
        mode="hybrid",
        rerank=False,
        paper_ids=["P002"],
        exclude_flagged=True,
    )

    for rank, row in enumerate(results, 1):
        print(
            f"{rank}. {row['chunk_id']} | "
            f"page {row['pdf_page']} | "
            f"RRF {row.get('rrf_score', 0):.5f}"
        )
