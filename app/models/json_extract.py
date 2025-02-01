import json

import json

def extract_version_from_file(json_path):
    """Lee un archivo JSON y extrae sus metadatos."""
    try:
        with open(json_path, 'r') as file:
            data = json.load(file)
        version = None

        # Iterar en caso de estructuras anidadas
        for key, value in data.items():
            if isinstance(value, dict):
                version = value.get('version')
        
        return {'version': version}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error leyendo el archivo JSON: {e}")
        return {}
    
def extract_license_from_file(json_path):
    """Lee un archivo JSON y extrae sus metadatos."""
    try:
        with open(json_path, 'r') as file:
            data = json.load(file)
        version = None

        # Iterar en caso de estructuras anidadas
        for key, value in data.items():
            if isinstance(value, dict):
                version = value.get('licence')
        
        return {'licence': version}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error leyendo el archivo JSON: {e}")
        return {}
    
def extract_devContact_from_file(json_path):
    """Lee un archivo JSON y extrae sus metadatos."""
    try:
        with open(json_path, 'r') as file:
            data = json.load(file)
        version = None

        # Iterar en caso de estructuras anidadas
        for key, value in data.items():
            if isinstance(value, dict):
                version = value.get('contact')
        
        return {'contact': version}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error leyendo el archivo JSON: {e}")
        return {}