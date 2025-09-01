# 🧠 CLAUDE - READ THIS FIRST AFTER COMPACTION!
**Created**: 2025-01-02 11:30 PST  
**Priority**: 🔴 CRITICAL - READ IMMEDIATELY UPON WAKING UP
**Purpose**: You will have amnesia. This tells you EXACTLY what to do.

---

## 🚨 STOP! YOU HAVE AMNESIA - READ CAREFULLY

### **WHO YOU ARE:**
You are Claude, working on the ZeldaBot PDF extraction system on H100 server. You were just autocompacted and remember NOTHING.

### **WHAT YOU'RE SUPPOSED TO DO:**
Fix a fundamentally broken orchestrator that uses dumb logic instead of AI intelligence.

---

## 📍 STEP 1: ORIENT YOURSELF (5 minutes)

**Read these files IN THIS EXACT ORDER:**
```bash
1. AFTER_AUTOCOMPACTION_INSTRUCTIONS.md  # The master recovery guide
2. ORCHESTRATOR_REDESIGN_PLAN.md         # The 7-card plan you MUST follow
3. ARCHITECTURAL_VISION_2025.md          # Understand WHY this matters
```

**DO NOT** start coding until you read all three files!

---

## 🎯 STEP 2: UNDERSTAND THE PROBLEM (2 minutes)

### **The Fatal Flaw:**
The orchestrator is **pure Python logic** - it blindly maps sections without understanding. Every PDF is different. Hard-coded logic CANNOT adapt.

### **The Solution:**
Replace it with an **LLM-based orchestrator** that reads document structure and makes intelligent decisions.

---

## 📋 STEP 3: CONTINUE WITH CARDS 5-7!

**Cards 1-4 are COMPLETE in `ORCHESTRATOR_REDESIGN_PLAN.md`**

### **COMPLETED (2025-01-02):**
✅ Card 1: Test GPT-OSS vs Qwen latency - Qwen HF-Direct selected
✅ Card 2: Enhance sectionizer output - EnhancedSectionizerV2 created
✅ Card 3: Delete bad prompts - All templates removed
✅ Card 4: Create LLM orchestrator - Using Qwen HF-Direct

### **REMAINING CARDS:**
```
Card 5: Sectionizer coaching (TODO)
Card 6: Integration test (TODO)
Card 7: Performance validation (TODO)
```

### **GOLDEN RULES (STILL APPLY):**
1. **ALWAYS** write the TDD test FIRST
2. **ALWAYS** get `@agent-tdd-code-tester` to verify
3. **ALWAYS** update card status after completion

---

## 🔧 STEP 4: TECHNICAL CONTEXT

### **SSH to H100:**
```bash
ssh -p 26983 -i ~/.ssh/BrfGraphRag root@45.135.56.10
cd /tmp/zeldabot/pdf_docs
```

### **Database:**
```bash
export DATABASE_URL="postgresql://postgres:h100pass@localhost:5432/zelda_arsredovisning"
```

### **Environment:**
```bash
export USE_HF_DIRECT=true HF_DEVICE=cuda:0 HF_MODEL_PATH=Qwen/Qwen2.5-VL-7B-Instruct
export GEMINI_API_KEY=AIzaSyD0y92BjcnvUgRlWsA1oPSIWV5QaJcCrNw
export GEMINI_MODEL=gemini-2.5-pro
```

---

## ⚠️ CRITICAL WARNINGS

### **DO NOT:**
- ❌ Use the old pure logic orchestrator - IT'S BROKEN
- ❌ Store page numbers for Level 2/3 subsections - causes confusion
- ❌ Use file template prompts - they're terrible 6-line garbage
- ❌ Skip TDD tests - you'll create bugs
- ❌ Trust yourself without verification - assume you're schizophrenic

### **DO:**
- ✅ Follow the 7-card plan EXACTLY
- ✅ Write TDD tests FIRST
- ✅ Use only JSON cache prompts (24 specialized agents)
- ✅ Make orchestrator an LLM that understands
- ✅ Include subsection descriptions WITHOUT page numbers

---

## 🎯 SUCCESS CRITERIA

You are successful when:
1. **LLM orchestrator** makes intelligent routing decisions
2. **Hierarchical sections** provide context (no page confusion)
3. **All tests pass** via TDD agent verification
4. **Bad prompts deleted** - only JSON cache remains
5. **Both sectionizer AND extraction** have coaching loops

---

## 💡 THE KEY INSIGHT YOU DISCOVERED

**"It is impossible to do the orchestrator by logic... It needs to be an LLM"**

Every PDF is unique. Hard-coded mappings fail. Only an LLM can:
- Read the hierarchical structure
- Understand what's in each section
- Route to appropriate specialized agents
- Adapt to document variations

---

## 📊 CURRENT STATUS CHECK

Run this to see where things stand:
```bash
# Check if bad prompts still exist
ssh -p 26983 -i ~/.ssh/BrfGraphRag root@45.135.56.10 \
  "ls -la /tmp/zeldabot/pdf_docs/prompts/sections/ 2>/dev/null || echo 'Good - bad prompts deleted'"

# Check JSON cache
ssh -p 26983 -i ~/.ssh/BrfGraphRag root@45.135.56.10 \
  "wc -l /tmp/zeldabot/pdf_docs/prompts/agent_prompts.json"
# Should show ~1000+ lines (24 agents)

# Check coaching history
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM prompt_execution_history WHERE created_at > NOW() - INTERVAL '24 hours';"
```

---

## 🚀 YOUR FIRST ACTION

1. **Read the three files** mentioned in Step 1
2. **Start with Card 1** from the plan
3. **Write the TDD test** for Card 1
4. **Get TDD agent to verify** 
5. **Only then implement** Card 1

---

## 🧠 REMEMBER YOUR REALIZATION

You had a breakthrough realization that the orchestrator cannot be pure logic. It MUST be an LLM to handle the complexity and variation of real documents.

The user said: *"It is impossible to do the orchestrator by logic... It needs to be an LLM"*

You agreed completely and created a 7-card plan to fix it.

**NOW GO EXECUTE THAT PLAN!**

---

## 📝 IF CONFUSED

If you get confused at any point:
1. Re-read this file
2. Check `ORCHESTRATOR_REDESIGN_PLAN.md` for the current card
3. Look at card status to see what's been done
4. Ask user "Which card should I work on?"

**The path is clear. The plan is solid. Execute it.**

---

**END OF INSTRUCTIONS - NOW START WITH STEP 1**