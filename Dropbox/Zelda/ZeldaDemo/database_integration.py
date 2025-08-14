"""
Database Integration Module for Zelda System
Provides connection pooling and unified data access for Hammarby Sjöstad prototype
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseIntegration:
    """
    Unified database integration with connection pooling for Zelda system.
    Handles all database operations for buildings, economy data, and documents.
    """
    
    def __init__(self, min_conn=2, max_conn=10):
        """
        Initialize database connection pool
        
        Args:
            min_conn: Minimum number of connections in pool
            max_conn: Maximum number of connections in pool
        """
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                min_conn,
                max_conn,
                dbname='zelda',
                user='postgres',
                password='zeldaMaster',
                host='localhost',
                port=5432
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Error creating connection pool: {e}")
            raise
    
    def get_connection(self):
        """Get a connection from the pool"""
        return self.connection_pool.getconn()
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        self.connection_pool.putconn(conn)
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """
        Execute a query and return results as list of dictionaries
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries with query results
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                return []
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def get_hammarby_buildings(self, limit: int = 12) -> List[Dict]:
        """
        Get buildings in Hammarby Sjöstad area
        
        Args:
            limit: Maximum number of buildings to return
            
        Returns:
            List of building dictionaries with location data
        """
        query = """
            SELECT 
                r.brf_id,
                r.brf_name,
                r.latitude,
                r.longitude,
                r.formatted_address,
                r.city_appended,
                r.postal_code,
                b.org_number
            FROM residences r
            JOIN brfs b ON r.brf_id = b.brf_id
            WHERE r.city_appended ILIKE %s OR r.formatted_address ILIKE %s
            ORDER BY r.brf_id
            LIMIT %s
        """
        params = ('%Hammarby%', '%Hammarby%', limit)
        return self.execute_query(query, params)
    
    def get_buildings_in_polygon(self, coordinates: List[tuple]) -> List[Dict]:
        """
        Get buildings within a polygon defined by coordinates
        
        Args:
            coordinates: List of (lat, lon) tuples defining polygon vertices
            
        Returns:
            List of buildings within the polygon
        """
        if not coordinates or len(coordinates) < 3:
            raise ValueError("Polygon must have at least 3 coordinates")
        
        # Calculate bounding box for initial filtering
        lats = [c[0] for c in coordinates]
        lons = [c[1] for c in coordinates]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        query = """
            SELECT 
                r.brf_id,
                r.brf_name,
                r.latitude,
                r.longitude,
                r.formatted_address,
                r.city_appended,
                r.postal_code,
                b.org_number
            FROM residences r
            JOIN brfs b ON r.brf_id = b.brf_id
            WHERE r.latitude BETWEEN %s AND %s
            AND r.longitude BETWEEN %s AND %s
        """
        params = (min_lat, max_lat, min_lon, max_lon)
        buildings = self.execute_query(query, params)
        
        # Filter using point-in-polygon algorithm
        filtered = []
        for building in buildings:
            if self._point_in_polygon(
                (building['latitude'], building['longitude']),
                coordinates
            ):
                filtered.append(building)
        
        return filtered
    
    def _point_in_polygon(self, point: tuple, polygon: List[tuple]) -> bool:
        """
        Check if a point is inside a polygon using ray casting algorithm
        
        Args:
            point: (lat, lon) tuple
            polygon: List of (lat, lon) tuples
            
        Returns:
            True if point is inside polygon
        """
        lat, lon = point
        n = len(polygon)
        inside = False
        
        j = n - 1
        for i in range(n):
            lat_i, lon_i = polygon[i]
            lat_j, lon_j = polygon[j]
            
            if ((lon_i > lon) != (lon_j > lon)) and \
               (lat < (lat_j - lat_i) * (lon - lon_i) / (lon_j - lon_i) + lat_i):
                inside = not inside
            j = i
        
        return inside
    
    def get_economy_data(self, brf_ids: List[int], year: int = None) -> List[Dict]:
        """
        Get economy data for specified BRFs
        
        Args:
            brf_ids: List of BRF IDs
            year: Optional year filter
            
        Returns:
            List of economy data dictionaries
        """
        if not brf_ids:
            return []
        
        query = """
            SELECT 
                e.*,
                b.brf_name,
                b.org_number
            FROM economy_data e
            JOIN brfs b ON e.brf_id = b.brf_id
            WHERE e.brf_id = ANY(%s)
        """
        params = [brf_ids]
        
        if year:
            query += " AND e.year = %s"
            params.append(year)
        
        query += " ORDER BY e.brf_id, e.year DESC"
        
        return self.execute_query(query, tuple(params))
    
    def get_documents(self, brf_ids: List[int], doc_type: str = None, 
                     year: int = None) -> List[Dict]:
        """
        Get documents for specified BRFs
        
        Args:
            brf_ids: List of BRF IDs
            doc_type: Optional document type filter
            year: Optional year filter
            
        Returns:
            List of document dictionaries
        """
        if not brf_ids:
            return []
        
        query = """
            SELECT 
                d.*,
                b.brf_name,
                b.org_number
            FROM documents d
            JOIN brfs b ON d.brf_id = b.brf_id
            WHERE d.brf_id = ANY(%s)
        """
        params = [brf_ids]
        
        if doc_type:
            query += " AND d.document_type = %s"
            params.append(doc_type)
        
        if year:
            query += " AND d.year = %s"
            params.append(year)
        
        query += " ORDER BY d.brf_id, d.year DESC, d.document_type"
        
        return self.execute_query(query, tuple(params))
    
    def get_aggregated_energy_stats(self, brf_ids: List[int], 
                                   start_year: int = 2022, 
                                   end_year: int = 2024) -> Dict:
        """
        Get aggregated energy statistics for BRFs
        
        Args:
            brf_ids: List of BRF IDs
            start_year: Start year for aggregation
            end_year: End year for aggregation
            
        Returns:
            Dictionary with aggregated statistics
        """
        if not brf_ids:
            return {}
        
        query = """
            SELECT 
                COUNT(DISTINCT e.brf_id) as building_count,
                AVG(e.energy_costs) as avg_energy_cost,
                AVG(e.water_costs) as avg_water_cost,
                AVG(e.heating_costs) as avg_heating_cost,
                SUM(e.energy_costs) as total_energy_cost,
                SUM(e.water_costs) as total_water_cost,
                SUM(e.heating_costs) as total_heating_cost,
                AVG(e.monthly_fee) as avg_monthly_fee,
                MIN(e.year) as min_year,
                MAX(e.year) as max_year
            FROM economy_data e
            WHERE e.brf_id = ANY(%s)
            AND e.year BETWEEN %s AND %s
        """
        params = (brf_ids, start_year, end_year)
        
        result = self.execute_query(query, params)
        return result[0] if result else {}
    
    def get_unified_building_data(self, limit: int = 12) -> Dict:
        """
        Get complete unified data for Hammarby Sjöstad buildings
        Including building info, economy data, and documents
        
        Args:
            limit: Maximum number of buildings
            
        Returns:
            Structured JSON with complete building data
        """
        # Get buildings
        buildings = self.get_hammarby_buildings(limit)
        brf_ids = [b['brf_id'] for b in buildings]
        
        # Get economy data for 2023
        economy_data = self.get_economy_data(brf_ids, year=2023)
        economy_by_brf = {e['brf_id']: e for e in economy_data}
        
        # Get annual reports
        documents = self.get_documents(brf_ids, doc_type='annual_report')
        docs_by_brf = {}
        for doc in documents:
            if doc['brf_id'] not in docs_by_brf:
                docs_by_brf[doc['brf_id']] = []
            docs_by_brf[doc['brf_id']].append(doc)
        
        # Get aggregated statistics
        stats = self.get_aggregated_energy_stats(brf_ids)
        
        # Build unified response
        unified_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'area': 'Hammarby Sjöstad',
                'building_count': len(buildings),
                'data_year': 2023
            },
            'statistics': {
                'total_buildings': stats.get('building_count', 0),
                'avg_energy_cost': float(stats.get('avg_energy_cost', 0)),
                'avg_water_cost': float(stats.get('avg_water_cost', 0)),
                'avg_heating_cost': float(stats.get('avg_heating_cost', 0)),
                'total_energy_cost': float(stats.get('total_energy_cost', 0)),
                'total_water_cost': float(stats.get('total_water_cost', 0)),
                'total_heating_cost': float(stats.get('total_heating_cost', 0)),
                'avg_monthly_fee': float(stats.get('avg_monthly_fee', 0))
            },
            'buildings': []
        }
        
        # Combine data for each building
        for building in buildings:
            brf_id = building['brf_id']
            
            building_data = {
                'brf_id': brf_id,
                'brf_name': building['brf_name'],
                'org_number': building['org_number'],
                'location': {
                    'latitude': float(building['latitude']),
                    'longitude': float(building['longitude']),
                    'address': building['formatted_address'],
                    'city': building['city_appended'],
                    'postal_code': building['postal_code']
                },
                'economy': {},
                'documents': []
            }
            
            # Add economy data if available
            if brf_id in economy_by_brf:
                eco = economy_by_brf[brf_id]
                building_data['economy'] = {
                    'year': eco['year'],
                    'monthly_fee': float(eco['monthly_fee']),
                    'energy_costs': float(eco['energy_costs']),
                    'water_costs': float(eco['water_costs']),
                    'heating_costs': float(eco['heating_costs']),
                    'total_income': float(eco['total_income']),
                    'total_expenses': float(eco['total_expenses']),
                    'maintenance_fund': float(eco['maintenance_fund'])
                }
            
            # Add documents if available
            if brf_id in docs_by_brf:
                for doc in docs_by_brf[brf_id]:
                    building_data['documents'].append({
                        'document_id': doc['document_id'],
                        'type': doc['document_type'],
                        'name': doc['document_name'],
                        'year': doc['year'],
                        'file_path': doc['file_path'],
                        'metadata': doc.get('metadata', {})
                    })
            
            unified_data['buildings'].append(building_data)
        
        return unified_data
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("All database connections closed")


# Convenience functions for direct usage
def get_hammarby_data():
    """
    Get complete Hammarby Sjöstad building data
    
    Returns:
        Dictionary with unified building data
    """
    db = DatabaseIntegration()
    try:
        return db.get_unified_building_data()
    finally:
        db.close_all_connections()


def query_buildings_in_area(polygon_coords):
    """
    Query buildings within a polygon area
    
    Args:
        polygon_coords: List of (lat, lon) tuples
        
    Returns:
        List of buildings in the area
    """
    db = DatabaseIntegration()
    try:
        return db.get_buildings_in_polygon(polygon_coords)
    finally:
        db.close_all_connections()


if __name__ == "__main__":
    # Test the integration
    print("Testing Database Integration Module...")
    
    # Get unified data
    data = get_hammarby_data()
    
    # Save to JSON file
    with open('hammarby_building_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Retrieved data for {len(data['buildings'])} buildings")
    print(f"✓ Average energy cost: {data['statistics']['avg_energy_cost']:,.2f} SEK")
    print(f"✓ Data saved to hammarby_building_data.json")