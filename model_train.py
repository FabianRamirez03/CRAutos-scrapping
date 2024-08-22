import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler


def connect_to_database():
    """Conectar a la base de datos SQL Server y devolver la conexión."""
    engine = create_engine(
        "mssql+pyodbc://FABIAN\\SQLEXPRESS/CRAutos?driver=SQL+Server"
    )
    return engine


def fetch_data(engine):
    """Ejecutar la consulta SQL y devolver un DataFrame con los datos."""
    query = """
    SELECT 
        Brand, 
        Model, 
        Year, 
        PriceColones, 
        EngineCapacity, 
        Mileage, 
        Transmission
    FROM Cars
    WHERE FuelType = 'Gasolina' AND EngineCapacity IS NOT NULL  -- Asegúrate de que el precio no sea nulo
    """
    df = pd.read_sql(query, engine)

    # Imprimir el total de filas
    print(f"Total rows in datafram: {df.shape[0]}")  # O usando df.count()

    return df


def preprocess_data(df):
    """Preprocesar los datos: manejar valores nulos y codificar categóricas."""
    df.dropna(inplace=True)  # Eliminar filas con valores nulos

    # Codificar variables categóricas usando pd.get_dummies
    df = pd.get_dummies(df, columns=["Brand", "Model", "Transmission"], drop_first=True)

    return df


def split_data(df):
    """Dividir los datos en características (X) y etiqueta (y)."""
    X = df.drop("PriceColones", axis=1)  # Características
    y = df["PriceColones"]  # Etiqueta
    return X, y


def plot_results(y_test, y_pred):
    plt.scatter(y_test, y_pred)
    plt.xlabel("Precios Reales")
    plt.ylabel("Precios Predichos")
    plt.title("Comparación de Precios Reales vs Predichos")
    plt.plot(
        [min(y_test), max(y_test)],
        [min(y_test), max(y_test)],
        color="red",
        linestyle="--",
    )
    plt.show()


def predict_price(model, scaler, X):
    """Función para predecir el precio de un vehículo basado en las características ingresadas por el usuario."""

    print("Introduce las características del vehículo:")

    # Solicitar las características
    brand = input("Marca: ")
    model_input = input("Modelo: ")
    year = int(input("Año: "))
    engine_capacity = float(input("Capacidad del motor: "))
    mileage = int(input("Kilometraje: "))
    transmission = input("Transmisión (Manual/Automática): ")

    # Crear un DataFrame con las características
    input_data = pd.DataFrame(
        {
            "Brand": [brand],
            "Model": [model_input],
            "Year": [year],
            "EngineCapacity": [engine_capacity],
            "Mileage": [mileage],
            "Transmission": [transmission],
        }
    )

    # Preprocesar los datos
    input_data = pd.get_dummies(
        input_data, columns=["Brand", "Model", "Transmission"], drop_first=True
    )

    # Asegurarte de que el DataFrame tenga las mismas columnas que el conjunto de entrenamiento
    missing_cols = set(X.columns) - set(input_data.columns)

    # Crear un DataFrame con columnas faltantes
    for col in missing_cols:
        input_data[col] = 0  # Agregar columnas faltantes con valor 0

    # Reordenar columnas para que coincidan con X
    input_data = input_data.reindex(columns=X.columns, fill_value=0)

    # Estandarizar los datos de entrada
    input_data[["Mileage", "EngineCapacity"]] = scaler.transform(
        input_data[["Mileage", "EngineCapacity"]]
    )

    # Realizar la predicción
    predicted_price = model.predict(input_data)

    print(
        f"El precio estimado del vehículo es: {np.exp(predicted_price[0]):,.2f} colones"
    )


def main():
    """Función principal para ejecutar el flujo del programa."""
    # Conectar a la base de datos
    engine = connect_to_database()

    # Obtener los datos
    df = fetch_data(engine)

    # Preprocesar los datos
    df = preprocess_data(df)

    # Dividir los datos en características y etiqueta
    X, y = split_data(df)

    y = np.log(y)

    # Dividir en conjunto de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Entrenar el modelo
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Hacer predicciones
    y_pred = model.predict(X_test)

    # Evaluar el modelo
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"Error cuadrático medio: {mse}")
    print(f"Coeficiente de determinación R²: {r2}")

    # Cerrar el motor de conexión
    engine.dispose()

    # Aquí deberías tener tu escalador ajustado
    scaler = StandardScaler()
    scaler.fit(X[["Mileage", "EngineCapacity"]])

    # Llamar a la función para predecir el precio
    predict_price(model, scaler, X)


if __name__ == "__main__":
    main()
