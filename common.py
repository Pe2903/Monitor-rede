import datetime

WELCOME = """{t}: CONECTADO!!
Comandos:
  CPU-<s>        -> monitorar uso de CPU a cada <s> segundos
  memoria-<s>    -> monitorar uso de Memória a cada <s> segundos
  disco-<s>      -> monitorar o uso de disco a cada <s> segundos
  usuarios       -> exibe os usuários conectados no servidor
  quit <nome>    -> parar um monitor (CPU ou memoria)
  exit           -> encerrar sessão

Insira o seu comando:
"""

def now_hms():
    return datetime.datetime.now().strftime("%H:%M:%S")
