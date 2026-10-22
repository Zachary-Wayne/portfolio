"""
Lab 4 - Spring Simulation
author: Zachary Wayne
license: CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)
"""

import pygame
from pygame import gfxdraw
import numpy as np
from scipy.integrate import ode

# Global variables
GRAVITY = [0, -9.8]
DT = 0.05
all_springs = []

class Spring:
    def __init__(self, anchor, K, position_from_anchor, rest_length=50, mass=2, damping=0.05):
        if K <= 0: raise ValueError('Spring constant must be greater than 0')
        if rest_length <= 0: raise ValueError('Rest length must be greater than 0')
        if mass <= 0: raise ValueError('Mass must be greater than 0')

        self.K = K
        self.damping = damping
        self.rest_length = rest_length
        self.mass = mass

        self.connectedSprings = []
        self.mass_damping = self.mass * self.damping
        self.mass_radius =  int(self.mass * 4)
        self.spring_thickness = int(self.K * 2) + 1
        self.external_force = GRAVITY

        if isinstance(anchor, Spring):
            anchor.addConnectedSpring(self)
        self.anchor = anchor

        self.pos = [position_from_anchor[0] + self.getAnchorPosition()[0], position_from_anchor[1] + self.getAnchorPosition()[1]]
        
        self.solver = ode(self.f).set_integrator('dop853') 
        self.solver.set_initial_value([self.pos[0], self.pos[1], 0, 0], 0)

        all_springs.append(self)

    def f(self, _, state):
        x, y, vx, vy = state

        dx = vx
        dy = vy

        anchor_x, anchor_y = self.getAnchorPosition()
        dx_anchor = x - anchor_x
        dy_anchor = y - anchor_y
        
        distance = np.hypot(dx_anchor, dy_anchor)

        spring_force = self.K * (self.rest_length - distance)
        spring_force_div_distance = spring_force / distance

        dvx = (spring_force_div_distance * dx_anchor - (self.mass_damping * vx) + self.external_force[0]) / self.mass
        dvy = (spring_force_div_distance * dy_anchor - (self.mass_damping * vy) + self.external_force[1]) / self.mass

        return [dx, dy, dvx, dvy]

    def update(self, screen):
        # Calculate force exerted by springs on each other
        for spring in self.connectedSprings:
            self.setExternalForce(spring.forceExertedBySpring(self))

        # Integrate the system
        self.solver.integrate(self.solver.t + DT)

        # Get current position
        x, y, vx, vy = self.solver.y
        self.pos = [x, y]
        x_anchor, y_anchor = self.getAnchorPosition()
        ax, ay = int(half_width + x), int(half_height - y)

        # Calculate the colour of the spring
        distance_ratio = (np.hypot(x - x_anchor, y - y_anchor) / self.rest_length - 1).clip(-1, 1)
        val = 255 - 255 * abs(distance_ratio)
        colour = (255, val, val) if distance_ratio < 0 else (val, val, 255)

        # Draw spring as a line
        pygame.draw.line(screen, (colour), (ax, ay), (half_width + x_anchor, half_height - y_anchor), self.spring_thickness)

        # Draw mass as a circle
        gfxdraw.aacircle(screen, ax, ay, self.mass_radius, (255, 255, 255))

        # Reset external forces
        self.external_force = GRAVITY
        
        # Set the solver's new initial value
        self.solver.set_initial_value([x, y, vx, vy], 0)

    def getAnchorPosition(self):
        if isinstance(self.anchor, Spring):
            return self.anchor.pos
        else:
            return self.anchor
    
    def setExternalForce(self, force):
        self.external_force += force

    def forceExertedBySpring(self, other_spring):
        delta_x = other_spring.solver.y[0] - self.solver.y[0]
        delta_y = other_spring.solver.y[1] - self.solver.y[1]
        distance = np.hypot(delta_x, delta_y)
        spring_force = self.K * (self.rest_length - distance)
        return spring_force * np.array([delta_x / distance, delta_y / distance])

    def addConnectedSpring(self, other_spring):
        self.connectedSprings.append(other_spring)


class Slider:
    def __init__(self, x, y, width, height, min_value, max_value, label, default_value = 0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_value = min_value
        self.max_value = max_value
    
        self.value = min_value
        # calculate thumb position based on default value
        self.thumb_x = self.x + self.width * (default_value - self.min_value) / (self.max_value - self.min_value)
        self.thumb_y = self.y
        self.dragging = False

        self.label = label
        self.value = default_value

    def draw(self, screen):
        dt_slider.update()
        # Draw label
        displayText(self.label + ": %.2f" % self.value, self.x, self.y + 30, antialias = True)
        # Draw track
        pygame.draw.rect(screen, (200, 200, 200), (self.x, self.y, self.width, self.height))
        # Draw thumb
        pygame.draw.rect(screen, (100, 100, 100), (self.thumb_x, self.thumb_y, self.height, self.height))

    def update(self):  
        if self.dragging:
            mx, _ = pygame.mouse.get_pos()
            # Update thumb position, making sure it stays within the bounds
            self.thumb_x = max(self.x, min(mx - self.height/2, self.x + self.width - self.height))
            # Update value based on thumb position
            self.value = (self.thumb_x - self.x) / (self.width - self.height) * (self.max_value - self.min_value) + self.min_value

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            # Check if the mouse is over the thumb
            if self.thumb_x - self.height <= mx <= self.thumb_x + self.height and self.thumb_y <= my <= self.thumb_y + self.height * 2:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

def displayText(text, x, y, antialias = False):
    font = pygame.font.Font(None, 24)
    text_surface = font.render(text, antialias, (200, 200, 200))
    text_rect = text_surface.get_rect()
    text_rect.topleft = (x, y)
    screen.blit(text_surface, text_rect)

# Initialize Pygame
pygame.init()

# Set up the simulation window
width, height = 800, 600
half_width, half_height = width >> 1, height >> 1
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Spring Simulation")

# Initialize springs
spring_a1 = Spring(K=0.5, anchor=[-300, 150], position_from_anchor=[20, 20])
spring_a11 = Spring(K=1.5, anchor=spring_a1, position_from_anchor=[-20, 40])

spring_b1 = Spring(K=3, anchor=[-200, 150], position_from_anchor=[30, 40], mass=1)
spring_b11 = Spring(K=0.5, anchor=spring_b1, position_from_anchor=[10, 90], mass=4)

spring_c1 = Spring(K=3, anchor=[-100, 150], position_from_anchor=[30, 40], mass=4)
spring_c11 = Spring(K=0.5, anchor=spring_c1, position_from_anchor=[10, 90], mass=1)

spring_d1 = Spring(K=1, anchor=[0, 150], position_from_anchor=[40, -30], mass=5)
spring_d11 = Spring(K=1, anchor=spring_d1, position_from_anchor=[20, 80], rest_length=40, mass=3)
spring_d111 = Spring(K=1, anchor=spring_d11, position_from_anchor=[40, 10], rest_length=30, mass=1)

spring_e1 = Spring(K=3, anchor=[100, 150], position_from_anchor=[30, 40])
spring_e11 = Spring(K=0.5, anchor=spring_e1, position_from_anchor=[-10, 30], mass=5)
spring_e12 = Spring(K=0.5, anchor=spring_e1, position_from_anchor=[-10, -40], rest_length=70)

spring_f1 = Spring(K=3, anchor=[200, 150], position_from_anchor=[40, -30])
spring_f11 = Spring(K=1.2, anchor=spring_f1, position_from_anchor=[20, 80], rest_length=20)
spring_f12 = Spring(K=0.8, anchor=spring_f1, position_from_anchor=[40, 10], mass=1)
spring_f111 = Spring(K=1, anchor=spring_f11, position_from_anchor=[-10, 10], mass=5)
spring_f112 = Spring(K=0.4, anchor=spring_f11, position_from_anchor=[50, 10])
spring_f121 = Spring(K=0.4, anchor=spring_f12, position_from_anchor=[10, 40])

spring_g1 = Spring(K=3, anchor=[300, 150], position_from_anchor=[40, -30], mass=4)
spring_g11 = Spring(K=0.7, anchor=spring_g1, position_from_anchor=[50, 10], rest_length=20)
spring_g12 = Spring(K=0.7, anchor=spring_g1, position_from_anchor=[10, 40], rest_length=40)
spring_g13 = Spring(K=0.7, anchor=spring_g1, position_from_anchor=[10, -40], rest_length=60)
spring_g14 = Spring(K=0.7, anchor=spring_g1, position_from_anchor=[-10, -40], rest_length=80)
spring_g15 = Spring(K=0.7, anchor=spring_g1, position_from_anchor=[-10, 40], rest_length=100)

# create the UI elements
dt_slider = Slider(10, 10, 200, 20, -0.1, 0.1, "DT", default_value = DT)

# Set up the clock for controlling the frame rate
clock = pygame.time.Clock()

# Main simulation loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        dt_slider.handle_event(event)
    
    # Clear the screen
    screen.fill((0,0,0))

    # Get slider values
    DT = dt_slider.value
    
    # Info stuff
    displayText("FPS: " + str(int(clock.get_fps())), width - 120, 20)
    displayText("Springs: " + str(len(all_springs)), width - 120, 50)
    
    # Update each spring
    for spring in all_springs:
        spring.update(screen)

    # Update the display
    dt_slider.draw(screen)
    pygame.display.flip()

    # Control the frame rate
    clock.tick(208)

# Quit Pygame
pygame.quit()