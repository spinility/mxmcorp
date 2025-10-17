# Roadmap: Architecture, data model & relationships

This document describes a machine-readable yet human-friendly roadmap model intended for planning, tracking and reporting. It covers core entities, their fields, relationships and example payloads. It is designed to be used as the single source of truth for Cortex planning and for automation (e.g., updating statuses, generating views, calculating progress).

## 1) Vision & scope
- Provide a consistent, versioned representation of work across time horizons (quarters, releases).
- Enable cross-team alignment: product, engineering, data, and ops.
- Support drill-down from high-level goals to concrete tasks with dependency tracking and owners.
- Serve as input to dashboards, reports, and milestone planning.

## 2) Core entities
- RoadmapVersion
- Timebox
- Objective
- Initiative
- Epic
- Feature (Capability)
- Task
- Dependency
- Owner / Stakeholder
- Milestone
- Label / Tag
- Risk / Mitigation
- Metric (Progress, Velocity)
- Stakeholder

## 3) Entity definitions (fields)
- RoadmapVersion
  - id: string (e.g., v2025.2)
  - name: string (e.g., "2025 Q4 Roadmap" )
  - start_date: date
  - end_date: date
  - status: enum(Planned, Active, OnHold, Completed, Archived)
  - description: string
  - version_notes: string
  - related_milestones: list[string] // Milestone ids

- Timebox
  - id: string
  - name: string
  - start_date: date
  - end_date: date
  - roadmaps: list[string] // RoadmapVersion ids
  - goals: list[string] // high-level goals

- Objective
  - id: string
  - title: string
  - description: string
  - alignment_to: list[string] // Epics/Initiatives IDs
  - owner: string // team or person
  - priority: enum(Low, Medium, High, Critical)
  - status: enum(Planned, InProgress, Completed, Blocked)
  - metrics: object // optional
  - related_initiatives: list[string]

- Initiative
  - id: string
  - title: string
  - description: string
  - objective_id: string
  - owner: string
  - priority: enum(Low, Medium, High, Critical)
  - status: enum(Planned, InProgress, Completed, Blocked)
  - epics: list[string]

- Epic
  - id: string
  - title: string
  - description: string
  - initiative_id: string
  - owner: string
  - priority: enum(Low, Medium, High, Critical)
  - status: enum(Planned, InProgress, Completed, Blocked)
  - features: list[string]

- Feature (Capability)
  - id: string
  - title: string
  - description: string
  - epic_id: string
  - owner: string
  - priority: enum(Low, Medium, High, Critical)
  - status: enum(Planned, InProgress, Completed, Blocked)
  - tasks: list[string]

- Task
  - id: string
  - title: string
  - description: string
  - feature_id: string
  - owner: string
  - status: enum(Planned, InProgress, Review, Completed, Blocked)
  - priority: enum(Low, Medium, High, Critical)
  - estimate_hours: number
  - start_date: date
  - due_date: date
  - dependencies: list[string] // task ids
  - tags: list[string]

- Dependency
  - id: string
  - depends_on: string // task id
  - depends_for: string // task id
  - type: enum(Finish-to-Start, Start-to-Start, Finish-to-Finish, Start-to-Finish)
  - reason: string

- Milestone
  - id: string
  - name: string
  - due_date: date
  - description: string
  - scope: list[string] // task/feature ids included
  - roadmap_version_id: string

- Label / Tag
  - id: string
  - name: string
  - description: string

- Risk / Mitigation
  - id: string
  - title: string
  - description: string
  - likelihood: enum(Low, Medium, High, Critical)
  - impact: enum(Low, Medium, High, Critical)
  - mitigation: string
  - owner: string

- Metric
  - id: string
  - type: enum(Progress, Velocity, Burnup, Burnout, LeadTime)
  - value: any
  - date: date
  - related_id: string // roadmap/objective/epic/etc.

- Stakeholder
  - id: string
  - name: string
  - role: string
  - contact: string

## 4) Relationships & rules
- A RoadmapVersion contains many Milestones and Objectives.
- An Objective groups multiple Initiatives.
- An Initiative contains multiple Epics.
- An Epic contains multiple Features.
- A Feature contains multiple Tasks.
- A Task may depend on one or more other Tasks (dependencies).
- Tasks have owners (team/person) and statuses; status propagates to parent elements when all children complete.
- Milestones link to a scope consisting of features/tasks; due_date constrains delivery windows.
- Labels/Tags classify items for filtering and dashboards.
- Risks are linked to items (which risk affects which work item) and have mitigations.
- Metrics capture progress at RoadmapVersion, Objective, Epic, or Feature levels.
- Timeboxs can be used to align RoadmapVersions with planning cycles.

## 5) Data modeling conventions
- IDs use a stable, unique format: TYPE-YYYY-NNN (e.g., TASK-0001).
- Dates should use ISO 8601 (YYYY-MM-DD).
- Status and Priority enums are centralized; avoid mixing spellings.
- Avoid circular dependencies; treat dependencies as directional.
- Each item has at least one owner.
- Each item should map to higher-level goals for traceability.

## 6) Example payload (JSON-like)
{
  "RoadmapVersion": {
    "id": "RV-2025H2",
    "name": "2025 H2 Roadmap",
    "start_date": "2025-07-01",
    "end_date": "2025-12-31",
    "status": "Active",
    "description": "Roadmap for H2 2025 focusing on stability, performance and developer experience."
  },
  "Objectives": [
    {
      "id": "OBJ-001",
      "title": "Stability & Reliability",
      "description": "Eliminate flake and improve crash-free user experience.",
      "owner": "Platform SRE",
      "priority": "Critical",
      "status": "InProgress",
      "initiatives": ["INIT-001"]
    }
  ],
  "Initiatives": [
    {
      "id": "INIT-001",
      "title": "Improve crash-free rate",
      "description": "Target 99.9% crash-free in production.",
      "objective_id": "OBJ-001",
      "owner": "Platform Eng",
      "priority": "High",
      "status": "InProgress",
      "epics": ["EPIC-001"]
    }
  ],
  "Epics": [
    {
      "id": "EPIC-001",
      "title": "Reliability improvements for core services",
      "description": "RCA-driven changes for core APIs.",
      "initiative_id": "INIT-001",
      "owner": "Platform Eng",
      "priority": "High",
      "status": "InProgress",
      "features": ["FEAT-001"]
    }
  ],
  "Features": [
    {
      "id": "FEAT-001",
      "title": "Circuit breaker patterns & timeout guards",
      "description": "Add resilience patterns to critical calls.",
      "epic_id": "EPIC-001",
      "owner": "Backend Team",
      "priority": "High",
      "status": "InProgress",
      "tasks": ["TASK-0001"]
    }
  ],
  "Tasks": [
    {
      "id": "TASK-0001",
      "title": "Add circuit breaker to gateway",
      "description": "Implement resilience in gateway routing.",
      "feature_id": "FEAT-001",
      "owner": "Backend Eng Team",
      "status": "InProgress",
      "priority": "High",
      "estimate_hours": 8,
      "start_date": "2025-08-01",
      "due_date": "2025-08-15",
      "dependencies": [],
      "tags": ["resilience", "gateway"]
    }
  ],
  "Milestones": [
    {
      "id": "MS-001",
      "name": "Prototype resilience in staging",
      "due_date": "2025-08-31",
      "description": "First pass on circuit breakers and timeouts",
      "scope": ["FEAT-001", "TASK-0001"],
      "roadmap_version_id": "RV-2025H2"
    }
  ],
  "Risks": [],
  "Metrics": []
}

## 7) Conventions for usage
- Prefer JSON for machine processing; Markdown for human-readable views.
- Keep the RoadmapVersion as the root year/period, with linked items to show traceability.
- Maintain a changelog in RoadmapVersion.description or a separate ChangeLog section.

## 8) How to evolve
- Add new RoadmapVersions for new time horizons; archive old versions.
- Use a stable identifier strategy and celebrate completed items; link to retrospective notes.

## 9) Next steps to integrate with your workflow
- Define a lightweight API or script to export/import this structure from a database or file store.
- Create views/dashboards based on RoadmapVersion with rollups up to Objectives and down to Tasks.
- Add validation to ensure dependencies do not form cycles and dates are coherent.
