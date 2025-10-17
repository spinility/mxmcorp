-- Migration 001: Ajout des tables pour la structure du codebase
-- Permet de stocker classes, fonctions, imports et relations

-- ========================================
-- STRUCTURE DU CODE (Code Intelligence)
-- ========================================

-- Modules/Packages Python
CREATE TABLE IF NOT EXISTS code_module (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,                       -- Nom complet du module (ex: cortex.core.llm_client)
    is_package BOOLEAN DEFAULT 0,             -- Est-ce un package (__init__.py) ?
    docstring TEXT,                           -- Documentation du module
    imports_count INTEGER DEFAULT 0,          -- Nombre d'imports
    lines_of_code INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES cortex_file(id) ON DELETE CASCADE,
    UNIQUE(file_id, name)
);

-- Classes définies dans le code
CREATE TABLE IF NOT EXISTS code_class (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL,
    name TEXT NOT NULL,                       -- Nom de la classe
    full_name TEXT NOT NULL,                  -- Nom qualifié complet
    base_classes TEXT,                        -- Classes parentes (JSON array)
    docstring TEXT,                           -- Documentation de la classe
    is_abstract BOOLEAN DEFAULT 0,            -- Classe abstraite ?
    decorators TEXT,                          -- Decorateurs (JSON array)
    line_start INTEGER,                       -- Ligne de début dans le fichier
    line_end INTEGER,                         -- Ligne de fin
    complexity_score REAL DEFAULT 0.0,        -- Complexité de la classe
    method_count INTEGER DEFAULT 0,           -- Nombre de méthodes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES code_module(id) ON DELETE CASCADE,
    UNIQUE(module_id, name)
);

-- Fonctions/Méthodes définies dans le code
CREATE TABLE IF NOT EXISTS code_function (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER,                        -- Module si fonction globale
    class_id INTEGER,                         -- Classe si méthode
    name TEXT NOT NULL,                       -- Nom de la fonction
    full_name TEXT NOT NULL,                  -- Nom qualifié complet
    signature TEXT,                           -- Signature complète
    return_type TEXT,                         -- Type de retour si annoté
    docstring TEXT,                           -- Documentation
    is_async BOOLEAN DEFAULT 0,               -- Fonction async ?
    is_static BOOLEAN DEFAULT 0,              -- Méthode statique ?
    is_classmethod BOOLEAN DEFAULT 0,         -- Méthode de classe ?
    is_property BOOLEAN DEFAULT 0,            -- Property ?
    decorators TEXT,                          -- Decorateurs (JSON array)
    line_start INTEGER,                       -- Ligne de début
    line_end INTEGER,                         -- Ligne de fin
    complexity_score REAL DEFAULT 0.0,        -- Complexité cyclomatique
    parameters TEXT,                          -- Paramètres (JSON)
    calls_count INTEGER DEFAULT 0,            -- Nombre d'appels à d'autres fonctions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES code_module(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES code_class(id) ON DELETE CASCADE,
    CHECK ((module_id IS NOT NULL AND class_id IS NULL) OR (module_id IS NULL AND class_id IS NOT NULL))
);

-- Imports entre modules
CREATE TABLE IF NOT EXISTS code_import (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_module_id INTEGER NOT NULL,        -- Module qui importe
    imported_module TEXT NOT NULL,            -- Module/item importé (nom complet)
    import_type TEXT NOT NULL,                -- 'module', 'from', 'relative'
    alias TEXT,                               -- Alias (as xxx)
    is_external BOOLEAN DEFAULT 0,            -- Import externe au projet ?
    line_number INTEGER,                      -- Ligne de l'import
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_module_id) REFERENCES code_module(id) ON DELETE CASCADE
);

-- Relations entre entités du code
CREATE TABLE IF NOT EXISTS code_relation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,                -- 'class', 'function', 'module'
    source_id INTEGER NOT NULL,
    target_type TEXT NOT NULL,                -- 'class', 'function', 'module'
    target_id INTEGER NOT NULL,
    relation_type TEXT NOT NULL,              -- 'calls', 'inherits', 'uses', 'implements', 'instantiates'
    confidence REAL DEFAULT 1.0,              -- Confiance dans la relation (0.0-1.0)
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_type, source_id, target_type, target_id, relation_type)
);

-- Variables globales et constantes
CREATE TABLE IF NOT EXISTS code_variable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER,                        -- Module si globale
    class_id INTEGER,                         -- Classe si attribut
    name TEXT NOT NULL,
    type_annotation TEXT,                     -- Type si annoté
    value_preview TEXT,                       -- Aperçu de la valeur (tronqué)
    is_constant BOOLEAN DEFAULT 0,            -- UPPERCASE = constante
    line_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES code_module(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES code_class(id) ON DELETE CASCADE
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_module_file ON code_module(file_id);
CREATE INDEX IF NOT EXISTS idx_class_module ON code_class(module_id);
CREATE INDEX IF NOT EXISTS idx_function_module ON code_function(module_id);
CREATE INDEX IF NOT EXISTS idx_function_class ON code_function(class_id);
CREATE INDEX IF NOT EXISTS idx_import_source ON code_import(source_module_id);
CREATE INDEX IF NOT EXISTS idx_import_module ON code_import(imported_module);
CREATE INDEX IF NOT EXISTS idx_relation_source ON code_relation(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_relation_target ON code_relation(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_variable_module ON code_variable(module_id);
CREATE INDEX IF NOT EXISTS idx_variable_class ON code_variable(class_id);

-- ========================================
-- VUES UTILES POUR CODE INTELLIGENCE
-- ========================================

-- Vue des classes les plus complexes
CREATE VIEW IF NOT EXISTS complex_classes AS
SELECT
    cc.name,
    cc.full_name,
    cc.complexity_score,
    cc.method_count,
    cm.name as module_name,
    cf.path as file_path
FROM code_class cc
JOIN code_module cm ON cc.module_id = cm.id
JOIN cortex_file cf ON cm.file_id = cf.id
WHERE cc.complexity_score > 0
ORDER BY cc.complexity_score DESC, cc.method_count DESC
LIMIT 20;

-- Vue des fonctions les plus complexes
CREATE VIEW IF NOT EXISTS complex_functions AS
SELECT
    cf.name,
    cf.full_name,
    cf.complexity_score,
    cf.calls_count,
    cm.name as module_name,
    cfi.path as file_path
FROM code_function cf
LEFT JOIN code_module cm ON cf.module_id = cm.id
LEFT JOIN code_class cc ON cf.class_id = cc.id
LEFT JOIN code_module cm2 ON cc.module_id = cm2.id
LEFT JOIN cortex_file cfi ON COALESCE(cm.file_id, cm2.file_id) = cfi.id
WHERE cf.complexity_score > 0
ORDER BY cf.complexity_score DESC
LIMIT 20;

-- Vue du graphe d'imports
CREATE VIEW IF NOT EXISTS import_graph AS
SELECT
    cm.name as source_module,
    ci.imported_module as target_module,
    ci.import_type,
    ci.is_external,
    cf.path as source_file
FROM code_import ci
JOIN code_module cm ON ci.source_module_id = cm.id
JOIN cortex_file cf ON cm.file_id = cf.id
ORDER BY cm.name, ci.imported_module;

-- Vue des classes parentes les plus utilisées
CREATE VIEW IF NOT EXISTS popular_base_classes AS
SELECT
    json_each.value as base_class,
    COUNT(*) as usage_count
FROM code_class,
     json_each(code_class.base_classes)
WHERE json_each.value IS NOT NULL
GROUP BY json_each.value
HAVING usage_count > 1
ORDER BY usage_count DESC;

-- ========================================
-- TRIGGERS POUR CODE INTELLIGENCE
-- ========================================

-- Trigger: Mettre à jour le timestamp updated_at des modules
CREATE TRIGGER IF NOT EXISTS update_module_timestamp
AFTER UPDATE ON code_module
BEGIN
    UPDATE code_module SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger: Mettre à jour le timestamp updated_at des classes
CREATE TRIGGER IF NOT EXISTS update_class_timestamp
AFTER UPDATE ON code_class
BEGIN
    UPDATE code_class SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger: Mettre à jour le timestamp updated_at des fonctions
CREATE TRIGGER IF NOT EXISTS update_function_timestamp
AFTER UPDATE ON code_function
BEGIN
    UPDATE code_function SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger: Logger les changements de modules
CREATE TRIGGER IF NOT EXISTS log_module_change
AFTER INSERT ON code_module
BEGIN
    INSERT INTO change_log (change_type, entity_type, author, description, impact_level)
    VALUES (
        'create',
        'code_module',
        'CodeScanner',
        'New module discovered: ' || NEW.name,
        'low'
    );
END;

-- Mise à jour de schema_version
INSERT OR IGNORE INTO schema_version (version, description)
VALUES ('1.1.0', 'Added codebase structure tables for code intelligence');
