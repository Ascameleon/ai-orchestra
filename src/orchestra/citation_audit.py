"""Deterministic citation-presence audit for generated answer text.

This is a formatting/integrity screen only. It cannot establish that cited
sources support a sentence, nor reliably distinguish factual from non-factual prose.
"""
import re
from dataclasses import dataclass

# Capture the complete token so overlong IDs are reported as invalid instead of
# silently disappearing from the audit. The input answer is bounded at the API.
_CITATION = re.compile(r"\[(ev_[^\]\s]+)\]")
# Split after terminal punctuation and any closing quotation/bracket characters.
# Without the optional closers, e.g. 'Claim [ev_id].” Next claim.' is counted
# as one sentence and can falsely inflate sentence-level citation coverage.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?؟。｡！？])[\\"'”’»）)\]]*\s+(?=\S)")


@dataclass(frozen=True)
class CitationCoverage:
    sentence_count: int
    sentences_with_valid_citations: int
    uncited_sentence_count: int
    invalid_citation_ids: tuple[str, ...]
    coverage_ratio: float


def audit_citation_coverage(
    answer: str,
    known_evidence_ids: set[str] | frozenset[str],
) -> CitationCoverage:
    """Measure sentence-level citation presence and unknown IDs without judging entailment."""
    if not isinstance(answer, str):
        raise TypeError("answer must be a string")
    if not isinstance(known_evidence_ids, (set, frozenset)):
        raise TypeError("known_evidence_ids must be a set or frozenset of non-empty strings")
    if any(not isinstance(item, str) for item in known_evidence_ids):
        raise TypeError("known evidence IDs must be strings")
    if any(not item.strip() for item in known_evidence_ids):
        raise ValueError("known evidence IDs must be non-empty strings")
    normalized_ids = {item.strip() for item in known_evidence_ids}
    if len(normalized_ids) != len(known_evidence_ids):
        raise ValueError("known evidence IDs collide after whitespace normalization")

    sentences: list[str] = []
    for line in answer.splitlines():
        normalized = line.strip()
        if not normalized:
            continue
        # Markdown headings alone do not make a factual sentence.
        normalized = re.sub(r"^#{1,6}\\s+", "", normalized)
        if not normalized or normalized in {"-", "*", "•"}:
            continue
        sentences.extend(
            part.strip()
            for part in _SENTENCE_SPLIT.split(normalized)
            if part.strip()
        )

    valid_cited_sentences = 0
    invalid_ids: list[str] = []
    for sentence in sentences:
        ids = _CITATION.findall(sentence)
        if any(evidence_id in normalized_ids for evidence_id in ids):
            valid_cited_sentences += 1
        invalid_ids.extend(evidence_id for evidence_id in ids if evidence_id not in normalized_ids)

    count = len(sentences)
    return CitationCoverage(
        sentence_count=count,
        sentences_with_valid_citations=valid_cited_sentences,
        uncited_sentence_count=count - valid_cited_sentences,
        invalid_citation_ids=tuple(dict.fromkeys(invalid_ids)),
        coverage_ratio=(valid_cited_sentences / count) if count else 0.0,
    )
