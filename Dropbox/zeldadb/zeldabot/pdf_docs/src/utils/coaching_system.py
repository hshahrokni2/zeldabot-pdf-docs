#!/usr/bin/env python3
"""
Coaching System - Persistent learning with append-only NDJSON memory
Applies coaching deltas at runtime without modifying base templates
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class CoachingSystem:
    def __init__(self, memory_path: str = "coaching/memory.ndjson"):
        self.memory_path = Path(memory_path)
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.deltas = self._load_memory()
    
    def _load_memory(self) -> List[Dict[str, Any]]:
        """Load coaching deltas from NDJSON file"""
        deltas = []
        if self.memory_path.exists():
            try:
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            deltas.append(json.loads(line))
            except Exception as e:
                print(f"⚠️  Error loading coaching memory: {e}")
        return deltas
    
    def _save_delta(self, delta: Dict[str, Any]):
        """Append delta to NDJSON memory file"""
        try:
            with open(self.memory_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(delta, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"❌ Error saving coaching delta: {e}")
    
    def _delta_hash(self, section: str, pattern: str, action: str) -> str:
        """Generate hash for delta deduplication"""
        combined = f"{section}|{pattern}|{action}"
        return hashlib.md5(combined.encode()).hexdigest()[:8]
    
    def apply_coaching_deltas(self, results: Dict[str, Any], failures: List[str]) -> List[Dict[str, Any]]:
        """Generate coaching deltas based on extraction failures"""
        new_deltas = []
        
        for failure in failures:
            # Parse failure message to determine coaching action
            if "Assets:" in failure:
                delta = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "section": "balance_sheet",
                    "failure_pattern": "assets_extraction",
                    "coaching_action": "emphasize_total_assets_anchor",
                    "delta_hash": self._delta_hash("balance_sheet", "assets_extraction", "emphasize_total_assets_anchor"),
                    "prompt_addition": "\\nSärskild uppmärksamhet på: SUMMA TILLGÅNGAR och liknande rubriker för total assets.",
                    "original_failure": failure
                }
            elif "Total debt:" in failure:
                delta = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "section": "balance_sheet", 
                    "failure_pattern": "debt_extraction",
                    "coaching_action": "emphasize_debt_terms",
                    "delta_hash": self._delta_hash("balance_sheet", "debt_extraction", "emphasize_debt_terms"),
                    "prompt_addition": "\\nSärskild uppmärksamhet på: SKULDER, långfristiga skulder, skulder till kreditinstitut.",
                    "original_failure": failure
                }
            elif "Cash:" in failure:
                delta = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "section": "cash_flow",
                    "failure_pattern": "cash_closing_extraction", 
                    "coaching_action": "emphasize_cash_terms",
                    "delta_hash": self._delta_hash("cash_flow", "cash_closing_extraction", "emphasize_cash_terms"),
                    "prompt_addition": "\\nSärskild uppmärksamhet på: utgående likvida medel, kassa och bank vid årets slut.",
                    "original_failure": failure
                }
            elif "Org no:" in failure:
                delta = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "section": "governance",
                    "failure_pattern": "org_number_extraction",
                    "coaching_action": "emphasize_org_number_formats",
                    "delta_hash": self._delta_hash("governance", "org_number_extraction", "emphasize_org_number_formats"), 
                    "prompt_addition": "\\nSärskild uppmärksamhet på: organisationsnummer med format XXXXXX-XXXX.",
                    "original_failure": failure
                }
            else:
                # Generic coaching delta
                delta = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "section": "general",
                    "failure_pattern": "generic_failure",
                    "coaching_action": "general_improvement",
                    "delta_hash": self._delta_hash("general", "generic_failure", "general_improvement"),
                    "prompt_addition": "\\nÖka noggrannheten i extraheringen av finansiella värden.",
                    "original_failure": failure
                }
            
            # Check for duplicates
            if not any(d.get("delta_hash") == delta["delta_hash"] for d in self.deltas):
                new_deltas.append(delta)
                self._save_delta(delta)
                self.deltas.append(delta)
                print(f"🧠 New coaching delta created: {delta['coaching_action']}")
            else:
                print(f"🔄 Coaching delta already exists: {delta['coaching_action']}")
        
        return new_deltas
    
    def load_prompt_with_coaching(self, section: str, base_prompt: str) -> str:
        """Apply coaching deltas to base prompt at runtime"""
        enhanced_prompt = base_prompt
        
        # Apply relevant deltas for this section
        for delta in self.deltas:
            if delta.get("section") == section or delta.get("section") == "general":
                if "prompt_addition" in delta:
                    enhanced_prompt += delta["prompt_addition"]
        
        return enhanced_prompt
    
    def get_coaching_stats(self) -> Dict[str, Any]:
        """Get statistics about coaching memory"""
        sections = {}
        for delta in self.deltas:
            section = delta.get("section", "unknown")
            if section not in sections:
                sections[section] = 0
            sections[section] += 1
        
        return {
            "total_deltas": len(self.deltas),
            "sections": sections,
            "memory_file_size": self.memory_path.stat().st_size if self.memory_path.exists() else 0
        }