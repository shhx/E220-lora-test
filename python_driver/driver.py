import time
from collections import deque
from ctypes import sizeof
from itertools import islice
from threading import Thread
from typing import Optional, Type

from e220_config import (AirSpeed, CmdID, Command, Config, MessageRSSI,
                         PackedStructure, PacketHeader, PacketType, Response,
                         ResponseStatus, TxPower, UARTSpeed)
from serial import Serial


class ControllerE220:

    def __init__(self):
        self._header = 0xAAAA
        self.ser = None
        self.port = None
        self.connected = False
        self._rx_thread = None
        self._rx_bytes = deque()
        self._parsed_packets = deque()

    def connect(self, port: str, baudrate: int = 9600):
        self.port = port
        self.ser = Serial(port=self.port, baudrate=baudrate, timeout=1)
        self.ser.flush()
        self.ser.read_all()
        self._rx_thread = Thread(target=self.recv_thread)
        self.connected = True
        self._rx_thread.start()

    def recv_thread(self):
        print('Starting recv thread')
        while self.connected:
            if self.ser.in_waiting != 0:
                data = self.ser.read(self.ser.in_waiting)
                self._rx_bytes.extend(data)
                print("Read: ", data, len(self._rx_bytes))
            resp = self.parse_packet()
            if resp is not None:
                print('Got response')
                print(resp)
                self._parsed_packets.append(resp)
            else:
                time.sleep(0.01)

    def checksum(self, data: bytearray):
        checksum = 0
        for d in data:
            checksum ^= d
        return checksum & 0xFF

    def parse_packet(self):
        if len(self._rx_bytes) < sizeof(PacketHeader):
            return None
        header_bytes = bytearray(islice(self._rx_bytes, 0, sizeof(PacketHeader)))
        packet_header = PacketHeader.from_buffer_copy(header_bytes)
        if packet_header.header != self._header:
            self._rx_bytes.popleft()
            print('Invalid header', len(self._rx_bytes))
            return None
        if len(self._rx_bytes) < packet_header.length + sizeof(PacketHeader):
            print('Not enough bytes: ', len(self._rx_bytes), packet_header.length + sizeof(PacketHeader))
            return None

        packet_bytes = bytearray(islice(self._rx_bytes, sizeof(PacketHeader), packet_header.length + sizeof(PacketHeader)))
        if self.checksum(packet_bytes) != packet_header.checksum:
            self._rx_bytes.popleft()
            print('Invalid checksum')
            return None
        # Remove header bytes
        for _ in range(sizeof(PacketHeader)):
            self._rx_bytes.popleft()

        if packet_header.type == PacketType.RESPONSE:
            packet_bytes = [self._rx_bytes.popleft() for _ in range(packet_header.length)]
            cmd = Response.from_buffer_copy(bytearray(packet_bytes))
        elif packet_header.type == PacketType.CONFIG:
            packet_bytes = [self._rx_bytes.popleft() for _ in range(packet_header.length)]
            cmd = Config.from_buffer_copy(bytearray(packet_bytes))
        elif packet_header.type == PacketType.DATA:
            packet_bytes = [self._rx_bytes.popleft() for _ in range(packet_header.length)]
            cmd = MessageRSSI.from_buffer_copy(bytearray(packet_bytes))
        else:
            print('Unknown packet type')
            return None
        return cmd

    def set_tx_power(self, power: TxPower):
        if not self.connected:
            return

        cmd = Command()
        cmd.header = self._header
        cmd.cid = CmdID.TX_POWER
        cmd.value = power
        self.send_cmd(cmd)
        status = self.get_response(CmdID.TX_POWER)
        if status != ResponseStatus.OK:
            raise Exception('Error setting air speed')

    def set_air_speed(self, speed: AirSpeed):
        if not self.connected:
            return

        cmd = Command()
        cmd.header = self._header
        cmd.cid = CmdID.AIR_SPEED
        cmd.value = speed
        self.send_cmd(cmd)
        status = self.get_response(CmdID.AIR_SPEED)
        if status != ResponseStatus.OK:
            raise Exception('Error setting air speed')

    def set_uart_speed(self, speed: UARTSpeed):
        if not self.connected:
            return
        cmd = Command()
        cmd.header = self._header
        cmd.cid = CmdID.UART_DATA_RATE
        cmd.value = speed
        self.send_cmd(cmd)
        status = self.get_response(CmdID.UART_DATA_RATE)
        if status != ResponseStatus.OK:
            raise Exception('Error setting air speed')

    def get_config(self) -> Optional[Config]:
        if not self.connected:
            return
        cmd = Command()
        cmd.header = self._header
        cmd.cid = CmdID.GET_CONFIG
        cmd.value = 0
        self.send_cmd(cmd)
        config = self.get_data(Config, timeout=1)
        return config

    def send_cmd(self, cmd: Command):
        if not self.connected:
            return
        data = bytes(cmd)
        # print(data)
        self.ser.write(data)

    def disconnect(self):
        if not self.connected:
            return
        self.connected = False
        if self._rx_thread is not None:
            self._rx_thread.join(timeout=2)
        self._rx_bytes.clear()
        self._parsed_packets.clear()
        self.ser.close()

    def get_data(self, packet_type: Type[PackedStructure], timeout: float = 0) -> Optional[PackedStructure]:
        if not self.connected:
            return None
        t0 = time.time()
        while len(self._parsed_packets) == 0:
            time.sleep(0.01)
            if time.time() - t0 > timeout:
                return None
        while True:
            if filter(lambda p: isinstance(p, packet_type), self._parsed_packets):
                packet = next(filter(lambda p: isinstance(p, packet_type), self._parsed_packets))
                self._parsed_packets.remove(packet)
                return packet
            if time.time() - t0 > timeout:
                return None

    def get_response(self, command_id, timeout: float = 3.0):
        t0 = time.time()
        while len(self._parsed_packets) == 0:
            time.sleep(0.01)
            if time.time() - t0 > timeout:
                raise Exception('Timeout waiting for response')
        while True:
            print('Getting response: ', self._parsed_packets)
            for packet in self._parsed_packets:
                if isinstance(packet, Response) and packet.cid == command_id:
                    status = packet.status
                    self._parsed_packets.remove(packet)
                    return status
            time.sleep(0.01)
            if time.time() - t0 > timeout:
                raise Exception('Timeout waiting for response')

if __name__ == '__main__':
    controller = ControllerE220()
    controller.connect('COM5', 115200)

    # config = controller.get_config()
    # print(config)


    controller.set_tx_power(TxPower.POWER_21)
    controller.set_air_speed(AirSpeed.AIR_DATA_RATE_111_625)
    controller.set_uart_speed(UARTSpeed.UART_DATA_RATE_115200)
    # config = controller.get_config()
    # print(config)

    controller.disconnect()
