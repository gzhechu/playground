#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import copy
import math
from enum import Enum
from tkinter import Tk, Frame, Canvas, ALL

BOARD_WIDTH = 720
BOARD_HEIGHT = 720
DELAY = 1
STEP = 30
SIDE = 28

ZONE_WIDTH = 12
ZONE_HEIGHT = 22
NEXT_X = 14
NEXT_Y = 1

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


class TetrisModel():
    def __init__(self, w: int, h: int):
        if w < 8:
            raise(Exception("game zone width less then 8"))
        if h < 8:
            raise(Exception("game zone height less then 8"))
        self.width = w
        self.height = h
        self.game_zone = []
        for i in range(self.height):
            row = [9, 9]
            for w in range(self.width):
                row.append(0)
            row.extend([9, 9])
            self.game_zone.append(row)
        row = []
        for w in range(self.width+4):
            row.append(9)
        self.game_zone.append(row)

        self.in_game = True
        self.moveX = 2
        self.moveY = 0
        self.shape_num = 0
        self.tetris_num = 0
        self.next_tetris = 1
        self.pause_move = False

    def new_tetris(self):
        self.tetris_num = self.next_tetris
        self.next_tetris = random.randint(0, len(T)-1)

        answer = self.solve()  # 尝试解题
        # print(answer)
        self.moveX = answer[1]
        self.shape_num = answer[3]
        # self.moveX = int(self.width / 2 - 2)
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
        ret = False
        for i in range(2, self.width + 2):
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
            self.in_game = False

    def melt_detect(self, n: int):
        cnt = 0
        ret = True
        for i in range(self.width + 4):
            if self.game_zone[n][i] > 0:
                cnt += 1
        if cnt < self.width + 4:
            ret = False
        return ret

    def melt_it(self, n: int):
        for i in range(n, 0, -1):
            for j in range(self.width + 4):
                self.game_zone[i][j] = self.game_zone[i - 1][j]

    def try_melt(self):
        i = self.height - 1
        while i > 0:
            if self.melt_detect(i):
                # print("try_melt", i, self.game_zone[i])
                self.melt_it(i)
                i += +1
            i -= 1

    def evaluate1(self):
        """评价函数，评价游戏区域的分值，用于搜索最优解答"""
        # 01 垂直检测空心悬空的列
        # 02 计算留空的区块数，一般在消融后计算计算
        # 03 检测堆积的高度以及分布
        solid = self.width
        space = 0
        for x in range(self.width):
            mark = 0
            cnt = 0
            clearance = True
            for y in range(self.height):
                if self.game_zone[y][x + 2] > 0:
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
        solid = self.width
        space = 0
        holes = 0
        for x in range(self.width):
            mark = 0
            cnt = 0
            clearance = True
            for y in range(self.height):
                if self.game_zone[y][x + 2] > 0:
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
        solid = self.width
        space = 0
        holes = 0
        for x in range(self.width):
            mark = 0
            cnt = 0
            clearance = True
            for y in range(self.height):
                if self.game_zone[y][x + 2] > 0:
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
        solid = self.width
        space = 0
        holes = 0
        hangs = 0  # 悬空
        narrow = 0  # 窄
        narrow_mark = 0
        for y in range(self.height):
            if y >= narrow_mark + 4 and narrow_mark != 0:
                break
            for x in range(self.width):
                if self.game_zone[y][x + 2] > 0:
                    # print(x, y)
                    pass
                else:
                    if (self.game_zone[y][x + 1] > 0) and (self.game_zone[y][x + 3] > 0):
                        # print("narrow", x, y)
                        narrow += 1
                        if narrow_mark == 0:
                            narrow_mark = y

        for x in range(self.width):
            mark = 0
            cnt = 0
            hang = 0
            clearance = True
            for y in range(self.height):
                if self.game_zone[y][x + 2] > 0:
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
                    pass
                else:
                    # space += 1
                    pass
            if cnt == 0:  # 本列没有方块，不用计算。
                continue
            if cnt != self.height - mark:
                solid -= 1
            holes += self.height - mark - cnt  # 洞

        hollow = 12 - solid
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
        # print("x {} y {} i {} solid {} space {} y1 {} y2 {} holes {} hangs {} narrow {}".format(
        #     self.moveX, self.moveY, self.shape_num, solid, space, y1, y2, holes, hangs, narrow))
        return [space + (y1 + y2)*6 - holes*12 - hangs - narrow*2, self.moveX, self.moveY, self.shape_num, holes, hangs, narrow]

    def solve(self):
        x = -2
        y = 0
        idx = 0
        possible = []
        for x in range(-2, 11, 1):
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

        # print("length possible {}".format(len(possible)))

        answers = []
        for xyz in possible:
            x = xyz[0]
            y = xyz[1]
            idx = xyz[2]
            t = copy.deepcopy(self)
            t.moveX = x
            t.moveY = y
            t.shape_num = idx
            t.save()
            t.try_melt()
            r = t.evaluate4()  # 评价函数
            answers.append(r)

        # for r in answers:
        #     print(r)
        answers = sorted(answers, key=lambda x: x[0], reverse=True)
        solve = answers[0]
        print("0", answers[0])
        print("1", answers[1])
        print("2", answers[2])
        return solve


class GameView(Canvas):
    def __init__(self, w=BOARD_WIDTH, h=BOARD_HEIGHT):
        super().__init__(width=w, height=h,
                         background="black", highlightthickness=0)
        self.nextX = NEXT_X
        self.nextY = NEXT_Y

        self.create_text(90, 90, text="Score: 0", tag="score",
                         fill="white", font=("Arial", 25), justify='center')
        self.create_text(90, 160, text="X: 0",
                         tag="xxx", fill="white", font=("Arial", 20), justify='center')
        self.create_text(90, 200, text="Y: 0",
                         tag="yyy", fill="white", font=("Arial", 20), justify='center')
        self.create_text(90, 240, text="T: 0",
                         tag="ttt", fill="white", font=("Arial", 20), justify='center')
        self.create_text(90, 280, text="I: 0",
                         tag="iii", fill="white", font=("Arial", 20), justify='center')
        self.create_rectangle(ZONE_LEFT_PX, ZONE_TOP_PX, ZONE_LEFT_PX + ZONE_WIDTH * STEP,
                              ZONE_TOP_PX + ZONE_HEIGHT * STEP,
                              fill="#1f1f1f", width=0, tag="zone")
        self.pack()

    def draw_tile(self, x, y, color, tag):
        rx = ZONE_LEFT_PX + x * STEP
        ry = ZONE_TOP_PX + y * STEP
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
                if (0 != shape[i][j]):
                    self.draw_tile(x + j, y + i, color, tag)

    def melt_tile(self, n):
        tag = "save"
        tiles = self.find_withtag(tag)
        # print("melt_tile", n, len(tiles))
        for tile in tiles:
            c = self.coords(tile)
            if c[1] == n*STEP+ZONE_TOP_PX:
                self.delete(tile)
            if c[1] < n*STEP+ZONE_TOP_PX:
                self.move(tile, 0, STEP)

    def draw_score(self, s, x, y, t, i):
        score = self.find_withtag("score")
        self.itemconfigure(score, text="Score: {0}".format(s))
        xxx = self.find_withtag("xxx")
        self.itemconfigure(xxx, text="X: {}".format(x+2))
        yyy = self.find_withtag("yyy")
        self.itemconfigure(yyy, text="Y: {}".format(y))
        ttt = self.find_withtag("ttt")
        self.itemconfigure(ttt, text="T: {}".format(t))
        iii = self.find_withtag("iii")
        self.itemconfigure(iii, text="I: {}".format(i))

    def game_over(self, score):
        '''删除画布上的所有信息，并显示游戏结束'''
        self.tetris.in_game = False
        self.delete(ALL)
        self.create_text(self.winfo_width() / 2, self.winfo_height()/2,
                         text="Game Over with score {0}".format(score), fill="white")


class GameController():
    def __init__(self, model, view):
        self._model = model
        self._view = view
        self.next_color = "lightblue"
        self.color = self.next_color
        self.score = 0
        self.nextX = 13
        self.nextY = 1
        self.new_tetris()

    def update(self, save=False):
        if save:
            self._view.redraw_shape(self._model.moveX, self._model.moveY, self.color,
                                    T[self._model.tetris_num][self._model.shape_num], "move", save=True)
        else:
            self._view.redraw_shape(self._model.moveX, self._model.moveY, self.color,
                                    T[self._model.tetris_num][self._model.shape_num], "move")
        self._view.draw_score(self.score, self._model.moveX,
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
            if not self._model.pause_move:
                if self._model.move(Direction.DOWN):
                    self.update()
                    pass
                else:
                    self.update(save=True)
                    self._model.save()
                    # print("evaluate")
                    # self._model.evaluate()  # 评估得分
                    self.try_melt()
                    self.new_tetris()
            self._view.after(DELAY, self.on_timer)
        else:
            self.game_over()

    def new_tetris(self):
        self.color = self.next_color
        self.next_color = colors[random.randint(0, 100) % 8]
        self._model.new_tetris()
        self._view.redraw_shape(self._model.moveX, self._model.moveY, self.color,
                                T[self._model.tetris_num][self._model.shape_num], "move")
        self._view.redraw_shape(self.nextX, self.nextY, self.next_color,
                                T[self._model.next_tetris][0], "next")

    def try_melt(self):
        i = ZONE_HEIGHT-1
        while i > 0:
            if self._model.melt_detect(i):
                # print("try_melt", i, self._model.game_zone[i])
                self._model.melt_it(i)
                self._view.melt_tile(i)
                self.score += 1
                i += +1
            i -= 1

    def game_over(self):
        self._model.in_game = False
        self._view.delete(ALL)
        self._view.create_text(self._view.winfo_width() / 2, self._view.winfo_height()/2,
                               text="Game Over with score {0}".format(self.score), fill="white")
        self._view.after(1000, self._quit)

    def _quit(self):
        self._view.quit()


class TetrisGame(Frame):
    def __init__(self):
        super().__init__()
        self.master.title('TETRIS - 俄罗斯方块大作战')
        m = TetrisModel(ZONE_WIDTH, ZONE_HEIGHT)
        v = GameView()
        c = GameController(m, v)
        v.bind_all("<Key>", c.on_key_pressed)
        v.after(DELAY, c.on_timer)
        self.board = v
        self.pack()


def main():
    root = Tk()
    nib = TetrisGame()
    root.mainloop()


if __name__ == '__main__':
    main()
