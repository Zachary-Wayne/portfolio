<#
.DESCRIPTION
### PDF Splitter Tool
Separates statement PDFs into individual PDF files.

**Export Format:**
 - `Label_<ClientName>_<Month>-<Year>.pdf`

.NOTES
    Author: Zachary Wayne
#>

param (
    [string]$BaseDir,
    [string]$Statements = "$PSScriptRoot",
    [string]$Trading,
    [string]$TradeDL,
    [string]$TradeUL,
    [string]$Scripts = "$PSScriptRoot",
    [string]$Exports = "$PSScriptRoot"
)


$pathInput = $Statements
$pathOutput = $Exports

Write-Host "Looking for files in $pathInput"

$iTextSharpFolder = Join-Path $Scripts "itextsharp"

$iTextSharpPath = Resolve-Path -Path (Join-Path $iTextSharpFolder "itextsharp.dll")
$BouncyCastlePath = Resolve-Path -Path (Join-Path $iTextSharpFolder "BouncyCastle.Cryptography.dll")

#try {
Write-Host $iTextSharpPath
Write-Host $BouncyCastlePath
[System.Reflection.Assembly]::LoadFrom($iTextSharpPath)
[System.Reflection.Assembly]::LoadFrom($BouncyCastlePath)
#} catch {
#	Write-Host "Failed to load dependencies. Make sure you have the library folder 'itextsharp\' in the script folder!" -ForegroundColor Yellow
#	Write-Host $iTextSharpPath
#	Write-Host $BouncyCastlePath
#	Write-Debug $PSitem
#	return
#}

# Prevent GUI blurriness
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
if (-not ([System.Management.Automation.PSTypeName]'DPI').Type) {
	Add-Type -TypeDefinition @"
	using System;
	using System.Runtime.InteropServices;
	public class DPI {
		[DllImport("user32.dll")]
		public static extern bool SetProcessDPIAware();
	}
"@
}
[DPI]::SetProcessDPIAware() | Out-Null

# File selection
$FileBrowser = New-Object System.Windows.Forms.OpenFileDialog
$FileBrowser.InitialDirectory = $pathInput
$FileBrowser.Filter = "PDF Files (*.pdf)|*.pdf"
$FileBrowser.Title = "Select a PDF File to Split by Month"

if ($FileBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
	$PdfPath = $FileBrowser.FileName
	Write-Host "Splitting: $PdfPath`n" -ForegroundColor Cyan
} else {
	Write-Warning "No file selected"
	return
}

$Months = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$MonthArray = @("January", "Jan", "February", "Feb", "March", "Mar", "April", "Apr", "May", "June", "Jun", 
 "July", "Jul", "August", "Aug", "September", "Sep", "Sept", "October", "Oct", 
 "November", "Nov", "December", "Dec")
$MonthArray | ForEach-Object { $Months.Add($_) | Out-Null }

$FileNameWithoutExt = [System.IO.Path]::GetFileNameWithoutExtension($PdfPath)
$OutputFolder = Join-Path $pathOutput $FileNameWithoutExt

if (-not (Test-Path $OutputFolder)) {
	New-Item -ItemType Directory -Path $OutputFolder | Out-Null
}

# --- Try to extract Month and Year from the filename ---
$DateFoundInFilename = $false
$FilenameDateSuffix = ""

$MonthRegexPattern = "([a-zA-Z]+)\s+(\d{4})"
if ($FileNameWithoutExt -match $MonthRegexPattern) {
	$ExtractedMonth = $Matches[1]
	$ExtractedYear = $Matches[2]

	if ($Months.Contains($ExtractedMonth)) {
		$CleanMonth = (Get-Culture).TextInfo.ToTitleCase($ExtractedMonth.ToLower())
		$FilenameDateSuffix = "${CleanMonth}_${ExtractedYear}"
		$DateFoundInFilename = $true
	}
}

try {
	$Reader = New-Object iTextSharp.text.pdf.PdfReader($PdfPath)
	$TotalPages = $Reader.NumberOfPages
	$MonthMarkers = [System.Collections.Generic.List[PSCustomObject]]::new()

	for ($page = 1; $page -le $TotalPages; $page++) {
		$Strategy = New-Object iTextSharp.text.pdf.parser.LocationTextExtractionStrategy
		$PageText = [iTextSharp.text.pdf.parser.PdfTextExtractor]::GetTextFromPage($Reader, $page, $Strategy)

		if (-not [string]::IsNullOrWhiteSpace($PageText)) {
			$Lines = $PageText -split '\r?\n' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
			
			if ($Lines.Count -gt 0) {
				if ($Lines[0] -match '^\b\w+\b') {
					$FirstWord = $Matches[0]

					if ($Months.Contains($FirstWord)) {
						if ($DateFoundInFilename) {
							$DateSuffix = $FilenameDateSuffix
						} else {
							if ($Lines[0] -match '^(\w+)\s+\d{1,2},\s+(\d{4})') {
								$RawMonth = $Matches[1]
								$Year = $Matches[2]
								$CleanMonth = (Get-Culture).TextInfo.ToTitleCase($RawMonth.ToLower())
								$DateSuffix = "${CleanMonth}_${Year}"
							} else {
								$CleanMonth = (Get-Culture).TextInfo.ToTitleCase($FirstWord.ToLower())
								$DateSuffix = "${CleanMonth}_Workbook"
							}
						}

						$PersonName = "Unknown_Name"
						if ($Lines.Count -gt 1) {
							$PersonName = $Lines[1]
							$InvalidChars = [System.IO.Path]::GetInvalidFileNameChars()
							foreach ($char in $InvalidChars) {
								$EscapedChar = [regex]::Escape($char)
								$PersonName = $PersonName -replace $EscapedChar, ""
							}
							$PersonName = $PersonName.Trim()
						}

						$MonthMarkers.Add([PSCustomObject]@{
							Page       = $page
							PersonName = $PersonName
							DateSuffix = $DateSuffix
							Lines      = $Lines 
							FullText   = $PageText
						})
					}
				}
			}
		}
	}

	if ($MonthMarkers.Count -eq 0) {
		Write-Warning "No pages starting with a month were found. Document will not be split."
		return
	}

	$InvalidChars = [System.IO.Path]::GetInvalidFileNameChars()

	for ($i = 0; $i -lt $MonthMarkers.Count; $i++) {
		$StartPage = $MonthMarkers[$i].Page
		$PersonName = $MonthMarkers[$i].PersonName
		$DateSuffix = $MonthMarkers[$i].DateSuffix
		$PageLines  = $MonthMarkers[$i].Lines
		$FullText   = $MonthMarkers[$i].FullText
		
		if ($i + 1 -lt $MonthMarkers.Count) {
			$EndPage = $MonthMarkers[$i + 1].Page - 1
		} else {
			$EndPage = $TotalPages
		}

		$OutputFileName = "Letter_$PersonName-$DateSuffix.pdf"
		$FinalOutputPath = Join-Path $OutputFolder $OutputFileName

		if (Test-Path $FinalOutputPath) {
			$AlternativeName = ""

			if ($FullText -match '(?m)^Re:\s*(.+)$') {
				$AlternativeName = $Matches[1].Trim()
			}
			elseif ($PageLines.Count -gt 2) {
				$AlternativeName = $PageLines[2].Trim()
			}

			if (-not [string]::IsNullOrWhiteSpace($AlternativeName)) {
				foreach ($char in $InvalidChars) {
					$EscapedChar = [regex]::Escape($char)
					$AlternativeName = $AlternativeName -replace $EscapedChar, ""
				}
				$PersonName = $AlternativeName.Trim()
				$OutputFileName = "Letter_$PersonName-$DateSuffix.pdf"
				$FinalOutputPath = Join-Path $OutputFolder $OutputFileName
			}

			$CollisionCount = 1
			while (Test-Path $FinalOutputPath) {
				$OutputFileName = "Letter_$PersonName-$DateSuffix-($CollisionCount).pdf"
				$FinalOutputPath = Join-Path $OutputFolder $OutputFileName
				$CollisionCount++
			}
		}

		$FileStream = New-Object System.IO.FileStream($FinalOutputPath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
		$Document = New-Object iTextSharp.text.Document
		$PdfCopy = New-Object iTextSharp.text.pdf.PdfCopy($Document, $FileStream)

		try {
			$Document.Open()
			for ($p = $StartPage; $p -le $EndPage; $p++) {
				$ImportedPage = $PdfCopy.GetImportedPage($Reader, $p)
				$PdfCopy.AddPage($ImportedPage)
			}
		} finally {
			if ($PdfCopy)   { $PdfCopy.Close() }
			if ($Document)  { $Document.Close() }
			if ($FileStream){ $FileStream.Close() }
		}

		Write-Host "[Pages $StartPage to $EndPage] " -NoNewline -ForegroundColor Gray
		Write-Host "Created: " -NoNewline -ForegroundColor Green
		Write-Host "$OutputFileName" -ForegroundColor Yellow
	}

} catch {
	Write-Error "An error occurred during extraction processing: $_"
} finally {
	if (-not $DateFoundInFilename) {
		Write-Host "Date could not be found in the original file name. Used page-level fallback naming instead." -BackgroundColor Yellow -ForegroundColor Black
	}
	Write-Host "`nDone!" -ForegroundColor Cyan
	if ($Reader) { $Reader.Close() }
}