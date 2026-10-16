-- PDF/LaTeX: require at least two paragraph lines at either page edge.
-- Standard LaTeX sectioning already keeps headings with following text.
-- DOCX uses the equivalent paragraph controls in report/reference.docx.
return {
  Meta = function(meta)
    if FORMAT ~= "latex" then return nil end
    local controls = pandoc.MetaBlocks({pandoc.RawBlock("latex", [[
\clubpenalty=10000
\widowpenalty=10000
\displaywidowpenalty=10000
]])})
    local includes = meta["header-includes"]
    if includes == nil then
      meta["header-includes"] = controls
    elseif pandoc.utils.type(includes) == "List" then
      includes:insert(controls)
    else
      meta["header-includes"] = pandoc.MetaList({includes, controls})
    end
    return meta
  end
}
