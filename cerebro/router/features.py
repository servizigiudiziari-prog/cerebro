"""Feature extraction from a raw query string.

Implements `QueryFeatures` exactly as specified in brief §5.1. Extraction
logic itself is a stub: filled in by the `feat/router-heuristic` issue.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class QueryFeatures:
    """Surface-level features used by the heuristic router.

    Attributes:
        length_tokens: approximate token count (whitespace tokenization for
            Phase 0, no real tokenizer dependency).
        has_code_blocks: presence of triple-backtick or recognizable code
            patterns (def/class/{}/=>) anywhere in the query.
        has_math: presence of formulas, numeric expressions, or math symbols
            (=, +, -, *, /, ^, integral, sigma, etc.).
        has_question_words: presence of WH-words in IT or EN
            (chi/cosa/quando/perché/come, who/what/when/why/how).
        references_past: phrases like "ricordi", "prima", "ieri", "l'altra
            volta", "yesterday", "earlier" suggesting episodic memory.
        references_facts: factual lookup intents like "qual è",
            "quando è nato", "definizione di", "what is", "definition of".
        estimated_complexity: float in [0, 1] based on length, conjunctions,
            nesting, and presence of multi-step intent markers. Exact formula
            is implemented in `_estimate_complexity` and documented inline.
        language: detected language. Phase 0 uses a tiny stoplist heuristic;
            a real detector is out of scope.
    """

    length_tokens: int
    has_code_blocks: bool
    has_math: bool
    has_question_words: bool
    references_past: bool
    references_facts: bool
    estimated_complexity: float
    language: Literal["it", "en", "mixed"]


def extract_features(query: str) -> QueryFeatures:
    """Extract `QueryFeatures` from a raw query.

    Args:
        query: user-provided text. Never None; may be empty.

    Returns:
        Populated `QueryFeatures`.

    Raises:
        NotImplementedError: implementation tracked by issue
            `[Phase 0] Heuristic router with feature extraction`.
    """
    raise NotImplementedError(
        "feature extraction not implemented yet (see GitHub issue: heuristic router)"
    )
