#!/usr/bin/env python3
"""
Script para análise estatística e espacial de prisões do Brasil
"""

import glob
import os
from typing import Dict, List
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from shapely.geometry import Point
import warnings
warnings.filterwarnings('ignore')


class PrisonAnalyzer:
    """Analisa dados de prisões extraídos do OSM"""
    
    # Divisão de estados por região
    REGIONS = {
        'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
        'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
        'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
        'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
        'Sul': ['PR', 'RS', 'SC']
    }
    
    def __init__(self, prisons_file: str):
        """
        Args:
            prisons_file: caminho para arquivo GeoJSON/GPKG com prisões
        """
        print(f"📂 Carregando {prisons_file}...")
        self.prisons_gdf = gpd.read_file(prisons_file)
        
        # Adicionar coluna de região se não existir
        if 'state' not in self.prisons_gdf.columns:
            self._add_state_info()
    
    def _add_state_info(self):
        """Adiciona informação de estado/região usando geocoding reverso simplificado"""
        # Para análise completa, seria ideal usar um shapefile de estados
        # Por enquanto, vamos tentar extrair da tag 'addr:state' se existir
        
        if 'addr:state' in self.prisons_gdf.columns:
            self.prisons_gdf['state'] = self.prisons_gdf['addr:state']
        else:
            # Tentar inferir do nome ou criar coluna vazia
            self.prisons_gdf['state'] = 'Unknown'
        
        # Adicionar região
        state_to_region = {}
        for region, states in self.REGIONS.items():
            for state in states:
                state_to_region[state] = region
        
        self.prisons_gdf['region'] = self.prisons_gdf['state'].map(state_to_region).fillna('Unknown')
    
    def basic_statistics(self) -> Dict:
        """
        Calcula estatísticas básicas
        
        Returns:
            Dict com estatísticas
        """
        print("\n" + "=" * 60)
        print("📊 ESTATÍSTICAS BÁSICAS")
        print("=" * 60)
        
        stats = {
            'total_prisons': len(self.prisons_gdf),
            'by_type': {},
            'by_state': {},
            'by_region': {},
            'has_name': self.prisons_gdf['name'].notna().sum() if 'name' in self.prisons_gdf.columns else 0,
            'has_operator': self.prisons_gdf['operator'].notna().sum() if 'operator' in self.prisons_gdf.columns else 0,
        }
        
        print(f"\n🏛️  Total de prisões: {stats['total_prisons']}")
        
        # Por tipo de geometria
        print(f"\n📍 Por tipo de representação:")
        type_counts = self.prisons_gdf['osm_type'].value_counts()
        for osm_type, count in type_counts.items():
            pct = (count / stats['total_prisons']) * 100
            print(f"   - {osm_type}: {count} ({pct:.1f}%)")
            stats['by_type'][osm_type] = count
        
        # Por região
        if 'region' in self.prisons_gdf.columns:
            print(f"\n🗺️  Por região:")
            region_counts = self.prisons_gdf['region'].value_counts()
            for region, count in region_counts.items():
                pct = (count / stats['total_prisons']) * 100
                print(f"   - {region}: {count} ({pct:.1f}%)")
                stats['by_region'][region] = count
        
        # Por estado (top 10)
        if 'state' in self.prisons_gdf.columns:
            print(f"\n🏴 Top 10 estados:")
            state_counts = self.prisons_gdf['state'].value_counts().head(10)
            for state, count in state_counts.items():
                pct = (count / stats['total_prisons']) * 100
                print(f"   - {state}: {count} ({pct:.1f}%)")
                stats['by_state'][state] = count
        
        # Qualidade dos dados
        print(f"\n✓ Qualidade dos dados:")
        print(f"   - Com nome: {stats['has_name']} ({stats['has_name']/stats['total_prisons']*100:.1f}%)")
        print(f"   - Com operador: {stats['has_operator']} ({stats['has_operator']/stats['total_prisons']*100:.1f}%)")
        
        # Verificar tags importantes
        important_tags = ['capacity', 'operator', 'name', 'addr:city', 'website']
        print(f"\n🏷️  Tags importantes:")
        for tag in important_tags:
            if tag in self.prisons_gdf.columns:
                count = self.prisons_gdf[tag].notna().sum()
                pct = (count / stats['total_prisons']) * 100
                print(f"   - {tag}: {count} ({pct:.1f}%)")
        
        return stats
    
    def analyze_clustering(self, distance_km: float = 50) -> pd.DataFrame:
        """
        Analisa clusters de prisões (proximidade)
        
        Args:
            distance_km: distância em km para considerar cluster
            
        Returns:
            DataFrame com prisões e seus vizinhos próximos
        """
        print(f"\n🎯 Analisando clusters (distância < {distance_km}km)...")
        
        # Converter para projeção métrica (Web Mercator) para cálculo de distância
        gdf_metric = self.prisons_gdf.to_crs(epsg=3857)
        
        # Criar buffer
        buffer_meters = distance_km * 1000
        gdf_metric['buffer'] = gdf_metric.geometry.buffer(buffer_meters)
        
        # Contar vizinhos
        neighbors = []
        for idx, prison in gdf_metric.iterrows():
            intersecting = gdf_metric[gdf_metric.geometry.within(prison['buffer'])]
            neighbor_count = len(intersecting) - 1  # Excluir ela mesma
            
            if neighbor_count > 0:
                neighbors.append({
                    'osm_id': prison['osm_id'],
                    'name': prison.get('name', 'Sem nome'),
                    'neighbors': neighbor_count
                })
        
        if neighbors:
            df_neighbors = pd.DataFrame(neighbors).sort_values('neighbors', ascending=False)
            print(f"\n   {len(df_neighbors)} prisões têm vizinhos próximos")
            print(f"\n   Top 5 com mais vizinhos:")
            for _, row in df_neighbors.head().iterrows():
                print(f"   - {row['name']}: {row['neighbors']} vizinhos")
            return df_neighbors
        else:
            print(f"   Nenhum cluster encontrado")
            return pd.DataFrame()
    
    def analyze_infrastructure(self, infra_files: Dict[str, str]) -> Dict:
        """
        Analisa infraestrutura ao redor das prisões
        
        Args:
            infra_files: Dict com {tipo: caminho_arquivo}
            
        Returns:
            Dict com estatísticas de infraestrutura
        """
        print("\n" + "=" * 60)
        print("🏗️  ANÁLISE DE INFRAESTRUTURA")
        print("=" * 60)
        
        stats = {}
        
        for infra_type, filepath in infra_files.items():
            if not os.path.exists(filepath):
                continue
            
            print(f"\n📍 Analisando {infra_type}...")
            gdf = gpd.read_file(filepath)
            
            if gdf.empty:
                continue
            
            stats[infra_type] = {
                'total': len(gdf),
                'by_category': {}
            }
            
            print(f"   Total: {len(gdf)}")
            
            # Análise por subcategoria (se aplicável)
            if infra_type == 'amenities' and 'amenity' in gdf.columns:
                top_amenities = gdf['amenity'].value_counts().head(10)
                print(f"   Top amenities:")
                for amenity, count in top_amenities.items():
                    print(f"      - {amenity}: {count}")
                    stats[infra_type]['by_category'][amenity] = count
            
            elif infra_type == 'buildings' and 'building' in gdf.columns:
                building_types = gdf['building'].value_counts().head(10)
                print(f"   Tipos de prédios:")
                for btype, count in building_types.items():
                    print(f"      - {btype}: {count}")
                    stats[infra_type]['by_category'][btype] = count
            
            elif infra_type == 'highways' and 'highway' in gdf.columns:
                highway_types = gdf['highway'].value_counts().head(10)
                print(f"   Tipos de vias:")
                for htype, count in highway_types.items():
                    print(f"      - {htype}: {count}")
                    stats[infra_type]['by_category'][htype] = count
        
        return stats
    
    def generate_visualizations(self, output_dir: str = 'reports'):
        """
        Gera visualizações estatísticas
        
        Args:
            output_dir: diretório para salvar gráficos
        """
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n📈 Gerando visualizações em {output_dir}/...")
        
        sns.set_style('whitegrid')
        
        # 1. Prisões por região
        if 'region' in self.prisons_gdf.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            region_counts = self.prisons_gdf['region'].value_counts()
            region_counts.plot(kind='bar', ax=ax, color='steelblue')
            ax.set_title('Prisões por Região - Brasil', fontsize=16, fontweight='bold')
            ax.set_xlabel('Região', fontsize=12)
            ax.set_ylabel('Número de Prisões', fontsize=12)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'{output_dir}/prisons_by_region.png', dpi=300)
            print("   ✓ prisons_by_region.png")
            plt.close()
        
        # 2. Top 15 estados
        if 'state' in self.prisons_gdf.columns:
            fig, ax = plt.subplots(figsize=(12, 6))
            state_counts = self.prisons_gdf['state'].value_counts().head(15)
            state_counts.plot(kind='barh', ax=ax, color='coral')
            ax.set_title('Top 15 Estados com Mais Prisões', fontsize=16, fontweight='bold')
            ax.set_xlabel('Número de Prisões', fontsize=12)
            ax.set_ylabel('Estado', fontsize=12)
            plt.tight_layout()
            plt.savefig(f'{output_dir}/prisons_by_state_top15.png', dpi=300)
            print("   ✓ prisons_by_state_top15.png")
            plt.close()
        
        # 3. Distribuição espacial (scatter)
        fig, ax = plt.subplots(figsize=(12, 10))
        self.prisons_gdf.plot(ax=ax, markersize=10, color='red', alpha=0.6)
        ax.set_title('Distribuição Espacial das Prisões - Brasil', fontsize=16, fontweight='bold')
        ax.set_xlabel('Longitude', fontsize=12)
        ax.set_ylabel('Latitude', fontsize=12)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/prisons_spatial_distribution.png', dpi=300)
        print("   ✓ prisons_spatial_distribution.png")
        plt.close()
        
        print("✅ Visualizações geradas!")


def main():
    """Função principal"""
    print("=" * 60)
    print("  ANÁLISE DE PRISÕES DO BRASIL")
    print("=" * 60)
    
    # Buscar arquivo mais recente
    geojson_files = glob.glob('data/prisons_brazil_*.geojson')
    
    if not geojson_files:
        print("❌ Nenhum arquivo de prisões encontrado em data/")
        print("   Execute primeiro: python extract_prisons.py")
        return
    
    # Usar o mais recente
    latest_file = max(geojson_files, key=os.path.getctime)
    print(f"📂 Usando arquivo: {latest_file}")
    
    # Criar analisador
    analyzer = PrisonAnalyzer(latest_file)
    
    # Estatísticas básicas
    stats = analyzer.basic_statistics()
    
    # Análise de clusters
    analyzer.analyze_clustering(distance_km=50)
    
    # Buscar arquivos de infraestrutura
    timestamp = latest_file.split('_')[-1].replace('.geojson', '')
    infra_files = {
        'buildings': f'data/buildings_near_prisons_{timestamp}.geojson',
        'amenities': f'data/amenities_near_prisons_{timestamp}.geojson',
        'highways': f'data/highways_near_prisons_{timestamp}.geojson',
    }
    
    # Analisar infraestrutura se disponível
    infra_available = any(os.path.exists(f) for f in infra_files.values())
    if infra_available:
        analyzer.analyze_infrastructure(infra_files)
    else:
        print("\n⚠️  Arquivos de infraestrutura não encontrados")
        print("   Execute extract_prisons.py com extração de infraestrutura")
    
    # Gerar visualizações
    analyzer.generate_visualizations()
    
    print("\n✅ Análise concluída!")


if __name__ == "__main__":
    main()

