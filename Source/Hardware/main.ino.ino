#include <Wire.h>
#include <LiquidCrystal_PCF8574.h>
#include <DHT.h>
#include <SoftwareSerial.h>

// Pin Definitions
#define DHTPIN 14            // DHT11 Sensor Pin
#define DHTTYPE DHT11        // DHT11 Sensor Type
#define SOIL_SENSOR 32       // Soil Moisture Sensor (Analog)
#define RAIN_SENSOR 35       // Rain Sensor (Digital)
#define PIR_SENSOR 15        // PIR Motion Sensor (Digital)
#define BUZZER 13            // Buzzer
#define RELAY_PIN 27         // Relay for Solenoid Pump
#define GSM_TX 17            // SIM800L TX
#define GSM_RX 16            // SIM800L RX
#define LCD_SDA 21           // I2C SDA for LCD
#define LCD_SCL 22           // I2C SCL for LCD

// Initialize Components
DHT dht(DHTPIN, DHTTYPE);
SoftwareSerial sim800l(GSM_TX, GSM_RX);  // SIM800L communication
LiquidCrystal_PCF8574 lcd(0x27);         // I2C LCD with address 0x27

// Interval for SMS alerts
unsigned long lastMotionAlert = 0;
const unsigned long motionAlertInterval = 60000; // 1 minute
unsigned long lastSMSUpdate = 0;
const unsigned long smsUpdateInterval = 2 * 60 * 60 * 1000; // 2 hours for status update

// Soil moisture threshold for pump control
int soilDryThreshold = 30; // Below 30% triggers the pump

void setup() {
    Serial.begin(115200);
    sim800l.begin(9600);  // SIM800L Baud Rate
    dht.begin();
    
    lcd.begin(16, 2);  // Initialize 16x2 LCD
    lcd.setBacklight(255);  // Turn on backlight

    pinMode(SOIL_SENSOR, INPUT);
    pinMode(RAIN_SENSOR, INPUT);
    pinMode(PIR_SENSOR, INPUT);
    pinMode(BUZZER, OUTPUT);
    pinMode(RELAY_PIN, OUTPUT);
    
    digitalWrite(BUZZER, LOW);
    digitalWrite(RELAY_PIN, LOW);

    lcd.setCursor(0, 0);
    lcd.print("Smart Irrigation");
    delay(2000);
    lcd.clear();
}

void loop() {
    // Read DHT11 Sensor
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    // Read Soil Moisture Sensor (Analog)
    int soilMoisture = analogRead(SOIL_SENSOR);
    int soilPercentage = map(soilMoisture, 0, 4095, 100, 0); // Convert to percentage

    // Read Rain Sensor (Digital)
    bool isRaining = digitalRead(RAIN_SENSOR) == LOW; // LOW means rain detected

    // Read PIR Sensor
    bool motionDetected = digitalRead(PIR_SENSOR);

    // Display Data on Serial Monitor
    Serial.print("Temp: "); Serial.print(temperature); Serial.print("°C | ");
    Serial.print("Humidity: "); Serial.print(humidity); Serial.print("% | ");
    Serial.print("Soil: "); Serial.print(soilPercentage); Serial.print("% | ");
    Serial.print("Rain: "); Serial.print(isRaining ? "Yes" : "No"); Serial.print(" | ");
    Serial.print("Motion: "); Serial.println(motionDetected ? "Yes" : "No");

    // Display on LCD
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Temp: "); lcd.print(temperature); lcd.print("C");
    lcd.setCursor(0, 1);
    lcd.print("Soil: "); lcd.print(soilPercentage); lcd.print("%");

    delay(2000);
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Rain: "); lcd.print(isRaining ? "Yes" : "No");
    lcd.setCursor(0, 1);
    lcd.print("Motion: "); lcd.print(motionDetected ? "Yes" : "No");

    // Pump Control Logic
    if (soilPercentage < soilDryThreshold && !isRaining) {  
        digitalWrite(RELAY_PIN, HIGH);
        Serial.println("Pump ON: Soil is dry.");
        lcd.setCursor(0, 1);
        lcd.print("Pump: ON");
        sendSMS("Pump ON: Soil is dry.");
    } else {
        digitalWrite(RELAY_PIN, LOW);
        Serial.println("Pump OFF.");
        lcd.setCursor(0, 1);
        lcd.print("Pump: OFF");
    }

    // Motion Detection Alert
    if (motionDetected && millis() - lastMotionAlert > motionAlertInterval) {
        digitalWrite(BUZZER, HIGH);
        Serial.println("Motion Detected! Buzzer ON.");
        sendSMS("Alert! Motion Detected in the Field.");
        lastMotionAlert = millis();
        delay(5000); // Buzzer ON for 5 sec
        digitalWrite(BUZZER, LOW);
    }

    // Send Status Update via SMS every 2 hours
    if (millis() - lastSMSUpdate >= smsUpdateInterval) {
        String statusMessage = "Status Update: Temp: " + String(temperature) + "C, Hum: " + String(humidity) + "%, Soil: " + String(soilPercentage) + "%, Rain: " + (isRaining ? "Yes" : "No");
        sendSMS(statusMessage);
        lastSMSUpdate = millis();
    }

    delay(3000); // Wait before next reading
}

// Function to Send SMS using SIM800L
void sendSMS(String message) {
    Serial.println("Sending SMS...");
    sim800l.println("AT+CMGF=1");  // Set SMS mode to text
    delay(100);
    sim800l.println("AT+CMGS=\"+9080553630\""); // Replace with your phone number
    delay(100);
    sim800l.println(message);
    delay(100);
    sim800l.write(26); // Send Ctrl+Z to finish message
    delay(5000);
    Serial.println("SMS Sent!");
}