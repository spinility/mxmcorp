"""
LLM Model Specifications - HARD LIMITS ENFORCED BY APIS
DO NOT MODIFY - These are the actual limits from the API providers
"""

from types import MappingProxyType

# Spécifications officielles des modèles LLM
# Ces valeurs sont des limites strictes imposées par les APIs
_LLM_SPECS = {
    "gpt-5-nano": {
        "context_window": 400_000,
        "max_output_tokens": 128_000,
    },
    "deepseek-reasoner": {
        "context_window": 128_000,
        "max_output_tokens": 64_000,
    },
    "gpt-5": {
        "context_window": 400_000,
        "max_output_tokens": 128_000,
    },
    "claude-sonnet-4-5": {
        "context_window": 200_000,
        "max_output_tokens": 64_000,
    },
}

# Freeze la configuration pour empêcher toute modification
LLM_SPECS = MappingProxyType({
    k: MappingProxyType(v) for k, v in _LLM_SPECS.items()
})


def get_max_output_tokens(model_name: str) -> int:
    """
    Récupère la limite maximale de tokens de sortie pour un modèle

    Args:
        model_name: Nom du modèle (ex: "gpt-5-nano", "deepseek-reasoner")

    Returns:
        Nombre maximum de tokens de sortie

    Raises:
        KeyError: Si le modèle n'existe pas
    """
    if model_name not in LLM_SPECS:
        raise KeyError(f"Unknown model: {model_name}. Available: {list(LLM_SPECS.keys())}")

    return LLM_SPECS[model_name]["max_output_tokens"]


def get_context_window(model_name: str) -> int:
    """
    Récupère la taille de la fenêtre de contexte pour un modèle

    Args:
        model_name: Nom du modèle

    Returns:
        Nombre maximum de tokens dans la fenêtre de contexte

    Raises:
        KeyError: Si le modèle n'existe pas
    """
    if model_name not in LLM_SPECS:
        raise KeyError(f"Unknown model: {model_name}. Available: {list(LLM_SPECS.keys())}")

    return LLM_SPECS[model_name]["context_window"]


# Test
if __name__ == "__main__":
    print("LLM Specifications (immutable):")
    print("=" * 60)
    for model, specs in LLM_SPECS.items():
        print(f"\n{model}:")
        print(f"  Context window:    {specs['context_window']:,} tokens")
        print(f"  Max output tokens: {specs['max_output_tokens']:,} tokens")

    print("\n" + "=" * 60)
    print("\n✓ These specifications are IMMUTABLE and enforced by the APIs")

    # Démontrer l'immutabilité
    try:
        LLM_SPECS["gpt-5-nano"]["max_output_tokens"] = 999
    except TypeError as e:
        print(f"\n✓ Modification attempt blocked: {e}")
