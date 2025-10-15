# Proposition: Système d'Escalade Intelligente

## Objectif

Permettre à chaque employé de:
1. **Commencer avec le modèle le plus économique** (NANO)
2. **Évaluer automatiquement la qualité** de sa réponse
3. **Escalader intelligemment** vers un modèle plus puissant ou un expert si nécessaire
4. **Optimiser le ratio coût/qualité** en permanence

## Philosophie

```
Toujours essayer NANO d'abord → Si insuffisant → Escalader à DEEPSEEK → Si insuffisant → Escalader à CLAUDE
                                                ↓
                                    Ou déléguer à un expert spécialisé
```

## Architecture Proposée

### 1. Système d'Évaluation de Qualité

```python
@dataclass
class QualityAssessment:
    """Évaluation de la qualité d'une réponse"""
    score: float  # 0-10
    confidence: float  # 0-1
    issues: List[str]  # Problèmes détectés
    needs_escalation: bool
    suggested_tier: Optional[ModelTier]
    suggested_expert: Optional[str]  # Type d'expert recommandé
```

**Critères d'évaluation:**
- Longueur de la réponse (trop courte = suspect)
- Présence de disclaimers type "Je ne peux pas..."
- Cohérence et structure
- Présence de code/données attendues
- Confiance exprimée dans la réponse

### 2. Méthode d'Escalade dans BaseAgent

```python
class BaseAgent:

    def execute_with_escalation(
        self,
        task: str,
        max_tier: ModelTier = ModelTier.CLAUDE,
        context: Optional[Dict] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Exécute avec escalade automatique si nécessaire

        1. Essaie avec tier actuel (ou NANO par défaut)
        2. Évalue la qualité de la réponse
        3. Si insuffisant, escalade au tier supérieur
        4. Si max_tier atteint et toujours insuffisant, délègue à un expert
        """

    def assess_quality(self, task: str, response: str) -> QualityAssessment:
        """Évalue la qualité d'une réponse"""

    def escalate_to_higher_tier(self, task: str, current_tier: ModelTier) -> Dict:
        """Escalade vers le tier supérieur"""

    def escalate_to_expert(self, task: str, expert_type: str) -> Dict:
        """Délègue à un agent expert spécialisé"""
```

### 3. Pool d'Experts Spécialisés

Créer des agents experts de haut niveau pour escalades:

```python
# Experts disponibles
experts = {
    "code_architect": Expert(tier=CLAUDE, specializations=["architecture", "design patterns"]),
    "algorithm_specialist": Expert(tier=CLAUDE, specializations=["algorithms", "optimization"]),
    "security_expert": Expert(tier=CLAUDE, specializations=["security", "vulnerabilities"]),
    "data_scientist": Expert(tier=CLAUDE, specializations=["ML", "statistics", "analysis"]),
    "system_designer": Expert(tier=CLAUDE, specializations=["system design", "scalability"]),
}
```

## Workflow d'Escalade

### Scénario 1: Escalade de Tier Simple

```
Employé (NANO) reçoit: "Write a function to sort a list"
    ↓
Essaie avec NANO
    ↓
Évalue la réponse → Score: 9/10 ✓
    ↓
Retourne la réponse (coût minimal)
```

### Scénario 2: Escalade de Tier Nécessaire

```
Employé (NANO) reçoit: "Design a distributed caching system"
    ↓
Essaie avec NANO
    ↓
Évalue la réponse → Score: 3/10 ✗ (réponse trop simple)
    ↓
Escalade à DEEPSEEK
    ↓
Essaie avec DEEPSEEK
    ↓
Évalue la réponse → Score: 8/10 ✓
    ↓
Retourne la réponse (coût optimisé)
```

### Scénario 3: Escalade vers Expert

```
Employé (NANO) reçoit: "Design a zero-trust security architecture"
    ↓
Essaie avec NANO → Score: 2/10 ✗
    ↓
Escalade à DEEPSEEK → Score: 4/10 ✗
    ↓
Escalade à CLAUDE → Score: 6/10 ✗ (domaine trop spécialisé)
    ↓
Détecte besoin d'expert: "security_expert"
    ↓
Délègue à Security Expert (CLAUDE + specialization)
    ↓
Expert retourne réponse complète → Score: 9/10 ✓
```

## Implémentation Proposée

### Phase 1: Évaluation de Qualité

```python
class QualityEvaluator:
    """Évalue la qualité des réponses"""

    def evaluate(self, task: str, response: str, tier_used: ModelTier) -> QualityAssessment:
        """
        Évalue si une réponse est de qualité suffisante

        Critères:
        1. Longueur appropriée
        2. Pas de disclaimers négatifs
        3. Structure cohérente
        4. Correspond aux attentes de la tâche
        """
        score = 0.0
        issues = []

        # Critère 1: Longueur
        if len(response) < 50:
            issues.append("Response too short")
            score += 2.0
        elif len(response) < 200:
            score += 5.0
        else:
            score += 8.0

        # Critère 2: Disclaimers négatifs
        negative_patterns = [
            "i cannot", "i can't", "unable to", "don't know",
            "insufficient information", "need more context"
        ]
        if any(pattern in response.lower() for pattern in negative_patterns):
            issues.append("Contains disclaimer")
            score -= 3.0

        # Critère 3: Structure (présence de paragraphes, listes, etc.)
        has_structure = ("\n" in response or ":" in response or "-" in response)
        if has_structure:
            score += 2.0

        # Critère 4: Correspondance tâche
        task_lower = task.lower()
        if "code" in task_lower or "function" in task_lower:
            if "def " in response or "function" in response or "class " in response:
                score += 3.0
            else:
                issues.append("Code expected but not provided")
                score -= 2.0

        # Normaliser
        score = max(0.0, min(10.0, score))

        # Déterminer si escalade nécessaire
        needs_escalation = score < 6.0

        # Suggérer tier ou expert
        suggested_tier = None
        suggested_expert = None

        if needs_escalation:
            if tier_used == ModelTier.NANO:
                suggested_tier = ModelTier.DEEPSEEK
            elif tier_used == ModelTier.DEEPSEEK:
                suggested_tier = ModelTier.CLAUDE
            elif tier_used == ModelTier.CLAUDE:
                # Max tier atteint, suggérer expert
                suggested_expert = self._detect_expert_needed(task)

        return QualityAssessment(
            score=score,
            confidence=0.7,  # TODO: Calculer confiance réelle
            issues=issues,
            needs_escalation=needs_escalation,
            suggested_tier=suggested_tier,
            suggested_expert=suggested_expert
        )

    def _detect_expert_needed(self, task: str) -> Optional[str]:
        """Détecte quel type d'expert est nécessaire"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["security", "vulnerability", "penetration", "exploit"]):
            return "security_expert"
        elif any(kw in task_lower for kw in ["architecture", "system design", "scalability"]):
            return "system_designer"
        elif any(kw in task_lower for kw in ["algorithm", "optimization", "complexity"]):
            return "algorithm_specialist"
        elif any(kw in task_lower for kw in ["ml", "machine learning", "neural", "model training"]):
            return "data_scientist"
        elif any(kw in task_lower for kw in ["refactor", "design pattern", "solid", "clean code"]):
            return "code_architect"

        return None
```

### Phase 2: Méthode d'Escalade

```python
# Dans BaseAgent

def execute_with_escalation(
    self,
    task: str,
    max_tier: ModelTier = ModelTier.CLAUDE,
    max_attempts: int = 3,
    quality_threshold: float = 6.0,
    context: Optional[Dict] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Exécute avec escalade automatique

    Args:
        task: Tâche à exécuter
        max_tier: Tier maximum avant délégation à expert
        max_attempts: Nombre max de tentatives d'escalade
        quality_threshold: Score minimum acceptable (0-10)
        context: Contexte additionnel
        verbose: Mode verbose

    Returns:
        Résultat avec escalation_history
    """
    evaluator = QualityEvaluator()
    current_tier = self.config.tier_preference
    escalation_history = []
    total_cost = 0.0

    for attempt in range(max_attempts):
        if verbose:
            print(f"\n[{self.config.name}] Attempt {attempt + 1} with tier: {current_tier.value}")

        # Exécuter avec le tier actuel
        result = self.execute(
            task=task,
            context=context,
            use_tools=True,
            verbose=False
        )

        if not result["success"]:
            if verbose:
                print(f"[{self.config.name}] Execution failed, escalating...")
            current_tier = self._get_next_tier(current_tier)
            continue

        response = result["data"]
        cost = result["cost"]
        total_cost += cost

        # Évaluer la qualité
        assessment = evaluator.evaluate(task, response, current_tier)

        escalation_history.append({
            "tier": current_tier.value,
            "quality_score": assessment.score,
            "cost": cost,
            "issues": assessment.issues
        })

        if verbose:
            print(f"[{self.config.name}] Quality score: {assessment.score:.1f}/10")
            if assessment.issues:
                print(f"[{self.config.name}] Issues: {', '.join(assessment.issues)}")

        # Si qualité suffisante, retourner
        if assessment.score >= quality_threshold:
            if verbose:
                print(f"[{self.config.name}] ✓ Quality threshold met, returning result")

            return {
                **result,
                "total_cost": total_cost,
                "final_tier": current_tier.value,
                "escalation_history": escalation_history,
                "quality_score": assessment.score,
                "escalated": len(escalation_history) > 1
            }

        # Si qualité insuffisante et suggestion disponible
        if assessment.needs_escalation:
            if assessment.suggested_tier and assessment.suggested_tier != current_tier:
                # Escalader au tier supérieur
                if self._is_tier_within_limit(assessment.suggested_tier, max_tier):
                    current_tier = assessment.suggested_tier
                    if verbose:
                        print(f"[{self.config.name}] Escalating to {current_tier.value}...")
                    continue

            if assessment.suggested_expert:
                # Déléguer à un expert
                if verbose:
                    print(f"[{self.config.name}] Max tier reached, delegating to {assessment.suggested_expert}...")

                return self.escalate_to_expert(
                    task=task,
                    expert_type=assessment.suggested_expert,
                    escalation_history=escalation_history,
                    total_cost=total_cost,
                    verbose=verbose
                )

        # Si on est au max_tier et toujours pas bon, forcer Claude
        if current_tier == max_tier:
            break

    # Retourner la meilleure tentative même si qualité < threshold
    if verbose:
        print(f"[{self.config.name}] Max attempts reached, returning best result")

    return {
        **result,
        "total_cost": total_cost,
        "final_tier": current_tier.value,
        "escalation_history": escalation_history,
        "quality_score": assessment.score,
        "escalated": True,
        "warning": "Quality threshold not met after all attempts"
    }

def _get_next_tier(self, current_tier: ModelTier) -> ModelTier:
    """Retourne le tier supérieur"""
    tier_order = [ModelTier.NANO, ModelTier.DEEPSEEK, ModelTier.CLAUDE]
    try:
        current_index = tier_order.index(current_tier)
        if current_index < len(tier_order) - 1:
            return tier_order[current_index + 1]
    except ValueError:
        pass
    return ModelTier.CLAUDE

def _is_tier_within_limit(self, tier: ModelTier, max_tier: ModelTier) -> bool:
    """Vérifie si un tier est dans la limite"""
    tier_order = [ModelTier.NANO, ModelTier.DEEPSEEK, ModelTier.CLAUDE]
    try:
        tier_index = tier_order.index(tier)
        max_index = tier_order.index(max_tier)
        return tier_index <= max_index
    except ValueError:
        return False

def escalate_to_expert(
    self,
    task: str,
    expert_type: str,
    escalation_history: List[Dict],
    total_cost: float,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Délègue à un agent expert spécialisé

    L'expert utilise CLAUDE + spécialisation approfondie
    """
    if verbose:
        print(f"\n[{self.config.name}] ═══ ESCALATING TO EXPERT: {expert_type} ═══")

    # Chercher l'expert dans le système
    # TODO: Implémenter pool d'experts
    # Pour l'instant, créer expert à la volée

    expert_config = self._create_expert_config(expert_type)
    expert = BaseAgent(
        expert_config,
        llm_client=self.llm_client,
        hr_department=self.hr_department,
        tools_department=self.tools_department
    )

    # Exécuter avec l'expert (forcé en CLAUDE)
    result = expert.execute(
        task=task,
        use_tools=True,
        verbose=verbose
    )

    total_cost += result.get("cost", 0)

    escalation_history.append({
        "tier": "expert",
        "expert_type": expert_type,
        "cost": result.get("cost", 0)
    })

    if verbose:
        print(f"[{self.config.name}] Expert completed task")

    return {
        **result,
        "total_cost": total_cost,
        "final_tier": "expert",
        "expert_type": expert_type,
        "escalation_history": escalation_history,
        "escalated": True
    }

def _create_expert_config(self, expert_type: str) -> AgentConfig:
    """Crée la configuration d'un expert spécialisé"""
    expert_profiles = {
        "security_expert": {
            "name": "SecurityExpert",
            "role": "Senior Security Architect",
            "description": "Expert in security, vulnerabilities, and threat modeling",
            "specializations": ["security", "vulnerabilities", "penetration-testing", "encryption"],
            "prompt": "You are a world-class security expert..."
        },
        "system_designer": {
            "name": "SystemDesigner",
            "role": "Principal System Architect",
            "description": "Expert in distributed systems and scalability",
            "specializations": ["system-design", "scalability", "distributed-systems", "architecture"],
            "prompt": "You are a principal system architect..."
        },
        "algorithm_specialist": {
            "name": "AlgorithmSpecialist",
            "role": "Senior Algorithm Engineer",
            "description": "Expert in algorithms, data structures, and optimization",
            "specializations": ["algorithms", "optimization", "complexity", "data-structures"],
            "prompt": "You are an algorithm specialist..."
        },
        "data_scientist": {
            "name": "DataScientist",
            "role": "Senior Data Scientist",
            "description": "Expert in ML, statistics, and data analysis",
            "specializations": ["machine-learning", "statistics", "data-analysis", "modeling"],
            "prompt": "You are a senior data scientist..."
        },
        "code_architect": {
            "name": "CodeArchitect",
            "role": "Senior Software Architect",
            "description": "Expert in software architecture and design patterns",
            "specializations": ["architecture", "design-patterns", "refactoring", "clean-code"],
            "prompt": "You are a senior software architect..."
        }
    }

    profile = expert_profiles.get(expert_type, expert_profiles["code_architect"])

    return AgentConfig(
        name=profile["name"],
        role=profile["role"],
        description=profile["description"],
        base_prompt=profile["prompt"],
        tier_preference=ModelTier.CLAUDE,  # Experts toujours en CLAUDE
        can_delegate=False,
        specializations=profile["specializations"]
    )
```

## Optimisations et Stratégies

### 1. Cache d'Escalade

```python
# Si une tâche similaire a déjà nécessité escalade, commencer directement au bon tier
escalation_cache = {
    "task_hash": {"required_tier": "deepseek", "quality_achieved": 8.5}
}
```

### 2. Apprentissage

```python
# Suivre les patterns de réussite/échec par tier
stats = {
    "nano": {"success_rate": 0.75, "avg_quality": 7.2},
    "deepseek": {"success_rate": 0.92, "avg_quality": 8.8},
    "claude": {"success_rate": 0.98, "avg_quality": 9.5}
}
```

### 3. Limites de Coût

```python
# Configurer des limites de coût par employé
employee.execute_with_escalation(
    task="...",
    max_cost=0.01,  # Maximum $0.01
    max_tier=ModelTier.DEEPSEEK  # Ne pas aller jusqu'à Claude
)
```

## Avantages

### 1. Optimisation Coût/Qualité

- Commence toujours par le moins cher
- Escalade seulement si nécessaire
- Évite les sur-dépenses inutiles

### 2. Qualité Garantie

- Évaluation automatique de qualité
- Escalade automatique si insuffisant
- Accès à des experts pour cas complexes

### 3. Transparent

- Historique complet d'escalade
- Coûts tracés par tentative
- Raisons d'escalade documentées

### 4. Flexible

- Configurable par tâche
- Limites de coût/tier ajustables
- Peut désactiver escalade si désiré

## Métriques de Succès

```python
{
    "total_tasks": 1000,
    "escalation_rate": 0.23,  # 23% ont nécessité escalade
    "tier_distribution": {
        "nano": 0.77,    # 77% réussis avec NANO
        "deepseek": 0.18,  # 18% ont nécessité DEEPSEEK
        "claude": 0.04,   # 4% ont nécessité CLAUDE
        "expert": 0.01    # 1% ont nécessité expert
    },
    "avg_quality_by_tier": {
        "nano": 7.8,
        "deepseek": 8.9,
        "claude": 9.4,
        "expert": 9.7
    },
    "cost_savings": "$42.50",  # Économies vs tout en Claude
    "quality_maintained": 8.5  # Quality moyenne globale
}
```

## Prochaines Étapes

1. **Implémenter QualityEvaluator** - Système d'évaluation de qualité
2. **Ajouter execute_with_escalation() à BaseAgent** - Méthode principale
3. **Créer ExpertPool** - Pool d'experts disponibles
4. **Ajouter cache d'escalade** - Optimisation basée sur historique
5. **Tester avec cas réels** - Validation du système

## Exemple Complet

```python
from cortex.agents.hierarchy import get_hierarchy

hierarchy = get_hierarchy()

# Tâche complexe
task = "Design a microservices architecture for a social media platform with 10M users"

# Exécuter avec escalade automatique
result = hierarchy.code_director.execute_with_escalation(
    task=task,
    max_tier=ModelTier.CLAUDE,
    quality_threshold=8.0,
    verbose=True
)

# Résultat
print(f"Escalated: {result['escalated']}")  # True
print(f"Final tier: {result['final_tier']}")  # "claude" ou "expert"
print(f"Quality: {result['quality_score']}/10")  # 9.2
print(f"Total cost: ${result['total_cost']:.6f}")  # $0.002145

# Historique d'escalade
for step in result['escalation_history']:
    print(f"  {step['tier']}: quality={step['quality_score']}, cost=${step['cost']:.6f}")
```

## Conclusion

Ce système permet d'**optimiser automatiquement** le ratio coût/qualité en:
- Essayant toujours le modèle le moins cher d'abord
- Évaluant objectivement la qualité
- Escaladant intelligemment si nécessaire
- Déléguant à des experts pour les cas ultra-spécialisés

**Résultat attendu:** Économies de 60-80% tout en maintenant une qualité élevée (8+/10).
