#!/usr/bin/env python3
"""
Prompt Sync System - Maintains JSON cache of DB prompts for fast retrieval
Ensures JSON always reflects latest coaching improvements
"""
import json
import psycopg2
import os
from typing import Dict, Any, Optional
from pathlib import Path
import time

class PromptSyncSystem:
    def __init__(self, db_url: str, json_path: str = "/tmp/zeldabot/pdf_docs/prompts/agent_prompts.json"):
        """
        Initialize prompt sync system
        
        Args:
            db_url: PostgreSQL connection string
            json_path: Path to JSON cache file
        """
        self.db_url = db_url
        self.json_path = json_path
        self.ensure_json_exists()
    
    def ensure_json_exists(self):
        """Create JSON file if it doesn't exist"""
        json_file = Path(self.json_path)
        if not json_file.exists():
            json_file.parent.mkdir(parents=True, exist_ok=True)
            json_file.write_text("{}")
            print(f"✅ Created prompt cache at {self.json_path}")
    
    def sync_from_db_to_json(self) -> Dict[str, Any]:
        """
        Pull all agent prompts from database and update JSON cache
        This is the main sync operation - DB is source of truth
        
        Returns:
            Dictionary of agent_id -> prompt data
        """
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Get all active agents with their prompts and schemas
            cursor.execute("""
                SELECT 
                    agent_id,
                    name,
                    specialization,
                    typical_sections,
                    typical_pages,
                    bounded_prompt,
                    output_schema,
                    confidence_threshold
                FROM agent_registry
                WHERE status = 'active'
                ORDER BY agent_id
            """)
            
            agents = {}
            for row in cursor.fetchall():
                agent_id = row[0]
                agents[agent_id] = {
                    "name": row[1],
                    "specialization": row[2],
                    "typical_sections": row[3],
                    "typical_pages": row[4],
                    "prompt": row[5],  # The actual prompt text
                    "output_schema": row[6],
                    "confidence_threshold": float(row[7]),
                    "last_synced": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            # Also create a section mapping for quick lookup
            section_to_agent = {}
            for agent_id, data in agents.items():
                for section in data.get("typical_sections", []):
                    if section not in section_to_agent:
                        section_to_agent[section] = []
                    section_to_agent[section].append(agent_id)
            
            # Save to JSON cache
            cache_data = {
                "agents": agents,
                "section_mapping": section_to_agent,
                "sync_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "agent_count": len(agents)
            }
            
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            conn.close()
            
            print(f"✅ Synced {len(agents)} agents from DB to JSON cache")
            print(f"   📁 Cache saved to: {self.json_path}")
            
            return cache_data
            
        except Exception as e:
            print(f"❌ Failed to sync from DB: {e}")
            return {}
    
    def load_prompts_from_json(self) -> Dict[str, Any]:
        """
        Load prompts from JSON cache (fast read for orchestrator)
        
        Returns:
            Dictionary with agents and section mappings
        """
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            print(f"⚠️ JSON cache not found, syncing from DB...")
            return self.sync_from_db_to_json()
        except json.JSONDecodeError:
            print(f"⚠️ JSON cache corrupted, resyncing from DB...")
            return self.sync_from_db_to_json()
    
    def update_prompt_after_coaching(self, agent_id: str, improved_prompt: str, 
                                    coaching_metadata: Optional[Dict] = None) -> bool:
        """
        Update both DB and JSON when coaching improves a prompt
        
        Args:
            agent_id: Agent to update
            improved_prompt: New improved prompt from coaching
            coaching_metadata: Optional metadata about the improvement
            
        Returns:
            True if update successful
        """
        try:
            # 1. Update database first (source of truth)
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE agent_registry
                SET bounded_prompt = %s,
                    updated_at = NOW()
                WHERE agent_id = %s
            """, (improved_prompt, agent_id))
            
            conn.commit()
            
            # 2. Store coaching history if table exists
            if coaching_metadata:
                try:
                    cursor.execute("""
                        INSERT INTO coaching_improvements
                        (agent_id, old_prompt, new_prompt, improvement_metadata, created_at)
                        VALUES (%s, 
                                (SELECT bounded_prompt FROM agent_registry WHERE agent_id = %s),
                                %s, %s, NOW())
                    """, (agent_id, agent_id, improved_prompt, json.dumps(coaching_metadata)))
                    conn.commit()
                except:
                    pass  # Table might not exist
            
            conn.close()
            
            # 3. Update JSON cache immediately
            cache_data = self.load_prompts_from_json()
            if agent_id in cache_data.get("agents", {}):
                cache_data["agents"][agent_id]["prompt"] = improved_prompt
                cache_data["agents"][agent_id]["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
                
                with open(self.json_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
                print(f"✅ Updated prompt for {agent_id} in both DB and JSON cache")
                return True
            else:
                # Agent not in cache, do full resync
                self.sync_from_db_to_json()
                return True
                
        except Exception as e:
            print(f"❌ Failed to update prompt: {e}")
            return False
    
    def get_prompt_for_section(self, section: str) -> Optional[str]:
        """
        Get the best prompt for a given section (from JSON cache)
        
        Args:
            section: Section name (e.g., "balance_sheet", "governance")
            
        Returns:
            Prompt text or None if not found
        """
        cache_data = self.load_prompts_from_json()
        
        # Check section mapping
        section_mapping = cache_data.get("section_mapping", {})
        agent_ids = section_mapping.get(section, [])
        
        if not agent_ids:
            # Try to find agent by ID match (e.g., "governance" -> "governance_agent")
            possible_id = f"{section}_agent"
            if possible_id in cache_data.get("agents", {}):
                agent_ids = [possible_id]
        
        if agent_ids:
            # Return prompt from first matching agent
            agent_id = agent_ids[0]
            agent_data = cache_data.get("agents", {}).get(agent_id, {})
            return agent_data.get("prompt")
        
        return None
    
    def get_all_prompts(self) -> Dict[str, str]:
        """
        Get all prompts as a simple dict (for backward compatibility)
        
        Returns:
            Dict of agent_id -> prompt text
        """
        cache_data = self.load_prompts_from_json()
        agents = cache_data.get("agents", {})
        
        return {
            agent_id: data.get("prompt", "")
            for agent_id, data in agents.items()
        }


# CLI for manual sync operations
if __name__ == "__main__":
    import sys
    
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL environment variable not set")
        sys.exit(1)
    
    sync = PromptSyncSystem(db_url)
    
    if len(sys.argv) > 1 and sys.argv[1] == "sync":
        print("🔄 Syncing prompts from database to JSON cache...")
        result = sync.sync_from_db_to_json()
        print(f"✅ Synced {result.get('agent_count', 0)} agents")
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        print("🧪 Testing prompt retrieval...")
        prompt = sync.get_prompt_for_section("governance")
        if prompt:
            print(f"✅ Found governance prompt: {prompt[:100]}...")
        else:
            print("❌ No governance prompt found")
    else:
        print("Usage: python prompt_sync.py [sync|test]")
        print("  sync - Pull all prompts from DB to JSON cache")
        print("  test - Test prompt retrieval")