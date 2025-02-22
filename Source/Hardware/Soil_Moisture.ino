#define SOIL_SENSOR_PIN A0
#define RELAY_PIN 7
#define MOISTURE_THRESHOLD 500  // Adjust based on soil condition

unsigned long lastCheckTime = 0;
const int checkInterval = 2000;  // Check every 2 seconds

void setup() {
    Serial.begin(9600);
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, HIGH); // Pump OFF initially
}

void loop() {
    // Non-blocking timer approach
    if (millis() - lastCheckTime >= checkInterval) {
        lastCheckTime = millis();  // Reset timer

        // Read soil moisture
        int moistureValue = analogRead(SOIL_SENSOR_PIN);
        Serial.print("Moisture Level: ");
        Serial.println(moistureValue);

        // Pump control logic
        if (moistureValue > MOISTURE_THRESHOLD) {  // Soil is dry
            Serial.println("Soil is dry. Turning ON pump.");
            digitalWrite(RELAY_PIN, LOW); // Activate pump
        } else {  // Soil is wet
            Serial.println("Soil is wet. Turning OFF pump.");
            digitalWrite(RELAY_PIN, HIGH); // Deactivate pump
        }
    }
}