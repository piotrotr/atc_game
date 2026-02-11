import numpy as np, re

# ===== CONFIG =====
MODEL_PATH = "models/whisper-medium.en-fine-tuned-for-ATC-faster-whisper"
SAMPLE_RATE = 16000
CHUNK_SECONDS = 10
DEVICE = "cpu"       # change to "cuda" if you have GPU
COMPUTE_TYPE = "int8"  # fastest on CPU

number_dict = {"one": "1", "two": "2", 
               "three": "3", "four": "4", 
               "five": "5", "six": "6", 
               "seven": "7", "eight": "8", 
               "nine": "9", "zero": "0"} 
# ==================

def preprocess_atc_command(text: str):
    for old, new in number_dict.items():
        # replacing numbers (text) with digits
        text = text.replace(old, new)

    text = text.replace("load", "lot")
    text = re.sub(r"whizz|ways", "wizz", text)

    text = text.replace("thousand", "000")
    if "correction" in text:
        text = re.sub(r"(\d+\s)+correction", "", text)
    
    atc_id = re.match("^[a-z ]+[0-9 ]+", text)
    response = text
    
    text = re.sub(r"(?<=\d)\s(?=\d)", "", text)

    if atc_id:
        atc_id = atc_id.group()
    else: return text, None, None

    response = f'{text.replace(atc_id, "")}, {atc_id}' 

    atc_id = atc_id.replace(" ", "")
    print(text)

    return text, atc_id, response



  

