#include <OneWire.h>
#include <DallasTemperature.h>
 
// Data wire is plugged into pin 2 on the Arduino
#define ONE_WIRE_BUS 2
 
// Setup a oneWire instance to communicate with any OneWire devices 
// (not just Maxim/Dallas temperature ICs)
OneWire oneWire(ONE_WIRE_BUS);
 
// Pass our oneWire reference to Dallas Temperature.
DallasTemperature sensors(&oneWire);

// Reception buffer
#define BUFFER_SIZE 256
byte receive_buffer[BUFFER_SIZE];
// Index of the next available byte in the buffer
byte buffer_index;

// Packet ready
boolean packet_ready;
 
void setup(void)
{
  // start serial port
  Serial.begin(9600);
  //Serial.println("Dallas Temperature IC Control Library Demo");

  // Start up the library
  sensors.begin();
  packet_ready = false;
  buffer_index = 0;
}
 
void float2array(float *number, byte *b_array)
{
  b_array[0] = (byte)*number;
  b_array[1] = (byte)*(number+1);
  b_array[2] = (byte)*(number+2);
  b_array[3] = (byte)*(number+3);
}

// Pull all the available data from the UART buffer
void pull_data()
{
  while( Serial.available() > 0 && buffer_index < BUFFER_SIZE )
  {
    receive_buffer[buffer_index] = Serial.read();
    buffer_index++;
  }
}

// Remember byte 4 defines the number of bytes of the whole packet. 
// So if I haven't received B4 yet we have to wait for it to confirm the whole packet has been received.
boolean is_full_packet()
{
  byte packet_size;
  if(buffer_index < 5)
  {
    return false;
  }
  // see what the size is according to B4 and compare it with buffer_index to see if all the byte have arrived
  packet_size = receive_buffer[4];
  if(packet_size == buffer_index)
  {
    return true;
  }
  return false;
}

boolean send_ping_response(byte packet_protocol_version, byte packet_id)
{
  byte response_packet[5];
  int sent;
  response_packet[0] = packet_protocol_version | 15;
  response_packet[1] = packet_id;
  response_packet[2] = 240;
  response_packet[3] = 0; // Not used for ping, maybe I should rework the bytes order an put size here instead to prevent this useless byte
  response_packet[4] = 5;

  sent = Serial.write(response_packet, 5);
  if(sent == 5)
  {
    return true;
  }
  return false;
}

// This function reads the full packet and actions on it according to whether it's a request or a response
boolean process_packet()
{
  byte packet_protocol_version, packet_type, packet_id, packet_operation_type, packet_operation_specific, packet_data_format, packet_size;
  boolean is_request = false;
  
  packet_protocol_version = receive_buffer[0] & 240; //get the higher nible
  packet_type = receive_buffer[0] & 15; //get the lower nible
  packet_id = receive_buffer[1];
  packet_operation_type = receive_buffer[2] & 240;
  packet_operation_specific = receive_buffer[2] & 15;
  packet_data_format = receive_buffer[3];
  packet_size = receive_buffer[4];

  // Is it a request or a response?
  if(packet_type == 0)
  {
    is_request = true;
  }
  
  if(is_request)
  {
    switch(packet_operation_type)
    {
      case 240:// PING request
        send_ping_response(packet_protocol_version,packet_id);
        break; 
      default:
        send_ping_response(packet_protocol_version,packet_id);
        break;
    }
  }
  else
  {//response of something we sent first. TODO
    return true;
  }
  return true;
}

void loop(void)
{
  if(packet_ready)
  {
    process_packet();
    //process the packet
    packet_ready = false;
    buffer_index = 0;
  }
  else
  {
    if(Serial.available() > 0)
    {
      //there's data to pull from the UART
      pull_data();
      if(is_full_packet())
      {
        packet_ready = true;
      }
    }
    else
    {
      delay(50);
    }
  }
}

void loop2(void)
{
  int aux;
  float temp;
  byte temp_array[4];
  // call sensors.requestTemperatures() to issue a global temperature
  // request to all devices on the bus
  //Serial.print(" Requesting temperatures...");
  sensors.requestTemperatures(); // Send the command to get temperatures
  //Serial.println("DONE");

  //Serial.print("Temperature for Device 1 is: ");
  temp = sensors.getTempCByIndex(0);
  //Serial.print(temp);
  //Serial.print("Float turned into 4 bytes array: ");
  float2array(&temp, temp_array);
  Serial.write(temp_array, 4);
//  Serial.print(aux); // Why "byIndex"? 
    // You can have more than one IC on the same bus. 
    // 0 refers to the first IC on the wire
  delay(1000);
}
