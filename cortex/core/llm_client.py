"""
LLM Client - Client unifié pour tous les modèles LLM
Gère OpenAI, DeepSeek, et Anthropic via une interface commune
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Imports conditionnels
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from .config_loader import get_config
from .model_router import ModelTier


@dataclass
class LLMResponse:
    """Réponse standardisée d'un LLM"""
    content: str
    model: str
    tokens_input: int
    tokens_output: int
    cost: float
    finish_reason: str


class LLMClient:
    """
    Client unifié pour tous les LLMs
    Interface commune pour OpenAI, DeepSeek, et Anthropic
    """

    def __init__(self):
        self.config = get_config()

        # Initialiser les clients
        self._init_clients()

        # Cache des coûts par modèle
        self.models_config = self.config.models.get("models", {})

    def _init_clients(self):
        """Initialise les clients API"""
        # OpenAI (gpt-5-nano)
        openai_key = self.config.get("api_keys.openai_key")
        if openai_key and OpenAI:
            self.openai_client = OpenAI(api_key=openai_key)
        else:
            self.openai_client = None

        # DeepSeek (deepseek-v3.2-exp)
        deepseek_key = self.config.get("api_keys.deepseek_key")
        if deepseek_key and OpenAI:
            # DeepSeek utilise API compatible OpenAI
            self.deepseek_client = OpenAI(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com"
            )
        else:
            self.deepseek_client = None

        # Anthropic (claude-sonnet-4-5)
        anthropic_key = self.config.get("api_keys.anthropic_key")
        if anthropic_key and Anthropic:
            self.anthropic_client = Anthropic(api_key=anthropic_key)
        else:
            self.anthropic_client = None

    def complete(
        self,
        messages: List[Dict[str, str]],
        tier: ModelTier,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Génère une complétion avec le modèle spécifié

        Args:
            messages: Liste de messages au format [{"role": "user", "content": "..."}]
            tier: Tier du modèle (NANO, DEEPSEEK, CLAUDE)
            max_tokens: Tokens maximum de sortie
            temperature: Température (0-1)
            **kwargs: Paramètres additionnels

        Returns:
            LLMResponse avec le contenu et les métadonnées
        """
        if tier == ModelTier.NANO:
            return self._complete_openai(messages, max_tokens, temperature, **kwargs)
        elif tier == ModelTier.DEEPSEEK:
            return self._complete_deepseek(messages, max_tokens, temperature, **kwargs)
        elif tier == ModelTier.CLAUDE:
            return self._complete_anthropic(messages, max_tokens, temperature, **kwargs)
        else:
            raise ValueError(f"Unknown model tier: {tier}")

    def _complete_openai(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> LLMResponse:
        """Complétion via OpenAI (gpt-5-nano)"""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized. Check API key.")

        model_config = self.models_config.get("nano", {})
        model_name = model_config.get("name", "gpt-3.5-turbo")  # Fallback à un modèle existant et économique

        try:
            # Préparer les paramètres, exclure temperature=1 (default)
            params = {
                "model": model_name,
                "messages": messages,
                "max_tokens": max_tokens if model_name == "gpt-3.5-turbo" else None,
                "max_completion_tokens": max_tokens if model_name != "gpt-3.5-turbo" else None,
                **kwargs
            }

            # Ajouter temperature seulement si différent de 1
            if temperature != 1.0:
                params["temperature"] = temperature

            # Retirer None values
            params = {k: v for k, v in params.items() if v is not None}

            response = self.openai_client.chat.completions.create(**params)

            content = response.choices[0].message.content
            tokens_input = response.usage.prompt_tokens
            tokens_output = response.usage.completion_tokens

            # Calculer le coût
            cost = self._calculate_cost(
                "nano",
                tokens_input,
                tokens_output
            )

            return LLMResponse(
                content=content,
                model=model_name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost=cost,
                finish_reason=response.choices[0].finish_reason
            )

        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")

    def _complete_deepseek(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> LLMResponse:
        """Complétion via DeepSeek"""
        if not self.deepseek_client:
            raise RuntimeError("DeepSeek client not initialized. Check API key.")

        model_config = self.models_config.get("deepseek", {})
        model_name = model_config.get("name", "deepseek-chat")

        try:
            response = self.deepseek_client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_completion_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            content = response.choices[0].message.content
            tokens_input = response.usage.prompt_tokens
            tokens_output = response.usage.completion_tokens

            # Calculer le coût
            cost = self._calculate_cost(
                "deepseek",
                tokens_input,
                tokens_output
            )

            return LLMResponse(
                content=content,
                model=model_name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost=cost,
                finish_reason=response.choices[0].finish_reason
            )

        except Exception as e:
            raise RuntimeError(f"DeepSeek API error: {e}")

    def _complete_anthropic(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> LLMResponse:
        """Complétion via Anthropic (Claude)"""
        if not self.anthropic_client:
            raise RuntimeError("Anthropic client not initialized. Check API key.")

        model_config = self.models_config.get("claude", {})
        model_name = model_config.get("name", "claude-sonnet-4-20250514")

        # Convertir le format des messages pour Anthropic
        system_message = None
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        try:
            response = self.anthropic_client.messages.create(
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=anthropic_messages,
                **kwargs
            )

            content = response.content[0].text
            tokens_input = response.usage.input_tokens
            tokens_output = response.usage.output_tokens

            # Calculer le coût
            cost = self._calculate_cost(
                "claude",
                tokens_input,
                tokens_output
            )

            return LLMResponse(
                content=content,
                model=model_name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost=cost,
                finish_reason=response.stop_reason
            )

        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {e}")

    def _calculate_cost(
        self,
        tier: str,
        tokens_input: int,
        tokens_output: int
    ) -> float:
        """Calcule le coût d'un appel"""
        model_config = self.models_config.get(tier, {})

        cost_per_1m_input = model_config.get("cost_per_1m_input", 0.0)
        cost_per_1m_output = model_config.get("cost_per_1m_output", 0.0)

        input_cost = (tokens_input / 1_000_000) * cost_per_1m_input
        output_cost = (tokens_output / 1_000_000) * cost_per_1m_output

        return input_cost + output_cost

    def is_available(self, tier: ModelTier) -> bool:
        """Vérifie si un tier de modèle est disponible"""
        if tier == ModelTier.NANO:
            return self.openai_client is not None
        elif tier == ModelTier.DEEPSEEK:
            return self.deepseek_client is not None
        elif tier == ModelTier.CLAUDE:
            return self.anthropic_client is not None
        return False


# Test du client
if __name__ == "__main__":
    import sys

    client = LLMClient()

    # Vérifier disponibilité
    print("Available models:")
    print(f"  Nano (OpenAI): {client.is_available(ModelTier.NANO)}")
    print(f"  DeepSeek: {client.is_available(ModelTier.DEEPSEEK)}")
    print(f"  Claude: {client.is_available(ModelTier.CLAUDE)}")

    if not any([
        client.is_available(ModelTier.NANO),
        client.is_available(ModelTier.DEEPSEEK),
        client.is_available(ModelTier.CLAUDE)
    ]):
        print("\nNo API keys configured. Please set up .env file.")
        sys.exit(1)

    # Test avec le modèle le moins cher disponible
    print("\nTesting with simple prompt...")

    messages = [
        {"role": "user", "content": "Say 'Hello from Cortex MXMCorp!' in one sentence."}
    ]

    # Essayer deepseek d'abord (plus stable et économique)
    if client.is_available(ModelTier.DEEPSEEK):
        tier = ModelTier.DEEPSEEK
    elif client.is_available(ModelTier.CLAUDE):
        tier = ModelTier.CLAUDE
    elif client.is_available(ModelTier.NANO):
        tier = ModelTier.NANO
    else:
        print("No models available")
        sys.exit(1)

    print(f"Using tier: {tier.value}")

    try:
        response = client.complete(messages, tier, max_tokens=100, temperature=1.0)
        print(f"\nModel: {response.model}")
        print(f"Response: {response.content}")
        print(f"Tokens: {response.tokens_input} in, {response.tokens_output} out")
        print(f"Cost: ${response.cost:.6f}")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
