-- PDF-only section heading treatment: title-style initials and numbering.
-- Keep Markdown headings natural; typography is applied when rendering LaTeX.
if not FORMAT:match('latex') then return {} end

local in_appendix = false

local function capitalize_initials(inlines)
  for _, inline in ipairs(inlines) do
    if inline.t == 'Str' then
      -- Preserve existing letters (including acronyms) while capitalizing the
      -- initial of each word for full-size initials with \scshape.
      inline.text = inline.text:gsub('%a+', function(word)
        return word:sub(1, 1):upper() .. word:sub(2)
      end)
    end
  end
end

function Header(header)
  if header.level == 1 then
    capitalize_initials(header.content)
    local heading = pandoc.utils.stringify(header.content)
    if heading == 'Abstract' or heading == 'References'
        or heading:match('^Appendix [A-F] ') then
      header.classes:insert('unnumbered')
    end
    if heading:match('^Appendix [A-F] ') then in_appendix = true end
  elseif header.level == 2 then
    capitalize_initials(header.content)
    -- Appendix titles already carry an A-F designation. Their internal
    -- subsections are descriptive, not part of the I-X section sequence.
    if in_appendix then header.classes:insert('unnumbered') end
  elseif header.level == 3 then
    capitalize_initials(header.content)
  end
  -- Place any remaining Appendix D floats before the Appendix E heading.
  if header.level == 1 and
      pandoc.utils.stringify(header.content):match('^Appendix E ') then
    return {pandoc.RawBlock('latex', '\\FloatBarrier'), header}
  end
  return header
end
