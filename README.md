# API Inteligente para Identificação de Pedidos

Esta API inteligente é capaz de conversar com o usuário em português e identificar, armazenar e recuperar três informações principais ao longo de uma ou mais mensagens:

- **Distribuidor** (ex: Officer, Alcateia)
- **Número do Pedido**
- **Número da Nota Fiscal**

## Funcionalidades

- **Detecção automática de entidades**: Identifica distribuidores, números de pedido e notas fiscais em mensagens em português.
- **Persistência de contexto**: Mantém o contexto da conversa entre mensagens.
- **Interação natural**: Solicita educadamente as informações que faltam.
- **Suporte a conversas fragmentadas**: O usuário pode fornecer informações em qualquer ordem e em mensagens separadas.

## Estrutura do Projeto

```
.
├── main.py              # Arquivo principal da API
├── config.py            # Configurações do projeto
├── storage.py           # Gerenciamento de armazenamento de contexto
├── nlp.py               # Processamento de linguagem natural
├── auth.py              # Autenticação e segurança
├── train_ner_model.py   # Script para treinar modelo NER personalizado
├── requirements.txt     # Dependências do projeto
└── README.md            # Documentação
```

## Endpoints da API

- **POST /conversar**: Recebe mensagens do usuário, responde e atualiza o contexto.
- **GET /contexto**: Retorna o estado atual da conversa do usuário.
- **DELETE /contexto**: Reinicia a conversa do usuário.
- **POST /token**: Gera um novo token de sessão.

## Exemplos de Uso

### Exemplo 1: Conversa em etapas

```
Usuário: "Fiz pedido na Officer"
API salva: distribuidor = Officer
API responde: "Qual o número do pedido ou nota fiscal?"

Usuário: "Pedido 123456"
API salva: pedido = 123456
API fecha a coleta: "Obrigado! Pedido 123456 na Officer foi registrado."
```

### Exemplo 2: Informações em uma única mensagem

```
Usuário: "Queria saber da nota 778899 da Alcateia"
API salva: nota_fiscal = 778899, distribuidor = Alcateia
API fecha a coleta: "Obrigado! Nota fiscal 778899 da Alcateia foi registrada."
```

## Requisitos

- Python 3.8+
- FastAPI
- Transformers (Hugging Face)
- PyTorch
- Outras dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório:

```bash
git clone <url-do-repositorio>
cd <nome-do-repositorio>
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente (opcional):

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```
NER_MODEL=pucpr/ner-bert-base-portuguese-cased
FALLBACK_NER_MODEL=xlm-roberta-base
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True
STORAGE_TYPE=memory  # memory, redis, sqlite
```

## Execução

Para iniciar a API:

```bash
python main.py
```

A API estará disponível em `http://localhost:8000`.

## Documentação da API

A documentação interativa da API estará disponível em:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Treinamento do Modelo NER

Para treinar um modelo NER personalizado para melhor detecção de entidades:

```bash
python train_ner_model.py
```

Este script criará um conjunto de dados de exemplo e perguntará se você deseja treinar o modelo. O modelo treinado será salvo no diretório `models/ner-model`.

## Armazenamento de Contexto

A API suporta três tipos de armazenamento de contexto:

- **Memória**: Armazenamento em memória (padrão, reinicia ao reiniciar o servidor)
- **Redis**: Armazenamento persistente usando Redis
- **SQLite**: Armazenamento persistente usando SQLite

Para alterar o tipo de armazenamento, modifique a variável `STORAGE_TYPE` no arquivo `.env` ou diretamente no arquivo `config.py`.

## Segurança

A API utiliza tokens JWT para autenticação e segurança das sessões. Os tokens são gerados automaticamente quando uma nova sessão é iniciada e podem ser usados para acessar e modificar o contexto da conversa.

## Licença

[Incluir informações de licença aqui]