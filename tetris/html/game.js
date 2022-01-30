$(function () {
    $("#speed_slider").slider({
        min: 1,
        max: 100,
        change: function (event, ui) {
            wait_interval = 1000 / parseInt($("#speed_slider").slider("value"));
            $("#speed").val(ui.value);
        },
        slide: function (event, ui) {
            wait_interval = 1000 / parseInt($("#speed_slider").slider("value"));
            $("#speed").val(ui.value);
        },
        value: 16,
    });
    $("#speed").val($("#speed_slider").slider("value"));
    wait_interval = 1000 / parseInt($("#speed_slider").slider("value"));
    $("#play").button({
        text: false,
        icons: {
            primary: "ui-icon-play"
        }
    }).click(function () {
        var options;
        if ($(this).text() === "play") {
            // Un-pause the game
            paused = false;

            // if (game_started) {
            //     play();
            // } else {
            //     startGame(parseInt($("#num_columns").val()),
            //         parseInt($("#num_rows").val()));
            // }
            options = {
                label: "pause",
                icons: {
                    primary: "ui-icon-pause"
                }
            };
        } else {
            paused = true;
            options = {
                label: "play",
                icons: {
                    primary: "ui-icon-play"
                }
            };
        }
        $(this).button("option", options);
    });

    $("#stop").button({
        text: false,
        icons: {
            primary: "ui-icon-stop"
        }
    }).click(function () {
        paused = true;
        game_started = false;
        enableSliders();
        $("#play").button("option", {
            label: "play",
            icons: {
                primary: "ui-icon-play"
            }
        });
    });

    $("#debug").button().click(function () {
        debug();
    });
});


function GameView(w, h, squareSize) {
    this.height = h;
    this.width = w;
    this.squareSize = squareSize;
    this.context = document.getElementById('grid').getContext("2d");
}

GameView.prototype.drawGrid = function () {
    this.context.beginPath();
    for (var x = 0, i = 0; i <= this.width; x += this.squareSize, i++) {
        this.context.moveTo(x, 0);
        this.context.lineTo(x, this.height * this.squareSize);
    }
    for (var y = 0, i = 0; i <= this.height; y += this.squareSize, i++) {
        this.context.moveTo(0, y);
        this.context.lineTo(this.width * this.squareSize, y);
    }
    this.context.strokeStyle = "#eee";
    this.context.stroke();
};

GameView.prototype.fill_cell = function (x, y, color, clear) {
    if (clear) {
        this.context.clearRect(
            (x * this.squareSize) + 1,
            (y * this.squareSize) + 1,
            this.squareSize - 2,
            this.squareSize - 2);
    }
    else {
        this.context.fillStyle = color;
        this.context.fillRect(
            (x * this.squareSize) + 1,
            (y * this.squareSize) + 1,
            this.squareSize - 2,
            this.squareSize - 2);
    }
};

GameView.prototype.draw_shape = function (x, y, shape, color, clear) {
    for (var h = 0; h < shape.height; h++) {
        for (var w = 0; w < shape.width; w++) {
            // console.info("shape cell: ", h, w, (shape.shape[h] >> w) & 1);
            if (shape.shape[h] >> w & 1) {
                this.fill_cell(x + w, y + h, color, clear);
            }
        }
    }
};

GameView.prototype.redraw = function (model) {
    // console.info("redraw", Date.now())
    this.context.clearRect(0, 0, 300, 600);
    this.drawGrid();
    for (var h = 0; h < model.height; h++) {
        for (var w = 0; w < model.width; w++) {
            if (model.grid[h] >> w & 1) {
                this.fill_cell(w, h, "#ff0000", false);
            }
        }
    }
};

GameView.prototype.melt_tile = function (x, y, shape, color, clear) {
    for (var h = 0; h < shape.height; h++) {
        for (var w = 0; w < shape.width; w++) {
            // console.info("shape cell: ", h, w, (shape.shape[h] >> w) & 1);
            if (shape.shape[h] >> w & 1) {
                this.fill_cell(x + w, y + h, color, clear);
            }
        }
    }
};

var COLORS = new Array();
var model = new TetrisModel(10, 20);
var game_view = new GameView(10, 20, 30);
game_view.drawGrid();
var wait_interval = parseInt($("#speed_slider").slider("value"));

function enableSliders() {
    // for (var i = 0; i < 6; i++)
    //     game_view.draw_shape(i * 2, i * 3, T[i][0], "#00ff00")
    s = model.get_tetris()
    console.info(s)
    game_view.draw_shape(model.move_x, model.move_y, s, "#00ff00", false)
}


function debug() {
    console.info("debug", Date.now())
    // s = model.get_tetris()
    // game_view.draw_shape(model.move_x, model.move_y, s, "#00ff00", true)
    // model.move(Direction.Down)
    // s = model.get_tetris()
    // // console.info(s)
    // game_view.draw_shape(model.move_x, model.move_y, s, "#00ff00", false)
    setTimeout(on_timer, wait_interval);
}

var px = -100
var py = -100
var ps = undefined

function update() {
    // console.info("update", Date.now())
    {
        previous = model.previous()
        px = previous.x
        py = previous.y
        s = previous.shape
        game_view.draw_shape(px, py, s, "#00ff00", true)
        s = model.get_tetris()
        // console.info(s)
        game_view.draw_shape(model.move_x, model.move_y, s, "#00ff00", false)
    }
}

var start = new Date;

function on_timer() {
    // console.info((new Date - start) / 1000 + " Seconds");
    if (model.in_game) {
        if (model.pause_move)
            return;
        if (model.move(Direction.Down)) {
            this.update()
        }
        else {
            model.save()
            melted = model.try_melt()
            game_view.redraw(model)
            model.new_tetris()
        }
    }
    // else {
    //     this.game_over()
    // }
    setTimeout(on_timer, wait_interval);
}

function on_keypressed(event) {
    console.info("on_keypress...", event)
    const keyDown = ["KeyD", "ArrowDown"];
    const keyLeft = ["KeyS", "ArrowLeft"];
    const keyRight = ["KeyF", "ArrowRight"];
    const keyRotate = ["KeyJ", "ArrowUp"];
    if (keyLeft.includes(event.code)) {
        console.info("left...")
        if (model.move(Direction.Left))
           this.update()
    }
    else if (keyRight.includes(event.code)) {
        console.info("right...")
        if (model.move(Direction.Right))
           this.update()
    }
    else if (keyDown.includes(event.code)) {
        console.info("down...")
        if (model.move(Direction.Down))
           this.update()
    }
    else if (keyRotate.includes(event.code)) {
        console.info("rotate...")
        if (model.rotate())
            this.update()
    }
}

