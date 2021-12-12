#!/usr/bin/env python3

import random
from tkinter import Tk, Frame, Canvas, ALL, NW

BOARD_WIDTH = 500
BOARD_HEIGHT = 500
DELAY = 100
STEP = 10
NODE_SIZE = 8


class Board(Canvas):
    def __init__(self):
        super().__init__(width=BOARD_WIDTH, height=BOARD_HEIGHT,
                         background="black", highlightthickness=0)
        self.init_game()
        self.pack()

    def init_game(self):
        '''初始化游戏数据'''
        self.inGame = True
        self.score = 0

        # 移动贪吃蛇的参数
        self.moveX = STEP
        self.moveY = 0

        # 初始的苹果坐标
        self.appleX = 100
        self.appleY = 190

        self.create_objects()
        self.draw_apple()
        self.bind_all("<Key>", self.on_key_pressed)
        self.after(DELAY, self.on_timer)

    def create_objects(self):
        '''在画布上绘制对象'''
        self.create_text(30, 10, text="Score: {0}".format(self.score),
                         tag="score", fill="white")
        self.create_rectangle(100, 100, 100+NODE_SIZE, 100+NODE_SIZE,
                              fill="yellow", width=0, tag="apple")
        self.create_oval(50, 50, 50+NODE_SIZE, 50+NODE_SIZE,
                         fill="green3", width=0, tag="head")
        self.create_oval(30, 50, 30+NODE_SIZE, 50+NODE_SIZE,
                         fill="green", width=0, tag="dot")
        self.create_oval(40, 50, 40+NODE_SIZE, 50+NODE_SIZE,
                         fill="green", width=0, tag="dot")

    def check_apple_collision(self):
        '''检查蛇头是否碰撞到苹果'''
        apple = self.find_withtag("apple")
        head = self.find_withtag("head")

        x1, y1, x2, y2 = self.bbox(head)
        overlap = self.find_overlapping(x1, y1, x2, y2)

        for ovr in overlap:
            if apple[0] == ovr:
                self.score += 1
                c = self.coords(ovr)
                self.create_oval(c[0], c[1], c[2], c[3],
                                 fill="green", width=0, tag="dot")
                self.draw_apple()

    def move_snake(self):
        '''移动蛇的身体'''
        dots = self.find_withtag("dot")
        head = self.find_withtag("head")
        items = dots + head

        z = 0
        while z < len(items)-1:
            c1 = self.coords(items[z])
            c2 = self.coords(items[z+1])
            self.move(items[z], c2[0]-c1[0], c2[1]-c1[1])
            z += 1
        self.move(head, self.moveX, self.moveY)

    def check_collisions(self):
        '''碰撞检查，是否碰撞到自己身体，是否碰撞到边缘（出界）'''
        dots = self.find_withtag("dot")
        head = self.find_withtag("head")

        x1, y1, x2, y2 = self.bbox(head)
        overlap = self.find_overlapping(x1, y1, x2, y2)

        for dot in dots:
            for over in overlap:
                if over == dot:
                    self.inGame = False

        if x1 < 0:
            self.inGame = False
        if x1 > BOARD_WIDTH - STEP:
            self.inGame = False
        if y1 < 0:
            self.inGame = False
        if y1 > BOARD_HEIGHT - STEP:
            self.inGame = False

    def draw_apple(self):
        '''在画布上绘制苹果'''
        apple = self.find_withtag("apple")
        self.delete(apple[0])
        x = random.randint(5, BOARD_WIDTH/STEP - 5)
        self.appleX = x * STEP
        y = random.randint(5, BOARD_HEIGHT/STEP - 5)
        self.appleY = y * STEP
        self.create_rectangle(self.appleX, self.appleY, self.appleX+NODE_SIZE, self.appleY+NODE_SIZE,
                              fill="yellow", width=0, tag="apple")

    def on_key_pressed(self, e):
        '''用方向键控制蛇身体移动'''
        key = e.keysym

        LEFT_CURSOR_KEY = "Left"
        if key == LEFT_CURSOR_KEY and self.moveX <= 0:
            self.moveX = -STEP
            self.moveY = 0

        RIGHT_CURSOR_KEY = "Right"
        if key == RIGHT_CURSOR_KEY and self.moveX >= 0:
            self.moveX = STEP
            self.moveY = 0

        UP_CURSOR_KEY = "Up"
        if key == UP_CURSOR_KEY and self.moveY <= 0:
            self.moveX = 0
            self.moveY = -STEP

        DOWN_CURSOR_KEY = "Down"
        if key == DOWN_CURSOR_KEY and self.moveY >= 0:
            self.moveX = 0
            self.moveY = STEP

    def on_timer(self):
        '''游戏的定时器，被定时呼叫执行'''
        self.draw_score()
        self.check_collisions()
        if self.inGame:
            self.check_apple_collision()
            self.move_snake()
            self.after(DELAY, self.on_timer)
        else:
            self.game_over()

    def draw_score(self):
        '''记分牌'''
        score = self.find_withtag("score")
        self.itemconfigure(score, text="score: {0}".format(self.score))

    def game_over(self):
        '''删除画布上的所有信息，并显示游戏结束'''
        self.delete(ALL)
        self.create_text(self.winfo_width() / 2, self.winfo_height()/2,
                         text="Game Over with score {0}".format(self.score), fill="white")


class Snake(Frame):
    def __init__(self):
        super().__init__()
        self.master.title('Snake - 贪吃蛇大作战')
        self.board = Board()
        self.pack()


def main():
    root = Tk()
    nib = Snake()
    root.mainloop()


if __name__ == '__main__':
    main()
