#ifndef CONFIG_E220_H
#define CONFIG_E220_H

#include "E220.h"

#define E220_SERIAL_SPEED     9600
#define E220_AIR_DATA_RATE    ADR_2400
#define E220_BAUD_RATE        UDR_9600
#define E220_CHANNEL          23
#define E220_MODE             MODE_NORMAL
#define E220_POWER            Power_21
#define E220_SUB_PACKET_SIZE  SPS_200
#define E220_UART_PARITY      PB_8N1
#define E220_RSSI_ENABLE      true

static uint32_t ADDRESS[] = {2, 3}; 
#endif // CONFIG_E220_H
