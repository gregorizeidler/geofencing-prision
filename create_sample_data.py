#!/usr/bin/env python3
"""
Cria dados de amostra para teste da API
"""

import geopandas as gpd
from shapely.geometry import Point, Polygon
import pandas as pd
import os

# Criar alguns exemplos de prisões no Rio de Janeiro
prisons_data = [
    {
        'osm_id': 999001,
        'osm_type': 'way',
        'name': 'Complexo de Gericinó',
        'operator': 'SEAP-RJ',
        'addr:state': 'RJ',
        'addr:city': 'Rio de Janeiro',
        'geometry': Point(-43.4686, -22.8475)  # Coordenadas aproximadas
    },
    {
        'osm_id': 999002,
        'osm_type': 'way',
        'name': 'Presídio Ary Franco',
        'operator': 'SEAP-RJ',
        'addr:state': 'RJ',
        'addr:city': 'Rio de Janeiro',
        'geometry': Point(-43.4120, -22.8550)
    },
    {
        'osm_id': 999003,
        'osm_type': 'way',
        'name': 'Cadeia Pública José Frederico Marques',
        'operator': 'SEAP-RJ',
        'addr:state': 'RJ',
        'addr:city': 'Rio de Janeiro',
        'geometry': Point(-43.3088, -22.8812)
    },
    {
        'osm_id': 999004,
        'osm_type': 'way',
        'name': 'Penitenciária Talavera Bruce',
        'operator': 'SEAP-RJ',
        'addr:state': 'RJ',
        'addr:city': 'Rio de Janeiro',
        'geometry': Point(-43.4650, -22.8460)
    },
    {
        'osm_id': 999005,
        'osm_type': 'way',
        'name': 'Presídio Milton Dias Moreira',
        'operator': 'SEAP-RJ',
        'addr:state': 'RJ',
        'addr:city': 'Japeri',
        'geometry': Point(-43.6518, -22.6425)
    }
]

# Criar GeoDataFrame
gdf = gpd.GeoDataFrame(prisons_data, crs='EPSG:4326')

# Criar diretório
os.makedirs('data', exist_ok=True)

# Salvar
output_file = 'data/prisons_brazil_sample.geojson'
gdf.to_file(output_file, driver='GeoJSON')

print(f"✅ Dados de amostra criados!")
print(f"📁 Arquivo: {output_file}")
print(f"🏛️  {len(gdf)} prisões de exemplo no Rio de Janeiro")
print(f"\n📍 Prisões criadas:")
for _, prison in gdf.iterrows():
    print(f"   - {prison['name']}")
print(f"\n💡 Agora você pode:")
print(f"   1. Iniciar a API: python geofencing_api.py --mode api")
print(f"   2. Testar a API: python test_api.py")
print(f"   3. Ver exemplos: python example_integration.py")

