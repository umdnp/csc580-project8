-- PDF tables: one rule width, continuous row shading, explicit wide floats.
-- Pandoc handles the Markdown; this filter only controls LaTeX layout.
if not FORMAT:match('latex') then return {} end

local function render(blocks)
  if not blocks or #blocks == 0 then return '' end
  return pandoc.write(pandoc.Pandoc(blocks), 'latex'):gsub('^%s+', ''):gsub('%s+$', ''):gsub('%s*\n%s*', ' ')
end

local function caption_info(el)
  local text = pandoc.utils.stringify(el.caption.long or {})
  -- Pandoc releases can interpret {.wide} as caption text or a table class.
  local wide = el.classes:includes('wide') or text:find('{.wide}', 1, true) ~= nil
  text = text:gsub('%s*{%s*%.wide%s*}', '')
  return text, wide
end

local function rows_of(el)
  local rows = {}
  for _, row in ipairs(el.head.rows) do rows[#rows+1] = row end
  for _, body in ipairs(el.bodies) do
    for _, row in ipairs(body.head) do rows[#rows+1] = row end
    for _, row in ipairs(body.body) do rows[#rows+1] = row end
  end
  for _, row in ipairs(el.foot.rows) do rows[#rows+1] = row end
  return rows
end

local function cell_text(cell)
  return render(cell.contents):gsub('\\texttt{([0-9a-fA-F]+)}', function(hash)
    if #hash < 28 then return '\\texttt{' .. hash .. '}' end
    local bits = {}
    for i = 1, #hash, 10 do bits[#bits+1] = hash:sub(i,i+9) end
    return '\\texttt{' .. table.concat(bits, '\\allowbreak{}') .. '}'
  end)
end

-- Simple width presets, not cell-by-cell heuristics. Header-specific choices
-- exist only where the column roles differ markedly from the defaults.
local function fractions(n, first)
  if n == 2 then
    if first == 'ID' then return {.15,.85} end
    if first == 'Setting' then return {.40,.60} end
    return {.34,.66}
  elseif n == 3 then
    if first == 'Trial' then return {.13,.42,.45} end
    if first == 'Priority' then return {.10,.28,.62} end
    return {.52,.24,.24}
  elseif n == 4 then
    if first == 'Trial' then return {.08,.23,.30,.39} end
    if first == 'Direction basis' then return {.38,.20,.21,.21} end
    return {.26,.20,.27,.27}
  elseif n == 5 then return {.42,.145,.145,.145,.145}
  elseif n == 6 then return {.30,.14,.14,.14,.14,.14} end
  local result = {}
  for i = 1,n do result[i] = 1/n end
  return result
end

function Table(el)
  local rows = rows_of(el)
  if #rows == 0 then return nil end
  local n = #rows[1].cells
  local caption, wide = caption_info(el)
  -- Wide flags have appeared in different AST locations across Pandoc builds.
  -- Long two-column tables get wide layout even if the caption hint is lost.
  local wide_three = {Trial=true, Priority=true, Indicator=true, ['Cumulative selection stage']=true}
  local first = pandoc.utils.stringify(rows[1].cells[1].contents)
  wide = wide or n >= 4 or (n == 2 and (#rows >= 9 or first == 'Change type')) or (n == 3 and wide_three[first])
  local width = wide and '\\textwidth' or '\\columnwidth'
  local env = wide and 'table*' or 'table'
  local sizes = fractions(n,first)
  local cols = {}
  for j=1,n do
    local align = el.colspecs[j] and el.colspecs[j][1] == pandoc.AlignRight
      and '\\RaggedLeft' or '\\RaggedRight'
    cols[j] = '>{'..align..'\\arraybackslash}p{\\dimexpr '..string.format('%.5f',sizes[j])..width..'-2\\tabcolsep\\relax}'
  end
  local code = {
    '\\begin{'..env..'}[!tp]',
    '\\centering\\begingroup',
    n >= 5 and '\\fontsize{7.7pt}{9.5pt}\\selectfont' or '\\small',
    '\\setlength{\\tabcolsep}{2.5pt}',
    '\\renewcommand{\\arraystretch}{1.25}',
    -- Slightly stronger than a hairline: survives PDF viewer pixel rounding.
    '\\setlength{\\arrayrulewidth}{0.68pt}',
    '\\arrayrulecolor{black!85}',
    -- Keep outer padding so row shading and horizontal rules share the same edges.
    '\\begin{tabular}{'..table.concat(cols)..'}',
    '\\hline',
  }
  -- Extend the normal header-row strut by 0.20 pt above and below.
  -- Unlike \vspace and \par, this adds no extra paragraph spacing.
  local header_pad = '\\rule[-\\dimexpr\\dp\\csname @arstrutbox\\endcsname+0.20pt\\relax]' ..
    '{0pt}{\\dimexpr\\ht\\csname @arstrutbox\\endcsname+' ..
    '\\dp\\csname @arstrutbox\\endcsname+0.40pt\\relax}'
  for i,row in ipairs(rows) do
    code[#code+1] = i == 1 and '\\rowcolor{reportTableHead}' or (i%2 == 0 and '\\rowcolor{reportTableStripe}' or '')
    local cells = {}
    for j,cell in ipairs(row.cells) do
      local str = cell_text(cell)
      if str == '' then str = '\\mbox{}' end
      if i == 1 and j == 1 then str = header_pad .. str end
      cells[#cells+1] = str
    end
    code[#code+1] = table.concat(cells,' & ')..' \\\\'
    if i == 1 then code[#code+1] = '\\hline' end
  end
  code[#code+1] = '\\hline'
  code[#code+1] = '\\end{tabular}'
  if caption ~= '' then code[#code+1] = '\\caption{'..render(pandoc.read(caption,'markdown').blocks)..'}' end
  if el.identifier and el.identifier ~= '' then code[#code+1] = '\\label{'..el.identifier..'}' end
  code[#code+1] = '\\endgroup\\end{'..env..'}'
  return pandoc.RawBlock('latex', table.concat(code,'\n'))
end

-- Keep figure handling separate from table layout.
function Figure(el)
  local image
  for _,block in ipairs(el.content) do
    if block.t == 'Plain' or block.t == 'Para' then
      for _,inline in ipairs(block.content) do
        if inline.t == 'Image' then image = inline; break end
      end
    end
  end
  if not image then return nil end
  local wide = el.classes:includes('wide') or image.classes:includes('wide')
  local full = el.classes:includes('fullpage') or image.classes:includes('fullpage')
  wide = wide or full
  local env = wide and 'figure*' or 'figure'
  local bounds = full and 'width=\\textwidth,height=.82\\textheight' or
    (wide and 'width=\\textwidth,height=.48\\textheight' or 'width=\\columnwidth,height=.58\\textheight')
  local code = {'\\begin{'..env..'}['..(full and 'p' or '!tp')..']',
    '\\centering', '\\includegraphics['..bounds..',keepaspectratio]{'..image.src..'}'}
  local caption = pandoc.utils.stringify(el.caption.long or {})
  if caption ~= '' then code[#code+1] = '\\caption{'..render(pandoc.read(caption,'markdown').blocks)..'}' end
  if el.identifier ~= '' then code[#code+1] = '\\label{'..el.identifier..'}' end
  code[#code+1] = '\\end{'..env..'}'
  local blocks = {}
  if full then blocks[#blocks+1] = pandoc.RawBlock('latex','\\clearpage') end
  blocks[#blocks+1] = pandoc.RawBlock('latex',table.concat(code,'\n'))
  if full then blocks[#blocks+1] = pandoc.RawBlock('latex','\\clearpage') end
  return blocks
end
