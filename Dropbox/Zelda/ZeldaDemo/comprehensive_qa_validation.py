#!/usr/bin/env python3
"""
Comprehensive QA Validation Suite for EGHS Interactive Map System
================================================================

This script performs complete quality assurance validation including:
- Data integrity validation
- Coordinate accuracy verification
- Energy performance data validation
- Cost data completeness and consistency checks
- Performance benchmarking
- System health assessment

Author: Claudette-Guardian (QA Specialist)
Date: 2025-08-13
"""

import json
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class EGHSQAValidator:
    """Comprehensive QA validator for EGHS system"""
    
    def __init__(self, data_file_path):
        self.data_file_path = data_file_path
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'data_integrity': {},
            'coordinate_validation': {},
            'energy_validation': {},
            'cost_validation': {},
            'system_health': {},
            'performance_metrics': {},
            'recommendations': []
        }
        
    def load_and_validate_data(self):
        """Load data and perform basic validation"""
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            if not isinstance(self.data, list):
                raise ValueError("Data should be a list of buildings")
                
            self.validation_results['data_integrity']['total_buildings'] = len(self.data)
            self.validation_results['data_integrity']['file_load_success'] = True
            print(f"✅ Successfully loaded {len(self.data)} buildings from dataset")
            
        except FileNotFoundError:
            self.validation_results['data_integrity']['file_load_success'] = False
            self.validation_results['data_integrity']['error'] = "Dataset file not found"
            print("❌ Dataset file not found!")
            return False
            
        except json.JSONDecodeError as e:
            self.validation_results['data_integrity']['file_load_success'] = False
            self.validation_results['data_integrity']['error'] = f"Invalid JSON: {str(e)}"
            print(f"❌ Invalid JSON format: {str(e)}")
            return False
            
        except Exception as e:
            self.validation_results['data_integrity']['file_load_success'] = False
            self.validation_results['data_integrity']['error'] = str(e)
            print(f"❌ Error loading data: {str(e)}")
            return False
            
        return True
    
    def validate_coordinates(self):
        """Validate coordinate accuracy and completeness"""
        print("\n🌍 Validating Coordinates...")
        
        coord_validation = {
            'total_buildings': len(self.data),
            'buildings_with_coordinates': 0,
            'real_coordinates_count': 0,
            'approximate_coordinates_count': 0,
            'missing_coordinates': [],
            'coordinate_sources': {},
            'coordinate_accuracy': {}
        }
        
        # Stockholm/Hammarby Sjöstad bounds for validation
        hammarby_bounds = {
            'lat_min': 59.300, 'lat_max': 59.310,
            'lng_min': 18.095, 'lng_max': 18.115
        }
        
        for building in self.data:
            building_name = building.get('brf_name', building.get('building_id', 'Unknown'))
            
            if building.get('latitude') and building.get('longitude'):
                coord_validation['buildings_with_coordinates'] += 1
                
                # Check coordinate source
                source = building.get('coordinates_source', 'original')
                coord_validation['coordinate_sources'][source] = coord_validation['coordinate_sources'].get(source, 0) + 1
                
                # Validate coordinates are within Hammarby Sjöstad
                lat, lng = building['latitude'], building['longitude']
                if (hammarby_bounds['lat_min'] <= lat <= hammarby_bounds['lat_max'] and 
                    hammarby_bounds['lng_min'] <= lng <= hammarby_bounds['lng_max']):
                    
                    if source == 'booli.se':
                        coord_validation['real_coordinates_count'] += 1
                    else:
                        coord_validation['approximate_coordinates_count'] += 1
                else:
                    coord_validation['coordinate_accuracy'][building_name] = f"Outside Hammarby bounds: {lat}, {lng}"
                    
            else:
                coord_validation['missing_coordinates'].append(building_name)
        
        # Calculate accuracy metrics
        coord_validation['coordinate_completeness'] = (coord_validation['buildings_with_coordinates'] / coord_validation['total_buildings']) * 100
        coord_validation['real_coordinate_percentage'] = (coord_validation['real_coordinates_count'] / coord_validation['total_buildings']) * 100
        
        self.validation_results['coordinate_validation'] = coord_validation
        
        print(f"  📍 Buildings with coordinates: {coord_validation['buildings_with_coordinates']}/{coord_validation['total_buildings']}")
        print(f"  🎯 Real coordinates (Booli.se): {coord_validation['real_coordinates_count']}")
        print(f"  📐 Approximate coordinates: {coord_validation['approximate_coordinates_count']}")
        print(f"  ❌ Missing coordinates: {len(coord_validation['missing_coordinates'])}")
        
        if coord_validation['missing_coordinates']:
            print(f"    Missing: {', '.join(coord_validation['missing_coordinates'])}")
            
        return coord_validation
    
    def validate_energy_data(self):
        """Validate energy performance data from EPC certificates"""
        print("\n⚡ Validating Energy Performance Data...")
        
        energy_validation = {
            'buildings_with_energy_data': 0,
            'energy_classes': {},
            'performance_range': {'min': None, 'max': None, 'avg': None},
            'swedish_avg_comparison': {'better': 0, 'worse': 0, 'equal': 0},
            'missing_energy_data': [],
            'data_consistency_issues': []
        }
        
        swedish_avg = 159  # kWh/m² Swedish average
        performances = []
        
        for building in self.data:
            building_name = building.get('brf_name', building.get('building_id', 'Unknown'))
            
            # Check energy performance
            energy_perf = building.get('energy_performance')
            energy_class = building.get('energy_class')
            
            if energy_perf is not None:
                energy_validation['buildings_with_energy_data'] += 1
                performances.append(energy_perf)
                
                # Compare to Swedish average
                if energy_perf < swedish_avg:
                    energy_validation['swedish_avg_comparison']['better'] += 1
                elif energy_perf > swedish_avg:
                    energy_validation['swedish_avg_comparison']['worse'] += 1
                else:
                    energy_validation['swedish_avg_comparison']['equal'] += 1
                    
                # Validate energy class consistency
                if energy_class:
                    energy_validation['energy_classes'][energy_class] = energy_validation['energy_classes'].get(energy_class, 0) + 1
                    
                    # Check if energy class matches performance value
                    class_ranges = {
                        'A': (0, 50), 'B': (50, 100), 'C': (100, 150),
                        'D': (150, 200), 'E': (200, 250), 'F': (250, 300), 'G': (300, float('inf'))
                    }
                    
                    if energy_class in class_ranges:
                        min_val, max_val = class_ranges[energy_class]
                        if not (min_val <= energy_perf <= max_val):
                            energy_validation['data_consistency_issues'].append(
                                f"{building_name}: Class {energy_class} but performance {energy_perf} kWh/m²"
                            )
                            
            else:
                energy_validation['missing_energy_data'].append(building_name)
        
        # Calculate performance statistics
        if performances:
            energy_validation['performance_range']['min'] = min(performances)
            energy_validation['performance_range']['max'] = max(performances)
            energy_validation['performance_range']['avg'] = np.mean(performances)
        
        energy_validation['energy_data_completeness'] = (energy_validation['buildings_with_energy_data'] / len(self.data)) * 100
        
        self.validation_results['energy_validation'] = energy_validation
        
        print(f"  ⚡ Buildings with energy data: {energy_validation['buildings_with_energy_data']}/{len(self.data)}")
        print(f"  📊 Performance range: {energy_validation['performance_range']['min']:.1f} - {energy_validation['performance_range']['max']:.1f} kWh/m²")
        print(f"  📈 Average performance: {energy_validation['performance_range']['avg']:.1f} kWh/m²")
        print(f"  🇸🇪 Better than Swedish avg: {energy_validation['swedish_avg_comparison']['better']} buildings")
        print(f"  ⚠️  Consistency issues: {len(energy_validation['data_consistency_issues'])}")
        
        return energy_validation
    
    def validate_cost_data(self):
        """Validate cost data completeness and accuracy"""
        print("\n💰 Validating Cost Data...")
        
        cost_validation = {
            'buildings_with_cost_data': 0,
            'cost_categories': {
                'electricity': {'count': 0, 'total': 0, 'avg': 0},
                'heating': {'count': 0, 'total': 0, 'avg': 0},
                'water': {'count': 0, 'total': 0, 'avg': 0},
                'internet_tv': {'count': 0, 'total': 0, 'avg': 0},
                'recycling': {'count': 0, 'total': 0, 'avg': 0},
                'total_cost': {'count': 0, 'total': 0, 'avg': 0}
            },
            'missing_cost_data': [],
            'cost_outliers': [],
            'data_consistency_issues': []
        }
        
        cost_fields = ['cost_electricity', 'cost_heating', 'cost_water', 'cost_internet_and_tv', 'cost_recycling', 'total_cost']
        
        for building in self.data:
            building_name = building.get('brf_name', building.get('building_id', 'Unknown'))
            has_cost_data = False
            
            # Check each cost category
            building_costs = {}
            for field in cost_fields:
                value = building.get(field)
                if value is not None and value > 0:
                    has_cost_data = True
                    category = field.replace('cost_', '').replace('_', '_')
                    if category in cost_validation['cost_categories']:
                        cost_validation['cost_categories'][category]['count'] += 1
                        cost_validation['cost_categories'][category]['total'] += value
                        building_costs[category] = value
            
            if has_cost_data:
                cost_validation['buildings_with_cost_data'] += 1
                
                # Check for cost consistency
                total_cost = building.get('total_cost', 0)
                calculated_total = sum([
                    building.get('cost_electricity', 0),
                    building.get('cost_heating', 0),
                    building.get('cost_water', 0),
                    building.get('cost_internet_and_tv', 0),
                    building.get('cost_recycling', 0)
                ])
                
                if total_cost > 0 and calculated_total > 0:
                    if abs(total_cost - calculated_total) > total_cost * 0.1:  # 10% tolerance
                        cost_validation['data_consistency_issues'].append(
                            f"{building_name}: Total cost {total_cost:,} vs calculated {calculated_total:,}"
                        )
            else:
                cost_validation['missing_cost_data'].append(building_name)
        
        # Calculate averages
        for category, data in cost_validation['cost_categories'].items():
            if data['count'] > 0:
                data['avg'] = data['total'] / data['count']
        
        cost_validation['cost_data_completeness'] = (cost_validation['buildings_with_cost_data'] / len(self.data)) * 100
        
        self.validation_results['cost_validation'] = cost_validation
        
        print(f"  💰 Buildings with cost data: {cost_validation['buildings_with_cost_data']}/{len(self.data)}")
        print(f"  🔍 Data consistency issues: {len(cost_validation['data_consistency_issues'])}")
        print(f"  ❌ Missing cost data: {len(cost_validation['missing_cost_data'])}")
        
        return cost_validation
    
    def perform_system_health_check(self):
        """Assess overall system health and readiness"""
        print("\n🏥 System Health Assessment...")
        
        health_check = {
            'data_quality_score': 0,
            'completeness_score': 0,
            'accuracy_score': 0,
            'consistency_score': 0,
            'overall_health': 'Unknown',
            'critical_issues': [],
            'warnings': [],
            'passed_checks': []
        }
        
        # Data quality metrics
        coord_completeness = self.validation_results['coordinate_validation']['coordinate_completeness']
        energy_completeness = self.validation_results['energy_validation']['energy_data_completeness']
        cost_completeness = self.validation_results['cost_validation']['cost_data_completeness']
        
        health_check['completeness_score'] = (coord_completeness + energy_completeness + cost_completeness) / 3
        
        # Critical issues check
        if coord_completeness < 90:
            health_check['critical_issues'].append(f"Low coordinate completeness: {coord_completeness:.1f}%")
        else:
            health_check['passed_checks'].append("Coordinate completeness > 90%")
            
        if energy_completeness < 90:
            health_check['critical_issues'].append(f"Low energy data completeness: {energy_completeness:.1f}%")
        else:
            health_check['passed_checks'].append("Energy data completeness > 90%")
        
        if len(self.validation_results['energy_validation']['data_consistency_issues']) > 2:
            health_check['critical_issues'].append("Multiple energy data consistency issues")
        else:
            health_check['passed_checks'].append("Energy data consistency acceptable")
            
        if len(self.validation_results['cost_validation']['data_consistency_issues']) > 2:
            health_check['critical_issues'].append("Multiple cost data consistency issues")
        else:
            health_check['passed_checks'].append("Cost data consistency acceptable")
        
        # Real coordinates check
        real_coord_percentage = self.validation_results['coordinate_validation']['real_coordinate_percentage']
        if real_coord_percentage < 70:
            health_check['warnings'].append(f"Only {real_coord_percentage:.1f}% have real coordinates from Booli.se")
        else:
            health_check['passed_checks'].append("Sufficient real coordinates from Booli.se")
        
        # Calculate overall health score
        base_score = health_check['completeness_score']
        penalty = len(health_check['critical_issues']) * 15 + len(health_check['warnings']) * 5
        health_check['data_quality_score'] = max(0, base_score - penalty)
        
        # Determine overall health status
        if health_check['data_quality_score'] >= 90:
            health_check['overall_health'] = 'Excellent'
        elif health_check['data_quality_score'] >= 80:
            health_check['overall_health'] = 'Good'
        elif health_check['data_quality_score'] >= 70:
            health_check['overall_health'] = 'Fair'
        else:
            health_check['overall_health'] = 'Poor'
        
        self.validation_results['system_health'] = health_check
        
        print(f"  🎯 Data Quality Score: {health_check['data_quality_score']:.1f}/100")
        print(f"  🏥 Overall Health: {health_check['overall_health']}")
        print(f"  ❌ Critical Issues: {len(health_check['critical_issues'])}")
        print(f"  ⚠️  Warnings: {len(health_check['warnings'])}")
        print(f"  ✅ Passed Checks: {len(health_check['passed_checks'])}")
        
        return health_check
    
    def performance_benchmark(self):
        """Benchmark system performance metrics"""
        print("\n⏱️  Performance Benchmarking...")
        
        start_time = datetime.now()
        
        # Simulate data processing operations
        df = pd.DataFrame(self.data)
        
        # Test data loading time
        load_start = datetime.now()
        test_data = self.data.copy()
        load_time = (datetime.now() - load_start).total_seconds()
        
        # Test filtering operations
        filter_start = datetime.now()
        filtered_data = [b for b in test_data if b.get('energy_performance', 0) < 200]
        filter_time = (datetime.now() - filter_start).total_seconds()
        
        # Test coordinate operations
        coord_start = datetime.now()
        coordinates = [(b.get('latitude'), b.get('longitude')) for b in test_data if b.get('latitude')]
        coord_time = (datetime.now() - coord_start).total_seconds()
        
        # Calculate memory usage approximation
        import sys
        data_size_mb = sys.getsizeof(str(self.data)) / (1024 * 1024)
        
        performance_metrics = {
            'data_load_time_ms': load_time * 1000,
            'filter_operation_time_ms': filter_time * 1000,
            'coordinate_processing_time_ms': coord_time * 1000,
            'estimated_memory_usage_mb': data_size_mb,
            'total_benchmark_time_ms': (datetime.now() - start_time).total_seconds() * 1000,
            'performance_rating': 'Unknown'
        }
        
        # Determine performance rating
        total_time = performance_metrics['total_benchmark_time_ms']
        if total_time < 100:
            performance_metrics['performance_rating'] = 'Excellent'
        elif total_time < 500:
            performance_metrics['performance_rating'] = 'Good'
        elif total_time < 1000:
            performance_metrics['performance_rating'] = 'Fair'
        else:
            performance_metrics['performance_rating'] = 'Poor'
        
        self.validation_results['performance_metrics'] = performance_metrics
        
        print(f"  ⚡ Data Load Time: {performance_metrics['data_load_time_ms']:.2f}ms")
        print(f"  🔍 Filter Time: {performance_metrics['filter_operation_time_ms']:.2f}ms")
        print(f"  📍 Coordinate Processing: {performance_metrics['coordinate_processing_time_ms']:.2f}ms")
        print(f"  💾 Memory Usage: {performance_metrics['estimated_memory_usage_mb']:.2f}MB")
        print(f"  ⭐ Performance Rating: {performance_metrics['performance_rating']}")
        
        return performance_metrics
    
    def generate_recommendations(self):
        """Generate actionable recommendations based on validation results"""
        print("\n💡 Generating Recommendations...")
        
        recommendations = []
        
        # Coordinate recommendations
        coord_data = self.validation_results['coordinate_validation']
        if coord_data['real_coordinate_percentage'] < 100:
            missing_real = coord_data['total_buildings'] - coord_data['real_coordinates_count']
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Coordinates',
                'issue': f"{missing_real} buildings lack real coordinates from Booli.se",
                'recommendation': "Obtain real coordinates for all buildings using Booli.se API or manual verification",
                'impact': "Critical for accurate mapping and location-based analysis"
            })
        
        # Energy data recommendations
        energy_data = self.validation_results['energy_validation']
        if len(energy_data['data_consistency_issues']) > 0:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Energy Data',
                'issue': f"{len(energy_data['data_consistency_issues'])} energy class/performance mismatches",
                'recommendation': "Review and correct energy class assignments based on performance values",
                'impact': "Affects energy performance analysis accuracy"
            })
        
        # Cost data recommendations
        cost_data = self.validation_results['cost_validation']
        if len(cost_data['data_consistency_issues']) > 0:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Cost Data',
                'issue': f"{len(cost_data['data_consistency_issues'])} cost calculation inconsistencies",
                'recommendation': "Verify total cost calculations and ensure all cost categories are included",
                'impact': "Affects financial analysis and building comparisons"
            })
        
        # System health recommendations
        health = self.validation_results['system_health']
        if health['overall_health'] in ['Fair', 'Poor']:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'System Health',
                'issue': f"Overall system health is {health['overall_health']}",
                'recommendation': "Address critical data quality issues before production deployment",
                'impact': "System reliability and user experience"
            })
        
        # Performance recommendations
        perf = self.validation_results['performance_metrics']
        if perf['performance_rating'] in ['Fair', 'Poor']:
            recommendations.append({
                'priority': 'LOW',
                'category': 'Performance',
                'issue': f"Performance rating is {perf['performance_rating']}",
                'recommendation': "Optimize data processing and consider caching for better performance",
                'impact': "User experience and system responsiveness"
            })
        
        # Production readiness recommendations
        if coord_data['coordinate_completeness'] >= 95 and energy_data['energy_data_completeness'] >= 95:
            recommendations.append({
                'priority': 'INFO',
                'category': 'Production Readiness',
                'issue': "System shows high data completeness",
                'recommendation': "System is ready for production deployment with current data quality",
                'impact': "Positive - ready for demonstration and live use"
            })
        
        self.validation_results['recommendations'] = recommendations
        
        print(f"  📋 Generated {len(recommendations)} recommendations")
        for rec in recommendations:
            priority_emoji = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢', 'INFO': '🔵'}
            print(f"    {priority_emoji.get(rec['priority'], '⚪')} {rec['priority']}: {rec['issue']}")
        
        return recommendations
    
    def save_validation_report(self):
        """Save comprehensive validation report"""
        report_filename = f"/Users/hosseins/Dropbox/Zelda/ZeldaDemo/qa_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 Validation report saved: {report_filename}")
            return report_filename
            
        except Exception as e:
            print(f"❌ Error saving report: {str(e)}")
            return None
    
    def run_complete_validation(self):
        """Run complete validation suite"""
        print("🔍 EGHS Interactive Map System - Comprehensive QA Validation")
        print("=" * 60)
        
        if not self.load_and_validate_data():
            return False
        
        # Run all validation checks
        self.validate_coordinates()
        self.validate_energy_data()
        self.validate_cost_data()
        self.perform_system_health_check()
        self.performance_benchmark()
        self.generate_recommendations()
        
        # Save report
        report_file = self.save_validation_report()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 VALIDATION SUMMARY")
        print("=" * 60)
        
        health = self.validation_results['system_health']
        print(f"Overall System Health: {health['overall_health']} ({health['data_quality_score']:.1f}/100)")
        print(f"Critical Issues: {len(health['critical_issues'])}")
        print(f"Warnings: {len(health['warnings'])}")
        print(f"Recommendations: {len(self.validation_results['recommendations'])}")
        
        # Production readiness assessment
        if health['data_quality_score'] >= 80 and len(health['critical_issues']) == 0:
            print("\n✅ PRODUCTION READY: System passes quality standards for production deployment")
        elif health['data_quality_score'] >= 70:
            print("\n⚠️  CAUTION: System has minor issues but may be suitable for demonstration")
        else:
            print("\n❌ NOT READY: Critical issues must be resolved before production use")
        
        return True

def main():
    """Main execution function"""
    # Path to the EGHS dataset
    data_file_path = "/Users/hosseins/Dropbox/Zelda/ZeldaDemo/killer_eghs_dataset_with_booli_coords.json"
    
    # Initialize and run validator
    validator = EGHSQAValidator(data_file_path)
    success = validator.run_complete_validation()
    
    if success:
        print(f"\n🎉 QA validation completed successfully!")
        return validator.validation_results
    else:
        print(f"\n❌ QA validation failed!")
        return None

if __name__ == "__main__":
    results = main()