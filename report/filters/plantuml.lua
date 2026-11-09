-- Render PlantUML as cached SVG, preserving vectors in HTML and PDFs.
-- Sources are rendered locally with Java and the pinned PlantUML JAR.
if PANDOC_VERSION < pandoc.types.Version('3.11') then
  error('Report diagrams require Pandoc 3.11 or newer')
end

local function read_file(path)
  local file = io.open(path, 'rb')
  if not file then return nil end
  local contents = file:read('*a')
  file:close()
  return contents
end

-- Prefer the JAR in the current checkout. An absolute PLANTUML_JAR path
-- created in WSL may be a UNC path that Windows Java cannot open reliably.
local function file_exists(path)
  local file = io.open(path, 'rb')
  if not file then return false end
  file:close()
  return true
end

local function locate_jar()
  local local_jar = '.cache/report-tools/plantuml.jar'
  if file_exists(local_jar) then return local_jar end

  local configured = os.getenv('PLANTUML_JAR')
  if configured and configured ~= '' and file_exists(configured) then
    return configured
  end
  error('PlantUML: JAR not found in this checkout (' .. local_jar .. '). ' ..
    'Run `uv run python bin/setup_report_tools.py` from your Windows ' ..
    'repository directory, then rebuild. PLANTUML_JAR=' ..
    tostring(configured or '(unset)'))
end

local function render(block)
  if not block.classes:includes('plantuml') then return nil end
  local source = block.text
  if block.attributes.source then
    source = read_file(block.attributes.source)
    if not source then error('PlantUML: cannot read ' .. block.attributes.source) end
  end
  source = source:gsub('\r\n', '\n'):gsub('\r', '\n')
  if not source:match('@startuml') or not source:match('@enduml') then
    error('PlantUML: expected @startuml and @enduml')
  end
  local toolchain = read_file('report/toolchain.json')
  if not toolchain then error('PlantUML: report/toolchain.json is missing') end
  local key = pandoc.utils.sha1(toolchain:gsub('\r\n', '\n') .. '\n' .. source)
  local directory = '.cache/report-plantuml'
  local path = directory .. '/' .. key .. '.svg'
  local bytes = read_file(path)
  if bytes and not bytes:find('<svg[%s>]', 1) then
    error('PlantUML: invalid cached SVG at ' .. path)
  end
  if not bytes then
    if os.getenv('PLANTUML_CACHED_ONLY') == '1' then
      error('PlantUML: missing cached SVG; run a normal local build first (' .. key .. ')')
    end
    local java = os.getenv('PLANTUML_JAVA') or 'java'
    local jar = locate_jar()
    local ok, contents = pcall(pandoc.pipe, java, {
      '-Djava.awt.headless=true', '-jar', jar, '-tsvg', '-pipe',
      '-charset', 'UTF-8', '-failfast2', '-Playout=smetana'
    }, source)
    if not ok or not contents or not contents:find('<svg[%s>]', 1) then
      error('PlantUML: SVG rendering failed using JAR ' .. jar .. '. ' ..
        'Check PLANTUML_JAVA and verify the JAR is readable by Java. ' ..
        tostring(contents))
    end
    pandoc.system.make_directory(directory, true)
    local file, reason = io.open(path, 'wb')
    if not file then error('PlantUML: cannot write SVG cache: ' .. tostring(reason)) end
    file:write(contents)
    file:close()
    bytes = contents
    io.stderr:write('Rendered PlantUML SVG locally: ' ..
      (block.attributes.source or block.identifier) .. '\n')
  end

  local target = path
  if FORMAT:match('html') then
    target = pandoc.mediabag.make_data_uri('image/svg+xml', bytes)
  end
  local caption = block.attributes.caption or ''
  local image = pandoc.Image(caption, target, '', pandoc.Attr('', {}, {
    width = block.attributes.width or '100%'
  }))
  return pandoc.Figure({pandoc.Plain({image})},
    pandoc.read(caption, 'markdown').blocks,
    pandoc.Attr(block.identifier, block.classes))
end

function CodeBlock(block)
  return render(block)
end
