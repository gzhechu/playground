#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import sys
import os
import getopt
from datetime import datetime
from enum import Enum
from tkinter import Tk, Frame, Canvas

STEP = 19  # pixel
SIDE = 17  #
BOARD_WIDTH = BOARD_HEIGHT = STEP * 24  #
DELAY = 300  # micro second

GRID_WIDTH = 10  # num
GRID_HEIGHT = 20  #

GRID_TOP = STEP*2  # pixel
GRID_LEFT = (BOARD_WIDTH-STEP*GRID_WIDTH)/2  # pixel


T = []
T.append([{"shape": [3, 3], "width": 2, "height": 2}])  # O
T.append([{"shape": [3, 6], "width": 3, "height": 2},  # S
          {"shape": [2, 3, 1], "width": 2, "height": 3}])
T.append([{"shape": [6, 3], "width": 3, "height": 2},  # Z
          {"shape": [1, 3, 2], "width": 2, "height": 3}])
T.append([{"shape": [1, 1, 3], "width": 2, "height": 3},  # J
          {"shape": [4, 7], "width": 3, "height": 2},
          {"shape": [3, 2, 2], "width": 2, "height": 3},
          {"shape": [7, 1], "width": 3, "height": 2}])
T.append([{"shape": [2, 2, 3], "width": 2, "height": 3},  # L
          {"shape": [1, 7], "width": 3, "height": 2},
          {"shape": [3, 1, 1], "width": 2, "height": 3},
          {"shape": [7, 4], "width": 3, "height": 2}])
T.append([{"shape": [2, 7], "width": 3, "height": 2},  # T
          {"shape": [2, 3, 2], "width": 2, "height": 3},
          {"shape": [7, 2], "width": 3, "height": 2},
          {"shape": [1, 3, 1], "width": 2, "height": 3}])
T.append([{"shape": [1, 1, 1, 1], "width": 1, "height": 4},  # I
          {"shape": [15], "width": 4, "height": 1}])
print("length of T:", len(T))

COLORS = ["red", "lightblue", "green", "brown",
          "yellow", "pink", "orange", "purple"]


class Direction(Enum):
    LEFT = 1
    RIGTHT = 2
    DOWN = 3


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
        self.shape_num = 0
        self.tetris_num = 0
        self.next_tetris = 5
        self.pause_move = False

    def new_tetris(self):
        self.count += 1
        self.tetris_num = self.next_tetris
        self.shape_num = 0
        self.next_tetris = int.from_bytes(os.urandom(
            4), byteorder='little', signed=False) % 7
        # self.next_tetris = 5
        self.moveX = int(self.width / 2 - 1)
        self.moveY = 0

    def collided(self, x: int, y: int, num=None):
        if x < 0:
            return True
        # print("collided:", self.tetris_num, x, y, num)
        if num is None:
            s = T[self.tetris_num][self.shape_num]
        else:
            s = T[self.tetris_num][num]

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
        elif d == Direction.RIGTHT:
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
        s = T[self.tetris_num]
        if self.shape_num >= len(s) - 1:
            if not self.collided(self.moveX, self.moveY, 0):
                self.shape_num = 0
                rotate = True
        elif not self.collided(self.moveX, self.moveY, self.shape_num+1):
            self.shape_num += 1
            rotate = True
        return rotate

    def save(self, grid=None, x=None, y=None, num=None):
        # print("save", grid, x, y, num)
        if not grid:
            grid = self.grid
        if not x:
            x = self.moveX
        if not y:
            y = self.moveY
        if not num:
            num = self.shape_num
        s = T[self.tetris_num][num]
        for h in range(s["height"]):
            grid[h + y] = grid[h + y] | (s["shape"][h] << x)

        if grid[0] > 0:
            self.in_game = False
        return grid

    def try_melt(self, grid=None):
        if not grid:
            grid = self.grid
        melted = []
        h = self.height - 1
        while h > 0:
            if 1 << self.width <= grid[h] + 1:
                # print("try_melt", h, grid[h])
                melted.append(h)
                for y in range(h, 0, -1):
                    grid[y] = self.grid[y - 1]
                h += +1
            h -= 1
        return melted

    def evaluate(self, grid=None, try_x=None, try_y=None, try_num=None):
        """ Impletment of Pierre Dellacherie  AI algorithm (El-Tetris) """
        if grid is None:
            grid = self.grid
        if try_x is None:
            try_x = self.moveX
        if try_y is None:
            try_y = self.moveY
        if try_num is None:
            try_num = self.shape_num

        LandingHeight = 0
        RowTransitions = 0
        ColumnTransitions = 0
        NumberOfHoles = 0
        WellSums = 0
        melted = len(self.try_melt(grid))

        # column transtion
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

        s = T[self.tetris_num][try_num]
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

    def long_solve(self):
        x = 0
        y = 0
        idx = 0
        t = T[self.tetris_num]
        possible = []
        for x in range(self.width):
            for idx in range(len(t)):
                # print("len of shape", len(t), idx)
                if self.collided(x, y, idx):  # 放不下
                    continue
                self.moveX = x
                self.moveY = y
                self.shape_num = idx
                while self.move(Direction.DOWN):
                    pass
                # print("x {} y {} i {}".format(x, self.moveY, idx))
                possible.append([x, self.moveY, idx])
        self.moveY = 0  # 恢复位置
        # print(possible)

        answer = [-1000000, ]
        for xyz in possible:
            x = xyz[0]
            y = xyz[1]
            idx = xyz[2]

            # t = copy.deepcopy(self)
            # t = pickle.loads(pickle.dumps(self, -1))
            # t.moveX = x
            # t.moveY = y
            # t.shape_num = idx
            # t.save()
            # r = t.evaluate()

            g = self.grid.copy()
            s = T[self.tetris_num][idx]
            for h in range(s["height"]):
                g[h + y] = g[h + y] | (s["shape"][h] << x)
            r = self.evaluate(g, x, y, idx)

            if r[0] > answer[0]:
                answer = r
        return answer

    def solve(self):
        t = T[self.tetris_num]
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

    def draw_score(self, dt, s, x, y, t, i):
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
        self._model = model
        self._view = view
        self.ai = ai
        self.next_color = "lightblue"
        self.color = self.next_color
        self.score = 0
        self.nextX = self._model.width + 1
        self.nextY = 1
        self.start = datetime.now()
        self.dt = "0:00:00"
        self.new_tetris()
        if self.ai:
            global DELAY
            DELAY = 1

    def update(self, save=False):
        if save:
            self._view.redraw_shape(self._model.moveX, self._model.moveY, self.color,
                                    T[self._model.tetris_num][self._model.shape_num], "move", save=True)
        else:
            self._view.redraw_shape(self._model.moveX, self._model.moveY, self.color,
                                    T[self._model.tetris_num][self._model.shape_num], "move")
        self._view.draw_score(self.dt, self.score, self._model.moveX,
                              self._model.moveY, self._model.tetris_num, self._model.shape_num)

    def on_key_pressed(self, e):
        if not self._model.in_game:
            return
        key = e.keysym
        # print("pressed", key)

        PAUSE_CURSOR_KEY = ["p", "P"]
        if key in PAUSE_CURSOR_KEY:
            self._model.pause_move = not self._model.pause_move
            # print("pause_move", self._model.pause_move)

        LEFT_CURSOR_KEY = ["Left", "s", "S"]
        if key in LEFT_CURSOR_KEY and self._model.move(Direction.LEFT):
            self.update()

        RIGHT_CURSOR_KEY = ["Right", "f", "F"]
        if key in RIGHT_CURSOR_KEY and self._model.move(Direction.RIGTHT):
            self.update()

        DOWN_CURSOR_KEY = ["Down", "d", "D"]
        if key in DOWN_CURSOR_KEY and self._model.move(Direction.DOWN):
            self.update()

        UP_CURSOR_KEY = ["Up", "j", "J", "e", "E"]
        if key in UP_CURSOR_KEY and self._model.rotate():
            self.update()

        ESCAPE_CURSOR_KEY = "Escape"
        if key == ESCAPE_CURSOR_KEY:
            # self.game_over()
            sys.exit(0)

        SPACE_CURSOR_KEY = "space"
        if key == SPACE_CURSOR_KEY:
            while self._model.move(Direction.DOWN):
                self.update()

    def on_timer(self):
        if self._model.in_game:
            self.dt = str(datetime.now() - self.start).split(".")[0]
            if not self._model.pause_move:
                if self._model.move(Direction.DOWN):
                    self.update()
                else:
                    self.update(save=True)
                    self._model.save()
                    self.try_melt()
                    self.new_tetris()

            self._view.after(DELAY, self.on_timer)
        else:
            self.game_over()

    def new_tetris(self):
        self.color = self.next_color
        self.next_color = COLORS[random.randint(0, 100) % 8]
        self._model.new_tetris()
        self._view.redraw_shape(self._model.moveX, self._model.moveY, self.color,
                                T[self._model.tetris_num][self._model.shape_num], "move")
        self._view.redraw_shape(self.nextX, self.nextY, self.next_color,
                                T[self._model.next_tetris][0], "next")
        if self.ai:  # 自动执行
            answer = self._model.solve()  # 尝试解题
            self._model.moveX = answer[1]
            self._model.shape_num = answer[3]
            print(self.dt, "score:", self.score,
                  self._model.tetris_num, answer)

    def try_melt(self):
        melted = self._model.try_melt()
        self.score += len(melted)
        for h in melted:
            self._view.melt_tile(h)

    def game_over(self):
        self._model.in_game = False
        self._view.game_over(self.score)


class TetrisGame(Frame):
    def __init__(self, ai=False):
        super().__init__()
        self.master.title('TETRIS - 俄罗斯方块大作战')
        m = TetrisModel(GRID_WIDTH, GRID_HEIGHT)
        v = GameView()
        c = GameController(m, v, ai)
        v.bind_all("<Key>", c.on_key_pressed)
        v.after(DELAY, c.on_timer)
        self.board = v
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
        m.shape_num = answer[3]
        m.save()
        melted = m.try_melt()
        score += len(melted)
        if m.count % 100 == 0:
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
