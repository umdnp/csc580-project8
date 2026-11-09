-- XeLaTeX cannot read SVG directly. Convert SVG source figures into cached
-- vector PDF for LaTeX only; other output formats keep the original SVG.
if not FORMAT:match('latex') then return {} end

local converter = 'report/filters/svg_to_pdf.py'

local function read_file(path)
  local file = io.open(path, 'rb')
  if not file then return nil end
  local contents = file:read('*a')
  file:close()
  return contents
end

local converter_source = read_file(converter)
if not converter_source then error('Missing SVG converter: ' .. converter) end

function Image(image)
  if not image.src:lower():match('%.svg$') then return nil end

  local contents = read_file(image.src)
  if not contents then error('Cannot read SVG figure: ' .. image.src) end
  local key = pandoc.utils.sha1(converter_source .. '\n' .. contents)
  local path = '.cache/report-svg-pdf/' .. key .. '.pdf'
  local cached = read_file(path)
  if not cached or cached:sub(1, 5) ~= '%PDF-' then
    pandoc.system.make_directory('.cache/report-svg-pdf', true)
    local python = os.getenv('REPORT_PYTHON') or 'python'
    local ok, result = pcall(pandoc.pipe, python, {converter, image.src, path}, '')
    if not ok then
      error('Unable to convert ' .. image.src .. ' to a vector PDF. ' ..
        'Install the SVG renderer once with `uv add --dev svglib` and retry. ' ..
        tostring(result))
    end
    cached = read_file(path)
    if not cached or cached:sub(1, 5) ~= '%PDF-' then
      error('SVG converter did not produce a valid PDF for ' .. image.src)
    end
  end
  image.src = path
  return image
end
