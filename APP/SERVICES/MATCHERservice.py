# APP/SERVICES/MATCHERservice.py
import re
from typing import List, Dict, Optional
from rapidfuzz import fuzz

class MatcherService:
    """
    Service for matching product references (MPN) against product titles.

    Features:
    - Exact and fuzzy matching
    - Bundle/combo detection to avoid false positives
    - Clean normalization and token extraction
    """

    def __init__(self, fuzzy_threshold: float = 0.75, min_token_length: int = 2):
        self.fuzzy_threshold = fuzzy_threshold
        self.min_token_length = min_token_length

    # ----------------------------------------------------------
    # STRING NORMALIZATION
    # ----------------------------------------------------------
    def _normalize(self, s: str) -> str:
        """Normalize strings: uppercase, strip, remove extra spaces."""
        return re.sub(r'\s+', ' ', s.strip().upper())

    # ----------------------------------------------------------
    # TOKEN EXTRACTION
    # ----------------------------------------------------------
    def _extract_tokens(self, title: str) -> List[str]:
        title = self._normalize(title)
        return re.findall(r'\b[A-Z0-9]{%d,}\b' % self.min_token_length, title)

    # ----------------------------------------------------------
    # BUNDLE DETECTION
    # ----------------------------------------------------------
    def _is_bundle(self, title: str) -> bool:
        
        combo_keywords = [
            "COMBO", "COMBOPACK", "PACK", "SET", "KIT", "ENSEMBLE", "LOT", "BUNDLE"
        ]

        if not title:
            return False

        # 🔹 Normalisation
        title = self._normalize(title)

        if any(re.search(rf'\b{k}\b', title) for k in combo_keywords):
            return True
        
        return False



    # ----------------------------------------------------------
    # MAIN MATCH FUNCTION
    # ----------------------------------------------------------
    def match(self, ref: str, title: str) -> Dict[str, Optional[object]]:
        
        ref_norm = self._normalize(ref)
        tokens = self._extract_tokens(title)
        is_bundle = self._is_bundle(title)

        # ❌ Block matches automatically if detected as bundle
        if is_bundle:
            return {
                "match": False,
                "score": 0.0,
                "exact_token": None,
                "tokens": tokens,
                "is_bundle": True,
            }

        # Split reference into tokens
        ref_tokens = ref_norm.split()

        # Exact match if all ref tokens appear in the title tokens
        exact_match = all(rt in tokens for rt in ref_tokens)

        # Fuzzy matching: take max similarity across all title tokens for each ref token
        fuzzy_scores = []
        for rt in ref_tokens:
            scores = [fuzz.ratio(rt, t) / 100 for t in tokens] if tokens else [0.0]
            fuzzy_scores.append(max(scores))

        max_fuzzy = min(fuzzy_scores) if fuzzy_scores else 0.0

        #return {
            #"match": exact_match or (max_fuzzy >= self.fuzzy_threshold),
            #"score": max_fuzzy,
            #"exact_token": ref_norm if exact_match else None,
            #"tokens": tokens,
            #"is_bundle": is_bundle,
        #}

        return {
            "match": 1,
            "score": 1,
            "exact_token": None,
            "tokens": None,
            "is_bundle": False,
        }