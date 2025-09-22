import socket
import threading
import queue
import sys
import psutil
import time
import signal
from common import WELCOME, now_hms
from verificar_porta import garantir_porta_livre

desligar_server = threading.Event()

usuarios = []
clientes_lock = threading.Lock()

def _handle_desligar(sig, frame):
    print("Encerrando o servidor...")
    desligar_server.set()

    with clientes_lock: snapshot = list(usuarios)
    for c in snapshot:
        c["out_q"].put(f"[{now_hms()}] Servidor encerrando. Você será desconectado.")
        c["out_q"].put(None)


    

signal.signal(signal.SIGINT, _handle_desligar)

class ClientWriter(threading.Thread):
    def __init__(self, conn, out_q, stop_event):
        super().__init__(daemon=True)
        self.conn = conn
        self.out_q = out_q
        self.stop_event = stop_event

    def run(self):
        try:
            while not self.stop_event.is_set():
                try:
                    msg = self.out_q.get(timeout=0.2)
                    if msg is None:
                        break
                except queue.Empty:
                    continue
                try:
                    self.conn.sendall((msg + "\n").encode())
                except (OSError, ConnectionResetError, BrokenPipeError):
                    break
        except Exception:
            self.stop_event.set()

class MonitorThread(threading.Thread):
    def __init__(self, nome, periodo, out_q, stop_event):
        super().__init__(daemon=True)
        self.nome = nome
        self.periodo = max(1, int(periodo))
        self.out_q = out_q
        self.stop_event = stop_event

    def run(self):
        try:
            while not self.stop_event.is_set():
                if self.nome.upper() == "CPU":
                    valor = psutil.cpu_percent(interval=None)
                    self.out_q.put(f"[{now_hms()}] CPU: {valor:.1f}%")
                elif self.nome.lower() == "memoria":
                    mem = psutil.virtual_memory()
                    self.out_q.put(
                        f"[{now_hms()}] Memória: {mem.percent:.1f}% "
                        f"({mem.used//(1024**2)}MB/{mem.total//(1024**2)}MB)"
                    )
                elif self.nome.lower() == "disco":
                    io1 = psutil.disk_io_counters()
                    time.sleep(1) 
                    io2 = psutil.disk_io_counters()

                    read_bytes = io2.read_bytes - io1.read_bytes
                    write_bytes = io2.write_bytes - io1.write_bytes

                    self.out_q.put(
                        f"[{now_hms()}] Disco: Leitura {read_bytes/1024:.1f} KB/s | Escrita {write_bytes/1024:.1f} KB/s"
                    )
                elif self.nome.lower() == "rede":
                    prev = psutil.net_io_counters()
                    while not self.stop_event.is_set():
                        time.sleep(self.periodo)
                        cur = psutil.net_io_counters()
                        sent = cur.bytes_sent - prev.bytes_sent
                        recv = cur.bytes_recv - prev.bytes_recv
                        prev = cur
                        self.out_q.put(
                            f"[{now_hms()}] Rede: ↑ {sent/1024:.1f} KB/s | ↓ {recv/1024:.1f} KB/s"
                        )
                else:
                    self.out_q.put(f"[{now_hms()}] Monitor desconhecido: {self.nome}")
                    break
                for _ in range(self.periodo * 10):
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)
        except Exception as e:
            self.out_q.put(f"[{now_hms()}] Erro no monitor {self.nome}: {e}")

def handle_client(conn, addr, limite):
    out_q = queue.Queue()
    writer_stop = threading.Event()
    writer = ClientWriter(conn, out_q, writer_stop)
    writer.start()

    with clientes_lock: usuarios.append({"conn": conn, "out_q": out_q, "writer_stop": writer_stop})

    out_q.put(WELCOME.format(t=now_hms()))
    monitores = {}

    try:
        with conn:
            conn.settimeout(0.5)
            while True:
                if desligar_server.is_set(): out_q.put("...Servidor encerrando..."); break

                try:
                    data = conn.recv(1024)
                except socket.timeout:
                    continue
                except (ConnectionResetError, BrokenPipeError):
                    print(f"[{now_hms()}] Cliente {addr} desconectou inesperadamente.")
                    break
                if not data:
                    break
                cmd = data.decode().strip()

                if cmd.lower() == "exit":
                    out_q.put(f"[{now_hms()}] Encerrando sessão…")
                    break

                if cmd.lower() == "usuarios":
                    with clientes_lock:
                        infos = [f"{c['conn'].getpeername()[0]}:{c['conn'].getpeername()[1]}" for c in usuarios]
                    out_q.put(f"{len(infos)} usuário(s) conectado(s): " + ", ".join(infos) if infos else "Nenhum usuário conectado.")
                    continue

                if cmd.lower().startswith("quit"):
                    parts = cmd.split(maxsplit=1)
                    if len(parts) == 2:
                        nome = parts[1].strip()
                        key = nome.upper() if nome.upper() == "CPU" else nome.lower()
                        if key in monitores:
                            thr, ev = monitores.pop(key)
                            ev.set()
                            out_q.put(f"[{now_hms()}] Monitor {nome} interrompido.")
                        else:
                            out_q.put(f"[{now_hms()}] Monitor {nome} não está ativo.")
                    else:
                        out_q.put(f"[{now_hms()}] Use: quit CPU | quit memoria")
                    continue

                if "-" in cmd and cmd.count("-") == 1:
                    nome, periodo = cmd.split("-", 1)
                    nome = nome.strip()
                    periodo = periodo.strip()
                    if not nome or not periodo:
                        out_q.put(f"[{now_hms()}] Formato inválido. Use: CPU-5 ou memoria-3")
                        continue
                    if not periodo.isdigit() or int(periodo) <= 0:  
                        out_q.put(f"[{now_hms()}] Período inválido: {periodo}. Use um número maior que 0.")
                        continue

                    key = nome.upper() if nome.upper() == "CPU" else nome.lower()
                    if key in monitores:
                        thr, ev = monitores.pop(key)
                        ev.set()

                    stop_ev = threading.Event()
                    thr = MonitorThread(nome=nome, periodo=int(periodo),
                                        out_q=out_q, stop_event=stop_ev)
                    monitores[key] = (thr, stop_ev)
                    thr.start()
                    out_q.put(f"[{now_hms()}] Monitor {nome} iniciado a cada {periodo}s.")
                    print(f"O usuário {addr} solicitou o monitor {nome} a cada {periodo}s.")
                else:
                    out_q.put(f"[{now_hms()}] Comando inválido. Exemplos: CPU-5 | memoria-2 | disco-3 | usuarios | quit CPU | exit")
    finally:
        limite.release()

        for _, (thr, ev) in list(monitores.items()):
            ev.set()
            
        out_q.put(None)
        writer.join(timeout=1)

        writer_stop.set()
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        with clientes_lock: usuarios[:] = [c for c in usuarios if c["conn"] is not conn]
        print(f"{addr} desconectou.")

def main():
    if len(sys.argv) < 3:
        print("Uso: python3 server.py <porta> <máx usuários>")
        sys.exit(1)
    host = "0.0.0.0"
    port = int(sys.argv[1])
    qnt = int(sys.argv[2])

    garantir_porta_livre(host, port)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            try:
                srv.bind((host, port))
            except OSError:
                print("Falha ao conectar. Esta porta provavelmente já está em uso.")
                sys.exit(1)

            srv.listen(qnt)
            srv.settimeout(0.5)
            print(f"Servidor escutando em {host}:{port}. Limitado a {qnt} usuário(s).")

            limite = threading.Semaphore(qnt)

            while not desligar_server.is_set():
                try:
                    conn, addr = srv.accept()

                    if not limite.acquire(blocking=False):
                        try:
                            conn.sendall(b"Servidor ocupado. Tente novamente mais tarde.\n")
                            print(f"{addr} não conseguiu se conectar - Servidor atingiu o limite de usuários.")
                        except OSError:
                            pass
                        conn.close()
                        continue

                    print(f"{addr} se conectou. ({len(usuarios) + 1}/{qnt})")

                    threading.Thread(target=handle_client, args=(conn, addr, limite), daemon=True).start() # cada cliente gera sua própria thread.
                except socket.timeout:
                    continue
                except OSError:
                    break
    finally:
        print("Servidor finalizado.")
            
            

if __name__ == "__main__":
    main()