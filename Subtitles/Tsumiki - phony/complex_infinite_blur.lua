SAMPLES = 5

BORD_RAD = 600
Y_CENTER = 1080/2

REAL_BLUR_AMNT = 0

-- ----- HOW TO DO THE EFFECT -----
-- Add a rect clip around your text
-- Run script
-- Open Shapery > Pathfinder and select Intersect
-- Make sure multiline is deselected
-- Click Ok

-- To REDUCE SHAPE COMPLEXITY:
-- Go to Shapery > Transform
-- Set Scale Ver. % to 1.0
-- Click Ok
-- Then go to Shapery > Manipulate
-- Uncheck Fit Curves and Execute on \clip
-- Set Tolerance to 10 and Angle Threshold to 100
-- (not sure if those settings do much)
-- Click on Simplify

if ((i-1) % SAMPLES) ~= (SAMPLES-1) then
    duplicate() 
end

local x1, y1, x2, y2 = get('clip')
local prog = ((i-1) % SAMPLES) / SAMPLES
local height = y2 - y1
local start_y = y1
y1 = start_y + height * prog
y2 = y1 + height / SAMPLES
-- y1 = start_y + (height * prog) + (height/SAMPLES) / 2
-- y2 = y1 + 1

mod('clip', rep(x1, y1, x2, y2))
mod('ybord', rep(BORD_RAD))
if REAL_BLUR_AMNT > 0 then
    mod('blur', rep(REAL_BLUR_AMNT))
end

-- Shadtrick line
-- (original shadtrick script by witchymary)

local color = get("c")
rem("c")
rem("4c")

local alpha = 0
if get("1a") ~= "&H00&" then
    alpha = get("1a")
    rem("1a")
elseif get("alpha") ~= "&H00&" then
    alpha = get("alpha")
end
rem("alpha")

mod("ko", rep(0))
mod("shad", rep(0.01))
mod("4c", rep(color))
--mod("alpha", rep("&HFF&"))

rem("4a")
if alpha ~= 0 then 
    --mod("4a", rep(alpha))
    mod("alpha", rep(string.format("&HFF&\\4a%s", alpha)))
else
    --mod("4a", rep("&H00&"))
    mod("alpha", rep("&HFF&\\4a&HF4&"))
end


