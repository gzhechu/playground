#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import copy
import pickle
import math
import sys
import os
import getopt
from datetime import datetime
from enum import Enum
from tkinter import Tk, Frame, Canvas

STEP = 28  # pixel
SIDE = 26  #
BOARD_WIDTH = BOARD_HEIGHT = STEP * 24  #
DELAY = 300  # micro second

GRID_WIDTH = 10  # num
GRID_HEIGHT = 20  #

GRID_TOP = STEP*2  # pixel
GRID_LEFT = (BOARD_WIDTH-STEP*GRID_WIDTH)/2  # pixel


T = ((((0, 1, 0, 0), (0, 1, 0, 0), (0, 1, 1, 0), (0, 0, 0, 0)),  # L
      ((0, 0, 0, 0), (0, 0, 1, 0), (1, 1, 1, 0), (0, 0, 0, 0)),
      ((1, 1, 0, 0), (0, 1, 0, 0), (0, 1, 0, 0), (0, 0, 0, 0)),
      ((0, 0, 0, 0), (1, 1, 1, 0), (1, 0, 0, 0), (0, 0, 0, 0))),
     (((0, 1, 1, 0), (0, 1, 1, 0), (0, 0, 0, 0), (0, 0, 0, 0)),  # O
      ((0, 1, 1, 0), (0, 1, 1, 0), (0, 0, 0, 0), (0, 0, 0, 0)),
      ((0, 1, 1, 0), (0, 1, 1, 0), (0, 0, 0, 0), (0, 0, 0, 0)),
      ((0, 1, 1, 0), (0, 1, 1, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
     (((0, 0, 1, 0), (0, 0, 1, 0), (0, 1, 1, 0), (0, 0, 0, 0)),  # J
      ((0, 0, 0, 0), (1, 1, 1, 0), (0, 0, 1, 0), (0, 0, 0, 0)),
      ((0, 1, 1, 0), (0, 1, 0, 0), (0, 1, 0, 0), (0, 0, 0, 0)),
      ((0, 0, 0, 0), (1, 0, 0, 0), (1, 1, 1, 0), (0, 0, 0, 0))),
     (((0, 0, 0, 0), (1, 1, 0, 0), (0, 1, 1, 0), (0, 0, 0, 0)),  # Z
      ((0, 1, 0, 0), (1, 1, 0, 0), (1, 0, 0, 0), (0, 0, 0, 0)),
      ((0, 0, 0, 0), (1, 1, 0, 0), (0, 1, 1, 0), (0, 0, 0, 0)),
      ((0, 1, 0, 0), (1, 1, 0, 0), (1, 0, 0, 0), (0, 0, 0, 0))),
     (((0, 0, 0, 0), (0, 1, 1, 0), (1, 1, 0, 0), (0, 0, 0, 0)),  # S
      ((1, 0, 0, 0), (1, 1, 0, 0), (0, 1, 0, 0), (0, 0, 0, 0)),
      ((0, 0, 0, 0), (0, 1, 1, 0), (1, 1, 0, 0), (0, 0, 0, 0)),
      ((1, 0, 0, 0), (1, 1, 0, 0), (0, 1, 0, 0), (0, 0, 0, 0))),
     (((0, 1, 0, 0), (0, 1, 0, 0), (0, 1, 0, 0), (0, 1, 0, 0)),  # I
      ((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (1, 1, 1, 1)),
      ((0, 0, 1, 0), (0, 0, 1, 0), (0, 0, 1, 0), (0, 0, 1, 0)),
      ((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (1, 1, 1, 1))),
     (((0, 0, 0, 0), (0, 1, 0, 0), (1, 1, 1, 0), (0, 0, 0, 0)),  # T
      ((0, 1, 0, 0), (1, 1, 0, 0), (0, 1, 0, 0), (0, 0, 0, 0)),
      ((0, 0, 0, 0), (1, 1, 1, 0), (0, 1, 0, 0), (0, 0, 0, 0)),
      ((0, 1, 0, 0), (0, 1, 1, 0), (0, 1, 0, 0), (0, 0, 0, 0))))

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
            row = [1, 1]
            for _ in range(self.width):
                row.append(0)
            row.extend([1, 1])
            self.grid.append(row)
        row = []
        for _ in range(self.width+4):
            row.append(1)
        self.grid.append(row)

        self.in_game = True
        self.moveX = 2
        self.moveY = 0
        self.shape_num = 0
        self.tetris_num = 0
        self.next_tetris = 6
        self.pause_move = False

    def new_tetris(self):
        self.count += 1
        self.tetris_num = self.next_tetris
        # self.next_tetris = 6
        self.next_tetris = int.from_bytes(os.urandom(
            4), byteorder='little', signed=False) % 7
        self.moveX = int(self.width / 2 - 2)
        self.moveY = 0

    def collision(self, x: int, y: int, num=None):
        # print(x, y, num)
        if num is None:
            s = T[self.tetris_num][self.shape_num]
        else:
            s = T[self.tetris_num][num]
        for i in range(4):
            for j in range(4):
                if 0 != s[i][j]:
                    # print(i, j, x, y, i+y, j+x+2)
                    if self.grid[i + y][j + x + 2] != 0:
                        # print("collision True")
                        return True
        return False

    def move(self, d: Direction):
        ret = False
        if d == Direction.LEFT:
            if not self.collision(self.moveX-1, self.moveY):
                self.moveX -= 1
                ret = True
        elif d == Direction.RIGTHT:
            if not self.collision(self.moveX+1, self.moveY):
                self.moveX += 1
                ret = True
        elif d == Direction.DOWN:
            if not self.collision(self.moveX, self.moveY+1):
                self.moveY += 1
                ret = True
        # print("x={}, y={}".format(self.moveX, self.moveY))
        return ret

    def rotate(self):
        rotate = False
        if self.shape_num >= 3:
            if not self.collision(self.moveX, self.moveY, 0):
                self.shape_num = 0
                rotate = True
        elif not self.collision(self.moveX, self.moveY, self.shape_num+1):
            self.shape_num += 1
            rotate = True
        return rotate

    def overflow(self):
        if sum(self.grid[0]) > 4:
            return True
        return False

    def save(self):
        x = self.moveX
        y = self.moveY
        s = T[self.tetris_num][self.shape_num]
        for i in range(4):
            for j in range(4):
                if 0 != s[i][j]:
                    self.grid[i + y][j + x + 2] = 1
        if self.overflow():
            self.in_game = False

    def melt_detect(self, n: int):
        cnt = sum(self.grid[n])
        if cnt < self.width + 4:
            return False
        return True

    def melt_it(self, n: int):
        for i in range(n, 0, -1):
            for j in range(self.width + 4):
                self.grid[i][j] = self.grid[i - 1][j]

    def try_melt(self):
        melted = 0
        i = self.height - 1
        while i > 0:
            if self.melt_detect(i):
                # print("try_melt", i, self.grid[i])
                self.melt_it(i)
                i += +1
                melted += 1
            i -= 1
        return melted

    def evaluate1(self):
        """评价函数，评价游戏区域的分值，用于搜索最优解答"""
        # 01 垂直检测空心悬空的列
        # 02 计算留空的区块数，一般在消融后计算计算
        # 03 检测堆积的高度以及分布
        self.try_melt()
        solid = self.width
        space = 0
        for x in range(self.width):
            mark = 0
            cnt = 0
            clearance = True
            for y in range(self.height):
                if self.grid[y][x + 2] > 0:
                    clearance = False
                    cnt += 1
                    if mark == 0:
                        mark = y
                if clearance:
                    space += 1
                else:
                    continue
            if cnt == 0:  # 本列没有方块，不用计算。
                continue
            if cnt != self.height - mark:
                solid -= 1
        aspect = 1  # 高宽比
        w = [0, 0, 0, 0]
        h = [0, 0, 0, 0]
        y1 = y2 = self.moveY  # 找到最低点
        s = T[self.tetris_num][self.shape_num]
        for i in range(4):
            cnt = 0
            for j in range(4):
                if 0 != s[i][j]:
                    cnt += 1
                    w[j] = 1
                    h[i] = 1
            if cnt == 0:
                y1 += 1
            else:
                y2 += cnt
        aspect = math.ceil(sum(w)/sum(h))
        # print("x {} y {} i {} solid {} space {} y1 {} y2 {}".format(
        #     self.moveX, self.moveY, self.shape_num, solid, space, y1, y2))
        # return [solid * 100 + y, self.moveX, self.moveY, self.shape_num]
        return [space + y1 + y2 + aspect, self.moveX, self.moveY, self.shape_num]

    def evaluate2(self):
        """评价函数"""
        self.try_melt()
        solid = self.width
        space = 0
        holes = 0
        for x in range(self.width):
            mark = 0
            cnt = 0
            clearance = True
            for y in range(self.height):
                if self.grid[y][x + 2] > 0:
                    clearance = False
                    cnt += 1
                    if mark == 0:
                        mark = y
                if clearance:
                    space += 1
                else:
                    continue
            if cnt == 0:  # 本列没有方块，不用计算。
                continue
            if cnt != self.height - mark:
                solid -= 1
            holes += self.height - mark - cnt  # 洞
        aspect = 1  # 高宽比
        w = [0, 0, 0, 0]
        h = [0, 0, 0, 0]
        y1 = y2 = self.moveY  # 最低点
        s = T[self.tetris_num][self.shape_num]
        for i in range(4):
            cnt = 0
            for j in range(4):
                if 0 != s[i][j]:
                    w[j] = 1
                    h[i] = 1
                    cnt += 1
            if cnt == 0:
                y1 += 1
            else:
                y2 += cnt
        aspect = math.ceil(sum(w)/sum(h))
        # 评价系数
        return [space + y1 + y2 - holes*12, self.moveX, self.moveY, self.shape_num]

    def evaluate3(self):
        """评价函数"""
        self.try_melt()
        solid = self.width
        space = 0
        holes = 0
        for x in range(self.width):
            mark = 0
            cnt = 0
            clearance = True
            for y in range(self.height):
                if self.grid[y][x + 2] > 0:
                    clearance = False
                    cnt += 1
                    if mark == 0:
                        mark = y
                if clearance:
                    space += 1
                else:
                    continue
            if cnt == 0:  # 本列没有方块，不用计算。
                continue
            if cnt != self.height - mark:
                solid -= 1
            holes += self.height - mark - cnt  # 洞
        aspect = 1  # 高宽比
        w = [0, 0, 0, 0]
        h = [0, 0, 0, 0]
        y1 = y2 = self.moveY  # 最低点
        s = T[self.tetris_num][self.shape_num]
        for i in range(4):
            cnt = 0
            for j in range(4):
                if 0 != s[i][j]:
                    w[j] = 1
                    h[i] = 1
                    cnt += 1
            if cnt == 0:
                y1 += 1
            else:
                y2 += cnt
        aspect = math.ceil(sum(w)/sum(h))
        # 评价系数
        return [space + y1 + y2 + aspect - holes*5, self.moveX, self.moveY, self.shape_num]
        # return [solid * 100000 + space * 100 + y1 + y2, self.moveX, self.moveY, self.shape_num]

    def evaluate4(self):
        """评价函数"""
        self.try_melt()
        solid = self.width
        space = 0
        holes = 0
        hangs = 0  # 悬空
        narrow = 0  # 窄
        for y in range(self.moveY, self.height):
            if y > self.moveY + 4:
                continue
            for x in range(self.width):
                if self.grid[y][x + 2] == 0:
                    if (self.grid[y][x + 1] > 0) and (self.grid[y][x + 3] > 0):
                        # print("narrow", x, y)
                        narrow += 1

        for x in range(self.width):
            mark = 0
            cnt = 0
            hang = 0
            clearance = True
            for y in range(self.height):
                if self.grid[y][x + 2] > 0:
                    clearance = False
                    cnt += 1
                    hang += 1
                    if mark == 0:
                        mark = y
                else:
                    if not clearance:
                        hangs += hang
                        hang = 0
                if clearance:
                    space += 1

            if cnt == 0:  # 本列没有方块，不用计算。
                continue
            if cnt != self.height - mark:
                solid -= 1
            holes += self.height - mark - cnt  # 洞

        y1 = y2 = self.moveY  # 最低点
        s = T[self.tetris_num][self.shape_num]
        for i in range(4):
            cnt = 0
            for j in range(4):
                if 0 != s[i][j]:
                    cnt += 1
            if cnt == 0:
                y1 += 1
            else:
                y2 += cnt

        # 评价系数
        # print("x {} y {} i {} solid {} space {} y1 {} y2 {} holes {} hangs {} narrow {}".format(
        #     self.moveX, self.moveY, self.shape_num, solid, space, y1, y2, holes, hangs, narrow))
        return [space + (y1 + y2)*6 - holes*12 - hangs - narrow*4, self.moveX, self.moveY, self.shape_num, holes, hangs, narrow]

    def evaluate5(self):
        """评价函数"""
        melted = self.try_melt()
        holes = 0
        hangs = 0  # 悬空
        narrow = 0  # 窄
        for y in range(self.moveY, self.height):
            if y > self.moveY + 4:
                continue
            for x in range(self.width):
                if self.grid[y][x + 2] == 0:
                    if (self.grid[y][x + 1] > 0) and (self.grid[y][x + 3] > 0):
                        # print("narrow", x, y)
                        narrow += 1

        for x in range(self.width):
            mark = 0
            cnt = 0
            hang = 0
            clearance = True
            for y in range(self.height):
                if self.grid[y][x + 2] > 0:
                    clearance = False
                    cnt += 1
                    hang += 1
                    if mark == 0:
                        mark = y
                else:
                    if not clearance:
                        hangs += hang
                        hang = 0
            if cnt == 0:  # 本列没有方块，不用计算。
                continue
            holes += self.height - mark - cnt  # 洞

        y1 = y2 = self.moveY  # 最低点
        # s = T[self.tetris_num][self.shape_num]
        # for i in range(4):
        #     cnt = 0
        #     for j in range(4):
        #         if 0 != s[i][j]:
        #             cnt += 1
        #     if cnt == 0:
        #         y1 += 1
        #     else:
        #         y2 += cnt

        # 评价系数
        point = melted + (y1 + y2)*self.width//2 - holes * \
            self.width - hangs - narrow*self.width/5
        return [point, self.moveX, self.moveY, self.shape_num, (melted, holes, hangs, narrow), (y1, y2)]

    def PierreDellacherie(self):
        melted = self.try_melt()

        LandingHeight = 0
        RowTransitions = 0
        ColumnTransitions = 0
        NumberOfHoles = 0
        WellSums = 0

        for y in range(self.height):
            last_cell = 1
            for x in range(self.width + 1):
                cell = self.grid[y][x + 2]
                if last_cell != cell:
                    RowTransitions += 1
                last_cell = cell

        for x in range(self.width):
            mark = 0
            cnt = -1
            wells = 0
            well_height = 0
            last_cell = 1
            for y in range(self.height+1):
                cell = self.grid[20 - y][x + 2]  # from bottom on
                if last_cell != cell:
                    ColumnTransitions += 1
                last_cell = cell

                if self.grid[y][x + 2] > 0:
                    cnt += 1
                    if mark == 0:
                        mark = y

                if self.grid[y][x + 2] == 0 and (self.grid[y][x + 1] > 0) and (self.grid[y][x + 3] > 0):
                    wells += 1
                    well_height += 1
                elif wells > 0:
                    WellSums += (1+wells)*well_height/2  # 高斯求和
                    wells = 0
                    well_height = 0

            if cnt > 0:
                NumberOfHoles += self.height - mark - cnt  # 洞

        h = [0, 0, 0, 0]
        s = T[self.tetris_num][self.shape_num]
        for i in range(4):
            for j in range(4):
                if 0 != s[i][j]:
                    h[i] = 1

        hc = sum(h)     # height of shape
        he = 0          # empty height at bottom
        while h[3-he] <= 0:
            he += 1

        lh = 20 - (self.moveY+4) + he
        LandingHeight = lh + (hc-1)/2

        score = (-4.500158825082766 * LandingHeight +
                 3.4181268101392694 * melted +
                 -3.2178882868487753 * RowTransitions +
                 -9.348695305445199 * ColumnTransitions +
                 -7.899265427351652 * NumberOfHoles +
                 -3.3855972247263626 * WellSums)
        return [score, self.moveX, self.moveY, self.shape_num,
                (self.count, LandingHeight, melted, RowTransitions,
                 ColumnTransitions, NumberOfHoles, WellSums)]

    def solve(self):
        x = -2
        y = 0
        idx = 0
        possible = []
        for x in range(-2, self.width, 1):
            for idx in range(4):
                if self.collision(x, y, idx):  # 放不下
                    continue
                self.moveX = x
                self.moveY = y
                self.shape_num = idx
                while self.move(Direction.DOWN):
                    pass
                # print("x {} y {} i {}".format(x, self.moveY, idx))
                possible.append([x, self.moveY, idx])
        self.moveY = 0  # 恢复位置

        answer = [-1000000, ]
        for xyz in possible:
            x = xyz[0]
            y = xyz[1]
            idx = xyz[2]

            # t = copy.deepcopy(self)
            t = pickle.loads(pickle.dumps(self, -1))
            t.moveX = x
            t.moveY = y
            t.shape_num = idx
            t.save()
            # r = t.evaluate5()  # 评价函数
            r = t.PierreDellacherie()
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
        for i in range(4):
            for j in range(4):
                if 0 != shape[i][j]:
                    self.draw_tile(x + j, y + i, color, tag)

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
        self.new_tetris()
        self.dt = ""
        if self.ai:
            global DELAY
            DELAY = 3

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
            self.game_over()

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
                    if self.ai:  # 自动执行
                        answer = self._model.solve()  # 尝试解题
                        self._model.moveX = answer[1]
                        self._model.shape_num = answer[3]
                        print(self.dt, "score:", self.score,
                              self._model.tetris_num, answer)

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

    def try_melt(self):
        i = GRID_HEIGHT-1
        while i > 0:
            if self._model.melt_detect(i):
                # print("try_melt", i, self._model.grid[i])
                self._model.melt_it(i)
                self._view.melt_tile(i)
                self.score += 1
                i += 1
            i -= 1

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


def verify():
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
        i = GRID_HEIGHT-1
        while i > 0:
            if m.melt_detect(i):
                m.melt_it(i)
                score += 1
                i += 1
            i -= 1
        print(dt, "score:", score, m.tetris_num, answer)


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
