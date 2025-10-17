Context caching and tool filtering for cost optimization

Goals
- Reduce token usage and runtime cost by caching results of frequent tool calls and filtering tool usage by cost.

Proposed strategies
- Context caching
  - Cache scope: per-session cache of tool results with TTL
  - Cache keys: (tool_name, serialized_parameters, user_context)
  - TTLs: 60-300 seconds based on volatility; invalidate on data-change signals
  - Invalidation: manual reset, explicit updates, or TTL expiry
- Tool filtering
  - Maintain approximate per-tool token cost model
  - Prefer lightweight tools when possible; batch parallel calls only if independence holds
  - Deduplicate identical requests within a short time window

Implementation plan
- Add an in-memory per-session cache with TTL management
- Intercept tool invocations to check cache before executing
- Extend tool dispatch to store/retrieve cached results
- Monitor and log cache hit rate and cost savings

Metrics
- Target: 30-50% reduction in token usage and cost
- Track: cache hit rate, average latency, total tokens used per session

Risks and mitigations
- Staleness: use TTL and explicit invalidation
- Incorrect results due to cached state: include full input parameters in cache keys; cache only idempotent results when safe

Next steps
- Implement lightweight CacheManager and patch tool dispatcher to consult cache
- Run A/B tests to measure savings
