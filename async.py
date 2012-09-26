import socket, json, select

class AsyncJsonTcp(object):
    """Single-source async server"""
    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, int(port)))
        self.buf = ''

    def send(self, data):
        self.socket.sendall(json.dumps(data) + '\n')

    def receive(self, timeout):
        r, w, x = select.select([self.socket], [], [], timeout)
        if len(r) > 0:
            self.buf += self.socket.recv(4096)
            while '\n' in self.buf:
                data, self.buf = self.buf.split('\n', 1)
                yield json.loads(data)

