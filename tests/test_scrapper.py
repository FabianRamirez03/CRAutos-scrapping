import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapper import (
    extract_price_colones,
    extract_price_dolares,
    capture_vehicle_details,
)


# Configuración del driver
@pytest.fixture(scope="module")
def driver():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    yield driver
    driver.quit()


# Ruta a los archivos HTML de prueba
HTML_DIR = os.path.join(os.path.dirname(__file__), "mock_html")


# Función para cargar un archivo HTML local en el driver
def load_local_html(driver, file_name):
    file_path = f"file:///{os.path.abspath(os.path.join(HTML_DIR, file_name))}"
    driver.get(file_path)


def test_capture_vehicle_details_colones_listing(driver):
    load_local_html(driver, "Colones/Colones_Example.html")
    vehicle_details = capture_vehicle_details(driver)
    assert vehicle_details["Marca"] == "Volvo"
    assert vehicle_details["Modelo"] == "S60"
    assert vehicle_details["Año"] == "2012"
    assert vehicle_details["PrecioColones"] == 7500000
    assert vehicle_details["PrecioDolares"] == 14395
    assert vehicle_details["Cilindrada"] == "2000"
    assert vehicle_details["Estilo"] == "Sedán"
    assert vehicle_details["# de pasajeros"] == "5"
    assert vehicle_details["Combustible"] == "Gasolina"
    assert vehicle_details["Transmisión"] == "Automática/Dual"
    assert vehicle_details["Estado"] == "Excelente"
    assert vehicle_details["Kilometraje"] == 98000
    assert vehicle_details["Color exterior"] == "BEIGE"
    assert vehicle_details["# de puertas"] == "4"
    assert vehicle_details["Ya pagó impuestos"] == "SI"
    assert vehicle_details["Precio negociable"] == "SI"
    assert vehicle_details["Se recibe vehículo"] == "NO"
    assert vehicle_details["Provincia"] == "San José"
    assert vehicle_details["Fecha de ingreso"] == "2024-07-03"


def test_capture_vehicle_details_dolares_listing(driver):
    load_local_html(driver, "Dollars/Dollars_example.html")
    vehicle_details = capture_vehicle_details(driver)
    assert vehicle_details["Marca"] == "Mercedes"
    assert vehicle_details["Modelo"] == "Benz B200"
    assert vehicle_details["Año"] == "2013"
    assert vehicle_details["PrecioColones"] == 8075500
    assert vehicle_details["PrecioDolares"] == 15500
    assert vehicle_details["Cilindrada"] == "1600"
    assert vehicle_details["Estilo"] == "Hatchback"
    assert vehicle_details["# de pasajeros"] == "5"
    assert vehicle_details["Combustible"] == "Eléctrico"
    assert vehicle_details["Transmisión"] == "Automática/Dual"
    assert vehicle_details["Estado"] == "Excelente"
    assert vehicle_details["Kilometraje"] == 93000
    assert vehicle_details["Color exterior"] == "BLANCO"
    assert vehicle_details["# de puertas"] == "4"
    assert vehicle_details["Ya pagó impuestos"] == "SI"
    assert vehicle_details["Precio negociable"] == "SI"
    assert vehicle_details["Se recibe vehículo"] == "SI"
    assert vehicle_details["Provincia"] == "San José"
    assert vehicle_details["Fecha de ingreso"] == "2024-08-01"
