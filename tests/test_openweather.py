import unittest
import configparser

CONFIGURATION_FILE = "general.conf"

class TestOpenweather(unittest.Testcase):
    def setUp(self):
        configuration = configparser.ConfigParser()
        configuration.read(CONFIGURATION_FILE)
        self.openweather = openweather.Openweather(
            configuration['COLLECTOR']['openweathermap-key'],
            configuration['COLLECTOR']['openweathermap-name'],
            configuration['COLLECTOR']['openweathermap-city-id'])

    def test_get_temperature(self):
        t = self.openweather.get_temperature()
        self.assertIsInstance(t, float)
        self.assertNotEquals(t, 100) #Default temperature value in openweather.py

    def test_get_weather(self):
        w = self.openweather.get_weather()
        self.assertIsInstance(w, string)
        self.assertIsInstance(w, "None")

if __name__ == '__main__':
    unittest.main()
