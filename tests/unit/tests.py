import unittest
from fastapi.testclient import TestClient
import json
from typing import Dict, List, Any

# Importações do projeto
from main import app
from nlp import EntityExtractor
from storage import MemoryStorage

# Cliente de teste
client = TestClient(app)

class TestEntityExtraction(unittest.TestCase):
    """Testes para a extração de entidades"""
    
    def setUp(self):
        # Inicializar o extrator de entidades com um modelo de fallback
        # para evitar carregar modelos grandes durante os testes
        self.extractor = EntityExtractor(
            model_name="pucpr/ner-bert-base-portuguese-cased",
            fallback_model="xlm-roberta-base"
        )
        
        # Substituir o método de extração por um mock para testes
        self.extractor._fallback_extraction = self.mock_extraction
    
    def mock_extraction(self, text: str) -> Dict[str, str]:
        """Mock para extração de entidades durante os testes"""
        result = {}
        
        # Simular detecção de distribuidores
        if "officer" in text.lower():
            result["distribuidor"] = "Officer"
        elif "alcateia" in text.lower():
            result["distribuidor"] = "Alcateia"
        
        # Simular detecção de números de pedido
        if "pedido" in text.lower() and any(c.isdigit() for c in text):
            # Extrair o primeiro número com pelo menos 5 dígitos
            import re
            pedido_matches = re.findall(r'\b\d{5,}\b', text)
            if pedido_matches:
                result["pedido"] = pedido_matches[0]
        
        # Simular detecção de notas fiscais
        if ("nota" in text.lower() or "fiscal" in text.lower()) and any(c.isdigit() for c in text):
            # Extrair o primeiro número com pelo menos 5 dígitos
            import re
            nota_matches = re.findall(r'\b\d{5,}\b', text)
            if nota_matches:
                result["nota_fiscal"] = nota_matches[0]
        
        return result
    
    def test_extract_distribuidor(self):
        """Testa a extração de distribuidores"""
        text = "Fiz um pedido com a Officer semana passada"
        entities = self.extractor.extract_entities(text)
        self.assertIn("distribuidor", entities)
        self.assertEqual(entities["distribuidor"], "Officer")
    
    def test_extract_pedido(self):
        """Testa a extração de números de pedido"""
        text = "Queria saber do pedido 112233"
        entities = self.extractor.extract_entities(text)
        self.assertIn("pedido", entities)
        self.assertEqual(entities["pedido"], "112233")
    
    def test_extract_nota_fiscal(self):
        """Testa a extração de números de nota fiscal"""
        text = "Nota fiscal 445566 da Alcateia já chegou?"
        entities = self.extractor.extract_entities(text)
        self.assertIn("nota_fiscal", entities)
        self.assertEqual(entities["nota_fiscal"], "445566")
        self.assertIn("distribuidor", entities)
        self.assertEqual(entities["distribuidor"], "Alcateia")
    
    def test_extract_multiple_entities(self):
        """Testa a extração de múltiplas entidades em uma mensagem"""
        text = "Queria saber do pedido 112233 com a Officer"
        entities = self.extractor.extract_entities(text)
        self.assertIn("pedido", entities)
        self.assertEqual(entities["pedido"], "112233")
        self.assertIn("distribuidor", entities)
        self.assertEqual(entities["distribuidor"], "Officer")

class TestStorage(unittest.TestCase):
    """Testes para o armazenamento de contexto"""
    
    def setUp(self):
        self.storage = MemoryStorage()
        self.session_id = "test-session-id"
        self.context = {"distribuidor": "Officer", "pedido": "123456"}
    
    def test_set_and_get(self):
        """Testa a definição e recuperação de contexto"""
        self.storage.set(self.session_id, self.context)
        retrieved_context = self.storage.get(self.session_id)
        self.assertEqual(retrieved_context, self.context)
    
    def test_exists(self):
        """Testa a verificação de existência de sessão"""
        self.assertFalse(self.storage.exists("non-existent-session"))
        self.storage.set(self.session_id, self.context)
        self.assertTrue(self.storage.exists(self.session_id))
    
    def test_delete(self):
        """Testa a exclusão de contexto"""
        self.storage.set(self.session_id, self.context)
        self.assertTrue(self.storage.exists(self.session_id))
        self.storage.delete(self.session_id)
        self.assertFalse(self.storage.exists(self.session_id))
        self.assertEqual(self.storage.get(self.session_id), {})

class TestAPI(unittest.TestCase):
    """Testes para os endpoints da API"""
    
    def test_root_endpoint(self):
        """Testa o endpoint raiz"""
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("version", data)
        self.assertIn("endpoints", data)
    
    def test_conversar_endpoint(self):
        """Testa o endpoint de conversa"""
        # Primeira mensagem
        response = client.post(
            "/conversar",
            json={"message": "Fiz um pedido na Officer"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("session_id", data)
        self.assertIn("context", data)
        
        # Verificar se o distribuidor foi detectado
        self.assertIn("distribuidor", data["context"])
        self.assertEqual(data["context"]["distribuidor"], "Officer")
        
        # Salvar o session_id para a próxima mensagem
        session_id = data["session_id"]
        
        # Segunda mensagem na mesma sessão
        response = client.post(
            "/conversar",
            json={"message": "O número do pedido é 123456", "session_id": session_id}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verificar se o pedido foi detectado e o contexto foi mantido
        self.assertIn("distribuidor", data["context"])
        self.assertEqual(data["context"]["distribuidor"], "Officer")
        self.assertIn("pedido", data["context"])
        self.assertEqual(data["context"]["pedido"], "123456")
    
    def test_token_endpoint(self):
        """Testa o endpoint de geração de token"""
        response = client.post("/token")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("token_type", data)
        self.assertEqual(data["token_type"], "bearer")

# Executar os testes
if __name__ == "__main__":
    unittest.main()