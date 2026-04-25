//To program the Pico:
//    1) Press and hold the Pico's BOOTSEL button
//    2) Plug pico into USB port
//    3) Release the Pico's BOOTSEL button
//    4) Click on the Arduino IDE => button to program

//The RX pin from the ESP01 goes to the TX pin on the pico and vice versa
#include <pio_encoder.h>
const int BUTTON_PIN = 28;
const int TX_PIN = 0;
const int RX_PIN = 1;
bool blinkyFlag = false;

// Motor 1 & 2 Pins (Existing)
const int motor1a = 18;
const int motor1b = 16;
const int l293Enable = 19;
const int motor2a = 13;
const int motor2b = 14;
const int l2932Enable = 15;
const int encoderA = 10;
const int encoder2A = 20;

// Motor 3 Pins (NEW - UPDATE THESE PINS TO MATCH YOUR WIRING)
// these are placeholder pins
const int motor3a = 11;       
const int motor3b = 12;       
const int l2933Enable = 17;   
const int encoder3A = 21;     

int currentCommand[4] = {0};
PioEncoder motor0(encoderA);
PioEncoder motor1(encoder2A);
PioEncoder motor2(encoder3A); // New Motor 3 Encoder

long encoderCounts = -999;
long goal = 0;
long newEncoderCounts;
int speed = 200;
int len = 0;

void setup() {
    Serial.begin(115200);

    Serial1.setRX(RX_PIN);
    Serial1.setTX(TX_PIN);
    Serial1.begin(115200);
    
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(BUTTON_PIN, INPUT);
    
    // Setup Motor 1 & 2
    pinMode(motor1a, OUTPUT);
    pinMode(motor1b, OUTPUT);
    pinMode(l293Enable, OUTPUT);
    pinMode(motor2a, OUTPUT);
    pinMode(motor2b, OUTPUT);
    pinMode(l2932Enable, OUTPUT);
    digitalWrite(l293Enable, HIGH);
    digitalWrite(l2932Enable, HIGH);

    // Setup Motor 3
    pinMode(motor3a, OUTPUT);
    pinMode(motor3b, OUTPUT);
    pinMode(l2933Enable, OUTPUT);
    digitalWrite(l2933Enable, HIGH);
    
    digitalWrite(LED_BUILTIN, HIGH);
    
    // Initialize Encoders
    motor0.begin();
    motor0.reset();
    motor1.begin();
    motor1.reset();
    motor2.begin();
    motor2.reset();
}

void loop() {
  static byte incomingPacket[128] = {0};
  static int dataIndex = 3;

  if(Serial1.available()) {
        memset(incomingPacket,0,sizeof(incomingPacket));
        len = Serial1.readBytes(incomingPacket, sizeof(incomingPacket));
        dataIndex = 3;
       
       for(int j = 0; j < len; j++)
       {
          Serial.println((int)incomingPacket[j]);
       }
    }
    if((int)incomingPacket[dataIndex] != 0)
    {
      Serial.println(dataIndex);
      for(int i = 0; i < 4; i++)
      {
        currentCommand[i] = (int)incomingPacket[dataIndex++];
      }
      Serial.println(currentCommand[0]);

      if(dataIndex == len || (int)incomingPacket[dataIndex] == 0) 
      {
        dataIndex = 3;
        memset(incomingPacket,0,sizeof(incomingPacket));
      } 

      char response = process_command(currentCommand);
      Serial1.write(response);
    }
}

char process_command(int packet[4]) {
    switch(packet[0]){
      case 1: // Original Forward/Backward
          move(packet[1],packet[2],packet[3]);
          return 'M';
      case 2: // Original Turn
          motor0.reset();
          motor1.reset();
          analogWrite(motor1a, (packet[1]*speed));
          analogWrite(motor1b, ((1-packet[1])*speed));
          analogWrite(motor2a, ((1-packet[1])*speed));
          analogWrite(motor2b, (packet[1]*speed));
          encoderCounts = motor0.getCount();
          goal = (int)(encoderCounts + (float)packet[2] * 34.4444);
          
          while(abs(encoderCounts) < goal)
          {
            encoderCounts = motor0.getCount();
          }
          digitalWrite(motor1a, LOW);
          digitalWrite(motor1b, LOW);
          digitalWrite(motor2a, LOW);
          digitalWrite(motor2b, LOW);
          return 'T';
      case 3: // Stop
        digitalWrite(motor1a, LOW);
        digitalWrite(motor1b, LOW);
        digitalWrite(motor2a, LOW);
        digitalWrite(motor2b, LOW);
        digitalWrite(motor3a, LOW);
        digitalWrite(motor3b, LOW);
        Serial.println("Stop");
        delay(packet[2]*10);
        return 'S';
      case 4: // Debug Encoders
        Serial.print("Motor 0 count:");
        Serial.println(motor0.getCount());
        Serial.print("Motor 1 count:");
        Serial.println(motor1.getCount());
        Serial.print("Motor 2 count:");
        Serial.println(motor2.getCount());
        return 'E';
      case 5: // NEW HOLONOMIC MOVE
        int angle = (packet[1] * 256) + packet[2]; 
        int dist = packet[3] * 100; // Scaled distance
        moveHolonomic(angle, dist);
        return 'H';
      default:
        return 'X';
    }
}
    
void move(int dir, int counts1, int counts2)
{
  motor0.reset();
  motor1.reset();
  analogWrite(motor1a, ((1-dir)*speed));
  analogWrite(motor1b, (dir*speed));
  analogWrite(motor2a, ((1-dir)*speed));
  analogWrite(motor2b, (dir*speed));
  encoderCounts = motor0.getCount();
  goal = encoderCounts + (counts1 * 256 + counts2) * 100;
  while(abs(encoderCounts) < goal)
  {
    encoderCounts = motor0.getCount();
  }
}

// NEW HOLONOMIC MOVEMENT FUNCTION
void moveHolonomic(int moveAngle, int distanceCounts) {
    motor0.reset();
    motor1.reset();
    motor2.reset();
    
    // Convert angle to radians for math functions
    float rad = moveAngle * (PI / 180.0);
    
    // Calculate the X and Y velocity vectors based on the angle
    float Vx = cos(rad);
    float Vy = sin(rad);
    
    // 3-Wheel Omni Kinematics (Assuming wheels at 30, 150, 270 degrees)
    float v1 = -0.5 * Vx + 0.866 * Vy;  
    float v2 = -0.5 * Vx - 0.866 * Vy;  
    float v3 = Vx;                      
    
    // Find the maximum speed to normalize the motor outputs (keep them below 255)
    float max_v = max(abs(v1), max(abs(v2), abs(v3)));
    
    // Prevent division by zero if stationary
    if (max_v == 0) max_v = 1;

    int pwm1 = (abs(v1) / max_v) * speed;
    int pwm2 = (abs(v2) / max_v) * speed;
    int pwm3 = (abs(v3) / max_v) * speed;
    
    // Determine directions (0 or 1) based on positive/negative velocity
    int dir1 = (v1 >= 0) ? 1 : 0;
    int dir2 = (v2 >= 0) ? 1 : 0;
    int dir3 = (v3 >= 0) ? 1 : 0;

    encoderCounts = motor0.getCount();
    goal = encoderCounts + distanceCounts;

    // Apply power to all 3 motors
    while(abs(encoderCounts) < goal) {
        analogWrite(motor1a, (dir1 * pwm1));
        analogWrite(motor1b, ((1 - dir1) * pwm1));
        
        analogWrite(motor2a, (dir2 * pwm2));
        analogWrite(motor2b, ((1 - dir2) * pwm2));
        
        analogWrite(motor3a, (dir3 * pwm3));
        analogWrite(motor3b, ((1 - dir3) * pwm3));
        
        encoderCounts = motor0.getCount(); 
    }
    
    // Stop all motors
    analogWrite(motor1a, 0); analogWrite(motor1b, 0);
    analogWrite(motor2a, 0); analogWrite(motor2b, 0);
    analogWrite(motor3a, 0); analogWrite(motor3b, 0);
}
