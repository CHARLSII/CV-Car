#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include "soc/soc.h"         // Disable brownout detector
#include "soc/rtc_cntl_reg.h"

// ---------- Motor Pin Definitions ----------
#define ENA 19  // Left motor enable
#define IN1 18
#define IN2 5
#define IN3 17
#define IN4 16
#define ENB 4   // Right motor enable

// ---------- BLE ----------
BLECharacteristic *pCharacteristic;
bool deviceConnected = false;

// ---------- Motor Control Functions ----------
void moveForward() {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
    digitalWrite(ENA, HIGH);
    digitalWrite(ENB, HIGH);
}

void moveBackward() {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
    digitalWrite(ENA, HIGH);
    digitalWrite(ENB, HIGH);
}

void turnLeft() {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
    digitalWrite(ENA, HIGH);
    digitalWrite(ENB, HIGH);
}

void turnRight() {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
    digitalWrite(ENA, HIGH);
    digitalWrite(ENB, HIGH);
}

void stopMotors() {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
    digitalWrite(ENA, LOW);
    digitalWrite(ENB, LOW);
}

// ---------- BLE Callbacks ----------
class MyServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        Serial.println("Client connected");
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        stopMotors();
        Serial.println("Client disconnected");
    }
};

class MyCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pChar) {
        String value = pChar->getValue();
        Serial.print("Received: ");
        Serial.println(value);

        if (value == "Forward") moveForward();
        else if (value == "Reverse") moveBackward();
        else if (value == "Left") turnLeft();
        else if (value == "Right") turnRight();
        else if (value == "Stop") stopMotors();
    }
};

// ---------- Setup ----------
void setup() {
    // Disable brownout detector
    WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

    Serial.begin(115200);

    // Motor pins
    pinMode(IN1, OUTPUT);
    pinMode(IN2, OUTPUT);
    pinMode(IN3, OUTPUT);
    pinMode(IN4, OUTPUT);
    pinMode(ENA, OUTPUT);
    pinMode(ENB, OUTPUT);

    stopMotors();

    // BLE setup
    BLEDevice::init("ESP32_RC_Car");  // Name of BLE server
    BLEServer *pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    BLEService *pService = pServer->createService(BLEUUID((uint16_t)0x181C));
    pCharacteristic = pService->createCharacteristic(
                          BLEUUID((uint16_t)0x2A56),
                          BLECharacteristic::PROPERTY_WRITE
                      );
    pCharacteristic->setCallbacks(new MyCallbacks());
    pService->start();

    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->start();
    Serial.println("BLE RC Car Server ready!");
}

// ---------- Loop ----------
void loop() {
    // Nothing needed; BLE callback handles motor control
}
