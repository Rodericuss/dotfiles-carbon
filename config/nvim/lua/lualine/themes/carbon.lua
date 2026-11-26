-- Carbon lualine: mode chip in the mode color, sections on layer 01 / 02.
local dark = vim.o.background ~= 'light'
local c = dark and { bg='#161616', l1='#262626', l2='#393939', fg='#c6c6c6', text='#f2f4f8', dim='#6f6f6f',
  blue='#78a9ff', green='#42be65', purple='#be95ff', pink='#ee5396', teal='#3ddbd9', magenta='#ff7eb6' }
  or { bg='#ffffff', l1='#f4f4f4', l2='#e0e0e0', fg='#393939', text='#161616', dim='#8d8d8d',
  blue='#0f62fe', green='#198038', purple='#8a3ffc', pink='#da1e28', teal='#007d79', magenta='#d02670' }
local function mode(color)
  return { a={fg=c.bg,bg=color,gui='bold'}, b={fg=c.text,bg=c.l2}, c={fg=c.fg,bg=c.l1}, y={fg=c.fg,bg=c.l2}, z={fg=c.bg,bg=color} }
end
return {
  normal=mode(c.blue), insert=mode(c.green), visual=mode(c.purple), replace=mode(c.pink),
  command=mode(c.teal), terminal=mode(c.magenta),
  inactive={ a={fg=c.dim,bg=c.l1}, b={fg=c.dim,bg=c.l1}, c={fg=c.dim,bg=c.l1} },
}
