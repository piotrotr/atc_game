SCREEN_HEIGHT = 750
SCREEN_WIDTH = 1500
PIXELS_PER_NM = 20 #0.005 
GRAY = (90, 90, 90)
LIGHTGRAY = (150, 150, 150)
WHITE = (255,255,255)
RIGHT_BAR_WIDTH = 500
RIGHT_BAR_MARGIN = 15
LIMEGREEN = (115,230,0)
DARKGREEN = (0, 128, 0)
BLACK = (0,0,0)
FPS = 100
N_TRAILS = 4
SIDE_BAR_FONT_SIZE=14
SIDE_BAR_BIG_FONT_SIZE = 18
TRAIL_SECONDS = 15


METERS_PER_NM = 1852
REF_LAT = 50.0777      # EPKK
REF_LON = 19.7848

#### constants relating to ATC speech transcription
MODEL_PATH = "models/whisper-medium.en-fine-tuned-for-ATC-faster-whisper"
SAMPLE_RATE = 16000
CHUNK_SECONDS = 10
DEVICE = "cpu"# "cpu"       # change to "cuda" if you have GPU
COMPUTE_TYPE = "int8"  # fastest on CPU
NUMBER_DICT = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "zero": "0"} 
CHANNELS = 1

#### airline data
AIRLINES = [
    {
        "airline_name": "LOT",
        "airline_icao": "LOT",
        "callsign": "lot",
        "aircraft_types": ["B737-800", "B737 MAX", "B787 Dreamliner", "E175", "E190", "E195"]
    },
    {
        "airline_name": "Air France",
        "airline_icao": "AFR",
        "callsign": "airfrance",
        "aircraft_types": ["A320", "A319", "A321", "A320neo"]
    },
    {
        "airline_name": "Wizz Air",
        "airline_icao": "WZZ",
        "callsign": "wizz",
        "aircraft_types": ["A320", "A321", "A321neo", "A320neo", "A321 XLR"]
    },
    {
        "airline_name": "Ryanair",
        "airline_icao": "RYR",
        "callsign": "ryanair",
        "aircraft_types": ["B737-800", "B737 MAX"]
    },
    {
        "airline_name": "SAS",
        "airline_icao": "SAS",
        "callsign": "scandinavian",
        "aircraft_types": ["B737-800", "B737-700"]
    },
    {
        "airline_name": "Lufthansa",
        "airline_icao": "DLH",
        "callsign": "lufthansa",
        "aircraft_types": ["A320", "A320neo", "A321"]
    },
    {
        "airline_name": "Austrian",
        "airline_icao": "AUA",
        "callsign": "austrian",
        "aircraft_types": ["A320", "E175"]
    },
    {
        "airline_name" : "Turkish Airlines",
        "airline_icao": "THY",
        "callsign": "turkish",
        "aircraft_types": ["B737-800"]
    },
    {
        "airline_name" : "Germanwings",
        "airline_icao": "GWI",
        "callsign": "germanwings",
        "aircraft_types": ["A320"]
    },
    {
        "airline_name": "easyJet",
        "airline_icao": "EZY",
        "callsign": "easy", 
        "aircraft_types": ["A320", "A320neo", "A321", "A321neo", "A319"]
    }
]

POINTS = {
    "AKFAG": {
        "lat": (50, 2, 6.7),
        "lon": (19, 22, 41)
    },
    "BAWZI": {
        "lat": (50, 8, 13.7), 
        "lon": (20, 13, 4.5)
    },

    "OFFUK": {
        "lat": (50, 7, 11.8),
        "lon": (20, 5, 28.3)
    },

    "KK362": {
        "lat": (50, 6, 13.2),
        "lon": (19, 58, 19.8)
    },

    "KK383":{
        "lat": (50, 2, 1.2),
        "lon": (19, 28, 18.1)
    }
}

DICTIONARY = {
  "alfa": "A",
  "bravo": "B",
  "charlie": "C",
  "delta": "D",
  "echo": "E",
  "foxtrot": "F",
  "golf": "G",
  "hotel": "H",
  "india": "I",
  "juliett": "J",
  "kilo": "K",
  "lima": "L",
  "mike": "M",
  "november": "N",
  "oscar": "O",
  "papa": "P",
  "quebec": "Q",
  "romeo": "R",
  "sierra": "S",
  "tango": "T",
  "uniform": "U",
  "victor": "V",
  "whiskey": "W",
  "x-ray": "X",
  "yankee": "Y",
  "zulu": "Z"
}



    # {
    #     "airline_name": "Flydubai",
    #     "airline_icao": "FDB",
    #     "callsign": "flydubai",
    #     "aircraft_types": ["B737 MAX"]
    # },

    # {
    #     "airline_name" : "Pegasus",
    #     "airline_icao": "PGT",
    #     "callsign": "sunturk",
    #     "aircraft_types": ["A320", "A321", "B737-800", "B737 MAX"]
    # },