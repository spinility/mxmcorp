"""
Conversation Manager - Gestion intelligente de l'historique avec résumés

Système de résumé hiérarchique:
- Sections de 5000 tokens → résumé automatique de section
- Quand toutes sections atteignent 10k tokens → résumé global + nouvelle section
- Garde trace des nouveaux messages non-résumés
"""

import json
import tiktoken
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier


@dataclass
class ConversationSection:
    """Une section de conversation avec son résumé"""
    id: str
    messages: List[Dict[str, str]]  # Messages bruts
    summary: Optional[str]  # Résumé de cette section (None si pas encore résumé)
    token_count: int  # Nombre de tokens dans cette section
    created_at: str
    summarized_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dict pour JSON"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationSection':
        """Crée une section depuis un dict"""
        return cls(**data)


class ConversationManager:
    """
    Gestionnaire d'historique de conversation avec résumés automatiques

    Architecture:
    - Sections de ~5000 tokens (nouvelle conversation active)
    - Quand section atteint 5000 tokens → résumé + nouvelle section
    - Quand toutes sections totalisent 10k tokens → résumé global
    """

    SECTION_TOKEN_THRESHOLD = 5000  # Seuil pour résumer une section
    GLOBAL_TOKEN_THRESHOLD = 10000  # Seuil pour résumé global

    def __init__(
        self,
        llm_client: LLMClient,
        storage_path: str = "cortex/data/conversation_history.json"
    ):
        """
        Initialize Conversation Manager

        Args:
            llm_client: Client LLM pour générer les résumés
            storage_path: Chemin du fichier JSON de stockage
        """
        self.llm_client = llm_client
        self.storage_path = Path(storage_path)
        self.sections: List[ConversationSection] = []
        self.current_section: ConversationSection = self._create_new_section()
        self.global_summary: Optional[str] = None

        # Encoder tiktoken pour compter les tokens
        try:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoder = None

        self._load()

    def _create_new_section(self) -> ConversationSection:
        """Crée une nouvelle section vide"""
        section_id = f"section_{len(self.sections) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return ConversationSection(
            id=section_id,
            messages=[],
            summary=None,
            token_count=0,
            created_at=datetime.now().isoformat()
        )

    def _count_tokens(self, text: str) -> int:
        """Compte le nombre de tokens dans un texte"""
        if self.encoder:
            return len(self.encoder.encode(text))
        else:
            # Fallback: approximation (1 token ≈ 4 caractères)
            return len(text) // 4

    def _count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Compte les tokens dans une liste de messages"""
        total = 0
        for msg in messages:
            content = msg.get('content', '')
            total += self._count_tokens(content)
        return total

    def _load(self):
        """Charge l'historique depuis le fichier"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sections = [
                        ConversationSection.from_dict(s)
                        for s in data.get('sections', [])
                    ]
                    self.global_summary = data.get('global_summary')

                    # Charger la section courante
                    current_data = data.get('current_section')
                    if current_data:
                        self.current_section = ConversationSection.from_dict(current_data)
                    else:
                        self.current_section = self._create_new_section()
            except Exception as e:
                print(f"Warning: Failed to load conversation history: {e}")
                self.sections = []
                self.current_section = self._create_new_section()
        else:
            # Créer le répertoire si nécessaire
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _save(self):
        """Sauvegarde l'historique dans le fichier"""
        try:
            data = {
                'sections': [section.to_dict() for section in self.sections],
                'current_section': self.current_section.to_dict(),
                'global_summary': self.global_summary,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error: Failed to save conversation history: {e}")

    def add_message(self, role: str, content: str):
        """
        Ajoute un message à la conversation
        Déclenche automatiquement les résumés si nécessaire

        Args:
            role: "user", "assistant", ou "system"
            content: Contenu du message
        """
        message = {"role": role, "content": content}
        self.current_section.messages.append(message)

        # Mettre à jour le compteur de tokens
        self.current_section.token_count = self._count_messages_tokens(
            self.current_section.messages
        )

        # Vérifier si on doit résumer la section courante
        if self.current_section.token_count >= self.SECTION_TOKEN_THRESHOLD:
            self._summarize_current_section()

        # Vérifier si on doit faire un résumé global
        total_tokens = self._get_total_tokens()
        if total_tokens >= self.GLOBAL_TOKEN_THRESHOLD:
            self._create_global_summary()

        self._save()

    def _summarize_current_section(self):
        """Résume la section courante et crée une nouvelle section"""
        if not self.current_section.messages:
            return

        print("\n🔄 Résumé automatique de la section en cours...")

        # Créer un prompt de résumé
        messages_text = "\n\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in self.current_section.messages
        ])

        summary_prompt = f"""Résume cette section de conversation de manière concise mais complète.
Garde tous les détails techniques importants, les décisions prises, et le contexte nécessaire pour continuer la conversation.

CONVERSATION:
{messages_text}

RÉSUMÉ (format structuré):"""

        # Utiliser DeepSeek pour le résumé (économique)
        try:
            response = self.llm_client.complete(
                messages=[{"role": "user", "content": summary_prompt}],
                tier=ModelTier.DEEPSEEK,
                max_tokens=1000,
                temperature=0.3
            )

            self.current_section.summary = response.content
            self.current_section.summarized_at = datetime.now().isoformat()

            # Archiver la section
            self.sections.append(self.current_section)

            # Créer une nouvelle section
            self.current_section = self._create_new_section()

            print(f"✓ Section résumée ({len(self.sections)} sections totales)")

        except Exception as e:
            print(f"⚠️  Erreur lors du résumé de section: {e}")

    def _create_global_summary(self):
        """Crée un résumé global et réinitialise les sections"""
        if not self.sections:
            return

        print("\n🔄 Résumé global de toutes les sections...")

        # Collecter tous les résumés de sections
        section_summaries = []
        for section in self.sections:
            if section.summary:
                section_summaries.append(f"Section {section.id}:\n{section.summary}")

        # Ajouter la section courante si elle a du contenu
        if self.current_section.messages:
            messages_text = "\n".join([
                f"{msg['role']}: {msg['content'][:200]}..."
                for msg in self.current_section.messages
            ])
            section_summaries.append(f"Section courante (non résumée):\n{messages_text}")

        all_summaries = "\n\n---\n\n".join(section_summaries)

        global_prompt = f"""Crée un résumé global ultra-condensé de toute cette conversation.
Ce résumé sera le contexte de base pour les futures conversations.
Inclus UNIQUEMENT les informations essentielles et critiques.

SECTIONS:
{all_summaries}

RÉSUMÉ GLOBAL (maximum 500 mots):"""

        # Utiliser DeepSeek pour le résumé global
        try:
            response = self.llm_client.complete(
                messages=[{"role": "user", "content": global_prompt}],
                tier=ModelTier.DEEPSEEK,
                max_tokens=800,
                temperature=0.3
            )

            # Combiner avec le résumé global précédent si existe
            if self.global_summary:
                self.global_summary = f"{self.global_summary}\n\n---NOUVEAU CYCLE---\n\n{response.content}"
            else:
                self.global_summary = response.content

            # Réinitialiser les sections (on garde que le résumé global)
            self.sections = []

            print(f"✓ Résumé global créé, sections réinitialisées")

        except Exception as e:
            print(f"⚠️  Erreur lors du résumé global: {e}")

    def _get_total_tokens(self) -> int:
        """Calcule le nombre total de tokens de toutes les sections"""
        total = sum(section.token_count for section in self.sections)
        total += self.current_section.token_count
        return total

    def get_context_for_llm(self, max_tokens: int = 4000) -> List[Dict[str, str]]:
        """
        Construit le contexte optimal pour un appel LLM

        Priorité:
        1. Résumé global (si existe)
        2. Résumés des sections archivées
        3. Messages bruts de la section courante

        Args:
            max_tokens: Limite de tokens pour le contexte

        Returns:
            Liste de messages optimisée
        """
        context_messages = []
        token_budget = max_tokens

        # 1. Ajouter le résumé global si existe
        if self.global_summary:
            summary_msg = {
                "role": "system",
                "content": f"CONTEXTE GLOBAL PRÉCÉDENT:\n{self.global_summary}"
            }
            tokens = self._count_tokens(summary_msg['content'])
            if tokens < token_budget:
                context_messages.append(summary_msg)
                token_budget -= tokens

        # 2. Ajouter les résumés de sections (les plus récentes en premier)
        for section in reversed(self.sections[-5:]):  # Max 5 dernières sections
            if section.summary and token_budget > 200:
                section_msg = {
                    "role": "system",
                    "content": f"SECTION PRÉCÉDENTE:\n{section.summary}"
                }
                tokens = self._count_tokens(section_msg['content'])
                if tokens < token_budget:
                    context_messages.insert(1 if self.global_summary else 0, section_msg)
                    token_budget -= tokens

        # 3. Ajouter les messages bruts de la section courante
        for msg in self.current_section.messages:
            tokens = self._count_tokens(msg['content'])
            if tokens < token_budget:
                context_messages.append(msg)
                token_budget -= tokens
            else:
                break

        return context_messages

    def get_statistics(self) -> Dict[str, Any]:
        """Obtient des statistiques sur l'historique"""
        return {
            'total_sections': len(self.sections),
            'current_section_messages': len(self.current_section.messages),
            'current_section_tokens': self.current_section.token_count,
            'total_tokens': self._get_total_tokens(),
            'has_global_summary': self.global_summary is not None,
            'section_threshold': self.SECTION_TOKEN_THRESHOLD,
            'global_threshold': self.GLOBAL_TOKEN_THRESHOLD
        }

    def clear_history(self):
        """Efface tout l'historique"""
        self.sections = []
        self.current_section = self._create_new_section()
        self.global_summary = None
        self._save()


def create_conversation_manager(
    llm_client: LLMClient,
    storage_path: str = "cortex/data/conversation_history.json"
) -> ConversationManager:
    """Factory function pour créer un ConversationManager"""
    return ConversationManager(llm_client, storage_path)


# Test si exécuté directement
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("Testing Conversation Manager...")

    client = LLMClient()
    manager = ConversationManager(client, "cortex/data/test_conversation.json")

    # Test: Ajouter des messages
    print("\n1. Adding messages...")
    manager.add_message("user", "Hello, I need help with authentication")
    manager.add_message("assistant", "I can help you with that. What authentication method?")

    # Stats
    stats = manager.get_statistics()
    print(f"Stats: {stats}")

    print("\n✓ Conversation Manager works correctly!")
