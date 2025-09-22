import datetime

WELCOME = """{t}: CONECTADO!!
Comandos:
  cpu-<s>        -> Monitora uso da CPU a cada <s> segundos.
  memoria-<s>    -> Monitora uso da Memória a cada <s> segundos.
  disco-<s>      -> Monitora o uso do disco a cada <s> segundos.
  rede-<s>       -> Monitora o uso de rede a cada <s> segundos.
  usuarios       -> Exibe os usuários conectados no servidor.
  quit <nome>    -> Parar um monitor.
  exit           -> Encerrar sessão.

Insira o seu comando:
"""

AJUDA = """
Comandos disponíveis:
  cpu-<s>        -> Monitora uso de CPU a cada <s> segundos.
  memoria-<s>    -> Monitora uso de Memória a cada <s> segundos.
  disco-<s>      -> Monitora o uso de disco a cada <s> segundos.
  rede-<s>       -> Monitora o uso de rede a cada <s> segundos.
  usuarios       -> Exibe os usuários conectados no servidor.
  quit <nome>    -> Parar um monitor.
  exit           -> Encerrar sessão.

  Exemplo de uso: CPU-5 -> recebe status do CPU a cada 5 segundos

Insira o seu comando:

"""

def now_hms():
    return datetime.datetime.now().strftime("%H:%M:%S")
