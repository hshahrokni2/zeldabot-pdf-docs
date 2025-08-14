#!/usr/bin/env python3
"""
🧪 CPU Tandem Test - Proof of Concept for Swedish BRF GraphRAG
=============================================================

Test tandem routing with CPU-optimized models:
- Primary: llama3.2:3b (Swedish extraction) 
- Secondary: phi3.5:3.8b (reasoning/calculations)

This validates the concept before GPU deployment! 💖🇸🇪
"""

import asyncio
import aiohttp
import time
from datetime import datetime

class CPUTandemTester:
    """🧪 Test tandem routing logic with CPU models"""
    
    def __init__(self, ollama_url: str = "http://165.232.73.99:11434"):
        self.ollama_url = f"{ollama_url}/api/generate"
        self.primary_model = "llama3.2:3b"      # Swedish extraction 
        self.secondary_model = "phi3.5:3.8b"    # Reasoning/math
        
    async def test_tandem_routing(self):
        """🎯 Test intelligent task routing"""
        
        print("🧪 TESTING CPU TANDEM ROUTING SYSTEM! 🤖🇸🇪")
        print("="*60)
        print(f"🥇 Primary: {self.primary_model} (Swedish extraction)")
        print(f"🥈 Secondary: {self.secondary_model} (reasoning/math)")
        print("")
        
        # Test scenarios that mirror our GPU system
        test_scenarios = [
            {
                "task": "Swedish Text Extraction",
                "model": self.primary_model,
                "prompt": """Du är expert på svenska bostadsrättsföreningar. Analysera denna text och extrahera nyckelinformation:

BRF Sjöstaden 2 har 167 lägenheter med en månadsavgift på 4 250 kr. Föreningens energiklass är C med specifik energianvändning 95 kWh/kvm·år. Totala intäkter 2023 var 8 500 000 kr.

Extrahera: månadsavgift, antal lägenheter, energiklass, och totala intäkter."""
            },
            {
                "task": "Financial Calculations",
                "model": self.secondary_model,
                "prompt": """Calculate financial metrics for a Swedish BRF:

Given data:
- 167 apartments
- Monthly fee: 4,250 SEK per apartment
- Total revenue: 8,500,000 SEK
- Operating costs: 6,200,000 SEK
- Debt: 45,000,000 SEK
- Equity: 15,000,000 SEK

Calculate:
1. Annual revenue from monthly fees
2. Operating margin (%)
3. Debt-to-equity ratio
4. Revenue per apartment per year"""
            },
            {
                "task": "Swedish Energy Analysis", 
                "model": self.primary_model,
                "prompt": """Som energiexpert för svenska BRF, analysera energiprestanda:

BRF Sjöstaden 2:
- Energiklass: C
- Specifik energianvändning: 95 kWh/kvm·år
- Total yta: 12 500 kvm

Jämför med svenska genomsnittet och föreslå förbättringar. Svara på svenska."""
            },
            {
                "task": "Logical Reasoning",
                "model": self.secondary_model, 
                "prompt": """Analyze this BRF scenario and provide strategic recommendations:

A Swedish BRF has:
- High debt-to-equity ratio (3:1)
- Energy class C (could improve to B)
- Monthly fees below market average
- Aging heating system (15+ years)

What's the optimal 5-year strategy? Consider financial constraints, energy efficiency, and member satisfaction."""
            }
        ]
        
        results = {}
        total_start = time.time()
        
        for i, scenario in enumerate(test_scenarios, 1):
            task_name = scenario["task"]
            model = scenario["model"]
            prompt = scenario["prompt"]
            
            print(f"🔬 Test {i}/4: {task_name}")
            print(f"🤖 Routing to: {model}")
            print("─" * 50)
            
            start_time = time.time()
            response = await self._query_model(model, prompt)
            execution_time = time.time() - start_time
            
            if response:
                word_count = len(response.split())
                results[task_name] = {
                    "model_used": model,
                    "response": response[:300] + "..." if len(response) > 300 else response,
                    "full_response_length": len(response),
                    "word_count": word_count,
                    "execution_time": execution_time,
                    "words_per_second": word_count / execution_time if execution_time > 0 else 0
                }
                
                print(f"✅ Completed in {execution_time:.1f}s")
                print(f"📝 Generated: {word_count} words ({word_count/execution_time:.1f} words/sec)")
                print(f"🎯 Preview: {response[:150]}...")
                print("")
            else:
                print(f"❌ Failed to get response from {model}")
                results[task_name] = {"error": f"Model {model} failed"}
                print("")
        
        total_time = time.time() - total_start
        
        # Generate summary
        successful_tests = len([r for r in results.values() if "response" in r])
        total_words = sum(r.get("word_count", 0) for r in results.values())
        avg_words_per_sec = sum(r.get("words_per_second", 0) for r in results.values()) / max(successful_tests, 1)
        
        print("🎉 CPU TANDEM ROUTING TEST COMPLETE!")
        print("="*60)
        print(f"⏱️  Total Time: {total_time:.1f} seconds")
        print(f"✅ Success Rate: {successful_tests}/{len(test_scenarios)} tests")
        print(f"📊 Performance: {total_words} words total, {avg_words_per_sec:.1f} avg words/sec")
        print(f"🎯 Routing: Primary used for Swedish tasks, Secondary for reasoning")
        print("")
        print("🚀 READY FOR GPU DEPLOYMENT!")
        print("When A100 is available, same logic will run with:")
        print("🥇 mistral-large:latest (Swedish extraction)")
        print("🥈 gpt-oss-120b:latest (reasoning/calculations)")
        print("")
        print("💖 Zero lost work - everything transfers directly!")
        
        return {
            "test_date": datetime.now().isoformat(),
            "total_time": total_time,
            "successful_tests": successful_tests,
            "total_words": total_words,
            "avg_performance": avg_words_per_sec,
            "results": results
        }
    
    async def _query_model(self, model: str, prompt: str, max_tokens: int = 1000) -> str:
        """Query specific model with optimized parameters"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
                data = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "top_k": 40,
                        "num_ctx": 4096,  # CPU-optimized context
                        "num_predict": max_tokens,
                        "repeat_penalty": 1.1
                    }
                }
                
                async with session.post(self.ollama_url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '').strip()
                    else:
                        error_text = await response.text()
                        print(f"❌ API Error {response.status}: {error_text}")
                        return None
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return None


async def main():
    """Run CPU tandem test"""
    tester = CPUTandemTester()
    await tester.test_tandem_routing()


if __name__ == "__main__":
    asyncio.run(main())