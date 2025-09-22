import socket, sys

# Verifica se a porta está livre antes de abrir o servidor
# Basicamente efetua uma conexão de teste, se conectar, significa que a porta está em uso.

def _testar_conexao(porta: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.25)
    try:
        return s.connect_ex(("127.0.0.1", porta)) == 0
    except OSError:
        return False
    finally:
        try: s.close()
        except: pass

def _bind_prova(host: str, porta: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):  # Windows
            s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:  # Linux/macOS
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, porta))
        return True
    except OSError:
        return False
    finally:
        try: s.close()
        except: pass

def porta_livre(host: str, porta: int) -> bool:
    if _testar_conexao(porta):
        return False
    return _bind_prova(host, porta)

def garantir_porta_livre(host: str, porta: int):
    if not porta_livre(host, porta):
        sys.exit(f"Porta {porta} já está em uso em {host}.")
