import re

def extract_session_id(session_str: str):
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)

    if match:
        extracted_string = match.group(1)
        return extracted_string

    return ""

def get_str_from_forge_dict(forge_dict: dict):
    return ", ".join([f"{int(value)} {key}" for key, value in forge_dict.items()])