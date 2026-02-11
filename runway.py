import pygame as pg
import math
from constants import *
from point import Point

scale =  PIXELS_PER_NM *1/ METERS_PER_NM

class Runway(pg.sprite.Sprite):
    def __init__(self, runway_heading, length=2550*scale, pos = None):
        super().__init__()
        if pos:
            self.x, self.y = pos
        else: 
            self.x = (SCREEN_WIDTH - RIGHT_BAR_WIDTH)/2
            self.y = SCREEN_HEIGHT/2

        radian_angle = (runway_heading+90)*math.pi/180
        self.start_pos = (self.x, self.y)
        self.end_pos = (self.x + math.cos(radian_angle)*length, self.y + math.sin(radian_angle)*length)
        self.runway_heading = runway_heading
            
        self.rwy_label = f"{runway_heading//10:02d}"
        self.rwy_label2 = f"{((runway_heading + 180) % 360)//10:02d}"

        self.rwy_data = {
            self.rwy_label: {"pos": self.start_pos, "hdg": self.runway_heading,
            "approach_points": pg.sprite.Group([Point("BAWZI", (50, 8, 13.7), (20, 13, 4.5)),
                                                        Point("OFFUK", (50, 7, 11.8), (20, 5, 28.3)),
                                                        Point("KK362", (50, 6, 13.2), (19, 58, 19.8)),
                                                        Point("25_threshold", *self.end_pos, screen_coords=True)])},
            self.rwy_label2: {"pos": self.end_pos, "hdg": (runway_heading + 180) % 360 }
        }

    def draw(self, screen, font):
        pg.draw.line(screen, color=GRAY, start_pos=self.start_pos, end_pos=self.end_pos, width=4)
        screen.blit(font.render(self.rwy_label, True, WHITE), self.end_pos)
        screen.blit(font.render(self.rwy_label2, True, WHITE), self.start_pos)
        