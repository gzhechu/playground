#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
from enum import Enum
from tkinter import Tk, Frame, Canvas, ALL, NW

BOARD_WIDTH = 720
BOARD_HEIGHT = 720
DELAY = 600
STEP = 6
SIDE = 5


ZONE_WIDTH = 12
ZONE_HEIGHT = 22

ZONE_TOP_PX = 30
ZONE_LEFT_PX = (BOARD_WIDTH-STEP*ZONE_WIDTH)/2


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

colors = ["red", "lightblue", "green", "brown",
          "yellow", "pink", "orange", "purple"]


class Direction(Enum):
    LEFT = 1
    RIGTHT = 2
    DOWN = 3


class Model():
    def __init__(self):
        self.game_zone = []
        for i in range(ZONE_HEIGHT):
            row = [9, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 9]
            self.game_zone.append(row)
        row = [9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9]
        self.game_zone.append(row)

        self.inGame = True
        self.moveX = 2
        self.moveY = 0
        self.shape_num = 0
        self.tetris_num = 0
        self.next_tetris = 1
        self.pause_move = False

    def new_tetris(self):
        self.tetris_num = self.next_tetris
        self.next_tetris = random.randint(0, 6)
        self.moveX = int(ZONE_WIDTH / 2 - 2)
        self.moveY = 0

    def collision(self, x: int, y: int, num=None):
        # print(x, y, num)
        if num is None:
            s = T[self.tetris_num][self.shape_num]
        else:
            s = T[self.tetris_num][num]
        for i in range(4):
            for j in range(4):
                if (0 != s[i][j]):
                    if (s[i][j] != s[i][j] + self.game_zone[i + y][j + x + 2]):
                        # print("collision True")
                        return True
        # print("collision False")
        return False

    def move(self, d: Direction):
        if d == Direction.LEFT:
            if not self.collision(self.moveX-1, self.moveY):
                self.moveX -= 1
                return True
        elif d == Direction.RIGTHT:
            if not self.collision(self.moveX+1, self.moveY):
                self.moveX += 1
                return True
        elif d == Direction.DOWN:
            if not self.collision(self.moveX, self.moveY+1):
                self.moveY += 1
                return True
        return False

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
        ret = False
        for i in range(2, ZONE_WIDTH + 2):
            if self.game_zone[0][i] > 0:
                ret = True
                break
        return ret

    def save(self):
        x = self.moveX
        y = self.moveY
        s = T[self.tetris_num][self.shape_num]
        for i in range(4):
            for j in range(4):
                if 0 != s[i][j]:
                    self.game_zone[i + y][j + x + 2] = self.tetris_num + 1
        if self.overflow():
            self.inGame = False

    def melt_detect(self, n: int):
        cnt = 0
        ret = True
        for i in range(ZONE_WIDTH+4):
            if self.game_zone[n][i] > 0:
                cnt += 1
        if cnt < ZONE_WIDTH + 4:
            ret = False
        return ret

    def melt_it(self, n: int):
        for i in range(n, 0, -1):
            for j in range(ZONE_WIDTH + 4):
                self.game_zone[i][j] = self.game_zone[i - 1][j]

    def try_melt(self):
        i = ZONE_HEIGHT-1
        while i > 0:
            if self.melt_detect(i):
                print("try_melt", i, self.game_zone[i])
                self.melt_it(i)
                i += +1
            i -= 1


class GameView(Canvas):
    def __init__(self):
        super().__init__(width=BOARD_WIDTH, height=BOARD_HEIGHT,
                         background="black", highlightthickness=0)
        self.tetris = Model()
        self.init_game()
        self.pack()

    def init_game(self):
        self.score = 0
        self.nextX = 13
        self.nextY = 1
        self.color = "lightblue"
        self.next_color = "lightblue"

        self.create_objects()
        self.bind_all("<Key>", self.on_key_pressed)
        self.after(DELAY, self.on_timer)

    def create_objects(self):
        '''在画布上绘制对象'''
        self.create_text(30, 10, text="Score: {0}".format(self.score),
                         tag="score", fill="white")
        self.create_rectangle(ZONE_LEFT_PX, ZONE_TOP_PX, ZONE_LEFT_PX + ZONE_WIDTH * STEP,
                              ZONE_TOP_PX + ZONE_HEIGHT * STEP,
                              fill="#0f0f0f", width=0, tag="zone")
        self.new_tetris()

    def draw_tile(self, x, y, color, tag):
        rx = ZONE_LEFT_PX + x * STEP
        ry = ZONE_TOP_PX + y * STEP
        self.create_rectangle(rx, ry, rx + SIDE, ry + SIDE,
                              fill=color, width=0, tag=tag)

    def draw_shape(self, x, y, color, s, tag):
        for i in range(4):
            for j in range(4):
                if (0 != s[i][j]):
                    self.draw_tile(x + j, y + i, color, tag)

    def move_shape(self, save=False):
        x = self.tetris.moveX
        y = self.tetris.moveY
        s = T[self.tetris.tetris_num][self.tetris.shape_num]
        tag = "move"
        dots = self.find_withtag(tag)
        for dot in dots:
            self.delete(dot)
        if save:
            tag = "save"
        self.draw_shape(x, y, self.color, s, tag)

    def on_key_pressed(self, e):
        if not self.tetris.inGame:
            return
        key = e.keysym
        # print("pressed", key)

        PAUSE_CURSOR_KEY = ["p", "P"]
        if key in PAUSE_CURSOR_KEY:
            self.tetris.pause_move = not self.tetris.pause_move
            print("pause_move", self.pause_move)

        LEFT_CURSOR_KEY = ["Left", "s", "S"]
        if key in LEFT_CURSOR_KEY and self.tetris.move(Direction.LEFT):
            self.move_shape()

        RIGHT_CURSOR_KEY = ["Right", "f", "F"]
        if key in RIGHT_CURSOR_KEY and self.tetris.move(Direction.RIGTHT):
            self.move_shape()

        DOWN_CURSOR_KEY = ["Down", "d", "D"]
        if key in DOWN_CURSOR_KEY and self.tetris.move(Direction.DOWN):
            self.move_shape()

        UP_CURSOR_KEY = ["Up", "j", "J", "e", "E"]
        if key in UP_CURSOR_KEY and self.tetris.rotate():
            self.move_shape()

        ESCAPE_CURSOR_KEY = "Escape"
        if key == ESCAPE_CURSOR_KEY:
            self.game_over()

        SPACE_CURSOR_KEY = "space"
        if key == SPACE_CURSOR_KEY:
            while self.tetris.move(Direction.DOWN):
                self.move_shape()

    def new_tetris(self):
        print("board new_tetris ")
        self.color = self.next_color
        self.next_color = colors[random.randint(0, 100) % 8]
        self.tetris.new_tetris()
        self.draw_shape(self.tetris.moveX, self.tetris.moveY, self.color,
                        T[self.tetris.tetris_num][self.tetris.shape_num], "move")
        dots = self.find_withtag("next")
        for dot in dots:
            self.delete(dot)
        self.draw_shape(self.nextX, self.nextY, self.next_color,
                        T[self.tetris.next_tetris][0], "next")

    def melt_tile(self, n):
        tag = "save"
        tiles = self.find_withtag(tag)
        print("melt_tile", n, len(tiles))
        for tile in tiles:
            c = self.coords(tile)
            if c[1] == n*STEP+ZONE_TOP_PX:
                self.delete(tile)
            if c[1] < n*STEP+ZONE_TOP_PX:
                self.move(tile, 0, STEP)

    def try_melt(self):
        i = ZONE_HEIGHT-1
        while i > 0:
            if self.tetris.melt_detect(i):
                print("try_melt", i, self.tetris.game_zone[i])
                self.tetris.melt_it(i)
                self.melt_tile(i)
                self.score += 1
                i += +1
            i -= 1

    def on_timer(self):
        # print("on_timer", self.color, self.next_color, self.tetris.next_tetris)
        self.draw_score()
        if self.tetris.inGame:
            if not self.tetris.pause_move:
                if self.tetris.collision(self.tetris.moveX, self.tetris.moveY+1):
                    self.move_shape(save=True)
                    self.tetris.save()
                    self.try_melt()
                    self.new_tetris()
                else:
                    self.tetris.moveY += 1
                    self.move_shape()
            self.after(DELAY, self.on_timer)
        else:
            self.game_over()

    def draw_score(self):
        '''记分牌'''
        score = self.find_withtag("score")
        self.itemconfigure(score, text="score: {0}".format(self.score))

    def game_over(self):
        '''删除画布上的所有信息，并显示游戏结束'''
        self.tetris.inGame = False
        self.delete(ALL)
        self.create_text(self.winfo_width() / 2, self.winfo_height()/2,
                         text="Game Over with score {0}".format(self.score), fill="white")
        self.after(1000, self._quit)

    def _quit(self):
        self.quit()


class TetrisGame(Frame):
    def __init__(self):
        super().__init__()
        self.master.title('TETRIS - 俄罗斯方块大作战')
        self.board = GameView()
        self.pack()


def main():
    root = Tk()
    nib = TetrisGame()
    root.mainloop()


if __name__ == '__main__':
    main()
