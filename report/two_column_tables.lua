-- Readable two-column tables and figures for PDF/LaTeX.
-- Markdown remains the source of truth; captions marked {.wide} are
-- converted to true two-column floats, rather than being printed literally.
local latex_format = FORMAT:match('latex') ~= nil

local function trim(s)
  return (s:gsub('^%s+', ''):gsub('%s+$', ''))
end
local function latex(blocks)
  if not blocks or #blocks == 0 then return '' end
  return trim(pandoc.write(pandoc.Pandoc(blocks), 'latex'):gsub('%s*\n%s*', ' '))
end
local function caption_info(caption)
  local s = pandoc.utils.stringify(caption.long or {})
  local wide = s:match('{%.wide}%s*$') ~= nil
  local page = s:match('{%.fullpage}%s*$') ~= nil
  s = trim(s:gsub('%s*{%.wide}', ''):gsub('%s*{%.fullpage}', ''))
  return s,wide,page
end
local function escape_caption(s)
  if s == '' then return '' end
  return latex(pandoc.read(s, 'markdown').blocks)
end
local function cell_text(cell)
  return latex(cell.contents)
end
local function get_rows(el)
  local result = {}
  for _,row in ipairs(el.head.rows) do result[#result+1]=row end
  for _,body in ipairs(el.bodies) do
    for _,row in ipairs(body.head) do result[#result+1]=row end
    for _,row in ipairs(body.body) do result[#result+1]=row end
  end
  for _,row in ipairs(el.foot.rows) do result[#result+1]=row end
  return result
end
local function numeric_cell(s)
  return s:match('^%s*[%+%-]?%d') ~= nil or s:find('\\%s*%d') ~= nil
end
local function widths(rows,n)
  local lengths = {}
  local numeric = {}
  for j=1,n do lengths[j]=1;numeric[j]=0 end
  for r=2,#rows do
    for j,cell in ipairs(rows[r].cells) do
      local txt = pandoc.utils.stringify(cell.contents)
      local size = #txt
      lengths[j] = math.max(lengths[j],size)
      if numeric_cell(txt) then numeric[j]=numeric[j]+1 end
    end
  end
  local numcols=0
  for j=1,n do if numeric[j] >= math.max(1,math.floor((#rows-1)/2)) then numcols=numcols+1 end end
  local frac={}
  if n==2 then
    if numcols==1 and numeric[2]>numeric[1] then frac={.74,.26}
    elseif numcols==1 then frac={.25,.75}
    elseif lengths[2] > lengths[1]*1.7 then frac={.29,.71}
    else frac={.45,.55} end
  elseif n==3 then
    if numcols >= 2 then frac={.56,.22,.22}
    elseif lengths[3] > 75 then frac={.11,.27,.62}
    else frac={.45,.28,.27} end
  elseif n==4 then
    if numcols>=2 then frac={.29,.25,.23,.23}
    else frac={.20,.21,.32,.27} end
  elseif n==5 then frac={.41,.1475,.1475,.1475,.1475}
  elseif n==6 then frac={.30,.14,.14,.14,.14,.14}
  else for j=1,n do frac[j]=1/n end end
  return frac,numeric
end

function Table(el)
  if not latex_format then
    local raw, wide = caption_info(el.caption)
    if wide then
      el.caption.long = pandoc.read(raw, 'markdown').blocks
      el.classes:insert('wide')
      return el
    end
    return nil
  end
  local rows=get_rows(el)
  if #rows==0 then return nil end
  local n=#rows[1].cells
  if n<1 then return nil end
  local caption,marked=caption_info(el.caption)
  local wide=marked or n>=4
  -- Avoid a narrow 2-col layout for long explanatory / multirow tables.
  local frac, numeric=widths(rows,n)
  local env=wide and 'table*' or 'table'
  local width=wide and '\\textwidth' or '\\columnwidth'
  local lines={}
  local function add(s) lines[#lines+1]=s end
  -- Figures and tables are placed by LaTeX; don't resize type to force a fit.
  add('\\begin{'..env..'}[!tp]')
  add('\\centering')
  add('\\begingroup')
  add('\\small')
  add('\\setlength{\\tabcolsep}{4pt}')
  add('\\renewcommand{\\arraystretch}{1.24}')
  -- Keep rule edges flush against shaded rows rather than separated by white strips.
  add('\\setlength{\\aboverulesep}{0pt}')
  add('\\setlength{\\belowrulesep}{0pt}')
  local cols={}
  for j=1,n do
    local align = numeric[j] >= math.max(1,math.floor((#rows-1)/2)) and j>1
      and '\\RaggedLeft' or '\\RaggedRight'
    cols[j] = '>{'..align..'\\arraybackslash}p{\\dimexpr '..string.format('%.5f',frac[j])..width..'-2\\tabcolsep\\relax}'
  end
  add('\\begin{tabular}{@{}'..table.concat(cols,'')..'@{}}')
  add('\\toprule')
  for ri,row in ipairs(rows) do
    local cells={}
    for j,cell in ipairs(row.cells) do
      local text=cell_text(cell)
      if text=='' then text='\\mbox{}' end
      cells[#cells+1]=text
    end
    -- Zero overhang keeps the background exactly inside the tabular's outer edges.
    if ri==1 then add('\\rowcolor{reportTableHead}[0pt][0pt]')
    elseif ri%2==0 then add('\\rowcolor{reportTableStripe}[0pt][0pt]') end
    add(table.concat(cells,' & ')..' \\\\')
    if ri==1 then add('\\midrule') end
  end
  add('\\bottomrule')
  add('\\end{tabular}')
  if caption~='' then add('\\caption{'..escape_caption(caption)..'}') end
  if el.identifier and el.identifier~='' then add('\\label{'..el.identifier..'}') end
  add('\\endgroup')
  add('\\end{'..env..'}')
  return pandoc.RawBlock('latex',table.concat(lines,'\n'))
end

function Figure(el)
  if not latex_format then return nil end
  local wide=el.classes:includes('wide') or el.classes:includes('fullpage')
  local fullpage=el.classes:includes('fullpage')
  local env=wide and 'figure*' or 'figure'
  local caption=pandoc.utils.stringify(el.caption.long or {})
  local image=nil
  for _,block in ipairs(el.content) do
    if block.t=='Plain' or block.t=='Para' then
      for _,inline in ipairs(block.content) do
        if inline.t=='Image' then image=inline;break end
      end
    end
  end
  if not image then return nil end
  wide=wide or image.classes:includes('wide')
  fullpage=fullpage or image.classes:includes('fullpage')
  env=wide and 'figure*' or 'figure'
  -- Bounding BOTH dimensions ensures images never bleed into adjacent columns.
  local options= fullpage and 'width=\\textwidth,height=.82\\textheight,keepaspectratio'
    or (wide and 'width=\\textwidth,height=.48\\textheight,keepaspectratio'
      or 'width=\\columnwidth,height=.58\\textheight,keepaspectratio')
  local cmd={'\\begin{'..env..'}['..(fullpage and 'p' or '!tp')..']',
    '\\centering', '\\includegraphics['..options..']{'..image.src..'}'}
  if caption~='' then cmd[#cmd+1]='\\caption{'..escape_caption(caption)..'}' end
  if el.identifier and el.identifier~='' then cmd[#cmd+1]='\\label{'..el.identifier..'}' end
  cmd[#cmd+1]='\\end{'..env..'}'
  local out={}
  if fullpage then out[#out+1]=pandoc.RawBlock('latex','\\clearpage') end
  out[#out+1]=pandoc.RawBlock('latex',table.concat(cmd,'\n'))
  if fullpage then out[#out+1]=pandoc.RawBlock('latex','\\clearpage') end
  return out
end
