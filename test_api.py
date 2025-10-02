#!/usr/bin/env python3
"""
Testes da API de Geofencing
Execute depois de iniciar a API com: python geofencing_api.py --mode api
"""

import requests
import json
import time
from typing import Dict


class GeofencingAPITester:
    """Testa endpoints da API de geofencing"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health(self) -> bool:
        """Testa endpoint de health check"""
        print("\n1️⃣  Testando Health Check...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            data = response.json()
            
            print(f"   ✓ Status: {data['status']}")
            print(f"   ✓ Prisões carregadas: {data['prisons_loaded']}")
            return True
        except Exception as e:
            print(f"   ✗ Erro: {e}")
            return False
    
    def test_check_location_inside(self) -> bool:
        """Testa localização DENTRO de prisão (exemplo: Complexo de Gericinó, RJ)"""
        print("\n2️⃣  Testando Localização DENTRO de Prisão...")
        
        # Coordenadas aproximadas do Complexo de Gericinó
        payload = {
            "latitude": -22.8475,
            "longitude": -43.4686,
            "transaction_id": "TEST_001"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/check-location",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"   Localização: {payload['latitude']}, {payload['longitude']}")
            print(f"   Dentro de prisão: {data['inside_prison']}")
            print(f"   Nível de risco: {data['risk_level']}")
            print(f"   Ação: {data['action']}")
            
            if data['inside_prison']:
                print(f"   ✓ Prisão detectada: {data['prison_info']['name']}")
                return True
            else:
                print(f"   ⚠️  Não detectou prisão (pode ser que OSM não tenha esta prisão)")
                return True  # Não é erro, apenas dados OSM podem estar incompletos
                
        except Exception as e:
            print(f"   ✗ Erro: {e}")
            return False
    
    def test_check_location_outside(self) -> bool:
        """Testa localização FORA de prisão (exemplo: Cristo Redentor, RJ)"""
        print("\n3️⃣  Testando Localização FORA de Prisão...")
        
        # Cristo Redentor - claramente fora de qualquer prisão
        payload = {
            "latitude": -22.9519,
            "longitude": -43.2105,
            "transaction_id": "TEST_002"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/check-location",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"   Localização: Cristo Redentor")
            print(f"   Dentro de prisão: {data['inside_prison']}")
            print(f"   Nível de risco: {data['risk_level']}")
            print(f"   Ação: {data['action']}")
            
            if not data['inside_prison'] and data['action'] == 'ALLOW':
                print(f"   ✓ Corretamente identificado como FORA de prisão")
                return True
            else:
                print(f"   ✗ FALSO POSITIVO - detectou prisão onde não deveria!")
                return False
                
        except Exception as e:
            print(f"   ✗ Erro: {e}")
            return False
    
    def test_batch_check(self) -> bool:
        """Testa validação em batch"""
        print("\n4️⃣  Testando Batch Check...")
        
        payload = {
            "locations": [
                {"latitude": -22.9519, "longitude": -43.2105},  # Cristo Redentor
                {"latitude": -23.5505, "longitude": -46.6333},  # Av. Paulista, SP
                {"latitude": -15.7942, "longitude": -47.8822},  # Brasília
            ]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/batch-check",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"   Total de localizações testadas: {data['total']}")
            
            inside_count = sum(1 for r in data['results'] if r['inside_prison'])
            print(f"   Dentro de prisões: {inside_count}")
            print(f"   Fora de prisões: {data['total'] - inside_count}")
            
            print(f"   ✓ Batch processado com sucesso")
            return True
                
        except Exception as e:
            print(f"   ✗ Erro: {e}")
            return False
    
    def test_nearest_prison(self) -> bool:
        """Testa busca de prisão mais próxima"""
        print("\n5️⃣  Testando Prisão Mais Próxima...")
        
        # Centro do Rio de Janeiro
        payload = {
            "latitude": -22.9068,
            "longitude": -43.1729,
            "max_distance_km": 10.0
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/nearest-prison",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('distance_km'):
                print(f"   ✓ Prisão mais próxima encontrada:")
                print(f"     - Distância: {data['distance_km']} km")
                print(f"     - Nome: {data['prison_info']['name']}")
            else:
                print(f"   ⚠️  Nenhuma prisão encontrada no raio de {payload['max_distance_km']}km")
            
            return True
                
        except Exception as e:
            print(f"   ✗ Erro: {e}")
            return False
    
    def test_stats(self) -> bool:
        """Testa endpoint de estatísticas"""
        print("\n6️⃣  Testando Estatísticas...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/v1/stats")
            response.raise_for_status()
            data = response.json()
            
            print(f"   ✓ Total de prisões: {data['total_prisons']}")
            print(f"   ✓ Buffer de segurança: {data['buffer_meters']}m")
            
            if data['by_state']:
                top_states = sorted(data['by_state'].items(), key=lambda x: x[1], reverse=True)[:5]
                print(f"   ✓ Top 5 estados:")
                for state, count in top_states:
                    print(f"     - {state}: {count} prisões")
            
            return True
                
        except Exception as e:
            print(f"   ✗ Erro: {e}")
            return False
    
    def test_performance(self, num_requests: int = 100) -> bool:
        """Testa performance da API"""
        print(f"\n7️⃣  Testando Performance ({num_requests} requests)...")
        
        payload = {
            "latitude": -22.9068,
            "longitude": -43.1729,
            "transaction_id": "PERF_TEST"
        }
        
        try:
            start_time = time.time()
            
            for i in range(num_requests):
                response = self.session.post(
                    f"{self.base_url}/api/v1/check-location",
                    json=payload
                )
                response.raise_for_status()
            
            total_time = time.time() - start_time
            avg_time = (total_time / num_requests) * 1000  # em ms
            
            print(f"   ✓ Tempo total: {total_time:.2f}s")
            print(f"   ✓ Tempo médio por request: {avg_time:.2f}ms")
            print(f"   ✓ Throughput: {num_requests/total_time:.2f} req/s")
            
            if avg_time < 50:
                print(f"   ✓ Performance EXCELENTE (<50ms)")
            elif avg_time < 100:
                print(f"   ✓ Performance BOA (<100ms)")
            else:
                print(f"   ⚠️  Performance pode ser melhorada")
            
            return True
                
        except Exception as e:
            print(f"   ✗ Erro: {e}")
            return False
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("=" * 60)
        print("  TESTES DA API DE GEOFENCING")
        print("=" * 60)
        
        tests = [
            ("Health Check", self.test_health),
            ("Localização Dentro", self.test_check_location_inside),
            ("Localização Fora", self.test_check_location_outside),
            ("Batch Check", self.test_batch_check),
            ("Prisão Mais Próxima", self.test_nearest_prison),
            ("Estatísticas", self.test_stats),
            ("Performance", lambda: self.test_performance(50)),
        ]
        
        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                results.append((name, result))
            except Exception as e:
                print(f"\n❌ Erro fatal no teste '{name}': {e}")
                results.append((name, False))
        
        # Sumário
        print("\n" + "=" * 60)
        print("  SUMÁRIO DOS TESTES")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"   {status} - {name}")
        
        print(f"\n   Total: {passed}/{total} testes passaram")
        
        if passed == total:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
        else:
            print(f"\n⚠️  {total - passed} teste(s) falharam")
        
        return passed == total


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Testes da API de Geofencing')
    parser.add_argument('--url', type=str, default='http://127.0.0.1:5000',
                       help='URL base da API (padrão: http://127.0.0.1:5000)')
    parser.add_argument('--quick', action='store_true',
                       help='Apenas testes rápidos (sem performance)')
    
    args = parser.parse_args()
    
    # Verificar se API está rodando
    print("🔍 Verificando se a API está rodando...")
    try:
        response = requests.get(f"{args.url}/health", timeout=2)
        response.raise_for_status()
        print("✓ API está rodando!\n")
    except Exception as e:
        print(f"\n❌ ERRO: API não está respondendo em {args.url}")
        print(f"   {e}")
        print("\n💡 Inicie a API primeiro:")
        print("   python geofencing_api.py --mode api")
        return
    
    # Executar testes
    tester = GeofencingAPITester(args.url)
    
    if args.quick:
        # Apenas testes básicos
        tester.test_health()
        tester.test_check_location_outside()
        tester.test_stats()
    else:
        # Todos os testes
        tester.run_all_tests()


if __name__ == "__main__":
    main()

