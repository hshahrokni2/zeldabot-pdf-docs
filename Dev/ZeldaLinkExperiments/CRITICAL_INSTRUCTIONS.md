# ⚠️ CRITICAL INSTRUCTIONS - READ COMPLETELY BEFORE DOING ANYTHING ⚠️

## IMMEDIATE ACTION SEQUENCE

1. STOP. Take a deep breath. Read this ENTIRE document FIRST.
2. Read `START.md` for comprehensive project information.
3. Check `docs/STATE_SNAPSHOT.md` for current project state.
4. Examine core files in this EXACT order:
   - `src/extraction/schema.py` - Pydantic models with year-over-year fields
   - `src/extraction/extract.py` - Extraction with unverified fields detection
   - `unverified_fields_guide.py` - Potential fields we're looking for

## DANGER ZONES - DO NOT TOUCH UNLESS ABSOLUTELY SURE

- **DO NOT** change any imports in `src/extraction/__init__.py`
- **DO NOT** modify existing field types in `src/extraction/schema.py`
- **DO NOT** change API calling patterns in extraction classes
- **DO NOT** create entirely new approaches before examining existing code

## IF YOU FEEL UNCERTAIN

If you feel uncertain about how to proceed:

1. Look for EXAMPLES in the codebase before creating something new
2. Run the existing tests/scripts to see behavior in action
3. Add to/extend existing components rather than creating new ones
4. Follow the patterns in the existing code even if they seem suboptimal

## IF YOU'RE ABOUT TO GO ROGUE

If you find yourself about to abandon existing patterns:

1. STOP and document what you're attempting to do
2. Review `docs/START.md` again, especially the DO NOT section
3. Create a backup of any files you plan to change significantly
4. Look for alternatives that follow existing patterns

## SAFETY NET COMMANDS

If all else fails, these commands will help you get back on track:

```bash
# Run test extraction to see correct behavior
./scripts/run_sailor_extraction.sh

# Check available scripts
ls -la scripts/

# View core Pydantic models
less src/extraction/schema.py

# See example extraction output
less data/examples/sailor_extraction_results.json
```

## CRITICAL PROJECT INSIGHT

This project integrates multiple LLMs to extract data from Swedish BRF reports with the CORE VALUE being in the self-learning schema improvement process. All designs should prioritize this capability.

## HOW TO EXTEND SCHEMA PROPERLY

To add new fields to the schema:

1. Examine current field patterns in `src/extraction/schema.py`
2. Add new fields following EXACTLY the same pattern as existing ones
3. Update ALL extractor prompts in `src/extraction/extract.py`
4. Test with REAL extraction before committing changes
5. Document all schema changes in `docs/STATE_SNAPSHOT.md`

## NEXT PLANNED TASKS (START HERE)

1. Test extraction with year-over-year comparison fields
2. Implement cross-page integration for complex data
3. Develop field-specific extractors for Swedish tables
4. Implement cross-page integration for complex data
5. Improve error handling for API failures

Remember: When in doubt, FOLLOW THE EXISTING PATTERNS!