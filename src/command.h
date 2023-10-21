#ifndef COMMAND_H
#define COMMAND_H

#include <stdint.h>
#include "E220.h"

#define PACKET_HEADER 0xAAAA

enum ResponseStatus {
    CMD_OK = 0x00,
    CMD_NOK = 0x01,
};

typedef struct __attribute__((packed)) {
    uint16_t header;
    uint8_t cid;
    uint8_t value;
} Command_t;

typedef struct __attribute__((packed)) {
    uint8_t cid;
    uint8_t status;
} Response_t;

typedef struct __attribute__((packed)) {
    uint8_t tx_power;
    uint8_t air_data_rate;
    uint8_t uart_baud_rate;
} Config_t;

enum CommandID {
    SET_TX_POWER = 0x00,
    SET_AIR_DATA_RATE = 0x01,
    SET_UART_BAUD_RATE = 0x02,
    GET_CONFIG = 0x03,
};

enum PacketType {
    PACKET_TYPE_DATA = 0x00,
    PACKET_TYPE_RESP = 0x01,
    PACKET_TYPE_CONFIG = 0x02,
};

typedef struct  __attribute__((packed)){
    uint16_t header;
    uint16_t length;
    uint8_t type;
    uint8_t checksum;
} PacketHeader_t;


bool parse_cmd(E220 &radioModule);
void send_packet(uint8_t *packet, size_t len, uint8_t type);

#endif // COMMAND_H
