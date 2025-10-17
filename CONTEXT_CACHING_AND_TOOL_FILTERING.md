Context caching and tool filtering (QC improvement)

Objective
- Reduce token and cost usage by reusing context and by filtering unnecessary tool calls.

Challenges
- Cache growth over time, stale data, privacy concerns, and cache invalidation.

Recommendations
- Context caching
  - Cache per session: map session_id -> relevant context (recent messages, key facts)
  - Cache eviction: implement TTL (time-to-live) and/or LRU policy
  - Context granularity: cache only structured, non-sensitive summaries when possible
  - Serialization: store cache in a lightweight in-memory store with optional persistence for long sessions
- Tool call filtering
  - Pre-checks: determine if user intent can be answered from cached context or static knowledge before invoking tools
  - Debounce duplicates: suppress identical tool requests within a small time window
  - Input validation: guard against malformed or unsafe requests before tool invocation
  - Budgeting: track estimated token cost per tool call and skip when near budget limit
- Token budgeting and measurement
  - Instrument logs to capture cache hits/misses, tool call counts, and token usage
  - Define a target reduction (e.g., 20-50%) and measure against it
- Observability and safety
  - Cache size monitoring and eviction metrics
  - Clear policies for stale or sensitive data (PII masking, no storage beyond necessity)

Implementation notes
- Data structures (pseudocode)
  - Cache: dict<session_id, CacheEntry>
  - CacheEntry: { context: string, timestamp: int, ttl: int, usage_count: int }
- Pseudo interfaces
  - get_context(session_id) -> Context
  - set_context(session_id, context, ttl)
  - should_call_tool(input) -> bool
  - record_tool_call(tool_name, input, output, tokens_used)
- Quick wins
  - Implement an in-memory LRU cache for the most recent N sessions
  - Add a lightweight pre-check that answers common, static questions without tool calls

Acceptance criteria
- Token usage reductions observed over a defined period
- Cache hit rate above a predefined threshold
- No regressions in latency beyond acceptable SLAs