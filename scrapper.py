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
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
import time
import pyodbc
import re
from datetime import datetime
import locale
import logging
import logging.config

# GLOBALS

CRAUTOS_BASE_PATH = "https://crautos.com/index.cfm"
locale.setlocale(locale.LC_TIME, "es_CR.UTF-8")  # Costa Rica

current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"logs\\car_scraper_{current_date}.log"),
        logging.StreamHandler(),
    ],
)


logger = logging.getLogger(__name__)

existing_vehicle_urls = []
possible_brands = []


def main():
    global existing_vehicle_urls

    logger.info("Starting the scraper.")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    try:
        driver.get(CRAUTOS_BASE_PATH)
        logger.info("Navigated to base URL.")

        get_to_all_cars_list(driver)
        logger.info("Navigated to the list of all cars.")

        page_index = 0

        existing_vehicle_urls = get_existing_vehicle_urls()

        while True:
            process_current_view_cars(driver)
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, ".page-item.page-next .page-link")
                    )
                )
                driver.execute_script("arguments[0].click();", next_button)
                page_index += 1
                logger.info(f"Clicked the next page button. Going to page {page_index}")
            except TimeoutException:
                logger.info("No more pages left to process.")
                break
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        driver.quit()
        logger.info("Closed the web driver.")


def get_to_all_cars_list(driver):

    find_used_cars_section(driver)

    scroll_to_bottom(driver)

    global possible_brands
    possible_brands = extract_brands_from_driver(driver)

    press_search_button(driver)


def process_current_view_cars(driver):
    global existing_vehicle_urls

    logger.info("Processing current view of cars.")
    try:
        vehicle_cards = WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".card"))
        )
        logger.info(f"Found {len(vehicle_cards)} vehicle cards.")
    except Exception as e:
        logger.error(f"An error occurred while processing vehicle card: {e}")

    for index, card in enumerate(vehicle_cards):
        # Ignorar el último elemento
        if index == len(vehicle_cards) - 1:
            continue
        try:
            # Encontrar el enlace del vehículo
            link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
            logger.info(f"Found vehicle link: {link}")

            # Verificar si el URL ya existe en la base de datos
            if link in existing_vehicle_urls:
                logger.info(
                    f"Vehicle link {link} already exists in the database. Skipping."
                )
                continue

            # Abrir el enlace en una nueva pestaña
            driver.execute_script("window.open(arguments[0]);", link)
            logger.info("Opened vehicle link in a new tab.")

            # Cambiar al nuevo contexto de la pestaña
            driver.switch_to.window(driver.window_handles[1])
            logger.info("Switched to new tab.")

            vehicle_details = capture_vehicle_details(driver)

            vehicle_details["URL"] = link

            marca = vehicle_details.get("Marca")
            modelo = vehicle_details.get("Modelo")
            año = vehicle_details.get("Año")
            logger.info(f"Captured details for vehicle: {marca} {modelo} {año}")

            if vehicle_exists(link):
                populate_date_exited(link)
                logger.info(f"Updated exit date for existing vehicle: {link}")
            else:
                save_vehicle_details(vehicle_details)
                logger.info(f"Saved new vehicle details: {link}")

            # Cerrar la pestaña actual
            driver.close()
            logger.info("Closed current tab.")

            # Regresar a la pestaña original
            driver.switch_to.window(driver.window_handles[0])
            logger.info("Switched back to original tab.")

        except Exception as e:
            logger.error(f"An error occurred while processing vehicle card: {e}")


def vehicle_exists(url):
    try:
        with pyodbc.connect(
            driver="SQL Server",
            server="FABIAN\\SQLEXPRESS",
            database="CRAutos",
            trusted_connection="yes",
        ) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Cars WHERE URL = ?", url)
            count = cursor.fetchone()[0]
            return count > 0
    except pyodbc.Error as e:
        logger.error(f"Error connecting to the database: {e}")
        return False


def populate_date_exited(url):
    try:
        with pyodbc.connect(
            driver="SQL Server",
            server="FABIAN\\SQLEXPRESS",
            database="CRAutos",
            trusted_connection="yes",
        ) as conn:
            cursor = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "UPDATE Cars SET DateExited = ? WHERE URL = ? AND DateExited IS NULL",
                (today, url),
            )
            conn.commit()
    except pyodbc.Error as e:
        logger.error(f"Error connecting to the database: {e}")


def capture_vehicle_details(driver):
    logger.info("Capturing vehicle details.")
    vehicle_details = {}

    header_details = capture_vehicle_header_details(driver)
    fields_details = capture_vehicle_fields_details(driver)

    vehicle_details.update(header_details)
    vehicle_details.update(fields_details)

    logger.info(vehicle_details)

    return reformat_vehicle_details(vehicle_details)


def capture_vehicle_header_details(driver):
    global possible_brands
    vehicle_details = {}
    logger.info("Capturing vehicle header details.")

    # Obtener el elemento del encabezado
    header_element = driver.find_element(By.CSS_SELECTOR, ".carheader")
    header_text = header_element.find_elements(By.TAG_NAME, "h1")

    if header_text:
        # Obtener el texto del encabezado
        brand_model_year = header_text[0].text.strip()
        # Dividir el texto en palabras
        brand_model = brand_model_year.split()

        # Buscar la marca en el texto utilizando la lista de marcas posibles
        for brand in possible_brands:
            # Verificar si el texto comienza con la marca
            if brand_model_year.startswith(brand):
                vehicle_details["Marca"] = brand

                # Encontrar el año en el texto
                for word in brand_model:
                    if word.isdigit() and 1900 <= int(word) <= 2050:
                        vehicle_details["Año"] = word
                        break  # Salir del bucle una vez encontrado el año

                # Asumir que el modelo es el texto restante después de quitar marca y año
                if "Marca" in vehicle_details and "Año" in vehicle_details:
                    # Obtener el texto restante después de la marca
                    remaining_text = brand_model_year[len(brand) :].strip()

                    # Eliminar el año del texto restante
                    if vehicle_details["Año"] in remaining_text:
                        remaining_text = remaining_text.replace(
                            vehicle_details["Año"], ""
                        ).strip()

                    # Guardar el modelo
                    vehicle_details["Modelo"] = remaining_text

                break

    logger.info(f"Brand found: {vehicle_details.get('Marca')}")
    logger.info(f"Model found: {vehicle_details.get('Modelo')}")
    logger.info(f"Year found: {vehicle_details.get('Año')}")
    # Capturar precios en colones y dólares utilizando las nuevas funciones
    price_colones = extract_price_colones(header_element)
    if price_colones is not None:
        vehicle_details["PrecioColones"] = price_colones

    price_dolares = extract_price_dolares(header_element)
    if price_dolares is not None:
        vehicle_details["PrecioDolares"] = price_dolares

    return vehicle_details


def capture_vehicle_fields_details(driver):
    vehicle_details = {}

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
        "Fecha de ingreso",
        "Autonomía",
        "Batería",
    ]

    for field in fields:
        try:
            element = driver.find_element(
                By.XPATH, f"//td[contains(text(), '{field}')]/following-sibling::td"
            )
            vehicle_details[field] = element.text.strip()
        except NoSuchElementException:
            vehicle_details[field] = None

    return vehicle_details


def capture_vehicle_details_2(driver):
    # Un diccionario para almacenar los detalles del vehículo
    logger.info("Capturing vehicle details.")
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
        "Fecha de ingreso",
    ]

    try:
        for field in fields:
            element = driver.find_element(
                By.XPATH, f"//td[contains(text(), '{field}')]/following-sibling::td"
            )
            vehicle_details[field] = element.text.strip()

        header_element = driver.find_element(By.CSS_SELECTOR, ".carheader")
        header_text = header_element.find_elements(By.TAG_NAME, "h1")

        if header_text:
            brand_model_year = header_text[0].text.strip()
            brand_model = brand_model_year.split()
            if len(brand_model) >= 2:
                vehicle_details["Marca"] = brand_model[0]
                vehicle_details["Modelo"] = " ".join(brand_model[1:-1])
                vehicle_details["Año"] = brand_model[-1]

        # Capturar precios en colones y dólares utilizando las nuevas funciones
        price_colones = extract_price_colones(header_element)
        if price_colones is not None:
            vehicle_details["PrecioColones"] = price_colones

        price_dolares = extract_price_dolares(header_element)
        if price_dolares is not None:
            vehicle_details["PrecioDolares"] = price_dolares

    except NoSuchElementException:
        logger.error(f"Missing vehicle information.")
    except TimeoutException:
        logger.error(f"TimeOut Exception.")

    logger.info("Vehicle details captured.")

    return reformat_vehicle_details(vehicle_details)


def extract_brands_from_driver(driver):
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, "html.parser")

    brands = []
    select_element = soup.find("select", {"name": "brand"})
    if select_element:
        options = select_element.find_all("option")
        for option in options:
            value = option.get("value")
            if value and value != "00":  # Ignorar la opción "No Importa"
                brand = option.text.strip()
                brands.append(brand)
    return brands


def extract_price_colones(header_element):
    logger.info("Extracting price in colones from header element.")

    price_elements = header_element.find_elements(
        By.TAG_NAME, "h1"
    ) + header_element.find_elements(By.TAG_NAME, "h3")

    logger.info(
        f"Found {len(price_elements)} price elements: {[element.text for element in price_elements]}"
    )

    # Filtrar y convertir los elementos que contienen precios en colones
    colones_prices = []
    for element in price_elements:
        text = (
            element.text.strip().replace("(", "").replace(")", "").replace("*", "")
        )  # Eliminar paréntesis
        if text.startswith("¢"):
            colones_price = int(
                text.replace("¢", "").replace(",", "").strip()
            )  # Eliminar el signo de ¢ y comas
            colones_prices.append(colones_price)
            logger.info(f"Found colones price: {colones_price}")

    # Si hay precios en colones, devolver el más bajo
    if colones_prices:
        min_price = min(colones_prices)
        logger.info(f"Lowest colones price found: {min_price}")
        return min_price
    else:
        logger.warning("No colones prices found.")
        return None


def extract_price_dolares(header_element):
    logger.info("Extracting price in dollars from header element.")

    price_elements = header_element.find_elements(
        By.TAG_NAME, "h1"
    ) + header_element.find_elements(By.TAG_NAME, "h3")

    logger.info(
        f"Found {len(price_elements)} price elements: {[element.text for element in price_elements]}"
    )

    # Filtrar y convertir los elementos que contienen precios en dólares
    dolares_prices = []
    for element in price_elements:
        text = (
            element.text.strip().replace("(", "").replace(")", "").replace("*", "")
        )  # Eliminar paréntesis
        if text.startswith("$"):
            dolares_price = int(
                text.replace("$", "").replace(",", "").strip()
            )  # Eliminar el signo de $ y comas
            dolares_prices.append(dolares_price)
            logger.info(f"Found dollar price: {dolares_price}")

    # Si hay precios en dólares, devolver el más bajo
    if dolares_prices:
        min_price = min(dolares_prices)
        logger.info(f"Lowest dollar price found: {min_price}")
        return min_price
    else:
        logger.warning("No dollar prices found.")
        return None


def get_existing_vehicle_urls():
    existing_urls = []

    try:
        with pyodbc.connect(
            driver="SQL Server",
            server="FABIAN\\SQLEXPRESS",
            database="CRAutos",
            trusted_connection="yes",
        ) as conn:
            cursor = conn.cursor()

            # Ejecutar la consulta
            cursor.execute("SELECT URL FROM Cars")

            # Obtener los resultados
            rows = cursor.fetchall()
            for row in rows:
                existing_urls.append(row.URL)

            # Cerrar la conexión
            cursor.close()
            conn.close()

    except pyodbc.Error as e:
        logger.error(f"Database error: {e}")

    return existing_urls


def save_vehicle_details(vehicle_details):
    try:

        with pyodbc.connect(
            driver="SQL Server",
            server="FABIAN\\SQLEXPRESS",
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
                    Notes, DateEntered, DateExited, URL
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        logger.error(f"Error connecting to the database: {e}")


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
    logger.debug(f"Sleeping {sleep_time} seconds.")
    time.sleep(sleep_time)
    logger.debug(f"I had slept {sleep_time} seconds.")


def print_dict(dictionary):
    for key, value in dictionary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
