import pygame as pg
import pygame_menu
import random
from collections import deque
import threading
import queue
import re
import time
import sounddevice as sd
import numpy as np
from datetime import datetime
import pyttsx3
from faster_whisper import WhisperModel
from constants import *
from runway import Runway
from aircraft import Aircraft
from point import Point
from transcribe import preprocess_atc_command
from pygame_menu.widgets.widget.frame import _FrameSizeException
from PIL import Image
import math

def get_angle(sprite_pos, target_pos):
    dx = target_pos[0] - sprite_pos[0]
    dy = target_pos[1] - sprite_pos[1]
    
    # Używamy atan2, ale zamieniamy dx i dy miejscami, 
    # aby zorientować kąt na oś Y (Północ)
    rads = math.atan2(dx, -dy) 
    
    # Konwersja na stopnie
    angle = math.degrees(rads)
    
    # Normalizacja do zakresu 0-360 (opcjonalnie)
    if angle < 0:
        angle += 360
        
    return angle


class Game:
    def __init__(self):
        print("Loading the model...")
        self.model = WhisperModel(
            MODEL_PATH,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            cpu_threads=10,
            num_workers=2)

        pg.init()
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("ATC Game")
        self.clock = pg.time.Clock()
        self.menu = pygame_menu.Menu(
            title="Flights",
            width=RIGHT_BAR_WIDTH,
            height=SCREEN_HEIGHT,
            position=(SCREEN_WIDTH - RIGHT_BAR_WIDTH, 0, False),
            center_content=False,
            theme=pygame_menu.themes.THEME_DARK,
        )

        self.aircrafts = pg.sprite.Group()
        self.trails = deque([], N_TRAILS)
        self.points = pg.sprite.Group(
            [Point(p, POINTS[p]["lat"], POINTS[p]["lon"]) for p in POINTS.keys()]
        )

        self.menu_widgets = {}

        # --- audio / ATC ---
        self.recording = False
        self.audio_buffer = []
        self.lock = threading.Lock()

        self.audio_queue = queue.Queue()
        self.reply_queue = queue.Queue()

        self.atc_comms = None
        self.new_message = False
        self.audio_data = []

        self.font = pg.font.SysFont("arial", 15, bold=True)
        self.small_font = pg.font.SysFont("arial", 12, bold=True)
        self.runway = Runway(258)

    def audio_callback(self, indata, frames, time_, status):
        if self.recording:
            with self.lock:
                self.audio_buffer.append(indata.copy())

    def audio_worker(self, model):
        while True:
            audio = np.squeeze(self.audio_queue.get())
            if audio is None:
                break

            start_time = datetime.now()
            segments, _ = model.transcribe(
                audio,
                language="en",
                beam_size=1,
                vad_filter=True
            )
            transcribe_time = (datetime.now() - start_time).total_seconds()

            for segment in segments:
                text = segment.text.strip()
                if not text:
                    continue

                atc_command, ac_id, response = preprocess_atc_command(text)
                self.generate_response(atc_command, ac_id)

                self.atc_comms = {
                    "atc_command": atc_command,
                    "ac_id": ac_id,
                    "timestamp": datetime.now(),
                    "response": response
                }
                self.new_message = True
                self.reply_queue.put(response)

            self.audio_data.append({
                "command": atc_command,
                "response": response,
                "audio_length": len(audio) / SAMPLE_RATE,
                "transcribe_time": transcribe_time
            })

            self.audio_queue.task_done()


    # convert this text to speech
    def reply_worker(self):
        engine = pyttsx3.init()
        engine.setProperty("voice", engine.getProperty("voices")[2].id)
        engine.startLoop(False)  

        while True:
            try:
                text = self.reply_queue.get()  
                engine.say(text)
                engine.iterate()     
                time.sleep(0.01)
                self.reply_queue.task_done()
            except Exception as e:
                print("TTS error:", e)

    def generate_response(self, atc_command, ac_id):
        target_alt = target_hdg = target_spd = None

        hdg = re.search(r"heading\s+(\d+)", atc_command)
        if hdg:
            target_hdg = int(hdg.group(1)) % 360

        direct = "direct" in atc_command
        if direct:
            for key, value in DICTIONARY.items():
                atc_command = atc_command.replace(key, value)

            waypoint = re.search(r"direct( to)? ([A-Z\s]+\d*)", atc_command)
            if waypoint:
                waypoint = waypoint.group(2).replace(" ", "")

        alt = re.search(r"(climb|descend|flight level)\s+(\d+)", atc_command)
        if alt:
            target_alt = int(alt.group(2))
            if target_alt < 1000:
                target_alt *= 100

        spd = re.search(r"speed\s+(\d+)", atc_command)
        if spd:
            target_spd = int(spd.group(1))

        for ac in self.aircrafts:
            if ac.atc_id == ac_id:
                if target_alt:
                    ac.target_alt = max(1000, min(40000, target_alt))
                if target_hdg is not None:
                    ac.target_heading = target_hdg
                    ac.target_point = None
                
                if direct and waypoint:
                    for point in self.points:
                        if point.name == waypoint:
                            ac.target_point = point

                if target_spd:
                    ac.target_speed = max(150, min(350, target_spd))
                break

    def update_aircrafts(self, font):
        self.aircrafts.update(self.screen, font, self.runway)
        self.aircrafts.draw(self.screen)

    def add_aircraft_to_menu(self, flight):
        
        # main frame corresponding to one flight
        main_frame = self.menu.add.frame_v(width = RIGHT_BAR_WIDTH-2*RIGHT_BAR_MARGIN,
                        height = 90, 
                        background_color = LIGHTGRAY, 
                        margin = (0, RIGHT_BAR_MARGIN),
                        align = pygame_menu.locals.ALIGN_CENTER)
        
        surface = pg.Surface(main_frame.get_inner_size())
        surface.fill((255,0,0))
        
        # header frame 
        header= self.menu.add.frame_h(width = RIGHT_BAR_WIDTH-4*RIGHT_BAR_MARGIN,
                        height = 50, 
                        background_color = LIGHTGRAY, 
                        padding = 0)
        
        img_path = f"./airline_logos/{re.search('^[A-Z]+', flight.flight_id).group().lower()}.png"
        imgy = Image.open(img_path).size[1]
        
        scale_coef = 50/(1.15*imgy)

        header.pack(self.menu.add.image(
            image_path=img_path,
            scale = (scale_coef, scale_coef)))
        try:
            header.pack(self.menu.add.label(
                f"{flight.airline}, {flight.flight_id}, {flight.aircraft_type}", 
                align=pygame_menu.locals.ALIGN_LEFT, font_size=SIDE_BAR_BIG_FONT_SIZE, font_color = BLACK))
        
        except _FrameSizeException:
            header.pack(self.menu.add.label(
                f"{flight.airline}, {flight.flight_id}, {flight.aircraft_type}", 
                align=pygame_menu.locals.ALIGN_LEFT, font_size=SIDE_BAR_BIG_FONT_SIZE-1, font_color = BLACK))

        main_frame.pack(header)
        
        # horizontal line
        horizontal_line = self.menu.add.frame_h(width = RIGHT_BAR_WIDTH-4*RIGHT_BAR_MARGIN,
                        height = 3, 
                        background_color = GRAY, 
                        padding = 0)
        
        main_frame.pack(horizontal_line)

        detailed_info = self.menu.add.label(
            "",
            align=pygame_menu.locals.ALIGN_LEFT, 
            font_size=SIDE_BAR_FONT_SIZE,
            font_color = BLACK)

        main_frame.pack(detailed_info)

        self.menu_widgets[flight.flight_id] = {
        "flight_info": detailed_info,
        "flight": flight
        }
    
    def update_menu_text(self, flight_id=None):
        
        # updates info about one particular flight once it has moved or changed its status
        if flight_id is not None:
            f = self.menu_widgets[flight_id]
            self.menu_widgets[flight_id]["flight_info"].set_title(
                f"HDG: {round(f.current_heading)}  "
                f"ALT: {round(f.current_alt)}  "
                f"SPD: {round(f.current_speed)}")
        
        # updates info about all flights  
        else:
            for data in self.menu_widgets.values():
                f = data["flight"]
                data["flight_info"].set_title(
                    f"HDG: {round(f.current_heading)}  "
                    f"ALT: {round(f.current_alt)}  "
                    f"SPD: {round(f.current_speed)}")

    def draw_aircraft_trails(self, j):
        # drawing aircraft trail
        if len(self.trails)!=0:
            for surface in self.trails:
                self.screen.blit(source=surface, dest = (0,0))
    
        # every FPS frames we append the current position to the list so that it becomes a trail in future frames
        if j%(TRAIL_SECONDS*FPS) == 0:
            alpha_surf = pg.Surface(self.screen.get_size(), pg.SRCALPHA)
            alpha_surf.fill((255, 255, 255, 220), special_flags=pg.BLEND_RGBA_MULT)
            for ac in self.aircrafts:
                ac.draw_trail(surface=alpha_surf)
            
            self.trails.append(alpha_surf)

    def generate_random_flight(self):

        flight = random.choice(AIRLINES)
        while True:
            # generating a unique flight number
            flight_number = random.randint(1, 500)
            flight_id = f"{flight['airline_icao']}{flight_number}"
            if flight_id not in [f.flight_number for f in self.aircrafts.sprites()]:
                break
        
        # generating the initial aircraft location and initial heading
        location_id = random.randint(1,4)
        if location_id == 1:
            # upper border
            pos = (random.randint(5, SCREEN_WIDTH - RIGHT_BAR_WIDTH-5), 0)
            heading = 180
        elif location_id ==2:
            # right border
            pos = (SCREEN_WIDTH - RIGHT_BAR_WIDTH-5, random.randint(5, SCREEN_HEIGHT-5))
            heading = 270
        elif location_id ==3:
            # lower border
            pos = (random.randint(5, SCREEN_WIDTH- RIGHT_BAR_WIDTH-5), SCREEN_HEIGHT)
            heading = 360
        else:
            # left border
            pos = (0, random.randint(5, SCREEN_HEIGHT-5))
            heading = 90

        new_aircraft = Aircraft(aircraft_type=random.choice(flight["aircraft_types"]),
                 airline=flight["airline_name"],
                 callsign=flight["callsign"],
                 flight_id=flight_id,
                 flight_number = flight_number,
                 pos = pos,
                 heading=heading,
                 groups=(self.aircrafts,))
        
        self.add_aircraft_to_menu(new_aircraft)

    def _add_test_aircraft(self):
        new_aircraft = Aircraft(aircraft_type = "B737-8",
            airline= "LOT",
            callsign="lot",
            flight_id= "LOT123",
            flight_number = 123,
            pos = (SCREEN_WIDTH - RIGHT_BAR_WIDTH, SCREEN_HEIGHT//2),
            heading= 252,
            groups=(self.aircrafts,))
        self.add_aircraft_to_menu(new_aircraft)


    def run(self):

        threading.Thread(target=self.audio_worker, args=(self.model,), daemon=True).start()
        threading.Thread(target=self.reply_worker, daemon=True).start()

        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            callback=self.audio_callback
        )
        stream.start()

        self.generate_random_flight()
        running = True
        j = 0

        while running:
            self.screen.fill(BLACK)
            self._draw_ui()
            self.runway.draw(self.screen, self.font)

            j += 1
            self.clock.tick(FPS)

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False

                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_SPACE:
                        self.recording = True
                    elif event.key == pg.K_p:
                        self._pause()

                elif event.type == pg.KEYUP and event.key == pg.K_SPACE:
                    self.recording = False
                    self._flush_audio()

            self.update_aircrafts(self.small_font)
            self.draw_aircraft_trails(j)

            if j % (250 * FPS) == 0:
                self.generate_random_flight()

            if j % FPS == 0:
                self.update_menu_text()

            pg.display.flip()

        stream.stop()
        stream.close()
        pg.quit()

    def _flush_audio(self):
        with self.lock:
            if self.audio_buffer:
                audio = np.concatenate(self.audio_buffer, axis=0)
                self.audio_buffer.clear()
                if len(audio) > SAMPLE_RATE // 5:
                    self.audio_queue.put(audio)

    def _draw_ui(self):
        self.menu.update(pg.event.get())
        self.menu.draw(self.screen)

        label = self.font.render(
            "TALKING..." if self.recording else "Hold SPACE to talk",
            True,
            LIMEGREEN if self.recording else WHITE
        )
        self.screen.blit(label, (50, 80))

        for point in self.points:
            point.draw(self.screen)

    def _shutdown(self):
        self.stream.stop()
        self.stream.close()
        pg.quit()

if __name__ == "__main__":
    game = Game()
    game.run()