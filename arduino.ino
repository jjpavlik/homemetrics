#include <OneWire.h>
#include <DallasTemperature.h>
#include <stdlib.h>
#include <LiquidCrystal.h>

// Data wire is plugged into pin 2 on the Arduino
#define ONE_WIRE_BUS 2

#define LOOP_DELAY 50
// Number of rotating pairs for the LCD. Pairs are 32 bytes size.
#define LCD_PAIRS 8
#define LCD_ROTATION_FACTOR 40
#define LCD_PAIRS_SIZE 32*LCD_PAIRS
char available_lcd_pairs[LCD_PAIRS_SIZE];
available_lcd_pairs[0] = "-Just Started-";
available_lcd_pairs[16] = "No Data Avail.";
byte current_pair = 0;//The one present on the LCD at the moment.
byte used_pairs = B00000001;//Bitmap of pairs in use, remember pair[0] is used by default
int rotate_lcd = LCD_ROTATION_FACTOR * LOOP_DELAY;//Considering the delay in loop() is 50ms, this results in ~2000ms between LCD rotation

// Setup a oneWire instance to communicate with any OneWire devices
// (not just Maxim/Dallas temperature ICs)
OneWire oneWire(ONE_WIRE_BUS);

// Pass our oneWire reference to Dallas Temperature.
DallasTemperature sensors(&oneWire);

// LCD CONFIGURATION
// PINs
const int rs = 12, en = 8, d4 = 6, d5 = 5, d6 = 4, d7 = 3;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// Reception buffer
#define BUFFER_SIZE 256
byte receive_buffer[BUFFER_SIZE];
// Index of the next available byte in the buffer
byte buffer_index;

//B0
// Higher nible
#define PROTOCOL 17 // 0001 ____
// Lower nible
#define RESPONSE 15 // ____ 1111
#define REQUEST 0 // ____ 0000

// B2
// Higher nibble
#define READ 0  // 0000 ____
#define WRITE 16 // 0001 ____
#define PING 240 // 1111 0000
#define CONTROL 224 // 1110 ____
//Lower nible defines the sensor ...
#define GET_SENSORS 15 // ____ 1111
#define TEMP1 0
#define TEMP2 1
#define SCREEN1 2

// Sensors
// Higher nibble is type
#define TEMP 0 // 0000 ____
#define LCD 32 // 0010 ____
// Lower nible is format
#define INTEGER 0
#define FLOAT 1
#define CHAR 2


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

  // Start lcd
  lcd.begin(16, 2);
  update_screen();
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
//  Serial.println("OOPs");
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
  response_packet[0] = packet_protocol_version | RESPONSE;
  response_packet[1] = packet_id;
  response_packet[2] = PING;
  response_packet[3] = 0; // Not used for ping, maybe I should rework the bytes order an put size here instead to prevent this useless byte
  response_packet[4] = 5;

  sent = Serial.write(response_packet, 5);
  if(sent == 5)
  {
    return true;
  }
  return false;
}

// Answer packaget for Write operations, some sort of ACK
boolean send_write_response(byte packet_protocol_version, byte packet_id)
{
  byte response_packet[5];
  int sent;
  response_packet[0] = packet_protocol_version | RESPONSE;
  response_packet[1] = packet_id;
  response_packet[2] = WRITE;
  response_packet[3] = 0; // Not used for ping, maybe I should rework the bytes order an put size here instead to prevent this useless byte
  response_packet[4] = 5;

  sent = Serial.write(response_packet, 5);
  if(sent == 5)
  {
    return true;
  }
  return false;
}

// This message lets the collector know which sensors are available on this devices
// along with the name, and the format of the data.
boolean send_available_sensors(byte packet_protocol_version, byte packet_id)
{
    // Maybe this should be a single global buffer, to prevent taking stack memory in every send_XXX function...
    byte response_packet[30];
    int sent;
    response_packet[0] = packet_protocol_version | RESPONSE;
    response_packet[1] = packet_id;
    response_packet[2] = CONTROL | GET_SENSORS;
    response_packet[3] = 0; // Not used for ping, maybe I should rework the bytes order an put size here instead to prevent this useless byte
    response_packet[4] = 19; // HEY, can we automatically calculate the size?
    response_packet[5] = 't';
    response_packet[6] = 'e';
    response_packet[7] = 'm';
    response_packet[8] = 'p';
    response_packet[9] = '1';
    response_packet[10] = '\n';
    response_packet[11] = TEMP | INTEGER;

    response_packet[12] = 't';
    response_packet[13] = 'e';
    response_packet[14] = 'm';
    response_packet[15] = 'p';
    response_packet[16] = '2';
    response_packet[17] = '\n';
    response_packet[18] = TEMP | FLOAT;

    response_packet[19] = 's';
    response_packet[20] = 'c';
    response_packet[21] = 'r';
    response_packet[22] = 'e';
    response_packet[23] = 'e';
    response_packet[24] = 'n';
    response_packet[25] = '1';
    response_packet[26] = '\n';
    response_packet[27] = LCD | CHAR;

    sent = Serial.write(response_packet, 28);
    if(sent == 28)
    {
      return true;
    }
    return false;
}

boolean send_sensor_read(byte packet_protocol_version, byte packet_id, byte sensor)
{
    // Maybe this should be a single global buffer, to prevent taking stack memory in every send_XXX function...
    char response_packet[15];
    int sent;
    float temp;

    response_packet[0] = packet_protocol_version | RESPONSE;
    response_packet[1] = packet_id;
    response_packet[2] = READ | TEMP1;
    response_packet[3] = 0;
//    response_packet[4] = 5;

    switch (sensor) {
        case TEMP1:
            sensors.requestTemperatures(); // Send the command to get temperatures
            temp = sensors.getTempCByIndex(0);
            dtostrf(temp, 4, 1, &response_packet[5]); //So the first byte should start here, and considering precision is 1, this should be up to 4 bytes.
            response_packet[4] = 9;
            sent = Serial.write(response_packet, 9);
        break;
    }
    return true;
}

// Pulls the data from receive_buffer and places it in row0 and row1
// Meh... all this memory movement might not be necessary, but it is a start (maybe could retrieve slot number earlier and then copy the strings directly to the LCD_PAIRS array).
// TODO: maybe there should be some boundary checks here, to make sure we don't
// go beyond row0 and row1...
boolean read_screen_data(byte size)
{
  // Data should start in B5 in receive_buffer. Two strings should come, separated by '\n'
  byte *read, *aux_row0, *aux_row1;
  byte ctr = 0;
  byte boundary = size - 5;// Used to make sure we don't read beyond the what we received.
  byte rboundary = 16;// To make sure I don't go beyond row0 or row1
  byte slot;
  byte position = B00000001;

  read = &receive_buffer[5];
  slot = receive_buffer[size - 1]; //Don't really need to copy it but wth, makes it easier to read.

  if(slot >= LCD_PAIRS)
  {// This should never happen, Arduino and Rapsberry should exchange number of available slots to prevent this
    return false;//This should result in an error back to the Rasp.
  }

  while(rboundary > 0)
  {
    if (*(read + ctr) != '\n')
    {//Copy the content from the receive_buffer
      available_lcd_pairs[16*slot + ctr] = *(read + ctr);
      ctr++;
    }
    else
    {//Fill up the rest with spaces to override any previously stored characters
      available_lcd_pairs[16*slot + ctr + rboundary - 1] = 0x20;
    }
    rboundary--;
  }

  available_lcd_pairs[16*slot + 15]='\0';//No matter what happens I close the string at the edge of the array

  boundary = boundary - ctr;

  read = read + ctr + 1;
  boundary = boundary - 1;
  ctr = 0;
  rboundary = 16;

  while(rboundary > 0)
  {
    if(*(read + ctr) != '\n')
    {//Copy the content from the receive_buffer
      available_lcd_pairs[16*slot + 16 + ctr] = *(read + ctr);
      ctr++;
    }
    else
    {//Fill up the rest with spaces to override any previously stored characters
      available_lcd_pairs[16*slot + 16 + ctr + rboundary - 1] = 0x20;
    }
    rboundary--;
  }

  boundary = boundary - ctr;
  if(boundary != 0)
  {// This means we have either read beyond the packet or there's left to read.
    return false;
  }

  available_lcd_pairs[16*slot + 16 + 15]; = '\0';

  //Updating the bitmap, first getting the position and then updating the bitmap
  position = position << slot;
  used_pairs = used_pairs | position;

  return true;
}

// This function updates the text on the LCD according to what the Pi sent.
// First needs to pull out the two strings one for each row :(
boolean update_screen()
{
  // Set cursor position to write
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print(available_lcd_pairs[0]);
  lcd.setCursor(0,1);
  lcd.print(available_lcd_pairs[16]);

  return true;
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
    switch(packet_operation_type | packet_operation_specific)
    {
      case PING:// PING request
        send_ping_response(packet_protocol_version, packet_id);
        break;
      case CONTROL | GET_SENSORS:
        send_available_sensors(packet_protocol_version, packet_id);
        break;
      case READ | TEMP1:
        send_sensor_read(packet_protocol_version, packet_id, TEMP1);
        break;
      case WRITE | SCREEN1:
        read_screen_data(packet_size);
//        update_screen();
        send_write_response(packet_protocol_version, packet_id);
        break;
      default:
        send_ping_response(packet_protocol_version, packet_id);
        break;
    }
  }
  else
  {//response of something we sent first. TODO
    return true;
  }
  return true;
}

// Just moving the LCD displayed data to the next available thing to display.
// A few things to keep in mind, even though there's LCD_PAIRS availabe, some
// of them may not be in use, so you have to be careful there. And you have to
// skig pair[0] after pair[1] is populated.
// This function is called roughly LCD_ROTATION_FACTOR * LOOP_DELAY ms to rotate
// the LCD display content.
void rotate_lcd_now()
{
  byte position = B00000001;
  if(used_pairs == 1)
  {//Nothing to do, we are still with default pair, this should be unlikely to extend in time.
    return;
  }

  // So now, try the moving current_pair forward and check if that pair is enabled in the bitmap.
  current_pair++;
  position<<current_pair;

  if((position & used_pairs) == 0)
  {//Example position=00000100 (for position 2), used_pairs=00000011 and current_pair=1
    current_pair=0;//Resesting it for now, but this should go to at least 1 to prevent showing the default data in pair[0]
  }

  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print(available_lcd_pairs[16*(current_pair+1)]);
  lcd.setCursor(0,1);
  lcd.print(available_lcd_pairs[16*(current_pair+1)+16]);

  return;
}

void loop(void)
{
  if(rotate_lcd == 0)
  {
    rotate_lcd_now();
    rotate_lcd = LCD_ROTATION_FACTOR * LOOP_DELAY;
  }
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
      //Serial.println("OOPs");
      pull_data();
      if(is_full_packet())
      {
        packet_ready = true;
      }
    }
    else
    {
      delay(LOOP_DELAY);
      rotate_lcd--;
    }
  }
}
