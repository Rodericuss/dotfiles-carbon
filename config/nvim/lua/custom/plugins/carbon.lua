-- Carbon theme hook: override the existing theme integrations without replacing editor tooling.
return {
 { 'folke/tokyonight.nvim', init=function() end },
 { 'scottmckendry/cyberdream.nvim', lazy=false, priority=1000, config=function()
    vim.o.background='dark'
    vim.cmd.colorscheme 'carbon'
    require('carbon.ui').setup()
 end },
 { 'nvim-lualine/lualine.nvim', config=function()
    require('lualine').setup {
      options={theme='carbon',globalstatus=true,component_separators='',section_separators=''},
      sections={lualine_a={'mode'},lualine_b={'branch','diff'},lualine_c={{'filename',path=1},'diagnostics'},
        lualine_x={'encoding','filetype'},lualine_y={'location'},lualine_z={'progress'}},
      inactive_sections={lualine_c={'filename'},lualine_x={'location'}},
    }
 end },
}
