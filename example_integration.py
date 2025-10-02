#!/usr/bin/env python3
"""
Exemplo de Integração - Como usar a API de Geofencing em seu sistema bancário
"""

import requests
from typing import Dict, Optional


class BankingGeofenceClient:
    """
    Cliente para integração com API de Geofencing
    Use esta classe como exemplo em seu sistema bancário
    """
    
    def __init__(self, api_url: str = "http://127.0.0.1:5000"):
        """
        Args:
            api_url: URL da API de geofencing
        """
        self.api_url = api_url
        self.session = requests.Session()
        # Em produção, adicione headers de autenticação:
        # self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def validate_transaction_location(
        self, 
        latitude: float, 
        longitude: float,
        transaction_id: str,
        timeout: float = 2.0
    ) -> Dict:
        """
        Valida se uma transação está sendo feita de dentro de uma prisão
        
        Args:
            latitude: latitude do dispositivo
            longitude: longitude do dispositivo
            transaction_id: ID da transação para log/auditoria
            timeout: timeout em segundos (padrão: 2s)
            
        Returns:
            Dict com:
                - should_block: bool (True se deve bloquear)
                - reason: str (motivo do bloqueio/liberação)
                - prison_name: str ou None
                - risk_level: str
        """
        try:
            response = self.session.post(
                f"{self.api_url}/api/v1/check-location",
                json={
                    'latitude': latitude,
                    'longitude': longitude,
                    'transaction_id': transaction_id
                },
                timeout=timeout
            )
            
            # Em caso de erro HTTP, fail-open (permite transação)
            if response.status_code != 200:
                return {
                    'should_block': False,
                    'reason': 'geofencing_service_error',
                    'prison_name': None,
                    'risk_level': 'UNKNOWN',
                    'error': True
                }
            
            data = response.json()
            
            return {
                'should_block': data['inside_prison'],
                'reason': 'inside_prison' if data['inside_prison'] else 'location_ok',
                'prison_name': data['prison_info']['name'] if data.get('prison_info') else None,
                'risk_level': data['risk_level'],
                'error': False
            }
            
        except requests.Timeout:
            # Timeout - fail-open (permite transação)
            return {
                'should_block': False,
                'reason': 'geofencing_timeout',
                'prison_name': None,
                'risk_level': 'UNKNOWN',
                'error': True
            }
        except Exception as e:
            # Erro genérico - fail-open (permite transação)
            return {
                'should_block': False,
                'reason': f'geofencing_error: {str(e)}',
                'prison_name': None,
                'risk_level': 'UNKNOWN',
                'error': True
            }


# ==================== EXEMPLO DE USO ====================

def example_pix_transaction():
    """
    Exemplo: Validar transação PIX
    """
    print("=" * 60)
    print("  EXEMPLO: Validação de Transação PIX")
    print("=" * 60)
    
    # Inicializar cliente
    client = BankingGeofenceClient()
    
    # Dados da transação
    transaction_data = {
        'transaction_id': 'PIX-123456789',
        'customer_id': 'CUST-001',
        'amount': 1000.00,
        'latitude': -22.9068,  # Coordenadas do dispositivo do cliente
        'longitude': -43.1729,
        'device_id': 'DEVICE-ABC123'
    }
    
    print(f"\n📱 Transação iniciada:")
    print(f"   ID: {transaction_data['transaction_id']}")
    print(f"   Valor: R$ {transaction_data['amount']:.2f}")
    print(f"   Localização: {transaction_data['latitude']}, {transaction_data['longitude']}")
    
    # Validar localização
    print(f"\n🔍 Validando geolocalização...")
    result = client.validate_transaction_location(
        latitude=transaction_data['latitude'],
        longitude=transaction_data['longitude'],
        transaction_id=transaction_data['transaction_id']
    )
    
    # Decisão
    print(f"\n📊 Resultado da validação:")
    print(f"   Nível de risco: {result['risk_level']}")
    print(f"   Motivo: {result['reason']}")
    
    if result['should_block']:
        print(f"\n⛔ TRANSAÇÃO BLOQUEADA!")
        print(f"   Prisão detectada: {result['prison_name']}")
        print(f"\n🚨 Ações recomendadas:")
        print(f"   1. Notificar cliente sobre bloqueio")
        print(f"   2. Alertar equipe de fraude")
        print(f"   3. Registrar incidente para análise")
        print(f"   4. Considerar bloqueio temporário da conta")
        
        # Log para auditoria
        log_blocked_transaction(transaction_data, result)
        
        return False
    
    elif result['error']:
        print(f"\n⚠️  Erro no serviço de geofencing")
        print(f"   Prosseguindo com transação (fail-open)")
        print(f"   Recomendação: Registrar para análise posterior")
        
        # Log do erro
        log_geofencing_error(transaction_data, result)
        
        return True
    
    else:
        print(f"\n✅ TRANSAÇÃO APROVADA (geolocalização OK)")
        return True


def example_batch_validation():
    """
    Exemplo: Validação em batch de transações suspeitas
    """
    print("\n" + "=" * 60)
    print("  EXEMPLO: Validação em Batch (Análise de Fraudes)")
    print("=" * 60)
    
    client = BankingGeofenceClient()
    
    # Transações suspeitas para análise
    suspicious_transactions = [
        {'id': 'TXN-001', 'lat': -22.9068, 'lon': -43.1729, 'amount': 500},
        {'id': 'TXN-002', 'lat': -23.5505, 'lon': -46.6333, 'amount': 1000},
        {'id': 'TXN-003', 'lat': -22.8475, 'lon': -43.4686, 'amount': 2000},
    ]
    
    print(f"\n📋 Analisando {len(suspicious_transactions)} transações suspeitas...")
    
    blocked_count = 0
    
    for txn in suspicious_transactions:
        result = client.validate_transaction_location(
            latitude=txn['lat'],
            longitude=txn['lon'],
            transaction_id=txn['id']
        )
        
        status = "🔴 BLOQUEADA" if result['should_block'] else "🟢 LIBERADA"
        print(f"\n   {txn['id']}: {status}")
        print(f"      Valor: R$ {txn['amount']:.2f}")
        print(f"      Risco: {result['risk_level']}")
        
        if result['should_block']:
            blocked_count += 1
            print(f"      Prisão: {result['prison_name']}")
    
    print(f"\n📊 Resumo:")
    print(f"   Total analisadas: {len(suspicious_transactions)}")
    print(f"   Bloqueadas: {blocked_count}")
    print(f"   Liberadas: {len(suspicious_transactions) - blocked_count}")


def log_blocked_transaction(transaction_data: Dict, result: Dict):
    """
    Exemplo de função para log de transação bloqueada
    Em produção, salvar em banco de dados, enviar para SIEM, etc.
    """
    print(f"\n📝 LOG REGISTRADO:")
    print(f"   Timestamp: {__import__('datetime').datetime.now().isoformat()}")
    print(f"   Transaction ID: {transaction_data['transaction_id']}")
    print(f"   Customer ID: {transaction_data['customer_id']}")
    print(f"   Prison: {result['prison_name']}")
    print(f"   Action: BLOCKED")
    
    # Em produção:
    # db.fraud_alerts.insert({
    #     'timestamp': datetime.now(),
    #     'transaction_id': transaction_data['transaction_id'],
    #     'customer_id': transaction_data['customer_id'],
    #     'prison_name': result['prison_name'],
    #     'action': 'BLOCKED',
    #     'coordinates': {'lat': transaction_data['latitude'], 'lon': transaction_data['longitude']}
    # })


def log_geofencing_error(transaction_data: Dict, result: Dict):
    """
    Exemplo de função para log de erro no geofencing
    """
    print(f"\n⚠️  ERRO REGISTRADO:")
    print(f"   Transaction ID: {transaction_data['transaction_id']}")
    print(f"   Error: {result['reason']}")
    
    # Em produção, monitorar erros e alertar se taxa for alta


# ==================== PADRÕES DE IMPLEMENTAÇÃO ====================

def example_transaction_flow():
    """
    Fluxo completo de uma transação com geofencing
    """
    print("\n" + "=" * 60)
    print("  FLUXO COMPLETO DE TRANSAÇÃO")
    print("=" * 60)
    
    print("""
    1. Cliente inicia transação no app
    2. App coleta localização GPS (com permissão do usuário)
    3. Backend recebe request de transação + coordenadas
    4. Backend chama API de geofencing
    5. Decisão baseada no resultado:
    
       SE inside_prison = TRUE:
           ⛔ BLOQUEAR transação
           📧 Notificar cliente
           🚨 Alertar equipe de fraude
           📝 Registrar incidente
           
       SE inside_prison = FALSE:
           ✅ Prosseguir com transação
           📝 Registrar validação OK
           
       SE error = TRUE (timeout/falha):
           ⚠️  Prosseguir com transação (fail-open)
           📝 Registrar erro para análise
           📊 Monitorar taxa de erro
    
    6. Retornar resultado para cliente
    """)


def main():
    """Função principal"""
    print("🏦 EXEMPLOS DE INTEGRAÇÃO - API DE GEOFENCING BANCÁRIO\n")
    
    # Verificar se API está rodando
    try:
        response = requests.get("http://127.0.0.1:5000/health", timeout=2)
        response.raise_for_status()
        print("✅ API de geofencing está rodando!\n")
    except Exception as e:
        print("❌ API não está rodando. Inicie com:")
        print("   python geofencing_api.py --mode api\n")
        return
    
    # Executar exemplos
    example_pix_transaction()
    example_batch_validation()
    example_transaction_flow()
    
    print("\n" + "=" * 60)
    print("💡 DICAS DE IMPLEMENTAÇÃO:")
    print("=" * 60)
    print("""
    1. Fail-Open: Em caso de erro/timeout, libere a transação
       (melhor experiência do usuário, menor impacto)
    
    2. Timeout Curto: Use timeout de 2-3s para não travar transação
    
    3. Cache: Considere cachear resultados por coordenadas
       (mas cuidado com precisão)
    
    4. Monitoramento: Monitore taxa de bloqueios e erros
    
    5. A/B Testing: Inicie com apenas alertas (não bloqueios)
       e valide a eficácia antes de bloquear de fato
    
    6. LGPD: Informe usuários sobre coleta de localização
    
    7. Logs: Mantenha logs detalhados para auditoria (5+ anos)
    
    8. Atualização: Re-extraia dados do OSM mensalmente
    
    9. Validação: Cruze com outras camadas de segurança
       (análise comportamental, device fingerprint, etc)
    
    10. Fallback: Tenha sistema secundário caso API fique offline
    """)


if __name__ == "__main__":
    main()

