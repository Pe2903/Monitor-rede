import datetime

WELCOME = """{t}: CONECTADO!!
Comandos:
  CPU-<s>        -> monitorar uso de CPU a cada <s> segundos
  memoria-<s>    -> monitorar uso de Memória a cada <s> segundos
  quit <nome>    -> parar um monitor (CPU ou memoria)
  exit           -> encerrar sessão
"""

def now_hms():
    return datetime.datetime.now().strftime("%H:%M:%S")
