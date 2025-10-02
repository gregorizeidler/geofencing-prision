#!/usr/bin/env python3
"""
Script para criar mapa interativo das prisões do Brasil
"""

import glob
import os
from typing import Optional
import geopandas as gpd
import folium
from folium import plugins
import json


class PrisonMapVisualizer:
    """Cria mapas interativos com Folium"""
    
    def __init__(self, prisons_file: str):
        """
        Args:
            prisons_file: caminho para arquivo GeoJSON/GPKG com prisões
        """
        print(f"📂 Carregando {prisons_file}...")
        self.prisons_gdf = gpd.read_file(prisons_file)
        
        # Centro do Brasil
        self.center = [-14.235, -51.925]
        self.zoom_start = 4
    
    def create_basic_map(self, output_file: str = 'prisons_map.html'):
        """
        Cria mapa básico com todas as prisões
        
        Args:
            output_file: nome do arquivo HTML de saída
        """
        print(f"\n🗺️  Criando mapa básico...")
        
        # Criar mapa base
        m = folium.Map(
            location=self.center,
            zoom_start=self.zoom_start,
            tiles='OpenStreetMap'
        )
        
        # Adicionar camadas de tiles alternativas
        folium.TileLayer('cartodbpositron', name='CartoDB Positron').add_to(m)
        folium.TileLayer('cartodbdark_matter', name='CartoDB Dark').add_to(m)
        
        # Adicionar marcadores para cada prisão
        marker_cluster = plugins.MarkerCluster(name='Prisões (Cluster)').add_to(m)
        
        for idx, prison in self.prisons_gdf.iterrows():
            # Criar popup com informações
            popup_html = self._create_popup_html(prison)
            
            # Ícone personalizado
            icon = folium.Icon(
                color='red',
                icon='institution',
                prefix='fa'
            )
            
            folium.Marker(
                location=[prison.geometry.y, prison.geometry.x],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=prison.get('name', f"Prisão {prison['osm_id']}"),
                icon=icon
            ).add_to(marker_cluster)
        
        # Adicionar layer de todas as prisões sem cluster
        feature_group = folium.FeatureGroup(name='Prisões (Todos)', show=False)
        
        for idx, prison in self.prisons_gdf.iterrows():
            folium.CircleMarker(
                location=[prison.geometry.y, prison.geometry.x],
                radius=6,
                popup=folium.Popup(self._create_popup_html(prison), max_width=300),
                color='darkred',
                fill=True,
                fillColor='red',
                fillOpacity=0.7,
                weight=2
            ).add_to(feature_group)
        
        feature_group.add_to(m)
        
        # Adicionar heatmap
        heat_data = [[prison.geometry.y, prison.geometry.x] for _, prison in self.prisons_gdf.iterrows()]
        plugins.HeatMap(
            heat_data,
            name='Mapa de Calor',
            min_opacity=0.3,
            radius=25,
            blur=35,
            show=False
        ).add_to(m)
        
        # Adicionar controle de camadas
        folium.LayerControl(position='topright', collapsed=False).add_to(m)
        
        # Adicionar fullscreen
        plugins.Fullscreen(
            position='topleft',
            title='Tela Cheia',
            title_cancel='Sair Tela Cheia'
        ).add_to(m)
        
        # Adicionar busca
        plugins.Search(
            layer=marker_cluster,
            search_label='name',
            placeholder='Buscar prisão...',
            collapsed=False,
            position='topleft'
        ).add_to(m)
        
        # Adicionar minimap
        minimap = plugins.MiniMap(toggle_display=True)
        m.add_child(minimap)
        
        # Adicionar legenda
        legend_html = self._create_legend_html()
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Salvar
        m.save(output_file)
        print(f"✓ Mapa salvo: {output_file}")
        print(f"   Total de prisões: {len(self.prisons_gdf)}")
        
        return m
    
    def create_regional_map(self, output_file: str = 'prisons_map_regional.html'):
        """
        Cria mapa com prisões coloridas por região
        
        Args:
            output_file: nome do arquivo HTML de saída
        """
        print(f"\n🗺️  Criando mapa regional...")
        
        # Cores por região
        region_colors = {
            'Norte': 'green',
            'Nordeste': 'orange',
            'Centro-Oeste': 'purple',
            'Sudeste': 'blue',
            'Sul': 'red',
            'Unknown': 'gray'
        }
        
        # Criar mapa base
        m = folium.Map(
            location=self.center,
            zoom_start=self.zoom_start,
            tiles='cartodbpositron'
        )
        
        # Criar feature groups por região
        if 'region' in self.prisons_gdf.columns:
            for region in self.prisons_gdf['region'].unique():
                fg = folium.FeatureGroup(name=f'Região {region}', show=True)
                
                region_prisons = self.prisons_gdf[self.prisons_gdf['region'] == region]
                
                for idx, prison in region_prisons.iterrows():
                    folium.CircleMarker(
                        location=[prison.geometry.y, prison.geometry.x],
                        radius=8,
                        popup=folium.Popup(self._create_popup_html(prison), max_width=300),
                        tooltip=prison.get('name', f"Prisão {prison['osm_id']}"),
                        color=region_colors.get(region, 'gray'),
                        fill=True,
                        fillColor=region_colors.get(region, 'gray'),
                        fillOpacity=0.7,
                        weight=2
                    ).add_to(fg)
                
                fg.add_to(m)
        else:
            # Fallback se não houver região
            for idx, prison in self.prisons_gdf.iterrows():
                folium.CircleMarker(
                    location=[prison.geometry.y, prison.geometry.x],
                    radius=6,
                    popup=folium.Popup(self._create_popup_html(prison), max_width=300),
                    color='red',
                    fill=True,
                    fillOpacity=0.7
                ).add_to(m)
        
        # Controles
        folium.LayerControl(position='topright', collapsed=False).add_to(m)
        plugins.Fullscreen(position='topleft').add_to(m)
        
        # Salvar
        m.save(output_file)
        print(f"✓ Mapa regional salvo: {output_file}")
        
        return m
    
    def create_map_with_infrastructure(
        self,
        infrastructure_files: dict,
        output_file: str = 'prisons_map_infrastructure.html'
    ):
        """
        Cria mapa com prisões e infraestrutura ao redor
        
        Args:
            infrastructure_files: Dict com {tipo: caminho}
            output_file: nome do arquivo HTML de saída
        """
        print(f"\n🗺️  Criando mapa com infraestrutura...")
        
        # Criar mapa base
        m = folium.Map(
            location=self.center,
            zoom_start=self.zoom_start,
            tiles='OpenStreetMap'
        )
        
        # Adicionar prisões
        prisons_fg = folium.FeatureGroup(name='🏛️ Prisões', show=True)
        for idx, prison in self.prisons_gdf.iterrows():
            folium.CircleMarker(
                location=[prison.geometry.y, prison.geometry.x],
                radius=10,
                popup=folium.Popup(self._create_popup_html(prison), max_width=300),
                tooltip=prison.get('name', f"Prisão {prison['osm_id']}"),
                color='darkred',
                fill=True,
                fillColor='red',
                fillOpacity=0.9,
                weight=3
            ).add_to(prisons_fg)
        prisons_fg.add_to(m)
        
        # Adicionar infraestrutura
        infra_config = {
            'buildings': {'color': 'gray', 'icon': '🏢', 'name': 'Prédios'},
            'amenities': {'color': 'blue', 'icon': '📍', 'name': 'Amenidades'},
            'highways': {'color': 'orange', 'icon': '🛣️', 'name': 'Vias'}
        }
        
        for infra_type, filepath in infrastructure_files.items():
            if not os.path.exists(filepath):
                continue
            
            print(f"   Carregando {infra_type}...")
            gdf = gpd.read_file(filepath)
            
            if gdf.empty:
                continue
            
            config = infra_config.get(infra_type, {'color': 'gray', 'icon': '📍', 'name': infra_type})
            
            fg = folium.FeatureGroup(
                name=f"{config['icon']} {config['name']} ({len(gdf)})",
                show=False
            )
            
            # Limitar a 1000 para não sobrecarregar
            sample_size = min(1000, len(gdf))
            gdf_sample = gdf.sample(n=sample_size) if len(gdf) > 1000 else gdf
            
            for idx, feature in gdf_sample.iterrows():
                # Popup simplificado
                tags = {k: v for k, v in feature.items() if k not in ['geometry', 'osm_id', 'osm_type'] and pd.notna(v)}
                popup_text = "<br>".join([f"<b>{k}:</b> {v}" for k, v in list(tags.items())[:5]])
                
                folium.CircleMarker(
                    location=[feature.geometry.y, feature.geometry.x],
                    radius=3,
                    popup=folium.Popup(popup_text, max_width=200),
                    color=config['color'],
                    fill=True,
                    fillOpacity=0.5,
                    weight=1
                ).add_to(fg)
            
            fg.add_to(m)
            
            if len(gdf) > 1000:
                print(f"   ⚠️  Amostrando {sample_size} de {len(gdf)} {infra_type}")
        
        # Controles
        folium.LayerControl(position='topright', collapsed=False).add_to(m)
        plugins.Fullscreen(position='topleft').add_to(m)
        
        # Salvar
        m.save(output_file)
        print(f"✓ Mapa com infraestrutura salvo: {output_file}")
        
        return m
    
    def _create_popup_html(self, prison) -> str:
        """Cria HTML para popup do marcador"""
        name = prison.get('name', 'Sem nome')
        osm_id = prison['osm_id']
        osm_type = prison['osm_type']
        
        html = f"""
        <div style="font-family: Arial; min-width: 200px;">
            <h4 style="margin: 0 0 10px 0; color: #d32f2f;">{name}</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>OSM ID:</b></td><td>{osm_id}</td></tr>
                <tr><td><b>Tipo:</b></td><td>{osm_type}</td></tr>
        """
        
        # Adicionar campos importantes
        important_fields = ['operator', 'capacity', 'addr:city', 'addr:state', 'website', 'phone']
        for field in important_fields:
            if field in prison and pd.notna(prison[field]):
                value = str(prison[field])[:50]  # Limitar tamanho
                html += f'<tr><td><b>{field}:</b></td><td>{value}</td></tr>'
        
        # Link para OSM
        osm_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
        html += f"""
            </table>
            <p style="margin-top: 10px; text-align: center;">
                <a href="{osm_url}" target="_blank" style="color: #1976d2;">
                    Ver no OpenStreetMap →
                </a>
            </p>
        </div>
        """
        
        return html
    
    def _create_legend_html(self) -> str:
        """Cria HTML para legenda"""
        return """
        <div style="
            position: fixed;
            bottom: 50px;
            left: 50px;
            width: 200px;
            background-color: white;
            border: 2px solid gray;
            border-radius: 5px;
            padding: 10px;
            font-family: Arial;
            font-size: 12px;
            z-index: 9999;
        ">
            <h4 style="margin: 0 0 10px 0;">Legenda</h4>
            <p style="margin: 5px 0;">
                <span style="color: red; font-size: 18px;">●</span> Prisões
            </p>
            <hr style="margin: 10px 0;">
            <p style="margin: 5px 0; font-size: 10px; color: gray;">
                Dados do OpenStreetMap<br>
                Tag: amenity=prison
            </p>
        </div>
        """


def main():
    """Função principal"""
    print("=" * 60)
    print("  VISUALIZAÇÃO DE PRISÕES DO BRASIL")
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
    
    # Criar visualizador
    visualizer = PrisonMapVisualizer(latest_file)
    
    # Criar mapas
    visualizer.create_basic_map('prisons_map_brazil.html')
    visualizer.create_regional_map('prisons_map_brazil_regional.html')
    
    # Buscar arquivos de infraestrutura
    timestamp = latest_file.split('_')[-1].replace('.geojson', '')
    infra_files = {
        'buildings': f'data/buildings_near_prisons_{timestamp}.geojson',
        'amenities': f'data/amenities_near_prisons_{timestamp}.geojson',
        'highways': f'data/highways_near_prisons_{timestamp}.geojson',
    }
    
    # Criar mapa com infraestrutura se disponível
    if any(os.path.exists(f) for f in infra_files.values()):
        visualizer.create_map_with_infrastructure(
            infra_files,
            'prisons_map_brazil_infrastructure.html'
        )
    
    print("\n✅ Mapas criados com sucesso!")
    print("\n📂 Arquivos gerados:")
    print("   - prisons_map_brazil.html (mapa básico)")
    print("   - prisons_map_brazil_regional.html (por região)")
    if any(os.path.exists(f) for f in infra_files.values()):
        print("   - prisons_map_brazil_infrastructure.html (com infraestrutura)")
    
    print("\n💡 Abra os arquivos .html no navegador para visualizar!")


if __name__ == "__main__":
    import pandas as pd
    main()

