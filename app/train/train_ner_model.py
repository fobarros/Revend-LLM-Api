import json
import os
import logging
from typing import List, Dict, Any, Optional

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, Trainer, TrainingArguments
from transformers import DataCollatorForTokenClassification
from datasets import Dataset, DatasetDict
from sklearn.model_selection import train_test_split

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Definição das labels para o modelo NER
NER_LABELS = [
    "O",  # Outside of a named entity (não é uma entidade nomeada)
    "B-DISTRIBUIDOR",  # Beginning of a distributor entity
    "I-DISTRIBUIDOR",  # Inside of a distributor entity
    "B-PEDIDO",  # Beginning of an order number entity
    "I-PEDIDO",  # Inside of an order number entity
    "B-NOTA_FISCAL",  # Beginning of an invoice number entity
    "I-NOTA_FISCAL",  # Inside of an invoice number entity
]

# Mapeamento de labels para IDs
label2id = {label: i for i, label in enumerate(NER_LABELS)}
id2label = {i: label for i, label in enumerate(NER_LABELS)}

# Função para carregar os dados de treinamento
def load_training_data(file_path: str) -> List[Dict[str, Any]]:
    """Carrega os dados de treinamento do arquivo JSON"""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

# Função para converter os dados para o formato esperado pelo modelo
def convert_to_ner_format(examples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converte os exemplos para o formato de treinamento NER"""
    formatted_examples = []
    
    for example in examples:
        text = example["text"]
        entities = example.get("entities", [])
        
        # Criar uma lista de tokens e suas labels
        tokens = []
        ner_tags = []
        
        # Se não houver entidades, todos os tokens são "O"
        if not entities:
            tokens = text.split()  # Tokenização simples por espaço
            ner_tags = ["O"] * len(tokens)
        else:
            # Ordenar entidades por posição inicial
            entities = sorted(entities, key=lambda x: x["start"])
            
            # Processar o texto e marcar as entidades
            current_pos = 0
            for entity in entities:
                start, end = entity["start"], entity["end"]
                label = entity["label"]
                
                # Adicionar tokens antes da entidade (se houver)
                if start > current_pos:
                    before_entity = text[current_pos:start].strip()
                    if before_entity:
                        before_tokens = before_entity.split()
                        tokens.extend(before_tokens)
                        ner_tags.extend(["O"] * len(before_tokens))
                
                # Adicionar a entidade
                entity_text = text[start:end].strip()
                entity_tokens = entity_text.split()
                
                if entity_tokens:
                    # Primeiro token da entidade
                    tokens.append(entity_tokens[0])
                    ner_tags.append(f"B-{label}")
                    
                    # Restante dos tokens da entidade
                    for token in entity_tokens[1:]:
                        tokens.append(token)
                        ner_tags.append(f"I-{label}")
                
                current_pos = end
            
            # Adicionar tokens após a última entidade (se houver)
            if current_pos < len(text):
                after_entity = text[current_pos:].strip()
                if after_entity:
                    after_tokens = after_entity.split()
                    tokens.extend(after_tokens)
                    ner_tags.extend(["O"] * len(after_tokens))
        
        formatted_examples.append({
            "tokens": tokens,
            "ner_tags": [label2id[tag] for tag in ner_tags]  # Converter para IDs
        })
    
    return formatted_examples

# Função para tokenizar os exemplos para o formato do modelo
def tokenize_and_align_labels(examples, tokenizer):
    """Tokeniza os exemplos e alinha as labels com os tokens do modelo"""
    tokenized_inputs = tokenizer(
        examples["tokens"],
        truncation=True,
        is_split_into_words=True,
        max_length=128,
        padding="max_length"
    )
    
    labels = []
    for i, label in enumerate(examples["ner_tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        
        for word_idx in word_ids:
            # Tokens especiais (CLS, SEP, PAD) recebem label -100
            if word_idx is None:
                label_ids.append(-100)
            # Para o primeiro token de uma palavra, usamos a label correspondente
            elif word_idx != previous_word_idx:
                label_ids.append(label[word_idx])
            # Para tokens subsequentes da mesma palavra, também usamos a label
            else:
                label_ids.append(label[word_idx])
            previous_word_idx = word_idx
        
        labels.append(label_ids)
    
    tokenized_inputs["labels"] = labels
    return tokenized_inputs

# Função principal para treinar o modelo
def train_ner_model(
    training_data_path: str,
    output_dir: str,
    base_model: str = "neuralmind/bert-base-portuguese-cased",
    num_train_epochs: int = 5,
    batch_size: int = 16,
    learning_rate: float = 5e-5,
):
    """Treina um modelo NER personalizado para detecção de entidades"""
    # Carregar os dados de treinamento
    logger.info(f"Carregando dados de treinamento de {training_data_path}")
    examples = load_training_data(training_data_path)
    
    # Converter para o formato NER
    logger.info("Convertendo exemplos para o formato NER")
    ner_examples = convert_to_ner_format(examples)
    
    # Dividir em conjuntos de treinamento e validação
    train_examples, val_examples = train_test_split(ner_examples, test_size=0.2, random_state=42)
    
    # Criar datasets
    train_dataset = Dataset.from_dict({
        "tokens": [example["tokens"] for example in train_examples],
        "ner_tags": [example["ner_tags"] for example in train_examples]
    })
    
    val_dataset = Dataset.from_dict({
        "tokens": [example["tokens"] for example in val_examples],
        "ner_tags": [example["ner_tags"] for example in val_examples]
    })
    
    # Combinar em um DatasetDict
    dataset_dict = DatasetDict({
        "train": train_dataset,
        "validation": val_dataset
    })

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForTokenClassification.from_pretrained(
        base_model,
        num_labels=len(NER_LABELS),
        id2label=id2label,
        label2id=label2id
    )
    
    # Tokenizar e alinhar as labels
    logger.info("Tokenizando e alinhando as labels")
    tokenized_datasets = dataset_dict.map(
        lambda examples: tokenize_and_align_labels(examples, tokenizer),
        batched=True
    )
    
    # Configurar o data collator
    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)
    
    # Configurar os argumentos de treinamento
    training_args = TrainingArguments(
        output_dir=output_dir,
        evaluation_strategy="epoch",
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=num_train_epochs,
        weight_decay=0.01,
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
    )
    
    # Inicializar o trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
    )
    
    # Treinar o modelo
    logger.info("Iniciando o treinamento do modelo")
    trainer.train()
    
    # Salvar o modelo treinado
    logger.info(f"Salvando o modelo treinado em {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    logger.info("Treinamento concluído com sucesso!")
    return model, tokenizer

# Exemplo de dados de treinamento
def create_example_training_data(output_file: str):
    """Cria um arquivo de exemplo com dados de treinamento"""
    examples = [
        {
            "text": "Fiz um pedido com a Officer semana passada",
            "entities": [
                {"start": 17, "end": 24, "label": "DISTRIBUIDOR"}
            ]
        },
        {
            "text": "Queria saber do pedido 112233",
            "entities": [
                {"start": 22, "end": 28, "label": "PEDIDO"}
            ]
        },
        {
            "text": "Nota fiscal 445566 da Alcateia já chegou?",
            "entities": [
                {"start": 12, "end": 18, "label": "NOTA_FISCAL"},
                {"start": 22, "end": 30, "label": "DISTRIBUIDOR"}
            ]
        },
        {
            "text": "Queria saber do pedido 112233 com a Officer",
            "entities": [
                {"start": 22, "end": 28, "label": "PEDIDO"},
                {"start": 38, "end": 45, "label": "DISTRIBUIDOR"}
            ]
        },
        {
            "text": "Meu pedido na Alcateia é o 987654",
            "entities": [
                {"start": 13, "end": 21, "label": "DISTRIBUIDOR"},
                {"start": 26, "end": 32, "label": "PEDIDO"}
            ]
        },
        {
            "text": "A nota fiscal 123456 da Officer está atrasada",
            "entities": [
                {"start": 13, "end": 19, "label": "NOTA_FISCAL"},
                {"start": 23, "end": 30, "label": "DISTRIBUIDOR"}
            ]
        },
        {
            "text": "Comprei na Officer e o número do pedido é 555666",
            "entities": [
                {"start": 12, "end": 19, "label": "DISTRIBUIDOR"},
                {"start": 43, "end": 49, "label": "PEDIDO"}
            ]
        },
        {
            "text": "A nota 778899 da Alcateia ainda não chegou",
            "entities": [
                {"start": 7, "end": 13, "label": "NOTA_FISCAL"},
                {"start": 17, "end": 25, "label": "DISTRIBUIDOR"}
            ]
        },
        {
            "text": "Fiz uma compra na Officer com o pedido 123987",
            "entities": [
                {"start": 17, "end": 24, "label": "DISTRIBUIDOR"},
                {"start": 39, "end": 45, "label": "PEDIDO"}
            ]
        },
        {
            "text": "Preciso rastrear o pedido 654321 da Alcateia",
            "entities": [
                {"start": 24, "end": 30, "label": "PEDIDO"},
                {"start": 34, "end": 42, "label": "DISTRIBUIDOR"}
            ]
        }
    ]
    
    # Salvar os exemplos em um arquivo JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(examples, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Arquivo de exemplo criado em {output_file}")
    return examples

# Função principal
if __name__ == "__main__":
    # Criar diretório para os dados de treinamento se não existir
    os.makedirs("data", exist_ok=True)
    
    # Criar arquivo de exemplo com dados de treinamento
    example_file = "data/training_examples.json"
    create_example_training_data(example_file)
    
    # Verificar se deve treinar o modelo
    should_train = input("Deseja treinar o modelo NER? (s/n): ").lower() == "s"
    
    if should_train:
        # Diretório para salvar o modelo treinado
        output_dir = "/models/ner-model"
        os.makedirs(output_dir, exist_ok=True)
        
        # Treinar o modelo
        train_ner_model(
            training_data_path=example_file,
            output_dir=output_dir,
            base_model="neuralmind/bert-base-portuguese-cased",
            num_train_epochs=3,  # Reduzido para exemplo
            batch_size=8,  # Reduzido para exemplo
        )
    else:
        logger.info("Treinamento cancelado pelo usuário.")