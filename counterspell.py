#!/usr/bin/python3
import pygame
from random import randint, choice
from threading import Thread
from math import floor, ceil
import os
from time import time, sleep

pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((800, 800))
font = pygame.font.Font("UbuntuMono-R.ttf", 100)
smallfont = pygame.font.Font("UbuntuMono-R.ttf", 32)
tinyfont = pygame.font.Font("UbuntuMono-R.ttf", 20)
pygame.mixer.init()

def exitcheck():
    global keypresses, heldkeys
    keypresses = []
    heldkeys = []
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                keypresses.append(event.key)
                if event.key not in heldkeys:
                    heldkeys.append(event.key)
            if event.type == pygame.KEYUP:
                if event.key in heldkeys:
                    heldkeys.remove(event.key)
            if event.type == pygame.QUIT:
                os._exit(0)
Thread(target = exitcheck).start()

def neigh(tile):
    return ((tile[0] - 1, tile[1] - 1), (tile[0] - 1, tile[1]), (tile[0] - 1, tile[1] + 1), (tile[0], tile[1] - 1), tile, (tile[0], tile[1] + 1), (tile[0] + 1, tile[1] - 1), (tile[0] + 1, tile[1]), (tile[0] + 1, tile[1] + 1))

def activate(tile):
    global active, terrain
    for ntile in neigh(tile):
        if ntile in terrain:
            active[ntile] = True

def sign(n):
    if n:
        return int(n / abs(n))
    return 0

def shuffle(thing):
    l = list(thing)
    n = []
    while l:
        x = choice(l)
        l.remove(x)
        n.append(x)
    return n

def passgen(draw):
    global terrain, active, boxes
    changes = {}
    oldactive = active.copy()
    active.clear()
    for tile in oldactive:
        neighbors = 0
        edge = False
        for ntile in neigh(tile):
            if ntile in terrain:
                neighbors += terrain[ntile]
            else:
                edge = True
        if edge:
            neighbors += randint(-6, 9)
        if (neighbors > 4) != terrain[tile]:
            activate(tile)
            changes[tile] = 1 - terrain[tile]
    for tile in changes:
        terrain[tile] = changes[tile]
        if draw:
            drawtile(tile)
    for tile in oldactive:
        if tile not in active and not terrain[tile] and not randint(0, 3071):
            boxes.append(Box(tile, (randint(0, 255), randint(0, 255), randint(0, 255))))
    return len(active)

def drawtile(tile):
    global terrain, visualchunks
    start = time()
    chunk = (floor(tile[0] / 20) * 800, floor(tile[1] / 20) * 800)
    if chunk not in visualchunks:
        visualchunks[chunk] = pygame.Surface((800, 800))
        visualchunks[chunk].fill("white")
    pygame.draw.rect(visualchunks[chunk], {0:"white", 1:"black"}[terrain[tile]], ((tile[0] % 20 * 40, tile[1] % 20 * 40), (40, 40)))
        

def terragen():
    global terrain, visualchunks, active, boxes, souls, camera, targetcam
    souls = 0
    boxes = []
    terrain = {}
    active = {}
    visualchunks = {}
    for x in range(100):
        for y in range(100):
            terrain[(x, y)] = randint(0, 1)
            if 39 < x < 61 and 39 < y < 61:
                terrain[(x, y)] = 0
            active[(x, y)] = True
    activetiles = 10000
    activitylist = [10000]
    nochange = 0
    while activetiles:
        print(activetiles)
        nochange += 1
        activetiles = passgen(False)
        if activetiles not in activitylist:
            nochange = 0
            activitylist.append(activetiles)
        if nochange > 15:
            break
    for tile in terrain:
        drawtile(tile)
    boxes.insert(0, Box((49.5, 49.5), "magenta"))
    camupdate()
    camera = targetcam
    pygame.mixer.music.play(loops = -1)

def camupdate():
    global boxes, targetcam
    targetcam = (boxes[0].tile[0] * 40 - 360, boxes[0].tile[1] * 40 - 360)

def collision(tile):
    global terrain
    for x in (floor(tile[0]), floor(tile[0] + 0.875)):
        for y in (floor(tile[1]), floor(tile[1] + 0.875)):
            if (x, y) not in terrain or terrain[(x, y)]:
                return True
    return False
    
class Box():
    def __init__(self, tile, color):
        self.tile = list(tile)
        self.vel = [0, 0]
        self.surface = pygame.Surface((40, 40))
        self.surface.fill(color)
        self.jumps = 0
        self.heldkeys = []
        self.keypresses = []
        self.heldkeydelays = []
        self.keypressdelays = []
        self.colored = []
        self.soulmark = False
        for x in range(40):
            for y in range(40):
                self.colored.append((x, y))
        self.holes = []
    def groundtouch(self):
        global terrain
        for x in (floor(self.tile[0]), floor(self.tile[0] + 0.875)):
            if (x, floor(self.tile[1] + 1)) not in terrain or terrain[(x, floor(self.tile[1] + 1))]:
                return True
        return False
    def damage(self, amount):
        global boxes, souls
        amount = floor(amount)
        if amount >= len(self.colored):
            boxes.remove(self)
            if self.soulmark:
                souls += 1
            print("death in damage")
            return "AAAA"
        for a in range(amount):
            pixel = choice(self.colored)
            self.colored.remove(pixel)
            self.holes.append(pixel)
            self.surface.set_at(pixel, "white")
    def physics(self):
        global terrain, boxes
        if self == boxes[0]:
            if self.damage(floor(randint(1, 8) / 8)) == "AAAA":
                print("death in physics")
                return "AAAA"
        for x in (floor(self.tile[0]), floor(self.tile[0] + 0.875)):
            for y in (floor(self.tile[1]), floor(self.tile[1] + 0.875)):
                if (x, y) in terrain:
                    if terrain[(x, y)]:
                        terrain[(x, y)] = 0
                        drawtile((x, y))
        for axis in shuffle([0 for a in range(floor(abs(self.vel[0])))] + [1 for a in range(floor(abs(self.vel[1])))]):
            projection = self.tile.copy()
            projection[axis] += sign(self.vel[axis]) / 8
            if collision(projection):
                if self.damage((self.vel[axis] - 1) * 2) == "AAAA":
                    return "AAAA"
                self.vel[axis] = 0
                if self == boxes[0]:
                    camupdate()
            else:
                good = True
                for box in boxes:
                    if box != self and max(abs(projection[0] - box.tile[0]), abs(projection[1] - box.tile[1])) < 1:
                        good = False
                        if self == boxes[0]:
                            box.soulmark = True
                            healing = ceil(len(box.holes) / 8)
                            box.damage(healing)
                            healing = floor(healing / 4)
                            for a in range(healing):
                                if not self.holes:
                                    break
                                pixel = choice(self.holes)
                                self.holes.remove(pixel)
                                self.colored.append(pixel)
                                self.surface.set_at(pixel, "magenta")
                        box.vel[axis] = self.vel[axis]
                if good:
                    self.tile = projection
                else:
                    self.vel[axis] = 0
                            
        if self.groundtouch():
            self.jumps = 3
            if self == boxes[0]:
                camupdate()
        self.vel[1] += 1
    def consciousness(self):
        global heldkeys, keypresses, boxes
        for key in keypresses:
            self.keypressdelays.append([key, 20 * sign(boxes.index(self))])
        for key in heldkeys:
            self.heldkeydelays.append([key, 20 * sign(boxes.index(self))])
        for key in self.keypressdelays.copy():
            if key[1]:
                key[1] -= 1
            else:
                self.keypressdelays.remove(key)
                self.keypresses.append(key[0])
        for key in self.heldkeydelays.copy():
            if key[1]:
                key[1] -= 1
            else:
                self.heldkeydelays.remove(key)
                self.heldkeys.append(key[0])
        if pygame.K_UP in self.keypresses:
            if self.jumps:
                if self == boxes[0]:
                    camupdate()
                self.vel[1] = -11
                self.jumps -= 1
        self.keypresses.clear()
        if pygame.K_LEFT in self.heldkeys:
            self.vel[0] -= 0.5
        if pygame.K_RIGHT in self.heldkeys:
            self.vel[0] += 0.5
        if pygame.K_DOWN in self.heldkeys:
            self.vel[0] -= sign(self.vel[0]) * 0.5
        self.heldkeys.clear()
    def expandterrain(self):
        newtiles = []
        for x in range(floor(self.tile[0]) - 15, ceil(self.tile[0]) + 16):
            for y in range(floor(self.tile[1]) - 15, ceil(self.tile[1]) + 16):
                if (x, y) not in terrain:
                    newtiles.append((x, y))
        for tile in newtiles:
            terrain[tile] = randint(0, 1)
            drawtile(tile)
            activate(tile)
        passgen(True)

def show():
    global visualchunks, targetcam, camera, boxes, souls
    if not -1 < boxes[0].tile[0] * 40 - targetcam[0] < 721 or not -1 < boxes[0].tile[1] * 40 - targetcam[1] < 721:
        camupdate()
    camera = (camera[0] + floor((targetcam[0] - camera[0]) / 8), camera[1] + floor((targetcam[1] - camera[1]) / 8))
    screen.fill("white")
    for x in (floor(camera[0] / 800) * 800, floor(camera[0] / 800) * 800 + 800):
        for y in (floor(camera[1] / 800) * 800, floor(camera[1] / 800) * 800 + 800):
            if (x, y) in visualchunks:
                screen.blit(visualchunks[(x, y)], (x - camera[0], y - camera[1]))
    for box in boxes:
        screen.blit(box.surface, (box.tile[0] * 40 - camera[0], box.tile[1] * 40 - camera[1]))
    healthstring = str(len(boxes[0].colored))
    screen.blit(font.render(healthstring, True, "magenta"), (0, 0))
    soulstring = str(souls)
    screen.blit(font.render(soulstring, True, (0, 255, 191)), (800 - 50 * len(soulstring), 0))
    pygame.display.update()

def boxstuff():
    global boxes, keypresses
    for box in boxes:
        thebox = box == boxes[0]
        if box.physics() == "AAAA" and thebox:
            print("death in boxstuff")
            return "AAAA"
    for box in boxes:
        box.consciousness()
    keypresses.clear()
    boxes[0].expandterrain()

def endscreen():
    global souls, highscore, keypresses
    pygame.mixer.music.rewind()
    pygame.mixer.music.stop()
    pygame.mixer.Sound.play(pygame.mixer.Sound("difeat.wav"))
    screen.fill("black")
    screen.blit(font.render(f"Souls: {souls}", True, (0, 255, 191)), (0, 0))
    screen.blit(font.render(f"Best:  {highscore}", True, "magenta"), (0, 100))
    if souls > highscore:
        screen.blit(font.render("NEW HIGHSCORE!!!", True, "white"), (0, 200))
        screen.blit(smallfont.render(choice(("Cannabalism is fun!", "The strong shall eat the weak", "You deserve this. They didn't.", "You monster.", "cannabalism go brr", "I'm genuinely impressed.")), True, "white"), (0, 300))
    screen.blit(smallfont.render("[enter] to play again", True, "white"), (0, 768))
    pygame.display.update()
    while pygame.K_RETURN not in keypresses:
        pass
    keypresses.clear()

def tutorial():
    global highscore
    highscore = 0
    screen.fill("white")
    screen.blit(pygame.image.load("counterspell-01.png"), (0, 0))
    screen.blit(smallfont.render("[enter] to start", True, "white"), (274, 498))
    screen.blit(smallfont.render("[enter] to start", True, "black"), (272, 500))
    pygame.display.update()
    while pygame.K_RETURN not in keypresses:
        pass
    keypresses.clear()
    for text in (("Welcome to the tutorial!", "Press [enter] to advance through the tutorial.", "Press [s] to conclude the tutorial at any time."), ("This game is an infinite procedurally generated platformer.",), ("Use arrow keys to move.", "Use [down] to slow down.", "Note: You can triple jump!"), ("The pink number on the top left will be your health.", "Your health decreases with time, and when you ram into walls.", "(This includes fall damage!)"), ("Your health is also represented by how much of you is left.", "You can have up to 1600 health."), ("Boxes are creatures which do what you do (with a delay) and look just like you.", "Chase down and push into other boxes to replenish your health.", "When you take health from a box, it will also give you a soul when it dies."), ("Your goal is to consume as many souls as possible before death.", "Good luck. You'll need it.", "No, seriously, the RNG in this game sucks."), ("The tutorial is over now. Press [enter] to start the game.",)):
        screen.fill("black")
        lines = 0
        for line in text:
            screen.blit(tinyfont.render(line, True, "white"), (0, lines * 20))
            lines += 1
        pygame.display.update()
        while True:
            if pygame.K_RETURN in keypresses or pygame.K_s in keypresses:
                break
        if pygame.K_s in keypresses:
            break
        keypresses.clear()
    pygame.mixer.music.load("nothing_wrong.wav")

highscore = 0
tutorial()
while True:
    terragen()
    while True:
        start = time()
        if boxstuff() == "AAAA":
            print("death in main loop")
            break
        show()
        sleep(max(0, 0.02 - (time() - start)))
    endscreen()
