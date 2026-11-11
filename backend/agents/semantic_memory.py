"""Small deterministic local embeddings for semantic retrieval of chat memory.

The embedding path is offline, has no extra model download, and does not send
chat history to a second service. It is intentionally a compact memory index,
not a general-purpose semantic search model.
"""

import hashlib
import math
import re
from typing import Any


DIMENSIONS = 512
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "for", "from",
    "how", "i", "in", "is", "it", "me", "of", "on", "or", "our", "the",
    "to", "was", "what", "when", "where", "which", "who", "why", "with",
}
CONCEPT_GROUPS = (
    ("north_star", "polaris", "northstar", "pole_star", "celestial_pole"),
    ("orbit", "trajectory", "orbital", "path", "flyby"),
    ("season", "spring", "summer", "autumn", "fall", "winter", "solstice", "equinox"),
    ("constellation", "asterism", "star_pattern", "star_map"),
    ("distance", "au", "astronomical_unit", "lightyear", "light_year"),
    ("precession", "axial_wobble", "pole_cycle"),
    ("asteroid", "neo", "near_earth_object", "apophis", "bennu"),
    ("comet", "halley", "neowise"),
)
ALIASES = {alias: group[0] for group in CONCEPT_GROUPS for alias in group}


def _features(text: str) -> list[tuple[str, float]]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    normalized = [ALIASES.get(word, word) for word in words if word not in STOP_WORDS]
    features: list[tuple[str, float]] = [(f"w:{word}", 1.0) for word in normalized]
    features.extend((f"b:{left}_{right}", 0.55) for left, right in zip(normalized, normalized[1:]))
    for word in set(normalized):
        padded = f"^{word}$"
        features.extend((f"c:{padded[i:i + 3]}", 0.18) for i in range(max(0, len(padded) - 2)))
    return features


def embed_text(text: str) -> list[float]:
    """Return a signed feature-hash embedding with a stable 512 element shape."""
    vector = [0.0] * DIMENSIONS
    for feature, weight in _features(text):
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        vector[value % DIMENSIONS] += weight if value & (1 << 63) else -weight
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def retrieve_relevant_memory(query: str, memories: list[dict[str, Any]], limit: int = 4) -> list[dict[str, Any]]:
    """Rank saved turns by embedding cosine similarity, with recency as a tie-breaker."""
    query_vector = embed_text(query)
    ranked = []
    for index, memory in enumerate(memories):
        vector = embed_text(memory.get("message", ""))
        score = sum(left * right for left, right in zip(query_vector, vector))
        ranked.append((score, index, memory))
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    selected = [(score, memory) for score, _, memory in ranked if score > 0.04][:limit]
    selected.sort(key=lambda item: item[1].get("timestamp", 0))
    return [{**memory, "relevance": round(score, 3)} for score, memory in selected]
