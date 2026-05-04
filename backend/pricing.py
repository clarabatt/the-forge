"""Gemini model pricing table.

Prices are USD per token (i.e. the published $/1M price divided by 1_000_000).
Lookup is exact-match first, then longest-prefix match, then falls back to Flash
tier as a conservative default for unknown/preview models.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPricing:
    input_per_token: float
    output_per_token: float


# Published Google AI pricing as of early 2026 (standard tier, ≤200K context window).
# Source: https://ai.google.dev/pricing
_PRICING: dict[str, ModelPricing] = {
    "gemini-2.5-pro":    ModelPricing(1.25  / 1_000_000, 10.00 / 1_000_000),
    "gemini-2.5-flash":  ModelPricing(0.15  / 1_000_000,  0.60 / 1_000_000),
    "gemini-2.0-flash":  ModelPricing(0.10  / 1_000_000,  0.40 / 1_000_000),
    "gemini-1.5-pro":    ModelPricing(1.25  / 1_000_000,  5.00 / 1_000_000),
    "gemini-1.5-flash":  ModelPricing(0.075 / 1_000_000,  0.30 / 1_000_000),
    # Gemini 3 series (estimated at Flash tier until official pricing is published)
    "gemini-3-pro":      ModelPricing(1.25  / 1_000_000, 10.00 / 1_000_000),
    "gemini-3-flash":    ModelPricing(0.15  / 1_000_000,  0.60 / 1_000_000),
}

# Safe default for models not in the table (Flash-tier pricing)
_FALLBACK = ModelPricing(0.15 / 1_000_000, 0.60 / 1_000_000)


def get_pricing(model: str) -> ModelPricing:
    """Return pricing for a model name.

    Tries exact match, then longest prefix match (handles versioned names like
    "gemini-2.5-flash-preview-05-20"), then falls back to _FALLBACK.
    """
    if model in _PRICING:
        return _PRICING[model]

    # Longest prefix wins so "gemini-2.5-flash-preview" beats "gemini-2.5"
    best_key = max(
        (k for k in _PRICING if model.startswith(k)),
        key=len,
        default=None,
    )
    return _PRICING[best_key] if best_key else _FALLBACK


def token_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return USD cost for the given model and token counts."""
    p = get_pricing(model)
    return input_tokens * p.input_per_token + output_tokens * p.output_per_token
