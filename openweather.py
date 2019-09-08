import logging
import requests
import time
import json

retention_threshold = 60 #Number of seconds to wait before actually sending a new API request.

class Openweather():

    def __init__(self, key, name, city_id):
        """
        Initilizes OpenWeather object, with the given parameters and queries the
        API for current data.
        """
        self.key = key
        self.name = name
        self.city_id = city_id
        self.temperature = 100
        self.weather = "None"
        if (self._get_weather()):
            self.last_measure = time.time()
        else:
            raise Exception("Couldn't get the first measure from OpenWeather for some reason... aborting")

    def get_temperature(self):
        """
        Returns temperature either from the cached value or by refreshing calling _get_weather()
        """
        if (time.time() - self.last_measure) > retention_threshold:
            logging.debug("Retrieving new data")
            try:
                _get_weather(self)
            except Exceprion as e:
                logging.warn("Couldn't update temperature and weather from OpenWeather. Maybe next time? Reason: " + str(e))
        else:
            logging.debug("Returning cached temperature")
        return self.temperature

    def get_weather(self):
        """
        Returns weather either from the cached value or by refreshing calling _get_weather()
        """
        if (time.time() - self.last_measure) > retention_threshold:
            logging.debug("Retrieving new data")
            try:
                _get_weather(self)
            except Exception as e:
                logging.warn("Couldn't update temperature and weather from OpenWeather. Maybe next time? Reason: " + str(e))
        else:
            logging.debug("Returning cached weather")
        return self.weather

    def _get_weather(self):
        """
        This function uses https://openweathermap.org/current API to get weather
        data for the given city_id. Example
        curl "https://api.openweathermap.org/data/2.5/weather?id=2964574&units=metric&appid=LALALA"
            {"coord":{"lon":-6.27,"lat":53.34},
            "weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03n"}],"base":"stations",
            "main":{"temp":5.5,"pressure":1014,"humidity":81,"temp_min":5,"temp_max":6},
            "visibility":10000,"wind":{"speed":3.1,"deg":220},"clouds":{"all":40},"dt":1549407600,
            ...}
        """
        parameters = {"id":self.city_id, "units":"metric", "appid":self.key}
        url = "https://api.openweathermap.org/data/2.5/weather"
        response = requests.get(url, params = parameters)
        logging.debug("Call to OpenWeatherMap returned " + str(response.status_code))

        if response.status_code == requests.codes.ok:
            json_data = response.json()
            logging.debug(json_data["main"])
            self.temperature = float(json_data["main"]["temp"])
            self.weather = json_data["weather"][0]["description"]
            self.last_measure = time.time()
            return True
        return False
