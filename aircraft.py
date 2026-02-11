import pygame as pg
import random
import math
from constants import *
import numpy as np
from point import Point
from runway import Runway

def normalize_angle(angle):
    """Normalize angle to range -180 .. +180"""
    return (angle + 180) % 360 - 180

def turn_rate_deg_per_sec(bank_deg, speed_kt):
    '''Calculates the turn rate based on aircraft's speed and the desired bank angle'''
    g = 9.81
    speed_mps = speed_kt * 0.514444
    bank_rad = math.radians(bank_deg)

    turn_rate_rad = (g * math.tan(bank_rad)) / speed_mps
    return math.degrees(turn_rate_rad)

class Aircraft(pg.sprite.Sprite):
    def __init__(self, 
                 airline, 
                 callsign,
                 aircraft_type, 
                 flight_id, 
                 flight_number,
                 pos=None,
                 alt = None, 
                 heading = None, 
                 speed=None,
                 groups = ()): # needed to add the Aircraft (Sprite object) to the collection of all aircrafts)
        super().__init__(*groups)

        # initializing aircraft position
        if pos:
            self.x, self.y = pos
        else:
            # spawn aircraft at the upper or lower screen boundary
            if random.random() < 0.5:
                self.x, self.y = (random.randrange(SCREEN_WIDTH), random.choice([2, SCREEN_HEIGHT]))
            
            # sprawn aircraft at the left or right screen boundary
            else:
                self.x, self.y = (random.randrange(SCREEN_HEIGHT), random.choice([2, SCREEN_WIDTH]))

        # initializing aircraft altitude
        if alt:
            self.current_alt = alt
            self.target_alt = alt
        else:
            self.current_alt = random.randint(4, 10) * 1000
            self.target_alt = self.current_alt
        
        # initializing aircraft heading
        if heading:
            if heading ==0:
                heading = 360
            
            self.current_heading = heading
            self.target_heading = heading
        else:
            self.current_heading = random.randint(1,360)
            self.target_heading = self.current_heading
        
        # initializing aircraft speed
        if speed:
            self.current_speed = speed
            self.target_speed = speed
        else: 
            self.current_speed = random.randrange(250, 310, 10)
            self.target_speed = self.current_speed

        self.target_point = None
        self.vertical_speed = 0
        self.airline = airline
        self.aircraft_type = aircraft_type
        self.callsign = callsign
        self.flight_id = flight_id
        self.flight_number = str(flight_number)
        self.atc_id = self.callsign.lower() + self.flight_number
        self.status = "flight"
        
        # drawing aircraft image
        self.image = pg.Surface((7, 7), pg.SRCALPHA)  # transparent surface
        self.image.fill((0, 0, 0, 0))  # fully transparent
        
        pg.draw.rect(self.image, (0, 0, 0), self.image.get_rect())
        pg.draw.rect(self.image, LIMEGREEN, self.image.get_rect(), width=1)

        self.rect = self.image.get_rect(center=(self.x, self.y))
    
    def current_position(self): return (self.x, self.y)

    def capture_loc(self, runway: Runway):
        """
        Checks and captures ILS Localizer.
        """
        # --- RWY data ---
        rwy = runway.rwy_data["25"]
        threshold_pos = pg.math.Vector2(rwy["pos"])
        rwy_hdg = rwy["hdg"]

        # --- Aircraft position ---
        ac_pos = pg.math.Vector2(self.current_position())

        # --- Distance to threshold (NM) ---
        distance = ac_pos.distance_to(threshold_pos) / PIXELS_PER_NM

        # --- Runway direction vector (pygame Y inverted) ---
        rwy_hdg_rad = math.radians(rwy_hdg)
        rwy_dir = pg.math.Vector2(
            math.sin(rwy_hdg_rad),
            -math.cos(rwy_hdg_rad)
        )

        # --- Vector from threshold to aircraft ---
        ac_vec = ac_pos - threshold_pos

        # --- Lateral deviation from LOC (cross-track error) ---
        lateral_offset = ac_vec.cross(rwy_dir) / PIXELS_PER_NM

        # --- Heading deviation ---
        hdg_deviation = ((self.current_heading - rwy_hdg + 180) % 360) - 180

        # --- LOC capture conditions ---
        if (
            distance < 25 and                 # within LOC range
            abs(lateral_offset) < 2.5 and     # LOC sensitivity
            abs(hdg_deviation) < 45       # intercept angle
        ):
            self.status = "LOC captured"
            self.landing_rwy = runway
    
    def approach(self):
        rwy_hdg = self.landing_rwy.runway_heading
        rwy = self.landing_rwy
        for approach_point in self.landing_rwy.rwy_data["25"]["approach_points"]:
                if (approach_point.position[0] < self.x and rwy_hdg > 180) or (approach_point.position[0] > self.x and rwy_hdg < 180):
                    self.target_point = approach_point
                    if self.target_point.name == "KK362":
                        self.status = "final approach"
                        return
                        
                        desc_angle = math.tan(math.radians(3))
                        rate_of_descent = desc_angle * self.current_speed * 101.268
                        # self.vertical_speed = rate_of_descent
                        distance_to_rwy = pg.math.Vector2(rwy["pos"]).distance_to(pg.math.Vector2(self.current_position())) / PIXELS_PER_NM
                        desired_alt = desc_angle * distance_to_rwy * METERS_PER_NM
                        if abs(self.current_alt - desired_alt) > 500:
                            self.status = "go around"
                            self.target_alt = 3000
                        elif self.current_alt > desired_alt + 250:
                            self.vertical_speed = 1000
                        elif self.current_alt < desired_alt - 250:
                            self.vertical_speed = 200
                        else:
                            self.vertical_speed = rate_of_descent

                    else: break

    
    def landing(self):
        # --- RWY data ---
        rwy = self.landing_rwy
        desc_angle = math.tan(math.radians(3))
        rate_of_descent = desc_angle * self.current_speed * 101.268
        # self.vertical_speed = rate_of_descent
        distance_to_rwy = pg.math.Vector2(rwy.rwy_data["25"]["pos"]).distance_to(pg.math.Vector2(self.current_position())) / PIXELS_PER_NM
        desired_alt = desc_angle * distance_to_rwy * METERS_PER_NM
        if self.current_alt - desired_alt > 500:
            self.status = "go around"
            self.target_alt = 3000
        elif self.current_alt > desired_alt + 250:
            self.vertical_speed = 1000
        elif self.current_alt < desired_alt - 250:
            self.vertical_speed = 200
        else:
            self.vertical_speed = rate_of_descent
            
    def target_heading_to_point(self, point: Point):
        dx = point.position[0] - self.x
        dy = point.position[1] - self.y
        
        rads = math.atan2(dx, -dy) 
        angle = math.degrees(rads)
        if angle < 0:
            angle += 360

        self.target_heading = angle
    
    def fly_to_point(self):
        if self.target_point is not None:
            self.target_heading_to_point(self.target_point)
            if pg.sprite.collide_rect(self, self.target_point):
                self.target_point = None

    def turn(self, target_heading = None, bank_angle = 25, turn_rate = None):
        # changes the aircrafts current heading (turn rate depends on aircraft speed)
        if target_heading is not None:
            self.target_heading = target_heading

        diff = normalize_angle(self.target_heading - self.current_heading)
        if abs(diff) < 0.1:
            self.current_heading = 360 if self.target_heading % 360 ==0 else self.target_heading % 360
            return
        elif abs(diff) <= 10:
            bank_angle = 10
        else:
            bank_angle = 25

        if bank_angle:
            turn_rate = turn_rate_deg_per_sec( bank_angle, self.current_speed)/FPS

        self.current_heading += np.sign(diff) * min(turn_rate, abs(diff))

        self.current_heading = 360 if self.current_heading ==0 else self.current_heading % 360
    
    def accelerate(self, spd_change=1.5):
        # changes aircraft speed
        diff = self.target_speed - self.current_speed
        if diff != 0:
            self.current_speed += np.sign(diff) * min(abs(diff), spd_change/FPS)

    # def accelerate(self, base_spd_change=1.5):
    #     # 1. Altitude Factor: Reduce engine performance as altitude increases
    #     # Assuming 40,000ft is the ceiling where performance is ~20%
    #     alt_factor = max(0.2, 1 - (self.current_alt / 40000))

    #     # 2. Gravity Factor: Impact of Vertical Speed (FPM) on longitudinal speed
    #     # If VS is negative (descending), gravity_effect is positive (helps accelerate)
    #     # 0.0005 is a tuning constant; adjust based on how "heavy" the plane feels
    #     gravity_effect = -(self.vertical_speed / 1000) * 0.5

    #     # Calculate total potential acceleration
    #     # We apply alt_factor to the base engine power, then add gravity
    #     effective_accel = (base_spd_change * alt_factor) + gravity_effect
        
    #     # Calculate difference
    #     diff = self.target_speed - self.current_speed
    
    #     if diff != 0:
    #         # Determine if we are speeding up or slowing down
    #         direction = np.sign(diff)
            
    #         # Adjust effective_accel based on direction 
    #         # (e.g., gravity helps acceleration but hinders braking while descending)
    #         if direction > 0: # Speeding up
    #             step = max(0.1, effective_accel) # Ensure we don't stall completely
    #         else: # Slowing down
    #             # If descending, gravity_effect is positive, making 'step' smaller (harder to slow)
    #             step = max(0.1, base_spd_change - gravity_effect)

    #         self.current_speed += direction * min(abs(diff), step / FPS)
    
    def climb(self):
        # changes aircraft altitude
        diff = self.target_alt - self.current_alt
        if diff != 0:
            if not self.vertical_speed: 
                self.vertical_speed = 1000
            self.current_alt += np.sign(diff) * min(abs(diff), self.vertical_speed/(60*FPS))
        else:
            self.vertical_speed ==0

    def move(self):
        # moves the aircraft in space
        rad = math.radians(self.current_heading)
        speed_px_s = self.current_speed/3600 * PIXELS_PER_NM / FPS

        self.x += math.sin(rad) * speed_px_s 
        self.y -= math.cos(rad) * speed_px_s
        self.rect.center = (self.x, self.y)

    def draw_heading_line(self, surface, length= 20):
        # draws a straight heading line
        rad = math.radians(self.current_heading - 90)
        cx, cy = self.rect.center

        dx = math.cos(rad) * self.current_speed/3600 * PIXELS_PER_NM  * length
        dy = math.sin(rad) * self.current_speed/3600 * PIXELS_PER_NM * length  
        pg.draw.line(
            surface = surface,
            color = DARKGREEN,
            start_pos = (cx, cy),
            end_pos = (cx + dx, cy + dy),
            width = 2)

    def update(self, screen, font, runway: Runway):
        # updates the aircraft position and speed
        if self.status == "flight":
            self.capture_loc(runway)
        elif self.status == "LOC captured":
            self.approach()
        elif self.status == "final approach":
            self.landing()

        self.fly_to_point()
        self.turn(bank_angle=15)
        self.climb()
        self.move()
        self.accelerate()
        self.draw_heading_line(screen)
        self.draw_aircraft_info(screen, font)

    def draw_trail(self, surface):
        # draws the aircraft trail
        cx, cy = self.rect.center
        trail = pg.Rect(cx-2, cy-2, 5, 5)
        pg.draw.rect(surface, DARKGREEN, trail, width=0)

    def draw_aircraft_info(self, screen, font):
        # draws basic info about the aircraft on screen
        if self.current_alt == self.target_alt:
            symbol = " "
        elif self.current_alt < self.target_alt:
            symbol = "↑"
        else: 
            symbol = "↓"

        text = font.render(f"{self.flight_id}\n{int(self.current_alt//100)}{symbol}= {int(self.target_alt//100)}\n{round(self.current_speed)} {'' if self.status == 'flight' else self.status}",
                        True, LIMEGREEN)
        
        textRect = text.get_rect()
        textRect.center = (self.x-13, self.y - 16)
        screen.blit(text, textRect)
