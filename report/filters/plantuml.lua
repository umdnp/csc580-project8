-- Pandoc includes Lua. Rendering uses portable local Java + PlantUML/Smetana.
-- No diagram text is sent to a remote service.
if PANDOC_VERSION < pandoc.types.Version("3.11") then
  error("Report diagrams require Pandoc 3.11 or newer")
end

local png_signature = "\137PNG\13\10\26\10"

local function read_file(path)
  local file = io.open(path, "rb")
  if not file then return nil end
  local contents = file:read("*a")
  file:close()
  return contents
end

local function render(block)
  if not block.classes:includes("plantuml") then return nil end
  local source = block.text
  if block.attributes.source then
    source = read_file(block.attributes.source)
    if not source then error("PlantUML: cannot read " .. block.attributes.source) end
  end
  source = source:gsub("\r\n", "\n"):gsub("\r", "\n")
  if not source:match("@startuml") or not source:match("@enduml") then
    error("PlantUML: expected @startuml and @enduml")
  end
  local toolchain = read_file("report/toolchain.json")
  if not toolchain then error("PlantUML: report/toolchain.json is missing") end
  toolchain = toolchain:gsub("\r\n", "\n")
  local key = pandoc.utils.sha1(toolchain .. "\n" .. source)
  local directory = "report/diagrams/rendered"
  local path = directory .. "/" .. key .. ".png"
  local bytes = read_file(path)
  if bytes and bytes:sub(1, 8) ~= png_signature then
    error("PlantUML: invalid cached PNG at " .. path)
  end
  if not bytes then
    if os.getenv("PLANTUML_CACHED_ONLY") == "1" then
      error("PlantUML: no cached image for this source; run a normal local build first (" .. key .. ")")
    end
    local java = os.getenv("PLANTUML_JAVA") or "java"
    local jar = os.getenv("PLANTUML_JAR") or ".cache/report-tools/plantuml.jar"
    -- Smetana is inside the JAR, so there is no Graphviz dependency.
    local ok, contents = pcall(pandoc.pipe, java, {
      "-Djava.awt.headless=true", "-jar", jar, "-tpng", "-pipe",
      "-charset", "UTF-8", "-failfast2", "-Playout=smetana"
    }, source)
    if not ok or not contents or contents:sub(1, 8) ~= png_signature then
      error("PlantUML: local rendering failed. Run bin/setup_report_tools.py " ..
        "or set PLANTUML_JAVA and PLANTUML_JAR; check diagram syntax. " .. tostring(contents))
    end
    pandoc.system.make_directory(directory, true)
    local file, reason = io.open(path, "wb")
    if not file then error("PlantUML: cannot write cache: " .. tostring(reason)) end
    file:write(contents)
    file:close()
    bytes = contents
    io.stderr:write("Rendered PlantUML locally: " .. (block.attributes.source or block.identifier) .. "\n")
  end
  local target = path
  if FORMAT:match("html") then
    target = pandoc.mediabag.make_data_uri("image/png", bytes)
  end
  local caption = block.attributes.caption or ""
  local image = pandoc.Image(caption, target, "", pandoc.Attr("", {}, {
    width = block.attributes.width or "6in"
  }))
  return pandoc.Figure({pandoc.Plain({image})},
    pandoc.Caption(pandoc.read(caption, "markdown").blocks), pandoc.Attr(block.identifier))
end

return {CodeBlock = render}
