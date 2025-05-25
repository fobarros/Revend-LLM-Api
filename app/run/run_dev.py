import os
import argparse
import uvicorn
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env se existir
load_dotenv()

def main():
    # Configurar o parser de argumentos
    parser = argparse.ArgumentParser(description="Iniciar a API de Identificação de Pedidos em modo de desenvolvimento")
    parser.add_argument(
        "--host", 
        type=str, 
        default=os.getenv("API_HOST", "0.0.0.0"),
        help="Host para executar a API (padrão: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=int(os.getenv("API_PORT", "8000")),
        help="Porta para executar a API (padrão: 8000)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        default=os.getenv("API_DEBUG", "True").lower() in ("true", "1", "t"),
        help="Ativar o modo de recarga automática (padrão: True)"
    )
    parser.add_argument(
        "--storage", 
        type=str, 
        choices=["memory", "redis", "sqlite"],
        default=os.getenv("STORAGE_TYPE", "memory"),
        help="Tipo de armazenamento a ser usado (padrão: memory)"
    )
    
    # Analisar os argumentos
    args = parser.parse_args()
    
    # Definir variáveis de ambiente com base nos argumentos
    os.environ["API_HOST"] = args.host
    os.environ["API_PORT"] = str(args.port)
    os.environ["API_DEBUG"] = str(args.reload).lower()
    os.environ["STORAGE_TYPE"] = args.storage
    
    # Exibir informações de inicialização
    print(f"Iniciando API de Identificação de Pedidos...")
    print(f"Host: {args.host}")
    print(f"Porta: {args.port}")
    print(f"Recarga automática: {args.reload}")
    print(f"Armazenamento: {args.storage}")
    print("\nAcesse a documentação da API em:")
    print(f"  - Swagger UI: http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}/docs")
    print(f"  - ReDoc: http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}/redoc")
    print("\nPressione CTRL+C para encerrar.")
    
    # Iniciar o servidor
    uvicorn.run(
        "main:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload
    )

if __name__ == "__main__":
    main()