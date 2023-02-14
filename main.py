import pygame as pg;
from os import urandom;
from time import time;
from random import randint, seed;


class Scene:
    menu = 0;
    play = 1;

class Color:
    black = (0, 0, 0);
    red = (255, 0, 0);
    green = (0, 255, 0);
    blue = (0, 0, 255);
    white = (255, 255, 255);


WIDTH, HEIGHT = 640, 480; FPS = 60;
DISPLAY = pg.display.set_mode((WIDTH, HEIGHT), pg.DOUBLEBUF);

BIRD_POSITION = WIDTH / 8;
BIRD_SIZE = HEIGHT / 12;

BIRD_START_ALTITUDE = HEIGHT / 2;
BIRD_JUMP_POWER = BIRD_SIZE / 1.5;

BIRD_FALL_SPEED = BIRD_SIZE / 15;
BIRD_TERMINAL_VELOCITY = BIRD_FALL_SPEED * 4;


SCORE_FONT = "Comic Sans";
SCORE_FONT_SIZE = 40;
SCORE_POSITION_X = BIRD_POSITION / 2;
SCORE_POSITION_Y = HEIGHT / 8;


PIPE_WIDTH = BIRD_SIZE * 2;
PIPE_VOID_SIZE = BIRD_SIZE * 5;

PIPE_VELOCITY = PIPE_WIDTH / 16;
MAX_PIPE_VELOCITY = PIPE_VELOCITY * 8;
PIPE_VELOCITY_INCREASE = PIPE_VELOCITY / 10;

PIPE_MIN_ALTITUDE = PIPE_VOID_SIZE / 4;
PIPE_MAX_ALTITUDE = HEIGHT - PIPE_VOID_SIZE;

PIPE_START_POSITION = WIDTH + PIPE_WIDTH;
PIPE_END_POSITION = -PIPE_WIDTH;

PIPE_SPAWN_COOLDOWN = PIPE_VELOCITY * 42;
PIPE_MIN_COOLDOWN = PIPE_SPAWN_COOLDOWN / 5;
PIPE_SPAWN_COOLDOWN_DECREASE = PIPE_SPAWN_COOLDOWN / 10;


class Bird:
    def __init__(self):
        self.reset();

    def reset(self):
        self.score = 0;
        self.next_pipe_seed_type = 0;
        self.altitude = BIRD_START_ALTITUDE;
        self.velocity = BIRD_FALL_SPEED;
        self.position = pg.Rect(BIRD_POSITION, self.altitude, BIRD_SIZE, BIRD_SIZE);

    def update(self, scene:int):
        if scene == Scene.play:
            if self.velocity < BIRD_TERMINAL_VELOCITY:
                self.velocity += BIRD_FALL_SPEED;

        self.altitude += self.velocity;
        self.position.centery = self.altitude;

    def react(self, event:list):
        if event.type == pg.KEYDOWN or event.type == pg.MOUSEBUTTONDOWN:
            self.velocity = -BIRD_JUMP_POWER;

    def draw(self, color:tuple):
        pg.draw.rect(DISPLAY, color, self.position);

    def is_collided(self, pipes:list) -> bool:
        if self.position.centery < 0 or self.position.centery > HEIGHT: return True;

        if pipes:
            for idx in range(3 if len(pipes) > 3 else len(pipes)):
                pipe = pipes[idx];
                #==# if arrived pipe #==#
                if pipe.top.left < self.position.right:
                    #==# if colliding vertically #==#
                    if self.position.top < pipe.top.bottom or \
                            self.position.bottom > pipe.bottom.top:
                        return True;
                    else: #==# if not collided vertically #==#
                        if pipe.seed_type == self.next_pipe_seed_type:
                            self.score += 1;
                            if self.next_pipe_seed_type == pipe.seed_type:
                                self.next_pipe_seed_type = 0 if pipe.seed_type else 1;
                        

class Pipe:
    def __init__(self, seed_type:int):
        self.reset(seed_type);

    def reset(self, seed_type:int):
        self.seed_type = seed_type;
        self.reached_end = False;
        self.velocity = PIPE_VELOCITY;
        self.set_random_altitude();

    def update(self, scene:int, velocity:int):
        if scene == Scene.play:
            if self.top.centerx > PIPE_END_POSITION:
                self.top.centerx -= velocity;
                self.bottom.centerx -= velocity;
            else:
                self.reached_end = True;
                if velocity < MAX_PIPE_VELOCITY:
                    velocity += PIPE_VELOCITY_INCREASE;
                    self.velocity = velocity;
                elif velocity > MAX_PIPE_VELOCITY:
                    self.velocity = MAX_PIPE_VELOCITY;
    
    def set_random_altitude(self):
        if self.seed_type == 0:
            seed(int(time()));
        else:
            seed(int.from_bytes(urandom(4)));

        self.altitude = randint(int(PIPE_MIN_ALTITUDE), int(PIPE_MAX_ALTITUDE));
        self.top = pg.Rect(PIPE_START_POSITION, 0, PIPE_WIDTH, self.altitude);
        self.bottom = pg.Rect(PIPE_START_POSITION, self.altitude + PIPE_VOID_SIZE,
                            PIPE_WIDTH, HEIGHT);

    def draw(self, color1:tuple, color2:tuple=(-1, -1, -1)):
        pg.draw.rect(DISPLAY, color1, self.top);
        color2 = color1 if color2[0] == -1 else color2;
        pg.draw.rect(DISPLAY, color2, self.bottom);


class Game:
    def __init__(self):
        pg.init();
        self.reset();

    def reset(self):
        self.clock = pg.time.Clock();
        self.spawn_cooldown = PIPE_SPAWN_COOLDOWN;
        self.pipe_cooldown = self.spawn_cooldown;
        self.running = True;
        self.scene = Scene.menu;
        self.game_over = False;
        self.score_text = pg.font.SysFont(SCORE_FONT, SCORE_FONT_SIZE);
        self.bird = Bird();
        self.pipe_seed_type = 0;
        self.pipes = [Pipe(self.pipe_seed_type),];
        self.pipes_to_remove = [];
        self.difficulty = PIPE_VELOCITY;

    def update(self):
        #==# handle inputs #==#
        self.react();

        #==# move bird if alive #==#
        if self.game_over:
            self.reset();

        self.bird.update(self.scene);

        #==# spawn pipe #==#
        if self.pipe_cooldown:
            if self.scene == Scene.play:
                self.pipe_cooldown -= 1;
        else:
            if self.pipe_seed_type == 0:
                self.pipe_seed_type = 1;
            else:
                self.pipe_seed_type = 0;
            
            self.pipes.append(Pipe(self.pipe_seed_type));
            if self.spawn_cooldown > PIPE_MIN_COOLDOWN:
                self.spawn_cooldown -= PIPE_SPAWN_COOLDOWN_DECREASE;
            if self.spawn_cooldown < PIPE_MIN_COOLDOWN:
                self.spawn_cooldown = PIPE_MIN_COOLDOWN;
            self.pipe_cooldown = self.spawn_cooldown;

        #==# move pipes #==#
        if self.pipes:
            for idx, pipe in enumerate(self.pipes):
                pipe.update(self.scene, self.difficulty);
                if pipe.reached_end:
                    self.pipes_to_remove.append(idx);

            if self.pipes_to_remove:
                self.difficulty = self.pipes[self.pipes_to_remove[0]].velocity;
                for pipe in self.pipes_to_remove:
                    self.pipes.pop(pipe);

                self.pipes_to_remove.clear();

        #==# draw things #==#
        self.draw();
        self.clock.tick(FPS);

    def draw(self):
        DISPLAY.fill(Color.black);
        self.bird.draw(Color.green);
        if self.scene == Scene.play:
            for pipe in self.pipes:
                pipe.draw(Color.red, Color.blue);
            text = self.score_text.render(f"{self.bird.score}", True, Color.white);
            rect = text.get_rect();
            rect.center = (SCORE_POSITION_X, SCORE_POSITION_Y);
            DISPLAY.blit(text, rect);
        pg.display.update();

    def react(self):
        for event in pg.event.get():
            #==# exit event #==#
            if event.type == pg.QUIT:
                self.running = False;
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.running = False;
            #==# switch scene #==#
                elif self.scene == Scene.menu:
                    self.scene = Scene.play;
            elif event.type == pg.MOUSEBUTTONDOWN:
                if self.scene == Scene.menu:
                    self.scene = Scene.play;

            #==# jump bird if alive #==#
            if self.bird.is_collided(self.pipes):
                self.game_over = True;
            
            self.bird.react(event);


if __name__ == "__main__":
    game = Game();
    print("Bird: game started.");
    while game.running:
        game.update();
    else:
        print("Bird: game exited.");
        pg.quit();
