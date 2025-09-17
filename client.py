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
    except Exception:
        pass

def writer(sock):
    try:
        while True:
            line = input("> ").strip()
            if not line:
                continue
            sock.sendall((line + "\n").encode())
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

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        t_read = threading.Thread(target=reader, args=(s,), daemon=True)
        t_read.start()
        writer(s)
        t_read.join(timeout=1)

if __name__ == "__main__":
    main()
