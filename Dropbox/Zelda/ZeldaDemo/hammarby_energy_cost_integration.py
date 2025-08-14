#!/usr/bin/env python3
"""
Hammarby Sjöstad Energy & Cost Integration Analysis
Integrates EPC energy data and cost analysis for Hammarby Sjöstad prototype.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
import re
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HammarbyEnergyAnalyzer:
    """Main class for integrating EPC energy data with cost analysis."""
    
    def __init__(self, epc_json_path: str, cost_excel_path: str, building_data_path: str):
        self.epc_json_path = epc_json_path
        self.cost_excel_path = cost_excel_path
        self.building_data_path = building_data_path
        self.swedish_avg_energy = 159  # kWh/m² Swedish average
        
        # Initialize data containers
        self.epc_data = None
        self.cost_data = None
        self.building_data = None
        self.integrated_data = []
        
    def load_epc_data(self) -> List[Dict]:
        """Parse EPC JSON and extract energy metrics."""
        logger.info("Loading EPC energy performance data...")
        
        try:
            with open(self.epc_json_path, 'r', encoding='utf-8') as f:
                epc_raw = json.load(f)
            
            epc_processed = []
            for entry in epc_raw:
                # Extract key energy metrics
                json_data = entry.get('json_data', {})
                
                epc_record = {
                    'epc_id': entry.get('epc_id'),
                    'year': entry.get('year'),
                    'property_owner': entry.get('property_owner'),
                    'property_name': entry.get('property_name'),
                    'house_numbers': entry.get('house_numbers'),
                    'main_street_address': json_data.get('mainStreetAddress'),
                    'energy_performance_kwh_m2': json_data.get('energyPerformance_kWh_per_m2'),
                    'energy_class': json_data.get('energyClass'),
                    'construction_year': json_data.get('constructionYear'),
                    'heated_area_m2': json_data.get('heatedArea_m2'),
                    'number_of_apartments': json_data.get('numberOfApartments'),
                    'heating_systems': json_data.get('heatingSystems', []),
                    'energy_consumption_kwh': json_data.get('energyConsumption_kWh'),
                    'specific_energy_use_kwh_m2': json_data.get('specificEnergyUse_kWh_per_m2'),
                    'measurement_period': f"{json_data.get('measurementFrom', '')} to {json_data.get('measurementTo', '')}",
                    'has_solar': json_data.get('hasPv', False) or json_data.get('hasSolarHeat', False),
                    'confidence_score': self._calculate_epc_confidence(json_data)
                }
                
                # Calculate energy efficiency vs Swedish average
                if epc_record['energy_performance_kwh_m2']:
                    epc_record['efficiency_vs_swedish_avg'] = (
                        epc_record['energy_performance_kwh_m2'] / self.swedish_avg_energy
                    )
                    epc_record['efficiency_rating'] = self._get_efficiency_rating(
                        epc_record['efficiency_vs_swedish_avg']
                    )
                
                epc_processed.append(epc_record)
            
            logger.info(f"Processed {len(epc_processed)} EPC records")
            self.epc_data = epc_processed
            return epc_processed
            
        except Exception as e:
            logger.error(f"Error loading EPC data: {e}")
            raise
    
    def load_cost_data(self) -> pd.DataFrame:
        """Parse Excel cost data from 'Raw data' sheet."""
        logger.info("Loading cost data from Excel...")
        
        try:
            # Read the Excel file, specifically the 'Raw data' sheet
            cost_df = pd.read_excel(self.cost_excel_path, sheet_name='Raw data')
            
            logger.info(f"Loaded cost data with {len(cost_df)} entries")
            logger.info(f"Cost data columns: {list(cost_df.columns)}")
            
            # Process and categorize cost data
            cost_df['cost_category'] = cost_df.apply(self._categorize_cost, axis=1)
            cost_df['confidence_score'] = cost_df.apply(self._calculate_cost_confidence, axis=1)
            
            self.cost_data = cost_df
            return cost_df
            
        except Exception as e:
            logger.error(f"Error loading cost data: {e}")
            raise
    
    def load_building_data(self) -> Dict:
        """Load existing building database data."""
        logger.info("Loading building database data...")
        
        try:
            with open(self.building_data_path, 'r', encoding='utf-8') as f:
                building_data = json.load(f)
            
            logger.info(f"Loaded data for {building_data['metadata']['building_count']} buildings")
            self.building_data = building_data
            return building_data
            
        except Exception as e:
            logger.error(f"Error loading building data: {e}")
            raise
    
    def merge_data_sources(self) -> List[Dict]:
        """Merge EPC, cost, and building data by matching property names."""
        logger.info("Merging data sources...")
        
        if not all([self.epc_data, self.cost_data is not None, self.building_data]):
            raise ValueError("All data sources must be loaded before merging")
        
        integrated_buildings = []
        
        for building in self.building_data['buildings']:
            brf_name = building['brf_name']
            
            # Find matching EPC data
            epc_matches = self._find_epc_matches(brf_name, building)
            
            # Find matching cost data
            cost_matches = self._find_cost_matches(brf_name, building)
            
            # Create integrated record
            integrated_record = self._create_integrated_record(
                building, epc_matches, cost_matches
            )
            
            integrated_buildings.append(integrated_record)
        
        logger.info(f"Created {len(integrated_buildings)} integrated building records")
        self.integrated_data = integrated_buildings
        return integrated_buildings
    
    def calculate_key_metrics(self) -> List[Dict]:
        """Calculate key performance and cost metrics."""
        logger.info("Calculating key metrics...")
        
        for building in self.integrated_data:
            # Energy efficiency metrics
            if building.get('energy_performance_kwh_m2'):
                building['energy_metrics'] = {
                    'efficiency_vs_swedish_avg': building['energy_performance_kwh_m2'] / self.swedish_avg_energy,
                    'efficiency_rating': self._get_efficiency_rating(
                        building['energy_performance_kwh_m2'] / self.swedish_avg_energy
                    ),
                    'annual_energy_cost_estimate': self._estimate_annual_energy_cost(building),
                    'carbon_intensity_estimate': self._estimate_carbon_intensity(building)
                }
            
            # Cost breakdown analysis
            if building.get('cost_breakdown'):
                building['cost_metrics'] = self._calculate_cost_metrics(building)
            
            # Bang-for-buck ratios (using placeholders until survey data)
            building['bang_for_buck'] = self._calculate_bang_for_buck(building)
            
            # Overall performance score
            building['performance_score'] = self._calculate_performance_score(building)
        
        return self.integrated_data
    
    def create_unified_dataset(self) -> Dict:
        """Create final unified dataset with confidence scores."""
        logger.info("Creating unified dataset...")
        
        unified_dataset = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'data_sources': {
                    'epc_data': self.epc_json_path,
                    'cost_data': self.cost_excel_path,
                    'building_data': self.building_data_path
                },
                'swedish_energy_benchmark': self.swedish_avg_energy,
                'total_buildings': len(self.integrated_data)
            },
            'statistics': self._calculate_dataset_statistics(),
            'buildings': self.integrated_data
        }
        
        return unified_dataset
    
    def export_results(self, output_path: str) -> str:
        """Export the enhanced building dataset."""
        unified_data = self.create_unified_dataset()
        
        # Convert numpy types to native Python types for JSON serialization
        unified_data = self._convert_numpy_types(unified_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(unified_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported enhanced dataset to {output_path}")
        return output_path
    
    # Helper methods
    def _calculate_epc_confidence(self, json_data: Dict) -> float:
        """Calculate confidence score for EPC data quality."""
        score = 0.0
        
        # Has full data
        if json_data.get('hasFullData'):
            score += 0.3
        
        # Has energy performance data
        if json_data.get('energyPerformance_kWh_per_m2'):
            score += 0.3
        
        # Has measurement period
        if json_data.get('measurementFrom') and json_data.get('measurementTo'):
            score += 0.2
        
        # Has building details
        if json_data.get('heatedArea_m2') and json_data.get('numberOfApartments'):
            score += 0.2
        
        return round(score, 2)
    
    def _calculate_cost_confidence(self, row) -> float:
        """Calculate confidence score for cost data quality."""
        score = 0.0
        
        # Check for non-null values in key columns
        key_columns = ['value', 'type', 'property']
        for col in key_columns:
            if col in row and pd.notna(row[col]):
                score += 0.33
        
        return round(min(score, 1.0), 2)
    
    def _categorize_cost(self, row) -> str:
        """Categorize cost entries into standard categories."""
        cost_type = str(row.get('type', '')).lower()
        
        # Categorize based on type field
        if any(keyword in cost_type for keyword in ['electric', 'el', 'kraft']):
            return 'electricity'
        elif any(keyword in cost_type for keyword in ['heat', 'värme', 'fjärr']):
            return 'heating'
        elif any(keyword in cost_type for keyword in ['water', 'vatten']):
            return 'water'
        elif any(keyword in cost_type for keyword in ['clean', 'reng', 'städ']):
            return 'cleaning'
        elif any(keyword in cost_type for keyword in ['maintenance', 'underhåll']):
            return 'maintenance'
        elif any(keyword in cost_type for keyword in ['admin', 'förvaltning']):
            return 'administration'
        else:
            return 'other'
    
    def _get_efficiency_rating(self, ratio: float) -> str:
        """Convert efficiency ratio to rating."""
        if ratio <= 0.7:
            return "Excellent"
        elif ratio <= 0.9:
            return "Good"
        elif ratio <= 1.1:
            return "Average"
        elif ratio <= 1.3:
            return "Below Average"
        else:
            return "Poor"
    
    def _find_epc_matches(self, brf_name: str, building: Dict) -> List[Dict]:
        """Find EPC records matching a building."""
        matches = []
        
        for epc_record in self.epc_data:
            # Match by property owner name similarity
            if self._is_name_match(brf_name, epc_record.get('property_owner', '')):
                matches.append(epc_record)
        
        return matches
    
    def _find_cost_matches(self, brf_name: str, building: Dict) -> List[Dict]:
        """Find cost records matching a building."""
        matches = []
        
        if self.cost_data is not None:
            for _, row in self.cost_data.iterrows():
                property_name = str(row.get('property', '')).lower()
                brf_name_clean = brf_name.lower()
                
                # Simple name matching - can be enhanced
                if self._is_name_match(brf_name, property_name):
                    matches.append({
                        'neighborhood': row.get('neighborhood'),
                        'property': row.get('property'),
                        'type': row.get('type'),
                        'datetime_utc': row.get('datetime_utc'),
                        'value': row.get('value'),
                        'cost_category': row.get('cost_category'),
                        'confidence_score': row.get('confidence_score')
                    })
        
        return matches
    
    def _is_name_match(self, name1: str, name2: str) -> bool:
        """Check if two property names are likely the same."""
        # Simple fuzzy matching - can be enhanced
        name1_clean = re.sub(r'[^\w\s]', '', name1.lower())
        name2_clean = re.sub(r'[^\w\s]', '', name2.lower())
        
        # Check for common words
        words1 = set(name1_clean.split())
        words2 = set(name2_clean.split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        # Simple Jaccard similarity
        similarity = len(intersection) / len(union) if union else 0
        return similarity > 0.3
    
    def _create_integrated_record(self, building: Dict, epc_matches: List[Dict], 
                                 cost_matches: List[Dict]) -> Dict:
        """Create an integrated building record."""
        integrated = building.copy()
        
        # Add EPC data if available
        if epc_matches:
            best_epc = max(epc_matches, key=lambda x: x.get('confidence_score', 0))
            integrated.update({
                'energy_performance_kwh_m2': best_epc.get('energy_performance_kwh_m2'),
                'energy_class': best_epc.get('energy_class'),
                'construction_year': best_epc.get('construction_year'),
                'heated_area_m2': best_epc.get('heated_area_m2'),
                'efficiency_vs_swedish_avg': best_epc.get('efficiency_vs_swedish_avg'),
                'efficiency_rating': best_epc.get('efficiency_rating'),
                'epc_confidence': best_epc.get('confidence_score'),
                'epc_data_source': f"EPC ID: {best_epc.get('epc_id')}"
            })
        
        # Add cost data if available
        if cost_matches:
            integrated['cost_breakdown'] = self._aggregate_cost_data(cost_matches)
            integrated['cost_confidence'] = np.mean([
                match.get('confidence_score', 0) for match in cost_matches
            ])
        
        return integrated
    
    def _aggregate_cost_data(self, cost_matches: List[Dict]) -> Dict:
        """Aggregate cost data by category."""
        aggregated = {}
        total = 0
        
        for match in cost_matches:
            category = match.get('cost_category', 'other')
            value = match.get('value', 0)
            
            if pd.notna(value) and isinstance(value, (int, float)):
                aggregated[category] = aggregated.get(category, 0) + float(value)
                total += float(value)
        
        aggregated['total'] = total
        return aggregated
    
    def _estimate_annual_energy_cost(self, building: Dict) -> Optional[float]:
        """Estimate annual energy cost based on performance and area."""
        if not all([
            building.get('energy_performance_kwh_m2'),
            building.get('heated_area_m2')
        ]):
            return None
        
        # Swedish energy price estimate (SEK/kWh)
        energy_price_sek_kwh = 1.2
        
        annual_consumption = (
            building['energy_performance_kwh_m2'] * building['heated_area_m2']
        )
        
        return annual_consumption * energy_price_sek_kwh
    
    def _estimate_carbon_intensity(self, building: Dict) -> Optional[float]:
        """Estimate carbon intensity based on heating system and consumption."""
        if not building.get('energy_performance_kwh_m2'):
            return None
        
        # Swedish electricity grid carbon intensity: ~50g CO2/kWh
        # District heating: ~80g CO2/kWh
        carbon_factor = 0.065  # kg CO2/kWh average
        
        return building['energy_performance_kwh_m2'] * carbon_factor
    
    def _calculate_cost_metrics(self, building: Dict) -> Dict:
        """Calculate detailed cost metrics."""
        cost_breakdown = building.get('cost_breakdown', {})
        
        metrics = {}
        
        # Cost per square meter if area is known
        if building.get('heated_area_m2'):
            metrics['cost_per_m2'] = {
                category: cost / building['heated_area_m2']
                for category, cost in cost_breakdown.items()
                if isinstance(cost, (int, float))
            }
        
        # Cost ratios
        total_cost = cost_breakdown.get('total', 0)
        if total_cost > 0:
            metrics['cost_ratios'] = {
                category: cost / total_cost
                for category, cost in cost_breakdown.items()
                if isinstance(cost, (int, float)) and category != 'total'
            }
        
        return metrics
    
    def _calculate_bang_for_buck(self, building: Dict) -> Dict:
        """Calculate bang-for-buck ratios using placeholder satisfaction scores."""
        # Placeholder satisfaction scores (will be replaced with survey data)
        satisfaction_placeholder = {
            'overall': 7.5,  # out of 10
            'energy_efficiency': 7.0,
            'maintenance_quality': 7.2,
            'cost_value': 6.8
        }
        
        bang_for_buck = {}
        
        # Overall bang-for-buck
        monthly_fee = building.get('economy', {}).get('monthly_fee', 0)
        if monthly_fee > 0:
            bang_for_buck['overall'] = satisfaction_placeholder['overall'] / (monthly_fee / 1000)
        
        # Energy efficiency bang-for-buck
        energy_costs = building.get('economy', {}).get('energy_costs', 0)
        if energy_costs > 0:
            bang_for_buck['energy_efficiency'] = (
                satisfaction_placeholder['energy_efficiency'] / (energy_costs / 10000)
            )
        
        return bang_for_buck
    
    def _calculate_performance_score(self, building: Dict) -> float:
        """Calculate overall performance score (0-100)."""
        score = 0.0
        weight_sum = 0.0
        
        # Energy efficiency (30% weight)
        if building.get('efficiency_vs_swedish_avg'):
            efficiency_score = max(0, (2 - building['efficiency_vs_swedish_avg']) * 50)
            score += efficiency_score * 0.3
            weight_sum += 0.3
        
        # Cost efficiency (25% weight)
        bang_for_buck = building.get('bang_for_buck', {})
        if bang_for_buck.get('overall'):
            cost_score = min(100, bang_for_buck['overall'] * 10)
            score += cost_score * 0.25
            weight_sum += 0.25
        
        # Building quality indicators (25% weight)
        maintenance_fund_ratio = 0
        economy = building.get('economy', {})
        if economy.get('maintenance_fund') and economy.get('total_income'):
            maintenance_fund_ratio = economy['maintenance_fund'] / economy['total_income']
            quality_score = min(100, maintenance_fund_ratio * 200)
            score += quality_score * 0.25
            weight_sum += 0.25
        
        # Data completeness (20% weight)
        completeness_score = (
            (1 if building.get('energy_performance_kwh_m2') else 0) +
            (1 if building.get('cost_breakdown') else 0) +
            (1 if building.get('economy') else 0)
        ) / 3 * 100
        score += completeness_score * 0.2
        weight_sum += 0.2
        
        return round(score / weight_sum if weight_sum > 0 else 0, 1)
    
    def _calculate_dataset_statistics(self) -> Dict:
        """Calculate summary statistics for the dataset."""
        if not self.integrated_data:
            return {}
        
        energy_performances = [
            b.get('energy_performance_kwh_m2') for b in self.integrated_data
            if b.get('energy_performance_kwh_m2')
        ]
        
        performance_scores = [
            b.get('performance_score') for b in self.integrated_data
            if b.get('performance_score')
        ]
        
        stats = {
            'energy_performance': {
                'avg_kwh_per_m2': np.mean(energy_performances) if energy_performances else None,
                'min_kwh_per_m2': np.min(energy_performances) if energy_performances else None,
                'max_kwh_per_m2': np.max(energy_performances) if energy_performances else None,
                'buildings_with_epc_data': len(energy_performances)
            },
            'performance_scores': {
                'avg_score': np.mean(performance_scores) if performance_scores else None,
                'min_score': np.min(performance_scores) if performance_scores else None,
                'max_score': np.max(performance_scores) if performance_scores else None
            },
            'data_quality': {
                'buildings_with_energy_data': len(energy_performances),
                'buildings_with_cost_data': len([
                    b for b in self.integrated_data if b.get('cost_breakdown')
                ]),
                'avg_confidence_epc': np.mean([
                    b.get('epc_confidence', 0) for b in self.integrated_data
                ]),
                'avg_confidence_cost': np.mean([
                    b.get('cost_confidence', 0) for b in self.integrated_data
                ])
            }
        }
        
        return stats
    
    def _convert_numpy_types(self, obj):
        """Recursively convert numpy types to native Python types."""
        if isinstance(obj, dict):
            return {k: self._convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj


def main():
    """Main execution function."""
    # File paths
    epc_json_path = "/Users/hosseins/Dropbox/Zelda/ZeldaDemo/EnergyPerformanceCertificatesEGHS.json"
    cost_excel_path = "/Users/hosseins/Dropbox/Zelda/ZeldaDemo/Parsed costs for EGHS and Finnboda for 2023 (1).xlsx"
    building_data_path = "/Users/hosseins/Dropbox/Zelda/ZeldaDemo/hammarby_building_data.json"
    output_path = "/Users/hosseins/Dropbox/Zelda/ZeldaDemo/hammarby_integrated_energy_cost_analysis.json"
    
    # Initialize analyzer
    analyzer = HammarbyEnergyAnalyzer(epc_json_path, cost_excel_path, building_data_path)
    
    try:
        # Load all data sources
        analyzer.load_epc_data()
        analyzer.load_cost_data()
        analyzer.load_building_data()
        
        # Merge and analyze
        analyzer.merge_data_sources()
        analyzer.calculate_key_metrics()
        
        # Export results
        output_file = analyzer.export_results(output_path)
        
        print(f"✅ Integration completed successfully!")
        print(f"📊 Enhanced dataset exported to: {output_file}")
        
        # Print summary statistics
        stats = analyzer._calculate_dataset_statistics()
        print(f"\n📈 Summary Statistics:")
        print(f"   Buildings with EPC data: {stats['energy_performance']['buildings_with_epc_data']}")
        print(f"   Average energy performance: {stats['energy_performance'].get('avg_kwh_per_m2', 'N/A')} kWh/m²")
        print(f"   Swedish average benchmark: 159 kWh/m²")
        
    except Exception as e:
        logger.error(f"Integration failed: {e}")
        raise


if __name__ == "__main__":
    main()