-- Cortex Intelligence Database (CID) - Schema v1.0
-- Le système nerveux de Cortex : relations, états, dépendances

-- ========================================
-- 1. FICHIERS & DÉPENDANCES (Graphe)
-- ========================================

-- Table des fichiers du projet
CREATE TABLE IF NOT EXISTS cortex_file (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,                -- Chemin complet du fichier
    type TEXT NOT NULL,                       -- 'code', 'config', 'doc', 'data'
    language TEXT,                            -- 'python', 'markdown', 'json', etc.
    size_bytes INTEGER,
    lines_of_code INTEGER,
    complexity_score REAL DEFAULT 0.0,        -- Complexité cyclomatique
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,              -- Fichier actif ou obsolète
    owner_agent TEXT,                         -- Agent responsable
    metadata JSON                             -- Métadonnées additionnelles
);

-- Relations de dépendance entre fichiers
CREATE TABLE IF NOT EXISTS file_dependency (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file_id INTEGER NOT NULL,
    target_file_id INTEGER NOT NULL,
    dependency_type TEXT NOT NULL,            -- 'import', 'uses', 'extends', 'requires'
    strength REAL DEFAULT 1.0,                -- Force de la dépendance (0.0-1.0)
    is_critical BOOLEAN DEFAULT 0,            -- Dépendance critique?
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_file_id) REFERENCES cortex_file(id) ON DELETE CASCADE,
    FOREIGN KEY (target_file_id) REFERENCES cortex_file(id) ON DELETE CASCADE,
    UNIQUE(source_file_id, target_file_id, dependency_type)
);

-- Index pour requêtes rapides
CREATE INDEX IF NOT EXISTS idx_file_path ON cortex_file(path);
CREATE INDEX IF NOT EXISTS idx_file_type ON cortex_file(type);
CREATE INDEX IF NOT EXISTS idx_dependency_source ON file_dependency(source_file_id);
CREATE INDEX IF NOT EXISTS idx_dependency_target ON file_dependency(target_file_id);

-- ========================================
-- 2. AGENTS & RÔLES (Relationnelle)
-- ========================================

-- Table des agents du système
CREATE TABLE IF NOT EXISTS agent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,                -- Nom de l'agent
    type TEXT NOT NULL,                       -- 'executor', 'decision', 'orchestrator'
    role TEXT NOT NULL,                       -- 'triage', 'planner', 'quality_control', etc.
    tier TEXT NOT NULL,                       -- 'NANO', 'DEEPSEEK', 'CLAUDE'
    specialization TEXT,                      -- Spécialisation spécifique
    expertise_level INTEGER DEFAULT 1,        -- Niveau d'expertise (1-10)
    status TEXT DEFAULT 'active',             -- 'active', 'idle', 'retired'
    total_executions INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    success_rate REAL DEFAULT 0.0,            -- % de succès
    avg_response_time REAL DEFAULT 0.0,       -- Temps moyen de réponse (secondes)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP,
    metadata JSON
);

-- Projets/tâches assignés aux agents
CREATE TABLE IF NOT EXISTS agent_assignment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    task_description TEXT,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT DEFAULT 'pending',            -- 'pending', 'in_progress', 'completed', 'failed'
    result TEXT,
    FOREIGN KEY (agent_id) REFERENCES agent(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_agent_role ON agent(role);
CREATE INDEX IF NOT EXISTS idx_agent_status ON agent(status);
CREATE INDEX IF NOT EXISTS idx_assignment_agent ON agent_assignment(agent_id);

-- ========================================
-- 3. ROADMAP & MILESTONES (Hiérarchique)
-- ========================================

-- Projets de la roadmap
CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 5,               -- 1 (critique) à 10 (bas)
    status TEXT DEFAULT 'planned',            -- 'planned', 'in_progress', 'completed', 'blocked', 'cancelled'
    parent_project_id INTEGER,                -- Pour hiérarchie de projets
    owner_agent TEXT,
    estimated_hours REAL,
    actual_hours REAL DEFAULT 0.0,
    progress_percent REAL DEFAULT 0.0,
    start_date DATE,
    target_date DATE,
    completion_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (parent_project_id) REFERENCES project(id) ON DELETE SET NULL
);

-- Milestones liés aux projets
CREATE TABLE IF NOT EXISTS milestone (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending',            -- 'pending', 'completed', 'missed'
    target_date DATE,
    completion_date DATE,
    is_critical BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_project_status ON project(status);
CREATE INDEX IF NOT EXISTS idx_project_priority ON project(priority);
CREATE INDEX IF NOT EXISTS idx_milestone_project ON milestone(project_id);

-- ========================================
-- 4. HISTORIQUE DE MODIFICATIONS (Transactionnelle)
-- ========================================

-- Log des changements architecturaux
CREATE TABLE IF NOT EXISTS change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commit_id TEXT,                           -- ID du commit git si applicable
    change_type TEXT NOT NULL,                -- 'create', 'modify', 'delete', 'refactor', 'rename'
    entity_type TEXT NOT NULL,                -- 'file', 'agent', 'project', 'dependency'
    entity_id INTEGER,
    author TEXT NOT NULL,                     -- Nom de l'agent/humain
    description TEXT NOT NULL,
    impact_level TEXT DEFAULT 'low',          -- 'low', 'medium', 'high', 'critical'
    affected_files TEXT,                      -- Liste de fichiers affectés (JSON)
    rollback_info JSON,                       -- Info pour rollback si nécessaire
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- Relation entre modifications pour traçabilité
CREATE TABLE IF NOT EXISTS change_relation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_change_id INTEGER NOT NULL,
    child_change_id INTEGER NOT NULL,
    relation_type TEXT NOT NULL,              -- 'triggers', 'requires', 'conflicts_with'
    FOREIGN KEY (parent_change_id) REFERENCES change_log(id) ON DELETE CASCADE,
    FOREIGN KEY (child_change_id) REFERENCES change_log(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_change_timestamp ON change_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_change_author ON change_log(author);
CREATE INDEX IF NOT EXISTS idx_change_impact ON change_log(impact_level);

-- ========================================
-- 5. DÉCISIONS ARCHITECTURALES (ADR)
-- ========================================

-- Architecture Decision Records
CREATE TABLE IF NOT EXISTS architectural_decision (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'proposed',           -- 'proposed', 'accepted', 'rejected', 'deprecated', 'superseded'
    context TEXT NOT NULL,                    -- Contexte de la décision
    decision TEXT NOT NULL,                   -- La décision prise
    consequences TEXT,                        -- Conséquences attendues
    alternatives TEXT,                        -- Alternatives considérées
    impact_level TEXT DEFAULT 'medium',       -- 'low', 'medium', 'high', 'critical'
    approved_by TEXT,                         -- Agent/humain qui a approuvé
    proposed_date DATE DEFAULT CURRENT_DATE,
    approved_date DATE,
    superseded_by_id INTEGER,                 -- ADR qui remplace celle-ci
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (superseded_by_id) REFERENCES architectural_decision(id) ON DELETE SET NULL
);

-- Tags pour catégoriser les décisions
CREATE TABLE IF NOT EXISTS decision_tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    FOREIGN KEY (decision_id) REFERENCES architectural_decision(id) ON DELETE CASCADE,
    UNIQUE(decision_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_decision_status ON architectural_decision(status);
CREATE INDEX IF NOT EXISTS idx_decision_impact ON architectural_decision(impact_level);
CREATE INDEX IF NOT EXISTS idx_decision_tag ON decision_tag(tag);

-- ========================================
-- 6. MÉTRIQUES DE PERFORMANCE (Séries temporelles)
-- ========================================

-- Métriques des agents
CREATE TABLE IF NOT EXISTS agent_metric (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    metric_type TEXT NOT NULL,                -- 'cost', 'latency', 'success_rate', 'quality_score'
    value REAL NOT NULL,
    unit TEXT,                                -- 'usd', 'seconds', 'percent', 'score'
    context TEXT,                             -- Contexte de la métrique
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agent(id) ON DELETE CASCADE
);

-- Métriques système globales
CREATE TABLE IF NOT EXISTS system_metric (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_type TEXT NOT NULL,                -- 'total_cost', 'total_requests', 'avg_quality'
    value REAL NOT NULL,
    unit TEXT,
    period TEXT,                              -- 'hourly', 'daily', 'weekly', 'monthly'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

CREATE INDEX IF NOT EXISTS idx_agent_metric_agent ON agent_metric(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_metric_type ON agent_metric(metric_type);
CREATE INDEX IF NOT EXISTS idx_agent_metric_timestamp ON agent_metric(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_metric_type ON system_metric(metric_type);
CREATE INDEX IF NOT EXISTS idx_system_metric_timestamp ON system_metric(timestamp);

-- ========================================
-- 7. VUES UTILES POUR REQUÊTAGE
-- ========================================

-- Vue des dépendances critiques
CREATE VIEW IF NOT EXISTS critical_dependencies AS
SELECT
    cf1.path as source_file,
    cf2.path as target_file,
    fd.dependency_type,
    fd.strength,
    cf1.owner_agent as source_owner,
    cf2.owner_agent as target_owner
FROM file_dependency fd
JOIN cortex_file cf1 ON fd.source_file_id = cf1.id
JOIN cortex_file cf2 ON fd.target_file_id = cf2.id
WHERE fd.is_critical = 1 AND cf1.is_active = 1 AND cf2.is_active = 1;

-- Vue des agents les plus performants
CREATE VIEW IF NOT EXISTS top_performing_agents AS
SELECT
    a.name,
    a.role,
    a.tier,
    a.total_executions,
    a.success_rate,
    a.avg_response_time,
    ROUND(a.total_cost, 6) as total_cost
FROM agent a
WHERE a.status = 'active' AND a.total_executions > 10
ORDER BY a.success_rate DESC, a.total_cost ASC
LIMIT 10;

-- Vue des projets en retard
CREATE VIEW IF NOT EXISTS overdue_projects AS
SELECT
    p.name,
    p.priority,
    p.status,
    p.target_date,
    p.progress_percent,
    p.owner_agent,
    julianday('now') - julianday(p.target_date) as days_overdue
FROM project p
WHERE p.status NOT IN ('completed', 'cancelled')
  AND p.target_date < date('now')
ORDER BY p.priority ASC, days_overdue DESC;

-- Vue des modifications à haut impact
CREATE VIEW IF NOT EXISTS high_impact_changes AS
SELECT
    cl.id,
    cl.change_type,
    cl.entity_type,
    cl.author,
    cl.description,
    cl.impact_level,
    cl.timestamp
FROM change_log cl
WHERE cl.impact_level IN ('high', 'critical')
ORDER BY cl.timestamp DESC
LIMIT 50;

-- ========================================
-- 8. TRIGGERS POUR COHÉRENCE
-- ========================================

-- Trigger: Mettre à jour le timestamp updated_at automatiquement
CREATE TRIGGER IF NOT EXISTS update_project_timestamp
AFTER UPDATE ON project
BEGIN
    UPDATE project SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger: Logger les changements de status d'agent
CREATE TRIGGER IF NOT EXISTS log_agent_status_change
AFTER UPDATE OF status ON agent
WHEN OLD.status != NEW.status
BEGIN
    INSERT INTO change_log (change_type, entity_type, entity_id, author, description, impact_level)
    VALUES (
        'modify',
        'agent',
        NEW.id,
        'system',
        'Agent status changed from ' || OLD.status || ' to ' || NEW.status,
        CASE
            WHEN NEW.status = 'retired' THEN 'high'
            ELSE 'low'
        END
    );
END;

-- Trigger: Mettre à jour le compteur d'exécutions
CREATE TRIGGER IF NOT EXISTS update_agent_executions
AFTER INSERT ON agent_assignment
BEGIN
    UPDATE agent
    SET total_executions = total_executions + 1,
        last_active = CURRENT_TIMESTAMP
    WHERE id = NEW.agent_id;
END;

-- ========================================
-- 9. MÉTADONNÉES DE LA BASE
-- ========================================

CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT OR IGNORE INTO schema_version (version, description)
VALUES ('1.0.0', 'Initial Cortex Intelligence Database schema');

-- ========================================
-- 10. SEED DATA (Données initiales)
-- ========================================

-- Agents existants
INSERT OR IGNORE INTO agent (name, type, role, tier, specialization, expertise_level, status) VALUES
    ('TriageAgent', 'decision', 'triage', 'NANO', 'request_routing', 8, 'active'),
    ('QuickActionsAgent', 'executor', 'quick_actions', 'NANO', 'atomic_operations', 7, 'active'),
    ('TaskExecutor', 'executor', 'task_execution', 'DEEPSEEK', 'multi_tool_tasks', 9, 'active'),
    ('PlannerAgent', 'decision', 'planner', 'DEEPSEEK', 'task_planning', 8, 'active'),
    ('ContextAgent', 'decision', 'context', 'DEEPSEEK', 'context_preparation', 8, 'active'),
    ('QualityControlAgent', 'decision', 'quality_control', 'DEEPSEEK', 'quality_evaluation', 9, 'active'),
    ('ToolerAgent', 'decision', 'tooler', 'DEEPSEEK', 'tool_research', 7, 'active'),
    ('CommunicationsAgent', 'decision', 'communications', 'NANO', 'user_communications', 6, 'active'),
    ('MaintenanceAgent', 'orchestrator', 'maintenance', 'DEEPSEEK', 'system_maintenance', 8, 'active'),
    ('HarmonizationAgent', 'orchestrator', 'harmonization', 'CLAUDE', 'architecture_coherence', 9, 'active'),
    ('SmartRouterAgent', 'decision', 'smart_router', 'NANO', 'department_routing', 7, 'active');

-- Décision architecturale initiale
INSERT OR IGNORE INTO architectural_decision (
    title,
    status,
    context,
    decision,
    consequences,
    impact_level,
    approved_by
) VALUES (
    'Use SQLite as Cortex Intelligence Database',
    'accepted',
    'Cortex needed a structured way to manage entities, relations, and temporal data beyond markdown files',
    'Implement a SQLite database (cortex.db) as the system nervous system, keeping .md files for human-readable narratives',
    'Better data consistency, relational queries, automatic reporting, and ability for Cortex to reason about its own architecture',
    'high',
    'CEO + Claude Code'
);
