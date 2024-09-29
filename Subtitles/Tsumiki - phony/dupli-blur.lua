-- y-blur by duplicating lines and reducing alpha

SAMPLES = 5
BLUR_AMNT = 15
ALPHA_MULT = 1
NORMALIZE_OPACITY = true

-- BLUR_AMNT also accepts a table (array)
-- first input line maps to the first number in the table
-- second input line maps to the second number of the table
-- etc...



-- thanks ChatGPT
function gaussian(x, mu, sigma)
    local coeff = 1 / (sigma * math.sqrt(2 * math.pi))
    local exponent = -((x - mu) ^ 2) / (2 * sigma ^ 2)
    return coeff * math.exp(exponent)
end


function remove_non_hex_chars(input)
    local clean_string = input:gsub("[^0-9A-Fa-f]", "")
    return clean_string
end

function hex_to_num(hex_string)
    return tonumber(hex_string, 16)
end

if type(BLUR_AMNT) == "number" then
    BLUR_AMNT = {BLUR_AMNT,}
end

local blur_amnt_i = (math.floor((i-1) / SAMPLES) % #BLUR_AMNT + 1)
local curr_blur_amnt = BLUR_AMNT[blur_amnt_i]

local mu = 0     -- Mean
local sigma = curr_blur_amnt/2  -- Standard deviation
local x = 0      -- Input value

local alpha_raw = 0
if get("1a") ~= "&H00&" then
    alpha_raw = get("1a")
elseif get("alpha") ~= "&H00&" then
    alpha_raw = get("alpha")
end
if alpha_raw == 0 then
    alpha_raw = "&H00&"
end
local alpha = hex_to_num(remove_non_hex_chars(alpha_raw))

if ((i-1) % SAMPLES) ~= (SAMPLES-1) then
    duplicate() 
end
prog = ((i-1) % SAMPLES) / (SAMPLES-1)

pos.y = pos.y + (-curr_blur_amnt + prog*curr_blur_amnt*2)

if NORMALIZE_OPACITY then
    alpha = 255-((255-alpha) * gaussian((-curr_blur_amnt + prog*curr_blur_amnt*2), mu, sigma)*math.pi*2*(curr_blur_amnt/SAMPLES)*ALPHA_MULT)
else
    alpha = 255-((255-alpha) * gaussian((-curr_blur_amnt + prog*curr_blur_amnt*2), mu, sigma)*math.pi*2*(SAMPLES/(math.pi*2))*ALPHA_MULT)
end

mod('1a', rep(("&H%02X&"):format(math.max(math.min(alpha,255),0))))