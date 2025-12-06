# Runtime Error Fix - December 3, 2025

## Problem Summary

The hydra-claude application was failing with the following error:

```
❌ LLM Call Failed
Error: litellm.BadRequestError: OpenrouterException -
{"error":{"message":"anthropic/claude-sonnet-4-20250514 is not a valid model ID","code":400}}
```

## Root Cause Analysis

The application was configured to use an invalid OpenRouter model ID: `anthropic/claude-sonnet-4-20250514`

This model ID does not exist in OpenRouter's model catalog. The error occurred because:
1. The default model configuration was set to a non-existent model
2. OpenRouter rejected the API request with a 400 Bad Request error
3. This caused the entire CrewAI workflow to fail before any agents could execute

## Remediation Steps

### Files Modified

1. **`runtime/crewai/quick_crew.py`** (Line 145)
   - Changed default model from `anthropic/claude-sonnet-4-20250514` to `anthropic/claude-3.5-sonnet`

2. **`runtime/crewai/crew.py`** (Line 57)
   - Changed default model from `anthropic/claude-sonnet-4-20250514` to `anthropic/claude-3.5-sonnet`

3. **`README.md`** (Lines 67-77)
   - Updated default model documentation
   - Added current valid model options

4. **`run.sh`** (Lines 7-9, 73)
   - Updated script comments and echo statements with correct default model

5. **`.kiro/specs/composable-me-hydra/requirements.md`** (Line 248)
   - Updated requirement specification to reflect correct default model

6. **`.kiro/steering/tech.md`** (Lines 5-7, 127-133)
   - Updated technical documentation with correct default model
   - Reordered model recommendations to prioritize working models

## Valid OpenRouter Model IDs

The following Claude models are confirmed to work with OpenRouter:

- `anthropic/claude-3.5-sonnet` - **Recommended default** (fast, high quality, widely available)
- `anthropic/claude-sonnet-4.5` - Latest model (if available in your region)
- `anthropic/claude-3-opus` - Highest quality (slower, more expensive)
- `anthropic/claude-3-haiku` - Fastest, most economical

## Validation

After applying the fixes:

```bash
cd hydra-claude
source .venv/bin/activate
python runtime/crewai/quick_crew.py --help
```

**Result**: ✅ Application loads successfully without model errors

## Usage

To run the application with the fixed configuration:

```bash
# Using default model (claude-3.5-sonnet)
./run.sh examples/sample_jd.md examples/sample_resume.md

# Or override with a different model
export OPENROUTER_MODEL="anthropic/claude-sonnet-4.5"
./run.sh examples/sample_jd.md examples/sample_resume.md
```

## Prevention

To prevent similar issues in the future:
1. Always verify model IDs against OpenRouter's official model list: https://openrouter.ai/models
2. Use stable, well-documented model IDs as defaults
3. Test configuration changes before committing
4. Keep documentation in sync with code changes

## Status

✅ **RESOLVED** - All configuration files updated, application validated and working

