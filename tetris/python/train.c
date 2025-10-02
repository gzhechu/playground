#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <time.h>
#include <stdint.h>

// --- 游戏常量 ---
#define GRID_WIDTH 10
#define GRID_HEIGHT 20

// --- 数据结构 ---

// 方块旋转信息
typedef struct {
    const int* shape;
    int width;
    int height;
} ShapeInfo;

// --- 所有方块的形状数据 ---
// I
const int SHAPE_I_0[] = {1, 1, 1, 1};
const int SHAPE_I_1[] = {15};
const ShapeInfo TETROMINO_I[] = {{SHAPE_I_0, 1, 4}, {SHAPE_I_1, 4, 1}};
// T
const int SHAPE_T_0[] = {2, 7};
const int SHAPE_T_1[] = {2, 3, 2};
const int SHAPE_T_2[] = {7, 2};
const int SHAPE_T_3[] = {1, 3, 1};
const ShapeInfo TETROMINO_T[] = {{SHAPE_T_0, 3, 2}, {SHAPE_T_1, 2, 3}, {SHAPE_T_2, 3, 2}, {SHAPE_T_3, 2, 3}};
// O
const int SHAPE_O_0[] = {3, 3};
const ShapeInfo TETROMINO_O[] = {{SHAPE_O_0, 2, 2}};
// L
const int SHAPE_L_0[] = {2, 2, 3};
const int SHAPE_L_1[] = {7, 4};
const int SHAPE_L_2[] = {3, 1, 1};
const int SHAPE_L_3[] = {1, 7};
const ShapeInfo TETROMINO_L[] = {{SHAPE_L_0, 2, 3}, {SHAPE_L_1, 3, 2}, {SHAPE_L_2, 2, 3}, {SHAPE_L_3, 3, 2}};
// J
const int SHAPE_J_0[] = {7, 1};
const int SHAPE_J_1[] = {1, 1, 3};
const int SHAPE_J_2[] = {4, 7};
const int SHAPE_J_3[] = {3, 2, 2};
const ShapeInfo TETROMINO_J[] = {{SHAPE_J_0, 3, 2}, {SHAPE_J_1, 2, 3}, {SHAPE_J_2, 3, 2}, {SHAPE_J_3, 2, 3}};
// Z
const int SHAPE_Z_0[] = {6, 3};
const int SHAPE_Z_1[] = {1, 3, 2};
const ShapeInfo TETROMINO_Z[] = {{SHAPE_Z_0, 3, 2}, {SHAPE_Z_1, 2, 3}};
// S
const int SHAPE_S_0[] = {3, 6};
const int SHAPE_S_1[] = {2, 3, 1};
const ShapeInfo TETROMINO_S[] = {{SHAPE_S_0, 3, 2}, {SHAPE_S_1, 2, 3}};

// 访问所有方块的数组
const ShapeInfo* TETROMINOES[] = {
    TETROMINO_I, TETROMINO_T, TETROMINO_O, TETROMINO_L, TETROMINO_J, TETROMINO_Z, TETROMINO_S
};
const int NUM_ROTATIONS[] = {2, 4, 1, 4, 4, 2, 2};


// --- 跨语言一致的 LCG 随机数生成器 ---
typedef struct {
    uint32_t state;
} LcgRandom;

void lcg_random_init(LcgRandom* r, uint64_t seed) {
    r->state = (uint32_t)seed;
}

int lcg_random_next(LcgRandom* r) {
    const uint32_t A = 1103515245;
    const uint32_t C = 12345;
    r->state = A * r->state + C;
    uint32_t random_value = (r->state >> 16) & 32767;
    return (int)(random_value % 7);
}

// --- 游戏核心模型 ---
typedef struct {
    int width;
    int height;
    int* grid;
    bool in_game;
    int count;
    int tetris_idx;
    int next_tetris;
    int shape_idx;
    int move_x;
    int move_y;
    const double* weights;
    LcgRandom piece_provider;
    int* evaluation_buffer;
    int* solve_buffer;
} TetrisModel;

// 函数声明
double evaluate(TetrisModel* m, int* grid, int try_y, int try_num);
void solve(TetrisModel* m, double* best_score, int* best_x, int* best_y, int* best_num);
void new_tetris(TetrisModel* m);


void tetris_model_init(TetrisModel* m, int w, int h, const double* weights, uint64_t seed) {
    m->width = w;
    m->height = h;
    m->grid = (int*)calloc(h, sizeof(int));
    if (!m->grid) { fprintf(stderr, "Memory allocation failed for grid.\n"); exit(EXIT_FAILURE); }
    m->evaluation_buffer = (int*)calloc(h, sizeof(int));
    if (!m->evaluation_buffer) { fprintf(stderr, "Memory allocation failed for evaluation_buffer.\n"); exit(EXIT_FAILURE); }
    m->solve_buffer = (int*)calloc(h, sizeof(int));
    if (!m->solve_buffer) { fprintf(stderr, "Memory allocation failed for solve_buffer.\n"); exit(EXIT_FAILURE); }
    m->in_game = true;
    m->count = 0;
    m->weights = weights;
    lcg_random_init(&m->piece_provider, seed);
    m->next_tetris = lcg_random_next(&m->piece_provider);
    new_tetris(m);
}

void tetris_model_destroy(TetrisModel* m) {
    free(m->grid);
    free(m->evaluation_buffer);
    free(m->solve_buffer);
}

void new_tetris(TetrisModel* m) {
    m->count++;
    m->tetris_idx = m->next_tetris;
    m->shape_idx = 0;
    m->next_tetris = lcg_random_next(&m->piece_provider);
    m->move_x = m->width / 2 - 1;
    m->move_y = 0;
}

bool collided(TetrisModel* m, int x, int y, int num) {
    if (x < 0) return true;
    const ShapeInfo s = TETROMINOES[m->tetris_idx][num];
    if (x > m->width - s.width) return true;
    if (y > m->height - s.height) return true;
    for (int h = 0; h < s.height; h++) {
        if ((s.shape[h] << x) & m->grid[y + h]) {
            return true;
        }
    }
    return false;
}

void save(TetrisModel* m) {
    const ShapeInfo s = TETROMINOES[m->tetris_idx][m->shape_idx];
    for (int h = 0; h < s.height; h++) {
        m->grid[h + m->move_y] |= s.shape[h] << m->move_x;
    }
    if (m->grid[0] > 0) {
        m->in_game = false;
    }
}

int try_melt(TetrisModel* m) {
    int melted_count = 0;
    int write_idx = m->height - 1; // Where to write the next non-full row

    const int full_row = (1 << m->width) - 1;

    for (int read_idx = m->height - 1; read_idx >= 0; read_idx--) {
        if (m->grid[read_idx] == full_row) {
            melted_count++;
        } else {
            // If it's not a full row, copy it to the write_idx
            m->grid[write_idx] = m->grid[read_idx];
            write_idx--;
        }
    }

    // Fill the top rows with zeros (these were the melted rows)
    for (int i = 0; i <= write_idx; i++) {
        m->grid[i] = 0;
    }
    return melted_count;
}

void solve(TetrisModel* m, double* best_score, int* best_x, int* best_y, int* best_num) {
    *best_score = -1e9;
    const ShapeInfo* t = TETROMINOES[m->tetris_idx];
    int num_rotations = NUM_ROTATIONS[m->tetris_idx];

    for (int idx = 0; idx < num_rotations; idx++) {
        ShapeInfo s = t[idx];
        for (int x = 0; x <= m->width - s.width; x++) {
            int y = 0;
            while (!collided(m, x, y + 1, idx)) {
                y++;
            }

            memcpy(m->solve_buffer, m->grid, m->height * sizeof(int));
            for (int h = 0; h < s.height; h++) {
                m->solve_buffer[h + y] |= s.shape[h] << x;
            }

            double r = evaluate(m, m->solve_buffer, y, idx);
            if (r > *best_score) {
                *best_score = r;
                *best_x = x;
                *best_y = y;
                *best_num = idx;
            }
        }
    }
}

double evaluate(TetrisModel* m, int* grid, int try_y, int try_num) {
    int row_transitions = 0;
    int column_transitions = 0;
    int number_of_holes = 0;
    int well_sums = 0;

    int* final_grid = m->evaluation_buffer;
    memset(final_grid, 0, m->height * sizeof(int));

    int melted = 0;
    const int full_row_mask = (1 << m->width) - 1;
    int current_write_row = m->height - 1;

    for (int y = m->height - 1; y >= 0; y--) {
        if (grid[y] == full_row_mask) {
            melted++;
        } else {
            if (current_write_row >= 0) {
                final_grid[current_write_row] = grid[y];
            }
            current_write_row--;
        }
    }

    for (int y = 0; y < m->height; y++) {
        int last_cell = 1;
        for (int x = 0; x < m->width; x++) {
            int cell = (final_grid[y] >> x) & 1;
            if (last_cell != cell) row_transitions++;
            last_cell = cell;
        }
        if (last_cell == 0) row_transitions++;
    }

    for (int x = 0; x < m->width; x++) {
        int mark = 0;
        int col_cells = 0;
        int wells = 0;
        int last_cell = 0;
        for (int y = 0; y < m->height; y++) {
            int cell = (final_grid[y] >> x) & 1;
            if (last_cell != cell) column_transitions++;
            last_cell = cell;

            bool is_well = false;
            if (cell == 0) { // Only empty cells can be part of a well
                int left_neighbor = (x > 0) ? (final_grid[y] >> (x - 1) & 1) : 0;
                int right_neighbor = (x < m->width - 1) ? (final_grid[y] >> (x + 1) & 1) : 0;

                if (x == 0) { // Leftmost column
                    if (right_neighbor == 1) is_well = true;
                } else if (x == m->width - 1) { // Rightmost column
                    if (left_neighbor == 1) is_well = true;
                } else { // Middle columns
                    if (left_neighbor == 1 && right_neighbor == 1) is_well = true;
                }
            }

            if (is_well) {
                wells++;
            } else if (wells > 0) {
                well_sums += (1 + wells) * wells / 2;
                wells = 0;
            }

            if (cell == 1) {
                col_cells++;
                if (mark == 0) mark = y;
            }
        }
        if (wells > 0) well_sums += (1 + wells) * wells / 2;
        if (col_cells > 0) number_of_holes += (m->height - mark - col_cells);
        if (last_cell == 0) column_transitions++;
    }

    const ShapeInfo s = TETROMINOES[m->tetris_idx][try_num];
    double landing_height = (20.0 - (double)(try_y + s.height)) + (double)(s.height - 1) / 2.0;

    return m->weights[0] * landing_height +
           m->weights[1] * (double)melted +
           m->weights[2] * (double)row_transitions +
           m->weights[3] * (double)column_transitions +
           m->weights[4] * (double)number_of_holes +
           m->weights[5] * (double)well_sums;
}

void verify_performance(int game_limit, const double* weights, uint64_t seed) {
    printf("Running verification with %d blocks and seed %llu...\n", game_limit, (unsigned long long)seed);
    clock_t start_time = clock();

    TetrisModel model;
    tetris_model_init(&model, GRID_WIDTH, GRID_HEIGHT, weights, seed);
    int lines_cleared = 0;
    int i = 0;

    for (i = 0; i < game_limit; i++) {
        if (!model.in_game) {
            printf("Game over after %d pieces.\n", i);
            break;
        }
        
        double best_score;
        int best_x, best_y, best_num;
        solve(&model, &best_score, &best_x, &best_y, &best_num);

        model.move_x = best_x;
        model.move_y = best_y;
        model.shape_idx = best_num;

        save(&model);
        lines_cleared += try_melt(&model);

        if (model.in_game) {
            new_tetris(&model);
        }
    }

    clock_t end_time = clock();
    double duration = ((double)(end_time - start_time)) / CLOCKS_PER_SEC;

    printf("Verification finished.\n");
    printf("Total pieces: %d, Total lines cleared: %d\n", model.count - 1, lines_cleared);
    printf("Total time: %.2fs\n", duration);

    tetris_model_destroy(&model);
}

int main(int argc, char *argv[]) {
    uint64_t seed = 12345;
    int limit = 1000000;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-verify") == 0 || strcmp(argv[i], "--verify") == 0) {
            // Included for compatibility, but this program only has verify mode.
        } else if ((strcmp(argv[i], "-seed") == 0 || strcmp(argv[i], "--seed") == 0) && i + 1 < argc) {
            seed = strtoull(argv[++i], NULL, 10);
        } else if ((strcmp(argv[i], "-limit") == 0 || strcmp(argv[i], "--limit") == 0) && i + 1 < argc) {
            limit = atoi(argv[++i]);
        }
    }

    const double python_weights[] = {
        -4.500158825082766,
        3.4181268101392694,
        -3.2178882868487753,
        -9.348695305445199,
        -7.899265427351652,
        -3.3855972247263626,
    };

    verify_performance(limit, python_weights, seed);

    return 0;
}
