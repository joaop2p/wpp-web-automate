# WhatsApp Web Automate

## Resumo:
Uma automação para o WhatsApp Web por meio de ações usando Selenium WebDriver.

## Instalação

Recomendo que instale na sua pasta python \packages (necessário a criação).

```bash
pip install selenium python-dotenv
```

## Configuração

### 1. Arquivo config.ini
Crie um arquivo `config.ini` na raiz do seu projeto:

```ini
[Paths]
database = ./data/whatsapp_data.sqlite
main_file = ./data/contacts.csv
driver_cache = ./cache/chrome_profile
repository_pdf = ./output

[Settings]
limit_hour = 17:30
headless_mode = false
limit_quantity = 100
days_to_update = 5
```

### 2. Arquivo .env (opcional)
```env
LOG_DIR=./logs
APP_CONFIG_FILE=./config.ini
PRIORITY_CITIES_FILE=./priority_cities.json
```

### 3. Arquivo priority_cities.json (opcional)
```json
{
  "cities": ["São Paulo", "Rio de Janeiro", "Belo Horizonte"]
}
```

## Exemplo de Uso

```python
from web.advanced.actions import Actions
from config import Config  # Sua classe Config

def main():
    # Inicializa a configuração (Singleton)
    config = Config()
    
    # Cria a instância de Actions
    bot = Actions(config)
    
    try:
        # Inicia o WhatsApp Web
        print("Iniciando WhatsApp Web...")
        bot.start_whatsapp()
        
        # Exemplo 1: Enviar mensagem simples
        numero = 5511999999999
        if bot.search(numero):
            bot.send_message("Olá! Esta é uma mensagem automática.")
            
            # Verifica se foi entregue
            if bot.entregue():
                print("Mensagem entregue com sucesso!")
            
            bot.exit_chat()
        
        # Exemplo 2: Enviar mensagem com múltiplas linhas
        if bot.search(numero):
            mensagem_multipla = """Linha 1 da mensagem
Linha 2 da mensagem
Linha 3 da mensagem"""
            bot.send_message(mensagem_multipla, split_lines=True)
            bot.exit_chat()
        
        # Exemplo 3: Enviar arquivo
        if bot.search(numero):
            bot.send_file("C:/caminho/para/arquivo.pdf", mode="*")
            bot.exit_chat()
        
        # Exemplo 4: Busca segura (recomendada)
        bot.safe_search(numero)
        bot.send_message("Mensagem via busca segura")
        bot.screenshot("conversa_" + str(numero))
        bot.cancel_safe_search()
        
        # Exemplo 5: Capturar PDF da conversa
        if bot.search(numero):
            bot.print_page("conversa_pdf_" + str(numero))
            bot.exit_chat()
            
    except Exception as e:
        print(f"Erro durante execução: {e}")
    
    finally:
        # Sempre finalizar o driver
        bot.stop()

def exemplo_busca_multiplos_contatos():
    """Exemplo de automação para múltiplos contatos"""
    config = Config()
    bot = Actions(config)
    
    contatos = [5511999999999, 5511888888888, 5511777777777]
    mensagem = "Mensagem automática para todos os contatos"
    
    try:
        bot.start_whatsapp()
        
        for numero in contatos:
            print(f"Processando contato: {numero}")
            
            if bot.search(numero):
                bot.send_message(mensagem)
                
                # Aguarda e verifica entrega
                if bot.entregue():
                    print(f"✅ Mensagem entregue para {numero}")
                else:
                    print(f"⚠️ Mensagem pode não ter sido entregue para {numero}")
                
                bot.exit_chat()
            else:
                print(f"❌ Contato {numero} não encontrado")
    
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        bot.stop()

if __name__ == "__main__":
    main()
    # exemplo_busca_multiplos_contatos()
```

## Métodos Disponíveis

### Inicialização
- `start_whatsapp()`: Inicia o WhatsApp Web e aguarda login
- `kill()`: Finaliza o WebDriver

### Busca de Contatos
- `search(numero)`: Busca contato pelo número (método tradicional)
- `safe_search(numero)`: Busca segura pelo número (recomendado)
- `cancel_safe_search()`: Cancela a busca segura ativa

### Envio de Mensagens
- `send_message(mensagem, split_lines=False)`: Envia mensagem de texto
- `send_file(caminho, mode='*')`: Envia arquivo (image/video/*)

### Navegação
- `exit_chat()`: Sai do chat atual
- `back()`: Volta para tela anterior

### Captura e Verificação
- `screenshot(nome)`: Captura screenshot da conversa
- `print_page(nome)`: Gera PDF da página atual
- `entregue()`: Verifica se última mensagem foi entregue

## Configurações do Driver

O objeto Config controla:
- **headless_mode**: Execução com/sem interface gráfica
- **driver_cache**: Diretório para cache do Chrome (mantém login)
- **repository_pdf**: Diretório para salvamento de PDFs e screenshots
- **limit_hour**: Horário limite para execução
- **limit_quantity**: Quantidade limite de contatos por execução

## Observações Importantes

1. **Cache do Driver**: Configure um diretório de cache para manter o login do WhatsApp
2. **Busca Segura**: Prefira `safe_search()` para melhor estabilidade
3. **Verificação de Entrega**: Use `entregue()` após enviar mensagens importantes
4. **Tratamento de Erros**: Sempre implemente try/catch para maior robustez
5. **Finalização**: Sempre chame `stop()` para fechar o WebDriver adequadamente


## Licença

O software é livre para uso, atualizações da comunidade são bem vindas.