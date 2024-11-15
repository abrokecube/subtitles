CENTER = [[
1030,570
]]

SCALE_PERCENT = 120


function stringToXY(str)
    local x, y = str:gsub("%s+", ""):match("([^,]+),([^,]+)")
    x = tonumber(x)
    y = tonumber(y)
    return x, y
end

x,y = stringToXY(CENTER)
factor = SCALE_PERCENT / 100

lx,ly = get('pos')
lx = ((lx - x) * factor) + x
ly = ((ly - y) * factor) + y
modify('pos', rep(lx,ly))

mod('fscx', mul(factor))
mod('fscy', mul(factor))
mod('bord', mul(factor))
mod('shad', mul(factor))

local lx1, ly1, lx2, ly2 = get('clip')
if type(lx1) ~= "string" then
    lx1 = ((lx1 - x) * factor) + x
    ly1 = ((ly1 - y) * factor) + y
    lx2 = ((lx2 - x) * factor) + x
    ly2 = ((ly2 - y) * factor) + y
    mod('clip', rep(lx1, ly1, lx2, ly2))
end