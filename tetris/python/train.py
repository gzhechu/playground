import random
import time
import numpy as np
import multiprocessing
from functools import partial
from typing import List, Tuple, Any
from multiprocessing.pool import Pool

# 从原始的 tetris.py 文件中导入必要的模块
# 我们需要 TetrisModel 作为父类，以及 T, GRID_WIDTH, GRID_HEIGHT 等常量
from tetris import TetrisModel, T, GRID_WIDTH, GRID_HEIGHT

# --- 遗传算法的超参数 ---
POPULATION_SIZE = 128  # 种群大小 (设为16线程的4倍，便于工作分配)
NUM_WEIGHTS = 6  # 权重的数量 (我们有6个指标)
MUTATION_RATE = 0.25      # 变异率 (increased for more exploration)
CROSSOVER_RATE = 0.8  # 交叉率
NUM_GENERATIONS = 100  # 迭代多少代
ELITISM_PERCENT = 0.1  # 保留多少比例的精英
GAME_LIMIT = 60000 # 每局游戏最多放置的方块数

# --- 步骤一：创建可训练的 Tetris 模型 ---


class TrainableTetrisModel(TetrisModel):
    """
    一个可训练的 Tetris 模型，它继承自原始的 TetrisModel,
    但使用可变的权重进行评估。
    """

    def __init__(self, w: int, h: int, weights: np.ndarray) -> None:
        # 调用父类的构造函数来初始化游戏板等
        super().__init__(w, h)
        # 存储我们自己的权重
        self.weights = weights

    def evaluate(self, grid: List[int], try_x: int, try_y: int, try_num: int) -> List:
        """
        重写(override)父类的评估函数。
        这里的代码和父类完全一样，除了最后计算 score 的部分。
        """
        # --- 这部分代码完全复制自 TetrisModel.evaluate ---
        LandingHeight = 0
        RowTransitions = 0
        ColumnTransitions = 0
        NumberOfHoles = 0
        WellSums = 0

        melted = 0
        h = self.height - 1
        while h > 0:
            if 1 << self.width <= grid[h] + 1:
                melted += 1
                for y in range(h, 0, -1):
                    grid[y] = grid[y - 1]
                h += 1
            h -= 1

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
                cell = (grid[y] >> x) & 1
                if last_cell != cell:
                    ColumnTransitions += 1
                last_cell = cell
                if x == 0:
                    if cell == 0 and (grid[y] >> 1 & 1) == 1:
                        wells += 1
                    elif wells > 0:
                        WellSums += (1 + wells) * wells / 2
                        wells = 0
                    if y >= self.height - 1:
                        WellSums += (1 + wells) * wells / 2
                        wells = 0
                elif x == self.width - 1:
                    if cell == 0 and (grid[y] >> x - 1 & 1) == 1:
                        wells += 1
                    elif wells > 0:
                        WellSums += (1 + wells) * wells / 2
                        wells = 0
                    if y >= self.height - 1:
                        WellSums += (1 + wells) * wells / 2
                        wells = 0
                else:
                    if (
                        cell == 0
                        and (grid[y] >> x - 1 & 1) == 1
                        and (grid[y] >> x + 1 & 1) == 1
                    ):
                        wells += 1
                    elif wells > 0:
                        WellSums += (1 + wells) * wells / 2
                        wells = 0
                    if y >= self.height - 1:
                        WellSums += (1 + wells) * wells / 2
                        wells = 0
                if cell == 1:
                    col_cells += 1
                    if mark == 0:
                        mark = y
            if col_cells > 0:
                NumberOfHoles += self.height - mark - col_cells
            if last_cell == 0:
                ColumnTransitions += 1

        s = T[self.tetris_idx][try_num]
        lh = 20 - (try_y + s["height"])
        LandingHeight = lh + (s["height"] - 1) / 2
        # --- 代码复制结束 ---

        # 唯一的改动：使用我们自己的权重来计算分数
        score = (
            self.weights[0] * LandingHeight
            + self.weights[1] * melted
            + self.weights[2] * RowTransitions
            + self.weights[3] * ColumnTransitions
            + self.weights[4] * NumberOfHoles
            + self.weights[5] * WellSums
        )

        # 返回的结果和父类保持一致
        return [
            score,
            try_x,
            try_y,
            try_num,
            (
                self.count,
                lh,
                s["height"],
                LandingHeight,
                melted,
                RowTransitions,
                ColumnTransitions,
                NumberOfHoles,
                WellSums,
            ),
        ]


# --- 步骤二：定义游戏运行和遗传算法函数 ---


def run_game_for_training(weights: np.ndarray) -> int:
    """为遗传算法运行一局无界面的游戏，返回消行数。"""
    lines_cleared = 0
    # 使用我们创建的可训练模型，并传入权重
    model = TrainableTetrisModel(GRID_WIDTH, GRID_HEIGHT, weights)

    for _ in range(GAME_LIMIT):
        if not model.in_game:
            break

        model.new_tetris()
        # model.solve() 会自动调用我们重写的 evaluate 方法
        answer = model.solve()

        model.moveX = answer[1]
        model.shape_idx = answer[3]

        # 模拟方块下落
        y = 0
        while not model.collided(model.moveX, y + 1, model.shape_idx):
            y += 1
        model.moveY = y

        model.save()
        melted = model.try_melt()
        lines_cleared += len(melted)

    return lines_cleared


def initialize_population() -> List[np.ndarray]:
    """初始化种群"""
    return [np.random.uniform(-1.0, 1.0, NUM_WEIGHTS) for _ in range(POPULATION_SIZE)]


def calculate_fitness_parallel(population: List[np.ndarray], pool: Pool) -> np.ndarray:
    """使用多进程并行计算适应度（接收一个已存在的pool）"""
    # 运行两次游戏取平均值，使分数更稳定
    scores1 = pool.map(run_game_for_training, population)
    scores2 = pool.map(run_game_for_training, population)
    fitness_scores = (np.array(scores1) + np.array(scores2)) / 2
    return fitness_scores


def selection(population: List[np.ndarray], fitness_scores: np.ndarray) -> List[np.ndarray]:
    """选择、交叉和变异来产生下一代"""
    # For roulette wheel selection, weights must be non-negative.
    # Shift fitness scores to be non-negative if they're not already.
    min_fitness = np.min(fitness_scores)
    if min_fitness < 0:
        fitness_weights = fitness_scores - min_fitness
    else:
        fitness_weights = fitness_scores

    # Avoid division by zero if all scores are zero.
    if np.sum(fitness_weights) == 0:
        fitness_weights = np.ones_like(fitness_weights)

    sorted_indices = np.argsort(fitness_scores)[::-1]
    
    num_elites = int(ELITISM_PERCENT * POPULATION_SIZE)
    elites = [population[i] for i in sorted_indices[:num_elites]]
    
    next_generation = elites
    
    while len(next_generation) < POPULATION_SIZE:
        # 改变选择策略：使用轮盘赌选择，从整个种群中根据适应度按比例选择父母
        parent1, parent2 = random.choices(population, weights=fitness_weights, k=2)
        
        # 交叉
        if random.random() < CROSSOVER_RATE:
            point = random.randint(1, NUM_WEIGHTS - 1)
            child = np.concatenate([parent1[:point], parent2[point:]])
        else:
            child = random.choice([parent1, parent2]).copy()
            
        # 变异
        for i in range(NUM_WEIGHTS):
            if random.random() < MUTATION_RATE:
                # 加大变异力度：扩大变异范围
                child[i] += np.random.uniform(-0.4, 0.4)
        
        next_generation.append(child)
        
    return next_generation


# --- 步骤三：主训练循环 ---


def main() -> None:
    # 设置多进程启动方式，兼容不同操作系统
    try:
        multiprocessing.set_start_method("fork", force=True)
    except RuntimeError:
        pass  # 'fork' might already be set

    population = initialize_population()

    # 在循环外只创建一次进程池
    with multiprocessing.Pool() as pool:
        for gen in range(NUM_GENERATIONS):
            start_time = time.monotonic()

            print(f"\n--- Generation {gen + 1}/{NUM_GENERATIONS} ---")

            # 将 pool 传入函数中
            fitness_scores = calculate_fitness_parallel(population, pool)

            best_fitness = np.max(fitness_scores)
            best_weights_idx = np.argmax(fitness_scores)
            best_weights = population[best_weights_idx]

            population = selection(population, fitness_scores)

            end_time = time.monotonic()
            duration = end_time - start_time

            print(f"Generation Time: {duration:.2f}s")
            print(f"Best Fitness (avg lines cleared): {best_fitness:.2f}")
            print(f"Best Weights: {np.round(best_weights, 4)}")

    print("\n--- Training Finished ---")
    # 最终找到的最优权重
    # 在这里也需要一个临时的pool来完成最后一次评估
    with multiprocessing.Pool() as pool:
        final_fitness = calculate_fitness_parallel(population, pool)
        final_best_idx = np.argmax(final_fitness)
        final_best_weights = population[final_best_idx]
        print(f"Final best weights found: {final_best_weights}")


if __name__ == "__main__":
    # 检查是否安装了 numpy
    try:
        import numpy as np
    except ImportError:
        print("Error: numpy is not installed. Please run 'pip install numpy'")
        exit()

    main()