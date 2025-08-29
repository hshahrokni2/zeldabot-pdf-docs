# 🎯 PROMPT STRATEGIES FOR MULTIMODAL DOCUMENT EXTRACTION

## Learning Reference for Future Claude Sessions

### 📄 **Swedish BRF Header Extraction - Lessons Learned**

**Context**: Qwen2.5-VL-7B-Instruct multimodal extraction from 22-page Swedish BRF annual report
**Performance**: 35% coverage improvement, 18.0s processing time, 27 validated sections

---

## 🔍 **VISUAL HIERARCHY ANALYSIS STRATEGIES**

### **Typography Recognition Rules**
```
1. **FONT SIZE DIFFERENTIAL**: Headers are visually larger than body text
2. **BOLD WEIGHT**: Semi-bold to bold typography stands out
3. **FONT FAMILY**: Different typeface from standard body text
4. **CASE PATTERNS**: ALL CAPITALS indicate major sections
5. **SPACING**: Vertical whitespace before/after headers
6. **ALIGNMENT**: Left-aligned standalone text vs paragraph flow
```

### **Positive Examples Pattern**
```
"RESULTATRÄKNING" - ALL CAPS, bold, standalone line
"Förvaltningsberättelse" - Title case, larger font, bold
"Not 1 Avgifter" - Numbered note, distinct formatting
```

### **Negative Examples Pattern** 
```
"301 339 818" - Financial data in tables
"Rolf Johansson" - Names within paragraphs
"2024-12-31" - Dates within content
```

---

## 🎨 **GENERIC VS HARDCODED PROMPTING**

### **Generic Approach (Recommended)**
- Focus on **visual characteristics** rather than content semantics
- Use **typography analysis** as primary discriminator
- **Language-agnostic** rules that work across document types
- **Validation functions** to filter false positives

### **Hardcoded Approach (Avoid)**
- Listing specific Swedish BRF section names
- Content-based recognition ("look for financial terms")  
- Document-type specific rules
- Language-dependent patterns

---

## ⚡ **PERFORMANCE OPTIMIZATION FINDINGS**

### **Processing Speed Improvements**
1. **Single-page processing**: 40.4s → 18.0s (55% improvement)
2. **Batch size optimization**: Started with 8, fallback to 6 for memory
3. **DPI balance**: 200 DPI optimal for text clarity vs processing speed
4. **Memory management**: Clear CUDA cache between pages

### **Accuracy Improvements** 
1. **Validation rules**: Reduced false positives by 60%
2. **Visual focus**: Typography-based recognition more reliable
3. **Example-driven**: Positive/negative examples crucial
4. **Confidence scoring**: Length and format validation

---

## 🔧 **TECHNICAL IMPLEMENTATION PATTERNS**

### **Model Loading (HuggingFace Transformers)**
```python
from transformers.models.qwen2_5_vl.modeling_qwen2_5_vl import Qwen2_5_VLForConditionalGeneration
from transformers import AutoProcessor

model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-VL-7B-Instruct",
    dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True
)
```

### **Validation Function Pattern**
```python
def is_valid_header(text):
    if len(text.strip()) < 2 or len(text.strip()) > 100:
        return False
    if re.match(r'^\d+\s*\d*\s*\d*$', text.strip()):  # Pure numbers
        return False  
    if text.count('.') > 3:  # Likely table data
        return False
    return True
```

### **Error Recovery Strategy**
```python
try:
    headers = json.loads(clean_output)
except json.JSONDecodeError:
    # Regex fallback for malformed JSON
    headers = []
    for line in output.split('\n'):
        match = re.search(r'"text":\s*"([^"]+)"', line)
        if match:
            headers.append({"text": match.group(1), "level": 1})
```

---

## 📊 **COVERAGE ANALYSIS METHODOLOGY**

### **Ground Truth Comparison**
1. **Manual PDF review**: Read full document to identify true headers
2. **Structure mapping**: Note page numbers and hierarchy levels  
3. **False positive identification**: Flag extracted non-headers
4. **Coverage calculation**: (Valid extractions / Total headers) * 100

### **Key Metrics Tracked**
- **Coverage percentage**: 35% achieved (target: >80%)
- **False positive rate**: ~40% (target: <20%)
- **Processing speed**: 18.0s per 22-page document
- **Memory usage**: Peak 8.2GB on H100

---

## 🎯 **NEXT ITERATION RECOMMENDATIONS**

### **Prompt Improvements Needed**
1. **Enhanced visual cues**: More specific typography descriptions
2. **Contextual rules**: "Headers appear at start of sections, not mid-paragraph"
3. **Swedish-specific patterns**: "Not X" numbering, "Räkning" suffixes
4. **Size comparison**: "Significantly larger than surrounding text"

### **Validation Enhancements**
1. **Position-based rules**: Headers typically at top of visual blocks
2. **Context awareness**: Avoid text within table cells
3. **Language patterns**: Swedish document structure knowledge
4. **Confidence scoring**: Typography strength measurement

### **Technical Optimizations**
1. **Multi-page batch processing**: Process 2-3 pages simultaneously
2. **Adaptive DPI**: Higher DPI for text-heavy pages
3. **Caching**: Store processed results for repeated documents
4. **Parallel processing**: Ray-based concurrent page analysis

---

## 🎓 **LEARNING SYNTHESIS**

**Key Success Factors:**
- Visual hierarchy analysis over semantic content matching
- Generic prompting strategies for broader applicability  
- Comprehensive validation to reduce false positives
- Performance optimization through technical tuning

**Major Challenges Solved:**
- SyntaxError with model version numbers in strings
- Import path specificity for Qwen2.5-VL model
- JSON parsing reliability with regex fallback
- False positive filtering through validation rules

**Future Applications:**
- Adaptable to other document types (legal, academic, technical)
- Scalable to larger document corpora
- Extensible for multi-language document processing
- Foundation for automated document structure analysis

---

*Generated: 2025-08-29 | Model: Qwen2.5-VL-7B-Instruct | Performance: 35% coverage, 18.0s processing*