#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEClient.h>
#include "soc/soc.h"         // Disable brownout detector
#include "soc/rtc_cntl_reg.h"

#define BUTTON_PIN 23 // Optional physical button

BLEClient* pClient;
BLERemoteCharacteristic* pRemoteCharacteristic;
bool connected = false;

const char* serverName = "ESP32_RC_Car";  // Must match BLE server name

// ---------- Connect to BLE server ----------
void connectToServer() {
    BLEScan* pBLEScan = BLEDevice::getScan();
    pBLEScan->setActiveScan(true);

    Serial.println("Scanning for BLE Server...");
    BLEScanResults* results = pBLEScan->start(5); // scan 5 seconds, returns pointer

    for (int i = 0; i < results->getCount(); i++) {
        BLEAdvertisedDevice device = results->getDevice(i);
        if (device.getName() == serverName) {
            Serial.println("Found server!");
            if (pClient->connect(&device)) {
                Serial.println("Connected to server");
                pRemoteCharacteristic = pClient->getService(BLEUUID((uint16_t)0x181C))
                                            ->getCharacteristic(BLEUUID((uint16_t)0x2A56));
                if (pRemoteCharacteristic != nullptr) {
                    Serial.println("Got characteristic");
                    connected = true;
                }
            }
            break;
        }
    }

    if (!connected) {
        Serial.println("Server not found or connection failed");
    }
}

// ---------- Setup ----------
void setup() {
    // Disable brownout detector
    WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

    Serial.begin(115200);
    pinMode(BUTTON_PIN, INPUT_PULLUP);

    BLEDevice::init("");
    pClient = BLEDevice::createClient();

    connectToServer(); // Initial connection
}

// ---------- Loop ----------
void loop() {
    // Reconnect if connection lost
    if (connected && !pClient->isConnected()) {
        Serial.println("Connection lost, reconnecting...");
        connected = false;
        connectToServer();
    } else if (!connected) {
        connectToServer();
    }

    // ---------- Optional: send gesture via button ----------
    static bool lastButtonState = HIGH;
    bool buttonState = digitalRead(BUTTON_PIN);

    if (connected) {
        if (buttonState == LOW && lastButtonState == HIGH) { // Pressed
            pRemoteCharacteristic->writeValue("Forward");
            Serial.println("Button pressed → Forward");
        } else if (buttonState == HIGH && lastButtonState == LOW) { // Released
            pRemoteCharacteristic->writeValue("Stop");
            Serial.println("Button released → Stop");
        }
    }

    lastButtonState = buttonState;
    delay(50); // simple debounce
}
