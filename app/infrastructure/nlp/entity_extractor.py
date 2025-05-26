from typing import Dict, List, Optional, Tuple, Any
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import re
import logging

logger = logging.getLogger(__name__)

class EntityExtractor:
    """Classe responsável por extrair entidades de textos usando modelos de NLP"""
    
    def __init__(self, model_name: str, fallback_model: Optional[str] = None):
        self.model_name = model_name
        self.fallback_model = fallback_model
        self.ner_pipeline = None
        self.tokenizer = None
        self.model = None
        self.is_fallback = False
        
        # Inicializar o modelo
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Inicializa o modelo NER principal ou o fallback se necessário"""
        try:
            logger.info(f"Carregando modelo NER: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(self.model_name)
            self.ner_pipeline = pipeline(
                "token-classification", 
                model=self.model, 
                tokenizer=self.tokenizer,
                aggregation_strategy="simple"
            )
            logger.info(f"Modelo NER carregado com sucesso: {self.model_name}")
        except Exception as e:
            logger.error(f"Erro ao carregar o modelo NER: {e}")
            self._load_fallback_model()
    
    def _load_fallback_model(self) -> None:
        """Carrega o modelo fallback em caso de falha no modelo principal"""
        if not self.fallback_model:
            logger.warning("Nenhum modelo fallback especificado")
            return
        
        try:
            logger.info(f"Tentando carregar modelo fallback: {self.fallback_model}")
            self.ner_pipeline = pipeline("ner", model=self.fallback_model)
            self.is_fallback = True
            logger.info("Modelo fallback carregado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo fallback: {e}")
            self.ner_pipeline = None
    
    def extract_entities(self, text: str) -> Dict[str, str]:
        """Extrai entidades do texto usando o modelo NER"""
        if self.ner_pipeline is None:
            logger.warning("Nenhum modelo NER disponível para extração de entidades")
            return self._fallback_extraction(text)
        
        try:
            # Realizar a detecção de entidades
            entities = self.ner_pipeline(text)
            
            # Processar as entidades detectadas
            if self.is_fallback:
                return self._process_fallback_entities(entities, text)
            else:
                return self._process_entities(entities, text)
        except Exception as e:
            logger.error(f"Erro durante a extração de entidades: {e}")
            return self._fallback_extraction(text)
    
    def _process_entities(self, entities: List[Dict], text: str) -> Dict[str, str]:
        """Processa as entidades detectadas pelo modelo principal"""
        result = {}
        
        for entity in entities:
            entity_text = entity["word"]
            entity_type = entity["entity_group"]
            
            # Mapeamento de entidades (ajustar conforme o modelo)
            if any(label in entity_type.upper() for label in ["DISTRIBUIDOR", "ORG", "ORGANIZATION"]):
                result["distribuidor"] = self._clean_entity_text(entity_text)
            
            elif any(label in entity_type.upper() for label in ["PEDIDO", "ORDER"]):
                if self._is_valid_number(entity_text):
                    result["pedido"] = self._clean_entity_text(entity_text)
            
            elif any(label in entity_type.upper() for label in ["NOTA", "FISCAL", "INVOICE"]):
                if self._is_valid_number(entity_text):
                    result["nota_fiscal"] = self._clean_entity_text(entity_text)
        
        # Se não encontrou entidades específicas, tenta extrair com heurísticas
        if not result:
            return self._fallback_extraction(text)
        
        return result
    
    def _process_fallback_entities(self, entities: List[Dict], text: str) -> Dict[str, str]:
        """Processa as entidades detectadas pelo modelo fallback"""
        result = {}
        
        # Modelos genéricos podem não ter labels específicas para nosso caso
        # Vamos usar heurísticas para identificar as entidades
        
        # Procurar por organizações (distribuidores)
        org_entities = [e for e in entities if e["entity"].endswith("-ORG")]
        if org_entities:
            result["distribuidor"] = self._clean_entity_text(org_entities[0]["word"])
        
        # Procurar por números que podem ser pedidos ou notas fiscais
        num_entities = [e for e in entities if e["entity"].endswith("-CARDINAL") or e["entity"].endswith("-NUM")]
        
        for entity in num_entities:
            entity_text = entity["word"]
            
            # Verificar se é um número válido
            if self._is_valid_number(entity_text):
                # Verificar o contexto para determinar se é pedido ou nota fiscal
                context_before = text[:entity["start"]].lower()
                
                if "pedido" in context_before or "order" in context_before:
                    result["pedido"] = self._clean_entity_text(entity_text)
                elif "nota" in context_before or "fiscal" in context_before or "nf" in context_before:
                    result["nota_fiscal"] = self._clean_entity_text(entity_text)
                # Se não tiver contexto claro e ainda não tiver pedido, assume como pedido
                elif "pedido" not in result:
                    result["pedido"] = self._clean_entity_text(entity_text)
        
        # Se ainda não encontrou entidades, tenta com heurísticas
        if not result:
            return self._fallback_extraction(text)
        
        return result
    
    def _fallback_extraction(self, text: str) -> Dict[str, str]:
        """Método de extração baseado em heurísticas quando os modelos falham"""
        result = {}
        
        # Extrair possíveis distribuidores (tanto suportados quanto não suportados)
        # Inclui todos os distribuidores que queremos reconhecer
        distribuidores_conhecidos = ["officer", "ingram", "golden", "alcateia", "network1", "n1"]
        text_lower = text.lower()
        
        for distribuidor in distribuidores_conhecidos:
            if distribuidor in text_lower:
                # Encontrar a palavra completa
                match = re.search(r'\b' + distribuidor + r'\b', text_lower)
                if match:
                    start, end = match.span()
                    # Pegar a palavra original com capitalização
                    result["distribuidor"] = text[start:end].strip()
                    break
        
        # Verificar padrões específicos de pedido (ex: "Pedido 1234")
        pedido_pattern = re.search(r'(?i)\b(?:pedido|order)\s*[:#]?\s*(\d+)\b', text)
        if pedido_pattern:
            result["pedido"] = pedido_pattern.group(1)
            
        # Verificar padrões específicos de nota fiscal
        nf_pattern = re.search(r'(?i)\b(?:nota\s*fiscal|nf)\s*[:#]?\s*(\d+)\b', text)
        if nf_pattern:
            result["nota_fiscal"] = nf_pattern.group(1)
        
        # Se não encontrou padrões específicos, tenta extrair números
        if "pedido" not in result and "nota_fiscal" not in result:
            # Extrair possíveis números de pedido (sequências de dígitos)
            pedido_matches = re.findall(r'\b\d+\b', text)
            if pedido_matches:
                # Verificar contexto para determinar se é pedido ou nota
                for match in pedido_matches:
                    # Encontrar a posição do número no texto
                    pos = text.find(match)
                    context_before = text[:pos].lower()
                    
                    if "nota" in context_before or "fiscal" in context_before or "nf" in context_before:
                        result["nota_fiscal"] = match
                    elif "pedido" in context_before or "order" in context_before:
                        result["pedido"] = match
                    # Se não tiver contexto claro e ainda não tiver pedido, assume como pedido
                    elif "pedido" not in result:
                        result["pedido"] = match
        
        return result
    
    def _is_valid_number(self, text: str) -> bool:
        """Verifica se o texto é um número válido para pedido ou nota fiscal"""
        # Remover caracteres não numéricos para verificação
        clean_text = re.sub(r'[^0-9]', '', text)
        
        # Números de pedido podem ter 4 ou mais dígitos
        # Notas fiscais geralmente têm pelo menos 5 dígitos
        return len(clean_text) >= 1  # Aceitamos qualquer número, o contexto determinará se é válido
    
    def _clean_entity_text(self, text: str) -> str:
        """Limpa o texto da entidade, removendo caracteres indesejados"""
        # Remover espaços extras e caracteres especiais indesejados
        return text.strip()
        
    def is_distribuidor_suportado(self, distribuidor: str) -> bool:
        """Verifica se o distribuidor é suportado pelo sistema"""
        if not distribuidor:
            return False
            
        # Lista de distribuidores oficialmente suportados
        distribuidores_suportados = ["officer", "ingram", "golden"]
        
        return distribuidor.lower() in [d.lower() for d in distribuidores_suportados]