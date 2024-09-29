-- infinite y-blur using huge ybord
-- Uses shadtrick
-- Edit \4a on the resulting line to change opacity
-- Good on really low opacites

Y_CENTER = 1080/2
BORD_RAD = 600

mod('ybord', rep(BORD_RAD))


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
    mod("alpha", rep("&HFF&\\4a&H00&"))
end

x,y = get('pos')
modify('pos', rep(x, Y_CENTER))