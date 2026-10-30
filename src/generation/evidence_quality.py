"""Conservative text-quality signals, never a semantic support verifier.

All scoring uses the original passage; no quote text is rewritten or truncated.
"""
import re
from collections import Counter


ASPECT_PATTERNS = {
    "methods": r"\b(method\w*|approach\w*|algorithm\w*|procedure\w*|framework\w*|"
               r"comput\w*|calculat\w*|compar\w*|sampl\w*|retriev\w*|train\w*|"
               r"evaluat\w*|classif\w*|estimat\w*|decompos\w*|uses?|using|steps?)\b",
    "limitations": r"\b(limit\w*|weakness\w*|assum\w*|restrict\w*|fail\w*|"
                   r"cannot|unable|requires?|depends? on|sensitive to|only works|"
                   r"not applicable|not suitable|does not|do not|computational cost)\b",
    "findings": r"\b(result\w*|finding\w*|experiment\w*|performance|accuracy|"
                r"precision|recall|scores?|achiev\w*|outperform\w*|improv\w*|"
                r"observ\w*|measur\w*|percent|latency|throughput|error rate)\b",
}


def words(text):
    return re.findall(r"\b[a-zA-Z]+\b", text.lower())


def quality(text):
    """Penalize artifact-dominated passages; retain explanatory numeric content."""
    tokens = words(text)
    if len(tokens) < 3:
        return 0.0
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    # Long prose mixed with a table should outweigh short axes/labels.
    prose_words = sum(len(words(line)) for line in lines if len(words(line)) >= 3)
    explanatory = prose_words / len(tokens)
    numeric_lines = sum(bool(re.fullmatch(r"[\d\s.,%()+\-]+", line)) for line in lines)
    references = sum(bool(re.search(r"(?:\[\d+\].*\b(?:19|20)\d{2}\b|"
                                    r"\b(?:19|20)\d{2}\b.*(?:proceedings|journal|doi:))", line, re.I))
                     for line in lines)
    repeated = sum(count - 1 for count in Counter(lines).values()) / len(lines)
    damage = text.count("\ufffd") / max(len(text), 1)
    score = (0.25 + 0.75 * explanatory - 0.4 * numeric_lines / len(lines)
             - 0.65 * references / len(lines) - 0.5 * repeated - min(0.6, damage * 20))
    if len(tokens) < 8:
        score -= 0.15
    if len(set(tokens)) < 3:
        score -= 0.35
    # Labeled quantitative rows can be useful without full prose sentences.
    metric_rows = sum(bool(re.search(r"\b(accuracy|precision|recall|latency|throughput|"
                                     r"score|error|mean|median)\b", line, re.I))
                      and bool(re.search(r"\d", line)) for line in lines)
    if metric_rows >= 2 and len(tokens) >= 5 and not references and not damage:
        score = max(score, 0.5)
    return max(0.0, min(1.0, score))


def supports_aspect(text, aspect):
    """Evidence of aspect discussion, not proof of any generated factual claim.

    Headings alone cannot establish coverage. Numeric tables may support findings
    when metric labels accompany the values. Final support remains with generation.
    """
    if quality(text) < 0.35:
        return False
    pattern = ASPECT_PATTERNS.get(aspect)
    if pattern is None:
        return False
    for sentence in re.split(r"[.!?\n]+", text):
        if len(words(sentence)) >= 4 and re.search(pattern, sentence, re.I):
            return True
    return (aspect == "findings" and len(words(text)) >= 5
            and bool(re.search(pattern, text, re.I)) and bool(re.search(r"\d", text)))


def near_duplicate(left, right):
    """Suppress strongly overlapping text within a paper, retaining changed numbers."""
    if left.paper_id != right.paper_id:
        return False
    a, b = left.text.split(), right.text.split()
    if a == b:
        return True
    if min(len(a), len(b)) < 12:
        return False
    if re.findall(r"\d+(?:\.\d+)?", left.text) != re.findall(r"\d+(?:\.\d+)?", right.text):
        return False
    negation = r"\b(?:no|not|never|cannot|without|unable)\b|n't\b"
    if re.findall(negation, left.text.lower()) != re.findall(negation, right.text.lower()):
        return False
    sa = {tuple(a[i:i + 4]) for i in range(len(a) - 3)}
    sb = {tuple(b[i:i + 4]) for i in range(len(b) - 3)}
    return len(sa & sb) / len(sa | sb) >= 0.85
