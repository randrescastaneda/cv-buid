-- Presentation only: the same semantic QMD supplies every output's content.
local latex = FORMAT:match('latex') ~= nil
local word = FORMAT:match('docx') ~= nil
local function wrap(blocks, before, after)
  local result = pandoc.List({pandoc.RawBlock('latex', before)})
  result:extend(blocks)
  result:insert(pandoc.RawBlock('latex', after))
  return result
end
function Span(el)
  if el.classes:includes('cv-date') then
    local result = pandoc.List()
    if latex then result:insert(pandoc.RawInline('latex', '\\hfill{} '))
    elseif word then result:insert(pandoc.RawInline('openxml', '<w:r><w:tab/></w:r>'))
    else result:insert(pandoc.Space()) end
    result:extend(el.content)
    return result
  end
end
function Emph(el)
  -- This professional preset deliberately uses no italics, even in citations.
  return el.content
end
function Div(el)
  if word and el.classes:includes('cv-entry') then
    for i, block in ipairs(el.content) do
      if block.t == 'Para' and i < #el.content then
        el.content[i] = pandoc.Div({block}, pandoc.Attr('', {}, {['custom-style']='CV Entry Lead'}))
      elseif block.t == 'Div' and block.attributes['custom-style'] == 'CV Support' and i < #el.content then
        block.attributes['custom-style'] = 'CV Support Keep'
      end
    end
    return el
  end
  if not latex then return el end
  if el.classes:includes('cv-name') then
    return wrap(el.content, '{\\fontsize{18}{21}\\selectfont\\bfseries', '\\par}\\vspace{2pt}')
  elseif el.classes:includes('cv-contact') then
    return wrap(el.content, '{\\fontsize{9.5}{11.5}\\selectfont', '\\par}')
  elseif el.classes:includes('cv-employer') then
    return wrap(el.content, '{\\fontsize{11.5}{14}\\selectfont\\bfseries', '\\par}')
  elseif el.classes:includes('cv-revision') then
    return wrap(el.content, '\\par\\nobreak\\addvspace{33pt}{\\raggedleft', '\\par}')
  elseif el.classes:includes('cv-support') then
    return wrap(el.content, '\\begin{list}{}{\\setlength{\\leftmargin}{0.42cm}\\setlength{\\rightmargin}{0pt}\\setlength{\\topsep}{0pt}}\\item\\relax', '\\end{list}')
  elseif el.classes:includes('cv-career') or el.classes:includes('cv-degree') then
    return wrap(el.content, '\\noindent', '\\par\\nopagebreak')
  elseif el.classes:includes('cv-entry') then
    return wrap(el.content, '\\par\\addvspace{3pt}\\noindent\\begin{minipage}{\\linewidth}', '\\end{minipage}\\par')
  end
end
