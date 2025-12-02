# 🏦 Sistema de Geofencing Bancário - Detecção de Transações em Prisões

**Sistema completo de geofencing para bancos e fintechs** detectarem e bloquearem transações financeiras realizadas dentro de prisões no Brasil, usando dados do OpenStreetMap.

<div align="center">   

### Sistema de Geofencing com Polígonos Precisos       

| ⛔ Dentro do Presídio | ✅ Fora do Presídio |
|:---:|:---:|
| **BLOQUEADO** | **LIBERADO** |
| Previne fraudes/golpes/crimes | Protege comércios e moradores próximos |

Performance: 1.12ms/request | Cobertura: Brasil completo

[📸 Ver Exemplos](#-precisão-com-polígonos---casos-reais) | [🚀 Começar](#-quick-start) | [🔌 API](#-api-rest---endpoints)

</div>
<img width="2816" height="1536" alt="Gemini_Generated_Image_9f5mjq9f5mjq9f5m (1)" src="https://github.com/user-attachments/assets/c1697f77-5bc7-43bd-8bc2-d93e6662b893" />
<img width="2816" height="1536" alt="Gemini_Generated_Image_9f5mjq9f5mjq9f5m (2)" src="https://github.com/user-attachments/assets/7e85f33c-fa49-40da-a228-4dc50c01dc95" />

---

## 🔍 Como Funciona

### Fluxo de Validação de Transação

```mermaid
flowchart TD
    A[📱 Transação Bancária] --> B[POST /api/v1/check-location]
    B --> C[Carregar GeoJSON<br/>com prisões]
    C --> D[Converter coordenadas<br/>para Point objeto]
    D --> E{Iterar sobre<br/>polígonos de prisões}
    E --> F{Ponto está dentro<br/>do polígono?}
    F -->|SIM| G[⛔ inside_prison: true]
    F -->|NÃO| H[✅ inside_prison: false]
    G --> I[risk_level: HIGH<br/>action: BLOCK]
    H --> J[risk_level: LOW<br/>action: ALLOW]
    I --> K[Retornar JSON]
    J --> K
    K --> L[Sistema Bancário<br/>executa ação]
    
    style G fill:#e74c3c,color:#fff
    style H fill:#27ae60,color:#fff
    style I fill:#c0392b,color:#fff
    style J fill:#229954,color:#fff
```

### Integração com Sistemas Bancários

```mermaid
sequenceDiagram
    participant Bank as Sistema Bancário
    participant API as Geofencing API
    participant Data as GeoJSON Database
    
    Note over Bank,Data: Validação Individual
    Bank->>API: POST /api/v1/check-location<br/>{latitude, longitude}
    API->>Data: Carregar polígonos das prisões
    Data-->>API: Lista de prisões carregada
    API->>API: Executar point-in-polygon check
    API-->>Bank: {inside_prison, risk_level, action, prison_info}
    
    Note over Bank,Data: Validação em Lote (Batch)
    Bank->>API: POST /api/v1/batch-check<br/>[{lat,lon}, {lat,lon}, ...]
    loop Para cada localização
        API->>Data: Verificar polígono
    end
    API-->>Bank: [{result1}, {result2}, {result3}, ...]
```

### Pipeline de Dados

```mermaid
graph LR
    A[🌍 OpenStreetMap] -->|Overpass API| B[extract_prisons.py]
    B -->|Query: amenity=prison| C[Raw OSM Data]
    C -->|GeoPandas Processing| D[prisons_brazil.geojson]
    D -->|Load at Startup| E[geofencing_api.py]
    E -->|Flask REST API| F[HTTP Endpoints]
    F -->|JSON Response| G[Sistema Bancário]
    
    style A fill:#7EBC6F,color:#fff
    style D fill:#3498db,color:#fff
    style F fill:#e74c3c,color:#fff
    style G fill:#27ae60,color:#fff
```

---

## 🎯 Caso de Uso Principal

**PROBLEMA**: Transações financeiras ilícitas (PIX, TED, cartões) realizadas dentro de prisões por criminosos, facilitando operações como:
- Extorsão e resgate
- Lavagem de dinheiro
- Comércio ilegal dentro de presídios
- Fraudes e golpes

**SOLUÇÃO**: Sistema de geofencing em tempo real que:
- ✅ Detecta se coordenadas GPS estão DENTRO de uma prisão
- ✅ Evita falsos positivos (não bloqueia prédios/ruas ao redor)
- ✅ API REST para integração bancária
- ✅ Export em formatos padrão (GeoJSON, JSON)
- ✅ Cobertura nacional (todas as prisões do Brasil)
- ✅ Atualização via dados abertos do OSM

## 🎯 Precisão com Polígonos - Casos Reais

### O Problema

Sistemas de geofencing tradicionais usam raios circulares que bloqueiam grandes áreas, afetando comércios e clientes legítimos próximos aos presídios. Isso gera falsos positivos e prejuízo operacional.

### A Solução

Este sistema usa **polígonos precisos** extraídos do OpenStreetMap, identificando o perímetro exato de cada presídio:

```mermaid
graph TB
    subgraph este["✅ POLÍGONO EXATO"]
        direction TB
        P2[🏛️ Prisão] --> POL[Perímetro Real OSM]
        POL -.->|Liberado| OK1[🏪 Comércio]
        POL -.->|Liberado| OK2[🏘️ Residências]
        POL -.->|Liberado| OK3[🏥 Hospital]
        OK1 --> S1[✅ Sem Impacto]
        OK2 --> S2[✅ Sem Impacto]
        OK3 --> S3[✅ Sem Impacto]
    end
    
    subgraph trad["❌ RAIO CIRCULAR"]
        direction TB
        P1[🏛️ Prisão] --> R1[Raio 500m]
        R1 -.->|Bloqueado| B1[🏪 Comércio]
        R1 -.->|Bloqueado| B2[🏘️ Residências]
        R1 -.->|Bloqueado| B3[🏥 Hospital]
        B1 --> FP1[❌ Falso Positivo]
        B2 --> FP2[❌ Falso Positivo]
        B3 --> FP3[❌ Falso Positivo]
    end
    
    style este fill:#d4edda,stroke:#28a745,stroke-width:4px,color:#000
    style trad fill:#ffdddd,stroke:#d32f2f,stroke-width:4px,color:#000
    style P1 fill:#d32f2f,color:#fff,stroke:#000,stroke-width:2px
    style P2 fill:#d32f2f,color:#fff,stroke:#000,stroke-width:2px
    style R1 fill:#999,color:#fff,stroke:#000,stroke-width:2px
    style POL fill:#555,color:#fff,stroke:#000,stroke-width:2px
    style B1 fill:#fff,color:#000,stroke:#000,stroke-width:2px
    style B2 fill:#fff,color:#000,stroke:#000,stroke-width:2px
    style B3 fill:#fff,color:#000,stroke:#000,stroke-width:2px
    style OK1 fill:#fff,color:#000,stroke:#000,stroke-width:2px
    style OK2 fill:#fff,color:#000,stroke:#000,stroke-width:2px
    style OK3 fill:#fff,color:#000,stroke:#000,stroke-width:2px
    style FP1 fill:#f44336,color:#fff,stroke:#000,stroke-width:2px
    style FP2 fill:#f44336,color:#fff,stroke:#000,stroke-width:2px
    style FP3 fill:#f44336,color:#fff,stroke:#000,stroke-width:2px
    style S1 fill:#4caf50,color:#fff,stroke:#000,stroke-width:2px
    style S2 fill:#4caf50,color:#fff,stroke:#000,stroke-width:2px
    style S3 fill:#4caf50,color:#fff,stroke:#000,stroke-width:2px
```

| Cenário | Resultado |
|---------|-----------|
| Transação DENTRO do presídio | ⛔ BLOQUEADA |
| Transação FORA do perímetro | ✅ LIBERADA |
| Transação em área segura | ✅ LIBERADA |

### 📸 Exemplos de Casos

<table>
  <tr>
    <td align="center" width="50%">
      <img src="screenshots/Transacao dentro Penitenciária Estadual de Charqueadas RS.png" width="100%"/>
      <br/>
      <b>⛔ BLOQUEADO</b>: Dentro da Penitenciária Estadual de Charqueadas - RS
    </td>
    <td align="center" width="50%">
      <img src="screenshots/transacoes fora presidio porto alegre 5 a 10 metros.png" width="100%"/>
      <br/>
      <b>✅ LIBERADO</b>: Fora do presídio - Porto Alegre
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <img src="screenshots/Transacoes dentro Penitenciária Estadual de SANTA MARIA RS.png" width="100%"/>
      <br/>
      <b>⛔ BLOQUEADO</b>: Penitenciária Estadual de Santa Maria - RS
    </td>
    <td align="center" width="50%">
      <img src="screenshots/Transacoes 5 a 10 metros fora presidio sorocaba.png" width="100%"/>
      <br/>
      <b>✅ LIBERADO</b>: Fora do presídio - Sorocaba - SP
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <img src="screenshots/Transacoes dentro complexo prisional em fortaleza.png" width="100%"/>
      <br/>
      <b>⛔ BLOQUEADO</b>: Complexo Prisional - Fortaleza - CE
    </td>
    <td align="center" width="50%">
      <img src="screenshots/Transacoes 5 - 10 metros presidio osasco.png" width="100%"/>
      <br/>
      <b>✅ LIBERADO</b>: Fora do presídio - Osasco - SP
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <img src="screenshots/transacoes dentro Funcadacao casa praia grande.png" width="100%"/>
      <br/>
      <b>⛔ BLOQUEADO</b>: Fundação Casa - Praia Grande - SP
    </td>
    <td align="center" width="50%">
      <img src="screenshots/TRANSACOES 5-10 Metros proximo bangu rj.png" width="100%"/>
      <br/>
      <b>✅ LIBERADO</b>: Fora do presídio - Bangu - RJ
    </td>
  </tr>
  <tr>
    <td align="center" colspan="2">
      <img src="screenshots/MAPA geral brasil transacoes presidios.png" width="80%"/>
      <br/>
      <b>🗺️ Cobertura Nacional</b>: Mapa do Brasil com localização de presídios
    </td>
  </tr>
</table>

### 💡 Diferencial

**Sistemas tradicionais (raio circular):**
- Bloqueio de 500m ao redor → dezenas de comércios afetados
- Falsos positivos → clientes legítimos bloqueados
- Prejuízo operacional → reversões e reclamações

**Este sistema (polígono preciso):**
- Bloqueio apenas do perímetro real do presídio
- Comércios vizinhos operam normalmente
- Segurança sem prejuízo à operação

---

## 📋 Funcionalidades

### Lógica de Decisão

```mermaid
flowchart LR
    A[Coordenadas GPS] --> B{Verificar<br/>Polígono}
    B -->|Dentro| C[⛔ HIGH RISK]
    B -->|Fora| D[✅ LOW RISK]
    
    C --> E[action: BLOCK]
    D --> F[action: ALLOW]
    
    E --> G[Retornar info<br/>da prisão]
    F --> H[Retornar<br/>localização OK]
    
    style A fill:#3498db,color:#fff
    style C fill:#e74c3c,color:#fff
    style D fill:#27ae60,color:#fff
    style E fill:#c0392b,color:#fff
    style F fill:#229954,color:#fff
```

### Para Bancos/Fintechs:
- ✅ **API REST** para validação de transações em tempo real
- ✅ **Performance excelente** - 1.12ms por request (892 req/s)
- ✅ **Polígonos precisos** - Sem falsos positivos
- ✅ **Batch processing** para análise de múltiplas transações
- ✅ **Buffer de precisão ajustável** (padrão: 50m)
- ✅ **Identificação da prisão** (nome, operador, localização)
- ✅ **Níveis de risco** (HIGH/LOW)
- ✅ **Ações recomendadas** (BLOCK/ALLOW)
- ✅ **Exemplos de integração** - Python, Node.js, Java

### Para Análise e Compliance:
- ✅ Extração de dados de prisões do Brasil (OSM)
- ✅ Análises estatísticas por estado/região
- ✅ Mapas interativos e visualizações
- ✅ Relatórios de cobertura
- ✅ Monitoramento de mudanças

## 🚀 Quick Start

### Pré-requisitos
- Python 3.8+
- pip

### Instalação

```bash
# Clone ou baixe o projeto
cd testessss

# Instale dependências
pip install -r requirements.txt

# Execute extração de dados (primeira vez)
python extract_prisons.py

# Inicie a API de geofencing
python geofencing_api.py --mode api
```

### Teste Rápido

```bash
# Testar com dados do Rio de Janeiro (1-2 minutos)
python extract_prisons_test.py

# Testar API
curl http://127.0.0.1:5000/health

# Testar validação de localização
curl -X POST http://127.0.0.1:5000/api/v1/check-location \
  -H "Content-Type: application/json" \
  -d '{"latitude": -22.9068, "longitude": -43.1729}'
```

## 📖 Guia de Uso

### 🏦 Para Integração Bancária (Caso de Uso Principal)

#### 1. Extrair Dados das Prisões

Primeira vez - extrair todas as prisões do Brasil:

```bash
python extract_prisons.py
```

Este script:
- Busca todas as prisões com tag `amenity=prison` no Brasil
- Salva os dados em `data/` nos formatos:
  - GeoJSON (para API e mapas)
  - GeoPackage (para análise espacial)
  - CSV (para análise tabular)

⚠️ **Para geofencing bancário**: responda **NÃO** quando perguntar sobre extrair infraestrutura. Você só precisa das prisões!

**Tempo de extração:**
- Apenas prisões: ~5-10 minutos ✅
- Com infraestrutura: ~2-6 horas (opcional, só para análises)

#### 2. Iniciar API de Geofencing

```bash
# Modo API (servidor REST)
python geofencing_api.py --mode api --buffer 50

# Opções:
#   --buffer 50  : buffer de segurança em metros (padrão: 50m)
#   --host 0.0.0.0 : expor para rede (padrão: 127.0.0.1)
#   --port 5000  : porta (padrão: 5000)
```

A API estará disponível em `http://127.0.0.1:5000`

#### 3. Exportar Dados para Outros Sistemas

```bash
# Exportar zonas de prisão (GeoJSON + JSON)
python geofencing_api.py --mode export --buffer 50

# Gera:
#   - exports/prison_zones.geojson (polígonos das zonas)
#   - exports/prisons_list.json (lista com coordenadas)
```

### 📊 Para Análise e Compliance

#### 1️⃣ Análise Estatística

Analisar os dados extraídos:

```bash
python analyze_prisons.py
```

Este script gera:
- 📊 Estatísticas básicas (total, por região, por estado)
- 🎯 Análise de clusters (prisões próximas)
- 🏗️ Análise de infraestrutura (se disponível)
- 📈 Gráficos em `reports/`:
  - `prisons_by_region.png`
  - `prisons_by_state_top15.png`
  - `prisons_spatial_distribution.png`

#### 2️⃣ Visualização em Mapas

Criar mapas interativos:

```bash
python visualize_prisons.py
```

Este script cria:
- 🗺️ `prisons_map_brazil.html` - Mapa básico com clusters
- 🗺️ `prisons_map_brazil_regional.html` - Mapa colorido por região
- 🗺️ `prisons_map_brazil_infrastructure.html` - Com infraestrutura (se disponível)

**Recursos dos mapas:**
- 🔍 Busca por nome
- 🎨 Múltiplas camadas (cluster, heatmap, etc)
- 📍 Popups com informações detalhadas
- 🌍 Diferentes estilos de mapa
- 📱 Responsivo e interativo

Abra os arquivos `.html` no navegador!

## 🔌 API REST - Endpoints

### Base URL
```
http://127.0.0.1:5000
```

### 1. Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "prisons_loaded": 450,
  "timestamp": "2025-10-02T10:30:00"
}
```

### 2. Validar Localização (Principal)
```bash
POST /api/v1/check-location
Content-Type: application/json

Body:
{
  "latitude": -22.9068,
  "longitude": -43.1729,
  "transaction_id": "TXN123456"  // opcional
}

Response (DENTRO de prisão):
{
  "inside_prison": true,
  "risk_level": "HIGH",
  "action": "BLOCK",
  "prison_info": {
    "osm_id": 123456,
    "name": "Complexo de Gericinó",
    "operator": "SEAP-RJ",
    "state": "RJ",
    "city": "Rio de Janeiro"
  },
  "coordinates": {
    "latitude": -22.9068,
    "longitude": -43.1729
  },
  "timestamp": "2025-10-02T10:30:00"
}

Response (FORA de prisão):
{
  "inside_prison": false,
  "risk_level": "LOW",
  "action": "ALLOW",
  "prison_info": null,
  "coordinates": {...},
  "timestamp": "2025-10-02T10:30:00"
}
```

### 3. Validação em Batch
```bash
POST /api/v1/batch-check
Content-Type: application/json

Body:
{
  "locations": [
    {"latitude": -22.9068, "longitude": -43.1729},
    {"latitude": -23.5505, "longitude": -46.6333}
  ]
}

Response:
{
  "total": 2,
  "results": [
    { "inside_prison": true, ... },
    { "inside_prison": false, ... }
  ]
}
```

### 4. Prisão Mais Próxima
```bash
POST /api/v1/nearest-prison
Content-Type: application/json

Body:
{
  "latitude": -22.9068,
  "longitude": -43.1729,
  "max_distance_km": 5.0
}

Response:
{
  "distance_km": 2.345,
  "distance_meters": 2345.0,
  "prison_info": {
    "osm_id": 123456,
    "name": "Complexo de Gericinó",
    "operator": "SEAP-RJ",
    "state": "RJ"
  }
}
```

### 5. Estatísticas
```bash
GET /api/v1/stats

Response:
{
  "total_prisons": 450,
  "by_state": {
    "SP": 120,
    "RJ": 80,
    "MG": 60,
    ...
  },
  "with_name": 380,
  "with_operator": 320,
  "buffer_meters": 50
}
```

## 💻 Exemplos de Integração

### Python
```python
import requests

def check_transaction_location(lat, lon, transaction_id):
    """Valida localização de transação"""
    response = requests.post(
        'http://127.0.0.1:5000/api/v1/check-location',
        json={
            'latitude': lat,
            'longitude': lon,
            'transaction_id': transaction_id
        }
    )
    
    result = response.json()
    
    if result['inside_prison']:
        # BLOQUEAR TRANSAÇÃO
        print(f"⛔ TRANSAÇÃO BLOQUEADA - Dentro de prisão: {result['prison_info']['name']}")
        return False
    else:
        # PERMITIR TRANSAÇÃO
        print("✅ Transação permitida")
        return True

# Exemplo de uso
check_transaction_location(-22.9068, -43.1729, "TXN123456")
```

### Node.js
```javascript
const axios = require('axios');

async function checkTransactionLocation(lat, lon, transactionId) {
  try {
    const response = await axios.post('http://127.0.0.1:5000/api/v1/check-location', {
      latitude: lat,
      longitude: lon,
      transaction_id: transactionId
    });
    
    const result = response.data;
    
    if (result.inside_prison) {
      console.log(`⛔ BLOQUEADA - Prisão: ${result.prison_info.name}`);
      return { allowed: false, reason: 'inside_prison' };
    }
    
    return { allowed: true };
  } catch (error) {
    console.error('Erro na validação:', error);
    return { allowed: true, error: true }; // Fail open
  }
}
```

### Java
```java
import java.net.http.*;
import com.google.gson.*;

public class PrisonGeofencing {
    private static final String API_URL = "http://127.0.0.1:5000/api/v1/check-location";
    
    public static boolean checkTransactionLocation(double lat, double lon, String txnId) {
        HttpClient client = HttpClient.newHttpClient();
        
        String json = String.format(
            "{\"latitude\": %f, \"longitude\": %f, \"transaction_id\": \"%s\"}",
            lat, lon, txnId
        );
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(API_URL))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(json))
            .build();
        
        try {
            HttpResponse<String> response = client.send(request, 
                HttpResponse.BodyHandlers.ofString());
            
            JsonObject result = JsonParser.parseString(response.body()).getAsJsonObject();
            
            if (result.get("inside_prison").getAsBoolean()) {
                System.out.println("⛔ BLOQUEADA - Dentro de prisão");
                return false;
            }
            
            return true;
        } catch (Exception e) {
            e.printStackTrace();
            return true; // Fail open em caso de erro
        }
    }
}
```

## 📁 Estrutura de Arquivos

```
testessss/
├── 🔥 CORE - Geofencing Bancário
│   ├── geofencing_api.py          # API REST principal
│   ├── extract_prisons.py         # Extração de dados OSM
│   ├── test_api.py                # Testes da API
│   └── extract_prisons_test.py    # Teste rápido (Rio)
│
├── 📊 Análise e Compliance
│   ├── analyze_prisons.py         # Análises estatísticas
│   ├── visualize_prisons.py       # Mapas interativos
│   └── advanced_analysis.py       # Análises espaciais
│
├── 📚 Documentação e Exemplos
│   ├── README.md                  # Este arquivo
│   ├── overpass_examples.py       # Exemplos de queries OSM
│   ├── requirements.txt           # Dependências
│   └── .gitignore
│
└── 📂 Dados Gerados
    ├── data/                      # Dados extraídos
    │   ├── prisons_brazil_*.geojson
    │   ├── prisons_brazil_*.gpkg
    │   └── prisons_brazil_*.csv
    ├── exports/                   # Exports para integração
    │   ├── prison_zones.geojson
    │   └── prisons_list.json
    └── reports/                   # Relatórios e gráficos
```

## 🔍 Tags OSM Utilizadas

### Prisões
- **Tag principal**: `amenity=prison`
- **Tags complementares**:
  - `name` - Nome da instituição
  - `operator` - Operador (federal/estadual)
  - `capacity` - Capacidade
  - `addr:*` - Endereço
  - `website`, `phone` - Contato
  - `prison:for` - Tipo (juvenil, provisória, etc)

### Infraestrutura
- `building=*` - Prédios ao redor
- `amenity=*` - Serviços (hospitais, escolas, etc)
- `highway=*` - Vias de acesso

## 📊 Exemplos de Análises

### Estatísticas Básicas

```python
from analyze_prisons import PrisonAnalyzer

analyzer = PrisonAnalyzer('data/prisons_brazil_*.geojson')
stats = analyzer.basic_statistics()

# Saída:
# Total de prisões: XXX
# Por região:
#   - Sudeste: XX (XX%)
#   - Nordeste: XX (XX%)
#   ...
```

### Análise de Clusters

```python
# Encontrar prisões com vizinhos a menos de 50km
clusters = analyzer.analyze_clustering(distance_km=50)
```

### Análise Espacial Avançada

```python
from advanced_analysis import AdvancedPrisonAnalyzer

analyzer = AdvancedPrisonAnalyzer('data/prisons_brazil_*.geojson')

# Buffer analysis
analyzer.buffer_analysis(radii=[100, 500, 1000, 5000])

# Nearest services
analyzer.nearest_services_analysis()
```

## 🎯 Casos de Uso Detalhados

### 1. 🏦 Bancos e Fintechs (Principal)

**Detecção de Transações Ilícitas**
- Validação em tempo real de PIX, TED, boletos
- Bloqueio de transações originadas dentro de prisões
- Alertas para equipe de fraude/compliance
- Redução de perdas com extorsão e crimes

**Implementação Recomendada:**
```
Fluxo de Transação:
1. Cliente inicia transação (PIX/TED/Cartão)
2. App coleta localização GPS
3. Backend chama API de geofencing
4. Se inside_prison = true:
   - BLOQUEAR transação
   - Alertar equipe de fraude
   - Notificar cliente
5. Se inside_prison = false:
   - Prosseguir normalmente
```

**Métricas de Sucesso:**
- Taxa de bloqueios dentro de prisões
- Redução de fraudes/extorsões
- Falsos positivos (deve ser <1%)

### 2. 🛡️ Compliance e Prevenção à Lavagem

**Monitoramento de Padrões Suspeitos**
- Análise histórica de transações por região
- Identificação de contas com múltiplas transações próximas a prisões
- Relatórios para COAF/Banco Central
- Auditoria e rastreabilidade

### 3. 📱 Operadoras de Telecomunicações

**Controle de Celulares em Prisões**
- Detecção de uso de chips dentro de presídios
- Bloqueio de ativação de linhas
- Colaboração com autoridades

### 4. 📊 Pesquisa e Análise de Dados

**Estudos Sobre Sistema Prisional**
- Distribuição geográfica de presídios
- Análise de infraestrutura ao redor
- Estudos de impacto social
- Jornalismo investigativo

## ⚙️ Configurações Avançadas

### Consulta Overpass Customizada

Para áreas específicas, edite `extract_prisons.py`:

```python
# Exemplo: Apenas São Paulo
BRAZIL_BBOX = (-25.31, -54.00, -19.78, -44.19)  # SP bbox
```

### Ajustar Raio de Busca

```python
# Em extract_prisons.py, método extract_nearby_infrastructure
infrastructure = extractor.extract_nearby_infrastructure(
    prisons_gdf, 
    radius_meters=1000  # Alterar raio (padrão: 500m)
)
```

### Rate Limiting

O script já inclui delays para não sobrecarregar a API Overpass:
- 2 segundos entre batches
- Retry automático em caso de erro
- Timeout configurável

## 🛠️ Análises Espaciais Avançadas

Execute `advanced_analysis.py` para:

### Buffer Concêntrico
```bash
python advanced_analysis.py --buffer-analysis
```
Analisa infraestrutura em múltiplos raios (100m, 500m, 1km, 5km)

### Serviços Mais Próximos
```bash
python advanced_analysis.py --nearest-services
```
Calcula distância aos serviços essenciais (hospitais, escolas, transporte)

### Densidade Populacional
```bash
python advanced_analysis.py --density
```
Estima densidade de prédios por área

### Acessibilidade
```bash
python advanced_analysis.py --accessibility
```
Analisa conectividade viária e acessibilidade

## 📚 Referências Técnicas

### Overpass API
- Documentação: https://wiki.openstreetmap.org/wiki/Overpass_API
- Overpass Turbo: https://overpass-turbo.eu/
- Rate limits: https://dev.overpass-api.de/overpass-doc/en/

### OSM Tags
- Prisões: https://wiki.openstreetmap.org/wiki/Tag:amenity=prison
- Edifícios: https://wiki.openstreetmap.org/wiki/Key:building
- Amenidades: https://wiki.openstreetmap.org/wiki/Key:amenity

### Bibliotecas
- GeoPandas: https://geopandas.org/
- Folium: https://python-visualization.github.io/folium/
- Overpy: https://github.com/DinoTools/python-overpy

## ⚖️ Considerações Legais e Éticas

### ✅ Uso Legítimo

**Este sistema é LEGAL e ÉTICO porque:**
- 📖 Dados são públicos (OpenStreetMap)
- 🛡️ Finalidade: prevenir crimes e fraudes
- 🏦 Uso por instituições financeiras reguladas
- 📊 Transparência nos dados e métodos
- 🔒 Não coleta dados pessoais

**Casos de uso legítimos:**
- ✅ Prevenção de fraudes financeiras
- ✅ Compliance bancário
- ✅ Combate à extorsão e lavagem de dinheiro
- ✅ Estudos acadêmicos e jornalismo
- ✅ Suporte a autoridades (via canais oficiais)

### 📋 Compliance Bancário

Para instituições financeiras:
- Documente o uso no programa de prevenção a fraudes
- Inclua em políticas de KYC/AML
- Mantenha logs para auditoria (mínimo 5 anos)
- Reporte padrões suspeitos ao COAF
- Revise periodicamente a eficácia

## 🐛 Troubleshooting

### Erro: "Rate limit exceeded"
- Aguarde alguns minutos e tente novamente
- Reduza o batch_size em `extract_prisons.py`

### Erro: "Timeout"
- Aumente o timeout: `OSMPrisonExtractor(timeout=300)`
- Divida a extração por estados

### Arquivo não encontrado
- Verifique se executou `extract_prisons.py` primeiro
- Confira o diretório `data/`

### Mapa não carrega
- Verifique se há dados em `data/`
- Teste com um navegador diferente
- Veja o console do navegador para erros

## 🤝 Contribuindo

Para melhorar este projeto:

1. Adicione novos tipos de análise
2. Melhore visualizações
3. Otimize performance
4. Corrija bugs
5. Melhore documentação

## 🚀 Deployment em Produção

### Docker (Recomendado)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Baixar dados na build (ou montar volume)
RUN python extract_prisons.py --headless

EXPOSE 5000

CMD ["python", "geofencing_api.py", "--mode", "api", "--host", "0.0.0.0"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prison-geofencing-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: prison-geofencing:latest
        ports:
        - containerPort: 5000
        env:
        - name: BUFFER_METERS
          value: "50"
```

### Performance

**Resultados reais em testes:**
- ✅ **1.12ms por request** (latência média)
- ✅ **892 requisições/segundo** (throughput)
- ✅ Performance muito superior aos requisitos

**Latência esperada em produção:**
- Check simples: <10ms
- Batch 100 localizações: <100ms

**Escalabilidade:**
- API é stateless (pode escalar horizontalmente)
- Considere cache Redis para hot paths
- Load balancer para múltiplas instâncias

## 🧪 Testes

```bash
# Instalar dependências de teste
pip install pytest requests

# Rodar testes da API
python test_api.py

# Testes unitários
pytest tests/
```

## 📄 Licença e Atribuição

**Dados:**
- Fonte: OpenStreetMap (ODbL License)
- Contribuidores: OSM Community
- Link: https://www.openstreetmap.org/copyright

**Código:**
- Fornecido "como está" para fins legítimos
- Uso comercial permitido
- Sem garantias - teste thoroughly antes de produção

**Atribuição Requerida:**
```
Dados © OpenStreetMap contributors
https://www.openstreetmap.org/copyright
```

## 🆘 Troubleshooting

### API não inicia
```bash
# Verificar se dados foram extraídos
ls -la data/prisons_brazil_*.geojson

# Se não, extrair:
python extract_prisons.py
```

### Falsos Positivos (bloqueando fora de prisões)
```bash
# Aumentar buffer de segurança
python geofencing_api.py --mode api --buffer 100
```

### Falsos Negativos (não bloqueando dentro)
```bash
# Reduzir buffer
python geofencing_api.py --mode api --buffer 20

# Verificar qualidade dos polígonos no OSM
```

### Performance Lenta
- Use caching (Redis)
- Indexação espacial (já inclusa no GeoPandas)
- Escale horizontalmente

## 📞 Suporte e Contribuições

**Dúvidas Técnicas:**
- OSM: https://help.openstreetmap.org/
- Overpass API: https://lz4.overpass-api.de/
- GeoPandas: https://geopandas.org/

**Melhorias nos Dados OSM:**
- Contribua no OpenStreetMap
- Reporte prisões faltantes
- Corrija geometrias imprecisas

**Segurança:**
- Para reportar vulnerabilidades, abra issue privada
- Não publique exploits

---

**🏦 Desenvolvido para prevenção de fraudes financeiras**  
**🗺️ Powered by OpenStreetMap**  
**🛡️ Ajudando a tornar o sistema financeiro mais seguro**

*Última atualização: Outubro 2025*

