-- Cross-references for report tables, figures, sections, and appendices.
-- Markdown keeps readable text and ordinary #anchor links for HTML/DOCX.
-- In PDF, numeric references use LaTeX's actual figure/table/section numbers.

local function add_class(element, name)
  if not element.classes:includes(name) then element.classes:insert(name) end
end

-- Pandoc's Markdown reader treats table caption suffixes as literal text.
-- Extract stable identifiers and existing layout hints into the table Attr.
-- This applies to HTML/DOCX as well as LaTeX, so all outputs have targets.
function Table(element)
  local original = pandoc.utils.stringify(element.caption.long or {})
  local updated = original:gsub('%s*{#([%w_%-:]+)}', function(id)
    element.identifier = id
    return ''
  end)
  updated = updated:gsub('%s*{%.([%w_%-]+)}', function(class)
    if class == 'wide' or class == 'here' then
      add_class(element, class)
      return ''
    end
    return ' {.' .. class .. '}'
  end)
  if updated ~= original then
    element.caption.long = pandoc.read(updated, 'markdown').blocks
  end
  return element
end

-- LaTeX/hyperref turns the whole printed reference into a link and obtains
-- its number from \ref*, so insertions/reordering cannot stale the PDF text.
-- Other formats retain ordinary, readable Markdown links.
function Link(link)
  if not FORMAT:match('latex') then return nil end
  local id = link.target:match('^#([%w_%-:]+)$')
  if not id then return nil end
  local printed = pandoc.utils.stringify(link.content)
  local kind
  if id:match('^tbl%-') and printed:match('^Table%s+%d+$') then
    kind = 'Table'
  elseif id:match('^fig%-') and printed:match('^Figure%s+%d+$') then
    kind = 'Figure'
  elseif id:match('^sec%-') and printed:match('^Section%s+[IVX]+$') then
    kind = 'Section'
  elseif id:match('^sec%-') and printed:match('^[IVX]+$') then
    kind = ''
  end
  if kind ~= nil then
    local prefix = kind == '' and '' or kind .. '~'
    return pandoc.RawInline('latex',
      '\\hyperref[' .. id .. ']{' .. prefix .. '\\ref*{' .. id .. '}}')
  end
  -- Appendices are deliberately unnumbered section headings with stable
  -- literal A-F titles, so link them without a numeric \ref.
  if id:match('^app%-[a-f]$') and printed:match('^Appendix%s+[A-F]$') then
    return pandoc.RawInline('latex',
      '\\hyperref[' .. id .. ']{' .. printed .. '}')
  end
  return nil
end
