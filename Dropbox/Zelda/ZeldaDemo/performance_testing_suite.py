#!/usr/bin/env python3
"""
Performance Testing Suite for EGHS Interactive Map System
========================================================

This script conducts comprehensive performance testing including:
- Load testing with various data sizes
- Memory usage profiling
- Response time measurement
- Scalability analysis
- Resource utilization monitoring
- Stress testing scenarios

Author: Claudette-Guardian (QA Specialist)  
Date: 2025-08-13
"""

import json
import pandas as pd
import numpy as np
import time
import psutil
import sys
import os
from datetime import datetime
import tracemalloc
import gc
import warnings
warnings.filterwarnings('ignore')

class PerformanceTester:
    """Comprehensive performance testing suite"""
    
    def __init__(self, data_file_path):
        self.data_file_path = data_file_path
        self.performance_results = {
            'timestamp': datetime.now().isoformat(),
            'load_testing': {},
            'memory_profiling': {},
            'response_times': {},
            'scalability_analysis': {},
            'stress_testing': {},
            'resource_monitoring': {},
            'performance_benchmarks': {}
        }
        self.baseline_memory = 0
        
    def get_system_info(self):
        """Get system information for context"""
        return {
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'platform': sys.platform,
            'python_version': sys.version.split()[0]
        }
    
    def measure_memory_usage(self):
        """Measure current memory usage"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)  # MB
    
    def load_test_data(self):
        """Load and prepare test data"""
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self.baseline_memory = self.measure_memory_usage()
            print(f"✅ Loaded {len(self.data)} buildings for performance testing")
            print(f"📊 Baseline memory usage: {self.baseline_memory:.2f}MB")
            return True
        except Exception as e:
            print(f"❌ Error loading test data: {str(e)}")
            return False
    
    def test_data_loading_performance(self):
        """Test data loading performance with various scenarios"""
        print("\n⚡ Testing Data Loading Performance...")
        
        load_tests = {
            'cold_load_times': [],
            'warm_load_times': [],
            'large_dataset_simulation': {},
            'concurrent_load_test': {},
            'memory_impact': {}
        }
        
        # Cold load test (first time loading)
        for i in range(5):
            start_time = time.perf_counter()
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            end_time = time.perf_counter()
            load_time = (end_time - start_time) * 1000  # milliseconds
            load_tests['cold_load_times'].append(load_time)
        
        # Warm load test (data already in memory)
        for i in range(5):
            start_time = time.perf_counter()
            test_data = self.data.copy()
            end_time = time.perf_counter()
            load_time = (end_time - start_time) * 1000
            load_tests['warm_load_times'].append(load_time)
        
        # Simulate larger dataset
        large_data = self.data * 10  # 90 buildings
        start_time = time.perf_counter()
        df_large = pd.DataFrame(large_data)
        end_time = time.perf_counter()
        load_tests['large_dataset_simulation'] = {
            'size': len(large_data),
            'load_time_ms': (end_time - start_time) * 1000,
            'memory_usage_mb': self.measure_memory_usage()
        }
        
        # Memory impact assessment
        memory_before = self.measure_memory_usage()
        df = pd.DataFrame(self.data)
        memory_after = self.measure_memory_usage()
        load_tests['memory_impact'] = {
            'before_mb': memory_before,
            'after_mb': memory_after,
            'increase_mb': memory_after - memory_before
        }
        
        # Calculate statistics
        avg_cold_load = np.mean(load_tests['cold_load_times'])
        avg_warm_load = np.mean(load_tests['warm_load_times'])
        
        print(f"  ❄️  Average cold load: {avg_cold_load:.2f}ms")
        print(f"  🔥 Average warm load: {avg_warm_load:.2f}ms")
        print(f"  📈 Large dataset (90 buildings): {load_tests['large_dataset_simulation']['load_time_ms']:.2f}ms")
        print(f"  💾 Memory increase: {load_tests['memory_impact']['increase_mb']:.2f}MB")
        
        self.performance_results['load_testing'] = load_tests
        return load_tests
    
    def test_data_processing_performance(self):
        """Test data processing operations performance"""
        print("\n🔄 Testing Data Processing Performance...")
        
        processing_tests = {
            'filtering_operations': [],
            'sorting_operations': [],
            'aggregation_operations': [],
            'coordinate_calculations': [],
            'chart_data_preparation': []
        }
        
        df = pd.DataFrame(self.data)
        
        # Filtering operations
        filters = [
            lambda d: d[d['energy_performance'] < 100],
            lambda d: d[d['energy_class'].isin(['A', 'B', 'C'])],
            lambda d: d[d['total_cost'] > 1000000],
            lambda d: d[d['construction_year'] > 2005]
        ]
        
        for filter_func in filters:
            start_time = time.perf_counter()
            filtered_df = filter_func(df)
            end_time = time.perf_counter()
            processing_tests['filtering_operations'].append({
                'time_ms': (end_time - start_time) * 1000,
                'result_count': len(filtered_df)
            })
        
        # Sorting operations
        sort_columns = ['energy_performance', 'total_cost', 'construction_year', 'brf_name']
        for col in sort_columns:
            if col in df.columns:
                start_time = time.perf_counter()
                sorted_df = df.sort_values(col)
                end_time = time.perf_counter()
                processing_tests['sorting_operations'].append({
                    'column': col,
                    'time_ms': (end_time - start_time) * 1000
                })
        
        # Aggregation operations
        aggregations = [
            ('energy_performance', 'mean'),
            ('total_cost', 'sum'),
            ('construction_year', 'min'),
            ('construction_year', 'max')
        ]
        
        for col, agg_func in aggregations:
            if col in df.columns:
                start_time = time.perf_counter()
                result = df[col].agg(agg_func)
                end_time = time.perf_counter()
                processing_tests['aggregation_operations'].append({
                    'operation': f"{col}_{agg_func}",
                    'time_ms': (end_time - start_time) * 1000,
                    'result': result
                })
        
        # Coordinate calculations
        start_time = time.perf_counter()
        lats = [b['latitude'] for b in self.data if b.get('latitude')]
        lngs = [b['longitude'] for b in self.data if b.get('longitude')]
        center_lat = np.mean(lats)
        center_lng = np.mean(lngs)
        end_time = time.perf_counter()
        processing_tests['coordinate_calculations'].append({
            'operation': 'center_calculation',
            'time_ms': (end_time - start_time) * 1000,
            'result_lat': center_lat,
            'result_lng': center_lng
        })
        
        # Chart data preparation
        start_time = time.perf_counter()
        chart_data = {
            'names': df['brf_name'].tolist(),
            'performances': df['energy_performance'].tolist(),
            'classes': df['energy_class'].tolist(),
            'costs': df['total_cost'].tolist()
        }
        end_time = time.perf_counter()
        processing_tests['chart_data_preparation'].append({
            'operation': 'chart_data_prep',
            'time_ms': (end_time - start_time) * 1000,
            'data_points': len(chart_data['names'])
        })
        
        # Calculate averages
        avg_filter_time = np.mean([op['time_ms'] for op in processing_tests['filtering_operations']])
        avg_sort_time = np.mean([op['time_ms'] for op in processing_tests['sorting_operations']])
        avg_agg_time = np.mean([op['time_ms'] for op in processing_tests['aggregation_operations']])
        
        print(f"  🔍 Average filtering time: {avg_filter_time:.2f}ms")
        print(f"  🔢 Average sorting time: {avg_sort_time:.2f}ms")
        print(f"  📊 Average aggregation time: {avg_agg_time:.2f}ms")
        print(f"  📍 Coordinate calculation: {processing_tests['coordinate_calculations'][0]['time_ms']:.2f}ms")
        print(f"  📈 Chart data prep: {processing_tests['chart_data_preparation'][0]['time_ms']:.2f}ms")
        
        self.performance_results['response_times'] = processing_tests
        return processing_tests
    
    def test_memory_profiling(self):
        """Profile memory usage patterns"""
        print("\n💾 Memory Profiling...")
        
        # Start memory tracing
        tracemalloc.start()
        
        memory_profile = {
            'baseline_memory_mb': self.baseline_memory,
            'operations': [],
            'peak_memory_mb': 0,
            'memory_leaks_detected': False
        }
        
        # Test various memory-intensive operations
        operations = [
            ('load_dataframe', lambda: pd.DataFrame(self.data)),
            ('duplicate_data', lambda: self.data * 5),
            ('create_large_array', lambda: np.random.randn(10000, 100)),
            ('json_serialization', lambda: json.dumps(self.data * 3)),
            ('coordinate_array', lambda: np.array([[b.get('latitude', 0), b.get('longitude', 0)] for b in self.data * 100]))
        ]
        
        for op_name, operation in operations:
            gc.collect()  # Force garbage collection
            memory_before = self.measure_memory_usage()
            
            start_time = time.perf_counter()
            result = operation()
            end_time = time.perf_counter()
            
            memory_after = self.measure_memory_usage()
            memory_peak = max(memory_before, memory_after)
            
            # Clean up
            del result
            gc.collect()
            memory_cleanup = self.measure_memory_usage()
            
            op_result = {
                'operation': op_name,
                'execution_time_ms': (end_time - start_time) * 1000,
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'memory_cleanup_mb': memory_cleanup,
                'memory_increase_mb': memory_after - memory_before,
                'memory_retained_mb': memory_cleanup - memory_before
            }
            
            memory_profile['operations'].append(op_result)
            memory_profile['peak_memory_mb'] = max(memory_profile['peak_memory_mb'], memory_peak)
            
            # Check for potential memory leaks
            if op_result['memory_retained_mb'] > 5:  # 5MB threshold
                memory_profile['memory_leaks_detected'] = True
        
        # Get memory trace
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        memory_profile['traced_current_mb'] = current / (1024 * 1024)
        memory_profile['traced_peak_mb'] = peak / (1024 * 1024)
        
        print(f"  📊 Peak memory usage: {memory_profile['peak_memory_mb']:.2f}MB")
        print(f"  🔍 Traced peak: {memory_profile['traced_peak_mb']:.2f}MB")
        print(f"  🚨 Memory leaks detected: {memory_profile['memory_leaks_detected']}")
        
        # Show top memory-consuming operations
        top_memory_ops = sorted(memory_profile['operations'], 
                               key=lambda x: x['memory_increase_mb'], reverse=True)[:3]
        print("  🔝 Top memory consumers:")
        for op in top_memory_ops:
            print(f"    - {op['operation']}: +{op['memory_increase_mb']:.2f}MB")
        
        self.performance_results['memory_profiling'] = memory_profile
        return memory_profile
    
    def test_scalability(self):
        """Test system scalability with increasing data sizes"""
        print("\n📈 Testing Scalability...")
        
        scalability_tests = {
            'data_size_tests': [],
            'performance_degradation': {},
            'resource_scaling': {},
            'breaking_point': None
        }
        
        # Test with increasing data sizes
        multipliers = [1, 2, 5, 10, 20, 50]
        
        for mult in multipliers:
            test_data = self.data * mult
            data_size = len(test_data)
            
            # Test loading performance
            start_time = time.perf_counter()
            df = pd.DataFrame(test_data)
            load_time = time.perf_counter() - start_time
            
            # Test filtering performance
            start_time = time.perf_counter()
            filtered = df[df['energy_performance'] < 100] if 'energy_performance' in df.columns else df
            filter_time = time.perf_counter() - start_time
            
            # Test memory usage
            memory_usage = self.measure_memory_usage()
            
            # Test chart data preparation
            start_time = time.perf_counter()
            chart_data = {
                'names': df['brf_name'].tolist() if 'brf_name' in df.columns else [],
                'performances': df['energy_performance'].tolist() if 'energy_performance' in df.columns else []
            }
            chart_prep_time = time.perf_counter() - start_time
            
            test_result = {
                'multiplier': mult,
                'data_size': data_size,
                'load_time_ms': load_time * 1000,
                'filter_time_ms': filter_time * 1000,
                'chart_prep_time_ms': chart_prep_time * 1000,
                'memory_usage_mb': memory_usage,
                'total_time_ms': (load_time + filter_time + chart_prep_time) * 1000
            }
            
            scalability_tests['data_size_tests'].append(test_result)
            
            # Check for breaking point (> 5 seconds total processing)
            if test_result['total_time_ms'] > 5000 and scalability_tests['breaking_point'] is None:
                scalability_tests['breaking_point'] = {
                    'data_size': data_size,
                    'multiplier': mult,
                    'processing_time_ms': test_result['total_time_ms']
                }
            
            print(f"  📊 Size {data_size:3d}: Load {load_time*1000:6.1f}ms, Filter {filter_time*1000:6.1f}ms, Memory {memory_usage:6.1f}MB")
            
            # Cleanup
            del test_data, df, filtered, chart_data
            gc.collect()
        
        # Analyze performance degradation
        baseline = scalability_tests['data_size_tests'][0]
        largest = scalability_tests['data_size_tests'][-1]
        
        scalability_tests['performance_degradation'] = {
            'size_increase_factor': largest['data_size'] / baseline['data_size'],
            'load_time_increase_factor': largest['load_time_ms'] / baseline['load_time_ms'],
            'memory_increase_factor': largest['memory_usage_mb'] / baseline['memory_usage_mb'],
            'linear_scaling': abs((largest['load_time_ms'] / baseline['load_time_ms']) - 
                                 (largest['data_size'] / baseline['data_size'])) < 2
        }
        
        print(f"  📈 Scalability analysis:")
        print(f"    Data size increased: {scalability_tests['performance_degradation']['size_increase_factor']:.1f}x")
        print(f"    Load time increased: {scalability_tests['performance_degradation']['load_time_increase_factor']:.1f}x")
        print(f"    Memory increased: {scalability_tests['performance_degradation']['memory_increase_factor']:.1f}x")
        print(f"    Linear scaling: {scalability_tests['performance_degradation']['linear_scaling']}")
        
        if scalability_tests['breaking_point']:
            print(f"  🚨 Breaking point: {scalability_tests['breaking_point']['data_size']} buildings")
        
        self.performance_results['scalability_analysis'] = scalability_tests
        return scalability_tests
    
    def test_stress_scenarios(self):
        """Test system under stress conditions"""
        print("\n🔥 Stress Testing...")
        
        stress_tests = {
            'rapid_operations': [],
            'concurrent_processing': {},
            'memory_pressure': {},
            'cpu_intensive': {},
            'system_stability': True
        }
        
        try:
            # Rapid operations test
            print("  ⚡ Testing rapid operations...")
            operations_per_second = []
            
            for _ in range(10):  # 10 rounds
                start_time = time.perf_counter()
                operations_count = 0
                
                # Perform operations for 1 second
                while time.perf_counter() - start_time < 1.0:
                    df = pd.DataFrame(self.data)
                    filtered = df[df['energy_performance'] < 200] if 'energy_performance' in df.columns else df
                    operations_count += 1
                
                operations_per_second.append(operations_count)
            
            stress_tests['rapid_operations'] = {
                'avg_ops_per_second': np.mean(operations_per_second),
                'max_ops_per_second': max(operations_per_second),
                'min_ops_per_second': min(operations_per_second),
                'stability': (max(operations_per_second) - min(operations_per_second)) / np.mean(operations_per_second) < 0.2
            }
            
            print(f"    Average operations/second: {stress_tests['rapid_operations']['avg_ops_per_second']:.1f}")
            
            # Memory pressure test
            print("  💾 Testing under memory pressure...")
            memory_before = self.measure_memory_usage()
            
            # Create large data structures
            large_datasets = []
            for i in range(20):
                large_data = self.data * (i + 1)
                large_datasets.append(pd.DataFrame(large_data))
            
            memory_peak = self.measure_memory_usage()
            
            # Test operations under pressure
            start_time = time.perf_counter()
            for df in large_datasets[:5]:  # Test with first 5 datasets
                filtered = df[df['energy_performance'] < 150] if 'energy_performance' in df.columns else df
            operation_time = time.perf_counter() - start_time
            
            # Cleanup
            del large_datasets
            gc.collect()
            memory_after = self.measure_memory_usage()
            
            stress_tests['memory_pressure'] = {
                'memory_before_mb': memory_before,
                'memory_peak_mb': memory_peak,
                'memory_after_mb': memory_after,
                'memory_increase_mb': memory_peak - memory_before,
                'operation_time_under_pressure_ms': operation_time * 1000,
                'memory_recovered': memory_after <= memory_before + 10  # 10MB tolerance
            }
            
            print(f"    Memory peak: {memory_peak:.1f}MB (+{memory_peak - memory_before:.1f}MB)")
            print(f"    Operations under pressure: {operation_time*1000:.1f}ms")
            
            # CPU intensive test
            print("  🖥️  Testing CPU intensive operations...")
            start_time = time.perf_counter()
            
            # Simulate CPU-intensive calculations
            for _ in range(1000):
                # Complex filtering and aggregations
                df = pd.DataFrame(self.data)
                if 'energy_performance' in df.columns and 'total_cost' in df.columns:
                    result = df.groupby('energy_class')['energy_performance'].agg(['mean', 'std', 'min', 'max'])
                    cost_analysis = df['total_cost'].describe()
            
            cpu_test_time = time.perf_counter() - start_time
            
            stress_tests['cpu_intensive'] = {
                'test_duration_ms': cpu_test_time * 1000,
                'operations_completed': 1000,
                'avg_time_per_operation_ms': cpu_test_time * 1000 / 1000,
                'cpu_performance': 'Good' if cpu_test_time < 10 else 'Poor'
            }
            
            print(f"    CPU intensive test: {cpu_test_time:.2f}s for 1000 operations")
            
        except Exception as e:
            print(f"    ❌ Stress test failed: {str(e)}")
            stress_tests['system_stability'] = False
        
        # Overall stability assessment
        stability_factors = [
            stress_tests['rapid_operations'].get('stability', False),
            stress_tests['memory_pressure'].get('memory_recovered', False),
            stress_tests['system_stability']
        ]
        
        overall_stability = sum(stability_factors) / len(stability_factors)
        stress_tests['overall_stability_score'] = overall_stability * 100
        
        print(f"  🎯 Overall stability score: {stress_tests['overall_stability_score']:.1f}%")
        
        self.performance_results['stress_testing'] = stress_tests
        return stress_tests
    
    def generate_performance_benchmarks(self):
        """Generate performance benchmarks and ratings"""
        print("\n📊 Generating Performance Benchmarks...")
        
        benchmarks = {
            'data_loading_rating': 'Unknown',
            'processing_speed_rating': 'Unknown',
            'memory_efficiency_rating': 'Unknown',
            'scalability_rating': 'Unknown',
            'stress_resistance_rating': 'Unknown',
            'overall_performance_score': 0,
            'overall_rating': 'Unknown'
        }
        
        # Data loading rating
        avg_cold_load = np.mean(self.performance_results['load_testing']['cold_load_times'])
        if avg_cold_load < 50:
            benchmarks['data_loading_rating'] = 'Excellent'
            load_score = 100
        elif avg_cold_load < 100:
            benchmarks['data_loading_rating'] = 'Good'
            load_score = 80
        elif avg_cold_load < 500:
            benchmarks['data_loading_rating'] = 'Fair'
            load_score = 60
        else:
            benchmarks['data_loading_rating'] = 'Poor'
            load_score = 40
        
        # Processing speed rating
        avg_filter_time = np.mean([op['time_ms'] for op in self.performance_results['response_times']['filtering_operations']])
        if avg_filter_time < 10:
            benchmarks['processing_speed_rating'] = 'Excellent'
            processing_score = 100
        elif avg_filter_time < 50:
            benchmarks['processing_speed_rating'] = 'Good'
            processing_score = 80
        elif avg_filter_time < 100:
            benchmarks['processing_speed_rating'] = 'Fair'
            processing_score = 60
        else:
            benchmarks['processing_speed_rating'] = 'Poor'
            processing_score = 40
        
        # Memory efficiency rating
        peak_memory = self.performance_results['memory_profiling']['peak_memory_mb']
        if peak_memory < 100:
            benchmarks['memory_efficiency_rating'] = 'Excellent'
            memory_score = 100
        elif peak_memory < 250:
            benchmarks['memory_efficiency_rating'] = 'Good'
            memory_score = 80
        elif peak_memory < 500:
            benchmarks['memory_efficiency_rating'] = 'Fair'
            memory_score = 60
        else:
            benchmarks['memory_efficiency_rating'] = 'Poor'
            memory_score = 40
        
        # Scalability rating
        linear_scaling = self.performance_results['scalability_analysis']['performance_degradation']['linear_scaling']
        breaking_point = self.performance_results['scalability_analysis']['breaking_point']
        
        if linear_scaling and (breaking_point is None or breaking_point['data_size'] > 450):
            benchmarks['scalability_rating'] = 'Excellent'
            scalability_score = 100
        elif linear_scaling:
            benchmarks['scalability_rating'] = 'Good'
            scalability_score = 80
        elif breaking_point is None or breaking_point['data_size'] > 180:
            benchmarks['scalability_rating'] = 'Fair'
            scalability_score = 60
        else:
            benchmarks['scalability_rating'] = 'Poor'
            scalability_score = 40
        
        # Stress resistance rating
        stability_score = self.performance_results['stress_testing']['overall_stability_score']
        if stability_score >= 90:
            benchmarks['stress_resistance_rating'] = 'Excellent'
            stress_score = 100
        elif stability_score >= 70:
            benchmarks['stress_resistance_rating'] = 'Good'
            stress_score = 80
        elif stability_score >= 50:
            benchmarks['stress_resistance_rating'] = 'Fair'
            stress_score = 60
        else:
            benchmarks['stress_resistance_rating'] = 'Poor'
            stress_score = 40
        
        # Overall performance score
        benchmarks['overall_performance_score'] = (load_score + processing_score + memory_score + scalability_score + stress_score) / 5
        
        if benchmarks['overall_performance_score'] >= 90:
            benchmarks['overall_rating'] = 'Excellent'
        elif benchmarks['overall_performance_score'] >= 80:
            benchmarks['overall_rating'] = 'Good'
        elif benchmarks['overall_performance_score'] >= 70:
            benchmarks['overall_rating'] = 'Fair'
        else:
            benchmarks['overall_rating'] = 'Poor'
        
        print(f"  ⚡ Data Loading: {benchmarks['data_loading_rating']}")
        print(f"  🔄 Processing Speed: {benchmarks['processing_speed_rating']}")
        print(f"  💾 Memory Efficiency: {benchmarks['memory_efficiency_rating']}")
        print(f"  📈 Scalability: {benchmarks['scalability_rating']}")
        print(f"  🔥 Stress Resistance: {benchmarks['stress_resistance_rating']}")
        print(f"  🎯 Overall Performance: {benchmarks['overall_rating']} ({benchmarks['overall_performance_score']:.1f}/100)")
        
        self.performance_results['performance_benchmarks'] = benchmarks
        return benchmarks
    
    def save_performance_report(self):
        """Save comprehensive performance report"""
        report_filename = f"/Users/hosseins/Dropbox/Zelda/ZeldaDemo/performance_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Add system info to results
        self.performance_results['system_info'] = self.get_system_info()
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(self.performance_results, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 Performance report saved: {report_filename}")
            return report_filename
            
        except Exception as e:
            print(f"❌ Error saving performance report: {str(e)}")
            return None
    
    def run_complete_performance_tests(self):
        """Run complete performance test suite"""
        print("🚀 EGHS Interactive Map - Performance Testing Suite")
        print("=" * 60)
        
        if not self.load_test_data():
            return False
        
        # System information
        sys_info = self.get_system_info()
        print(f"System: {sys_info['cpu_count']} CPU cores, {sys_info['memory_total_gb']:.1f}GB RAM, {sys_info['platform']}")
        
        # Run all performance tests
        self.test_data_loading_performance()
        self.test_data_processing_performance()
        self.test_memory_profiling()
        self.test_scalability()
        self.test_stress_scenarios()
        
        # Generate benchmarks
        benchmarks = self.generate_performance_benchmarks()
        
        # Save report
        self.save_performance_report()
        
        # Print final assessment
        print("\n" + "=" * 60)
        print("🎯 PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        
        print(f"Overall Performance: {benchmarks['overall_rating']} ({benchmarks['overall_performance_score']:.1f}/100)")
        
        if benchmarks['overall_performance_score'] >= 80:
            print("\n✅ PERFORMANCE EXCELLENT: System demonstrates excellent performance characteristics")
        elif benchmarks['overall_performance_score'] >= 70:
            print("\n👍 PERFORMANCE GOOD: System performance is acceptable for production use")
        else:
            print("\n⚠️  PERFORMANCE CONCERNS: Consider optimization before production deployment")
        
        return True

def main():
    """Main execution function"""
    data_file_path = "/Users/hosseins/Dropbox/Zelda/ZeldaDemo/killer_eghs_dataset_with_booli_coords.json"
    
    tester = PerformanceTester(data_file_path)
    success = tester.run_complete_performance_tests()
    
    if success:
        print(f"\n🎉 Performance testing completed successfully!")
        return tester.performance_results
    else:
        print(f"\n❌ Performance testing failed!")
        return None

if __name__ == "__main__":
    results = main()