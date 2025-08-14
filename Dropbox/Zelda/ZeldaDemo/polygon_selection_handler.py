#!/usr/bin/env python3
"""
Polygon Selection Handler for Hammarby Sjöstad Map

This module handles polygon-based building selection, spatial queries,
and integration with the database for document retrieval workflow.
"""

import json
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import unary_union
import pandas as pd
from datetime import datetime

class PolygonSelectionHandler:
    """Handles polygon-based building selection and spatial operations."""
    
    def __init__(self, buildings_data: List[Dict]):
        """Initialize with building data."""
        self.buildings = buildings_data
        self.selected_buildings = []
        self.selection_polygons = []
        self.selection_history = []
    
    def parse_geojson_polygon(self, geojson_data: Dict) -> Union[Polygon, MultiPolygon]:
        """Parse GeoJSON polygon data into Shapely geometry."""
        try:
            if geojson_data['type'] == 'Polygon':
                coordinates = geojson_data['coordinates'][0]  # Exterior ring
                return Polygon([(coord[0], coord[1]) for coord in coordinates])
            
            elif geojson_data['type'] == 'MultiPolygon':
                polygons = []
                for polygon_coords in geojson_data['coordinates']:
                    exterior_ring = polygon_coords[0]
                    poly = Polygon([(coord[0], coord[1]) for coord in exterior_ring])
                    polygons.append(poly)
                return MultiPolygon(polygons)
            
            else:
                raise ValueError(f"Unsupported geometry type: {geojson_data['type']}")
                
        except Exception as e:
            raise ValueError(f"Error parsing GeoJSON polygon: {e}")
    
    def point_in_polygon(self, lat: float, lng: float, polygon: Union[Polygon, MultiPolygon]) -> bool:
        """Check if a point (lat, lng) is within the polygon."""
        point = Point(lng, lat)  # Note: Shapely uses (x, y) = (lng, lat)
        return polygon.contains(point) or polygon.intersects(point)
    
    def select_buildings_in_polygon(self, geojson_polygon: Dict) -> List[Dict]:
        """Select buildings within the given GeoJSON polygon."""
        try:
            # Parse the polygon
            polygon = self.parse_geojson_polygon(geojson_polygon)
            
            # Find buildings within the polygon
            selected = []
            for building in self.buildings:
                lat = building['coordinates']['lat']
                lng = building['coordinates']['lng']
                
                if self.point_in_polygon(lat, lng, polygon):
                    selected.append(building)
            
            return selected
            
        except Exception as e:
            print(f"Error selecting buildings in polygon: {e}")
            return []
    
    def select_buildings_in_rectangle(self, bounds: Dict) -> List[Dict]:
        """Select buildings within rectangular bounds."""
        try:
            # Extract bounds
            south = bounds['south']
            north = bounds['north']
            west = bounds['west']
            east = bounds['east']
            
            # Create rectangle polygon
            rectangle_coords = [
                (west, south),   # SW
                (east, south),   # SE
                (east, north),   # NE
                (west, north),   # NW
                (west, south)    # Close polygon
            ]
            rectangle = Polygon(rectangle_coords)
            
            # Find buildings within rectangle
            selected = []
            for building in self.buildings:
                lat = building['coordinates']['lat']
                lng = building['coordinates']['lng']
                
                if self.point_in_polygon(lat, lng, rectangle):
                    selected.append(building)
            
            return selected
            
        except Exception as e:
            print(f"Error selecting buildings in rectangle: {e}")
            return []
    
    def add_selection(self, buildings: List[Dict], selection_type: str = "polygon") -> None:
        """Add buildings to the current selection."""
        # Avoid duplicates
        existing_ids = {b['id'] for b in self.selected_buildings}
        new_buildings = [b for b in buildings if b['id'] not in existing_ids]
        
        self.selected_buildings.extend(new_buildings)
        
        # Record selection in history
        self.selection_history.append({
            'timestamp': datetime.now().isoformat(),
            'type': selection_type,
            'buildings_added': len(new_buildings),
            'total_selected': len(self.selected_buildings)
        })
    
    def remove_selection(self, building_ids: List[int]) -> None:
        """Remove buildings from the current selection."""
        self.selected_buildings = [
            b for b in self.selected_buildings 
            if b['id'] not in building_ids
        ]
    
    def clear_selection(self) -> None:
        """Clear all selected buildings."""
        self.selected_buildings = []
        self.selection_polygons = []
    
    def get_selection_summary(self) -> Dict:
        """Get summary statistics for the current selection."""
        if not self.selected_buildings:
            return {'error': 'No buildings selected'}
        
        # Basic counts
        total_buildings = len(self.selected_buildings)
        buildings_with_energy = len([b for b in self.selected_buildings 
                                   if b.get('energy_performance_kwh_m2')])
        buildings_with_costs = len([b for b in self.selected_buildings 
                                  if b.get('monthly_fee')])
        
        # Energy performance statistics
        energy_performances = [b['energy_performance_kwh_m2'] 
                             for b in self.selected_buildings 
                             if b.get('energy_performance_kwh_m2')]
        
        # Performance scores
        performance_scores = [b.get('performance_score', 0) 
                            for b in self.selected_buildings]
        
        # Cost statistics
        monthly_fees = [b.get('monthly_fee', 0) 
                       for b in self.selected_buildings 
                       if b.get('monthly_fee')]
        
        summary = {
            'selection_info': {
                'total_buildings': total_buildings,
                'buildings_with_energy_data': buildings_with_energy,
                'buildings_with_cost_data': buildings_with_costs,
                'selection_timestamp': datetime.now().isoformat()
            },
            'energy_performance': {
                'count': len(energy_performances),
                'avg_kwh_m2': round(np.mean(energy_performances), 1) if energy_performances else None,
                'min_kwh_m2': min(energy_performances) if energy_performances else None,
                'max_kwh_m2': max(energy_performances) if energy_performances else None,
                'std_kwh_m2': round(np.std(energy_performances), 1) if energy_performances else None
            },
            'performance_scores': {
                'avg_score': round(np.mean(performance_scores), 1),
                'min_score': min(performance_scores),
                'max_score': max(performance_scores),
                'std_score': round(np.std(performance_scores), 1)
            },
            'cost_analysis': {
                'count': len(monthly_fees),
                'avg_monthly_fee': round(np.mean(monthly_fees), 2) if monthly_fees else None,
                'min_monthly_fee': min(monthly_fees) if monthly_fees else None,
                'max_monthly_fee': max(monthly_fees) if monthly_fees else None,
                'total_annual_fees': round(sum(monthly_fees) * 12, 2) if monthly_fees else None
            },
            'building_ids': [b['id'] for b in self.selected_buildings],
            'building_names': [b['name'] for b in self.selected_buildings]
        }
        
        return summary
    
    def export_selection_data(self, format_type: str = 'json') -> Union[str, Dict, pd.DataFrame]:
        """Export selected building data in specified format."""
        if not self.selected_buildings:
            return {'error': 'No buildings selected'}
        
        if format_type == 'json':
            return {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'total_buildings': len(self.selected_buildings),
                    'format': 'json'
                },
                'summary': self.get_selection_summary(),
                'buildings': self.selected_buildings
            }
        
        elif format_type == 'dataframe':
            # Flatten building data for DataFrame
            flattened_data = []
            for building in self.selected_buildings:
                flat_building = {
                    'id': building['id'],
                    'name': building['name'],
                    'address': building['address'],
                    'postal_code': building.get('postal_code', ''),
                    'latitude': building['coordinates']['lat'],
                    'longitude': building['coordinates']['lng'],
                    'energy_performance_kwh_m2': building.get('energy_performance_kwh_m2'),
                    'energy_class': building.get('energy_class'),
                    'efficiency_vs_swedish_avg': building.get('efficiency_vs_swedish_avg'),
                    'construction_year': building.get('construction_year'),
                    'monthly_fee': building.get('monthly_fee'),
                    'energy_costs': building.get('energy_costs'),
                    'heating_costs': building.get('heating_costs'),
                    'water_costs': building.get('water_costs'),
                    'performance_score': building.get('performance_score', 0),
                    'bang_for_buck_overall': building.get('bang_for_buck_overall', 0),
                    'epc_confidence': building.get('epc_confidence', 0),
                    'cost_confidence': building.get('cost_confidence', 0)
                }
                flattened_data.append(flat_building)
            
            return pd.DataFrame(flattened_data)
        
        elif format_type == 'geojson':
            # Create GeoJSON format for GIS applications
            features = []
            for building in self.selected_buildings:
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [
                            building['coordinates']['lng'],
                            building['coordinates']['lat']
                        ]
                    },
                    'properties': {
                        'id': building['id'],
                        'name': building['name'],
                        'address': building['address'],
                        'energy_performance_kwh_m2': building.get('energy_performance_kwh_m2'),
                        'energy_class': building.get('energy_class'),
                        'performance_score': building.get('performance_score', 0),
                        'monthly_fee': building.get('monthly_fee')
                    }
                }
                features.append(feature)
            
            return {
                'type': 'FeatureCollection',
                'features': features,
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'total_features': len(features)
                }
            }
        
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def get_database_integration_payload(self) -> Dict:
        """Prepare payload for database integration module."""
        if not self.selected_buildings:
            return {'error': 'No buildings selected'}
        
        return {
            'operation': 'get_documents_for_buildings',
            'building_ids': [b['id'] for b in self.selected_buildings],
            'building_names': [b['name'] for b in self.selected_buildings],
            'selection_summary': self.get_selection_summary(),
            'request_timestamp': datetime.now().isoformat(),
            'metadata': {
                'total_buildings': len(self.selected_buildings),
                'avg_performance_score': round(np.mean([b.get('performance_score', 0) 
                                                      for b in self.selected_buildings]), 1),
                'selection_criteria': 'polygon_based'
            }
        }
    
    def calculate_selection_metrics(self) -> Dict:
        """Calculate comparative metrics for the selected buildings."""
        if not self.selected_buildings:
            return {'error': 'No buildings selected'}
        
        # Calculate metrics relative to the full dataset
        all_performance_scores = [b.get('performance_score', 0) for b in self.buildings]
        selected_performance_scores = [b.get('performance_score', 0) for b in self.selected_buildings]
        
        all_monthly_fees = [b.get('monthly_fee', 0) for b in self.buildings if b.get('monthly_fee')]
        selected_monthly_fees = [b.get('monthly_fee', 0) for b in self.selected_buildings if b.get('monthly_fee')]
        
        metrics = {
            'performance_comparison': {
                'selected_avg': round(np.mean(selected_performance_scores), 1),
                'dataset_avg': round(np.mean(all_performance_scores), 1),
                'relative_performance': round(
                    (np.mean(selected_performance_scores) / np.mean(all_performance_scores) - 1) * 100, 1
                )
            },
            'cost_comparison': {
                'selected_avg_fee': round(np.mean(selected_monthly_fees), 2) if selected_monthly_fees else None,
                'dataset_avg_fee': round(np.mean(all_monthly_fees), 2) if all_monthly_fees else None,
                'relative_cost': round(
                    (np.mean(selected_monthly_fees) / np.mean(all_monthly_fees) - 1) * 100, 1
                ) if selected_monthly_fees and all_monthly_fees else None
            },
            'selection_diversity': {
                'performance_std': round(np.std(selected_performance_scores), 1),
                'cost_std': round(np.std(selected_monthly_fees), 2) if selected_monthly_fees else None,
                'unique_energy_classes': len(set(b.get('energy_class') for b in self.selected_buildings 
                                               if b.get('energy_class'))),
                'geographic_spread': self._calculate_geographic_spread()
            }
        }
        
        return metrics
    
    def _calculate_geographic_spread(self) -> Dict:
        """Calculate geographic spread of selected buildings."""
        if not self.selected_buildings:
            return {}
        
        lats = [b['coordinates']['lat'] for b in self.selected_buildings]
        lngs = [b['coordinates']['lng'] for b in self.selected_buildings]
        
        return {
            'center_lat': round(np.mean(lats), 6),
            'center_lng': round(np.mean(lngs), 6),
            'lat_range': round(max(lats) - min(lats), 6),
            'lng_range': round(max(lngs) - min(lngs), 6),
            'bounding_box': {
                'north': max(lats),
                'south': min(lats),
                'east': max(lngs),
                'west': min(lngs)
            }
        }

# Utility functions for integration with other modules

def integrate_with_database(selection_handler: PolygonSelectionHandler, db_connector=None):
    """Integrate polygon selection with database document retrieval."""
    payload = selection_handler.get_database_integration_payload()
    
    if 'error' in payload:
        return payload
    
    # This would integrate with the existing database_integration.py module
    if db_connector:
        try:
            # Example integration
            building_ids = payload['building_ids']
            documents = db_connector.get_documents_for_buildings(building_ids)
            
            return {
                'status': 'success',
                'building_selection': payload,
                'documents_found': len(documents) if documents else 0,
                'documents': documents
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Database integration failed: {e}",
                'building_selection': payload
            }
    else:
        return {
            'status': 'ready_for_integration',
            'message': 'Selection ready for database integration',
            'payload': payload,
            'next_steps': [
                'Initialize database connector',
                'Call get_documents_for_buildings() with building_ids',
                'Process returned documents for analysis'
            ]
        }

def create_selection_report(selection_handler: PolygonSelectionHandler) -> Dict:
    """Create a comprehensive report of the polygon selection."""
    summary = selection_handler.get_selection_summary()
    metrics = selection_handler.calculate_selection_metrics()
    
    report = {
        'report_info': {
            'timestamp': datetime.now().isoformat(),
            'report_type': 'polygon_selection_analysis'
        },
        'selection_summary': summary,
        'comparative_metrics': metrics,
        'recommendations': []
    }
    
    # Add recommendations based on selection analysis
    if 'performance_comparison' in metrics:
        perf_diff = metrics['performance_comparison']['relative_performance']
        if perf_diff > 10:
            report['recommendations'].append(
                f"Selected buildings perform {perf_diff:.1f}% better than average - good selection for best practices analysis"
            )
        elif perf_diff < -10:
            report['recommendations'].append(
                f"Selected buildings underperform by {abs(perf_diff):.1f}% - potential improvement opportunities"
            )
    
    if 'cost_comparison' in metrics and metrics['cost_comparison']['relative_cost']:
        cost_diff = metrics['cost_comparison']['relative_cost']
        if cost_diff > 10:
            report['recommendations'].append(
                f"Selected buildings have {cost_diff:.1f}% higher costs - investigate cost drivers"
            )
        elif cost_diff < -10:
            report['recommendations'].append(
                f"Selected buildings achieve {abs(cost_diff):.1f}% cost savings - analyze cost optimization strategies"
            )
    
    return report