# Imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pyodbc
import re
from datetime import datetime
import locale

# GLOBALS

CRAUTOS_BASE_PATH = "https://crautos.com/index.cfm"
locale.setlocale(locale.LC_TIME, "es_CR.UTF-8")  # Para Costa Rica


def main():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    driver.get(CRAUTOS_BASE_PATH)

    get_to_all_cars_list(driver)

    process_current_view_cars(driver)

    driver.quit()


def get_to_all_cars_list(driver):

    find_used_cars_section(driver)

    scroll_to_bottom(driver)

    press_search_button(driver)


def process_current_view_cars(driver):

    # Obtener todos los contenedores de vehículos
    vehicle_cards = driver.find_elements(By.CSS_SELECTOR, ".card")

    for card in vehicle_cards:
        # Encontrar el enlace del vehículo
        link = card.find_element(By.TAG_NAME, "a").get_attribute("href")

        # Abrir el enlace en una nueva pestaña
        driver.execute_script("window.open(arguments[0]);", link)

        # Cambiar al nuevo contexto de la pestaña
        driver.switch_to.window(driver.window_handles[1])

        vehicle_details = capture_vehicle_details(driver)
        vehicle_details["URL"] = link

        save_vehicle_details(vehicle_details)
        marca = vehicle_details.get("Marca")
        modelo = vehicle_details.get("Modelo")
        año = vehicle_details.get("Año")
        print(f"Save {marca}-{modelo}-{año}")
        # break

        # Cerrar la pestaña actual
        driver.close()

        # Regresar a la pestaña original
        driver.switch_to.window(driver.window_handles[0])


def capture_vehicle_details(driver):
    # Un diccionario para almacenar los detalles del vehículo
    vehicle_details = {}

    # Lista de campos que queremos capturar
    fields = [
        "Cilindrada",
        "Estilo",
        "# de pasajeros",
        "Combustible",
        "Transmisión",
        "Estado",
        "Kilometraje",
        "Color exterior",
        "Color interior",
        "# de puertas",
        "Ya pagó impuestos",
        "Precio negociable",
        "Se recibe vehículo",
        "Provincia",
        "Traspaso",
        "Fecha de ingreso",
    ]

    try:
        # Capturar los campos de la tabla
        for field in fields:
            # Intentar encontrar el elemento correspondiente
            element = driver.find_element(
                By.XPATH, f"//td[contains(text(), '{field}')]/following-sibling::td"
            )
            vehicle_details[field] = element.text.strip()

        # Capturar la marca, modelo, año y precios
        header_element = driver.find_element(By.CSS_SELECTOR, ".carheader")
        header_text = header_element.find_elements(By.TAG_NAME, "h1")

        # Obtener la información de la marca, modelo y año
        if header_text:
            # El primer h1 es la marca y modelo, el segundo h1 es el precio en colones
            brand_model_year = header_text[0].text.strip()
            price_colones = header_text[1].text.strip()

            # Separar marca y modelo
            brand_model = brand_model_year.split()
            if len(brand_model) >= 2:
                vehicle_details["Marca"] = brand_model[0]  # Marca
                vehicle_details["Modelo"] = " ".join(
                    brand_model[1:-1]
                )  # Modelo (todo excepto el año)
                vehicle_details["Año"] = brand_model[-1]  # Año

            # Reformatear precio en colones
            vehicle_details["PrecioColones"] = int(
                price_colones.replace("¢", "").replace(",", "").strip()
            )

        # Capturar el precio en dólares (el tercer h3)
        price_dolares = header_element.find_element(By.XPATH, ".//h3").text.strip()
        vehicle_details["PrecioDolares"] = int(
            price_dolares.replace("($ ", "").replace(")*", "").replace(",", "").strip()
        )

    except NoSuchElementException:
        print(f"Missing vehicle information.")

    return reformat_vehicle_details(vehicle_details)


def save_vehicle_details(vehicle_details):
    try:

        with pyodbc.connect(
            driver="SQL Server",
            server="FABIAN\SQLEXPRESS",
            database="CRAutos",
            trusted_connection="yes",
        ) as conn:
            cursor = conn.cursor()

            # Insert vehicle details into the Cars table
            cursor.execute(
                """
                INSERT INTO Cars (
                    Brand, Model, Year, PriceColones, PriceDollars,
                    EngineCapacity, Style, Passengers, FuelType,
                    Transmission, Condition, Mileage,
                    ExteriorColor, InteriorColor, Doors, TaxesPaid,
                    NegotiablePrice, AcceptsVehicle, Province,
                    TransferCost, Notes, DateEntered, DateExited, URL
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    vehicle_details.get("Marca"),
                    vehicle_details.get("Modelo"),
                    vehicle_details.get("Año"),
                    vehicle_details.get("PrecioColones"),
                    vehicle_details.get("PrecioDolares"),
                    vehicle_details.get("Cilindrada"),
                    vehicle_details.get("Estilo"),
                    vehicle_details.get("# de pasajeros"),
                    vehicle_details.get("Combustible"),
                    vehicle_details.get("Transmisión"),
                    vehicle_details.get("Estado"),
                    vehicle_details.get("Kilometraje"),
                    vehicle_details.get("Color exterior"),
                    vehicle_details.get("Color interior"),
                    vehicle_details.get("# de puertas"),
                    vehicle_details.get("Ya pagó impuestos"),
                    vehicle_details.get("Precio negociable"),
                    vehicle_details.get("Se recibe vehículo"),
                    vehicle_details.get("Provincia"),
                    vehicle_details.get("Traspaso"),
                    vehicle_details.get(
                        "Notas", ""
                    ),  # Use an empty string if "Notas" not present
                    vehicle_details.get("Fecha de ingreso"),
                    vehicle_details.get("Fecha de salida"),
                    vehicle_details.get("URL"),
                ),
            )

            # Commit the transaction
            conn.commit()

    except pyodbc.Error as e:
        print(f"Error connecting to the database: {e}")


def reformat_vehicle_details(vehicle_details):
    # Reformatear Cilindrada
    if "Cilindrada" in vehicle_details:
        vehicle_details["Cilindrada"] = vehicle_details["Cilindrada"].replace(" cc", "")

    # Reformatear Traspaso
    if "Traspaso" in vehicle_details:
        traspaso_value = re.search(r"¢\s*([\d,]+)", vehicle_details["Traspaso"])
        if traspaso_value:
            vehicle_details["Traspaso"] = int(traspaso_value.group(1).replace(",", ""))

    # Reformatear Fecha de ingreso
    if "Fecha de ingreso" in vehicle_details:
        date_str = vehicle_details["Fecha de ingreso"]
        # Convertir a formato de fecha
        try:
            # Intenta convertir la fecha en el formato actual
            date_object = datetime.strptime(date_str, "%d de %B del %Y")
            # Reformatea a 'YYYY-MM-DD' que es el formato estándar para SQL
            vehicle_details["Fecha de ingreso"] = date_object.strftime("%Y-%m-%d")
        except ValueError:
            print(f"Date format error for: {date_str}")
            # Si hay un error, asigna None o un valor predeterminado
            vehicle_details["Fecha de ingreso"] = None

    # Reformatear Kilometraje

    if "Kilometraje" in vehicle_details:
        mileage_value = re.search(
            r"([\d,]+)\s*(kms|millas)", vehicle_details["Kilometraje"], re.IGNORECASE
        )

        if mileage_value:
            try:
                # Convertir a entero, manejando posibles errores
                mileage = int(mileage_value.group(1).replace(",", ""))
                if "millas" in mileage_value.group(2).lower():  # Si está en millas
                    mileage = int(mileage * 1.60934)  # Convertir millas a kilómetros
                vehicle_details["Kilometraje"] = mileage  # Guardar en kilómetros
            except ValueError:
                print(f"Invalid mileage value: {vehicle_details['Kilometraje']}")
                vehicle_details["Kilometraje"] = (
                    None  # O asignar un valor predeterminado
                )
        else:
            print(f"Kilometraje format error: {vehicle_details['Kilometraje']}")
            vehicle_details["Kilometraje"] = None  # O asignar un valor predeterminado

    return vehicle_details


def find_used_cars_section(driver):
    try:
        link = driver.find_element(By.XPATH, "//a[@href='./autosusados']/img")
        link.click()

        if "autosusados" in driver.current_url:
            print("Navigated to the used cars section successfully!")
        else:
            print("Failed to navigate to the used cars section.")
    except NoSuchElementException:
        print("Used cars section link not found.")


def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Desplazarse hacia abajo
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Esperar que se cargue el contenido nuevo
        time.sleep(1)  # Ajusta este tiempo si es necesario

        # Calcular la nueva altura y comparar con la anterior
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:  # Si no hay más contenido, salimos del bucle
            break
        last_height = new_height


def is_overlay_present(driver):
    try:
        # Ajusta el selector al del overlay en tu página
        overlay = driver.find_element(By.XPATH, "//div[@class='overlay']")
        return overlay.is_displayed()  # Devuelve True si el overlay está visible
    except NoSuchElementException:
        return False  # No hay overlay presente


def press_search_button(driver):
    try:

        # Buscar el botón utilizando el texto "Buscar"
        search_button = WebDriverWait(driver, 1000).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'BUSCAR')]")
            )
        )

        # Intenta hacer clic en el botón
        search_button.click()
        print("Search button clicked successfully!")

    except ElementClickInterceptedException:
        print("Search button was not clickable. An overlay might be present.")
    except NoSuchElementException:
        print("Search button not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def custom_sleep(sleep_time):
    print(f"Sleeping {sleep_time} seconds.")
    time.sleep(sleep_time)
    print(f"I had slept {sleep_time} seconds.")


def print_dict(dictionary):
    for key, value in dictionary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
