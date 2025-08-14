"""
API Endpoints for Zelda Database Integration
Provides RESTful API endpoints for accessing building data
"""

from flask import Flask, jsonify, request
from database_integration import DatabaseIntegration
import logging

app = Flask(__name__)
db = DatabaseIntegration()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/api/buildings/hammarby', methods=['GET'])
def get_hammarby_buildings():
    """
    Get all buildings in Hammarby Sjöstad
    Query params:
        - limit: Maximum number of buildings (default: 12)
    """
    try:
        limit = request.args.get('limit', 12, type=int)
        data = db.get_unified_building_data(limit)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching Hammarby buildings: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/buildings/polygon', methods=['POST'])
def get_buildings_in_polygon():
    """
    Get buildings within a polygon
    Request body:
        {
            "coordinates": [[lat1, lon1], [lat2, lon2], ...]
        }
    """
    try:
        data = request.get_json()
        if not data or 'coordinates' not in data:
            return jsonify({'error': 'coordinates required'}), 400
        
        coordinates = [(c[0], c[1]) for c in data['coordinates']]
        buildings = db.get_buildings_in_polygon(coordinates)
        
        # Get additional data for these buildings
        brf_ids = [b['brf_id'] for b in buildings]
        economy_data = db.get_economy_data(brf_ids, year=2023)
        documents = db.get_documents(brf_ids, doc_type='annual_report')
        
        return jsonify({
            'building_count': len(buildings),
            'buildings': buildings,
            'economy_data': economy_data,
            'documents': documents
        })
    except Exception as e:
        logger.error(f"Error fetching buildings in polygon: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/buildings/<int:brf_id>', methods=['GET'])
def get_building_details(brf_id):
    """
    Get detailed information for a specific building
    """
    try:
        # Get building info
        query = """
            SELECT r.*, b.org_number 
            FROM residences r
            JOIN brfs b ON r.brf_id = b.brf_id
            WHERE r.brf_id = %s
        """
        buildings = db.execute_query(query, (brf_id,))
        
        if not buildings:
            return jsonify({'error': 'Building not found'}), 404
        
        building = buildings[0]
        
        # Get economy data
        economy_data = db.get_economy_data([brf_id])
        
        # Get documents
        documents = db.get_documents([brf_id])
        
        return jsonify({
            'building': building,
            'economy_data': economy_data,
            'documents': documents
        })
    except Exception as e:
        logger.error(f"Error fetching building {brf_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/economy/stats', methods=['GET'])
def get_economy_statistics():
    """
    Get aggregated economy statistics
    Query params:
        - year: Year for statistics (default: 2023)
        - area: Area filter (default: 'Hammarby')
    """
    try:
        year = request.args.get('year', 2023, type=int)
        area = request.args.get('area', 'Hammarby', type=str)
        
        # Get buildings in area
        buildings = db.get_hammarby_buildings(limit=100)
        brf_ids = [b['brf_id'] for b in buildings]
        
        # Get aggregated stats
        stats = db.get_aggregated_energy_stats(brf_ids, year, year)
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error fetching economy statistics: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/documents/<int:brf_id>', methods=['GET'])
def get_building_documents(brf_id):
    """
    Get all documents for a specific building
    Query params:
        - type: Document type filter
        - year: Year filter
    """
    try:
        doc_type = request.args.get('type', None)
        year = request.args.get('year', None, type=int)
        
        documents = db.get_documents([brf_id], doc_type, year)
        
        return jsonify({
            'brf_id': brf_id,
            'document_count': len(documents),
            'documents': documents
        })
    except Exception as e:
        logger.error(f"Error fetching documents for building {brf_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute_query("SELECT 1")
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Zelda API Server...")
    print("API Endpoints available:")
    print("  - GET  /api/buildings/hammarby")
    print("  - POST /api/buildings/polygon")
    print("  - GET  /api/buildings/<brf_id>")
    print("  - GET  /api/economy/stats")
    print("  - GET  /api/documents/<brf_id>")
    print("  - GET  /api/health")
    print("\nServer running on http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)