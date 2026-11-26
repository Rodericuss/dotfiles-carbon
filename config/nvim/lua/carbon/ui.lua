local M={}
function M.setup()
 vim.o.guifont='IBM Plex Mono:h11'
 vim.o.showtabline=2
 vim.o.fillchars='eob: ,vert:│,horiz:─,fold: ,foldopen:▾,foldclose:▸'
 vim.o.guicursor='n-v-c:block,i-ci-ve:ver25,r-cr:hor20,o:hor50,a:blinkon0'
 vim.o.pumblend=0
 vim.o.winblend=0
 if vim.fn.exists('+winborder')==1 then vim.o.winborder='solid' end
 vim.diagnostic.config({ virtual_text={ prefix='■', spacing=2 }, float={ border='solid' },
   signs={ text={ [vim.diagnostic.severity.ERROR]='■', [vim.diagnostic.severity.WARN]='▲', [vim.diagnostic.severity.INFO]='●', [vim.diagnostic.severity.HINT]='◆' } } })
 -- Buffer tabs as Carbon tabs: active one on the background with a blue rule under it.
 _G.CarbonBufferClick=function(n) if vim.api.nvim_buf_is_valid(n) then vim.api.nvim_set_current_buf(n) end end
 _G.CarbonTabline=function()
   local s='%#CarbonTabLabel# buf '
   local cur=vim.api.nvim_get_current_buf()
   for _,b in ipairs(vim.api.nvim_list_bufs()) do
     if vim.bo[b].buflisted then
       local name=vim.fn.fnamemodify(vim.api.nvim_buf_get_name(b),':t');if name=='' then name='[novo]' end
       name=name:gsub('%%','%%%%')
       local sel=b==cur
       s=s..(sel and '%#TabLineSel#' or '%#TabLine#')..'%'..b..'@v:lua.CarbonBufferClick@  '..name..' '
       s=s..(vim.bo[b].modified and ((sel and '%#CarbonTabModifiedSel#' or '%#CarbonTabModified#')..'■ ') or '  ')..'%T'
     end
   end
   return s..'%#TabLineFill#%='
 end
 vim.o.tabline='%!v:lua.CarbonTabline()'
 local saved=nil
 vim.api.nvim_create_user_command('CarbonFocus',function()
   if saved then
     for k,v in pairs(saved) do vim.o[k]=v end;saved=nil
   else
     saved={number=vim.o.number,relativenumber=vim.o.relativenumber,laststatus=vim.o.laststatus,showtabline=vim.o.showtabline,signcolumn=vim.o.signcolumn}
     vim.o.number=false;vim.o.relativenumber=false;vim.o.laststatus=0;vim.o.showtabline=0;vim.o.signcolumn='no'
   end
 end,{})
 vim.keymap.set('n','<leader>uz','<cmd>CarbonFocus<cr>',{desc='Carbon: foco de leitura'})
 vim.keymap.set('n','<leader>ub',function() vim.o.background = vim.o.background=='dark' and 'light' or 'dark'; vim.cmd.colorscheme('carbon') end,{desc='Carbon: alternar g100 / g10'})
end
return M
