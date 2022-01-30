
var T = new Array();
T[0] = [                                                // I
    { shape: [1, 1, 1, 1], width: 1, height: 4 },
    { shape: [15], width: 4, height: 1 }];
T[1] = [                                                // T
    { shape: [2, 7], width: 3, height: 2 },
    { shape: [2, 3, 2], width: 2, height: 3 },
    { shape: [7, 2], width: 3, height: 2 },
    { shape: [1, 3, 1], width: 2, height: 3 }];
T[2] = [                                                // O
    { shape: [3, 3], width: 2, height: 2 }];
T[3] = [                                                // L
    { shape: [2, 2, 3], width: 2, height: 3 },
    { shape: [7, 4], width: 3, height: 2 },
    { shape: [3, 1, 1], width: 2, height: 3 },
    { shape: [1, 7], width: 3, height: 2 }];
T[4] = [                                                // J
    { shape: [7, 1], width: 3, height: 2 },
    { shape: [1, 1, 3], width: 2, height: 3 },
    { shape: [4, 7], width: 3, height: 2 },
    { shape: [3, 2, 2], width: 2, height: 3 }];
T[5] = [                                                // Z
    { shape: [6, 3], width: 3, height: 2 },
    { shape: [1, 3, 2], width: 2, height: 3 }];
T[6] = [                                                // S
    { shape: [3, 6], width: 3, height: 2 },
    { shape: [2, 3, 1], width: 2, height: 3 }];


function TetrisModel(w, h) {
    this.width = w;
    this.height = h;
    this.rows_completed = 0;
    this.count = 0;
    this.tetris_idx = 0
    this.shape_idx = 0
    this.next_tetris = 5
    this.pause_move = false
    this.move_x = 3
    this.move_y = 0
    this.previous_x = this.move_x
    this.previous_y = this.move_y
    this.in_game = true

    // The board is represented as an array of integers, one integer for each row.
    this.grid = new Array(this.height);
    for (var i = 0; i < this.height; i++) {
        this.grid[i] = 0;
    }
    this.new_tetris()
    console.info(this.width, this.height)
}

TetrisModel.prototype.get_tetris = function () {
    // console.info("get_tetris", this.tetris_idx, this.shape_idx)
    return T[this.tetris_idx][this.shape_idx]
};

TetrisModel.prototype.previous = function () {
    // console.info("previous", this.tetris_idx, this.shape_idx)
    return { 'x': this.previous_x, 'y': this.previous_y, 'shape': T[this.tetris_idx][this.previous_idx] }
};

TetrisModel.prototype.new_tetris = function () {
    this.count += 1
    this.tetris_idx = this.next_tetris
    this.shape_idx = 0
    this.next_tetris = Math.floor(Math.random() * T.length);
    this.move_x = 3
    this.move_y = 0
    // console.info("new_tetris idx:", this.tetris_idx)
};

TetrisModel.prototype.collision_detect = function (x, y, idx) {
    if (x < 0)
        return true;
    var s;
    if (idx >= 0)
        s = T[this.tetris_idx][idx]
    else
        s = T[this.tetris_idx][this.shape_idx]
    if (x > this.width - s.width)
        return true;
    if (y > this.height - s.height)
        return true;
    for (var h = 0; h < s.height; h++)
        if (s.shape << x & this.grid[y + h] != 0)
            return true
    return false;
};

const Direction = {
    Up: 'Up',
    Down: 'Down',
    Left: 'Left',
    Right: 'Right'
};

TetrisModel.prototype.move = function (val) {
    ret = false;
    this.previous_x = this.move_x
    this.previous_y = this.move_y
    if (val === Direction.Left) {
        if (!this.collision_detect(this.move_x - 1, this.move_y, -1)) {
            this.move_x -= 1
            ret = true
        }
    }
    else if (val === Direction.Right) {
        if (!this.collision_detect(this.move_x + 1, this.move_y, -1)) {
            this.move_x += 1
            ret = true
        }
    }
    else if (val === Direction.Down) {
        if (!this.collision_detect(this.move_x, this.move_y + 1, -1)) {
            this.move_y += 1
            ret = true
        }
    }
    return ret
};

TetrisModel.prototype.rotate = function (val) {
    rotate = false
    this.previous_x = this.move_x
    this.previous_y = this.move_y
    s = T[this.tetris_idx]
    if (this.shape_idx >= s.length - 1)
        if (!this.collision_detect(this.move_x, this.move_y, 0)) {
            this.shape_idx = 0
            rotate = true
        }
        else if (!this.collided(this.moveX, this.moveY, this.shape_idx + 1)) {
            this.shape_idx += 1
            rotate = True
        }
    return rotate
}

TetrisModel.prototype.try_melt = function () {
    console.info("try_melt ... ")
    melted = []
    h = this.height - 1
    while (h > 0) {
        if (1 << this.width <= this.grid[h] + 1) {
            // # print("try_melt", h, grid[h])
            console.info("try_melt ... ", h, this.grid[h])
            melted.push(h)
            for (var y = h; y > 0; y--) {
                this.grid[y] = this.grid[y - 1]
            }
            h += 1
        }
        h -= 1
    }
    return melted
}

TetrisModel.prototype.save = function () {
    x = this.move_x
    y = this.move_y
    s = T[this.tetris_idx][this.shape_idx]
    for (var h = 0; h < s.height; h++) {
        this.grid[h + y] = this.grid[h + y] | (s.shape[h] << x)
    }
    console.info("save", this.grid)
    if (this.grid[0] > 0)
        this.in_game = false
};
