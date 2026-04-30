
def strip_quotes(value: str) -> str:
    value = value.strip()

    if len(value) >= 2:
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1].strip()

    return value