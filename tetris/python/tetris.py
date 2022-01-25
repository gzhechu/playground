#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# to gain maximum speed, try pypy3.
#

import math
import time
import random
import sys
import getopt
from datetime import datetime
from enum import Enum
from tkinter import Tk, Frame, Canvas

STEP = 19  # pixel, how many pixel each step moves.
SIDE = 17  # pixel, side length of square
BOARD_WIDTH = BOARD_HEIGHT = STEP * 24  # game window size
DELAY = 300  # micro second
AI_DELAY = 5  # micro second

GRID_WIDTH = 10  # num
GRID_HEIGHT = 20  #

GRID_TOP = STEP*2  # pixel, position of grid.
GRID_LEFT = (BOARD_WIDTH-STEP*GRID_WIDTH)/2  # pixel


T = []
T.append([{"shape": [1, 1, 1, 1], "width": 1, "height": 4},  # I
          {"shape": [15], "width": 4, "height": 1}])
T.append([{"shape": [2, 7], "width": 3, "height": 2},  # T
          {"shape": [2, 3, 2], "width": 2, "height": 3},
          {"shape": [7, 2], "width": 3, "height": 2},
          {"shape": [1, 3, 1], "width": 2, "height": 3}])
T.append([{"shape": [3, 3], "width": 2, "height": 2}])  # O
T.append([{"shape": [2, 2, 3], "width": 2, "height": 3},  # L
          {"shape": [7, 4], "width": 3, "height": 2},
          {"shape": [3, 1, 1], "width": 2, "height": 3},
          {"shape": [1, 7], "width": 3, "height": 2}])
T.append([{"shape": [7, 1], "width": 3, "height": 2},  # J
          {"shape": [1, 1, 3], "width": 2, "height": 3},
          {"shape": [4, 7], "width": 3, "height": 2},
          {"shape": [3, 2, 2], "width": 2, "height": 3}])
T.append([{"shape": [6, 3], "width": 3, "height": 2},  # Z
          {"shape": [1, 3, 2], "width": 2, "height": 3}])
T.append([{"shape": [3, 6], "width": 3, "height": 2},  # S
          {"shape": [2, 3, 1], "width": 2, "height": 3}])
# print("length of T:", len(T))

COLORS = ["red", "lightblue", "green", "brown",
          "yellow", "pink", "orange", "purple"]


class Direction(Enum):
    LEFT = 1
    RIGHT = 2
    DOWN = 3


class TetrisRandom(object):
    def __init__(self):
        self.pool = []

    @classmethod
    def instance(cls, *args, **kwargs):
        if not hasattr(TetrisRandom, "_instance"):
            TetrisRandom._instance = TetrisRandom(*args, **kwargs)
        return TetrisRandom._instance

    def next(self):
        if len(self.pool) <= 0:
            self.pool = [* range(7)] * 7
            random.shuffle(self.pool)
        return self.pool.pop()


class TetrisModel():
    def __init__(self, w: int, h: int):
        # print(w, h)
        if w < 8:
            raise(Exception("game grid width less then 8"))
        if h < 8:
            raise(Exception("game grid height less then 8"))
        self.count = 0
        self.width = w
        self.height = h
        self.grid = []
        for i in range(self.height):
            self.grid.append(0)

        self.in_game = True
        self.moveX = 3
        self.moveY = 0
        self.shape_idx = 0
        self.next_tetris = 5
        self.pause_move = False
        self.new_tetris()

    def new_tetris(self):
        self.count += 1
        self.tetris_idx = self.next_tetris
        self.shape_idx = 0
        # self.next_tetris = random.randint(0, 6)
        # self.next_tetris = math.floor(random.SystemRandom().random() * 7)
        # self.next_tetris = self.count % 7
        # self.next_tetris = 5
        self.next_tetris = TetrisRandom.instance().next()
        self.moveX = int(self.width / 2 - 1)
        self.moveY = 0

    def collided(self, x: int, y: int, num: int = None):
        if x < 0:
            return True
        # print("collided:", self.tetris_idx, x, y, num)
        if num is None:
            s = T[self.tetris_idx][self.shape_idx]
        else:
            s = T[self.tetris_idx][num]

        if x > self.width - s["width"]:
            return True
        if y > self.height - s["height"]:
            return True

        for h in range(s["height"]):
            if (s["shape"][h] << x) & self.grid[y+h] != 0:
                return True
        return False

    def move(self, d: Direction):
        ret = False
        if d == Direction.LEFT:
            if not self.collided(self.moveX-1, self.moveY):
                self.moveX -= 1
                ret = True
        elif d == Direction.RIGHT:
            if not self.collided(self.moveX+1, self.moveY):
                self.moveX += 1
                ret = True
        elif d == Direction.DOWN:
            if not self.collided(self.moveX, self.moveY+1):
                self.moveY += 1
                ret = True
        return ret

    def rotate(self):
        rotate = False
        s = T[self.tetris_idx]
        if self.shape_idx >= len(s) - 1:
            if not self.collided(self.moveX, self.moveY, 0):
                self.shape_idx = 0
                rotate = True
        elif not self.collided(self.moveX, self.moveY, self.shape_idx+1):
            self.shape_idx += 1
            rotate = True
        return rotate

    def save(self):
        x = self.moveX
        y = self.moveY
        s = T[self.tetris_idx][self.shape_idx]
        for h in range(s["height"]):
            self.grid[h + y] = self.grid[h + y] | (s["shape"][h] << x)

        if self.grid[0] > 0:
            self.in_game = False

    def try_melt(self):
        melted = []
        h = self.height - 1
        while h > 0:
            if 1 << self.width <= self.grid[h] + 1:
                # print("try_melt", h, grid[h])
                melted.append(h)
                for y in range(h, 0, -1):
                    self.grid[y] = self.grid[y - 1]
                h += +1
            h -= 1
        return melted

    def evaluate(self, grid, try_x, try_y, try_num):
        """ Impletment of Pierre Dellacherie's AI algorithm (El-Tetris) """
        LandingHeight = 0
        RowTransitions = 0
        ColumnTransitions = 0
        NumberOfHoles = 0
        WellSums = 0

        melted = 0
        h = self.height - 1
        while h > 0:
            if 1 << self.width <= grid[h] + 1:
                # print("try_melt", h, grid[h])
                melted += 1
                for y in range(h, 0, -1):
                    grid[y] = grid[y - 1]
                h += +1
            h -= 1

        # row transtion
        for y in range(self.height):
            last_cell = 1
            for x in range(self.width):
                cell = (grid[y] >> x) & 1
                if last_cell != cell:
                    RowTransitions += 1
                last_cell = cell
            if cell == 0:
                RowTransitions += 1

        for x in range(self.width):
            mark = 0
            col_cells = 0
            wells = 0
            last_cell = 0
            for y in range(self.height):
                # column transtion
                cell = (grid[y] >> x) & 1
                # print(x, y, last_cell, cell, ColumnTransitions)
                if last_cell != cell:
                    ColumnTransitions += 1
                last_cell = cell

                # wells
                # print(x, y, cell, )
                if x == 0:
                    if cell == 0 and (grid[y] >> 1 & 1) == 1:
                        wells += 1
                    elif wells > 0:
                        WellSums += (1+wells)*wells/2  # Gaussian quadrature
                        wells = 0
                    if y >= self.height-1:
                        WellSums += (1+wells)*wells/2  #
                        wells = 0
                elif x == self.width - 1:
                    if cell == 0 and (grid[y] >> x-1 & 1) == 1:
                        wells += 1
                    elif wells > 0:
                        WellSums += (1+wells)*wells/2  #
                        wells = 0
                    if y >= self.height-1:
                        WellSums += (1+wells)*wells/2  #
                        wells = 0
                else:
                    if cell == 0 and (grid[y] >> x-1 & 1) == 1 and (grid[y] >> x+1 & 1) == 1:
                        wells += 1
                    elif wells > 0:
                        WellSums += (1+wells)*wells/2  #
                        wells = 0
                    if y >= self.height-1:
                        WellSums += (1+wells)*wells/2  #
                        wells = 0

                if cell == 1:
                    col_cells += 1
                    if mark == 0:
                        mark = y

            if col_cells > 0:
                NumberOfHoles += (self.height - mark - col_cells)
            if last_cell == 0:
                ColumnTransitions += 1
            # print(x, ColumnTransitions, NumberOfHoles, WellSums)

        s = T[self.tetris_idx][try_num]
        lh = 20 - (try_y + s["height"])
        LandingHeight = lh + (s["height"]-1)/2

        score = (-4.500158825082766 * LandingHeight +
                 3.4181268101392694 * melted +
                 -3.2178882868487753 * RowTransitions +
                 -9.348695305445199 * ColumnTransitions +
                 -7.899265427351652 * NumberOfHoles +
                 -3.3855972247263626 * WellSums)
        return [score, try_x, try_y, try_num,
                (self.count, lh, s["height"], LandingHeight, melted, RowTransitions,
                 ColumnTransitions, NumberOfHoles, WellSums)]

    def solve(self):
        t = T[self.tetris_idx]
        answer = [-1000000, ]
        for idx in range(len(t)):
            s = t[idx]
            for x in range(self.width-s["width"]+1):
                y = 0
                while y <= self.height - s["height"]:
                    collided = False
                    for h in range(s["height"]):
                        if (s["shape"][h] << x) & self.grid[y+h] != 0:
                            collided = True
                            break
                    if not collided:
                        y += 1
                    else:
                        break
                y -= 1

                g = [*self.grid]
                for h in range(s["height"]):
                    g[h + y] = g[h + y] | (s["shape"][h] << x)
                r = self.evaluate(g, x, y, idx)
                # print(r)
                if r[0] > answer[0]:
                    answer = r
        return answer


class GameView(Canvas):
    def __init__(self, w=BOARD_WIDTH, h=BOARD_HEIGHT):
        super().__init__(width=w, height=h,
                         background="black", highlightthickness=0)
        self.create_text(SIDE*4, SIDE*3, text="01:23:45", tag="time",
                         fill="white", font=("Arial", 5+SIDE//2), justify='center')
        self.create_text(SIDE*4, SIDE*5, text="Score: 0", tag="score",
                         fill="white", font=("Arial", 5+SIDE//2), justify='center')
        self.create_text(SIDE*4, SIDE*7, text="X: 0",
                         tag="xxx", fill="white", font=("Arial", 3+STEP//2), justify='center')
        self.create_text(SIDE*4, SIDE*8, text="Y: 0",
                         tag="yyy", fill="white", font=("Arial", 3+STEP//2), justify='center')
        self.create_text(SIDE*4, SIDE*9, text="T: 0",
                         tag="ttt", fill="white", font=("Arial", 3+STEP//2), justify='center')
        self.create_text(SIDE*4, SIDE*10, text="I: 0",
                         tag="iii", fill="white", font=("Arial", 3+STEP//2), justify='center')
        self.create_rectangle(GRID_LEFT, GRID_TOP, GRID_LEFT + GRID_WIDTH * STEP,
                              GRID_TOP + GRID_HEIGHT * STEP,
                              fill="#1f1f1f", width=0, tag="grid")
        self.create_text(GRID_LEFT + SIDE*(GRID_WIDTH+1)/2, SIDE*10, text="",
                         tag="hardcore", fill="red", font=("Arial", 6+STEP//2), justify='center')
        self.pack()

    def draw_tile(self, x, y, color, tag):
        rx = GRID_LEFT + x * STEP
        ry = GRID_TOP + y * STEP
        self.create_rectangle(rx, ry, rx + SIDE, ry + SIDE,
                              fill=color, width=0, tag=tag)

    def redraw_shape(self, x, y, color, shape, tag, save=False):
        dots = self.find_withtag(tag)
        for dot in dots:
            self.delete(dot)
        if save:
            tag = "save"
        for h in range(shape["height"]):
            for w in range(shape["width"]):
                if (shape["shape"][h] >> w) & 1:
                    self.draw_tile(x + w, y + h, color, tag)

    def melt_tile(self, n):
        tag = "save"
        tiles = self.find_withtag(tag)
        # print("melt_tile", n, len(tiles))
        for tile in tiles:
            c = self.coords(tile)
            if c[1] == n*STEP+GRID_TOP:
                self.delete(tile)
            if c[1] < n*STEP+GRID_TOP:
                self.move(tile, 0, STEP)

    def draw_score(self, dt, s, x, y, t, i, h=False):
        tm = self.find_withtag("time")
        self.itemconfigure(tm, text=dt)
        score = self.find_withtag("score")
        self.itemconfigure(score, text="Score: {0}".format(s))
        xxx = self.find_withtag("xxx")
        self.itemconfigure(xxx, text="X: {}".format(x))
        yyy = self.find_withtag("yyy")
        self.itemconfigure(yyy, text="Y: {}".format(y))
        ttt = self.find_withtag("ttt")
        self.itemconfigure(ttt, text="T: {}".format(t))
        iii = self.find_withtag("iii")
        self.itemconfigure(iii, text="I: {}".format(i))
        hardcore = self.find_withtag("hardcore")
        if h:
            self.itemconfigure(hardcore, text="HARDCORE MODE")
        else:
            self.itemconfigure(hardcore, text="")

    def redraw_hardcore(self, color, m: TetrisModel):
        tag = "move"
        dots = self.find_withtag(tag)
        for dot in dots:
            self.delete(dot)
        tag = "save"
        dots = self.find_withtag(tag)
        for dot in dots:
            self.delete(dot)
        for h in range(m.height):
            for w in range(m.width):
                if (m.grid[h] >> w) & 1:
                    self.draw_tile(w, h, color, tag)

    def game_over(self, score):
        self.create_rectangle(STEP*5, self.winfo_height()/2-STEP*3,
                              self.winfo_width()-STEP*5,
                              self.winfo_height()/2+STEP,
                              fill="#2f2f2f", width=1, tag="gameover")

        self.create_text(self.winfo_width() / 2, self.winfo_height()/2-STEP,
                         text="Game Over with Score {0}.".format(score), fill="white",
                         font=("Arial", 5+STEP//2))


class GameController():
    def __init__(self, model, view, ai=False):
        self.model = model
        self.view = view
        self.ai = ai
        self.hardcore = False
        self.next_color = "lightblue"
        self.color = self.next_color
        self.score = 0
        self.nextX = self.model.width + 1
        self.nextY = 1
        self.start = datetime.now()
        self.dt = "0:00:00"
        self.new_tetris()

    def update(self, save=False):
        s = T[self.model.tetris_idx][self.model.shape_idx]
        self.view.redraw_shape(self.model.moveX, self.model.moveY, self.color,
                               s, "move", save)
        self.view.draw_score(self.dt, self.score, self.model.moveX,
                             self.model.moveY, self.model.tetris_idx, self.model.shape_idx)

    def draw_hardcore(self):
        self.view.redraw_hardcore("green2", self.model)
        self.next_color = COLORS[random.randint(0, 7)]
        self.view.redraw_shape(self.nextX, self.nextY, self.next_color,
                               T[self.model.next_tetris][0], "next")
        self.view.draw_score(self.dt, self.score, self.model.moveX,
                             self.model.moveY, self.model.tetris_idx, self.model.shape_idx, True)

    def on_key_pressed(self, e):
        if not self.model.in_game:
            return
        key = e.keysym
        # print("pressed", key)
        ESCAPE_KEY = "Escape"
        AI_KEY = ["a", "A"]
        HARDCORE_KEY = ["h", "H"]
        PAUSE_KEY = ["p", "P"]
        LEFT_CURSOR_KEY = ["Left", "s", "S"]
        RIGHT_CURSOR_KEY = ["Right", "f", "F"]
        DOWN_CURSOR_KEY = ["Down", "d", "D"]
        UP_CURSOR_KEY = ["Up", "j", "J", "e", "E"]
        SPACE_KEY = "space"

        if key in PAUSE_KEY:
            self.model.pause_move = not self.model.pause_move
        if key in LEFT_CURSOR_KEY and self.model.move(Direction.LEFT):
            self.update()
        if key in RIGHT_CURSOR_KEY and self.model.move(Direction.RIGHT):
            self.update()
        if key in DOWN_CURSOR_KEY and self.model.move(Direction.DOWN):
            self.update()
        if key in UP_CURSOR_KEY and self.model.rotate():
            self.update()
        if key in AI_KEY:
            self.ai = not self.ai
        if key in HARDCORE_KEY:
            self.hardcore = not self.hardcore
        if key == ESCAPE_KEY:
            # self.game_over()
            sys.exit(0)
        if key == SPACE_KEY:
            while self.model.move(Direction.DOWN):
                self.update()

    def on_timer(self):
        if self.hardcore:
            ts = int(time.time())
            while self.model.in_game:
                answer = self.model.solve()  # 尝试解题
                self.model.moveX = answer[1]
                self.model.moveY = answer[2]
                self.model.shape_idx = answer[3]
                self.model.save()
                melted = self.model.try_melt()
                self.score += len(melted)
                self.model.new_tetris()
                if int(time.time()) != ts:
                    self.dt = str(datetime.now() - self.start).split(".")[0]
                    print(self.dt, "score:", self.score, answer)
                    self.draw_hardcore()
                    self.view.after(AI_DELAY, self.on_timer)
                    break
            if not self.model.in_game:
                self.game_over()

        elif self.model.in_game:
            self.dt = str(datetime.now() - self.start).split(".")[0]
            if not self.model.pause_move:
                if self.model.move(Direction.DOWN):
                    self.update()
                else:
                    self.update(save=True)
                    self.model.save()
                    self.try_melt()
                    self.new_tetris()
            if self.ai:
                self.view.after(AI_DELAY, self.on_timer)
            else:
                self.view.after(DELAY, self.on_timer)
        else:
            self.game_over()

    def new_tetris(self):
        self.color = self.next_color
        self.next_color = COLORS[random.randint(0, 7)]
        self.model.new_tetris()
        self.view.redraw_shape(self.model.moveX, self.model.moveY, self.color,
                               T[self.model.tetris_idx][self.model.shape_idx], "move")
        self.view.redraw_shape(self.nextX, self.nextY, self.next_color,
                               T[self.model.next_tetris][0], "next")
        if self.ai:  # 自动执行
            answer = self.model.solve()  # 尝试解题
            self.model.moveX = answer[1]
            self.model.shape_idx = answer[3]
            print(self.dt, "score:", self.score,
                  self.model.tetris_idx, answer)

    def try_melt(self):
        melted = self.model.try_melt()
        self.score += len(melted)
        for h in melted:
            self.view.melt_tile(h)

    def game_over(self):
        self.model.in_game = False
        self.view.game_over(self.score)


class TetrisGame(Frame):
    def __init__(self, ai=False):
        super().__init__()
        self.master.title('TETRIS - 俄罗斯方块AI大作战')
        model = TetrisModel(GRID_WIDTH, GRID_HEIGHT)
        view = GameView()
        controller = GameController(model, view, ai)
        view.bind_all("<Key>", controller.on_key_pressed)
        view.after(DELAY, controller.on_timer)
        self.board = view
        self.pack()


def main(ai=False):
    root = Tk()
    TetrisGame(ai)
    root.mainloop()


def verify(count=None):
    # 验证模式，无GUI界面动画
    score = 0
    start = datetime.now()
    m = TetrisModel(GRID_WIDTH, GRID_HEIGHT)
    while m.in_game:
        dt = str(datetime.now() - start).split(".")[0]
        m.new_tetris()
        answer = m.solve()  # 尝试解题
        m.moveX = answer[1]
        m.moveY = answer[2]
        m.shape_idx = answer[3]
        m.save()
        melted = m.try_melt()
        score += len(melted)
        if m.count % 5000 == 0:
            print(dt, "score:", score, answer)
        if count and score >= count:
            print(dt, "score:", score, answer)
            break


if __name__ == '__main__':
    opts, args = getopt.getopt(
        sys.argv[1:], '-v-a', ['verify', 'auto'])
    for opt_name, opt_value in opts:
        if opt_name in ('-v', '--verify'):
            verify()
            sys.exit()
        if opt_name in ('-a', '--auto'):
            main(ai=True)
            sys.exit()
    main()
