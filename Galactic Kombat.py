# This is a videogame in the style of Space Invaders.
# You pilot a ship at the botom of the screen and attempt
# to shoot down various enemies at the top, whilst also
# dodging their shots.

# Legend:
#     -background: https://opengameart.org/content/space-skybox-0
#     -MySpaceShip: https://opengameart.org/content/purple-space-ship
#     -ShipDefaultBullet: https://opengameart.org/content/pixel-bullet
#     -EnemyBullet2: https://opengameart.org/content/missile-32x32

import pygame
from pygame.locals import *
import random
import abc

    # A Catalogue of color codes to be used for displaying.
    # Currently intializes the codes for red and greed
ColorPallete ={
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "white": (255, 255, 255)
}

victory_condition = 0

class GenericObject(pygame.sprite.Sprite):
    """
    Generic class for 2D objects on the screen
    """
    def __init__(self, x_coord:int, y_coord:int, image:str):
        """
        Intitalize the sprite that will be used for the object as well as the
        point that will be used to center it on the screen at the given coordinates.
        """
        pygame.sprite.Sprite.__init__(self)
        self.__image = pygame.image.load(image)
        self.__mask = pygame.mask.from_surface(self.__image)
        self.__rect = self.__image.get_rect()
        self.__rect.center = [x_coord, y_coord]

    @abc.abstractmethod
    def update(self):
        pass

    @property
    def rect(self):
        return self.__rect
    
    @property
    def image(self):
        return self.__image
    
    @property
    def mask(self):
        return self.__mask

class GenericProjectileType(GenericObject):
    """
    This class represents the generic bullet type that is inherited by all others.
    """
    def __init__(self, x_coord:int, y_coord:int, image:str, cooldown:int, speed:int):
        super().__init__(x_coord, y_coord, image)
        self.__cooldown = cooldown
        self.__speed = speed

    def get_cooldown(self):
         return self.__cooldown

    @property
    def speed(self):
        return self.__speed
        

class UpwardsBullet(GenericProjectileType):
    """
    This class represents a bullet that travels upwards.
    """
    def update(self, enemy_ship_group):
        """
        Update the bullet's position. If it goes off the screen, delete it
        """
        self.rect.y -= self.speed
        if self.rect.bottom < 0:
            self.kill()

        if pygame.sprite.spritecollide(self, enemy_ship_group, True, pygame.sprite.collide_mask):
            self.kill()

class DownwardsBullet(GenericProjectileType):
    """
    This class represents a bullet that travels upwards.
    """
    def __init__(self, x_coord:int, y_coord:int, image:str, cooldown:int, speed:int, height):
        """
        Call the constructor of GenericProjectileType and set the top as a limit for the bullet.
        """
        super().__init__(x_coord, y_coord, image, cooldown, speed)
        self.__top = height

    def update(self, my_ship_group):
        """
        Update the bullet's position. If it goes off the screen, delete it
        """
        self.rect.y += self.speed
        if self.rect.top > self.__top:
            self.kill()

        if pygame.sprite.spritecollide(self, my_ship_group, False, pygame.sprite.collide_mask):
            ship = pygame.sprite.Group.sprites(my_ship_group)[0]
            ship.remaining_health -= 1
            self.kill()

class WaponsSytem():
    """
    This class acts similar to a Factory, creating bullets of the specified type
    at the specified location
    """

    def create_bullet(self, x_coord:int, y_coord:int, image, speed:int, cooldown:int, upward_or_downward, height = None):
        """
        This class initializes a bullet by instantiating a GenericProjectileType
        at the given coordinates, with the speed and image that passed on.
        If upward_or_downward is set, it will be an UpwardsBullet. Else it will
        be a DownwardsBulet
        """
        if upward_or_downward:
            return UpwardsBullet(x_coord, y_coord, image, cooldown, speed)
        return DownwardsBullet(x_coord, y_coord, image, cooldown, speed, height)
    
class Enemy(GenericObject):
    """
    This class is used to create the various enemies that the player will be facing
    """
    def __init__(self, x_coord:int, y_coord:int, image:str, bullet_image:str, bullet_speed:int, game_master):
        """
        Intitalize the sprite that will be used for the ship as well as the
        point that will be used to center it on the screen at the given coordinates.
        The speed and bullet type are hardcoded. The screen is also passed onto the object
        so it can update itself. The step and steps variables are hardcoded to allow the
        ship to move horizontally.
        """

        super().__init__(x_coord, y_coord, image)
        self.__speed = 10
        self.__bullet_image = bullet_image
        self.__bullet_speed = bullet_speed
        self.__steps = 0
        self.__step = 1

    def update(self):
        """
        Make the ship move horizontally to a limit of 150 pixels
        from where it started in each direction 
        """
        self.rect.x += self.__speed
        self.__steps += self.__step
        if abs(self.__steps) >= 15:
            self.__step *= -1
            self.__speed *= -1

    @property
    def bullet_image(self):
        return self.__bullet_image
    
    @property
    def bullet_speed(self):
        return self.__bullet_speed


class MyShip(GenericObject):
    """
    This class represents the spaceship controlled by the player
    """

    def __init__(self, x_coord:int, y_coord:int, image:str, health:int, game_master):
        """
        Intitalize the sprite that will be used for the ship as well as the
        point that will be used to center it on the screen at the given coordinates.
        The speed and bullet type are hardcoded. Both current and total health are initially
        set to the vallue that is passed on here. The screen is also passed onto the object
        so it can update itself.
        """
        super().__init__(x_coord, y_coord, image)
        self.__speed = 12
        self.__starting_health = health
        self.__remaining_health = health
        self.__game_master = game_master
        self.__weapon_system = game_master.weapon_system
        self.__last_time_fired = pygame.time.get_ticks()
        self.__cooldown = 500

    def update(self):
        """
        Function sued to move the spaceship left or right, 
        according to the key that is pressed.
        New Projectiles are generated when space is pressed
        The health bar will also be drawn beneath the Ship
        """
        # Control the position of the shup with the Left and Right keys
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if key[pygame.K_RIGHT] and self.rect.right < self.__game_master.width :
            self.rect.x += self.speed

        # get the current time before checking for having presseed SPACE
        get_time = pygame.time.get_ticks()

        # if more time hjas gone by since the last time SPACE was pressed
        # than the weapon system cooldown, fire a bullet
        if key[pygame.K_SPACE] and get_time - self.__last_time_fired > self.__cooldown:
            bullet = self.__weapon_system.create_bullet(self.rect.centerx, self.rect.top, "Images/ShipDefaultBullet.png", 24, 500, upward_or_downward = True)
            self.__game_master.add_my_bullet(bullet)
            self.__last_time_fired = get_time

        # draw 2 hjealth bars under the ship, a red one that is covered by a green one
        # which shrinks, gradually revealing the red opne, as the ship gets hit
        pygame.draw.rect(self.__game_master.screen, ColorPallete["red"], (self.rect.x, (self.rect.bottom + 10), self.rect.width, 15))
        if self.__remaining_health > 0:
            pygame.draw.rect(self.__game_master.screen, ColorPallete["green"], (self.rect.x, (self.rect.bottom + 10), int(self.rect.width * (self.__remaining_health)/ self.__starting_health), 15))
    
    @property
    def speed(self):
         return self.__speed
    
    @property
    def projetyle_type(self):
         return self.__projetyle_type
    
    @property
    def last_time_fired(self):
         return self.__last_time_fired
    
    @property
    def cooldown(self):
        return self.__cooldown
    
    @property
    def remaining_health(self):
        return self.__remaining_health
    
    @remaining_health.setter
    def remaining_health(self, a):
        self.__remaining_health = a



class GameMaster():
    """
    This is the class in charge of handling the execution of the game  
    """
    def __init__(self, width:int, height:int, fps:int, caption:str, background:str):
        """
        Intitalize the width, height and FPS, caption and background variables
        Object group is a list of all the generic objects. It begins as
        an empty sprite group. The enemies dictionary conmtains all the .png
        images that will be used for enemies, and their bullets. The map 
        specifies where each enemy should go. an The weapons system will be
        used by the ships to create bullets.
        """
        self.__clock = pygame.time.Clock()
        self.__fps = fps
        self.__width = width
        self.__heigth = height
        self.__caption = caption
        self.__background = background
        self.__my_bullets_group = pygame.sprite.Group()
        self.__enemy_bullets_group = pygame.sprite.Group()
        self.__ship_group = pygame.sprite.Group()
        self.__enemy_ship_group = pygame.sprite.Group()
        self.__enemies = {"enemy 1": {"Image": "Images/enemy.png", "Bullet": "Images/EnemyBullet1.png", "Bullet Speed": 18}, "enemy 2": {"Image": "Images/enemy2.png", "Bullet": "Images/EnemyBullet2.png", "Bullet Speed": 36}}
        self.__enemies_map =[
            [                        ( 312, 100, "enemy 2"), ( 637, 100, "enemy 2"), ( 963, 100, "enemy 2"), ( 1288, 100, "enemy 2"), ],
            [( 220, 200, "enemy 1"), ( 454, 200, "enemy 1"), ( 688, 200, "enemy 1"), ( 922, 200, "enemy 1"), ( 1156, 200, "enemy 1"), ( 1390, 200, "enemy 1")],
            [( 220, 300, "enemy 1"), ( 454, 300, "enemy 1"), ( 688, 300, "enemy 1"), ( 922, 300, "enemy 1"), ( 1156, 300, "enemy 1"), ( 1390, 300, "enemy 1")],
            [( 220, 400, "enemy 1"), ( 454, 400, "enemy 1"), ( 688, 400, "enemy 1"), ( 922, 400, "enemy 1"), ( 1156, 400, "enemy 1"), ( 1390, 400, "enemy 1")]        
        ]
        self.__last_time_enemy_fired = pygame.time.get_ticks()
        self.__enemy_bulled_cooldown = 1000
        self.__weapon_system = WaponsSytem()
        self.create_enemies()

    def start_display(self):
        """
        Start the game display:
            -set the game mode with the width and heigth
            -set the display caption
            -set the game background
        """

        self.__screen = pygame.display.set_mode((self.__width, self.__heigth))
        pygame.display.set_caption(self.__caption)
        self.__game_background = pygame.image.load(self.__background)

    def screen_message(self, received_text):
        """
        Function to paste text on screen
        """
        pygame.init()
        font_to_use = pygame.font.SysFont('Arial', 50)
        image = font_to_use.render(received_text, True, ColorPallete["red"])
        x_coord = int(self.__width / 2 - 110)
        y_coord = int(self.__heigth / 2 + 50)
        self.__screen.blit(image, (x_coord, y_coord))

    def create_enemies(self):
        """
        Crerates enemies according to the enemies_map and enemies dictionary provided earlier.
        """
        for row in self.__enemies_map:
            for enemy in row:
                x_coord = enemy[0]
                y_coord = enemy[1]
                enemy_img = self.__enemies[enemy[2]]["Image"]
                bullet_img = self.__enemies[enemy[2]]["Bullet"]
                bullet_speed = self.__enemies[enemy[2]]["Bullet Speed"]

                new_enemy = Enemy(x_coord, y_coord, enemy_img, bullet_img, bullet_speed, self)
                self.add_enemy_ship(new_enemy)

    def add_enemy_bullet(self):
        """
        Adds an enemy bullet originating from a random enemy ship.
        This is only done once a second, to a limit of 5 bullets.
        """

        # get the current time before the enmy attempts to attack
        get_time = pygame.time.get_ticks()
        if get_time - self.__last_time_enemy_fired > self.__enemy_bulled_cooldown and len(self.__enemy_bullets_group) <= 10 and len(self.__enemy_ship_group) > 0:
            enemy_ship = random.choice(self.__enemy_ship_group.sprites())
            bullet = self.__weapon_system.create_bullet(enemy_ship.rect.centerx, enemy_ship.rect.top, enemy_ship.bullet_image, enemy_ship.bullet_speed, self.__enemy_bulled_cooldown, upward_or_downward = False, height = self.__heigth)
            self.__enemy_bullets_group.add(bullet)
            self.__last_time_enemy_fired = get_time

    def update_screen(self) -> bool:
        """
        Update the screen:
            -tick a number of frames in accodance with the FPS preciously set
            -updatre the position of the player ship
            -updatre the position of the enemy ships
            -updatre the position of the player bullets
            -updatre the position of the enemy bullets
            -draw all of them
            -check if an event that would cause an end to the game has occured
            -if not, update the position of every spaceship onto the screen
                then draw the screem
        """
        global victory_condition
        
        self.__clock.tick(self.__fps)

        self.__screen.blit(self.__game_background, (0,0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        
        self.__spaceship.update()

        for my_bullet in self.__my_bullets_group:
            my_bullet.update(self.__enemy_ship_group)

        for enemy_ship in self.__enemy_ship_group:
            enemy_ship.update()

        self.add_enemy_bullet()
        for enemy_bullet in self.__enemy_bullets_group:
            enemy_bullet.update(self.__ship_group)

        self.__ship_group.draw(game_master.screen)
        self.__enemy_ship_group.draw(game_master.screen)
        self.__my_bullets_group.draw(game_master.screen)
        self.__enemy_bullets_group.draw(game_master.screen)

        pygame.display.update()

        if self.__spaceship.remaining_health <= 0 or len(self.__enemy_ship_group) <= 0:
            if self.__spaceship.remaining_health <= 0:
                victory_condition = -1
            else:
                victory_condition = 1
            return False
        return True
    
    def add_ship(self, flying_object:GenericObject):
        self.__ship_group.add(flying_object)
        self.__spaceship = flying_object

    def add_enemy_ship(self, flying_object:GenericObject):
        self.__enemy_ship_group.add(flying_object)

    def add_my_bullet(self, bullet:UpwardsBullet):
        self.__my_bullets_group.add(bullet)

    @property
    def width(self):
         return self.__width
    
    @property
    def heigth(self):
         return self.__heigth
    
    @property
    def screen(self):
         return self.__screen
    
    @property
    def weapon_system(self):
        return self.__weapon_system

game_master = GameMaster(1638, 1228, 60, "Galactic Kombat", "Images/background.png")
game_master.start_display()

my_ship = MyShip(int(game_master.width / 2), game_master.heigth - 100, "Images/MySpaceShip.png", 3, game_master)
game_master.add_ship(my_ship)

keep_running = True
while keep_running:

            keep_running = game_master.update_screen() #update the screen        

if victory_condition == 1:
    game_master.screen_message("YOU WON!")
else:
    game_master.screen_message("GAME OVER")

pygame.display.flip()

done = False
while True:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            done = True
    if done == True:
        break
pygame.quit()