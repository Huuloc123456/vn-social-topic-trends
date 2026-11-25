# Builds docs/slides/BigData-thuyet-trinh.pptx from docs/slides/build/bigdata-slides.json on the HUIT frame of
# KhoGuard-thuyet-trinh.pptx: each new slide duplicates the matching frame slide, deletes everything but the frame
# (header band, logo, campus photo, footer strip, huit.edu.vn) and adds its own content. Same look as build-slides.ps1.
# Needs PowerPoint (COM) and the Montserrat font. Usage, from the repository root:
#   python docs/slides/build/bigdata_spec.py  # validates the canonical JSON only
#   powershell -NoProfile -ExecutionPolicy Bypass -File docs/slides/build/build-bigdata-slides.ps1
param(
  [string]$Template = "docs\slides\KhoGuard-thuyet-trinh.pptx",
  [string]$SpecPath = "docs\slides\build\bigdata-slides.json",
  [string]$Out = "docs\slides\BigData-thuyet-trinh.pptx"
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$Template = Join-Path $root $Template; $SpecPath = Join-Path $root $SpecPath; $Out = Join-Path $root $Out
$data = Get-Content -LiteralPath $SpecPath -Raw -Encoding UTF8 | ConvertFrom-Json
$TXT = $data.strings

# Frame slides of the KhoGuard deck and the frame shapes kept on each.
$FRAMES = @{
  cover   = @{ index = 1;  keep = @('Group 2','Group 4','Group 6','TextBox 8','Group 9','TextBox 11','Group 12') }
  agenda  = @{ index = 2;  keep = @('Group 2','Group 4','Freeform 6','Freeform 7','TextBox 8','Group 9','Group 13','TextBox 16') }
  section = @{ index = 3;  keep = @('Group 2','Group 4','Group 6','TextBox 8','Group 9','Group 11','TextBox 13') }
  content = @{ index = 4;  keep = @('Group 2','Group 4','Freeform 6','Freeform 7','TextBox 9') }
  ending  = @{ index = 33; keep = @('Group 2','TextBox 4','Group 5','Group 10','Group 12','TextBox 14') }
}
function RGB([string]$hex) { [int]('0x' + $hex.Substring(4,2)) * 65536 + [int]('0x' + $hex.Substring(2,2)) * 256 + [int]('0x' + $hex.Substring(0,2)) }
$C_BLUE = RGB '0070C0'; $C_COVER = RGB '00529C'; $C_RED = RGB 'ED1C24'; $C_ORANGE = RGB 'F27121'
$C_INK = RGB '1F2328'; $C_PANEL = RGB 'F2F2F2'; $C_RULE = RGB 'D0D5DA'; $C_WHITE = RGB 'FFFFFF'; $C_ROW = RGB 'F5F7F9'
$FONT = 'Montserrat'
$X0 = 53; $W = 1334; $BODY_TOP = 168; $BODY_BOTTOM = 752; $GAP = 24

# Long headings break once, at the space nearest the middle, so the two lines are even.
function Balance-Title([string]$text, [int]$max) {
  if ($text.Length -le $max) { return $text }
  $mid = [int]($text.Length / 2); $best = -1
  for ($i = 0; $i -lt $text.Length; $i++) { if ($text[$i] -eq ' ' -and ($best -lt 0 -or [Math]::Abs($i - $mid) -lt [Math]::Abs($best - $mid))) { $best = $i } }
  if ($best -lt 0) { return $text }
  $text.Substring(0, $best) + [char]11 + $text.Substring($best + 1)
}
# Inline **bold** becomes a bold run; returns plain text plus the spans to format.
function Parse-Rich([string]$text) {
  $plain = New-Object System.Text.StringBuilder; $spans = @(); $last = 0
  foreach ($m in [regex]::Matches($text, '\*\*(.+?)\*\*')) {
    [void]$plain.Append($text.Substring($last, $m.Index - $last))
    $spans += [pscustomobject]@{ start = $plain.Length; length = $m.Groups[1].Value.Length }
    [void]$plain.Append($m.Groups[1].Value); $last = $m.Index + $m.Length
  }
  [void]$plain.Append($text.Substring($last))
  [pscustomobject]@{ text = $plain.ToString(); spans = $spans }
}
function Set-Rich($range, [string[]]$paragraphs, [int]$size, [int]$color, [bool]$bold = $false) {
  $parts = $paragraphs | ForEach-Object { Parse-Rich $_ }
  $range.Text = ($parts | ForEach-Object { $_.text }) -join "`r"
  $range.Font.Name = $FONT; $range.Font.Size = $size; $range.Font.Color.RGB = $color; $range.Font.Bold = [int]$bold
  $offset = 0
  foreach ($p in $parts) {
    foreach ($s in $p.spans) { $range.Characters($offset + $s.start + 1, $s.length).Font.Bold = -1 }
    $offset += $p.text.Length + 1
  }
}
function Add-Text($slide, $x, $y, $w, $h, [string[]]$paragraphs, $size, $color, $bold = $false, $align = 1, $name = 'Text') {
  $box = $slide.Shapes.AddTextbox(1, $x, $y, $w, $h)
  $box.Name = $name
  $tf = $box.TextFrame; $tf.WordWrap = -1; $tf.AutoSize = 0
  $tf.MarginLeft = 0; $tf.MarginRight = 0; $tf.MarginTop = 0; $tf.MarginBottom = 0
  Set-Rich $tf.TextRange $paragraphs $size $color $bold
  $tf.TextRange.ParagraphFormat.Alignment = $align
  $box
}
function Format-List($range, [int]$size) {
  $range.ParagraphFormat.LineRuleAfter = 0; $range.ParagraphFormat.SpaceAfter = [Math]::Round($size * 0.85)
  $range.ParagraphFormat.LineRuleWithin = -1; $range.ParagraphFormat.SpaceWithin = 1.1
  $range.ParagraphFormat.Bullet.Visible = 0
}
# Grey rounded panel; an optional heading is the first paragraph, bold and orange like the reference cards.
# Measured to its text, then stretched to $minHeight with the text centred vertically.
function Add-Panel($slide, $x, $y, $w, [string[]]$items, $minHeight, $size = 19, [string]$heading = '') {
  $panel = $slide.Shapes.AddShape(5, $x, $y, $w, 100)
  $panel.Name = 'Panel'
  $panel.Adjustments.Item(1) = 0.05
  $panel.Fill.ForeColor.RGB = $C_PANEL; $panel.Line.Visible = 0; $panel.Shadow.Visible = 0
  $tf = $panel.TextFrame; $tf.WordWrap = -1; $tf.VerticalAnchor = 1
  $tf.MarginLeft = 26; $tf.MarginRight = 26; $tf.MarginTop = 22; $tf.MarginBottom = 22
  $all = @(); if ($heading) { $all += $heading }; $all += $items
  Set-Rich $tf.TextRange $all $size $C_INK
  $tf.TextRange.ParagraphFormat.Alignment = 1
  Format-List $tf.TextRange $size
  if ($heading) { $h = $tf.TextRange.Paragraphs(1); $h.Font.Bold = -1; $h.Font.Color.RGB = $C_ORANGE; $h.Font.Size = $size + 3 }
  $tf.AutoSize = 1; $natural = $panel.Height; $tf.AutoSize = 0
  if ($minHeight -gt $natural) { $panel.Height = [single]$minHeight; $tf.VerticalAnchor = 3 }
  $panel
}
# Picture scaled to fit the box keeping its ratio; screenshots get a hairline so white UI does not melt into the page.
function Add-Image($slide, [string]$path, $x, $y, $w, $h, [bool]$frame, $alt, $valign = 'top') {
  $full = Join-Path $root $path
  $pic = $slide.Shapes.AddPicture($full, 0, -1, $x, $y)
  $pic.LockAspectRatio = -1
  $scale = [Math]::Min($w / $pic.Width, $h / $pic.Height)
  $pic.Width = $pic.Width * $scale
  $pic.Left = $x + ($w - $pic.Width) / 2
  [single]$top = $y; if ($valign -eq 'middle') { $top = $y + ($h - $pic.Height) / 2 }
  $pic.Top = $top
  $pic.AlternativeText = $alt; $pic.Name = 'Picture'
  if ($frame) { $pic.Line.Visible = -1; $pic.Line.ForeColor.RGB = $C_RULE; $pic.Line.Weight = 0.75 }
  $pic
}
function Add-Table($slide, $rows, $x, $y, $w, $size = 16) {
  $cols = $rows[0].Count
  $shape = $slide.Shapes.AddTable($rows.Count, $cols, $x, $y, $w, 30 * $rows.Count)
  $shape.Name = 'Table'
  $t = $shape.Table
  # Column widths follow the longest cell text, with a floor so short columns stay readable.
  $weights = @(); for ($c = 0; $c -lt $cols; $c++) { $max = ($rows | ForEach-Object { (Parse-Rich $_[$c]).text.Length } | Measure-Object -Maximum).Maximum; $weights += [Math]::Max(10, [Math]::Min(46, $max)) }
  $sum = ($weights | Measure-Object -Sum).Sum
  for ($c = 0; $c -lt $cols; $c++) { $t.Columns.Item($c + 1).Width = $w * $weights[$c] / $sum }
  for ($r = 0; $r -lt $rows.Count; $r++) {
    for ($c = 0; $c -lt $cols; $c++) {
      $cell = $t.Cell($r + 1, $c + 1)
      $cell.Shape.Fill.Visible = -1; $cell.Shape.Fill.Solid()
      $cell.Shape.Fill.ForeColor.RGB = if ($r -eq 0) { $C_BLUE } elseif ($r % 2 -eq 0) { $C_ROW } else { $C_WHITE }
      $tf = $cell.Shape.TextFrame; $tf.MarginLeft = 12; $tf.MarginRight = 12; $tf.MarginTop = 7; $tf.MarginBottom = 7; $tf.VerticalAnchor = 3
      Set-Rich $tf.TextRange @($rows[$r][$c]) $size $(if ($r -eq 0) { $C_WHITE } else { $C_INK }) ($r -eq 0)
      foreach ($side in 1, 2, 3, 4) { $border = $cell.Borders.Item($side); $border.Visible = -1; $border.ForeColor.RGB = $C_RULE; $border.Weight = 0.75 }
    }
  }
  for ($r = 1; $r -le $rows.Count; $r++) { $t.Rows.Item($r).Height = 34 }
  $shape
}
# Big number over a short label, on a grey card.
function Add-Stat($slide, $x, $y, $w, $h, [string]$value, [string]$label) {
  $card = $slide.Shapes.AddShape(5, $x, $y, $w, $h); $card.Name = 'Stat'
  $card.Adjustments.Item(1) = 0.08; $card.Fill.ForeColor.RGB = $C_PANEL; $card.Line.Visible = 0; $card.Shadow.Visible = 0
  $tf = $card.TextFrame; $tf.WordWrap = -1; $tf.VerticalAnchor = 3; $tf.MarginLeft = 14; $tf.MarginRight = 14; $tf.MarginTop = 10; $tf.MarginBottom = 10
  Set-Rich $tf.TextRange @($value, $label) 18 $C_INK
  $tf.TextRange.ParagraphFormat.Alignment = 2
  $v = $tf.TextRange.Paragraphs(1); $v.Font.Bold = -1; $v.Font.Size = 44; $v.Font.Color.RGB = $C_BLUE; $v.ParagraphFormat.SpaceAfter = 4
}
# Two panels side by side, equal height, from $y down to $bottom (or their natural height if larger).
function Add-PanelPair($slide, $cards, $y, $bottom, $size = 19) {
  $colW = ($W - $GAP) / 2
  $l = Add-Panel $slide $X0 $y $colW @($cards[0][1]) ($bottom - $y) $size $cards[0][0]
  $r = Add-Panel $slide ($X0 + $colW + $GAP) $y $colW @($cards[1][1]) ($bottom - $y) $size $cards[1][0]
  [single]$ph = [Math]::Max([single]$l.Height, [single]$r.Height); $l.Height = $ph; $r.Height = $ph
  @($l, $r)
}
function Add-PageNumber($slide, $n, $color) { [void](Add-Text $slide 1330 757 70 24 @("$n") 18 $color $false 3 'Slide Number') }
function Add-Heading($slide, [string]$title) { [void](Add-Text $slide $X0 96 $W 50 @($title) 34 $C_BLUE $true 1 'Title') }
function Set-Notes($slide, [string]$text) { $slide.NotesPage.Shapes.Placeholders.Item(2).TextFrame.TextRange.Text = ((Parse-Rich $text).text) }
function New-Frame($pres, $kind) {
  $frame = $FRAMES[$kind]
  $copy = $pres.Slides.Item($frame.index).Duplicate()
  $copy.MoveTo($pres.Slides.Count)
  $slide = $pres.Slides.Item($pres.Slides.Count)
  for ($i = $slide.Shapes.Count; $i -ge 1; $i--) { $sh = $slide.Shapes.Item($i); if ($frame.keep -notcontains $sh.Name) { $sh.Delete() } }
  $slide
}

$pp = New-Object -ComObject PowerPoint.Application
$pres = $pp.Presentations.Open($Template, -1, 0, 0)
try {
  $templateCount = $pres.Slides.Count
  $n = 0
  foreach ($spec in $data.slides) {
    $n++
    if ($spec.kind -eq 'section') {
      $s = New-Frame $pres 'section'
      [void](Add-Text $s 110 270 1220 200 @((Balance-Title "$($spec.number). $($spec.title)" 36)) 44 $C_BLUE $true 2 'Title')
      $s.Shapes.Item('Title').TextFrame.VerticalAnchor = 3
      Add-PageNumber $s $n $C_INK
      Set-Notes $s ''
      continue
    }
    $img = $spec.images
    switch ($spec.layout) {
      'cover' {
        $s = New-Frame $pres 'cover'
        [void](Add-Text $s 120 120 1200 60 @($TXT.course) 44 $C_RED $true 2 'Course')
        [void](Add-Text $s 60 196 1320 130 @($TXT.product) 96 $C_COVER $true 2 'Product')
        [void](Add-Text $s 120 340 1200 80 @($TXT.tagline) 26 $C_INK $true 2 'Tagline')
        [void](Add-Text $s 120 462 1200 36 @($TXT.advisor) 24 $C_INK $true 2 'Advisor')
        [void](Add-Text $s 120 508 1200 40 @($TXT.members) 24 $C_INK $false 2 'Members')
        Set-Notes $s $spec.notes
      }
      'agenda' {
        $s = New-Frame $pres 'agenda'
        $y = 286; $i = 0
        foreach ($item in $spec.items) { $i++; [void](Add-Text $s 168 $y 1100 44 @("$i. $item") 26 $C_INK $true 1 "Chapter $i"); $y += 110 }
        Add-PageNumber $s $n $C_BLUE
        Set-Notes $s $spec.notes
      }
      'end' {
        $s = New-Frame $pres 'ending'
        [void](Add-Text $s 100 268 1240 60 @($TXT.thanks) 40 $C_INK $true 2 'Thanks')
        [void](Add-Text $s 100 346 1240 36 @($TXT.team) 26 $C_BLUE $true 2 'Team')
        [void](Add-Panel $s 300 420 840 @($spec.items) 0 20)
        Set-Notes $s $spec.notes
      }
      default {
        $s = New-Frame $pres 'content'
        Add-Heading $s $spec.title
        $bodyH = $BODY_BOTTOM - $BODY_TOP
        switch ($spec.layout) {
          { $_ -in 'text-img', 'img-text' } {
            $imgW = 664; $textW = $W - $imgW - $GAP
            $imgX = if ($spec.layout -eq 'text-img') { $X0 + $textW + $GAP } else { $X0 }
            $textX = if ($spec.layout -eq 'text-img') { $X0 } else { $X0 + $imgW + $GAP }
            $pic = Add-Image $s $img[0].path $imgX $BODY_TOP $imgW $bodyH $true $img[0].alt 'middle'
            [void](Add-Panel $s $textX $BODY_TOP $textW @($spec.items) $bodyH 21)
          }
          'img-top' {
            # Panels along the bottom, the picture filling the space above.
            $pair = Add-PanelPair $s $spec.cards $BODY_TOP 0 21
            $pairTop = [single]($BODY_BOTTOM - $pair[0].Height); $pair[0].Top = $pairTop; $pair[1].Top = $pairTop
            $isShot = -not ($img[0].path -like '*architecture*')
            [void](Add-Image $s $img[0].path $X0 $BODY_TOP $W ($pairTop - $BODY_TOP - $GAP) $isShot $img[0].alt 'middle')
          }
          'table-img' {
            $tw = 760
            [void](Add-Table $s $spec.table $X0 $BODY_TOP $tw 20)
            [void](Add-Image $s $img[0].path ($X0 + $tw + 30) $BODY_TOP ($W - $tw - 30) $bodyH $true $img[0].alt 'middle')
          }
          'table-text' {
            $tw = 760
            # Table and panel share one height and sit centred in the body area.
            $tbl = @(Add-Table $s $spec.table $X0 $BODY_TOP $tw 20)[-1]
            $p = Add-Panel $s ($X0 + $tw + $GAP) $BODY_TOP ($W - $tw - $GAP) @($spec.items) $tbl.Height 21
            [single]$h = [Math]::Max([single]$tbl.Height, [single]$p.Height); $p.Height = $h
            $tbl.Top = [single]($BODY_TOP + ($bodyH - $h) / 3); $p.Top = [single]$tbl.Top
          }
          'stats' {
            $k = $spec.stats.Count; $cw = ($W - ($k - 1) * $GAP) / $k; $x = $X0
            foreach ($st in $spec.stats) { Add-Stat $s $x $BODY_TOP $cw 150 $st[0] $st[1]; $x += $cw + $GAP }
            [void](Add-PanelPair $s $spec.cards ($BODY_TOP + 150 + $GAP) $BODY_BOTTOM 21)
          }
          'compare' { [void](Add-PanelPair $s $spec.cards $BODY_TOP $BODY_BOTTOM 23) }
          'table-top-img' {
            $tbl = @(Add-Table $s $spec.table $X0 $BODY_TOP $W 20)[-1]
            $y = $BODY_TOP + $tbl.Height + $GAP
            [void](Add-Image $s $img[0].path $X0 $y $W ($BODY_BOTTOM - $y) $true $img[0].alt 'middle')
          }
          'table-top' {
            $tbl = @(Add-Table $s $spec.table $X0 $BODY_TOP $W 20)[-1]
            $y = $BODY_TOP + $tbl.Height + $GAP
            [void](Add-Panel $s $X0 $y $W @($spec.items) ($BODY_BOTTOM - $y) 22)
          }
          'quad' {
            $cw = ($W - $GAP) / 2; $ch = ($bodyH - $GAP) / 2; $i = 0
            foreach ($card in $spec.cards) {
              $x = $X0 + ($i % 2) * ($cw + $GAP); $y = $BODY_TOP + [Math]::Floor($i / 2) * ($ch + $GAP)
              [void](Add-Panel $s $x $y $cw @($card[1]) $ch 23 $card[0]); $i++
            }
          }
        }
        Add-PageNumber $s $n $C_BLUE
        Set-Notes $s $spec.notes
      }
    }
  }
  for ($i = 1; $i -le $templateCount; $i++) { $pres.Slides.Item(1).Delete() }
  # Anything added must stay between the header band and the footer strip.
  $k = 0
  foreach ($slide in $pres.Slides) { $k++; foreach ($sh in $slide.Shapes) { if ($sh.Name -in 'Title','Panel','Picture','Table','Stat','Text','Thanks','Team','Tagline','Advisor','Members','Course','Product' -and ($sh.Top + $sh.Height -gt 790 -or $sh.Left + $sh.Width -gt 1400)) { Write-Warning "slide ${k}: $($sh.Name) ends at $([int]($sh.Top + $sh.Height)) x $([int]($sh.Left + $sh.Width))" } } }
  # Embed the fonts (Montserrat must be installed here) so the deck renders the same on the presentation PC.
  $pres.SaveAs($Out, 24, -1)
  "Built $($pres.Slides.Count) slides -> $Out"
} finally {
  $pres.Close(); $pp.Quit()
}
