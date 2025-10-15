"""
Partial Update System - Système d'updates partiels
LE système le plus important pour économiser des tokens

Au lieu d'envoyer tout le contexte à chaque fois, on envoie seulement
ce qui a changé. Peut économiser 70-95% des tokens.
"""

import difflib
import json
from typing import Any, Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass


class UpdateMethod(Enum):
    """Méthodes d'update partiel disponibles"""
    FULL = "full"                    # Full update (fallback)
    GIT_DIFF = "git_diff_style"      # Style diff git (code)
    JSON_PATCH = "json_patch"        # RFC 6902 (JSON/data)
    INCREMENTAL = "incremental"      # État incrémental (text)
    CONTEXT_REUSE = "context_reuse"  # Réutilisation contexte


@dataclass
class UpdateResult:
    """Résultat d'un update"""
    method: UpdateMethod
    content: Any
    token_savings: float  # Ratio 0.0-1.0 (ex: 0.85 = 85% économisé)
    original_tokens: int
    updated_tokens: int


class PartialUpdater:
    """
    Système intelligent d'updates partiels
    Choisit automatiquement la meilleure stratégie
    """

    def __init__(self, change_threshold: float = 0.3):
        """
        Args:
            change_threshold: Si changement < seuil, utiliser update partiel
                            Ex: 0.3 = si <30% changé, update partiel
        """
        self.change_threshold = change_threshold
        self.context_cache: Dict[str, Any] = {}  # Cache des contextes précédents

    def should_use_partial_update(
        self,
        old_content: str,
        new_content: str
    ) -> bool:
        """
        Détermine si un update partiel est bénéfique

        Returns:
            True si update partiel recommandé
        """
        if not old_content:
            return False  # Pas de contexte précédent

        # Calculer le ratio de changement
        change_ratio = self._calculate_change_ratio(old_content, new_content)

        return change_ratio < self.change_threshold

    def create_update(
        self,
        old_content: Any,
        new_content: Any,
        content_type: str = "text",
        context_id: Optional[str] = None
    ) -> UpdateResult:
        """
        Crée un update optimal (partiel si possible)

        Args:
            old_content: Contenu précédent
            new_content: Nouveau contenu
            content_type: "code", "json", "text", "data"
            context_id: ID pour le cache de contexte

        Returns:
            UpdateResult avec méthode et contenu optimisés
        """
        # Convertir en string si nécessaire
        old_str = self._to_string(old_content)
        new_str = self._to_string(new_content)

        # Calculer tokens originaux (approximation)
        original_tokens = self._estimate_tokens(old_str + new_str)

        # Vérifier si update partiel est bénéfique
        if not self.should_use_partial_update(old_str, new_str):
            # Full update
            return UpdateResult(
                method=UpdateMethod.FULL,
                content=new_content,
                token_savings=0.0,
                original_tokens=original_tokens,
                updated_tokens=original_tokens
            )

        # Choisir la meilleure méthode selon le type
        if content_type == "code":
            return self._create_git_diff_update(old_str, new_str, original_tokens)

        elif content_type == "json":
            return self._create_json_patch_update(old_content, new_content, original_tokens)

        elif content_type == "text":
            return self._create_incremental_update(old_str, new_str, original_tokens)

        else:  # data
            return self._create_context_reuse_update(
                old_content, new_content, original_tokens, context_id
            )

    def _create_git_diff_update(
        self,
        old_str: str,
        new_str: str,
        original_tokens: int
    ) -> UpdateResult:
        """
        Crée un update style git diff (optimal pour code)

        Example:
            @@ -12,3 +12,4 @@
             def hello():
            -    print("old")
            +    print("new")
            +    return True
        """
        old_lines = old_str.splitlines(keepends=True)
        new_lines = new_str.splitlines(keepends=True)

        # Générer le diff unifié
        diff = list(difflib.unified_diff(
            old_lines,
            new_lines,
            lineterm='',
            n=3  # 3 lignes de contexte
        ))

        if not diff:
            # Pas de changement
            return UpdateResult(
                method=UpdateMethod.GIT_DIFF,
                content=new_str,
                token_savings=0.0,
                original_tokens=original_tokens,
                updated_tokens=original_tokens
            )

        # Combiner le diff en string
        diff_content = '\n'.join(diff)

        # Créer le message d'update
        update_message = {
            "method": "git_diff",
            "instruction": "Apply the following diff to the previous content:",
            "diff": diff_content,
            "context_lines": 3
        }

        updated_tokens = self._estimate_tokens(json.dumps(update_message))
        savings = 1.0 - (updated_tokens / original_tokens)

        return UpdateResult(
            method=UpdateMethod.GIT_DIFF,
            content=update_message,
            token_savings=max(0.0, savings),
            original_tokens=original_tokens,
            updated_tokens=updated_tokens
        )

    def _create_json_patch_update(
        self,
        old_data: Any,
        new_data: Any,
        original_tokens: int
    ) -> UpdateResult:
        """
        Crée un JSON Patch (RFC 6902) pour données structurées

        Example:
            [
              {"op": "replace", "path": "/name", "value": "new_name"},
              {"op": "add", "path": "/items/-", "value": "new_item"}
            ]
        """
        # Générer les opérations de patch
        patches = self._generate_json_patches(old_data, new_data)

        if not patches:
            # Pas de changement
            return UpdateResult(
                method=UpdateMethod.JSON_PATCH,
                content=new_data,
                token_savings=0.0,
                original_tokens=original_tokens,
                updated_tokens=original_tokens
            )

        update_message = {
            "method": "json_patch",
            "instruction": "Apply the following JSON patches:",
            "patches": patches,
            "base_version": "previous"
        }

        updated_tokens = self._estimate_tokens(json.dumps(update_message))
        savings = 1.0 - (updated_tokens / original_tokens)

        return UpdateResult(
            method=UpdateMethod.JSON_PATCH,
            content=update_message,
            token_savings=max(0.0, savings),
            original_tokens=original_tokens,
            updated_tokens=updated_tokens
        )

    def _create_incremental_update(
        self,
        old_str: str,
        new_str: str,
        original_tokens: int
    ) -> UpdateResult:
        """
        Update incrémental pour texte (envoie seulement les paragraphes changés)
        """
        old_chunks = self._chunk_text(old_str)
        new_chunks = self._chunk_text(new_str)

        # Identifier les chunks qui ont changé
        changes = []
        for i, (old_chunk, new_chunk) in enumerate(zip(old_chunks, new_chunks)):
            if old_chunk != new_chunk:
                changes.append({
                    "position": i,
                    "old": old_chunk[:50] + "..." if len(old_chunk) > 50 else old_chunk,
                    "new": new_chunk
                })

        # Ajouter les nouveaux chunks
        if len(new_chunks) > len(old_chunks):
            for i in range(len(old_chunks), len(new_chunks)):
                changes.append({
                    "position": i,
                    "old": None,
                    "new": new_chunks[i]
                })

        update_message = {
            "method": "incremental",
            "instruction": "Update the following chunks of text:",
            "total_chunks": len(new_chunks),
            "changes": changes
        }

        updated_tokens = self._estimate_tokens(json.dumps(update_message))
        savings = 1.0 - (updated_tokens / original_tokens)

        return UpdateResult(
            method=UpdateMethod.INCREMENTAL,
            content=update_message,
            token_savings=max(0.0, savings),
            original_tokens=original_tokens,
            updated_tokens=updated_tokens
        )

    def _create_context_reuse_update(
        self,
        old_content: Any,
        new_content: Any,
        original_tokens: int,
        context_id: Optional[str]
    ) -> UpdateResult:
        """
        Réutilisation de contexte avec référence

        Au lieu d'envoyer tout le contexte, on dit:
        "Use context from [context_id] and apply these changes"
        """
        if context_id:
            # Sauvegarder le contexte pour réutilisation future
            self.context_cache[context_id] = old_content

        # Identifier seulement les différences essentielles
        diff_summary = self._summarize_differences(old_content, new_content)

        update_message = {
            "method": "context_reuse",
            "instruction": f"Reuse context [{context_id}] with the following updates:",
            "context_id": context_id,
            "changes": diff_summary,
            "reuse_percentage": 0.8  # 80% du contexte réutilisé
        }

        # Économies massives: on n'envoie que la référence + changements
        updated_tokens = self._estimate_tokens(json.dumps(update_message))
        savings = 1.0 - (updated_tokens / original_tokens)

        return UpdateResult(
            method=UpdateMethod.CONTEXT_REUSE,
            content=update_message,
            token_savings=max(0.0, savings),
            original_tokens=original_tokens,
            updated_tokens=updated_tokens
        )

    def _calculate_change_ratio(self, old_str: str, new_str: str) -> float:
        """
        Calcule le ratio de changement (0.0 = identique, 1.0 = totalement différent)
        """
        if not old_str or not new_str:
            return 1.0

        # Utiliser SequenceMatcher pour calculer similarité
        matcher = difflib.SequenceMatcher(None, old_str, new_str)
        similarity = matcher.ratio()

        return 1.0 - similarity  # Convertir similarité en changement

    def _generate_json_patches(self, old_data: Any, new_data: Any, path: str = "") -> List[Dict]:
        """Génère les opérations JSON Patch entre deux objets"""
        patches = []

        if type(old_data) != type(new_data):
            # Type changé = replace complet
            patches.append({
                "op": "replace",
                "path": path or "/",
                "value": new_data
            })
            return patches

        if isinstance(old_data, dict) and isinstance(new_data, dict):
            # Comparer les dictionnaires
            all_keys = set(old_data.keys()) | set(new_data.keys())

            for key in all_keys:
                current_path = f"{path}/{key}"

                if key not in old_data:
                    # Nouveau champ
                    patches.append({
                        "op": "add",
                        "path": current_path,
                        "value": new_data[key]
                    })
                elif key not in new_data:
                    # Champ supprimé
                    patches.append({
                        "op": "remove",
                        "path": current_path
                    })
                elif old_data[key] != new_data[key]:
                    # Champ modifié - récursion
                    if isinstance(old_data[key], (dict, list)):
                        patches.extend(
                            self._generate_json_patches(
                                old_data[key],
                                new_data[key],
                                current_path
                            )
                        )
                    else:
                        patches.append({
                            "op": "replace",
                            "path": current_path,
                            "value": new_data[key]
                        })

        elif isinstance(old_data, list) and isinstance(new_data, list):
            # Comparer les listes (simplifié)
            if old_data != new_data:
                patches.append({
                    "op": "replace",
                    "path": path or "/",
                    "value": new_data
                })

        elif old_data != new_data:
            # Valeurs primitives différentes
            patches.append({
                "op": "replace",
                "path": path or "/",
                "value": new_data
            })

        return patches

    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Divise le texte en chunks (paragraphes ou taille fixe)"""
        # Essayer de diviser par paragraphes d'abord
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _summarize_differences(self, old_content: Any, new_content: Any) -> str:
        """Résume les différences de façon concise"""
        old_str = self._to_string(old_content)
        new_str = self._to_string(new_content)

        # Trouver les principales différences
        old_words = set(old_str.split())
        new_words = set(new_str.split())

        added = new_words - old_words
        removed = old_words - new_words

        summary = []
        if added:
            summary.append(f"Added: {', '.join(list(added)[:10])}")
        if removed:
            summary.append(f"Removed: {', '.join(list(removed)[:10])}")

        return "; ".join(summary) if summary else "Minor changes"

    def _to_string(self, content: Any) -> str:
        """Convertit n'importe quel contenu en string"""
        if isinstance(content, str):
            return content
        elif isinstance(content, (dict, list)):
            return json.dumps(content, indent=2)
        else:
            return str(content)

    def _estimate_tokens(self, text: str) -> int:
        """
        Estime le nombre de tokens (approximation rapide)
        Règle générale: ~4 caractères = 1 token
        """
        return len(text) // 4


# Exemple d'utilisation
if __name__ == "__main__":
    updater = PartialUpdater(change_threshold=0.3)

    # Exemple 1: Code
    old_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total
"""

    new_code = """
def calculate_total(items):
    total = 0
    tax_rate = 0.15
    for item in items:
        total += item.price * (1 + tax_rate)
    return round(total, 2)
"""

    result = updater.create_update(old_code, new_code, content_type="code")
    print(f"Method: {result.method.value}")
    print(f"Token savings: {result.token_savings*100:.1f}%")
    print(f"Original: {result.original_tokens} tokens")
    print(f"Updated: {result.updated_tokens} tokens")
    print(f"\nUpdate content:\n{json.dumps(result.content, indent=2)}")
