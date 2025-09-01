"""
Proof-of-work receipt logging with GPU samples and HTTP status tracking.
"""
import json
import time
import hashlib
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class ReceiptLogger:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.artifacts_dir = Path("artifacts")
        self.artifacts_dir.mkdir(exist_ok=True)
        self.calls_log_path = self.artifacts_dir / "calls_log.ndjson"
    
    def get_gpu_sample(self) -> Optional[str]:
        """Get GPU status sample for proof-of-work."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,temperature.gpu,utilization.gpu", 
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if lines:
                    # Parse first GPU: name, mem_used, mem_total, temp, util
                    parts = [p.strip() for p in lines[0].split(',')]
                    if len(parts) >= 5:
                        name, mem_used, mem_total, temp, util = parts[:5]
                        return f"{name}, {mem_used}/{mem_total} MiB, {temp}C, util {util}%"
            return None
        except Exception:
            return None
    
    def compute_pdf_hash(self, pdf_path: str) -> str:
        """Compute SHA256 hash of PDF for provenance."""
        try:
            hasher = hashlib.sha256()
            with open(pdf_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return "unknown"
    
    def log_model_call(
        self, 
        section: str,
        model: str,
        transport: str,
        http_status: int,
        json_ok: bool,
        schema_ok: bool,
        latency_ms: int,
        pages_used: List[int],
        pdf_path: str,
        twin_pair_id: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ):
        """Log model call with full proof-of-work receipt."""
        
        receipt = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "run_id": self.run_id,
            "section": section,
            "model": model,
            "transport": transport,
            "http_status": http_status,
            "json_ok": json_ok,
            "schema_ok": schema_ok,
            "latency_ms": latency_ms,
            "pages_used": pages_used,
            "pdf_sha256": self.compute_pdf_hash(pdf_path),
            "gpu_sample": self.get_gpu_sample()
        }
        
        if twin_pair_id:
            receipt["twin_pair_id"] = twin_pair_id
        
        if additional_metadata:
            receipt.update(additional_metadata)
        
        # Write to NDJSON log
        with open(self.calls_log_path, 'a') as f:
            f.write(json.dumps(receipt) + '\n')
    
    def log_coaching_delta(
        self,
        section: str,
        before_prompt: str,
        delta_prompt: str,
        after_prompt: str,
        reason: str
    ):
        """Log coaching delta to both NDJSON and prepare for DB insert."""
        coaching_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "run_id": self.run_id,
            "type": "coaching_delta",
            "section": section,
            "before_prompt": before_prompt,
            "delta_prompt": delta_prompt,
            "after_prompt": after_prompt,
            "reason": reason
        }
        
        # Write to coaching memory NDJSON
        coaching_dir = self.artifacts_dir / "coaching"
        coaching_dir.mkdir(exist_ok=True)
        coaching_log = coaching_dir / "memory.ndjson"
        
        with open(coaching_log, 'a') as f:
            f.write(json.dumps(coaching_entry) + '\n')
        
        return coaching_entry
    
    def get_run_summary(self) -> Dict[str, Any]:
        """Generate run summary from logged receipts."""
        if not self.calls_log_path.exists():
            return {"error": "No receipts logged"}
        
        receipts = []
        with open(self.calls_log_path, 'r') as f:
            for line in f:
                try:
                    receipts.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        
        # Filter for this run_id
        run_receipts = [r for r in receipts if r.get("run_id") == self.run_id and r.get("type") != "coaching_delta"]
        
        if not run_receipts:
            return {"error": f"No receipts found for run_id {self.run_id}"}
        
        summary = {
            "run_id": self.run_id,
            "total_calls": len(run_receipts),
            "successful_calls": len([r for r in run_receipts if r.get("http_status") == 200]),
            "json_success_rate": len([r for r in run_receipts if r.get("json_ok")]) / len(run_receipts),
            "schema_success_rate": len([r for r in run_receipts if r.get("schema_ok")]) / len(run_receipts),
            "total_latency_ms": sum(r.get("latency_ms", 0) for r in run_receipts),
            "sections_attempted": list(set(r.get("section") for r in run_receipts if r.get("section"))),
            "models_used": list(set(r.get("model") for r in run_receipts if r.get("model"))),
            "gpu_samples": [r.get("gpu_sample") for r in run_receipts if r.get("gpu_sample")]
        }
        
        return summary