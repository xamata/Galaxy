import random
from kivy.config import Config

Config.set("graphics", "width", "900")
Config.set("graphics", "height", "400")
# KIVY.CONFIG must be placed before any other import to set the window's size

from kivy import platform
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, Clock, ObjectProperty, StringProperty
from kivy.graphics import *
from kivy.core.window import Window
from kivy.graphics.vertex_instructions import Quad
from kivy.uix.relativelayout import RelativeLayout
from kivy.lang.builder import Builder
from kivy.core.audio import SoundLoader

Builder.load_file("menu.kv")


class MainWidget(RelativeLayout):
    from transforms import transform, transform_2D, transform_perspective
    from user_actions import (
        on_keyboard_down,
        on_keyboard_up,
        on_touch_down,
        on_touch_up,
        keyboard_closed,
    )

    # creates the menu widget that allows menu screen to be turned off
    menu_widget = ObjectProperty()
    perspective_point_x = NumericProperty(0)
    # used later in a function
    # creates a numericproperty within kivy to be called
    perspective_point_y = NumericProperty(0)

    V_NB_LINES = 8  # number of verical lines we have, must be odd # to keep symmetry
    V_LINES_SPACING = 0.2  # 10 of screen width so it's adaptable to each screen
    # line = None  # create this variable to save position of the line
    # changed from line=None to list vertical_lines, bc multiple lines
    vertical_lines = []

    # number of horizontal lines we have, must be odd # to keep symmetry
    H_NB_LINES = 10
    H_LINES_SPACING = 0.2  # 10 of screen height so it's adaptable to each screen
    horizontal_lines = []

    # var that stores how far the horiz line(up and down) has traveled from original pos
    current_offset_y = 0
    # speed of the current_offset_y
    SPEED = 0.8
    # get the position of the whole gameboard
    current_y_loop = 0

    # var that stores the offset of the grid(left to right or right to left)
    current_offset_x = 0
    SPEED_X = 2  # speed of current_offset_x

    current_speed_x = 0
    # change one tile to many tiles:
    # tile = None
    # ti_x = 0
    # ti_y = 2
    NB_TILES = 16
    tiles = []
    tiles_coordinates = []

    SHIP_WIDTH = 0.1
    SHIP_HEIGHT = 0.035
    SHIP_BASE_Y = 0.04
    ship = None
    ship_coordinates = [(0, 0), (0, 0), (0, 0)]

    state_game_over = False
    state_game_has_started = False

    # String property allows .kv to update accordingly
    menu_title = StringProperty("G   A   L   A   X   Y")
    menu_button_title = StringProperty("START")

    score_txt = StringProperty("SCORE: 0")

    sound_begin = None
    sound_galaxy = None
    sound_gameover_impact = None
    sound_gameover_voice = None
    sound_music1 = None
    sound_restart = None

    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        self.init_audio()
        # grabs the size of the widget and displays it
        # print("INIT W: " + str(self.width) + " H:" + str(self.height))
        # if not called here, the function init_vetical_lines() will not run
        self.init_vertical_lines()
        self.init_horizontal_lines()
        self.init_tiles()
        self.init_ship()
        # resets the game variables/functions
        self.reset_game()

        if self.is_desktop():
            # KEYBOARD extension, from stack overflow
            self._keyboard = Window.request_keyboard(self.keyboard_closed, self)
            self._keyboard.bind(on_key_down=self.on_keyboard_down)
            self._keyboard.bind(on_key_up=self.on_keyboard_up)

        # clock that updates the game, should be at the end so that everything else is intialized
        Clock.schedule_interval(self.update, 1.0 / 60.0)

    def init_audio(self):
        self.sound_begin = SoundLoader.load("audio/begin.wav")
        self.sound_galaxy = SoundLoader.load("audio/galaxy.wav")
        self.sound_gameover_impact = SoundLoader.load("audio/gameover_impact.wav")
        self.sound_gameover_voice = SoundLoader.load("audio/gameover_voice.wav")
        self.sound_music1 = SoundLoader.load("audio/music1.wav")
        self.sound_restart = SoundLoader.load("audio/restart.wav")

        self.sound_music1.volume = 1
        self.sound_begin.volume = 0.25
        self.sound_galaxy.volume = 0.25
        self.sound_gameover_impact.volume = 0.6
        self.sound_gameover_voice.volume = 0.25
        self.sound_restart.volume = 0.25

    def reset_game(self):
        # resets all the variables for the new game
        self.score_txt = "SCORE: 0"
        self.current_offset_y = 0
        self.current_y_loop = 0
        self.current_offset_x = 0
        self.current_speed_x = 0
        self.tiles_coordinates = []
        self.pre_fill_tiles_coordinates()
        self.generate_tiles_coordinates()

        # means the game has started
        self.state_game_over = False

    # configures keyboard if we are on desktop, if not turns keybaord
    def is_desktop(self):
        if platform in ("linux", "win", "macosx"):
            return True
        return False

    def init_ship(self):
        with self.canvas:
            Color(0, 0, 0)
            self.ship = Triangle()

    def update_ship(self):
        center_x = self.width / 2
        base_y = self.SHIP_BASE_Y * self.height
        ship_half_width = self.SHIP_WIDTH * self.width / 2
        ship_height = self.SHIP_HEIGHT * self.height
        #    2    How the ship looks
        # 1     3
        # call self.transform
        # get the coordinates before the transform, not after. after is just for display
        self.ship_coordinates[0] = (center_x - ship_half_width, base_y)
        self.ship_coordinates[1] = (center_x, base_y + ship_height)
        self.ship_coordinates[2] = (center_x + ship_half_width, base_y)

        # COOL PYTHON TIP: the star expands the tuple, so that the function now sees the 1argument as 2
        x1, y1 = self.transform(*self.ship_coordinates[0])
        x2, y2 = self.transform(*self.ship_coordinates[1])
        x3, y3 = self.transform(*self.ship_coordinates[2])

        self.ship.points = [x1, y1, x2, y2, x3, y3]

    # function that checks if ship is on the track, false = game over
    def check_ship_collision(self):
        # loops only some of the tile_coordinates bc ship is always at the bottom of screen
        for i in range(0, len(self.tiles_coordinates)):
            # variables that pull out the current tile coords
            ti_x, ti_y = self.tiles_coordinates[i]
            # avoid extra work bc once the tile is greater than tile loop, we can assume the first two tiles were false
            # '+1' is there bc we only want to test the first two tiles(coming from the bottom)
            if ti_y > self.current_y_loop + 1:
                return False
            if self.check_ship_collision_with_tile(ti_x, ti_y):
                return True
        return False

    # func that checks if ship collides with tile
    # True means that the ship is inside the tile
    # False means that the ship is not colliding with the tile, not inside the tile
    def check_ship_collision_with_tile(self, ti_x, ti_y):
        xmin, ymin = self.get_tile_coordinates(ti_x, ti_y)
        xmax, ymax = self.get_tile_coordinates(ti_x + 1, ti_y + 1)
        # checks if ship coords are inside self.get_tile_coords()
        for i in range(0, 3):
            px, py = self.ship_coordinates[i]
            # check if point is colliding with tile
            if xmin <= px <= xmax and ymin <= py <= ymax:  # px >= xmin and px<= xmax
                return True
        return False

    def init_tiles(self):
        with self.canvas:
            Color(1, 1, 1)
            for i in range(0, self.NB_TILES):
                self.tiles.append(Quad())

    # creates 10 tiles to start the level, easier for user
    def pre_fill_tiles_coordinates(self):
        straight_x = 0
        for i in range(10):
            self.tiles_coordinates.append((straight_x, i))
            print("tiles: " + str(self.tiles_coordinates))

    # create tiles to be placed in tiles_coordinates list
    def generate_tiles_coordinates(self):
        last_x = 0
        last_y = 0

        # clean the coordinates that are out of the screen
        # ti_y < self.curent_y_loop
        # START FROM THE END, so steps backwards and ends at -1 to reach 0
        for i in range(len(self.tiles_coordinates) - 1, -1, -1):
            if self.tiles_coordinates[i][1] < self.current_y_loop:
                del self.tiles_coordinates[i]

        if len(self.tiles_coordinates) > 0:
            last_coordinates = self.tiles_coordinates[-1]
            # we don't need the +1 bc we keep the same x, and 0 to get x-coordinate
            last_x = last_coordinates[0]
            last_y = last_coordinates[1] + 1
        print("foo1")

        # start from the # of elements i.e. self.tiles_coordinates to start from where the last tile ended
        for i in range(len(self.tiles_coordinates), self.NB_TILES):
            # generate a random value for tile positions
            r = random.randint(0, 2)
            # copied from update_horizontal_lines()
            start_index = -int(self.V_NB_LINES / 2) + 1  # -(8/2) + 1 = -3
            end_index = start_index + self.V_NB_LINES - 2  # -3 + 8 = 5 -1 = 4
            # -3 -2 -1 0 1 2 3 4
            if last_x <= start_index:
                print("set r=1")
                r = 1
            if last_x >= end_index:
                print("set r = 2")
                r = 2
            # 0 -> straight
            # 1 -> tile that goes to the right
            # 2 -> tile that goes to the left
            # coordinates (0,1), (0,2)...(0,self.NB_Tiles-1)
            self.tiles_coordinates.append((last_x, last_y))
            if r == 1:
                last_x += 1
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))
            if r == 2:
                last_x -= 1
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))

            last_y += 1
        print("foo2")

    def init_vertical_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            # self.line = Line(points=[100, 0, 100, 100])
            for i in range(0, self.V_NB_LINES):  # for 7 lines, list will append(Line())
                self.vertical_lines.append(Line())

    def get_line_x_from_index(self, index):
        # we change from int(self.width / 2) bc although they are both center, perspective_point_x allows us to change the position of the perspective_point_x in the future
        central_line_x = self.perspective_point_x
        spacing = self.V_LINES_SPACING * self.width
        # offset takes into account that each vertical line is 0.5 from perspective_point_
        # 4:00:00 of Johnathan's Kivy Course
        offset = index - 0.5
        line_x = central_line_x + offset * spacing + self.current_offset_x
        return line_x

    def get_line_y_from_index(self, index):
        spacing_y = self.H_LINES_SPACING * self.height
        line_y = index * spacing_y - self.current_offset_y
        return line_y

    def get_tile_coordinates(self, ti_x, ti_y):
        # for every loop(that 1 horiz reaches 0,0 coord), the tile changes with it
        ti_y = ti_y - self.current_y_loop

        x = self.get_line_x_from_index(ti_x)
        y = self.get_line_y_from_index(ti_y)
        return x, y

    # create the tiles that acts as the playing field
    def update_tiles(self):
        for i in range(0, self.NB_TILES):
            tile = self.tiles[i]
            tile_coordinates = self.tiles_coordinates[i]
            # creates the coordinates so that the tile knows where it belongs
            # Quad takes in coordinates of 4 corners, 4:08:00
            xmin, ymin = self.get_tile_coordinates(
                tile_coordinates[0], tile_coordinates[1]
            )
            xmax, ymax = self.get_tile_coordinates(
                tile_coordinates[0] + 1, tile_coordinates[1] + 1
            )

            # Quad Demo:
            # 2     3
            #
            # 1     4
            x1, y1 = self.transform(xmin, ymin)
            x2, y2 = self.transform(xmin, ymax)
            x3, y3 = self.transform(xmax, ymax)
            x4, y4 = self.transform(xmax, ymin)

            tile.points = [x1, y1, x2, y2, x3, y3, x4, y4]

    # we need this function to move the vertical line to the center. if we tried to center it inside
    # init_vertical_lines() then we'd only get the center of the widget to the left
    # if we tried to center it using the on_size, say plugging init_vertical_lines() inside of the
    # on_size(), then it will create many instances as the window moves around
    def update_vertical_lines(self):
        # we need lines to be EX1: -1 0 1 2
        # range will start from arbitrary location index, not 0.
        # If we have 4 lines like EX1 we need to start at -1
        start_index = -int(self.V_NB_LINES / 2) + 1
        # range must be so that -1 0 1 2 are all accounted for: start_index + numberOfVertLines
        # range(-1, [4-1] = 3) -> range(-1,3) -> (-1,0,1,2)
        for i in range(start_index, start_index + self.V_NB_LINES):
            # if no int, the coordinates will be float numbers, causing a slight disruption in each line
            # line_x important, grabs the central_line_x=center of window, adds it by it's offset, and
            # multiples it by the desired spacing of the lines
            line_x = self.get_line_x_from_index(i)

            # create x1, y1, x2, y2 so that they can be manipulated in the future
            # line_x determines the where the line will be
            # coordiantes are set equal to the original coordiantes(line_x) passed through the
            # transfrom_perspective() which is then called by transform() which calls transform_2D()

            x1, y1 = self.transform(line_x, 0)
            x2, y2 = self.transform(line_x, self.height)
            self.vertical_lines[i].points = [x1, y1, x2, y2]

            # each line is drawn to the top of the window
            # self.vertical_lines[i].points = [line_x, 0, line_x, self.height]

    def init_horizontal_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            for i in range(0, self.H_NB_LINES):  # for 7 lines, list will append(Line())
                self.horizontal_lines.append(Line())

    def update_horizontal_lines(self):
        # copied from update_vertical_lines(), gives line totally on the left
        start_index = -int(self.V_NB_LINES / 2) + 1
        # -1_index + 4_lines = 3 -> -1,0,1,2 so -1 , give line totally on the right
        end_index = start_index + self.V_NB_LINES - 1

        xmin = self.get_line_x_from_index(start_index)
        xmax = self.get_line_x_from_index(end_index)

        for i in range(0, self.H_NB_LINES):

            # horizontal lines depends on the height of the lines
            # self.current_offset_y subtracted to the equation below to shift the game screen
            line_y = self.get_line_y_from_index(i)
            # line_y = i * spacing_y  # number of lines multiplied by height of window
            x1, y1 = self.transform(xmin, line_y)
            x2, y2 = self.transform(xmax, line_y)
            self.horizontal_lines[i].points = [x1, y1, x2, y2]

    def update(self, dt):
        # checks the deltatime , multiply by 60 makes it around 1
        # print('dt: ' + str(dt*60) + ' - 1/60: ' + str(1.0/60.0))
        # print('update')

        time_factor = dt * 60
        self.update_vertical_lines()
        self.update_horizontal_lines()
        self.update_tiles()
        self.update_ship()

        # shifts the lines from top to bottom
        # speed_y makes it so when the window adjusts, the speed will stay the same
        if not self.state_game_over and self.state_game_has_started:
            speed_y = self.SPEED * self.height / 100
            self.current_offset_y += speed_y * time_factor

            spacing_y = self.H_LINES_SPACING * self.height
            # bc our timefactor is related to dt, if our speed of the game is faster than what dt is starting up at, /
            # check_ship_collision() would be checking tiles that aren't even there yet, giving us a game over.
            # so instead of putting 'if' , we put 'while'
            while self.current_offset_y >= spacing_y:
                self.current_offset_y -= spacing_y
                self.current_y_loop += 1
                # displays the score of the game
                self.score_txt = "SCORE: " + str(self.current_y_loop)
                self.generate_tiles_coordinates()
                print("Loop: " + str(self.current_y_loop))

            # shifts the lines from left to right
            # OLD: self.current_offset_x += self.SPEED_X * time_factor
            # NEW:
            # speed_x makes it so when the window adjusts, the speed will stay the same
            speed_x = self.current_speed_x * self.width / 100
            self.current_offset_x += speed_x * time_factor

        # spacing_x = self.V_LINES_SPACING * self.width
        # if self.current_offset_x >= spacing_x:
        #     self.current_offset_x -= spacing_x

        if not self.check_ship_collision() and not self.state_game_over:
            # audio
            self.sound_gameover_impact.play()
            self.sound_music1.stop()
            Clock.schedule_once(self.play_gameover_voice_sound, 1.5)

            self.state_game_over = True
            self.menu_title = "G  A  M  E    O  V  E  R"
            self.menu_button_title = "RESTART"
            # Turns on Menu Screen so the game can be replayed
            self.menu_widget.opacity = 1
            print("Game Over!")

    def play_gameover_voice_sound(self, dt):
        if self.state_game_over:
            self.sound_gameover_voice.play()

    def on_menu_button_pressed(self):
        # audio
        if self.state_game_over:
            self.sound_restart.play()
        else:
            self.sound_begin.play()
        self.sound_music1.play()

        print("Button")
        # resets the game
        self.reset_game()
        self.state_game_has_started = True
        # Turns off menu screen so the game can be played
        self.menu_widget.opacity = 0


class GalaxyApp(App):
    def __init__(self, **kwargs):
        super(GalaxyApp, self).__init__(**kwargs)


def main():
    GalaxyApp().run()


if __name__ == "__main__":
    main()


"""
This is the transform perspective that 'laid down' the 2D perspective, RIGHT BEFORE we adjust the 
size of the horizontal boxes 3:20:00 into the video
# shows the game in a transformed perspective
    def transform_perspective(self, x, y):
        # create the transformation_perspective
        # @ y=self.height, perspective point is lin_y
        lin_y = y * self.perspective_point_y / self.height
        # check if point is greater than perspective point and change it to stay in bounds
        if lin_y > self.perspective_point_y:
            lin_y = self.perspective_point_y

        diff_x = x-self.perspective_point_x
        diff_y = self.perspective_point_y - lin_y
        # 1 when diff_y == self.perspective_point_y / 0 when diff_y = 0
        factor_y = diff_y / self.perspective_point_y

        tr_x = self.perspective_point_x + diff_x * factor_y

        # always return int coordinates bc float causes shakiness
        return int(tr_x), int(lin_y)



        ============SOME MORE REMOVAL====================

    def on_parent(self, widget, parent):
        # print("ON PARENT: " + str(self.width) + " H:" + str(self.height))
        pass

    def on_size(self, *args):
        # on_size obtains the actual size of the window
        # print("ON SIZE: " + str(self.width) + " H:" + str(self.height))
        # COMMENT: changes the perpective_point_x to width(of window)/2
        # self.perspective_point_x = self.width/2
        # COMMENT: changes the perspective_point_y to height(of window) * 0.75
        # self.perspective_point_y = self.height * 0.75

        # COMMENT: Moved these two functions to the clock method so that they can be updated with the game
        # COMMENT CONT: Allows for board shifting, creating a game moving effect
        # self.update_vertical_lines()
        # self.update_horizontal_lines()
        pass

    def on_perspective_point_x(self, widget, value):
        # print("PX: " + str(value))  # prints perspective_point_x
        pass

    def on_perspective_point_y(self, widget, value):
        # print("PY: " + str(value))  # prints perspective_point_y
        pass
"""
"""
# CHANGED AFTER get_line_x_from_index() FUCNTION:
def update_vertical_lines(self):
    # center_x changed to central_line_x so we can establish
    # that the central line is in the middle and we need 3 lines on the left and 3 on the right
    central_line_x = int(self.width / 2)

    # create the spacing between the lines, we have V_LINES_SPACING already but we need
    # adaptive to the screen size so
    spacing = self.V_LINES_SPACING * self.width

    # create an offset that will be negative, this applies to the line position,
    # it will start at 'line negative 3' then using "offset +=1" it will go to
    # 'line negative 2' and so on till the last line is filled in (line 7)
    # +0.5 moves line from center to offcenter
    offset = -int(self.V_NB_LINES / 2) + 0.5

    # coordinates (x0,y0,x1,y1)
    # notice that this calls from self.line = Line(points=[coordinates]), list is changed
    # self.line.points = [center_x, 0, center_x, 100]
    for i in range(0, self.V_NB_LINES):
        # if no int, the coordinates will be float numbers, causing a slight disruption in each line
        # line_x important, grabs the central_line_x=center of window, adds it by it's offset, and
        # multiples it by the desired spacing of the lines
        line_x = int(central_line_x + offset * spacing + self.current_offset_x)

        # create x1, y1, x2, y2 so that they can be manipulated in the future
        # line_x determines the where the line will be
        # coordiantes are set equal to the original coordiantes(line_x) passed through the
        # transfrom_perspective() which is then called by transform() which calls transform_2D()

        x1, y1 = self.transform(line_x, 0)
        x2, y2 = self.transform(line_x, self.height)
        self.vertical_lines[i].points = [x1, y1, x2, y2]

        # each line is drawn to the top of the window
        # self.vertical_lines[i].points = [line_x, 0, line_x, self.height]

        # offset creates the spacing betwen the lines
        offset += 1

def update_horizontal_lines(self):
        central_line_x = int(self.width / 2)
        spacing = self.V_LINES_SPACING * self.width
        offset = -int(self.V_NB_LINES / 2) + 0.5

        # creates a line at xmin, using offset and spacing required between each line
        # offset is negative so when adding it, it will go to the left
        xmin = central_line_x + offset * spacing + self.current_offset_x
        # self.current_offset_x added to move the horizontal lines left or right
        # this workds by shifting the position of the horizontal lines, their coordinatates
        xmax = central_line_x - offset * spacing + self.current_offset_x
        spacing_y = self.H_LINES_SPACING * self.height

        for i in range(0, self.H_NB_LINES):

            # horizontal lines depends on the height of the lines
            # self.current_offset_y subtracted to the equation below to shift the game screen
            line_y = i * spacing_y - self.current_offset_y
            # line_y = i * spacing_y  # number of lines multiplied by height of window
            x1, y1 = self.transform(xmin, line_y)
            x2, y2 = self.transform(xmax, line_y)
            self.horizontal_lines[i].points = [x1, y1, x2, y2]
"""

