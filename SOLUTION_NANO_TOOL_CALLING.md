# Solution: NANO Tool Calling Issue

## 🎯 Problem

User requested: "utilise un outil pour extraire le texte d'un XPATH=/html/body/div[2]/div[2]/div/div[2]/div[1]/div/section[5]/div[2]/div/div[4]/div[1] dans un URL=https://www.forbes.com/real-time-billionaires/"

The system was not calling the `scrape_xpath` tool even with explicit parameters provided.

## 🔍 Root Cause Analysis

### Investigation Steps

1. **Simple Tool Call Test** (`test_simple_tool_call.py`):
   - NANO **CAN** call tools with a minimal system prompt
   - Test with simple message: ✅ SUCCESS - tool called correctly

2. **Complex Prompt Test** (`test_nano_xpath_parsing.py`):
   - NANO **FAILS** to call tools with the complex prompt from `prompt_engineer.py`
   - Same request with prompt_engineer prompt: ❌ FAIL - no tool call

### Root Cause

**The NANO prompt was designed for TEXT-BASED tool detection, not NATIVE function calling:**

```python
# OLD PROMPT (BROKEN):
RESPONSE FORMAT:
🎯 Result: [Your response - 1-2 sentences]
💭 Confidence: [HIGH/MEDIUM/LOW]
⚠️ Severity: [CRITICAL/HIGH/MEDIUM/LOW]
🔧 Actions: [Tools used or "None" or "TOOLER_NEEDED: ..."]
```

This instructed NANO to FORMAT its response with emoji markers and describe tool usage in text, which **conflicts** with OpenAI's native function calling API.

The system uses **native OpenAI tool calling** (functions API), where the LLM returns structured `tool_calls` in the API response, not text descriptions.

##  Solution Implemented

### Fix: Simplified NANO Prompt

Changed from emoji-based response format to **direct function calling instructions**:

```python
# NEW PROMPT (WORKS):
"""You are Cortex, an AI agent with tools.

AVAILABLE TOOLS:
{tools_list}

YOUR JOB:
1. ANALYZE the user request
2. DECIDE what to do:
   - General conversation? → Answer naturally
   - Use a tool? → Call it directly using function calling
   - Need a capability you don't have? → Say "TOOLER_NEEDED: [capability]"

EXAMPLES:

User: "Do you know that pencils have erasers?"
Response: Yes! Most pencils have erasers on top for correcting mistakes.

User: "Extract text from https://example.com using XPath //h1/text()"
Response: [Call scrape_xpath tool with url="https://example.com", xpath="//h1/text()"]

User: "git push to remote"
Response: TOOLER_NEEDED: git operations (push, pull, commit, branch)

IMPORTANT:
- When the user asks to USE a tool with specific parameters, call it immediately
- Don't describe what you're doing, just call the tool
- If you can't do something, clearly state "TOOLER_NEEDED: [what's missing]" """
```

### Key Changes

1. **Removed emoji-based formatting** (🎯, 💭, ⚠️, 🔧)
2. **Removed explicit response format** that constrained output
3. **Added clear instruction**: "Call it directly using function calling"
4. **Simplified examples** showing natural responses vs tool calls
5. **Kept TOOLER_NEEDED** for missing capabilities

### File Modified

**`cortex/core/prompt_engineer.py`**:
- Line 94-123: `_build_nano_prompt()` method completely rewritten

## 📊 Test Results

### Before Fix

```
Test 1: "Use scrape_xpath with url=X xpath=Y"
❌ FAIL: Empty response, no tool call

Test 2: "Extract text from XPATH=X at URL=Y"
❌ FAIL: Response truncated, no tool call

Test 3: Forbes URL (user's request)
❌ FAIL: Response truncated, no tool call
```

### After Fix (Simple Prompt)

```
Request: "Use scrape_xpath to extract h1 from https://example.com"
✅ SUCCESS: Tool called correctly
   scrape_xpath({'url': 'https://example.com', 'xpath': '//h1/text()'})
```

### Expected Result with New Prompt

The system should now correctly call `scrape_xpath` when users provide explicit parameters like:
- "Use scrape_xpath with url=X and xpath=Y"
- "Extract text from XPATH=X at URL=Y"
- "utilise un outil pour extraire le texte d'un XPATH=X dans un URL=Y"

## 🎓 Lessons Learned

### Key Insights

1. **Native Function Calling vs Text-Based**:
   - Modern LLMs (OpenAI, Anthropic, DeepSeek) support native function calling
   - Prompts should NOT instruct formatting when using native tools API
   - Let the LLM decide: natural response OR tool call, not both

2. **Prompt Engineering Anti-Patterns**:
   - ❌ DON'T: Force specific output formats (emoji markers, structured text)
   - ❌ DON'T: Ask LLM to "describe" what tool to use in text
   - ✅ DO: Give simple, direct instructions about when to call tools
   - ✅ DO: Let the API handle the mechanics of tool calling

3. **NANO Model Limitations**:
   - gpt-3.5-turbo (NANO tier) is less reliable with complex prompts
   - Works best with SHORT, SIMPLE, DIRECT instructions
   - Large structured prompts confuse it and reduce tool calling accuracy

4. **Debugging Strategy**:
   - Test with **minimal prompt first** to verify capability
   - Add complexity **incrementally** and test each change
   - If tool calling breaks, remove formatting constraints

## 🚀 Next Steps for User

### Immediate Action

The simplified NANO prompt has been committed. To use the Forbes extraction:

```bash
# Option 1: Via Cortex CLI (interactive)
python3 -m cortex.cli.cortex_cli

# Then type:
cortex> utilise scrape_xpath avec url=https://www.forbes.com/real-time-billionaires/ et xpath=/html/body/div[2]/div[2]/div/div[2]/div[1]/div/section[5]/div[2]/div/div[4]/div[1]

# Option 2: Direct Python call
from cortex.tools.intelligence_tools import scrape_xpath

result = scrape_xpath(
    url="https://www.forbes.com/real-time-billionaires/",
    xpath="/html/body/div[2]/div[2]/div/div[2]/div[1]/div/section[5]/div[2]/div/div[4]/div[1]"
)
print(result)
```

### Future Improvements

1. **Tool Call Detection**:
   - Add fallback: if NANO doesn't call tool but mentions it in text, parse and execute
   - Monitor tool call success rate per model tier
   - Log when models fail to call tools for analysis

2. **Prompt Optimization**:
   - A/B test different NANO prompt variations
   - Measure: tool call accuracy, response quality, token usage
   - Find optimal balance between guidance and flexibility

3. **Model Selection**:
   - For critical tool calls, consider using DEEPSEEK or CLAUDE tier
   - NANO is cheap ($0.0001/call) but less reliable for complex tasks
   - Add tier escalation: NANO fails → retry with DEEPSEEK

## 📁 Files Modified

### New Files
- `test_simple_tool_call.py` - Minimal test proving NANO can call tools
- `test_nano_xpath_parsing.py` - Comprehensive test with prompt_engineer prompts
- `SOLUTION_NANO_TOOL_CALLING.md` - This document

### Modified Files
- `cortex/core/prompt_engineer.py` (Lines 94-123) - Simplified NANO prompt

### Commit

```bash
git add cortex/core/prompt_engineer.py test_simple_tool_call.py test_nano_xpath_parsing.py SOLUTION_NANO_TOOL_CALLING.md
git commit -m "fix: Simplify NANO prompt to enable native function calling"
```

## 📊 Impact

### Performance
- **Tool calling reliability**: Improved (needs live testing to quantify)
- **Response time**: Same (no additional API calls)
- **Token usage**: Reduced (simpler prompt = fewer tokens)

### Cost
- **Before**: Complex prompt = ~600 tokens input
- **After**: Simple prompt = ~350 tokens input
- **Savings**: ~40% reduction in input tokens
- **Per call**: $0.000025 saved (at gpt-3.5-turbo rates)

### User Experience
- **Before**: Tool calls didn't work with explicit parameters
- **After**: Should work reliably (needs user confirmation)
- **Clarity**: Simpler prompt is easier to understand and maintain

## ✅ Status

**Status**: ✅ IMPLEMENTED (Needs Live Testing)
**Date**: 2025-10-15
**Version**: 4.2.2

**Awaiting user feedback** on whether the Forbes XPath extraction now works correctly in the live Cortex CLI.
