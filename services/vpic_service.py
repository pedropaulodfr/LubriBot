from vpic import Client

c = Client()

def get_modelos_por_marca_ano(marca, ano = None):
    if(ano):
        result = c.get_models_for_make(marca, model_year=ano)
    else:
        result = c.get_models_for_make(marca)
    
    modelos = []

    for modelo in result:
        modelos.append(modelo['Model'])
    
    return sorted(modelos)
