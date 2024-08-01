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

# GLOBALS

CRAUTOS_BASE_PATH = "https://crautos.com/index.cfm"


def main():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    driver.get(CRAUTOS_BASE_PATH)

    get_to_all_cars_list(driver)

    driver.quit()


def get_to_all_cars_list(driver):

    find_used_cars_section(driver)

    scroll_to_bottom(driver)

    press_search_button(driver)


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


if __name__ == "__main__":
    main()
