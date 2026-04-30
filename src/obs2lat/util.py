
def strip_quotes(value: str) -> str:
    value = value.strip()

    if len(value) >= 2:
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1].strip()

    return value

def latex_escape(text: str) -> str:
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text