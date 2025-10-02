
use clap::Parser;
use indicatif::{ProgressBar, ProgressStyle};
use rand::prelude::*;
use rayon::prelude::*;
use std::time::Instant;

// --- 遗传算法的超参数 (Hyperparameters) ---
const POPULATION_SIZE: usize = 128;
const NUM_WEIGHTS: usize = 6;
const CROSSOVER_RATE: f64 = 0.8;
const ELITISM_PERCENT: f64 = 0.1;
const GAME_LIMIT: u32 = 50000000;
const MUTATION_RATE: f64 = 0.17;
const MUTATION_MAGNITUDE: f64 = 0.4;

// --- Tetris 游戏常量 ---
const GRID_WIDTH: i32 = 10;
const GRID_HEIGHT: i32 = 20;

// ShapeInfo 对应 Python 中 T 列表里的每个方块的旋转信息
#[derive(Clone, Copy)]
struct ShapeInfo {
    shape: &'static [i32],
    width: i32,
    height: i32,
}

// Tetrominoes 对应 Python 中的 T 列表
static TETROMINOES: [&[ShapeInfo]; 7] = [
    &[ // I
        ShapeInfo { shape: &[1, 1, 1, 1], width: 1, height: 4 },
        ShapeInfo { shape: &[15], width: 4, height: 1 },
    ],
    &[ // T
        ShapeInfo { shape: &[2, 7], width: 3, height: 2 },
        ShapeInfo { shape: &[2, 3, 2], width: 2, height: 3 },
        ShapeInfo { shape: &[7, 2], width: 3, height: 2 },
        ShapeInfo { shape: &[1, 3, 1], width: 2, height: 3 },
    ],
    &[ // O
        ShapeInfo { shape: &[3, 3], width: 2, height: 2 },
    ],
    &[ // L
        ShapeInfo { shape: &[2, 2, 3], width: 2, height: 3 },
        ShapeInfo { shape: &[7, 4], width: 3, height: 2 },
        ShapeInfo { shape: &[3, 1, 1], width: 2, height: 3 },
        ShapeInfo { shape: &[1, 7], width: 3, height: 2 },
    ],
    &[ // J
        ShapeInfo { shape: &[7, 1], width: 3, height: 2 },
        ShapeInfo { shape: &[1, 1, 3], width: 2, height: 3 },
        ShapeInfo { shape: &[4, 7], width: 3, height: 2 },
        ShapeInfo { shape: &[3, 2, 2], width: 2, height: 3 },
    ],
    &[ // Z
        ShapeInfo { shape: &[6, 3], width: 3, height: 2 },
        ShapeInfo { shape: &[1, 3, 2], width: 2, height: 3 },
    ],
    &[ // S
        ShapeInfo { shape: &[3, 6], width: 3, height: 2 },
        ShapeInfo { shape: &[2, 3, 1], width: 2, height: 3 },
    ],
];

// --- Tetris 游戏模型 ---

// PieceProvider 定义了任何方块生成器都需要满足的接口
trait PieceProvider: Send {
    fn next(&mut self) -> usize;
}

// TetrisRandom 实现了 "7-bag" 随机生成算法
struct TetrisRandom {
    pool: Vec<usize>,
    rng: StdRng,
}

impl TetrisRandom {
    fn new(seed: u64) -> Self {
        TetrisRandom {
            pool: Vec::new(),
            rng: StdRng::seed_from_u64(seed),
        }
    }
}

impl PieceProvider for TetrisRandom {
    fn next(&mut self) -> usize {
        if self.pool.is_empty() {
            // 7 bags of 7 tetrominos
            let mut new_pool: Vec<usize> = (0..49).map(|i| i % 7).collect();
            new_pool.shuffle(&mut self.rng);
            self.pool = new_pool;
        }
        self.pool.pop().unwrap()
    }
}

// LcgRandom 实现了与 Go 版本兼容的线性同余生成器 (LCG)
struct LcgRandom {
    state: u32,
}

impl LcgRandom {
    fn new(seed: u64) -> Self {
        LcgRandom { state: seed as u32 }
    }
}

impl PieceProvider for LcgRandom {
    fn next(&mut self) -> usize {
        // Parameters from POSIX standard (used in glibc's rand())
        const A: u32 = 1103515245;
        const C: u32 = 12345;

        self.state = A.wrapping_mul(self.state).wrapping_add(C);
        let random_value = (self.state >> 16) & 32767; // Get high 15 bits
        (random_value % 7) as usize
    }
}

// TetrisModel 翻译自 Go 的 TetrisModel 结构体
struct TetrisModel<'a> {
    width: i32,
    height: i32,
    grid: Vec<i32>,
    in_game: bool,
    count: u32,
    tetris_idx: usize,
    next_tetris: usize,
    shape_idx: usize,
    move_x: i32,
    move_y: i32,
    weights: &'a [f64],
    piece_provider: Box<dyn PieceProvider>,
    evaluation_buffer: Vec<i32>,
    solve_buffer: Vec<i32>,
}

impl<'a> TetrisModel<'a> {
    fn new(
        w: i32,
        h: i32,
        weights: &'a [f64],
        mut provider: Box<dyn PieceProvider>,
    ) -> Self {
        let next_tetris = provider.next();
        let mut model = TetrisModel {
            width: w,
            height: h,
            grid: vec![0; h as usize],
            in_game: true,
            count: 0,
            tetris_idx: 0, // Will be overwritten by new_tetris
            next_tetris,
            shape_idx: 0,
            move_x: 0,
            move_y: 0,
            weights,
            piece_provider: provider,
            evaluation_buffer: vec![0; h as usize],
            solve_buffer: vec![0; h as usize],
        };
        model.new_tetris();
        model
    }

    fn new_tetris(&mut self) {
        self.count += 1;
        self.tetris_idx = self.next_tetris;
        self.shape_idx = 0;
        self.next_tetris = self.piece_provider.next();
        self.move_x = self.width / 2 - 1;
        self.move_y = 0;
    }

    fn collided(&self, x: i32, y: i32, num: usize) -> bool {
        if x < 0 {
            return true;
        }
        let s = TETROMINOES[self.tetris_idx][num];
        if x > self.width - s.width {
            return true;
        }
        if y > self.height - s.height {
            return true;
        }
        for h in 0..s.height {
            if (s.shape[h as usize] << x) & self.grid[(y + h) as usize] != 0 {
                return true;
            }
        }
        false
    }

    fn save(&mut self) {
        let s = TETROMINOES[self.tetris_idx][self.shape_idx];
        for h in 0..s.height {
            self.grid[(h + self.move_y) as usize] |= s.shape[h as usize] << self.move_x;
        }
        if self.grid[0] > 0 {
            self.in_game = false;
        }
    }

    fn try_melt(&mut self) -> i32 {
        let mut melted_count = 0;
        let mut h = (self.height - 1) as usize;
        let full_row = (1 << self.width) - 1;

        while h > 0 {
            if self.grid[h] == full_row {
                melted_count += 1;
                for y in (1..=h).rev() {
                    self.grid[y] = self.grid[y - 1];
                }
                self.grid[0] = 0;
            } else {
                h -= 1;
            }
        }
        melted_count
    }

    fn solve(&mut self) -> (f64, i32, i32, usize) {
        let mut best_score = -1e9;
        let mut best_x = 0;
        let mut best_y = 0;
        let mut best_num = 0;

        let t = TETROMINOES[self.tetris_idx];
        
        for idx in 0..t.len() {
            let s = t[idx];
            for x in 0..=self.width - s.width {
                let y = {
                    let mut y_inner = 0;
                    while !self.collided(x, y_inner + 1, idx) {
                        y_inner += 1;
                    }
                    y_inner
                };

                let temp_grid = &mut self.solve_buffer;
                temp_grid.copy_from_slice(&self.grid);
                for h in 0..s.height {
                    temp_grid[(h + y) as usize] |= s.shape[h as usize] << x;
                }

                let r = evaluate(
                    self.weights,
                    self.width,
                    self.height,
                    self.tetris_idx,
                    &mut self.evaluation_buffer,
                    temp_grid,
                    y,
                    idx,
                );
                if r > best_score {
                    best_score = r;
                    best_x = x;
                    best_y = y;
                    best_num = idx;
                }
            }
        }
        (best_score, best_x, best_y, best_num)
    }
}

// `evaluate` is now a free function, completely decoupled from the TetrisModel instance.
fn evaluate(
    weights: &[f64],
    width: i32,
    height: i32,
    tetris_idx: usize,
    evaluation_buffer: &mut [i32],
    grid: &[i32],
    try_y: i32,
    try_num: usize,
) -> f64 {
    let mut row_transitions = 0;
    let mut column_transitions = 0;
    let mut number_of_holes = 0;
    let mut well_sums = 0;

    let final_grid = evaluation_buffer;
    final_grid.fill(0);

    let melted;
    let full_row_mask = (1 << width) - 1;

    let mut current_write_row = (height - 1) as i32;
    let mut melted_count = 0;
    for y in (0..height as usize).rev() {
        if grid[y] == full_row_mask {
            melted_count += 1;
        } else {
            if current_write_row >= 0 {
                final_grid[current_write_row as usize] = grid[y];
            }
            current_write_row -= 1;
        }
    }
    melted = melted_count;

    for y in 0..height as usize {
        let mut last_cell = 1;
        for x in 0..width {
            let cell = (final_grid[y] >> x) & 1;
            if last_cell != cell {
                row_transitions += 1;
            }
            last_cell = cell;
        }
        if last_cell == 0 {
            row_transitions += 1;
        }
    }

    for x in 0..width {
        let mut mark = 0;
        let mut col_cells = 0;
        let mut wells = 0;
        let mut last_cell = 0;
        for y in 0..height as usize {
            let cell = (final_grid[y] >> x) & 1;
            if last_cell != cell {
                column_transitions += 1;
            }
            last_cell = cell;

            let is_well = if x == 0 {
                cell == 0 && (final_grid[y] >> 1 & 1) == 1
            } else if x == width - 1 {
                cell == 0 && (final_grid[y] >> (x - 1) & 1) == 1
            } else {
                cell == 0
                    && (final_grid[y] >> (x - 1) & 1) == 1
                    && (final_grid[y] >> (x + 1) & 1) == 1
            };

            if is_well {
                wells += 1;
            } else if wells > 0 {
                well_sums += (1 + wells) * wells / 2;
                wells = 0;
            }

            if cell == 1 {
                col_cells += 1;
                if mark == 0 {
                    mark = y as i32;
                }
            }
        }
        if wells > 0 {
            well_sums += (1 + wells) * wells / 2;
        }
        if col_cells > 0 {
            number_of_holes += height - mark - col_cells;
        }
        if last_cell == 0 {
            column_transitions += 1;
        }
    }

    let s = TETROMINOES[tetris_idx][try_num];
    let landing_height = (20.0 - (try_y as f64 + s.height as f64)) + (s.height as f64 - 1.0) / 2.0;

    weights[0] * landing_height
        + weights[1] * melted as f64
        + weights[2] * row_transitions as f64
        + weights[3] * column_transitions as f64
        + weights[4] * number_of_holes as f64
        + weights[5] * well_sums as f64
}

// --- 遗传算法逻辑 ---

fn run_game_for_training(weights: &[f64], provider: Box<dyn PieceProvider>) -> i32 {
    let mut lines_cleared = 0;
    let mut model = TetrisModel::new(GRID_WIDTH, GRID_HEIGHT, weights, provider);

    for _ in 0..GAME_LIMIT {
        if !model.in_game {
            break;
        }
        let (_, best_x, best_y, best_num) = model.solve();

        model.move_x = best_x;
        model.move_y = best_y;
        model.shape_idx = best_num;

        model.save();
        lines_cleared += model.try_melt();

        if model.in_game {
            model.new_tetris();
        }
    }
    lines_cleared
}

fn initialize_population() -> Vec<Vec<f64>> {
    let mut rng = thread_rng();
    (0..POPULATION_SIZE)
        .map(|_| (0..NUM_WEIGHTS).map(|_| rng.gen_range(-1.0..1.0)).collect())
        .collect()
}

fn calculate_fitness_parallel(population: &[Vec<f64>]) -> Vec<f64> {
    population
        .par_iter()
        .map(|weights| {
            let seed1 = rand::thread_rng().next_u64();
            let provider1 = Box::new(TetrisRandom::new(seed1));
            let score1 = run_game_for_training(weights, provider1);

            let seed2 = rand::thread_rng().next_u64();
            let provider2 = Box::new(TetrisRandom::new(seed2));
            let score2 = run_game_for_training(weights, provider2);

            let seed3 = rand::thread_rng().next_u64();
            let provider3 = Box::new(TetrisRandom::new(seed3));
            let score3 = run_game_for_training(weights, provider3);
            
            (score1 as f64 + score2 as f64 + score3 as f64) / 3.0
        })
        .collect()
}

#[derive(Clone)]
struct Individual {
    weights: Vec<f64>,
    fitness: f64,
}

fn selection(population: Vec<Vec<f64>>, fitness_scores: &[f64]) -> Vec<Vec<f64>> {
    let mut individuals: Vec<Individual> = population
        .into_iter()
        .zip(fitness_scores.iter())
        .map(|(weights, &fitness)| Individual { weights, fitness })
        .collect();

    individuals.sort_by(|a, b| b.fitness.partial_cmp(&a.fitness).unwrap());

    let num_elites = (ELITISM_PERCENT * POPULATION_SIZE as f64).round() as usize;
    let mut next_generation: Vec<Vec<f64>> = individuals
        .iter()
        .take(num_elites)
        .map(|ind| ind.weights.clone())
        .collect();

    let min_fitness = individuals.iter().map(|i| i.fitness).fold(f64::INFINITY, f64::min);
    let fitness_weights: Vec<f64> = individuals
        .iter()
        .map(|i| {
            let weight = if min_fitness < 0.0 { i.fitness - min_fitness } else { i.fitness };
            if weight > 0.0 { weight } else { 1.0 } // Ensure non-zero weight
        })
        .collect();

    let mut rng = thread_rng();
    while next_generation.len() < POPULATION_SIZE {
        let p1 = roulette_wheel_select(&individuals, &fitness_weights, &mut rng);
        let p2 = roulette_wheel_select(&individuals, &fitness_weights, &mut rng);

        let mut child = if rng.gen::<f64>() < CROSSOVER_RATE {
            let point = rng.gen_range(1..NUM_WEIGHTS);
            let mut c = p1.weights.clone();
            c[point..].copy_from_slice(&p2.weights[point..]);
            c
        } else {
            if rng.gen::<f64>() < 0.5 { p1.weights.clone() } else { p2.weights.clone() }
        };

        for w in &mut child {
            if rng.gen::<f64>() < MUTATION_RATE {
                *w += rng.gen_range(-1.0..1.0) * MUTATION_MAGNITUDE;
            }
        }
        next_generation.push(child);
    }

    next_generation
}

fn roulette_wheel_select<'a, R: Rng>(
    individuals: &'a [Individual],
    weights: &[f64],
    rng: &mut R,
) -> &'a Individual {
    let total_weight: f64 = weights.iter().sum();
    let mut r = rng.gen::<f64>() * total_weight;

    for (i, w) in weights.iter().enumerate() {
        r -= w;
        if r <= 0.0 {
            return &individuals[i];
        }
    }
    &individuals[individuals.len() - 1]
}

fn verify_performance(game_limit: u32, weights: &[f64], seed: u64) {
    println!("Running verification with {} blocks and seed {}...", game_limit, seed);
    let start_time = Instant::now();

    let provider = Box::new(LcgRandom::new(seed));
    let mut model = TetrisModel::new(GRID_WIDTH, GRID_HEIGHT, weights, provider);
    let mut lines_cleared = 0;

    for i in 0..game_limit {
        if !model.in_game {
            println!("Game over after {} pieces.", i);
            break;
        }
        let (_, best_x, best_y, best_num) = model.solve();

        model.move_x = best_x;
        model.move_y = best_y;
        model.shape_idx = best_num;

        model.save();
        lines_cleared += model.try_melt();

        if model.in_game {
            model.new_tetris();
        }
    }

    let duration = start_time.elapsed();
    println!("Verification finished.");
    println!("Total pieces: {}, Total lines cleared: {}", model.count.saturating_sub(1), lines_cleared);
    println!("Total time: {:.2?}", duration);
}

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Run performance verification instead of training
    #[arg(short, long)]
    verify: bool,

    /// Number of blocks for verification game
    #[arg(short, long, default_value_t = 1_000_000)]
    limit: u32,

    /// Seed for verification game
    #[arg(short, long, default_value_t = 12345)]
    seed: u64,

    /// Number of generations to iterate for training
    #[arg(short = 'g', long, default_value_t = 20)]
    generations: u32,
}

fn main() {
    let args = Args::parse();

    if args.verify {
        // Hardcoded weights from tetris.py for verification
        let python_weights: Vec<f64> = vec![
            // -4.500158825082766, // LandingHeight
            // 3.4181268101392694, // melted
            // -3.2178882868487753, // RowTransitions
            // -9.348695305445199, // ColumnTransitions
            // -7.899265427351652, // NumberOfHoles
            // -3.3855972247263626, // WellSums

            // -0.6365146060448055, 0.684445809747336, -0.3857237764989978, -1.3645038100517701, -0.6600842832984106, -0.41315261503740774,
            -0.8229968113792483, 0.3816371409567763, -0.3822535695191802, -1.6210899838124477, -0.7829249929709147, -0.524241666771028,
        ];
        verify_performance(args.limit, &python_weights, args.seed);
    } else {
        println!("Starting Rust version of Tetris GA training...");
        let mut population = initialize_population();

        let bar = ProgressBar::new(args.generations as u64);
        bar.set_style(ProgressStyle::default_bar()
            .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} (ETA: {eta})")
            .unwrap()
            .progress_chars("#>-"));

        for gen in 0..args.generations {
            let start_time = Instant::now();
            
            let fitness_scores = calculate_fitness_parallel(&population);

            let (best_fitness, best_weights_idx) = fitness_scores
                .iter()
                .enumerate()
                .fold((-1.0, 0), |(max_f, max_i), (i, &f)| {
                    if f > max_f { (f, i) } else { (max_f, max_i) }
                });
            
            let best_weights = population[best_weights_idx].clone();
            
            population = selection(population, &fitness_scores);
            
            let duration = start_time.elapsed();
            
            bar.inc(1);
            
            bar.suspend(|| {
                println!("\n--- Generation {}/{} ---", gen + 1, args.generations);
                println!("Generation Time: {:.2?}", duration);
                println!("Best Fitness (avg lines cleared): {:.2}", best_fitness);
                println!("Best Weights: {:?}", best_weights);
            });
        }
        bar.finish_with_message("Training finished");


        println!("\n--- Finding best individual in final population ---");
        let final_fitness = calculate_fitness_parallel(&population);
        let (best_fitness, best_weights_idx) = final_fitness
            .iter()
            .enumerate()
            .fold((-1.0, 0), |(max_f, max_i), (i, &f)| {
                if f > max_f { (f, i) } else { (max_f, max_i) }
            });
        
        let final_best_weights = &population[best_weights_idx];
        println!("Final best fitness: {:.2}", best_fitness);
        println!("Final best weights found: {:?}", final_best_weights);
    }
}
