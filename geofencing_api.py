#!/usr/bin/env python3
"""
API de Geofencing para Detecção de Transações em Prisões
Uso: Bancos e fintechs para bloqueio/alerta de transações suspeitas
"""

from flask import Flask, jsonify, request
import geopandas as gpd
from shapely.geometry import Point
import os
import glob
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime, timezone


app = Flask(__name__)

# Cache global para os dados de prisões
PRISONS_DATA = None
PRISONS_BUFFERS = None


class PrisonGeofencing:
    """Sistema de geofencing para detecção de transações em prisões"""
    
    def __init__(self, prisons_file: str, buffer_meters: int = 50):
        """
        Args:
            prisons_file: arquivo GeoJSON/GPKG com prisões
            buffer_meters: buffer interno para precisão (padrão: 50m)
        """
        print(f"📂 Carregando prisões de {prisons_file}...")
        self.prisons_gdf = gpd.read_file(prisons_file)
        self.buffer_meters = buffer_meters
        
        # Converter para projeção métrica para buffers precisos
        self.prisons_metric = self.prisons_gdf.to_crs(epsg=3857)
        
        # Criar buffers para cada prisão (área de segurança)
        self._create_prison_zones()
        
        print(f"✓ {len(self.prisons_gdf)} prisões carregadas")
        print(f"✓ Buffer de segurança: {buffer_meters}m")
    
    def _create_prison_zones(self):
        """Cria zonas de prisão com buffer de segurança"""
        # Buffer interno para garantir que estamos DENTRO da prisão
        # Isso evita pegar pontos na borda/rua ao redor
        self.prisons_metric['zone'] = self.prisons_metric.geometry.buffer(-self.buffer_meters)
        
        # Voltar para lat/lon
        self.prisons_zones = self.prisons_metric.to_crs(epsg=4326)
    
    def check_location(
        self, 
        latitude: float, 
        longitude: float
    ) -> Dict:
        """
        Verifica se uma localização está dentro de uma prisão
        
        Args:
            latitude: latitude da transação
            longitude: longitude da transação
            
        Returns:
            Dict com resultado da verificação
        """
        point = Point(longitude, latitude)
        
        # Verificar se está dentro de alguma zona de prisão
        for idx, prison in self.prisons_zones.iterrows():
            if prison['zone'].contains(point):
                return {
                    'inside_prison': True,
                    'risk_level': 'HIGH',
                    'action': 'BLOCK',
                    'prison_info': {
                        'osm_id': prison['osm_id'],
                        'name': prison.get('name', 'Prisão não identificada'),
                        'operator': prison.get('operator', 'N/A'),
                        'state': prison.get('addr:state', 'N/A'),
                        'city': prison.get('addr:city', 'N/A')
                    },
                    'coordinates': {
                        'latitude': latitude,
                        'longitude': longitude
                    },
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
        
        return {
            'inside_prison': False,
            'risk_level': 'LOW',
            'action': 'ALLOW',
            'prison_info': None,
            'coordinates': {
                'latitude': latitude,
                'longitude': longitude
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def batch_check(
        self, 
        locations: List[Tuple[float, float]]
    ) -> List[Dict]:
        """
        Verifica múltiplas localizações em batch
        
        Args:
            locations: lista de (latitude, longitude)
            
        Returns:
            Lista de resultados
        """
        results = []
        for lat, lon in locations:
            results.append(self.check_location(lat, lon))
        return results
    
    def get_nearest_prison(
        self, 
        latitude: float, 
        longitude: float,
        max_distance_km: float = 5.0
    ) -> Optional[Dict]:
        """
        Retorna a prisão mais próxima (se dentro do raio máximo)
        
        Args:
            latitude: latitude
            longitude: longitude
            max_distance_km: distância máxima em km
            
        Returns:
            Dict com info da prisão ou None
        """
        point = Point(longitude, latitude)
        point_metric = gpd.GeoSeries([point], crs='EPSG:4326').to_crs(epsg=3857).iloc[0]
        
        # Calcular distâncias
        distances = self.prisons_metric.geometry.distance(point_metric)
        min_distance = distances.min()
        
        # Converter para km
        min_distance_km = min_distance / 1000
        
        if min_distance_km <= max_distance_km:
            nearest_idx = distances.idxmin()
            nearest_prison = self.prisons_gdf.iloc[nearest_idx]
            
            return {
                'distance_km': round(min_distance_km, 3),
                'distance_meters': round(min_distance, 1),
                'prison_info': {
                    'osm_id': nearest_prison['osm_id'],
                    'name': nearest_prison.get('name', 'N/A'),
                    'operator': nearest_prison.get('operator', 'N/A'),
                    'state': nearest_prison.get('addr:state', 'N/A')
                }
            }
        
        return None
    
    def export_geojson_zones(self, output_file: str):
        """
        Export zonas de prisão para GeoJSON (para uso em outros sistemas)
        
        Args:
            output_file: arquivo de saída
        """
        # Preparar dados limpos para export
        export_gdf = self.prisons_zones[['osm_id', 'name', 'operator', 'zone']].copy()
        export_gdf = export_gdf.rename(columns={'zone': 'geometry'})
        export_gdf = export_gdf.set_geometry('geometry')
        
        export_gdf.to_file(output_file, driver='GeoJSON')
        print(f"✓ Zonas exportadas: {output_file}")
    
    def export_json_list(self, output_file: str):
        """
        Export lista simples de prisões em JSON (para cache em apps)
        
        Args:
            output_file: arquivo de saída JSON
        """
        prisons_list = []
        
        for idx, prison in self.prisons_gdf.iterrows():
            prisons_list.append({
                'id': prison['osm_id'],
                'name': prison.get('name', 'N/A'),
                'operator': prison.get('operator', 'N/A'),
                'state': prison.get('addr:state', 'N/A'),
                'city': prison.get('addr:city', 'N/A'),
                'latitude': prison.geometry.y,
                'longitude': prison.geometry.x,
                'osm_link': f"https://www.openstreetmap.org/{prison['osm_type']}/{prison['osm_id']}"
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total': len(prisons_list),
                'buffer_meters': self.buffer_meters,
                'generated_at': datetime.utcnow().isoformat(),
                'prisons': prisons_list
            }, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Lista JSON exportada: {output_file}")


# ==================== API REST ENDPOINTS ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        'status': 'healthy',
        'prisons_loaded': len(PRISONS_DATA.prisons_gdf) if PRISONS_DATA else 0,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/v1/check-location', methods=['POST'])
def check_location():
    """
    Verifica se uma localização está dentro de uma prisão
    
    Body JSON:
    {
        "latitude": -22.9068,
        "longitude": -43.1729,
        "transaction_id": "optional-id"
    }
    
    Response:
    {
        "inside_prison": true/false,
        "risk_level": "HIGH/MEDIUM/LOW",
        "action": "BLOCK/ALERT/ALLOW",
        "prison_info": {...} or null
    }
    """
    if not PRISONS_DATA:
        return jsonify({'error': 'Prison data not loaded'}), 500
    
    data = request.json
    
    if not data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({'error': 'Missing latitude or longitude'}), 400
    
    try:
        lat = float(data['latitude'])
        lon = float(data['longitude'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid coordinates'}), 400
    
    result = PRISONS_DATA.check_location(lat, lon)
    
    # Adicionar transaction_id se fornecido
    if 'transaction_id' in data:
        result['transaction_id'] = data['transaction_id']
    
    return jsonify(result)


@app.route('/api/v1/batch-check', methods=['POST'])
def batch_check():
    """
    Verifica múltiplas localizações em batch
    
    Body JSON:
    {
        "locations": [
            {"latitude": -22.9068, "longitude": -43.1729},
            {"latitude": -23.5505, "longitude": -46.6333}
        ]
    }
    """
    if not PRISONS_DATA:
        return jsonify({'error': 'Prison data not loaded'}), 500
    
    data = request.json
    
    if not data or 'locations' not in data:
        return jsonify({'error': 'Missing locations array'}), 400
    
    locations = []
    for loc in data['locations']:
        try:
            lat = float(loc['latitude'])
            lon = float(loc['longitude'])
            locations.append((lat, lon))
        except (ValueError, TypeError, KeyError):
            return jsonify({'error': 'Invalid location format'}), 400
    
    results = PRISONS_DATA.batch_check(locations)
    
    return jsonify({
        'total': len(results),
        'results': results
    })


@app.route('/api/v1/nearest-prison', methods=['POST'])
def nearest_prison():
    """
    Retorna a prisão mais próxima
    
    Body JSON:
    {
        "latitude": -22.9068,
        "longitude": -43.1729,
        "max_distance_km": 5.0
    }
    """
    if not PRISONS_DATA:
        return jsonify({'error': 'Prison data not loaded'}), 500
    
    data = request.json
    
    if not data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({'error': 'Missing latitude or longitude'}), 400
    
    try:
        lat = float(data['latitude'])
        lon = float(data['longitude'])
        max_dist = float(data.get('max_distance_km', 5.0))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid parameters'}), 400
    
    result = PRISONS_DATA.get_nearest_prison(lat, lon, max_dist)
    
    if result:
        return jsonify(result)
    else:
        return jsonify({
            'distance_km': None,
            'prison_info': None,
            'message': f'No prison found within {max_dist}km'
        })


@app.route('/api/v1/stats', methods=['GET'])
def stats():
    """Retorna estatísticas do sistema"""
    if not PRISONS_DATA:
        return jsonify({'error': 'Prison data not loaded'}), 500
    
    gdf = PRISONS_DATA.prisons_gdf
    
    # Converter numpy int64 para int nativo do Python
    by_state = {}
    if 'addr:state' in gdf.columns:
        for state, count in gdf['addr:state'].value_counts().items():
            by_state[str(state)] = int(count)
    
    return jsonify({
        'total_prisons': int(len(gdf)),
        'by_state': by_state,
        'with_name': int(gdf['name'].notna().sum()) if 'name' in gdf.columns else 0,
        'with_operator': int(gdf['operator'].notna().sum()) if 'operator' in gdf.columns else 0,
        'buffer_meters': int(PRISONS_DATA.buffer_meters)
    })


def initialize_api(prisons_file: str = None, buffer_meters: int = 50):
    """
    Inicializa a API com dados de prisões
    
    Args:
        prisons_file: arquivo com prisões (se None, busca automaticamente)
        buffer_meters: buffer de segurança
    """
    global PRISONS_DATA
    
    if prisons_file is None:
        # Buscar arquivo mais recente
        geojson_files = glob.glob('data/prisons_brazil_*.geojson')
        if not geojson_files:
            raise FileNotFoundError("Nenhum arquivo de prisões encontrado em data/")
        prisons_file = max(geojson_files, key=os.path.getctime)
    
    PRISONS_DATA = PrisonGeofencing(prisons_file, buffer_meters)
    print("✅ API inicializada!")


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='API de Geofencing para Prisões')
    parser.add_argument('--mode', choices=['api', 'export'], default='api',
                       help='Modo: api (servidor REST) ou export (exportar dados)')
    parser.add_argument('--file', type=str, help='Arquivo com prisões')
    parser.add_argument('--buffer', type=int, default=50,
                       help='Buffer de segurança em metros (padrão: 50)')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                       help='Host da API (padrão: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Porta da API (padrão: 5000)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  API DE GEOFENCING - DETECÇÃO DE TRANSAÇÕES EM PRISÕES")
    print("=" * 60)
    
    if args.mode == 'api':
        # Inicializar e rodar API
        initialize_api(args.file, args.buffer)
        
        print(f"\n🚀 Iniciando servidor em http://{args.host}:{args.port}")
        print("\n📖 Endpoints disponíveis:")
        print(f"  - GET  http://{args.host}:{args.port}/health")
        print(f"  - POST http://{args.host}:{args.port}/api/v1/check-location")
        print(f"  - POST http://{args.host}:{args.port}/api/v1/batch-check")
        print(f"  - POST http://{args.host}:{args.port}/api/v1/nearest-prison")
        print(f"  - GET  http://{args.host}:{args.port}/api/v1/stats")
        print("\n💡 Teste com: curl http://127.0.0.1:5000/health")
        
        app.run(host=args.host, port=args.port, debug=False)
    
    elif args.mode == 'export':
        # Apenas exportar dados
        prisons_file = args.file
        if not prisons_file:
            geojson_files = glob.glob('data/prisons_brazil_*.geojson')
            if not geojson_files:
                print("❌ Nenhum arquivo de prisões encontrado")
                return
            prisons_file = max(geojson_files, key=os.path.getctime)
        
        geofencing = PrisonGeofencing(prisons_file, args.buffer)
        
        os.makedirs('exports', exist_ok=True)
        geofencing.export_geojson_zones('exports/prison_zones.geojson')
        geofencing.export_json_list('exports/prisons_list.json')
        
        print("\n✅ Exports concluídos em exports/")


if __name__ == "__main__":
    main()

