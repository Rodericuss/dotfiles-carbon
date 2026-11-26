-- carbon: Oxocarbon upgraded to IBM Carbon semantics.
-- Palette and spirit from nyoom-engineering/oxocarbon.nvim (MIT, (c) 2022 Riccardo Mazzarini).
-- Changes: Carbon layers (01/02/03) for UI depth, pink reserved for errors, readable comments,
-- neutral punctuation, a g10 light variant, square borderless floats and plugin coverage.
vim.cmd 'highlight clear'
if vim.fn.exists('syntax_on') == 1 then vim.cmd 'syntax reset' end
vim.o.termguicolors = true
vim.g.colors_name = 'carbon'

local dark = vim.o.background ~= 'light'
local p = dark and {
  bg='#161616', l1='#262626', l2='#393939', l3='#4c4c4c', hover='#333333',
  rule='#393939', strong='#6f6f6f', faint='#525252',
  fg='#dde1e6', text='#f2f4f8', text2='#c6c6c6', muted='#a8a8a8', dim='#6f6f6f',
  blue='#78a9ff', blue2='#a6c8ff', cyan='#33b1ff', sky='#82cfff', teal='#3ddbd9', teal2='#08bdba',
  purple='#be95ff', magenta='#ff7eb6', pink='#ee5396', green='#42be65', orange='#ff832b',
  on='#161616',
} or {
  bg='#ffffff', l1='#f4f4f4', l2='#e0e0e0', l3='#c6c6c6', hover='#e8e8e8',
  rule='#e0e0e0', strong='#8d8d8d', faint='#c6c6c6',
  fg='#262626', text='#161616', text2='#393939', muted='#525252', dim='#8d8d8d',
  blue='#0f62fe', blue2='#0043ce', cyan='#0072c3', sky='#00539a', teal='#007d79', teal2='#005d5d',
  purple='#8a3ffc', magenta='#d02670', pink='#da1e28', green='#198038', orange='#ba4e00',
  on='#ffffff',
}
local NONE = 'NONE'

local function tint(c, a) -- blend c over the background, for diagnostic and diff fills
  local function ch(h, i) return tonumber(h:sub(i, i + 1), 16) end
  local r, g, b = ch(c, 2), ch(c, 4), ch(c, 6)
  local R, G, B = ch(p.bg, 2), ch(p.bg, 4), ch(p.bg, 6)
  return string.format('#%02x%02x%02x', R + (r - R) * a, G + (g - G) * a, B + (b - B) * a)
end

local hl = {
  -- editor
  Normal={fg=p.fg,bg=p.bg}, NormalNC={fg=p.fg,bg=p.bg}, NormalFloat={fg=p.fg,bg=p.l1},
  FloatBorder={fg=p.l1,bg=p.l1}, FloatTitle={fg=p.text,bg=p.l2,bold=true}, FloatFooter={fg=p.muted,bg=p.l1},
  Cursor={fg=p.bg,bg=p.text}, lCursor={link='Cursor'}, TermCursor={link='Cursor'},
  CursorLine={bg=p.l1}, CursorColumn={bg=p.l1}, ColorColumn={bg=p.l1}, CursorLineNr={fg=p.text,bold=true},
  LineNr={fg=p.faint}, SignColumn={bg=p.bg}, FoldColumn={fg=p.faint,bg=p.bg}, Folded={fg=p.muted,bg=p.l1},
  EndOfBuffer={fg=p.bg}, NonText={fg=p.l3}, Whitespace={fg=p.l2}, SpecialKey={fg=p.l3}, Conceal={fg=p.dim},
  WinSeparator={fg=p.rule}, VertSplit={fg=p.rule}, WinBar={fg=p.text2,bg=p.bg}, WinBarNC={fg=p.dim,bg=p.bg},
  Visual={bg=p.l2}, VisualNOS={bg=p.l2}, Search={fg=p.on,bg=p.blue}, IncSearch={fg=p.on,bg=p.magenta},
  CurSearch={link='IncSearch'}, Substitute={fg=p.on,bg=p.purple}, MatchParen={fg=p.text,bg=p.l3,bold=true},
  QuickFixLine={bg=p.l2}, Directory={fg=p.blue}, Title={fg=p.text,bold=true}, Question={fg=p.blue}, MoreMsg={fg=p.green},
  ModeMsg={fg=p.text}, MsgArea={fg=p.fg}, ErrorMsg={fg=p.pink}, WarningMsg={fg=p.orange},
  Pmenu={fg=p.fg,bg=p.l1}, PmenuSel={fg=p.text,bg=p.l2,bold=true}, PmenuKind={fg=p.teal,bg=p.l1}, PmenuExtra={fg=p.muted,bg=p.l1},
  PmenuSbar={bg=p.l1}, PmenuThumb={bg=p.l3}, PmenuMatch={fg=p.blue,bold=true}, PmenuMatchSel={fg=p.blue,bold=true},
  StatusLine={fg=p.text2,bg=p.l1}, StatusLineNC={fg=p.dim,bg=p.l1},
  TabLine={fg=p.muted,bg=p.l1}, TabLineFill={bg=p.l1}, TabLineSel={fg=p.text,bg=p.bg,underline=true,sp=p.blue},
  CarbonTabLabel={fg=p.on,bg=p.blue}, CarbonTabModified={fg=p.magenta,bg=p.l1}, CarbonTabModifiedSel={fg=p.magenta,bg=p.bg,underline=true,sp=p.blue},
  SpellBad={undercurl=true,sp=p.pink}, SpellCap={undercurl=true,sp=p.orange}, SpellRare={undercurl=true,sp=p.purple}, SpellLocal={undercurl=true,sp=p.cyan},
  -- syntax
  Comment={fg=p.dim,italic=true}, Constant={fg=p.magenta}, String={fg=p.purple}, Character={fg=p.purple},
  Number={fg=p.magenta}, Boolean={fg=p.magenta}, Float={fg=p.magenta},
  Identifier={fg=p.fg}, Function={fg=p.teal},
  Statement={fg=p.blue}, Conditional={fg=p.blue}, Repeat={fg=p.blue}, Label={fg=p.blue}, Keyword={fg=p.blue}, Exception={fg=p.blue},
  Operator={fg=p.blue2}, PreProc={fg=p.blue}, Include={fg=p.blue}, Define={fg=p.blue}, Macro={fg=p.teal2}, PreCondit={fg=p.blue},
  Type={fg=p.cyan}, StorageClass={fg=p.blue}, Structure={fg=p.cyan}, Typedef={fg=p.cyan},
  Special={fg=p.sky}, SpecialChar={fg=p.magenta}, Tag={fg=p.blue}, Delimiter={fg=p.muted}, SpecialComment={fg=p.muted,italic=true}, Debug={fg=p.orange},
  Underlined={underline=true}, Bold={bold=true}, Italic={italic=true}, Error={fg=p.pink}, Todo={fg=p.on,bg=p.purple,bold=true},
  Added={fg=p.green}, Changed={fg=p.orange}, Removed={fg=p.pink},
  -- treesitter
  ['@variable']={fg=p.fg}, ['@variable.builtin']={fg=p.magenta}, ['@variable.parameter']={fg=p.text2}, ['@variable.member']={fg=p.sky},
  ['@property']={fg=p.sky}, ['@field']={fg=p.sky}, ['@constant']={fg=p.magenta}, ['@constant.builtin']={fg=p.magenta}, ['@constant.macro']={fg=p.teal2},
  ['@module']={fg=p.cyan}, ['@namespace']={fg=p.cyan}, ['@label']={fg=p.blue},
  ['@string']={fg=p.purple}, ['@string.escape']={fg=p.magenta}, ['@string.regexp']={fg=p.magenta}, ['@string.special']={fg=p.magenta},
  ['@string.special.symbol']={fg=p.magenta}, ['@string.special.url']={fg=p.blue,underline=true}, ['@character']={fg=p.purple},
  ['@number']={fg=p.magenta}, ['@boolean']={fg=p.magenta}, ['@type']={fg=p.cyan}, ['@type.builtin']={fg=p.cyan,italic=true}, ['@type.definition']={fg=p.cyan},
  ['@attribute']={fg=p.teal2}, ['@function']={fg=p.teal,bold=true}, ['@function.call']={fg=p.teal}, ['@function.builtin']={fg=p.teal2},
  ['@function.macro']={fg=p.teal2}, ['@function.method']={fg=p.teal}, ['@function.method.call']={fg=p.teal}, ['@constructor']={fg=p.cyan},
  ['@operator']={fg=p.blue2}, ['@keyword']={fg=p.blue}, ['@keyword.function']={fg=p.blue}, ['@keyword.return']={fg=p.blue,italic=true},
  ['@keyword.import']={fg=p.blue}, ['@keyword.operator']={fg=p.blue}, ['@keyword.exception']={fg=p.pink},
  ['@punctuation']={fg=p.muted}, ['@punctuation.delimiter']={fg=p.muted}, ['@punctuation.bracket']={fg=p.muted}, ['@punctuation.special']={fg=p.magenta},
  ['@comment']={link='Comment'}, ['@comment.todo']={link='Todo'}, ['@comment.note']={fg=p.on,bg=p.blue,bold=true},
  ['@comment.warning']={fg=p.on,bg=p.orange,bold=true}, ['@comment.error']={fg=p.on,bg=p.pink,bold=true},
  ['@tag']={fg=p.blue}, ['@tag.builtin']={fg=p.blue}, ['@tag.attribute']={fg=p.sky}, ['@tag.delimiter']={fg=p.dim},
  ['@markup.heading']={fg=p.text,bold=true}, ['@markup.heading.1']={fg=p.blue,bold=true}, ['@markup.heading.2']={fg=p.purple,bold=true},
  ['@markup.heading.3']={fg=p.magenta,bold=true}, ['@markup.heading.4']={fg=p.teal,bold=true},
  ['@markup.strong']={bold=true}, ['@markup.italic']={italic=true}, ['@markup.strikethrough']={strikethrough=true},
  ['@markup.link']={fg=p.blue}, ['@markup.link.url']={fg=p.blue,underline=true}, ['@markup.link.label']={fg=p.sky},
  ['@markup.raw']={fg=p.purple}, ['@markup.list']={fg=p.blue}, ['@markup.quote']={fg=p.muted,italic=true},
  ['@diff.plus']={fg=p.green}, ['@diff.minus']={fg=p.pink}, ['@diff.delta']={fg=p.orange},
  -- lsp semantic tokens
  ['@lsp.type.namespace']={link='@module'}, ['@lsp.type.type']={link='@type'}, ['@lsp.type.class']={link='@type'}, ['@lsp.type.enum']={link='@type'},
  ['@lsp.type.interface']={link='@type'}, ['@lsp.type.struct']={link='@type'}, ['@lsp.type.parameter']={link='@variable.parameter'},
  ['@lsp.type.property']={link='@property'}, ['@lsp.type.enumMember']={link='@constant'}, ['@lsp.type.function']={link='@function.call'},
  ['@lsp.type.method']={link='@function.method.call'}, ['@lsp.type.macro']={link='@function.macro'}, ['@lsp.type.decorator']={link='@attribute'},
  ['@lsp.mod.readonly']={link='@constant'}, ['@lsp.typemod.variable.defaultLibrary']={link='@variable.builtin'},
  LspReferenceText={bg=p.l2}, LspReferenceRead={bg=p.l2}, LspReferenceWrite={bg=p.l2,underline=true,sp=p.blue},
  LspInlayHint={fg=p.dim,bg=p.l1}, LspCodeLens={fg=p.dim}, LspSignatureActiveParameter={fg=p.text,bg=p.l2,bold=true}, LspInfoBorder={link='FloatBorder'},
  -- diagnostics: Carbon support colors, tinted virtual text
  DiagnosticError={fg=p.pink}, DiagnosticWarn={fg=p.orange}, DiagnosticInfo={fg=p.blue}, DiagnosticHint={fg=p.teal}, DiagnosticOk={fg=p.green},
  DiagnosticVirtualTextError={fg=p.pink,bg=tint(p.pink,.1)}, DiagnosticVirtualTextWarn={fg=p.orange,bg=tint(p.orange,.1)},
  DiagnosticVirtualTextInfo={fg=p.blue,bg=tint(p.blue,.1)}, DiagnosticVirtualTextHint={fg=p.teal,bg=tint(p.teal,.1)},
  DiagnosticUnderlineError={undercurl=true,sp=p.pink}, DiagnosticUnderlineWarn={undercurl=true,sp=p.orange},
  DiagnosticUnderlineInfo={undercurl=true,sp=p.blue}, DiagnosticUnderlineHint={undercurl=true,sp=p.teal},
  DiagnosticUnnecessary={fg=p.dim}, DiagnosticDeprecated={strikethrough=true,sp=p.dim},
  -- diff and git
  DiffAdd={bg=tint(p.green,.15)}, DiffChange={bg=tint(p.blue,.1)}, DiffDelete={fg=p.pink,bg=tint(p.pink,.12)}, DiffText={bg=tint(p.blue,.28)},
  diffAdded={fg=p.green}, diffRemoved={fg=p.pink}, diffChanged={fg=p.orange},
  GitSignsAdd={fg=p.green}, GitSignsChange={fg=p.orange}, GitSignsDelete={fg=p.pink}, GitSignsCurrentLineBlame={fg=p.dim,italic=true},
  -- telescope: borderless panels on layers
  TelescopeNormal={fg=p.fg,bg=p.l1}, TelescopeBorder={fg=p.l1,bg=p.l1}, TelescopeTitle={fg=p.text,bg=p.l2,bold=true},
  TelescopePromptNormal={fg=p.text,bg=p.l2}, TelescopePromptBorder={fg=p.l2,bg=p.l2}, TelescopePromptTitle={fg=p.on,bg=p.blue,bold=true},
  TelescopePromptPrefix={fg=p.blue}, TelescopePreviewTitle={fg=p.on,bg=p.teal,bold=true}, TelescopeResultsTitle={fg=p.l1,bg=p.l1},
  TelescopeSelection={fg=p.text,bg=p.l2,bold=true}, TelescopeSelectionCaret={fg=p.blue,bg=p.l2}, TelescopeMatching={fg=p.blue,bold=true},
  -- neo-tree
  NeoTreeNormal={fg=p.fg,bg=p.bg}, NeoTreeNormalNC={fg=p.fg,bg=p.bg}, NeoTreeWinSeparator={fg=p.rule,bg=p.bg},
  NeoTreeRootName={fg=p.text,bold=true}, NeoTreeDirectoryName={fg=p.fg}, NeoTreeDirectoryIcon={fg=p.blue}, NeoTreeFileIcon={fg=p.muted},
  NeoTreeFileName={fg=p.fg}, NeoTreeFileNameOpened={fg=p.text,bold=true}, NeoTreeIndentMarker={fg=p.l2}, NeoTreeExpander={fg=p.dim},
  NeoTreeCursorLine={bg=p.l2}, NeoTreeModified={fg=p.magenta}, NeoTreeDimText={fg=p.dim}, NeoTreeDotfile={fg=p.dim},
  NeoTreeGitAdded={fg=p.green}, NeoTreeGitModified={fg=p.orange}, NeoTreeGitDeleted={fg=p.pink}, NeoTreeGitUntracked={fg=p.purple},
  NeoTreeGitIgnored={fg=p.faint}, NeoTreeGitConflict={fg=p.pink,bold=true}, NeoTreeTitleBar={fg=p.on,bg=p.blue},
  NeoTreeFloatBorder={link='FloatBorder'}, NeoTreeFloatTitle={link='FloatTitle'},
  -- mini, flash, which-key, harpoon, lazy, mason, undotree, indent
  MiniIndentscopeSymbol={fg=p.l3}, MiniFilesNormal={link='NormalFloat'}, MiniFilesBorder={link='FloatBorder'}, MiniFilesTitle={fg=p.muted,bg=p.l1},
  MiniFilesTitleFocused={fg=p.text,bg=p.l2,bold=true}, MiniFilesDirectory={fg=p.blue}, MiniIconsAzure={fg=p.cyan}, MiniIconsBlue={fg=p.blue},
  MiniIconsCyan={fg=p.teal}, MiniIconsGreen={fg=p.green}, MiniIconsGrey={fg=p.muted}, MiniIconsOrange={fg=p.orange}, MiniIconsPurple={fg=p.purple},
  MiniIconsRed={fg=p.pink}, MiniIconsYellow={fg=p.orange},
  FlashLabel={fg=p.on,bg=p.magenta,bold=true}, FlashMatch={fg=p.text,bg=p.l2}, FlashCurrent={fg=p.on,bg=p.blue}, FlashBackdrop={fg=p.dim},
  WhichKey={fg=p.blue}, WhichKeyGroup={fg=p.purple}, WhichKeyDesc={fg=p.fg}, WhichKeySeparator={fg=p.dim}, WhichKeyNormal={bg=p.l1}, WhichKeyBorder={link='FloatBorder'},
  HarpoonWindow={link='NormalFloat'}, HarpoonBorder={link='FloatBorder'},
  LazyNormal={bg=p.l1}, LazyButton={fg=p.fg,bg=p.l2}, LazyButtonActive={fg=p.on,bg=p.blue,bold=true}, LazyH1={fg=p.on,bg=p.blue,bold=true},
  LazySpecial={fg=p.blue}, LazyProgressDone={fg=p.blue}, LazyProgressTodo={fg=p.l3},
  MasonNormal={bg=p.l1}, MasonHeader={fg=p.on,bg=p.blue,bold=true}, MasonHighlight={fg=p.blue}, MasonHighlightBlockBold={fg=p.on,bg=p.blue,bold=true},
  MasonMuted={fg=p.dim}, MasonMutedBlock={fg=p.fg,bg=p.l2},
  UndotreeNode={fg=p.blue}, UndotreeSeq={fg=p.purple}, UndotreeCurrent={fg=p.magenta}, UndotreeTimeStamp={fg=p.dim},
  IblIndent={fg=p.l2}, IblScope={fg=p.l3},
  -- completion (nvim-cmp and blink.cmp)
  CmpItemAbbrMatch={fg=p.blue,bold=true}, CmpItemAbbrMatchFuzzy={fg=p.blue}, CmpItemAbbrDeprecated={fg=p.dim,strikethrough=true},
  CmpItemKind={fg=p.teal}, CmpItemMenu={fg=p.muted},
  BlinkCmpMenu={link='Pmenu'}, BlinkCmpMenuBorder={fg=p.l1,bg=p.l1}, BlinkCmpMenuSelection={link='PmenuSel'}, BlinkCmpLabelMatch={fg=p.blue,bold=true},
  BlinkCmpKind={fg=p.teal}, BlinkCmpDoc={link='NormalFloat'}, BlinkCmpDocBorder={link='FloatBorder'},
  -- notify / noice / hlslens / biscuits / treesitter context
  NotifyBackground={bg=p.l2}, NotifyERRORBorder={fg=p.pink}, NotifyWARNBorder={fg=p.orange}, NotifyINFOBorder={fg=p.blue},
  NotifyERRORTitle={fg=p.pink}, NotifyWARNTitle={fg=p.orange}, NotifyINFOTitle={fg=p.blue},
  HlSearchLens={fg=p.muted,bg=p.l1}, HlSearchLensNear={fg=p.on,bg=p.blue}, BiscuitColor={fg=p.dim,italic=true},
  TreesitterContext={bg=p.l1}, TreesitterContextLineNumber={fg=p.muted,bg=p.l1}, TreesitterContextBottom={underline=true,sp=p.rule},
}
for name, value in pairs(hl) do vim.api.nvim_set_hl(0, name, value) end

-- terminal: same ANSI set as the Kitty theme
local ansi = dark and { '#262626','#ee5396','#42be65','#ff832b','#78a9ff','#be95ff','#3ddbd9','#c6c6c6',
                         '#6f6f6f','#ff7eb6','#6fdc8c','#ffb784','#a6c8ff','#d4bbff','#82cfff','#f2f4f8' }
                  or   { '#e0e0e0','#da1e28','#198038','#ba4e00','#0f62fe','#8a3ffc','#007d79','#525252',
                         '#8d8d8d','#d02670','#24a148','#eb6200','#4589ff','#a56eff','#0072c3','#161616' }
for i, c in ipairs(ansi) do vim.g['terminal_color_' .. (i - 1)] = c end
