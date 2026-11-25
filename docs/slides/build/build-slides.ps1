# Builds docs/slides/KhoGuard-thuyet-trinh.pptx from docs/NOI_DUNG_SLIDE.md on the HUIT frame of a reference deck.
# The reference keeps its frame (header band, logo, campus photo, footer strip, huit.edu.vn) as per-slide groups, so
# each new slide duplicates the matching reference slide, deletes everything but the frame and adds its own content.
# Needs PowerPoint (COM). Usage, from the repository root:
#   node docs/slides/build/parse-slides.mjs > docs/slides/build/slides.json
#   powershell -NoProfile -ExecutionPolicy Bypass -File docs/slides/build/build-slides.ps1 -Template "<reference.pptx>"
param(
  [Parameter(Mandatory = $true)][string]$Template,
  [string]$SpecPath = "docs\slides\build\slides.json",
  [string]$Out = "docs\slides\KhoGuard-thuyet-trinh.pptx",
  [int]$Limit = 0
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$SpecPath = Join-Path $root $SpecPath; $Out = Join-Path $root $Out
$data = Get-Content -LiteralPath $SpecPath -Raw -Encoding UTF8 | ConvertFrom-Json
$TXT = $data.strings

# Reference slides used as frames and the frame shapes kept on each.
$FRAMES = @{
  cover   = @{ index = 1;  keep = @('Group 2','Group 4','Group 6','TextBox 8','Group 9','TextBox 11','Group 12') }
  agenda  = @{ index = 2;  keep = @('Group 2','Group 4','Freeform 6','Freeform 7','TextBox 8','Group 9','Group 13','TextBox 16') }
  section = @{ index = 3;  keep = @('Group 2','Group 4','Group 6','TextBox 8','Group 9','Group 11','TextBox 13') }
  content = @{ index = 5;  keep = @('Group 2','Group 4','Freeform 6','Freeform 7','TextBox 9') }
  ending  = @{ index = 22; keep = @('Group 2','TextBox 4','Group 5','Group 10','Group 12','TextBox 14') }
}
# Reference palette (sampled from the template) and content geometry in points on the 1440 x 810 canvas.
function RGB([string]$hex) { [int]('0x' + $hex.Substring(4,2)) * 65536 + [int]('0x' + $hex.Substring(2,2)) * 256 + [int]('0x' + $hex.Substring(0,2)) }
$C_BLUE = RGB '0070C0'; $C_NAVY = RGB '034EA2'; $C_COVER = RGB '00529C'; $C_RED = RGB 'ED1C24'; $C_ORANGE = RGB 'F27121'
$C_INK = RGB '1F2328'; $C_PANEL = RGB 'F2F2F2'; $C_RULE = RGB 'D0D5DA'; $C_WHITE = RGB 'FFFFFF'; $C_ROW = RGB 'F5F7F9'
$FONT = 'Montserrat'; $CODE = 'Consolas'
$X0 = 53; $W = 1334; $BODY_TOP = 168; $BODY_BOTTOM = 752

# Long headings break once, at the space nearest the middle, so the two lines are even (PowerPoint does not balance).
function Balance-Title([string]$text, [int]$max) {
  if ($text.Length -le $max) { return $text }
  $mid = [int]($text.Length / 2); $best = -1
  for ($i = 0; $i -lt $text.Length; $i++) { if ($text[$i] -eq ' ' -and ($best -lt 0 -or [Math]::Abs($i - $mid) -lt [Math]::Abs($best - $mid))) { $best = $i } }
  if ($best -lt 0) { return $text }
  $text.Substring(0, $best) + [char]11 + $text.Substring($best + 1)
}

# Inline **bold** and `code` become runs; returns plain text plus the character spans to format.
function Parse-Rich([string]$text) {
  $plain = New-Object System.Text.StringBuilder; $spans = @()
  $pattern = '\*\*(.+?)\*\*|`(.+?)`'
  $last = 0
  foreach ($m in [regex]::Matches($text, $pattern)) {
    [void]$plain.Append($text.Substring($last, $m.Index - $last))
    $body = if ($m.Groups[1].Success) { $m.Groups[1].Value } else { $m.Groups[2].Value }
    $spans += [pscustomobject]@{ start = $plain.Length; length = $body.Length; kind = $(if ($m.Groups[1].Success) { 'bold' } else { 'code' }) }
    [void]$plain.Append($body); $last = $m.Index + $m.Length
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
    foreach ($s in $p.spans) {
      $chars = $range.Characters($offset + $s.start + 1, $s.length)
      if ($s.kind -eq 'bold') { $chars.Font.Bold = -1 } else { $chars.Font.Name = $CODE; $chars.Font.Size = [Math]::Max(14, $size - 2) }
    }
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
# Points are separated by paragraph space rather than bullet dots; ordered lists keep their numbers.
function Format-List($range, [bool]$ordered, [int]$size) {
  $range.ParagraphFormat.LineRuleAfter = 0; $range.ParagraphFormat.SpaceAfter = [Math]::Round($size * 0.85)
  $range.ParagraphFormat.LineRuleWithin = -1; $range.ParagraphFormat.SpaceWithin = 1.1
  $b = $range.ParagraphFormat.Bullet
  if ($ordered) { $b.Visible = -1; $b.Type = 2; $b.Style = 3; $b.Font.Color.RGB = $C_BLUE; $b.RelativeSize = 1 } else { $b.Visible = 0 }
}
# Grey rounded panel holding a bulleted list; measured to its text, then stretched to $minHeight.
function Add-Panel($slide, $x, $y, $w, [string[]]$items, [bool]$ordered, $minHeight, $size = 20) {
  $panel = $slide.Shapes.AddShape(5, $x, $y, $w, 100)
  $panel.Name = 'Panel'
  $panel.Adjustments.Item(1) = 0.05
  $panel.Fill.ForeColor.RGB = $C_PANEL; $panel.Line.Visible = 0; $panel.Shadow.Visible = 0
  $tf = $panel.TextFrame; $tf.WordWrap = -1; $tf.VerticalAnchor = 1
  $tf.MarginLeft = 26; $tf.MarginRight = 26; $tf.MarginTop = 24; $tf.MarginBottom = 24
  Set-Rich $tf.TextRange $items $size $C_INK
  $tf.TextRange.ParagraphFormat.Alignment = 1
  Format-List $tf.TextRange $ordered $size
  [single]$hang = 0; if ($ordered) { $hang = [Math]::Round($size * 1.4) }
  $tf.Ruler.Levels(1).FirstMargin = 0; $tf.Ruler.Levels(1).LeftMargin = $hang
  $tf.AutoSize = 1; $natural = $panel.Height; $tf.AutoSize = 0
  # Stretched to sit level with its picture, the list is centred rather than leaving a blank lower half.
  if ($minHeight -gt $natural) { $panel.Height = $minHeight; $tf.VerticalAnchor = 3 }
  $panel
}
# Picture scaled to fit the box, keeping its ratio; screenshots get a hairline so white UI does not melt into the page.
function Add-Image($slide, [string]$path, $x, $y, $w, $h, [bool]$frame, $alt, $valign = 'top') {
  $full = if ([IO.Path]::IsPathRooted($path)) { $path } else { Join-Path $root $path }
  $pic = $slide.Shapes.AddPicture($full, 0, -1, $x, $y)
  $pic.LockAspectRatio = -1
  if ($full -like '*.svg') {
    # The diagrams are drawn as full 1600x900 slides with their own title (y<150) and caption (y>790);
    # the slide already has the title, so keep only the drawing and let it use the space.
    $k = $pic.Width / 1600
    $pic.PictureFormat.CropTop = 160 * $k; $pic.PictureFormat.CropBottom = 108 * $k
    $pic.PictureFormat.CropLeft = 40 * $k; $pic.PictureFormat.CropRight = 40 * $k
  }
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
  $shape = $slide.Shapes.AddTable($rows.Count, $cols, $x, $y, $w, 40 * $rows.Count)
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
      $tf = $cell.Shape.TextFrame; $tf.MarginLeft = 12; $tf.MarginRight = 12; $tf.MarginTop = 8; $tf.MarginBottom = 8; $tf.VerticalAnchor = 3
      Set-Rich $tf.TextRange @($rows[$r][$c]) $size $(if ($r -eq 0) { $C_WHITE } else { $C_INK }) ($r -eq 0)
      foreach ($side in 1, 2, 3, 4) { $border = $cell.Borders.Item($side); $border.Visible = -1; $border.ForeColor.RGB = $C_RULE; $border.Weight = 0.75 }
    }
  }
  for ($r = 1; $r -le $rows.Count; $r++) { $t.Rows.Item($r).Height = 30 }
  $shape
}
function Add-PageNumber($slide, $n, $color) {
  $box = Add-Text $slide 1330 757 70 24 @("$n") 18 $color $false 3 'Slide Number'
}
function Add-Heading($slide, $spec) {
  [void](Add-Text $slide $X0 96 $W 50 @($spec.title) 34 $C_BLUE $true 1 'Title')
}
function Set-Notes($slide, [string]$text) {
  $slide.NotesPage.Shapes.Placeholders.Item(2).TextFrame.TextRange.Text = ((Parse-Rich $text).text)
}
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
    if ($Limit -and $n -gt $Limit) { break }
    if ($spec.kind -eq 'section') {
      $s = New-Frame $pres 'section'
      [void](Add-Text $s 110 270 1220 200 @((Balance-Title "$($spec.chapter.number). $($spec.chapter.title)" 36)) 44 $C_BLUE $true 2 'Title')
      $s.Shapes.Item('Title').TextFrame.VerticalAnchor = 3
      Add-PageNumber $s $n $C_INK
      Set-Notes $s ''
      continue
    }
    $img = $spec.images
    switch ($spec.layout) {
      'cover' {
        $s = New-Frame $pres 'cover'
        [void](Add-Text $s 120 128 1200 64 @($TXT.course) 46 $C_RED $true 2 'Course')
        [void](Add-Text $s 60 218 1320 170 @($TXT.product) 138 $C_COVER $true 2 'Product')
        [void](Add-Text $s 120 392 1200 46 @($TXT.tagline) 30 $C_INK $true 2 'Tagline')
        [void](Add-Text $s 120 462 1200 36 @($TXT.advisor) 26 $C_INK $true 2 'Advisor')
        [void](Add-Text $s 120 512 1200 40 @($TXT.members) 26 $C_INK $false 2 'Members')
        Set-Notes $s (($spec.items -join ' ') + ' ' + $spec.notes)
      }
      'agenda' {
        $s = New-Frame $pres 'agenda'
        $y = 286
        $i = 0
        foreach ($item in $spec.items) { $i++; [void](Add-Text $s 168 $y 840 44 @("$i. $($item.TrimEnd('.'))") 24 $C_INK $true 1 "Chapter $i"); $y += 88 }
        Add-PageNumber $s $n $C_BLUE
        Set-Notes $s $spec.notes
      }
      'end' {
        $s = New-Frame $pres 'ending'
        [void](Add-Text $s 100 268 1240 60 @($TXT.thanks) 40 $C_INK $true 2 'Thanks')
        [void](Add-Text $s 100 346 1240 36 @($spec.items[1].TrimEnd('.')) 26 $C_BLUE $true 2 'Team')
        $p = Add-Panel $s 300 420 840 @($spec.items[2], $spec.items[3]) $false 0 20
        Set-Notes $s $spec.notes
      }
      default {
        $s = New-Frame $pres 'content'
        Add-Heading $s $spec
        $bodyH = $BODY_BOTTOM - $BODY_TOP
        $frameShot = { param($p) $p -like '*.png' }
        # Diagrams carry small labels, so they get the wider column; screenshots and text split evenly.
        $gap = 24
        $imgW = if ($img.Count -and $img[0].path -like '*.svg') { 860 } else { 664 }
        $textW = $W - $imgW - $gap
        switch ($spec.layout) {
          { $_ -in 'text-img', 'img-text' -and $img[0].path -like '*.svg' } {
            # Diagrams are ~2.4:1, so beside text they stay short and leave the lower third empty.
            # Stack them instead: the points in two columns along the bottom, the diagram filling the rest.
            $half = [Math]::Ceiling($spec.items.Count / 2)
            $colW = ($W - $gap) / 2
            $left = Add-Panel $s $X0 $BODY_TOP $colW @($spec.items[0..($half - 1)]) $spec.ordered 0 19
            $right = Add-Panel $s ($X0 + $colW + $gap) $BODY_TOP $colW @($spec.items[$half..($spec.items.Count - 1)]) $spec.ordered 0 19
            if ($spec.ordered) { $right.TextFrame.TextRange.ParagraphFormat.Bullet.StartValue = $half + 1 }
            $ph = [Math]::Max($left.Height, $right.Height); $left.Height = $ph; $right.Height = $ph
            $top = $BODY_BOTTOM - $ph; $left.Top = $top; $right.Top = $top
            [void](Add-Image $s $img[0].path $X0 $BODY_TOP $W ($top - $BODY_TOP - $gap) $false $img[0].alt 'middle')
            break
          }
          { $_ -in 'text-img', 'img-text' } {
            $imgX = if ($spec.layout -eq 'text-img') { $X0 + $textW + $gap } else { $X0 }
            $textX = if ($spec.layout -eq 'text-img') { $X0 } else { $X0 + $imgW + $gap }
            $pic = Add-Image $s $img[0].path $imgX $BODY_TOP $imgW $bodyH (& $frameShot $img[0].path) $img[0].alt
            $panel = Add-Panel $s $textX $BODY_TOP $textW $spec.items $spec.ordered $pic.Height
          }
          'table-img' {
            $tw = 790
            $tbl = Add-Table $s $spec.table $X0 $BODY_TOP $tw 18
            [void](Add-Image $s $img[0].path ($X0 + $tw + 30) $BODY_TOP ($W - $tw - 30) $bodyH (& $frameShot $img[0].path) $img[0].alt)
          }
          'table-top' {
            $tbl = Add-Table $s $spec.table $X0 $BODY_TOP $W 18
            $y = $BODY_TOP + $tbl.Height + $gap
            [void](Add-Image $s $img[0].path $X0 $y $W ($BODY_BOTTOM - $y) (& $frameShot $img[0].path) $img[0].alt 'middle')
          }
          'img-quad' {
            [void](Add-Image $s $img[0].path $X0 $BODY_TOP $W 380 $false $img[0].alt 'middle')
            $cw = ($W - 3 * $gap) / 4; $x = $X0; $y = $BODY_TOP + 380 + 20
            foreach ($item in $spec.items) {
              $m = [regex]::Match($item, '^\*\*(.+?):\*\*\s*(.+)$')
              $card = $s.Shapes.AddShape(5, $x, $y, $cw, $BODY_BOTTOM - $y); $card.Name = 'Tier'
              $card.Adjustments.Item(1) = 0.06; $card.Fill.ForeColor.RGB = $C_PANEL; $card.Line.Visible = 0; $card.Shadow.Visible = 0
              $tf = $card.TextFrame; $tf.WordWrap = -1; $tf.VerticalAnchor = 1; $tf.MarginLeft = 18; $tf.MarginRight = 18; $tf.MarginTop = 16; $tf.MarginBottom = 14
              Set-Rich $tf.TextRange @($m.Groups[1].Value, $m.Groups[2].Value) 17 $C_INK
              $tf.TextRange.ParagraphFormat.Alignment = 1
              $head = $tf.TextRange.Paragraphs(1); $head.Font.Bold = -1; $head.Font.Color.RGB = $C_ORANGE; $head.Font.Size = 20; $head.ParagraphFormat.SpaceAfter = 6
              $x += $cw + $gap
            }
          }
          'two-img' {
            $half = [Math]::Ceiling($spec.items.Count / 2)
            $left = Add-Panel $s $X0 $BODY_TOP 655 @($spec.items[0..($half - 1)]) $false 0 19
            $right = Add-Panel $s ($X0 + 679) $BODY_TOP 655 @($spec.items[$half..($spec.items.Count - 1)]) $false 0 19
            $ph = [Math]::Max($left.Height, $right.Height); $left.Height = $ph; $right.Height = $ph
            $y = $BODY_TOP + $ph + 24
            [void](Add-Image $s $img[0].path $X0 $y 655 ($BODY_BOTTOM - $y) $false $img[0].alt 'middle')
            [void](Add-Image $s $img[1].path ($X0 + 679) $y 655 ($BODY_BOTTOM - $y) $true $img[1].alt 'middle')
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
  foreach ($slide in $pres.Slides) { $k++; foreach ($sh in $slide.Shapes) { if ($sh.Name -in 'Title','Panel','Picture','Table','Tier','Text','Thanks','Team','Tagline','Advisor','Members','Course','Product' -and ($sh.Top + $sh.Height -gt 790 -or $sh.Left + $sh.Width -gt 1400)) { Write-Warning "slide ${k}: $($sh.Name) ends at $([int]($sh.Top + $sh.Height)) x $([int]($sh.Left + $sh.Width))" } } }
  # Embed the fonts used (Montserrat must be installed here) so the deck renders the same on the presentation PC.
  $pres.SaveAs($Out, 24, -1)
  "Built $($pres.Slides.Count) slides -> $Out"
} finally {
  $pres.Close(); $pp.Quit()
}
