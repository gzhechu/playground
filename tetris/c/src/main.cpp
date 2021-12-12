#include <curses.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

#define TIMESTEP 500000
#define TILE ' '

#define ZONEWIDTH 12
#define ZONEHEIGHT 22

enum DIRECTION { UP = 1, DOWN = 2, LEFT = 3, RIGHT = 4 };
enum REASON { USER_QUIT = 1, SMALLWINSIZE };

char game_zone[ZONEHEIGHT + 1][ZONEWIDTH + 4] = {0};
int zone_top = 0, zone_left = 0;

typedef char shape[4][4];
typedef shape tetris[4];

tetris T[7] = {{{{0, 1, 0, 0}, {0, 1, 0, 0}, {0, 1, 1, 0}, {0, 0, 0, 0}}, // L
                {{0, 0, 0, 0}, {0, 0, 1, 0}, {1, 1, 1, 0}, {0, 0, 0, 0}},
                {{1, 1, 0, 0}, {0, 1, 0, 0}, {0, 1, 0, 0}, {0, 0, 0, 0}},
                {{0, 0, 0, 0}, {1, 1, 1, 0}, {1, 0, 0, 0}, {0, 0, 0, 0}}},
               {{{0, 1, 1, 0}, {0, 1, 1, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}}, // O
                {{0, 1, 1, 0}, {0, 1, 1, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}},
                {{0, 1, 1, 0}, {0, 1, 1, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}},
                {{0, 1, 1, 0}, {0, 1, 1, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}}},
               {{{0, 0, 1, 0}, {0, 0, 1, 0}, {0, 1, 1, 0}, {0, 0, 0, 0}}, // J
                {{0, 0, 0, 0}, {1, 1, 1, 0}, {0, 0, 1, 0}, {0, 0, 0, 0}},
                {{0, 1, 1, 0}, {0, 1, 0, 0}, {0, 1, 0, 0}, {0, 0, 0, 0}},
                {{0, 0, 0, 0}, {1, 0, 0, 0}, {1, 1, 1, 0}, {0, 0, 0, 0}}},
               {{{0, 0, 0, 0}, {1, 1, 0, 0}, {0, 1, 1, 0}, {0, 0, 0, 0}}, // Z
                {{0, 1, 0, 0}, {1, 1, 0, 0}, {1, 0, 0, 0}, {0, 0, 0, 0}},
                {{0, 0, 0, 0}, {1, 1, 0, 0}, {0, 1, 1, 0}, {0, 0, 0, 0}},
                {{0, 1, 0, 0}, {1, 1, 0, 0}, {1, 0, 0, 0}, {0, 0, 0, 0}}},
               {{{0, 0, 0, 0}, {0, 1, 1, 0}, {1, 1, 0, 0}, {0, 0, 0, 0}}, // S
                {{1, 0, 0, 0}, {1, 1, 0, 0}, {0, 1, 0, 0}, {0, 0, 0, 0}},
                {{0, 0, 0, 0}, {0, 1, 1, 0}, {1, 1, 0, 0}, {0, 0, 0, 0}},
                {{1, 0, 0, 0}, {1, 1, 0, 0}, {0, 1, 0, 0}, {0, 0, 0, 0}}},
               {{{0, 1, 0, 0}, {0, 1, 0, 0}, {0, 1, 0, 0}, {0, 1, 0, 0}}, // I
                {{0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {1, 1, 1, 1}},
                {{0, 0, 1, 0}, {0, 0, 1, 0}, {0, 0, 1, 0}, {0, 0, 1, 0}},
                {{0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {1, 1, 1, 1}}},
               {{{0, 0, 0, 0}, {0, 1, 0, 0}, {1, 1, 1, 0}, {0, 0, 0, 0}}, // T
                {{0, 1, 0, 0}, {1, 1, 0, 0}, {0, 1, 0, 0}, {0, 0, 0, 0}},
                {{0, 0, 0, 0}, {1, 1, 1, 0}, {0, 1, 0, 0}, {0, 0, 0, 0}},
                {{0, 1, 0, 0}, {0, 1, 1, 0}, {0, 1, 0, 0}, {0, 0, 0, 0}}}};

int tetris_num = 0;
int shape_num = 0;
int color_num = 0;

int position_x = 0;
int position_y = 0;

bool pause_move = false;

WINDOW *mainwin;
int oldcur;
int rows, cols;

void debug(void) {
    mvwprintw(mainwin, rows - 1, 0,
              "rows:%d, cols:%d, w:%d, h:%d, l:%d, t:%d, x:%d, y:%d, T:%d t:%d "
              "s:%d c:%d\n ",
              rows, cols, ZONEWIDTH, ZONEHEIGHT, zone_left, zone_top,
              position_x, position_y, sizeof(T) / sizeof(tetris), tetris_num,
              shape_num, color_num);
}

void game_zone_init() {
    for (int i = 0; i < ZONEHEIGHT + 1; i++) {
        game_zone[i][0] = 1;
        game_zone[i][1] = 1;
        game_zone[i][ZONEWIDTH + 2] = 1;
        game_zone[i][ZONEWIDTH + 3] = 1;
    }
    for (int j = 0; j < ZONEWIDTH + 4; j++) {
        game_zone[ZONEHEIGHT][j] = 1;
    }
}

void draw_frame() {
    attron(COLOR_PAIR(7));
    for (int i = 2; i < ZONEHEIGHT + 1; i++) {
        for (int j = 1; j < ZONEWIDTH + 3; j++) {
            if (1 == j) {
                mvaddch(zone_top + i, zone_left - 4 + j * 2 + 1, TILE);
            } else if (ZONEWIDTH + 2 == j) {
                mvaddch(zone_top + i, zone_left - 4 + j * 2, TILE);
            }
            if (i == ZONEHEIGHT) {
                mvaddch(zone_top + i, zone_left - 4 + j * 2, TILE);
                mvaddch(zone_top + i, zone_left - 4 + j * 2 + 1, TILE);
            }
        }
    }
    attroff(COLOR_PAIR(7));
}

bool collision_detect(int x, int y, shape s) {
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            if (0 != s[i][j]) {
                if (s[i][j] != s[i][j] + game_zone[i + y][j + x + 2]) {
                    return true;
                }
            }
        }
    }
    return false;
}

void draw_tile(int x, int y, int color) {
    attron(COLOR_PAIR(color));
    if (255 == color) {
        mvaddch(zone_top + y, zone_left + x * 2, color + '0');
        mvaddch(zone_top + y, zone_left + x * 2 + 1, color + '0');
    } else {
        mvaddch(zone_top + y, zone_left + x * 2, TILE);
        mvaddch(zone_top + y, zone_left + x * 2 + 1, TILE);
    }
    attroff(COLOR_PAIR(color));
}

void shape_draw(int x, int y, int color, shape s) {
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            if (0 != s[i][j]) {
                draw_tile(x + j, y + i, color);
            }
        }
    }
}

void game_zone_redraw() {
    for (int i = 0; i < ZONEHEIGHT; i++) {
        for (int j = 2; j < ZONEWIDTH + 2; j++) {
            draw_tile(j - 2, i, game_zone[i][j]);
        }
    }
}

bool game_zone_overflow() {
    bool ret = false;
    int n = 1;
    for (int i = 2; i < ZONEWIDTH + 2; i++) {
        if (game_zone[n][i] > 0) {
            ret = true;
            break;
        }
    }
    return ret;
}

void quit(int reason) {
    delwin(mainwin);
    curs_set(oldcur);
    endwin();
    refresh();

    switch (reason) {
    case SMALLWINSIZE:
        printf("\nWindows size is too small!\n");
        printf("\nGoodbye!\n");
        break;
    default:
        printf("\nGoodbye!\n");
        break;
    }
    exit(EXIT_SUCCESS);
}

void game_over() {
    pause_move = true;
    int color;
    for (int y = ZONEHEIGHT - 1; y > 1; y--) {
        for (int x = 2; x < ZONEWIDTH + 2; x++) {
            color = rand() % COLOR_CYAN + 1;
            draw_tile(x - 2, y, color);
        }
        // usleep(1000 * 100);
    }

    int rows, cols;
    char gameover[] = " Game  Over! ";
    getmaxyx(mainwin, rows, cols);
    mvprintw(rows / 2, (cols - strlen(gameover)) / 2, gameover);
    getch();
    quit(USER_QUIT);
}

void tetris_rotate(void) {
    if (shape_num >= 3) {
        if (!collision_detect(position_x, position_y, T[tetris_num][0])) {
            shape_draw(position_x, position_y, COLOR_BLACK,
                       T[tetris_num][shape_num]);
            shape_num = 0;
            shape_draw(position_x, position_y, color_num,
                       T[tetris_num][shape_num]);
        }
    } else {
        if (!collision_detect(position_x, position_y,
                              T[tetris_num][shape_num + 1])) {
            shape_draw(position_x, position_y, COLOR_BLACK,
                       T[tetris_num][shape_num]);
            shape_num = shape_num + 1;
            shape_draw(position_x, position_y, color_num,
                       T[tetris_num][shape_num]);
        }
    }
}

bool shape_move(int dir) {
    shape *s = &T[tetris_num][shape_num];
    bool ret = false;
    switch (dir) {
    case DOWN:
        if (!collision_detect(position_x, position_y + 1, *s)) {
            shape_draw(position_x, position_y, COLOR_BLACK, *s);
            position_y = position_y + 1;
            shape_draw(position_x, position_y, color_num, *s);
            ret = true;
        }
        break;
    case LEFT:
        if (!collision_detect(position_x - 1, position_y, *s)) {
            shape_draw(position_x, position_y, COLOR_BLACK, *s);
            position_x = position_x - 1;
            shape_draw(position_x, position_y, color_num, *s);
            ret = true;
        }
        break;
    case RIGHT:
        if (!collision_detect(position_x + 1, position_y, *s)) {
            shape_draw(position_x, position_y, COLOR_BLACK, *s);
            position_x = position_x + 1;
            shape_draw(position_x, position_y, color_num, *s);
            ret = true;
        }
        break;
    }
    return ret;
}

void shape_save(int x, int y, shape s) {
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            if (0 != s[i][j]) {
                game_zone[i + y][j + x + 2] = color_num;
            }
        }
    }

    if (game_zone_overflow())
        game_over();
}

bool melt_detect(int n) {
    int cnt = 0;
    bool ret = true;
    for (int i = 0; i < ZONEWIDTH + 4; i++) {
        if (game_zone[n][i] > 0)
            cnt += 1;
    }
    if (cnt == ZONEWIDTH + 4)
        ret = true;
    else
        ret = false;
    return ret;
}

void melt_it(int n) {
    for (int i = n; i > 0; i--) {
        for (int j = 0; j < ZONEWIDTH + 4; j++) {
            game_zone[i][j] = game_zone[i - 1][j];
        }
    }
}

bool try_melt() {
    bool ret = false;
    for (int i = ZONEHEIGHT - 1; i > 0; i--) {
        if (melt_detect(i)) {
            melt_it(i++);
            ret = true;
        }
    }
    return ret;
}

void tetris_new() {
    tetris_num = rand() % (sizeof(T) / sizeof(tetris));
    color_num = rand() % COLOR_CYAN + 1;
    position_x = ZONEWIDTH / 2 - 2;
    position_y = 0;
    shape_draw(position_x, position_y, color_num, T[tetris_num][shape_num]);
}

void get_term_size(int *rows, int *cols) {
    struct winsize ws;
    /*  Get terminal size  */
    if (ioctl(0, TIOCGWINSZ, &ws) < 0) {
        perror("couldn't get window size");
        exit(EXIT_FAILURE);
    }
    *rows = ws.ws_row;
    *cols = ws.ws_col;
}

void signal_handler(int signum) {
    /*  Switch on signal number  */
    switch (signum) {
    case SIGALRM:
        /*  Received from the timer  */
        if (!pause_move) {
            if (!shape_move(DOWN)) {
                shape_save(position_x, position_y, T[tetris_num][shape_num]);
                if (try_melt())
                    game_zone_redraw();
                tetris_new();
            }
        }
        debug();
        return;
    case SIGTERM:
    case SIGINT:
        quit(USER_QUIT);
    }
}

/*  Sets up the game timer  */
void set_timer(void) {
    struct itimerval it;
    /*  Clear itimerval struct members  */
    timerclear(&it.it_interval);
    timerclear(&it.it_value);
    /*  Set timer  */
    it.it_interval.tv_usec = TIMESTEP;
    it.it_value.tv_usec = TIMESTEP;
    setitimer(ITIMER_REAL, &it, NULL);
}

/*  Sets up signal handlers we need  */
void set_signals(void) {
    struct sigaction sa;
    /*  Fill in sigaction struct  */
    sa.sa_handler = signal_handler;
    sa.sa_flags = 0;
    sigemptyset(&sa.sa_mask);
    /*  Set signal handlers  */
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGALRM, &sa, NULL);
    /*  Ignore SIGTSTP  */
    sa.sa_handler = SIG_IGN;
    sigaction(SIGTSTP, &sa, NULL);
}

int main(void) {
    /*  Seed RNG, set timer and register signal handlers  */
    srand((unsigned)time(NULL));
    set_timer();
    set_signals();

    /*  Initialize ncurses  */
    if ((mainwin = initscr()) == NULL) {
        perror("error initialising ncurses");
        exit(EXIT_FAILURE);
    }

    noecho();
    keypad(mainwin, TRUE);
    oldcur = curs_set(0);

    start_color();
    for (int i = 0; i <= COLOR_WHITE; i++)
        init_pair(i, COLOR_WHITE, i);

    /* Get window size */
    get_term_size(&rows, &cols);

    if (cols < ZONEWIDTH * 2 + 16 || rows < ZONEHEIGHT + 1) {
        quit(SMALLWINSIZE);
    }

    zone_left = (cols - ZONEWIDTH * 2) / 2;
    zone_top = 1;

    game_zone_init();
    draw_frame();
    tetris_new();

    /*  Loop and get user input  */
    while (1) {
        int key = getch();

        switch (key) {
        case KEY_DOWN:
        case 'D':
        case 'd':
            if (!shape_move(DOWN)) {
                shape_save(position_x, position_y, T[tetris_num][shape_num]);
                if (try_melt())
                    game_zone_redraw();
                tetris_new();
            }
            break;

        case ' ':
            while (shape_move(DOWN)) {
            }
            break;

        case KEY_LEFT:
        case 'S':
        case 's':
            shape_move(LEFT);
            break;

        case KEY_RIGHT:
        case 'F':
        case 'f':
            shape_move(RIGHT);
            break;

        case KEY_UP:
        case 'J':
        case 'j':
            tetris_rotate();
            break;

        case 'P':
        case 'p':
            pause_move = !pause_move;
            break;

        case 27:
        case 'Q':
        case 'q':
            quit(USER_QUIT);
            break;
        }
    }
    return EXIT_SUCCESS;
}
