#include <Arduino.h>
#define FREQUENCY_868
#define E220_30
#include <LoRa_E220.h>

#define AUX_PIN 25
#define M0_PIN 15
#define M1_PIN 2
#define TX_PIN 22
#define RX_PIN 17

#define DESTINATION_ADDL 3
#define ROOM "Kitchen"

#define ENABLE_RSSI true
#define LoRa_E220_DEBUG

LoRa_E220 e220ttl(TX_PIN, RX_PIN, &Serial1, AUX_PIN, M0_PIN, M1_PIN, UART_BPS_RATE_9600); //  RX AUX M0 M1

struct Message {
	char type[5];
	char message[8];
	float temperature;
};

void setup() {
    Serial.begin(9600);
    delay(500);

    // Startup all pins and UART
    e220ttl.begin();
    ResponseStructContainer rc = e220ttl.getModuleInformation();
    Serial.println(rc.status.getResponseDescription());
    if (rc.status.code != E220_SUCCESS){
    	Serial.println("Error on startup");
    	while(1);
    }
    rc = e220ttl.getConfiguration();
    Configuration configuration = *(Configuration*) rc.data;
    Serial.println("Hi, I'm going to send message!");

    struct	Message message = {"TEMP", ROOM, 19.2};

    // Send message
    ResponseStatus rs = e220ttl.sendFixedMessage(0, DESTINATION_ADDL, 23, &message, sizeof(Message));
    // Check If there is some problem of succesfully send
    Serial.println(rs.getResponseDescription());
}

void loop() {
	// If something available
  if (e220ttl.available()>1) {
	  // read the String message
#ifdef ENABLE_RSSI
		ResponseStructContainer rsc = e220ttl.receiveMessageRSSI(sizeof(Message));
#else
		ResponseStructContainer rsc = e220ttl.receiveMessage(sizeof(Message));
#endif

	// Is something goes wrong print error
	if (rsc.status.code!=1){
		Serial.println(rsc.status.getResponseDescription());
	}else{
		// Print the data received
		Serial.println(rsc.status.getResponseDescription());
		struct Message message = *(Message*) rsc.data;
		Serial.println(message.type);
		Serial.println(message.message);
		Serial.println(message.temperature);

#ifdef ENABLE_RSSI
		Serial.print("RSSI: "); Serial.println(rsc.rssi, DEC);
#endif
	}
  }
    struct Message message = { "TEMP", ROOM, 0 };
    message.temperature = 69;

    // Send message
    ResponseStatus rs = e220ttl.sendFixedMessage(0, DESTINATION_ADDL, 23, &message, sizeof(Message));
    // Check If there is some problem of succesfully send
    Serial.println(rs.getResponseDescription());
    delay(1000);
}
