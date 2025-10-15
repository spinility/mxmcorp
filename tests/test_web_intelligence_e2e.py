"""
End-to-End Test for Phase 4.1 - Web Intelligence System

Tests complete flow:
1. Add URL + XPath to registry
2. Validate XPath with stealth crawler
3. Scrape data
4. Optimize context with DynamicContextManager
5. Enrich prompt with ContextEnrichmentAgent
6. Execute workflow with enriched context
"""

import time
from cortex.departments.intelligence.xpath_source_registry import XPathSourceRegistry
from cortex.departments.intelligence.stealth_web_crawler import StealthWebCrawler
from cortex.departments.intelligence.dynamic_context_manager import DynamicContextManager
from cortex.departments.intelligence.context_enrichment_agent import (
    ContextEnrichmentAgent,
    AgentMessage
)
from cortex.core.workflow_engine import WorkflowEngine, WorkflowStep


def test_complete_web_intelligence_flow():
    """Test complet du système Web Intelligence"""

    print("="*70)
    print("PHASE 4.1 - WEB INTELLIGENCE SYSTEM - END-TO-END TEST")
    print("="*70)

    # STEP 1: Setup components
    print("\n1. Setting up components...")

    registry = XPathSourceRegistry("cortex/data/test_web_intelligence_e2e.json")
    crawler = StealthWebCrawler("cortex/data/test_web_intelligence_e2e_scraped")
    context_manager = DynamicContextManager("cortex/data/test_web_intelligence_e2e_scraped")
    enrichment_agent = ContextEnrichmentAgent(context_manager, registry)

    print("✓ All components initialized")

    # STEP 2: Add web sources
    print("\n2. Adding web sources to registry...")

    source_hn = registry.add_source(
        name="HackerNews Frontpage",
        url="https://news.ycombinator.com",
        xpath="//span[@class='titleline']/a/text()",
        description="Top stories on HackerNews",
        category="tech_news",
        refresh_interval_hours=6
    )

    print(f"✓ Added source: {source_hn.name} ({source_hn.id})")

    # STEP 3: Validate XPath
    print("\n3. Validating XPath...")

    validation = crawler.validate_xpath(source_hn)

    print(f"✓ Validation result:")
    print(f"  Success: {validation.success}")
    print(f"  Elements found: {validation.elements_found}")
    print(f"  Response time: {validation.response_time_ms:.0f}ms")
    print(f"  Sample: {validation.sample_data[:2]}")

    assert validation.success, "XPath validation failed"

    # STEP 4: Scrape data
    print("\n4. Scraping data...")

    scraped = crawler.scrape(source_hn, validate_first=False)

    print(f"✓ Scraped {len(scraped.data)} items")
    print(f"  First 3 items:")
    for i, item in enumerate(scraped.data[:3], 1):
        print(f"    {i}. {item[:60]}...")

    assert len(scraped.data) > 0, "No data scraped"

    # STEP 5: Optimize context
    print("\n5. Optimizing context...")

    optimized = context_manager.optimize_scraped_data(
        scraped,
        query="Python AI trends"
    )

    print(f"✓ Context optimized:")
    print(f"  Context ID: {optimized.context_id}")
    print(f"  Summary: {optimized.summary[:100]}...")
    print(f"  Key items: {len(optimized.key_items)}")
    print(f"  Insights: {optimized.insights}")
    print(f"  Freshness: {optimized.freshness_score:.0%}")
    print(f"  Confidence: {optimized.confidence_score:.0%}")
    print(f"  Relevance: {optimized.relevance_score:.0%}")

    # STEP 6: Test enrichment agent
    print("\n6. Testing context enrichment...")

    message = AgentMessage(
        from_agent="RequirementsAnalyzer",
        to_agent="CodeWriter",
        task="Analyze current trends in Python and AI development",
        context_requests=["tech_news", "hackernews"],
        metadata={"priority": "high"}
    )

    enriched_message = enrichment_agent.enrich_message(
        message,
        query="Python AI trends"
    )

    print(f"✓ Message enriched:")
    print(f"  Enriched: {enriched_message.enriched}")
    print(f"  Contexts added: {enriched_message.contexts_added}")
    print(f"  Task length: {len(message.task)} → {len(enriched_message.task)} chars")

    if enriched_message.contexts_added:
        print(f"\n  Preview of enriched task:")
        print(f"  {'-'*60}")
        print(f"  {enriched_message.task[:300]}...")
        print(f"  {'-'*60}")

    # STEP 7: Test workflow with enrichment
    print("\n7. Testing workflow with context enrichment...")

    # Créer workflow engine avec enrichment agent
    workflow_engine = WorkflowEngine(context_enrichment_agent=enrichment_agent)

    # Définir workflow steps
    def analyze_trends():
        """Simule analyse de tendances"""
        time.sleep(0.1)
        return "Analyzed: Python AI frameworks are trending"

    def write_report():
        """Simule écriture de rapport"""
        time.sleep(0.1)
        return "Report written with dynamic context"

    steps = [
        WorkflowStep(
            name="Analyze trending tech topics",
            action=analyze_trends,
            department="analysis",
            agent_name="TrendAnalyzer",
            context_requests=["tech_news"],  # Demande contexte dynamique
            allow_enrichment=True
        ),
        WorkflowStep(
            name="Write technical report",
            action=write_report,
            department="writing",
            agent_name="ReportWriter",
            context_requests=[],  # Pas de contexte additionnel
            allow_enrichment=False
        )
    ]

    result = workflow_engine.execute_workflow(
        workflow_name="tech_trend_analysis",
        request_text="Analyze current tech trends and write report",
        steps=steps,
        request_type="analysis"
    )

    print(f"✓ Workflow executed:")
    print(f"  Success: {result.success}")
    print(f"  Duration: {result.duration_seconds:.2f}s")
    print(f"  Steps: {result.steps_completed}/{result.steps_total}")

    assert result.success, "Workflow failed"

    # STEP 8: Statistics
    print("\n8. System statistics...")

    stats = enrichment_agent.get_statistics()
    print(f"✓ Enrichment Agent stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    registry_stats = registry.get_statistics()
    print(f"\n✓ Registry stats:")
    for key, value in registry_stats.items():
        print(f"  {key}: {value}")

    # STEP 9: Display optimized context
    print("\n9. Display prompt-ready context...")

    prompt_context = optimized.to_prompt_context(include_metadata=True)
    print(f"✓ Generated prompt context ({len(prompt_context)} chars):")
    print("="*70)
    print(prompt_context)
    print("="*70)

    print("\n" + "="*70)
    print("✅ PHASE 4.1 WEB INTELLIGENCE SYSTEM - ALL TESTS PASSED!")
    print("="*70)

    return True


if __name__ == "__main__":
    try:
        success = test_complete_web_intelligence_flow()

        if success:
            print("\n✅ All tests passed successfully!")
        else:
            print("\n❌ Some tests failed")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
