# Copyright (c) 2014 Per Lindstrand

import logging
import logging.config
import socket
import select
import networking

LOG = logging.getLogger(__name__)

def main():
    logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

    clients = {}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 9009))

    while True:
        try:
            # check if there's anything on the socket
            readable, _, _ = select.select([sock], [], [], 0)
            if readable:
                data, addr = sock.recvfrom(1024)
                if data:
                    chn = clients.get(addr)
                    if not chn:
                        chn = networking.Channel(sock, addr)
                        clients[addr] = chn
                    chn.on_data_received(data)
                else:
                    # client disconnected
                    if addr in clients:
                        del clients[addr]

            # handle packets
            for addr, chn in clients.items():
                packet = chn.recv_packet()
                if packet:
                    print(addr, 'sent', packet)
                    chn.send_packet(packet)
                    # parse!

            # check if the socket is writable
            _, writable, _ = select.select([], [sock], [], 0)
            if writable:
                removed_clients = []
                for addr, chn in clients.items():
                    if not chn.send_data():
                        removed_clients.append(addr)
                for addr in removed_clients:
                    LOG.info('Client %r disconnected', addr)
                    del clients[addr]
        except socket.error:
            LOG.exception('Socket error')

if __name__ == '__main__':
    main()
