import pygame
import utm
import numpy as np
import math


pygame.init()

class Road:
    def __init__(self, p1, p2):
        self.x1, self.y1 = p1
        self.x2, self.y2 = p2

        self.slope = (self.y2 - self.y1) / (self.x2 - self.x1) if self.x2 != self.x1 else None
        self.linear = self.y1 - self.slope * self.x1 if self.slope is not None else None
    def is_in_road(self, x, y):
        x1, y1 = self.x1, self.y1
        x2, y2 = self.x2, self.y2
        if (x1 > x2):
            tmp = x1
            x1 = x2
            x2 = tmp
        if (y1 > y2):
            tmp = y1
            y1 = y2
            y2 = tmp

        if self.slope is None:
            return (np.abs(x - x1) < ROAD_SIZE / 2) & (y1 <= y) & (y <= y2)

        slope_target = - 1 / self.slope
        linear_target = y + x / self.slope

        x_intersect = (self.linear - linear_target) / (slope_target - self.slope)
        y_intersect = x_intersect * self.slope + self.linear
        square_dist_to_road = (y_intersect - y) ** 2 + (x_intersect - x) ** 2
        return (x1 <= x_intersect) & (x_intersect <= x2) & (square_dist_to_road <= ROAD_SIZE)


class Car:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.v = 0
        self.a = 0

        self.dir = 0
        self.wheel = 0

        self.breaking = False
    
    def update_pos(self, dt):
        self.v += self.a * dt - DECCEL_FACTOR * self.v * dt * (BREAKING_FACTOR if self.breaking else 1)

        self.x += self.v * math.cos(self.dir) * dt
        self.y += self.v * math.sin(self.dir) * dt

        self.dir += self.wheel * self.v * dt

    def set_acceleration(self, a):
        self.a = a

class World:
    def __init__(self):
        self.pygame_clock = pygame.time.Clock()

        self.car = Car(0, 0)
        self.roads = []
    def tick(self, screen):
        dt = self.pygame_clock.tick(TARGET_FPS) / 1000
        
        self.get_input(dt)
        self.car.update_pos(dt)
        self.draw(screen)

    def raycast(self, screen):
        screen_array = np.zeros((RES_W, RES_H, 3), dtype = np.uint8)

        HALF_H = RES_H // 2
        BASE_FLOOR_CALC = CAR_HEIGHT * PROJ_PLANE_DIST

        screen_x = np.arange(RES_W)
        screen_y = np.arange(HALF_H + 1, RES_H)

        ray_angle = (screen_x / RES_W - 0.5) * FOV / 180 * math.pi
        cos_ray = np.cos(ray_angle)
        ray_dir_x = np.cos(self.car.dir + ray_angle)
        ray_dir_y = np.sin(self.car.dir + ray_angle)

        straight_dist_to_floor = BASE_FLOOR_CALC / (screen_y - HALF_H)

        dist_to_floor = straight_dist_to_floor[np.newaxis, :] / cos_ray[:, np.newaxis]
        floor_x = self.car.x + ray_dir_x[:, np.newaxis] * dist_to_floor
        floor_y = self.car.y + ray_dir_y[:, np.newaxis] * dist_to_floor

        is_road = np.zeros((RES_W, RES_H - HALF_H - 1), dtype = np.bool)
        for road in self.roads:
            is_road |= road.is_in_road(floor_x, floor_y)

        floor_colors = np.where(is_road[:, :, np.newaxis], ROAD_COLOR, GROUND_COLOR)

        screen_array[:, 0:HALF_H + 1] = SKY_COLOR
        screen_array[:, HALF_H + 1:] = floor_colors
        
        raycast_surface = pygame.surfarray.make_surface(screen_array)
        scaled_raycast_surface = pygame.Surface((w, h))
        pygame.transform.scale(raycast_surface, (w, h), scaled_raycast_surface)
        screen.blit(scaled_raycast_surface, (0, 0))
    
    def draw(self, screen):
        screen.fill((225, 225, 225))

        self.raycast(screen)

        fps_label_surface = font.render(str(int(self.pygame_clock.get_fps())), True, (0, 0, 0))
        screen.blit(fps_label_surface, (16, 16))

        velocity_label_surface = font.render(f"{self.car.v * 3.6:.1f} Km / h", True, (0, 0, 0))
        velocity_label_rect = velocity_label_surface.get_rect(bottomright = (w - 16, h - 16))
        screen.blit(velocity_label_surface, velocity_label_rect)
        
    def get_input(self, dt):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        keys = pygame.key.get_pressed()
        self.car.wheel = 0
        if keys[pygame.K_d]:
            self.car.wheel += ROTATION_FACTOR
        if keys[pygame.K_a]:
            self.car.wheel -= ROTATION_FACTOR

        if keys[pygame.K_s]:
            self.car.a = 0
            self.car.breaking = True
        else:
            self.car.breaking = False
            if keys[pygame.K_w]:
                self.car.a = CAR_ACCEL
            else:
                self.car.a = 0

    def add_road(self, road):
        self.roads.append(road)

    def parse_road_data(self, road_data):
        for road_json in road_data["elements"]:
            road = Road()
            for point in road_json["geometry"]:
                x, y, zone_n, zone_letter = utm.from_latlon(point["lat"] - START_LAT, point["lon"] - START_LON)
                point_adjusted = (x, y)
                road.add_point(point_adjusted)

RES_W = 360
RES_H = 270
WINDOW_SCALE = 3

w, h = RES_W * WINDOW_SCALE, RES_H * WINDOW_SCALE
screen = pygame.display.set_mode((w, h))
pygame.display.set_caption("Driver")

font = pygame.font.SysFont("arial", 24)

world = World()

TARGET_FPS = 60
with open('my_lat_lon.txt', 'r') as f:
    lat_lon = f.read().strip().split(',')
    START_LAT = float(lat_lon[0])
    START_LON = float(lat_lon[1])
ROAD_SIZE = 2 ** 2

FOV = 90
CAR_HEIGHT = 1 # m
PROJ_PLANE_DIST = RES_W / 2 / (math.tan(FOV / 2))

ROTATION_FACTOR = 1 / 8
CAR_ACCEL = 3 # m/s^2
DECCEL_FACTOR = 1 / 20 # m/s^2
BREAKING_FACTOR = 75

SKY_COLOR = (0, 200, 255)
GROUND_COLOR = (0, 180, 0)
ROAD_COLOR = (128, 128, 128)

road_data = [[[-34.89404, -8.113252], [-34.895161, -8.112694], [-34.895201, -8.112673], [-34.895826, -8.112377], [-34.896432, -8.11207], [-34.89654, -8.112015], [-34.897147, -8.111712], [-34.89772, -8.111417], [-34.897769, -8.111394], [-34.898391, -8.111064], [-34.898977, -8.110761], [-34.899476, -8.110514], [-34.899528, -8.110488], [-34.899596, -8.110452]], [[-34.896732, -8.115149], [-34.896267, -8.114387], [-34.896228, -8.114322], [-34.8957, -8.11349], [-34.895201, -8.112673], [-34.894716, -8.111855]], [[-34.895337, -8.111536], [-34.895826, -8.112377], [-34.895839, -8.112398], [-34.896283, -8.113177]], [[-34.896432, -8.11207], [-34.896396, -8.112008], [-34.895891, -8.111235]], [[-34.898162, -8.112242], [-34.897047, -8.112813], [-34.896943,-8.112865], [-34.896283, -8.113177], [-34.895786, -8.113444], [-34.8957, -8.11349], [-34.894659, -8.114018], [-34.894625, -8.114037], [-34.894555, -8.114073]]]
world.add_road_data(road_data, center = (START_LAT, START_LON))

while 1:
    world.tick(screen)
    pygame.display.update()