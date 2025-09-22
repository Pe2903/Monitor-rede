# Monitor-Rede

Sistema de monitoramento remoto desenvolvido para a disciplina de Redes de Computadores.

## Sobre o Projeto

Este projeto implementa um sistema cliente/servidor que permite monitorar recursos do sistema (CPU, memória, disco e rede) remotamente via TCP. Foi desenvolvido seguindo as especificações da Fase 1, 2 e 3 do projeto prático.

## Como Usar

### Rodar o Servidor
```bash
python3 server.py 8080 3
```
- 8080 = porta do servidor
- 3 = máximo de usuários simultâneos

### Conectar um Cliente
```bash
python3 client.py localhost 8080
```

## Comandos Disponíveis

```
CPU-5        -> monitora CPU a cada 5 segundos
memoria-3    -> monitora memória a cada 3 segundos  
disco-10     -> monitora disco a cada 10 segundos
rede-2       -> monitora rede a cada 2 segundos
usuarios     -> mostra quem está conectado
quit CPU     -> para o monitor de CPU
exit         -> sai do programa
```

## Exemplo de Uso

```
> CPU-2
[14:30:25] Monitor CPU iniciado a cada 2s.
[14:30:27] CPU: 15.2%
[14:30:29] CPU: 18.7%

> memoria-3
[14:30:33] Memória: 45.2% (2048MB/4096MB)

> usuarios
[14:30:35] Usuários conectados: 2
```

## Funcionalidades Implementadas

### Fase 1
- Monitoramento básico de CPU e memória
- Threads para cada monitor
- Comandos quit e exit

### Fase 2  
- Suporte a múltiplos clientes simultâneos
- Limite de usuários configurável
- Isolamento de dados entre clientes

### Fase 3
- Tratamento robusto de exceções
- Validação de entrada de comandos
- Mensagens de erro claras
- Sem warnings no terminal

### Melhorias Adicionais
- Monitoramento de disco e rede
- Comando para ver usuários conectados
- Verificação de porta antes de iniciar servidor
- Melhorias na interface do usuário

## Dependências

```bash
pip3 install psutil
```

## Arquivos do Projeto

- `server.py` - Servidor principal
- `client.py` - Cliente
- `common.py` - Funções compartilhadas
- `verificar_porta.py` - Utilitário para verificar portas

## Desenvolvimento

O projeto foi desenvolvido incrementalmente, começando com funcionalidades básicas e adicionando melhorias ao longo do tempo. Cada fase foi testada e validada antes de prosseguir.

### Principais Desafios
- Implementar comunicação bidirecional assíncrona
- Gerenciar múltiplos clientes simultâneos
- Tratar exceções de rede adequadamente
- Validar entrada de comandos

## Como Testar

1. Inicie o servidor em um terminal
2. Conecte um ou mais clientes em terminais separados
3. Teste os comandos de monitoramento
4. Teste desconexões inesperadas
5. Verifique se não há erros ou warnings
