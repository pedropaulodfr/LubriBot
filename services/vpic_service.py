from vpic import Client

c = Client()

def get_modelos_por_marca_ano(marca, ano = None, tipo_veiculo = None):
    tipo_veiculo_api = {
        "Moto": "Motorcycle",
        "Carro": "Passenger Car",
        "Caminhão": "Truck"
    }.get(tipo_veiculo, None)

    # Montar parâmetros dinamicamente
    args = {"make": marca}

    if ano is not None:
        args["model_year"] = ano

    if tipo_veiculo is not None:
        args["vehicle_type"] = tipo_veiculo_api
    
    result = c.get_models_for_make(**args)
    
    modelos = []

    for modelo in result:
        modelos.append(modelo['Model'])
    
    # Modelos ordenados
    modelos_ordenados = sorted(modelos)
    
    return modelos_ordenados


def get_tipos_veiculos_por_id_marca(id_marca):
    result = c.get_vehicle_types_for_make(id_marca)

    print(result)
    