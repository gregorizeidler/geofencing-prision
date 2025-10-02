#!/usr/bin/env python3
"""
Script para extrair todas as prisões do Brasil do OpenStreetMap
usando a Overpass API e analisar infraestrutura ao redor.
"""

import json
import time
import requests
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point, Polygon, MultiPolygon, shape
import pandas as pd
from tqdm import tqdm


class OSMPrisonExtractor:
    """Extrai dados de prisões do OpenStreetMap via Overpass API"""
    
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    
    # Bounding box do Brasil: [min_lat, min_lon, max_lat, max_lon]
    BRAZIL_BBOX = (-33.75, -73.99, 5.27, -34.79)
    
    def __init__(self, timeout: int = 180):
        """
        Args:
            timeout: timeout em segundos para queries Overpass
        """
        self.timeout = timeout
        self.session = requests.Session()
        
    def _execute_overpass_query(self, query: str, retry: int = 3) -> Dict:
        """
        Executa query Overpass com retry em caso de erro
        
        Args:
            query: Query Overpass QL
            retry: número de tentativas
            
        Returns:
            Resultado JSON da API
        """
        for attempt in range(retry):
            try:
                response = self.session.post(
                    self.OVERPASS_URL,
                    data={'data': query},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, json.JSONDecodeError) as e:
                if attempt < retry - 1:
                    wait_time = (attempt + 1) * 10
                    print(f"Erro na query, tentando novamente em {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    raise
        
    def extract_prisons(self) -> gpd.GeoDataFrame:
        """
        Extrai todas as prisões do Brasil
        
        Returns:
            GeoDataFrame com prisões
        """
        print("🔍 Extraindo prisões do Brasil...")
        
        bbox_str = f"{self.BRAZIL_BBOX[0]},{self.BRAZIL_BBOX[1]},{self.BRAZIL_BBOX[2]},{self.BRAZIL_BBOX[3]}"
        
        query = f"""
        [out:json][timeout:{self.timeout}][bbox:{bbox_str}];
        (
          node["amenity"="prison"];
          way["amenity"="prison"];
          relation["amenity"="prison"];
        );
        out center tags geom;
        """
        
        result = self._execute_overpass_query(query)
        
        return self._parse_osm_elements(result['elements'], 'prison')
    
    def extract_nearby_infrastructure(
        self, 
        prison_gdf: gpd.GeoDataFrame, 
        radius_meters: int = 500
    ) -> Dict[str, gpd.GeoDataFrame]:
        """
        Extrai infraestrutura ao redor de cada prisão
        
        Args:
            prison_gdf: GeoDataFrame com prisões
            radius_meters: raio em metros para busca
            
        Returns:
            Dict com GeoDataFrames de buildings, amenities, highways
        """
        print(f"\n🏗️  Extraindo infraestrutura num raio de {radius_meters}m...")
        
        results = {
            'buildings': [],
            'amenities': [],
            'highways': []
        }
        
        # Processar por lotes para não sobrecarregar a API
        batch_size = 10
        
        for i in tqdm(range(0, len(prison_gdf), batch_size)):
            batch = prison_gdf.iloc[i:i+batch_size]
            
            # Criar query around para o batch
            around_coords = []
            for _, prison in batch.iterrows():
                lat = prison.geometry.y
                lon = prison.geometry.x
                around_coords.append(f"  around:{radius_meters},{lat},{lon}")
            
            around_str = ";\n".join(around_coords)
            
            query = f"""
            [out:json][timeout:{self.timeout}];
            (
              node(
{around_str}
              )["building"];
              way(
{around_str}
              )["building"];
              relation(
{around_str}
              )["building"];
              
              node(
{around_str}
              )["amenity"];
              way(
{around_str}
              )["amenity"];
              relation(
{around_str}
              )["amenity"];
              
              way(
{around_str}
              )["highway"];
            );
            out center tags geom;
            """
            
            try:
                result = self._execute_overpass_query(query)
                elements = result['elements']
                
                # Separar por tipo
                buildings = [e for e in elements if 'building' in e.get('tags', {})]
                amenities = [e for e in elements if 'amenity' in e.get('tags', {}) and e['tags']['amenity'] != 'prison']
                highways = [e for e in elements if 'highway' in e.get('tags', {})]
                
                if buildings:
                    results['buildings'].extend(buildings)
                if amenities:
                    results['amenities'].extend(amenities)
                if highways:
                    results['highways'].extend(highways)
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"Erro no batch {i//batch_size + 1}: {e}")
                continue
        
        # Converter para GeoDataFrames
        gdf_dict = {}
        for key, elements in results.items():
            if elements:
                gdf_dict[key] = self._parse_osm_elements(elements, key)
            else:
                gdf_dict[key] = gpd.GeoDataFrame()
        
        return gdf_dict
    
    def _parse_osm_elements(self, elements: List[Dict], element_type: str) -> gpd.GeoDataFrame:
        """
        Converte elementos OSM em GeoDataFrame
        
        Args:
            elements: lista de elementos OSM
            element_type: tipo do elemento (para logging)
            
        Returns:
            GeoDataFrame
        """
        features = []
        
        for element in elements:
            try:
                # Extrair geometria
                geom = None
                
                if element['type'] == 'node':
                    geom = Point(element['lon'], element['lat'])
                
                elif element['type'] == 'way':
                    if 'geometry' in element:
                        coords = [(node['lon'], node['lat']) for node in element['geometry']]
                        if len(coords) >= 3 and coords[0] == coords[-1]:
                            geom = Polygon(coords)
                        else:
                            # Usar center como fallback
                            if 'center' in element:
                                geom = Point(element['center']['lon'], element['center']['lat'])
                    elif 'center' in element:
                        geom = Point(element['center']['lon'], element['center']['lat'])
                
                elif element['type'] == 'relation':
                    if 'center' in element:
                        geom = Point(element['center']['lon'], element['center']['lat'])
                
                if geom is None:
                    continue
                
                # Extrair tags
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
                continue
        
        if not features:
            return gpd.GeoDataFrame()
        
        gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')
        print(f"✓ {len(gdf)} {element_type} extraídos")
        
        return gdf
    
    def save_data(
        self, 
        prisons_gdf: gpd.GeoDataFrame,
        infrastructure: Optional[Dict[str, gpd.GeoDataFrame]] = None,
        output_dir: str = 'data'
    ):
        """
        Salva dados em múltiplos formatos
        
        Args:
            prisons_gdf: GeoDataFrame com prisões
            infrastructure: Dict com infraestrutura
            output_dir: diretório de saída
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        print(f"\n💾 Salvando dados em {output_dir}/...")
        
        # Salvar prisões
        prisons_gdf.to_file(f"{output_dir}/prisons_brazil_{timestamp}.geojson", driver='GeoJSON')
        prisons_gdf.to_file(f"{output_dir}/prisons_brazil_{timestamp}.gpkg", driver='GPKG', layer='prisons')
        
        # Salvar CSV também (sem geometria complexa)
        prisons_csv = prisons_gdf.copy()
        prisons_csv['latitude'] = prisons_csv.geometry.y
        prisons_csv['longitude'] = prisons_csv.geometry.x
        prisons_csv.drop(columns=['geometry']).to_csv(
            f"{output_dir}/prisons_brazil_{timestamp}.csv", 
            index=False
        )
        
        print(f"✓ Prisões salvas ({len(prisons_gdf)} registros)")
        
        # Salvar infraestrutura
        if infrastructure:
            for key, gdf in infrastructure.items():
                if not gdf.empty:
                    gdf.to_file(
                        f"{output_dir}/{key}_near_prisons_{timestamp}.geojson", 
                        driver='GeoJSON'
                    )
                    print(f"✓ {key.capitalize()} salvos ({len(gdf)} registros)")


def main():
    """Função principal"""
    print("=" * 60)
    print("  EXTRAÇÃO DE PRISÕES DO BRASIL - OpenStreetMap")
    print("=" * 60)
    
    extractor = OSMPrisonExtractor(timeout=180)
    
    # Extrair prisões
    prisons_gdf = extractor.extract_prisons()
    
    if prisons_gdf.empty:
        print("❌ Nenhuma prisão encontrada!")
        return
    
    print(f"\n📊 Total de prisões encontradas: {len(prisons_gdf)}")
    
    # Perguntar se quer extrair infraestrutura (demora muito)
    print("\n" + "=" * 60)
    print("⚠️  ATENÇÃO: Extrair infraestrutura ao redor pode demorar HORAS")
    print("   para todas as prisões do Brasil!")
    extract_infra = input("Deseja extrair infraestrutura ao redor? (s/N): ").lower() == 's'
    
    infrastructure = None
    if extract_infra:
        radius = int(input("Raio em metros (padrão 500): ") or "500")
        infrastructure = extractor.extract_nearby_infrastructure(prisons_gdf, radius)
    
    # Salvar dados
    extractor.save_data(prisons_gdf, infrastructure)
    
    print("\n✅ Extração concluída!")
    print("\nPróximos passos:")
    print("  - Execute 'python analyze_prisons.py' para análises estatísticas")
    print("  - Execute 'python visualize_prisons.py' para criar mapas interativos")


if __name__ == "__main__":
    main()

