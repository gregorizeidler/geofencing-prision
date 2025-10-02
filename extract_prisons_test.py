#!/usr/bin/env python3
"""
Script de teste rápido - extrai prisões de uma área menor (Rio de Janeiro)
Use este script para testar antes de rodar no Brasil inteiro!
"""

import json
import time
import requests
from typing import Dict, List
import geopandas as gpd
from shapely.geometry import Point, Polygon
import pandas as pd


class QuickTestExtractor:
    """Extrator rápido para teste"""
    
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    
    # Bounding box do Rio de Janeiro (cidade)
    RIO_BBOX = (-23.08, -43.80, -22.75, -43.09)
    
    def __init__(self):
        self.session = requests.Session()
    
    def extract_prisons_rio(self) -> gpd.GeoDataFrame:
        """Extrai prisões do Rio de Janeiro"""
        print("🔍 Extraindo prisões do Rio de Janeiro...")
        
        bbox_str = f"{self.RIO_BBOX[0]},{self.RIO_BBOX[1]},{self.RIO_BBOX[2]},{self.RIO_BBOX[3]}"
        
        query = f"""
        [out:json][timeout:60][bbox:{bbox_str}];
        (
          node["amenity"="prison"];
          way["amenity"="prison"];
          relation["amenity"="prison"];
        );
        out center tags geom;
        """
        
        response = self.session.post(
            self.OVERPASS_URL,
            data={'data': query},
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        features = []
        for element in result['elements']:
            try:
                if element['type'] == 'node':
                    geom = Point(element['lon'], element['lat'])
                elif 'center' in element:
                    geom = Point(element['center']['lon'], element['center']['lat'])
                else:
                    continue
                
                tags = element.get('tags', {})
                feature = {
                    'osm_id': element['id'],
                    'osm_type': element['type'],
                    'geometry': geom,
                    **tags
                }
                features.append(feature)
            except Exception as e:
                print(f"Erro ao processar elemento {element.get('id')}: {e}")
        
        gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')
        print(f"✓ {len(gdf)} prisões encontradas no Rio de Janeiro")
        
        return gdf
    
    def extract_nearby_quick(self, prison_gdf: gpd.GeoDataFrame) -> Dict[str, gpd.GeoDataFrame]:
        """Extrai infraestrutura ao redor (versão rápida)"""
        print(f"\n🏗️  Extraindo infraestrutura ao redor (500m)...")
        
        if len(prison_gdf) == 0:
            return {}
        
        # Pegar coordenadas de todas as prisões
        coords = []
        for _, prison in prison_gdf.iterrows():
            coords.append(f"around:500,{prison.geometry.y},{prison.geometry.x}")
        
        around_str = ";".join(coords)
        
        query = f"""
        [out:json][timeout:60];
        (
          node({around_str})["building"];
          way({around_str})["building"];
          node({around_str})["amenity"]["amenity"!="prison"];
          way({around_str})["amenity"]["amenity"!="prison"];
          way({around_str})["highway"];
        );
        out center tags geom;
        """
        
        response = self.session.post(
            self.OVERPASS_URL,
            data={'data': query},
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        # Separar por tipo
        buildings = []
        amenities = []
        highways = []
        
        for element in result['elements']:
            try:
                if element['type'] == 'node':
                    geom = Point(element['lon'], element['lat'])
                elif 'center' in element:
                    geom = Point(element['center']['lon'], element['center']['lat'])
                else:
                    continue
                
                tags = element.get('tags', {})
                feature = {
                    'osm_id': element['id'],
                    'osm_type': element['type'],
                    'geometry': geom,
                    **tags
                }
                
                if 'building' in tags:
                    buildings.append(feature)
                elif 'amenity' in tags:
                    amenities.append(feature)
                elif 'highway' in tags:
                    highways.append(feature)
                    
            except Exception as e:
                continue
        
        result_gdfs = {}
        if buildings:
            result_gdfs['buildings'] = gpd.GeoDataFrame(buildings, crs='EPSG:4326')
            print(f"✓ {len(buildings)} prédios")
        if amenities:
            result_gdfs['amenities'] = gpd.GeoDataFrame(amenities, crs='EPSG:4326')
            print(f"✓ {len(amenities)} amenidades")
        if highways:
            result_gdfs['highways'] = gpd.GeoDataFrame(highways, crs='EPSG:4326')
            print(f"✓ {len(highways)} vias")
        
        return result_gdfs
    
    def save_test_data(self, prisons_gdf: gpd.GeoDataFrame, infrastructure: Dict):
        """Salva dados de teste"""
        import os
        os.makedirs('data', exist_ok=True)
        
        print(f"\n💾 Salvando dados em data/...")
        
        # Salvar prisões
        prisons_gdf.to_file('data/prisons_rio_test.geojson', driver='GeoJSON')
        print("✓ prisons_rio_test.geojson")
        
        # Salvar infraestrutura
        for key, gdf in infrastructure.items():
            filename = f'data/{key}_rio_test.geojson'
            gdf.to_file(filename, driver='GeoJSON')
            print(f"✓ {key}_rio_test.geojson")


def main():
    """Função principal"""
    print("=" * 60)
    print("  TESTE RÁPIDO - RIO DE JANEIRO")
    print("=" * 60)
    print("\n💡 Use este script para testar antes de rodar no Brasil inteiro!")
    print("   Tempo estimado: 1-2 minutos\n")
    
    extractor = QuickTestExtractor()
    
    # Extrair prisões
    prisons_gdf = extractor.extract_prisons_rio()
    
    if prisons_gdf.empty:
        print("❌ Nenhuma prisão encontrada no Rio de Janeiro")
        return
    
    # Mostrar informações
    print(f"\n📊 Prisões encontradas:")
    for idx, prison in prisons_gdf.iterrows():
        name = prison.get('name', 'Sem nome')
        osm_type = prison.get('osm_type', 'unknown')
        print(f"  - {name} ({osm_type})")
    
    # Perguntar sobre infraestrutura
    print("\n" + "=" * 60)
    extract_infra = input("Extrair infraestrutura ao redor? (S/n): ").lower() != 'n'
    
    infrastructure = {}
    if extract_infra:
        infrastructure = extractor.extract_nearby_quick(prisons_gdf)
    
    # Salvar
    extractor.save_test_data(prisons_gdf, infrastructure)
    
    print("\n✅ Teste concluído!")
    print("\n📂 Próximos passos:")
    print("  1. Verifique os arquivos em data/")
    print("  2. Execute: python visualize_prisons.py (ajuste o nome do arquivo)")
    print("  3. Se tudo estiver OK, execute: python extract_prisons.py (Brasil inteiro)")


if __name__ == "__main__":
    main()

