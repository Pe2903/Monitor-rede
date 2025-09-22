import socket, sys, threading, os, time

PROMPT = "> "
buf = []                      # caracteres digitados
stop = threading.Event()
io_lock = threading.Lock()    # sincroniza prints

def _texto(): return "".join(buf)

def _prompt():
    with io_lock:
        sys.stdout.write("\r\x1b[2K" + PROMPT + _texto())
        sys.stdout.flush()

def _print_srv(msg):
    with io_lock:
        sys.stdout.write("\r\x1b[2K" + msg + "\n")
        sys.stdout.flush()
    _prompt()

def reader(sock):
    try:
        pend = ""
        while not stop.is_set():
            data = sock.recv(4096)
            if not data:
                _print_srv("[Conexão encerrada pelo servidor]")
                stop.set(); break
            pend += data.decode(errors="replace")
            while "\n" in pend:
                linha, pend = pend.split("\n", 1)
                _print_srv(linha.rstrip())
    except (ConnectionResetError, BrokenPipeError):
        _print_srv("[Servidor desconectou]")
        stop.set()
    except Exception as e:
        _print_srv(f"[Erro de conexão: {e}]")
        stop.set()

def _enviar_linha(sock):
    linha = _texto().strip()
    buf.clear(); _prompt()
    if not linha: return
    try: sock.sendall((linha + "\n").encode())
    except Exception:
        _print_srv("[Erro: servidor desconectou]"); stop.set(); return
    if linha.lower() == "exit": stop.set()

def _loop_windows(sock):
    import msvcrt
    _prompt()
    while not stop.is_set():
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"): _enviar_linha(sock); continue
            if ch in ("\b", "\x7f"): 
                if buf: buf.pop(); _prompt(); continue
            if ch == "\x03":            # Ctrl+C
                try: sock.sendall(b"exit\n")
                except: pass
                stop.set(); break
            if ch in ("\x00", "\xe0"):  # ignora teclas especiais
                if msvcrt.kbhit(): msvcrt.getwch()
                continue
            buf.append(ch); _prompt()
        else:
            time.sleep(0.01)

def _loop_posix(sock):
    import termios, tty, select
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        _prompt()
        while not stop.is_set():
            r,_,_ = select.select([sys.stdin], [], [], 0.1)
            if not r: continue
            ch = sys.stdin.read(1)
            if ch in ("\r", "\n"): _enviar_linha(sock); continue
            if ch in ("\x7f", "\b"): 
                if buf: buf.pop(); _prompt(); continue
            if ch in ("\x03", "\x04"):  # Ctrl+C / Ctrl+D
                try: sock.sendall(b"exit\n")
                except: pass
                stop.set(); break
            if ch.isprintable():
                buf.append(ch); _prompt()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        with io_lock: sys.stdout.write("\n"); sys.stdout.flush()

def writer(sock):
    if os.name == "nt": _loop_windows(sock)
    else: _loop_posix(sock)

def main():
    if len(sys.argv) < 3:
        print("Uso: python3 client.py <host> <porta>"); sys.exit(1)
    host, port = sys.argv[1], int(sys.argv[2])
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            threading.Thread(target=reader, args=(s,), daemon=True).start()
            writer(s)
    except ConnectionRefusedError:
        _print_srv(f"[Erro: não foi possível conectar a {host}:{port}]"); sys.exit(1)
    except Exception as e:
        _print_srv(f"[Erro de conexão: {e}]"); sys.exit(1)

if __name__ == "__main__":
    main()
