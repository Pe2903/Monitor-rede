import socket
import sys
import threading

def reader(sock):
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                print("[conexão encerrada pelo servidor]")
                sys.exit(1)
                break
            print(data.decode().rstrip())
    except (ConnectionResetError, BrokenPipeError):
        print("[servidor desconectou inesperadamente]")
        sys.exit(1)
    except Exception as e:
        print(f"[erro de conexão: {e}]")
        sys.exit(1)

def writer(sock):
    try:
        while True:
            line = input("> ").strip()
            if not line:
                continue
            try:
                sock.sendall((line + "\n").encode())
            except (ConnectionResetError, BrokenPipeError):
                print("[erro: servidor desconectou]")
                break
            if line.lower() == "exit":
                break
    except (EOFError, KeyboardInterrupt):
        try:
            sock.sendall(b"exit\n")
        except Exception:
            pass

def main():
    if len(sys.argv) < 3:
        print("Uso: python3 client.py <host> <porta>")
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2])

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            t_read = threading.Thread(target=reader, args=(s,), daemon=True)
            t_read.start()
            writer(s)
            t_read.join(timeout=1)
    except ConnectionRefusedError:
        print(f"[erro: não foi possível conectar ao servidor {host}:{port}]")
        sys.exit(1)
    except Exception as e:
        print(f"[erro de conexão: {e}]")
        sys.exit(1)

if __name__ == "__main__":
    main()