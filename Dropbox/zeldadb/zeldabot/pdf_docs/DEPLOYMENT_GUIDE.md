# 🚀 Project Zelda H100 Årsredovisning Deployment Guide

Complete setup for processing your 200 selected BRF annual reports on H100 with PostgreSQL database.

## 📋 Prerequisites

- ✅ H100 server access: `ssh -i ~/.ssh/BrfGraphRag -p 26983 root@45.135.56.10`
- ✅ 200 selected PDFs from diversity sampler
- ✅ Training sample metadata CSV
- ✅ Ubuntu 20.04+ on H100

## 🎯 Step-by-Step Deployment

### 1️⃣ **Prepare Files on Mac**

```bash
# Generate H100 setup script
python zelda_h100_arsredovisning_pipeline.py --setup

# Transfer setup files to H100
scp -i ~/.ssh/BrfGraphRag -P 26983 setup_h100_arsredovisning.sh root@45.135.56.10:/root/
scp -i ~/.ssh/BrfGraphRag -P 26983 zelda_h100_arsredovisning_pipeline.py root@45.135.56.10:/root/
scp -i ~/.ssh/BrfGraphRag -P 26983 arsredovisning_training_sample_metadata.csv root@45.135.56.10:/root/
```

### 2️⃣ **Setup H100 Environment**

```bash
# Connect to H100
ssh -i ~/.ssh/BrfGraphRag -p 26983 root@45.135.56.10

# Run setup script
chmod +x setup_h100_arsredovisning.sh
./setup_h100_arsredovisning.sh

# Source new environment
source ~/.bashrc
source /opt/zelda/venv/bin/activate
```

### 3️⃣ **Transfer Training PDFs**

From your Mac, transfer the 200 selected PDFs:

```bash
# Create PDF list from CSV
python -c "
import pandas as pd
df = pd.read_csv('arsredovisning_training_sample_metadata.csv')
paths = df['file_path'].tolist()
with open('pdf_transfer_list.txt', 'w') as f:
    for path in paths:
        f.write(path + '\n')
"

# Transfer PDFs using file list
rsync -avP --files-from=pdf_transfer_list.txt -e "ssh -i ~/.ssh/BrfGraphRag -p 26983" / root@45.135.56.10:/data/zelda/pdfs/
```

### 4️⃣ **Initialize Database on H100**

```bash
# Initialize database schema
python zelda_h100_arsredovisning_pipeline.py --init-db

# Verify database
psql -U zelda_user -d zelda_arsredovisning -c "\dt"
```

### 5️⃣ **Ingest PDFs with Metadata**

```bash
# Ingest all 200 PDFs with diversity sample metadata
python zelda_h100_arsredovisning_pipeline.py --ingest /data/zelda/pdfs/

# Check ingestion status
python zelda_h100_arsredovisning_pipeline.py --stats
```

### 6️⃣ **Start Processing**

```bash
# Process with Titan (simulated for now)
python zelda_h100_arsredovisning_pipeline.py --process

# Monitor progress
python zelda_h100_arsredovisning_pipeline.py --dashboard
```

## 📊 Expected Results

### **Document Distribution:**
- **Financial Heavy**: 70 documents (high priority)
- **Comprehensive Report**: 52 documents 
- **Visual Summary**: 60 documents
- **Standard Report**: 18 documents

### **Success Rates (Simulated):**
- Visual Summary: ~95% success (simple docs)
- Standard Report: ~85% success
- Comprehensive Report: ~70% success  
- Financial Heavy: ~60% success (complex tables → Qwen)

### **Database Schema:**
- ✅ `arsredovisning_documents` - Main document table
- ✅ `arsredovisning_sections` - Financial sections
- ✅ `arsredovisning_financial_tables` - Table extractions
- ✅ `arsredovisning_brf_info` - Building/BRF metadata
- ✅ `arsredovisning_queue` - Processing queue
- ✅ `arsredovisning_qwen_candidates` - Failed docs for Qwen

## 🔧 Management Commands

```bash
# View processing statistics
python zelda_h100_arsredovisning_pipeline.py --stats

# Show detailed dashboard
python zelda_h100_arsredovisning_pipeline.py --dashboard

# Get Qwen candidates (failed extractions)
python zelda_h100_arsredovisning_pipeline.py --process-qwen

# Export successful extractions
python zelda_h100_arsredovisning_pipeline.py --export extracted_data.json

# Clean up PDF binaries (keep failed ones for Qwen)
python zelda_h100_arsredovisning_pipeline.py --cleanup
```

## 🗄️ Database Queries

### Check Processing Status
```sql
SELECT processing_status, COUNT(*) 
FROM arsredovisning_documents 
GROUP BY processing_status;
```

### View Successful Extractions
```sql
SELECT filename, brf_name, city, organization, 
       has_resultatrakning, has_balansrakning, has_kassaflode,
       extraction_confidence
FROM arsredovisning_documents 
WHERE processing_status = 'extracted';
```

### Get Qwen Candidates
```sql
SELECT ad.filename, ad.document_complexity, aqc.failure_type, aqc.priority
FROM arsredovisning_documents ad
JOIN arsredovisning_qwen_candidates aqc ON ad.id = aqc.document_id
WHERE ad.extraction_failed = TRUE
ORDER BY aqc.priority DESC;
```

## 📈 Integration Points

### **With Existing Titan System:**
Replace the simulation in `_extract_arsredovisning()` with your actual Swedish Table Extractor:

```python
# In ArsredovisningTitanProcessor._extract_arsredovisning()
from your_titan_system import SwedishTableExtractor

extractor = SwedishTableExtractor()
result = extractor.extract_brf_annual_report(pdf_path)
```

### **With Qwen Integration:**
Failed documents are stored with PDF binaries for Qwen processing:

```python
# Get failed documents
candidates = db_manager.get_qwen_candidates(limit=50)
for doc in candidates:
    pdf_binary = doc['pdf_binary']  # Ready for Qwen
    # Process with Qwen vision model
```

## 🚨 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -U zelda_user -d zelda_arsredovisning -c "SELECT version();"
```

### PDF Transfer Issues
```bash
# Check transferred files
ls -la /data/zelda/pdfs/ | wc -l  # Should show 200+ files

# Check file permissions
sudo chown -R $(whoami):$(whoami) /data/zelda/
```

### Processing Issues
```bash
# Check logs
tail -f /data/zelda/logs/processing.log

# Verify Python environment
source /opt/zelda/venv/bin/activate
pip list | grep -E "(psycopg2|pandas|pymupdf)"
```

## 🎉 Success Metrics

**🎯 Target Outcomes:**
- ✅ 200 PDFs ingested with complete metadata
- ✅ ~160-170 successful extractions (80-85% success rate)
- ✅ ~30-40 documents marked for Qwen processing  
- ✅ Complete financial data extraction from BRF reports
- ✅ Structured database ready for analysis/training

**📊 Quality Indicators:**
- High extraction confidence (>0.8) on successful docs
- Clear failure categorization for Qwen prioritization
- Complete preservation of PDF binaries for failed cases
- Searchable structured data for successful extractions

Ready to process your Swedish BRF paradise! 🇸🇪💖🚀