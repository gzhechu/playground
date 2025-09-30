package main

import (
	"flag"
	"fmt"
	"math/rand"
	"runtime"
	"sort"
	"sync"
	"time"
)

// --- 遗传算法的超参数 (Hyperparameters) ---
const (
	PopulationSize    = 128      // 种群大小
	NumWeights        = 6        // 权重的数量
	CrossoverRate     = 0.8      // 交叉率
	NumGenerations    = 100      // 迭代多少代
	ElitismPercent    = 0.1      // 保留多少比例的精英
	GameLimit         = 10000000 // 每局游戏最多放置的方块数
	MutationRate      = 0.25     // 变异率 (已调高)
	MutationMagnitude = 0.4      // 变异范围 (已调高)
)

// --- Tetris 游戏常量 ---
const (
	GridWidth  = 10
	GridHeight = 20
)

// ShapeInfo 对应 Python 中 T 列表里的每个方块的旋转信息
type ShapeInfo struct {
	Shape  []int
	Width  int
	Height int
}

// Tetrominoes 对应 Python 中的 T 列表
var Tetrominoes = [][]*ShapeInfo{
	{ // I
		{Shape: []int{1, 1, 1, 1}, Width: 1, Height: 4},
		{Shape: []int{15}, Width: 4, Height: 1},
	},
	{ // T
		{Shape: []int{2, 7}, Width: 3, Height: 2},
		{Shape: []int{2, 3, 2}, Width: 2, Height: 3},
		{Shape: []int{7, 2}, Width: 3, Height: 2},
		{Shape: []int{1, 3, 1}, Width: 2, Height: 3},
	},
	{ // O
		{Shape: []int{3, 3}, Width: 2, Height: 2},
	},
	{ // L
		{Shape: []int{2, 2, 3}, Width: 2, Height: 3},
		{Shape: []int{7, 4}, Width: 3, Height: 2},
		{Shape: []int{3, 1, 1}, Width: 2, Height: 3},
		{Shape: []int{1, 7}, Width: 3, Height: 2},
	},
	{ // J
		{Shape: []int{7, 1}, Width: 3, Height: 2},
		{Shape: []int{1, 1, 3}, Width: 2, Height: 3},
		{Shape: []int{4, 7}, Width: 3, Height: 2},
		{Shape: []int{3, 2, 2}, Width: 2, Height: 3},
	},
	{ // Z
		{Shape: []int{6, 3}, Width: 3, Height: 2},
		{Shape: []int{1, 3, 2}, Width: 2, Height: 3},
	},
	{ // S
		{Shape: []int{3, 6}, Width: 3, Height: 2},
		{Shape: []int{2, 3, 1}, Width: 2, Height: 3},
	},
}

// --- Tetris 游戏模型 ---

// PieceProvider 定义了任何方块生成器都需要满足的接口
type PieceProvider interface {
	Next() int
}

// TetrisRandom 实现了 "7-bag" 随机生成算法
type TetrisRandom struct {
	pool []int
	src  rand.Source
	mu   sync.Mutex
}

// NewTetrisRandom 创建一个 "7-bag" 生成器，使用给定的种子
func NewTetrisRandom(seed int64) *TetrisRandom {
	src := rand.NewSource(seed)
	return &TetrisRandom{pool: []int{}, src: src}
}

func (r *TetrisRandom) Next() int {
	r.mu.Lock()
	defer r.mu.Unlock()

	if len(r.pool) == 0 {
		// 7 bags of 7 tetrominos
		newPool := make([]int, 49)
		for i := 0; i < 49; i++ {
			newPool[i] = i % 7
		}
		// Shuffle
		rnd := rand.New(r.src)
		rnd.Shuffle(len(newPool), func(i, j int) {
			newPool[i], newPool[j] = newPool[j], newPool[i]
		})
		r.pool = newPool
	}
	next := r.pool[len(r.pool)-1]
	r.pool = r.pool[:len(r.pool)-1]
	return next
}

// SimpleRandom 实现了纯粹的伪随机生成算法（非 "7-bag"）
type SimpleRandom struct {
	rnd *rand.Rand
	mu  sync.Mutex
}

// NewSimpleRandom 创建一个简单的伪随机生成器，使用给定的种子
func NewSimpleRandom(seed int64) *SimpleRandom {
	src := rand.NewSource(seed)
	return &SimpleRandom{rnd: rand.New(src)}
}

func (r *SimpleRandom) Next() int {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.rnd.Intn(7)
}

// TetrisModel 翻译自 Python 的 TetrisModel 类
type TetrisModel struct {
	Width            int
	Height           int
	Grid             []int
	InGame           bool
	Count            int
	TetrisIdx        int
	NextTetris       int
	ShapeIdx         int
	MoveX            int
	MoveY            int
	Weights          []float64 // 权重，用于可训练的模型
	pieceProvider    PieceProvider
	evaluationBuffer []int
	solveBuffer      []int
}

func NewTrainableTetrisModel(w, h int, weights []float64, provider PieceProvider) *TetrisModel {
	m := &TetrisModel{
		Width:            w,
		Height:           h,
		Grid:             make([]int, h),
		InGame:           true,
		Weights:          weights,
		pieceProvider:    provider,
		evaluationBuffer: make([]int, h),
		solveBuffer:      make([]int, h),
	}
	m.NextTetris = m.pieceProvider.Next()
	m.NewTetris()
	return m
}

func (m *TetrisModel) NewTetris() {
	m.Count++
	m.TetrisIdx = m.NextTetris
	m.ShapeIdx = 0
	m.NextTetris = m.pieceProvider.Next()
	m.MoveX = m.Width/2 - 1
	m.MoveY = 0
}

func (m *TetrisModel) Collided(x, y, num int) bool {
	if x < 0 {
		return true
	}
	s := Tetrominoes[m.TetrisIdx][num]
	if x > m.Width-s.Width {
		return true
	}
	if y > m.Height-s.Height {
		return true
	}
	for h := 0; h < s.Height; h++ {
		if (s.Shape[h]<<x)&m.Grid[y+h] != 0 {
			return true
		}
	}
	return false
}

func (m *TetrisModel) Save() {
	s := Tetrominoes[m.TetrisIdx][m.ShapeIdx]
	for h := 0; h < s.Height; h++ {
		m.Grid[h+m.MoveY] |= s.Shape[h] << m.MoveX
	}
	if m.Grid[0] > 0 {
		m.InGame = false
	}
}

func (m *TetrisModel) TryMelt() int {
	meltedCount := 0
	h := m.Height - 1
	for h > 0 {
		if (1<<m.Width)-1 == m.Grid[h] {
			meltedCount++
			for y := h; y > 0; y-- {
				m.Grid[y] = m.Grid[y-1]
			}
			m.Grid[0] = 0
		} else {
			h--
		}
	}
	return meltedCount
}

// Evaluate 评估函数，最核心的 AI 逻辑
func (m *TetrisModel) Evaluate(grid []int, tryX, tryY, tryNum int) float64 {
	landingHeight := 0.0
	rowTransitions := 0
	columnTransitions := 0
	numberOfHoles := 0
	wellSums := 0

	// --- Optimization: Use pre-allocated buffer to avoid allocation ---
	finalGrid := m.evaluationBuffer
	// Clear buffer before use
	for i := range finalGrid {
		finalGrid[i] = 0
	}

	// Virtual melting: build finalGrid from bottom up, skipping full rows
	melted := 0
	fullRowMask := (1 << m.Width) - 1

	currentWriteRow := m.Height - 1
	for y := m.Height - 1; y >= 0; y-- {
		if grid[y] == fullRowMask { // Check if row is full
			melted++
		} else {
			if currentWriteRow >= 0 {
				finalGrid[currentWriteRow] = grid[y]
			}
			currentWriteRow--
		}
	}

	// 计算各项指标 (现在使用 finalGrid)
	for y := 0; y < m.Height; y++ {
		lastCell := 1
		for x := 0; x < m.Width; x++ {
			cell := (finalGrid[y] >> x) & 1
			if lastCell != cell {
				rowTransitions++
			}
			lastCell = cell
		}
		if lastCell == 0 {
			rowTransitions++
		}
	}

	for x := 0; x < m.Width; x++ {
		mark := 0
		colCells := 0
		wells := 0
		lastCell := 0
		for y := 0; y < m.Height; y++ {
			cell := (finalGrid[y] >> x) & 1
			if lastCell != cell {
				columnTransitions++
			}
			lastCell = cell

			isWell := false
			if x == 0 {
				if cell == 0 && (finalGrid[y]>>1&1) == 1 {
					isWell = true
				}
			} else if x == m.Width-1 {
				if cell == 0 && (finalGrid[y]>>(x-1)&1) == 1 {
					isWell = true
				}
			} else {
				if cell == 0 && (finalGrid[y]>>(x-1)&1) == 1 && (finalGrid[y]>>(x+1)&1) == 1 {
					isWell = true
				}
			}

			if isWell {
				wells++
			} else if wells > 0 {
				wellSums += (1 + wells) * wells / 2
				wells = 0
			}

			if cell == 1 {
				colCells++
				if mark == 0 {
					mark = y
				}
			}
		}
		if wells > 0 {
			wellSums += (1 + wells) * wells / 2
		}
		if colCells > 0 {
			numberOfHoles += (m.Height - mark - colCells)
		}
		if lastCell == 0 {
			columnTransitions++
		}
	}

	s := Tetrominoes[m.TetrisIdx][tryNum]
	lh := float64(20 - (tryY + s.Height))
	landingHeight = lh + float64(s.Height-1)/2.0

	// 使用传入的权重计算分数
	score := m.Weights[0]*landingHeight +
		m.Weights[1]*float64(melted) +
		m.Weights[2]*float64(rowTransitions) +
		m.Weights[3]*float64(columnTransitions) +
		m.Weights[4]*float64(numberOfHoles) +
		m.Weights[5]*float64(wellSums)

	return score
}

// Solve 找到当前方块的最佳落点
func (m *TetrisModel) Solve() (bestScore float64, bestX, bestY, bestNum int) {
	bestScore = -1e9 // A very small number
	t := Tetrominoes[m.TetrisIdx]
	tempGrid := m.solveBuffer // Use the pre-allocated buffer

	for idx := 0; idx < len(t); idx++ {
		s := t[idx]
		for x := 0; x <= m.Width-s.Width; x++ {
			y := 0
			// Find the lowest possible y
			for !m.Collided(x, y+1, idx) {
				y++
			}

			// Use the buffer instead of creating a new grid
			copy(tempGrid, m.Grid)
			for h := 0; h < s.Height; h++ {
				tempGrid[h+y] |= s.Shape[h] << x
			}

			r := m.Evaluate(tempGrid, x, y, idx)
			if r > bestScore {
				bestScore = r
				bestX = x
				bestY = y
				bestNum = idx
			}
		}
	}
	return
}

// --- 遗传算法逻辑 ---

// RunGameForTraining 运行一局无界面的游戏，返回消行数
func RunGameForTraining(weights []float64, provider PieceProvider) int {
	linesCleared := 0
	model := NewTrainableTetrisModel(GridWidth, GridHeight, weights, provider)

	for i := 0; i < GameLimit && model.InGame; i++ {
		_, bestX, bestY, bestNum := model.Solve()

		model.MoveX = bestX
		model.MoveY = bestY
		model.ShapeIdx = bestNum

		model.Save()
		melted := model.TryMelt()
		linesCleared += melted

		if model.InGame {
			model.NewTetris()
		}
	}
	return linesCleared
}

// InitializePopulation 初始化种群
func InitializePopulation() [][]float64 {
	population := make([][]float64, PopulationSize)
	for i := range population {
		weights := make([]float64, NumWeights)
		for j := range weights {
			weights[j] = rand.Float64()*2 - 1 // Random float between -1.0 and 1.0
		}
		population[i] = weights
	}
	return population
}

// Job and Result structs for ordered parallel execution
type Job struct {
	Index   int
	Weights []float64
}
type Result struct {
	Index   int
	Fitness float64
}

// CalculateFitnessParallel 使用 Goroutines 并行计算适应度
func CalculateFitnessParallel(population [][]float64) []float64 {
	numJobs := len(population)
	jobCh := make(chan Job, numJobs)
	resultCh := make(chan Result, numJobs)

	numWorkers := runtime.NumCPU()
	for w := 0; w < numWorkers; w++ {
		go func() {
			for job := range jobCh {
				// 为每场游戏创建一个新的随机 provider
				provider1 := NewTetrisRandom(time.Now().UnixNano())
				score1 := RunGameForTraining(job.Weights, provider1)

				provider2 := NewTetrisRandom(time.Now().UnixNano())
				score2 := RunGameForTraining(job.Weights, provider2)
				resultCh <- Result{Index: job.Index, Fitness: (float64(score1) + float64(score2)) / 2.0}
			}
		}()
	}

	for i, p := range population {
		jobCh <- Job{Index: i, Weights: p}
	}
	close(jobCh)

	fitnessScores := make([]float64, numJobs)
	for i := 0; i < numJobs; i++ {
		result := <-resultCh
		fitnessScores[result.Index] = result.Fitness
	}
	return fitnessScores
}

// Individual 用于排序
type Individual struct {
	Weights []float64
	Fitness float64
}

// Selection 选择、交叉和变异来产生下一代
func Selection(population [][]float64, fitnessScores []float64) [][]float64 {
	// --- 轮盘赌选择的权重准备 ---
	minFitness := 0.0
	if len(fitnessScores) > 0 {
		minFitness = fitnessScores[0]
		for _, score := range fitnessScores {
			if score < minFitness {
				minFitness = score
			}
		}
	}
	fitnessWeights := make([]float64, len(fitnessScores))
	var totalWeight float64
	for i, score := range fitnessScores {
		weight := 0.0
		if minFitness < 0 {
			weight = score - minFitness
		} else {
			weight = score
		}
		fitnessWeights[i] = weight
		totalWeight += weight
	}
	if totalWeight == 0 {
		for i := range fitnessWeights {
			fitnessWeights[i] = 1.0
		}
	}

	// --- 精英选择 ---
	individuals := make([]Individual, len(population))
	for i := range population {
		individuals[i] = Individual{Weights: population[i], Fitness: fitnessScores[i]}
	}
	sort.Slice(individuals, func(i, j int) bool {
		return individuals[i].Fitness > individuals[j].Fitness
	})

	floatNumElites := ElitismPercent * float64(PopulationSize)
	numElites := int(floatNumElites)
	nextGeneration := make([][]float64, 0, PopulationSize)
	for i := 0; i < numElites && i < len(individuals); i++ {
		// Deep copy
		eliteCopy := make([]float64, NumWeights)
		copy(eliteCopy, individuals[i].Weights)
		nextGeneration = append(nextGeneration, eliteCopy)
	}

	// --- 繁殖后代 ---
	for len(nextGeneration) < PopulationSize {
		// 轮盘赌选择父母
		p1 := rouletteWheelSelect(population, fitnessWeights)
		p2 := rouletteWheelSelect(population, fitnessWeights)

		var child []float64
		if rand.Float64() < CrossoverRate {
			point := rand.Intn(NumWeights-1) + 1
			child = make([]float64, NumWeights)
			copy(child[:point], p1[:point])
			copy(child[point:], p2[point:])
		} else {
			child = make([]float64, NumWeights)
			if rand.Float64() < 0.5 {
				copy(child, p1)
			} else {
				copy(child, p2)
			}
		}

		// 变异
		for i := 0; i < NumWeights; i++ {
			if rand.Float64() < MutationRate {
				child[i] += (rand.Float64()*2 - 1) * MutationMagnitude
			}
		}
		nextGeneration = append(nextGeneration, child)
	}
	return nextGeneration
}

func rouletteWheelSelect(population [][]float64, weights []float64) []float64 {
	totalWeight := 0.0
	for _, w := range weights {
		totalWeight += w
	}
	r := rand.Float64() * totalWeight
	for i, w := range weights {
		r -= w
		if r <= 0 {
			return population[i]
		}
	}
	return population[len(population)-1]
}

func verifyPerformance(gameLimit int, weights []float64, seed int64) {
	fmt.Printf("Running verification with %d blocks and seed %d...\n", gameLimit, seed)

	startTime := time.Now()

	linesCleared := 0
	// 使用 SimpleRandom 创建一个确定性的、非 7-bag 的序列
	provider := NewSimpleRandom(seed)
	model := NewTrainableTetrisModel(GridWidth, GridHeight, weights, provider)

	for i := 0; i < gameLimit && model.InGame; i++ {
		_, bestX, bestY, bestNum := model.Solve()

		model.MoveX = bestX
		model.MoveY = bestY
		model.ShapeIdx = bestNum

		model.Save()
		melted := model.TryMelt()
		linesCleared += melted

		if model.InGame {
			model.NewTetris()
		}
	}

	duration := time.Since(startTime)
	fmt.Printf("Verification finished.\n")
	fmt.Printf("Total blocks: %d, Total lines cleared: %d\n", gameLimit, linesCleared)
	fmt.Printf("Total time: %.2fs\n", duration.Seconds())
}

// --- 主函数 ---
func main() {
	verifyFlag := flag.Bool("verify", false, "Run performance verification instead of training.")
	limitFlag := flag.Int("limit", 1000000, "Number of blocks for verification game.")
	seedFlag := flag.Int64("seed", 12345, "Seed for verification game.")
	flag.Parse()

	if *verifyFlag {
		// Hardcoded weights from tetris.py for verification
		// pythonWeights := []float64{
		// 	-4.500158825082766, // LandingHeight
		// 	3.4181268101392694, // melted
		// 	-3.2178882868487753, // RowTransitions
		// 	-9.348695305445199, // ColumnTransitions
		// 	-7.899265427351652, // NumberOfHoles
		// 	-3.3855972247263626, // WellSums
		// }
		pythonWeights := []float64{
			-0.39413604554508086,
			1.2719295949626823,
			-0.22715173199605562,
			-1.0709336700132304,
			-0.12734757334004457,
			-0.18636589656874655,
		}

		// Run verification test
		verifyPerformance(*limitFlag, pythonWeights, *seedFlag)
	} else {
		rand.Seed(time.Now().UnixNano())
		fmt.Println("Starting Go version of Tetris GA training...")

		population := InitializePopulation()

		for gen := 0; gen < NumGenerations; gen++ {
			startTime := time.Now()
			fmt.Printf("\n--- Generation %d/%d ---\n", gen+1, NumGenerations)

			fitnessScores := CalculateFitnessParallel(population)

			bestFitness := -1.0
			bestWeightsIdx := -1
			for i, score := range fitnessScores {
				if score > bestFitness {
					bestFitness = score
					bestWeightsIdx = i
				}
			}
			bestWeights := population[bestWeightsIdx]

			population = Selection(population, fitnessScores)

			duration := time.Since(startTime)

			fmt.Printf("Generation Time: %.2fs\n", duration.Seconds())
			fmt.Printf("Best Fitness (avg lines cleared): %.2f\n", bestFitness)
			fmt.Printf("Best Weights: %v\n", bestWeights)
		}

		fmt.Println("\n--- Training Finished ---")
		// 在最终种群上再跑一次评估，找到最好的那个
		finalFitness := CalculateFitnessParallel(population)
		bestFitness := -1.0
		bestWeightsIdx := -1
		for i, score := range finalFitness {
			if score > bestFitness {
				bestFitness = score
				bestWeightsIdx = i
			}
		}
		finalBestWeights := population[bestWeightsIdx]
		fmt.Print("Final best weights found: [")
		for i, w := range finalBestWeights {
			fmt.Printf("%f", w)
			if i < len(finalBestWeights)-1 {
				fmt.Print(" ")
			}
		}
		fmt.Println("]")
	}
}
