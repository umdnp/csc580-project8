-- PDF-only section heading treatment: title-style initials and numbering.
-- Keep Markdown headings natural; typography is applied when rendering LaTeX.
if not FORMAT:match('latex') then return {} end

local in_appendix = false

-- Title-case headings for small caps: minor words have no full-height initial.
local minor_words = {}
for _, word in ipairs({
  'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'from', 'in',
  'into', 'nor', 'of', 'on', 'onto', 'or', 'over', 'per', 'so',
  'the', 'to', 'under', 'up', 'via', 'with', 'yet',
}) do
  minor_words[word] = true
end

local function capitalize_initials(inlines)
  -- Count words across all heading inlines, not separately per text node.
  local word_count = 0
  for _, inline in ipairs(inlines) do
    if inline.t == 'Str' then
      for _ in inline.text:gmatch('%a+') do word_count = word_count + 1 end
    end
  end

  local word_index = 0
  for _, inline in ipairs(inlines) do
    if inline.t == 'Str' then
      inline.text = inline.text:gsub('%a+', function(word)
        word_index = word_index + 1
        local is_end_word = word_index == 1 or word_index == word_count
        -- Preserve uppercase single-letter identifiers, e.g. Appendix A.
        if not is_end_word and minor_words[word:lower()]
            and not word:match('^[A-Z]$') then
          return word:lower()
        end
        -- Leave existing capitalization beyond the initial intact (AI, RIs).
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
  -- Unnumbered appendix headings need their own hyperlink target.
  if header.level == 1 and
      pandoc.utils.stringify(header.content):match('^Appendix [A-F] ') then
    local blocks = {}
    -- Keep the barrier before Appendix E's destination.
    if pandoc.utils.stringify(header.content):match('^Appendix E ') then
      blocks[#blocks+1] = pandoc.RawBlock('latex', [[\FloatBarrier]])
    end
    blocks[#blocks+1] = pandoc.RawBlock('latex', [[\phantomsection]])
    blocks[#blocks+1] = header
    return blocks
  end
  return header
end
