# Copyright (c) 2014 Per Lindstrand

import logging
import socket
import struct
import zlib

LOG = logging.getLogger(__name__)

COMPRESSION_LEVEL = 1


def compress_data(data):
    return zlib.compress(data.encode('ascii'), COMPRESSION_LEVEL)


def decompress_data(data):
    return str(zlib.decompress(data))


class WriteBuffer(object):

    def __init__(self, max_size=None):
        self.buffer = b''
        self.max_size = max_size

    def get_data(self):
        return self.buffer

    def get_size(self):
        return len(self.buffer)

    def is_empty(self):
        return len(self.buffer) == 0

    def can_write(self, length=1):
        if self.max_size is None:
            return True
        else:
            return len(self.buffer) + length <= self.max_size

    def write(self, data):
        if self.can_write(len(data)):
            self.buffer += data
            return True
        else:
            return False

    def write_string(self, data):
        return (self.can_write(2 + len(data)) and
                self.write_uint16(len(data)) and
                self.write(data))

    def write_int8(self, data):
        return self.can_write(1) and self.write(struct.pack('!b', data))

    def write_uint8(self, data):
        return self.can_write(1) and self.write(struct.pack('!B', data))

    def write_int16(self, data):
        return self.can_write(2) and self.write(struct.pack('!h', data))

    def write_uint16(self, data):
        return self.can_write(2) and self.write(struct.pack('!H', data))

    def write_int32(self, data):
        return self.can_write(4) and self.write(struct.pack('!i', data))

    def write_uint32(self, data):
        return self.can_write(4) and self.write(struct.pack('!I', data))

    def write_float(self, data):
        return self.can_write(4) and self.write(struct.pack('!f', data))


class ReadBuffer(object):

    def __init__(self, data=None):
        if data:
            self.buffer = data
        else:
            self.buffer = b''

    def get_data(self):
        return self.buffer

    def get_size(self):
        return len(self.buffer)

    def feed(self, data):
        self.buffer += data

    def peek(self, length):
        if self.can_read(length):
            return self.buffer[:length]
        else:
            return None

    def can_read(self, length=1):
        return len(self.buffer) >= length

    def skip(self, length):
        if self.can_read(length):
            self.buffer = self.buffer[length:]

    def read(self, length):
        if len(self.buffer) >= length:
            data = self.buffer[:length]
            self.buffer = self.buffer[length:]
            return data
        else:
            return None

    def read_string(self):
        if not self.can_read(2):
            return None
        length = struct.unpack('!H', self.peek(2))[0]
        if self.can_read(2 + length):
            self.skip(2)
            return self.read(length)
        else:
            return None

    def read_int8(self):
        data = self.read(1)
        if data:
            data = struct.unpack('!b', data)[0]
        return data

    def read_uint8(self):
        data = self.read(1)
        if data:
            data = struct.unpack('!B', data)[0]
        return data

    def read_int16(self):
        data = self.read(2)
        if data:
            data = struct.unpack('!h', data)[0]
        return data

    def read_uint16(self):
        data = self.read(2)
        if data:
            data = struct.unpack('!H', data)[0]
        return data

    def read_int32(self):
        data = self.read(4)
        if data:
            data = struct.unpack('!i', data)[0]
        return data

    def read_uint32(self):
        data = self.read(4)
        if data:
            data = struct.unpack('!I', data)[0]
        return data

    def read_float(self):
        data = self.read(4)
        if data:
            data = struct.unpack('!f', data)[0]
        return data


class Channel(object):

    #MAX_PACKET_ID = 512
    MAX_PACKET_SIZE = 512

    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr
        self.recv_buffer = ReadBuffer()
        self.send_packet_id = 0
        self.recv_packet_id = None
        self.outbox = []
        self.inbox = []

    def send_packet(self, data):
        compressed_data = compress_data(data)
        #LOG.debug(
        #    'Compression %d -> %d bytes, compression factor %f',
        #    len(data), len(compressed_data),
        #    float(len(compressed_data)) / len(data))
        buf = WriteBuffer(self.MAX_PACKET_SIZE)
        buf.write_uint16(2 + 4 + len(compressed_data))
        buf.write_uint32(self.send_packet_id)
        buf.write_string(compressed_data)
        self.outbox.append(buf.get_data())
        self.send_packet_id = (self.send_packet_id + 1)# % self.MAX_PACKET_ID

    def send_data(self):
        try:
            # check if we have anything to send, and try to send it
            if self.outbox:
                data = self.outbox.pop(0)
                # try until all data is sent
                while data:
                    bytes_sent = self.sock.sendto(data, self.addr)
                    if bytes_sent == 0:
                        # failed to send - probably disconnected
                        return False
                    data = data[bytes_sent:]
            return True
        except socket.error:
            LOG.exception('Socket error')
            return False

    def on_data_received(self, data):
        self.recv_buffer.feed(data)
        if self.recv_buffer.can_read(2):
            buf = ReadBuffer(self.recv_buffer.get_data())
            packet_size = buf.read_uint16()
            if self.recv_buffer.get_size() >= packet_size:
                packet_size = self.recv_buffer.read_uint16()
                packet_id = self.recv_buffer.read_uint32()
                packet_data = decompress_data(
                    self.recv_buffer.read_string())
                if (self.recv_packet_id is None or
                    self.recv_packet_id < packet_id):
                    if (self.recv_packet_id is not None and
                        (self.recv_packet_id + 1) != packet_id):
                        LOG.debug(
                            'Packet loss or out-of-order expect %d but got %d',
                            self.recv_packet_id + 1, packet_id)
                    self.recv_packet_id = packet_id
                    self.inbox.append(packet_data)

    def recv_packet(self):
        if self.inbox:
            return self.inbox.pop(0)
        else:
            return None
