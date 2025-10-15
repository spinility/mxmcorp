"""
Project Knowledge Base - Système d'embeddings pour context applicatif complet

Permet de maintenir un context ultra-compact du projet entier:
- Structure des fichiers
- Code et objets
- Workflows
- Employés (agents)
- Base de données

Le tout accessible en < 1000 tokens via semantic search
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️  ChromaDB not installed. Run: pip install chromadb")


@dataclass
class KnowledgeChunk:
    """Un chunk de connaissance du projet"""
    id: str
    type: str  # code, structure, workflow, employee, database
    content: str
    metadata: Dict[str, Any]
    tokens: int


class ProjectKnowledgeBase:
    """
    Base de connaissance du projet avec embeddings

    Utilise ChromaDB pour stocker et rechercher via embeddings
    """

    def __init__(self, project_root: Path, use_local_embeddings: bool = False):
        """
        Args:
            project_root: Racine du projet
            use_local_embeddings: Si True, utilise un modèle local (gratuit mais moins bon)
        """
        self.project_root = Path(project_root)
        self.kb_dir = self.project_root / ".cortex" / "knowledge_base"
        self.kb_dir.mkdir(parents=True, exist_ok=True)

        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB required. Install: pip install chromadb")

        # ChromaDB client
        self.client = chromadb.PersistentClient(path=str(self.kb_dir))

        # Embedding function
        if use_local_embeddings:
            # Utilise un modèle local (gratuit, mais moins performant)
            self.embed_fn = embedding_functions.DefaultEmbeddingFunction()
        else:
            # Utilise OpenAI (meilleur, minimal cost)
            self.embed_fn = embedding_functions.OpenAIEmbeddingFunction(
                model_name="text-embedding-3-small",
                api_key=os.getenv("OPENAI_API_KEY")
            )

        # Collection
        self.collection = self.client.get_or_create_collection(
            name="project_knowledge",
            embedding_function=self.embed_fn,
            metadata={"description": "Project knowledge base with embeddings"}
        )

        # Stats
        self.stats = {
            "total_chunks": 0,
            "total_tokens": 0,
            "embedding_cost": 0.0,
            "last_indexed": None
        }

        self._load_stats()

    def index_project(self, force_reindex: bool = False, verbose: bool = True):
        """
        Index tout le projet

        Args:
            force_reindex: Si True, ré-index même si déjà indexé
            verbose: Afficher le progrès
        """
        if verbose:
            print("\n🔍 Indexing project knowledge...")

        # Vérifier si déjà indexé
        if not force_reindex and self.stats["last_indexed"]:
            if verbose:
                print(f"   Already indexed on {self.stats['last_indexed']}")
                print("   Use force_reindex=True to re-index")
            return self.stats

        chunks = []

        # 1. Index code files
        if verbose:
            print("   📄 Indexing code files...")
        chunks.extend(self._index_code_files())

        # 2. Index project structure
        if verbose:
            print("   📁 Indexing project structure...")
        chunks.extend(self._index_structure())

        # 3. Index workflows (from docs)
        if verbose:
            print("   🔄 Indexing workflows...")
        chunks.extend(self._index_workflows())

        # 4. Index agents (employees)
        if verbose:
            print("   🤖 Indexing agents...")
        chunks.extend(self._index_agents())

        # 5. Index configuration
        if verbose:
            print("   ⚙️  Indexing configuration...")
        chunks.extend(self._index_config())

        # Add to vector DB
        if chunks:
            if verbose:
                print(f"\n   💾 Storing {len(chunks)} chunks in vector database...")

            self.collection.add(
                documents=[c.content for c in chunks],
                metadatas=[c.metadata for c in chunks],
                ids=[c.id for c in chunks]
            )

            # Update stats
            self.stats["total_chunks"] = len(chunks)
            self.stats["total_tokens"] = sum(c.tokens for c in chunks)
            self.stats["embedding_cost"] = self.stats["total_tokens"] * 0.00002 / 1000  # $0.02 per 1M
            self.stats["last_indexed"] = datetime.now().isoformat()
            self._save_stats()

        if verbose:
            print(f"\n✅ Indexing complete!")
            print(f"   Chunks: {self.stats['total_chunks']}")
            print(f"   Tokens: {self.stats['total_tokens']:,}")
            print(f"   Cost: ${self.stats['embedding_cost']:.4f}")

        return self.stats

    def _index_code_files(self) -> List[KnowledgeChunk]:
        """Index tous les fichiers Python"""
        chunks = []

        for py_file in self.project_root.rglob("*.py"):
            # Skip virtual envs and hidden dirs
            if any(part.startswith('.') or part == '__pycache__' for part in py_file.parts):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Chunk par classe/fonction
                file_chunks = self._chunk_python_file(py_file, content)
                chunks.extend(file_chunks)

            except Exception as e:
                print(f"   ⚠️  Error reading {py_file}: {e}")

        return chunks

    def _chunk_python_file(self, file_path: Path, content: str) -> List[KnowledgeChunk]:
        """
        Découpe un fichier Python en chunks intelligents

        Stratégie: 1 chunk par classe ou fonction top-level
        """
        chunks = []
        relative_path = str(file_path.relative_to(self.project_root))

        # Simple parsing: split by "class" or "def" at start of line
        lines = content.split('\n')
        current_chunk = []
        current_name = None

        for line in lines:
            stripped = line.strip()

            # Nouvelle classe ou fonction
            if (stripped.startswith('class ') or
                (stripped.startswith('def ') and not line.startswith(' '))):

                # Sauvegarder le chunk précédent
                if current_chunk and current_name:
                    chunk_content = '\n'.join(current_chunk)
                    tokens = len(chunk_content) // 4  # Rough estimate

                    # Générer un ID unique avec path + name + line number
                    unique_id = f"{relative_path}:{current_name}:{len(chunks)}"

                    chunks.append(KnowledgeChunk(
                        id=hashlib.md5(unique_id.encode()).hexdigest(),
                        type="code",
                        content=chunk_content[:2000],  # Max 2000 chars per chunk
                        metadata={
                            "file": relative_path,
                            "name": current_name,
                            "category": "class" if current_chunk[0].strip().startswith('class') else "function",
                            "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        },
                        tokens=min(tokens, 500)
                    ))

                # Nouveau chunk
                current_chunk = [line]
                current_name = stripped.split('(')[0].split(' ')[1] if '(' in stripped else stripped.split(' ')[1]
            else:
                if current_chunk:  # Ajouter à current chunk
                    current_chunk.append(line)

        # Dernier chunk
        if current_chunk and current_name:
            chunk_content = '\n'.join(current_chunk)
            tokens = len(chunk_content) // 4

            # Générer un ID unique avec path + name + line number
            unique_id = f"{relative_path}:{current_name}:{len(chunks)}"

            chunks.append(KnowledgeChunk(
                id=hashlib.md5(unique_id.encode()).hexdigest(),
                type="code",
                content=chunk_content[:2000],
                metadata={
                    "file": relative_path,
                    "name": current_name,
                    "category": "class" if current_chunk[0].strip().startswith('class') else "function",
                    "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                },
                tokens=min(tokens, 500)
            ))

        return chunks

    def _index_structure(self) -> List[KnowledgeChunk]:
        """Index la structure du projet"""
        chunks = []

        # Parcourir les dossiers principaux
        for item in self.project_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Créer un chunk pour ce dossier
                files = list(item.rglob("*.py"))
                description = f"Directory: {item.name}\n"
                description += f"Contains {len(files)} Python files\n"

                # Lister les fichiers principaux
                main_files = [f.name for f in files if f.parent == item][:10]
                if main_files:
                    description += "Main files: " + ", ".join(main_files)

                chunks.append(KnowledgeChunk(
                    id=f"structure_{item.name}",
                    type="structure",
                    content=description,
                    metadata={
                        "directory": item.name,
                        "file_count": len(files),
                        "category": "structure"
                    },
                    tokens=len(description) // 4
                ))

        return chunks

    def _index_workflows(self) -> List[KnowledgeChunk]:
        """Index les workflows depuis les docs markdown"""
        chunks = []

        # Chercher les fichiers markdown
        for md_file in self.project_root.rglob("*.md"):
            if md_file.name in ["README.md", "WORKFLOW.md", "PROCESS.md", "ESCALATION_SYSTEM.md"]:
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Chunk par section (##)
                    sections = content.split('\n## ')
                    for section in sections:
                        if len(section) > 100:  # Ignorer sections trop courtes
                            title = section.split('\n')[0]
                            chunks.append(KnowledgeChunk(
                                id=f"workflow_{hashlib.md5(title.encode()).hexdigest()}",
                                type="workflow",
                                content=section[:1000],
                                metadata={
                                    "file": md_file.name,
                                    "title": title,
                                    "category": "workflow"
                                },
                                tokens=min(len(section) // 4, 250)
                            ))
                except Exception as e:
                    print(f"   ⚠️  Error reading {md_file}: {e}")

        return chunks

    def _index_agents(self) -> List[KnowledgeChunk]:
        """Index tous les agents (employees)"""
        chunks = []

        agents_dir = self.project_root / "cortex" / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*_agent.py"):
                try:
                    with open(agent_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Extraire la docstring de classe
                    if '"""' in content:
                        docstring = content.split('"""')[1]
                        agent_name = agent_file.stem.replace('_agent', '').replace('_', ' ').title()

                        chunks.append(KnowledgeChunk(
                            id=f"agent_{agent_file.stem}",
                            type="employee",
                            content=f"Agent: {agent_name}\n{docstring[:500]}",
                            metadata={
                                "name": agent_name,
                                "file": str(agent_file.relative_to(self.project_root)),
                                "category": "agent"
                            },
                            tokens=len(docstring) // 4
                        ))
                except Exception as e:
                    print(f"   ⚠️  Error reading {agent_file}: {e}")

        return chunks

    def _index_config(self) -> List[KnowledgeChunk]:
        """Index les fichiers de configuration"""
        chunks = []

        config_dir = self.project_root / "cortex" / "config"
        if config_dir.exists():
            for config_file in config_dir.glob("*.yaml"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    chunks.append(KnowledgeChunk(
                        id=f"config_{config_file.stem}",
                        type="configuration",
                        content=content[:1000],
                        metadata={
                            "file": config_file.name,
                            "category": "configuration"
                        },
                        tokens=min(len(content) // 4, 250)
                    ))
                except Exception as e:
                    print(f"   ⚠️  Error reading {config_file}: {e}")

        return chunks

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recherche sémantique dans la base de connaissance

        Args:
            query: Question ou description de la tâche
            n_results: Nombre de résultats à retourner
            filter_type: Filtrer par type (code, structure, workflow, employee)

        Returns:
            Résultats avec documents, métadonnées et distances
        """
        where = {"type": filter_type} if filter_type else None

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la KB"""
        return self.stats.copy()

    def _load_stats(self):
        """Charge les stats depuis le fichier"""
        stats_file = self.kb_dir / "stats.json"
        if stats_file.exists():
            with open(stats_file, 'r') as f:
                self.stats.update(json.load(f))

    def _save_stats(self):
        """Sauvegarde les stats"""
        stats_file = self.kb_dir / "stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)


if __name__ == "__main__":
    # Test
    print("Testing Project Knowledge Base...")

    kb = ProjectKnowledgeBase(
        project_root=Path.cwd(),
        use_local_embeddings=True  # Utiliser embeddings locaux pour le test
    )

    # Index le projet
    stats = kb.index_project(verbose=True)

    # Test de recherche
    print("\n🔍 Testing semantic search...")
    print("\nQuery: 'User model validation'")
    results = kb.search("User model validation", n_results=3)

    for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
        print(f"\n{i}. [{meta.get('type', 'unknown')}] {meta.get('file', 'N/A')}")
        print(f"   {doc[:200]}...")

    print("\n✅ Knowledge base test complete!")
