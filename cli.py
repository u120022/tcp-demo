import socket
import argparse
import PIL.Image

BUF_SIZE = 512

def sequential_send(args):
    ip = socket.gethostbyname(socket.gethostname())
    print(f"Host IPv4: {ip}")

    # TCP socket
    if args.mode == "tcp":
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            print("Creating TCP socket")

            sock.connect((args.interface, args.port))
            print(f"Connecting to TCP socket {args.interface}:{args.port}")

            for i in range(args.n):
                print("Sending to all")
                data = f"<{i}>"
                sock.sendall(data.encode())

    # UDP socket
    elif args.mode == "udp":
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            print("Creating UDP socket")

            for i in range(args.n):
                print(f"Sending to UDP socket {args.interface}:{args.port}")
                data = f"<{i}>"
                size = sock.sendto(data.encode(), (args.interface, args.port))
                assert size == len(data)


def sequential_recp(args):
    ip = socket.gethostbyname(socket.gethostname())
    print(f"Host IPv4: {ip}")

    # TCP socket
    if args.mode == "tcp":
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            print("Creating TCP socket")

            sock.bind((args.interface, args.port))
            print(f"Binding on TCP socket {args.interface}:{args.port}")

            sock.listen()
            print(f"Listening on TCP socket {args.interface}:{args.port}")

            conn, (interface, port) = sock.accept()
            print(f"Accepted connection from {interface}:{port}")

            with conn:
                while True: # Polling
                    data = conn.recv(BUF_SIZE)
                    if not data:
                        break
                    print(f"Received \"{data.decode()}\"")

    # UDP socket
    elif args.mode == "udp":
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            print("Creating UDP socket")

            sock.bind((args.interface, args.port))
            print(f"Binding on UDP socket {args.interface}:{args.port}")

            while True:
                data, (interface, port) = sock.recvfrom(BUF_SIZE)
                print(f"Received \"{data.decode()}\" from {interface}:{port}")


def media_send(args):
    ip = socket.gethostbyname(socket.gethostname())
    print(f"Host IPv4: {ip}")

    records = []
    im = PIL.Image.open(args.file)
    w, h = im.size

    # init
    data = [0] * 12
    data[0:4] = w.to_bytes(4)
    data[4:8] = h.to_bytes(4)
    records.append(bytes(data))

    for y in range(h):
        for x in range(w):
            pixel = im.getpixel((x, y))
            if type(pixel) is not tuple:
                raise ValueError(f"Pixel ({x}, {y}) is None")

            # put pixel
            data = [0] * 12
            data[0:4] = x.to_bytes(4)
            data[4:8] = y.to_bytes(4)
            data[8] = pixel[0]
            data[9] = pixel[1]
            data[10] = pixel[2]
            data[11] = 128
            records.append(bytes(data))

    # cleanup
    data = [0] * 12
    data[11] = 255
    records.append(bytes(data))

    # TCP socket
    if args.mode == "tcp":
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            print("Creating TCP socket")

            sock.connect((args.interface, args.port))
            print(f"Connecting to TCP socket {args.interface}:{args.port}")

            for data in records:
                sock.sendall(data)

    # UDP socket
    elif args.mode == "udp":
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            print("Creating UDP socket")

            for data in records:
                size = sock.sendto(data, (args.interface, args.port))
                assert size == len(data)


def media_recp(args):
    ip = socket.gethostbyname(socket.gethostname())
    print(f"Host IPv4: {ip}")


    # TCP socket
    if args.mode == "tcp":
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            print("Creating TCP socket")

            sock.bind((args.interface, args.port))
            print(f"Binding on TCP socket {args.interface}:{args.port}")

            sock.listen()
            print(f"Listening on TCP socket {args.interface}:{args.port}")

            conn, (interface, port) = sock.accept()
            print(f"Accepted connection from {interface}:{port}")

            concat = bytearray()
            with conn:
                while True: # Polling
                    data = conn.recv(BUF_SIZE)

                    if not data:
                        break

                    concat += data

            im = None
            par_len = len(concat) // 12
            for i in range(par_len):
                data = concat[12 * i:12 * (i + 1)]

                # init
                if data[11] == 0:
                    bx = data[0:4]
                    by = data[4:8]
                    
                    x = int.from_bytes(bx)
                    y = int.from_bytes(by)

                    im = PIL.Image.new("RGB", (x, y))

                # put pixel
                if data[11] == 128:
                    if im is None:
                        raise ValueError("Image is not initialized")

                    bx = data[0:4]
                    by = data[4:8]
                    pixels = data[8:11]

                    x = int.from_bytes(bx)
                    y = int.from_bytes(by)
                    r, g, b = pixels
                    im.putpixel((x, y), (r, g, b))

                # cleanup
                if data[11] == 255:
                    if im is None:
                        raise ValueError("Image is not initialized")

                    im.save(args.file)
                    break


    # UDP socket
    elif args.mode == "udp":
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            print("Creating UDP socket")

            sock.bind((args.interface, args.port))
            print(f"Binding on UDP socket {args.interface}:{args.port}")

            im = None
            while True:
                data = sock.recv(BUF_SIZE)

                # init
                if data[11] == 0:
                    bx = data[0:4]
                    by = data[4:8]
                    
                    x = int.from_bytes(bx)
                    y = int.from_bytes(by)

                    im = PIL.Image.new("RGB", (x, y))

                # put pixel
                if data[11] == 128:
                    if im is None:
                        raise ValueError("Image is not initialized")

                    bx = data[0:4]
                    by = data[4:8]
                    pixels = data[8:11]

                    x = int.from_bytes(bx)
                    y = int.from_bytes(by)
                    r, g, b = pixels
                    im.putpixel((x, y), (r, g, b))

                # cleanup
                if data[11] == 255:
                    if im is None:
                        raise ValueError("Image is not initialized")

                    im.save(args.file)
                    break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_seq = subparsers.add_parser("seq")
    subparsers_seq = parser_seq.add_subparsers()

    parser_send = subparsers_seq.add_parser("send")
    parser_send.add_argument("-m", "--mode", type=str, default="tcp")
    parser_send.add_argument("-i", "--interface", type=str, default="localhost")
    parser_send.add_argument("-p", "--port", type=int, default=8080)
    parser_send.add_argument("-n", type=int, default=10)
    parser_send.set_defaults(func=sequential_send)

    parser_recp = subparsers_seq.add_parser("recp")
    parser_recp.add_argument("-m", "--mode", type=str, default="tcp")
    parser_recp.add_argument("-i", "--interface", type=str, default="localhost")
    parser_recp.add_argument("-p", "--port", type=int, default=8080)
    parser_recp.set_defaults(func=sequential_recp)

    parser_med = subparsers.add_parser("med")
    subparsers_med = parser_med.add_subparsers()

    parser_send = subparsers_med.add_parser("send")
    parser_send.add_argument("-m", "--mode", type=str, default="tcp")
    parser_send.add_argument("-i", "--interface", type=str, default="localhost")
    parser_send.add_argument("-p", "--port", type=int, default=8080)
    parser_send.add_argument("-f", "--file", type=str, default="media_in.png")
    parser_send.set_defaults(func=media_send)

    parser_recp = subparsers_med.add_parser("recp")
    parser_recp.add_argument("-m", "--mode", type=str, default="tcp")
    parser_recp.add_argument("-i", "--interface", type=str, default="localhost")
    parser_recp.add_argument("-p", "--port", type=int, default=8080)
    parser_recp.add_argument("-f", "--file", type=str, default="media_out.png")
    parser_recp.set_defaults(func=media_recp)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
