import socket
import threading
import queue
import sys
import psutil
import time
from common import WELCOME, now_hms

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
                except queue.Empty:
                    continue
                self.conn.sendall((msg + "\n").encode())
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
                else:
                    self.out_q.put(f"[{now_hms()}] Monitor desconhecido: {self.nome}")
                    break
                for _ in range(self.periodo * 10):
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)
        except Exception as e:
            self.out_q.put(f"[{now_hms()}] Erro no monitor {self.nome}: {e}")

def handle_client(conn, addr):
    out_q = queue.Queue()
    writer_stop = threading.Event()
    writer = ClientWriter(conn, out_q, writer_stop)
    writer.start()

    out_q.put(WELCOME.format(t=now_hms()))
    monitores = {}

    try:
        with conn:
            conn.settimeout(0.5)
            while True:
                try:
                    data = conn.recv(1024)
                except socket.timeout:
                    continue
                if not data:
                    break
                cmd = data.decode().strip()

                if cmd.lower() == "exit":
                    out_q.put(f"[{now_hms()}] Encerrando sessão…")
                    break

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

                if "-" in cmd:
                    nome, periodo = cmd.split("-", 1)
                    nome = nome.strip()
                    periodo = periodo.strip()
                    if not periodo.isdigit():
                        out_q.put(f"[{now_hms()}] Período inválido: {periodo}")
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
                else:
                    out_q.put(f"[{now_hms()}] Comando inválido. Exemplos: CPU-5 | memoria-2 | quit CPU | exit")
    finally:
        for _, (thr, ev) in list(monitores.items()):
            ev.set()
        writer_stop.set()
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 server.py <porta>")
        sys.exit(1)
    host = "0.0.0.0"
    port = int(sys.argv[1])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(1)  # Fase 1: um cliente
        print(f"Servidor escutando em {host}:{port}")

        conn, addr = srv.accept()
        print(f"Conexão de {addr}")
        handle_client(conn, addr)
        print("Sessão encerrada.")

if __name__ == "__main__":
    main()
