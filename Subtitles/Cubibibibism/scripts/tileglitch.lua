SQUARE_X = 75
SQUARE_Y = 75
SEED = 237894
MULT = 7


X_MIN = -1 * MULT
Y_MIN = -1 * MULT
X_MAX = 1 * MULT
Y_MAX = 1 * MULT

local x1, y1, x2, y2 = get('clip')

local x_squares = math.ceil((x2 - x1) / SQUARE_X)+1
local y_squares = math.ceil((y2 - y1) / SQUARE_Y)+1

local total_squares = x_squares * y_squares

if not flags['last_end_i'] then
    flags['last_end_i'] = 1
end

local curr_i = i - flags['last_end_i']

math.randomseed(SEED)

if curr_i < total_squares-1 then
    duplicate()
else
    flags['last_end_i'] = i+1
end

local curr_row = math.floor(curr_i / x_squares)
local curr_col = math.ceil(curr_i % x_squares)

local min_x = x1
local min_y = y1
local max_x = x2
local max_y = y2
local clip_xshift = -(min_x % SQUARE_X) + math.random(-SQUARE_X, 0)
local clip_yshift = -(min_y % SQUARE_Y) + math.random(-SQUARE_Y, 0)

x1 = x1 + clip_xshift + curr_col * SQUARE_X
y1 = y1 + clip_yshift + curr_row * SQUARE_Y
x2 = math.min(x1 + SQUARE_X, max_x)
y2 = math.min(y1 + SQUARE_Y, max_y)
x1 = math.max(x1, min_x)
y1 = math.max(y1, min_y)

x1 = math.floor(x1)
y1 = math.floor(y1)
x2 = math.floor(x2)
y2 = math.floor(y2)

mod('clip', rep(x1, y1, x2, y2))

local randplus = math.floor(x1 / SQUARE_X) + math.floor(y1 / SQUARE_Y) * math.floor(1920 / SQUARE_X)
randplus = randplus + (X_MIN * Y_MIN * X_MAX * Y_MAX)

for a = 0, randplus do
    math.random()
end

local shift_x = math.random(X_MIN, X_MAX)
local shift_y = math.random(Y_MIN, Y_MAX)
mod('pos', add(shift_x, shift_y))