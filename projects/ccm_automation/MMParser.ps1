<#
.DESCRIPTION
### Trade Report MM Parser
Cleans and exports trade reports into a useable format.

**Usage Instructions:**
1. Export a money market report from the portfolio management system as a `Raw Comma Delimited CSV`.
2. Run this script to clean and format the report.

You will be given options to specify what currencies to export, accounts requiring aproval to act on, date, and export path.

*Make sure to check that the date matches!!!*
If you already cleaned a file but did not use the correct settings, the script should allow you to re-export without having to clean the CSV file again.

.NOTES
    Author: Zachary Wayne
#>
param (
    [string]$BaseDir,
    [string]$Statements,
    [string]$Trading,
    [string]$TradeDL = "$PSScriptRoot\Input\",
    [string]$TradeUL,
    [string]$Scripts,
    [string]$Exports = "$PSScriptRoot\Output\"
)

$pathInput = $TradeDL
$pathOutput = $Exports

# This will stop GUIs from being blurry on some monitors.
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

$inputFileSelection = New-Object System.Windows.Forms.OpenFileDialog
$inputFileSelection.InitialDirectory = $pathInput
$inputFileSelection.filter = "Raw Comma Separated Values File (*.csv)|*.csv"

if ($inputFileSelection.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK -and (Test-Path $inputFileSelection.FileName)) {
    $fileInput = $inputFileSelection.FileName
} else {
    exit
}

$fileName = [System.IO.Path]::GetFileNameWithoutExtension($fileInput)
$filePathOutFullCleaned = (Join-Path $pathOutput "${fileName}_cleaned.csv")
$filePathOutFullFormatted = (Join-Path $pathOutput "${fileName}_formatted.csv")

# OPERATION 1 - CLEAN CSV
<#
NOTES:

Error name: "Delimiter in notes field"
Example: row 2 of a custodian report
Detection Rule: "If initial_bal_date is empty or null"
Corrective Code:
	if row+1.mat_id is not blank, do the following:
		Add '`n' + contents from row+1.mat_id to row.notes. Append the remaining properties
		from row+1 to row starting with row.initial_bal_date.
		(The second property of row+1 will be row.initial_bal_date and so on)
	if row+1.mat_id is blank, do the following:
		Add '`n' to row.notes and keep adding '`n' for every row until non-blank,
		then go to the first if branch to repair row.

Error Name: "Bank name in the currency column"
Example: one account row in a custodian report.
Detection Rule: "If usd_fx_rate is empty or null"
Corrective Code:
	Apply the corrective code from "Delimiter in notes field" but use usd_account as the start index.
	Set the value of modifiedRow.usd_account to row.usd_account.
#>


if (Test-Path -Path $filePathOutFullCleaned){
	# This will allow the user to re-export already cleaned files.
	# Cleaning a file can take a while so this is good if the user just wants to re-export a file without waiting.
	$response = [System.Windows.Forms.MessageBox]::Show(
		"A cleaned copy of '$fileName' was found.
		`nWould you like to format and export this found report?
		`n- Selecting 'yes' will skip the cleaning process`n- Selecting 'no' will overwrite and clean this report",
		"Found cleaned report",
		[System.Windows.Forms.MessageBoxButtons]::YesNo,
		[System.Windows.Forms.MessageBoxIcon]::Question,
		[System.Windows.Forms.MessageBoxDefaultButton]::Button1,
		[System.Windows.Forms.MessageBoxOptions]::ServiceNotification
	)

	if ($response -eq [System.Windows.Forms.DialogResult]::No) {
		$doCleaning = $true
	}
	else {
		$doCleaning = $false
	}
} else {
	$doCleaning = $true
}


if ($doCleaning) {
	
	$rows = Import-Csv -Path $fileInput
	$cleaned = New-Object System.Collections.Generic.List[object]
	$totalRows = $rows.Count
	$lastCleanedEntry = "Looking for uncleaned data..."
	
	for ($index = 0; $index -lt $totalRows; $index++) {
		$percent = [Math]::Round(($index / $totalRows) * 100)
		Write-Progress 	`
			-Activity "Cleaning in progress... ($lastCleanedEntry)" `
			-Status "$percent% Complete:" `
			-PercentComplete $percent
			
		$row = $rows[$index]
		
		# Remove whitespace from all fields
		foreach ($prop in $row.PSObject.Properties) {
			if ($prop.Value -is [string]) {
				$prop.Value = $prop.Value.Trim()
			}
		}
		
		if (-not [string]::IsNullOrWhitespace($row.initial_bal_date)) {
			# If row is clean, keep it and move on
			$cleaned.Add($row)
			continue
		}
		
		# We found a broken row. Let's build the repaired row.
		$modifiedRow = $row | Select-Object *
		
		$next_index = $index + 1
		$maxLookahead = [Math]::Min($totalRows - 1, $index + 15)
		
		# Keep track of the notes we collect across lines
		$notesAccumulator = New-Object System.Text.StringBuilder
		[void]$notesAccumulator.Append($row.notes)
		
		while ($next_index -le $maxLookahead){
			$next = $rows[$next_index]
			
			# If the next row is just a continuation of notes (no account code)
			if ([string]::IsNullOrWhitespace($next.account_code)){
				# Grab whatever text was dumped into the first column (mat_id) of this broken row
				if (-not [string]::IsNullOrWhitespace($next.mat_id)) {
					[void]$notesAccumulator.Append("`n" + $next.mat_id.Trim())
				} else {
					[void]$notesAccumulator.Append("`n")
				}
				$next_index++
				continue
			}
			
			# Append its first column to our notes accumulator before shifting the remaining columns.
			if (-not [string]::IsNullOrWhitespace($next.mat_id)) {
				[void]$notesAccumulator.Append("`n" + $next.mat_id.Trim())
			}
			
			# Move misplaced fields structure 
			$properties = $row.PSObject.Properties.Name
			$startColumn = if ([string]::IsNullOrWhitespace($row.usd_fx_rate)){ # Fix for "Bank name in the currency column"
				"usd_account"
			} else {
				"notes"
			}

			$start = $properties.IndexOf($startColumn)
			$sourceValues = $next.PSObject.Properties.Value
			
			for ($i = 0; $i -lt $sourceValues.Count; $i++) {
				$field = $properties[$start + $i]
				if ($field) {
					$modifiedRow.$field = $sourceValues[$i]
				}
			}
			break
		}
		
		# Overwrite the notes column with newly consolidated notes
		$modifiedRow.notes = $notesAccumulator.ToString()
		
		$lastCleanedEntry = $modifiedRow.account_code
		
		$modifiedRow.usd_account = $row.usd_account # Fix for "Bank name in the currency column"
		
		$cleaned.Add($modifiedRow)
		$index = $next_index
	}
	$cleaned | Export-Csv -Path $filePathOutFullCleaned -NoTypeInformation
} else {
	$cleaned = Import-Csv -Path $filePathOutFullCleaned
}

# OPERATION 2 - FORMAT CSV

<#
Feilds are mapped to match the following:
	account_code,
	account_number, (USD account)
	fund/security currency, (Mapped by sec_cur_seq, picked by the user from the list of items in sec_cur)
	MM TO BUY,
	Granted approval (if funds over 100k),
	Portfolio manager name,
	initial_cash_bal, 
	initial_cash_bal - MM_TO_BUY / remainder

NOTE: All 'Funds' (sec_currency) in the example allocation sheet are listed as USD.

The goal of this script is to:
-	Create the daily money-market allocation sheet completely from nothing more than the raw custodian CSV export
	with a single (double) click and minimal additional inputs as required.
#>

# Reports may show past and future funds on different dates resulting in multiple entries.
# This will set the default date to a date found in the file name, and if not, the file creation date.
$regex = '(?<month>\d{2})[-_](?<day>\d{2})[-_](?<year>\d{4})$'
$defaultDate = (Get-Item $fileInput).CreationTime.Date
if ($filename -match $regex) {
	$day   = [int]$Matches.day
	$month = [int]$Matches.month
	$year  = [int]$Matches.year
    try {
		$defaultDate = Get-Date -Month $month -Day $day -Year $year
		Write-Host "Date found in file name, using file name date:`n`t$($defaultDate.Date)" 
	} catch {
		Write-Host "No date in file name found, using file creation date:`n`t$($defaultDate.Date)"
	}
}

$persistFile = Join-Path $PSScriptRoot "always_request_aproval.txt"
$initReqAprovalAccs = ""
if (Test-Path $persistFile) {
    $initReqAprovalAccs = Get-Content $persistFile -Raw
}

# Main Form Window
$form = New-Object System.Windows.Forms.Form
$form.Text = 'Export Options'
$form.Size = New-Object System.Drawing.Size(800, 680)
$form.StartPosition = 'CenterScreen'
$form.TopMost = $true
$form.FormBorderStyle = 'FixedSingle'
$form.MaximizeBox = $false

# Font Styling
$fontLabel = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Bold)
$fontInput = New-Object System.Drawing.Font("Segoe UI", 10)

# Settings & Inputs
$leftX = 30
$inputWidth = 320

# Date Selection
$labelDate = New-Object System.Windows.Forms.Label
$labelDate.Text = "Select Initial Balance Date:"
$labelDate.Font = $fontLabel
$labelDate.Location = New-Object System.Drawing.Point($leftX, 25)
$labelDate.AutoSize = $true
$form.Controls.Add($labelDate)

$comboDate = New-Object System.Windows.Forms.ComboBox
$comboDate.Font = $fontInput
$comboDate.Location = New-Object System.Drawing.Point($leftX, ($labelDate.Bottom + 5))
$comboDate.Size = New-Object System.Drawing.Size($inputWidth, 25)
$comboDate.DropDownStyle = 'DropDownList'

# Populate Dates
if ($cleaned -and $cleaned.initial_bal_date) {
    $availableDates = $cleaned.initial_bal_date | ForEach-Object { [datetime]$_ } | Where-Object { $_ -ne $null } | Sort-Object -Unique
    $availableDates | ForEach-Object { $comboDate.Items.Add($_.ToString('MM/dd/yyyy')) | Out-Null }
}
if ($defaultDate) {
    $defaultFormatted = $defaultDate.ToString('MM/dd/yyyy')
    if ($comboDate.Items.Contains($defaultFormatted)){ $comboDate.SelectedItem = $defaultFormatted }
}
if ($comboDate.SelectedIndex -eq -1 -and $comboDate.Items.Count -gt 0) { $comboDate.SelectedIndex = 0 }
$form.Controls.Add($comboDate)


# Threshold Value
$labelThreshold = New-Object System.Windows.Forms.Label
$labelThreshold.Text = "Require Approval Over ($):"
$labelThreshold.Font = $fontLabel
$labelThreshold.Location = New-Object System.Drawing.Point($leftX, ($comboDate.Bottom + 20))
$labelThreshold.AutoSize = $true
$form.Controls.Add($labelThreshold)

$boxThreshold = New-Object System.Windows.Forms.NumericUpDown
$boxThreshold.Font = $fontInput
$boxThreshold.Location = New-Object System.Drawing.Point($leftX, ($labelThreshold.Bottom + 5))
$boxThreshold.Size = New-Object System.Drawing.Size($inputWidth, 25)
$boxThreshold.Minimum = 0
$boxThreshold.Maximum = 10000000
$boxThreshold.Increment = 1000
$boxThreshold.Value = 1000000
$form.Controls.Add($boxThreshold)


# Always Require Approval List
$labelAlwaysApprove = New-Object System.Windows.Forms.Label
$labelAlwaysApprove.Text = "Always Require Aproval`n(Comma/Line Separated):"
$labelAlwaysApprove.Font = $fontLabel
$labelAlwaysApprove.Location = New-Object System.Drawing.Point($leftX, ($boxThreshold.Bottom + 20))
$labelAlwaysApprove.AutoSize = $true
$form.Controls.Add($labelAlwaysApprove)

$boxAlwaysApprove = New-Object System.Windows.Forms.TextBox
$boxAlwaysApprove.Font = $fontInput
$boxAlwaysApprove.Location = New-Object System.Drawing.Point($leftX, ($labelAlwaysApprove.Bottom + 5))
$boxAlwaysApprove.Size = New-Object System.Drawing.Size($inputWidth, 120)
$boxAlwaysApprove.Multiline = $true
$boxAlwaysApprove.ScrollBars = 'Vertical'
$boxAlwaysApprove.Text = $initReqAprovalAccs
$form.Controls.Add($boxAlwaysApprove)


# Currencies Checklist
$rightX = 410

$labelCur = New-Object System.Windows.Forms.Label
$labelCur.Text = "Select Currencies:"
$labelCur.Font = $fontLabel
$labelCur.Location = New-Object System.Drawing.Point($rightX, 25)
$labelCur.AutoSize = $true 
$form.Controls.Add($labelCur)

$listCur = New-Object System.Windows.Forms.CheckedListBox
$listCur.Font = $fontInput
$listCur.CheckOnClick = $true
$listCur.Location = New-Object System.Drawing.Point($rightX, ($labelCur.Bottom + 5))
$listCur.Size = New-Object System.Drawing.Size($inputWidth, 150)

# Populate currency list
if ($cleaned -and $cleaned.sec_currency) {
    $availableCurrencies = $cleaned.sec_currency | Where-Object { $_ -and $_.Trim() -ne '' } | Sort-Object -Unique
    $availableCurrencies | ForEach-Object { $listCur.Items.Add($_) | Out-Null }
}
$form.Controls.Add($listCur)

# Select All link for convenience
$btnSelectAll = New-Object System.Windows.Forms.Button
$btnSelectAll.Text = "Select All Currencies"
$btnSelectAll.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$btnSelectAll.BackColor = [System.Drawing.Color]::SeaGreen
$btnSelectAll.ForeColor = [System.Drawing.Color]::White
$btnSelectAll.Location = New-Object System.Drawing.Point($rightX, ($listCur.Bottom + 6))
$btnSelectAll.Size = New-Object System.Drawing.Size($inputWidth, 30)
$btnSelectAll.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$btnSelectAll.FlatAppearance.BorderSize = 0
$btnSelectAll.Add_Click({
    for ($i = 0; $i -lt $listCur.Items.Count; $i++) { $listCur.SetItemChecked($i, $true) }
})
$form.Controls.Add($btnSelectAll)

# Save File Path
$labelSaveAs = New-Object System.Windows.Forms.Label
$labelSaveAs.Text = "Output Save Path:"
$labelSaveAs.Font = $fontLabel
$labelSaveAs.Location = New-Object System.Drawing.Point($leftX, ($boxAlwaysApprove.Bottom + 25))
$labelSaveAs.AutoSize = $true 
$form.Controls.Add($labelSaveAs)

$boxSaveAs = New-Object System.Windows.Forms.TextBox
$boxSaveAs.Font = $fontInput
$boxSaveAs.Text = $filePathOutFullFormatted
$boxSaveAs.Location = New-Object System.Drawing.Point($leftX, ($labelSaveAs.Bottom + 5))
$boxSaveAs.Size = New-Object System.Drawing.Size(640, 25)
$boxSaveAs.ReadOnly = $true
$boxSaveAs.BackColor = [System.Drawing.Color]::FromArgb(230, 235, 240)
$form.Controls.Add($boxSaveAs)

# Browse Button (...)
$browseButton = New-Object System.Windows.Forms.Button
$browseButton.Text = "..."
$browseButton.Font = $fontInput
$browseButton.BackColor = [System.Drawing.Color]::SeaGreen
$browseButton.ForeColor = [System.Drawing.Color]::White
$browseButton.Location = New-Object System.Drawing.Point(($boxSaveAs.Right + 10), $boxSaveAs.Top)
$browseButton.Size = New-Object System.Drawing.Size(50, $boxSaveAs.Height)
$browseButton.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$browseButton.FlatAppearance.BorderSize = 0
$browseButton.Add_Click({
    $dialog = New-Object System.Windows.Forms.SaveFileDialog
    $dialog.Filter = "CSV files (*.csv)|*.csv"
    $dialog.FileName = $boxSaveAs.Text
    if ($dialog.ShowDialog() -eq "OK") { $boxSaveAs.Text = $dialog.FileName }
})
$form.Controls.Add($browseButton)


# OK Button
$buttonOk = New-Object System.Windows.Forms.Button
$buttonOk.Text = 'Export'
$buttonOk.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$buttonOk.BackColor = [System.Drawing.Color]::SeaGreen
$buttonOk.ForeColor = [System.Drawing.Color]::White
$buttonOk.Location = New-Object System.Drawing.Point($leftX, ($boxSaveAs.Bottom + 30))
$buttonOk.Size = New-Object System.Drawing.Size(150, 40)
$buttonOk.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$buttonOk.FlatAppearance.BorderSize = 0
$buttonOk.Add_Click({
    if ($listCur.CheckedItems.Count -eq 0) {
        [System.Windows.Forms.MessageBox]::Show("Please select at least one currency.", "Selection Required", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning)
    } else {
        $boxAlwaysApprove.Text | Out-File $persistFile -Encoding utf8
        $form.DialogResult = 'OK'
        $form.Close()
    }
})
$form.Controls.Add($buttonOk)

# Execution Logic
if ($form.ShowDialog() -eq 'OK') {
    $selectedDate = [datetime]$comboDate.SelectedItem
    $selectedCurrencies = @($listCur.CheckedItems)
    $thresholdValue = [int]$boxThreshold.Value
    $filePathOutFullFormatted = $boxSaveAs.Text

    $alwaysApproveAccounts = $boxAlwaysApprove.Text -split "[\r\n,]" | 
        Where-Object { -not [string]::IsNullOrWhitespace($_) } | 
        ForEach-Object { $_.Trim() }
    Write-Host "`n--- Export Options Selected ---" -ForegroundColor Cyan
    Write-Host "Threshold:        $thresholdValue"
    Write-Host "Save To:          $filePathOutFullFormatted"
    Write-Host "Filter Date:      $selectedDate"
    Write-Host "Currencies:       $($selectedCurrencies -join ', ')"
    Write-Host "Bypass Accounts:  $($alwaysApproveAccounts -join ', ')"
} else {
    Write-Host "Operation cancelled by user." -ForegroundColor Yellow
    exit
}

# And finally apply the formatting rules

$CurrencyMap = @{
	1					= 'CAD'
	'Canadian Dollar' 	= 'CAD'
	2					= 'USD'
	'American Dollar' 	= 'USD'
	'US Dollar'			= 'USD'
	# 3					= 'EUR'
	# 'Euro'			= 'EUR'
	# 'European Euro'	= 'EUR'
}

function Get-CurrencyCode {
	param($row)
	if ($CurrencyMap.ContainsKey($row.sec_currency)) {
		return $CurrencyMap[$row.sec_currency]
	}
	if ($CurrencyMap.ContainsKey([int]$row.sec_cur_seq)) {
		return $CurrencyMap[[int]$row.sec_cur_seq]
	}
	throw "Fund type '$($row.sec_currency)' not defined in CurrencyMap"
}

function Get-MMValue {
	param([decimal]$balance)
	return [math]::Floor($balance / 1000) * 1000
}

$formatted =
	$cleaned |
	Group-Object -Property account_code, sec_currency |
	ForEach-Object {
		$group = $_.Group

		# Row for the selected date
		$selectedRow = $group | Where-Object {
			([datetime]$_.initial_bal_date -eq $selectedDate) -and
			($selectedCurrencies -contains $_.sec_currency)
		}

		if ($selectedRow) {
			
			$futureNegative =
				$group |
				# Dates after the selected date
				Where-Object { [datetime]$_.initial_bal_date -gt $selectedDate } |
				# Where the balance is less than 0
				Where-Object { [decimal]$_.initial_cash_bal -lt 0 } |
				# Sort by the dates they occur on
				Sort-Object initial_bal_date |
				# And finally select the earliest date
				Select-Object -First 1

			if ($futureNegative) {
				$selectedRow | Add-Member -NotePropertyName FutureNegativeDate -NotePropertyValue $futureNegative.initial_bal_date
				$selectedRow | Add-Member -NotePropertyName FutureNegativeValue -NotePropertyValue $futureNegative.initial_cash_bal
			}
			else {
				$selectedRow | Add-Member -NotePropertyName FutureNegativeDate -NotePropertyValue ''
				$selectedRow | Add-Member -NotePropertyName FutureNegativeValue -NotePropertyValue ''
			}
			$selectedRow
		}
	} |
	Sort-Object -Property account_code |
	Select-Object `
		@{ Name = 'Account Code'; Expression = { $_.account_code }},
		@{ Name = 'Account Number'; Expression = {
			$currency = Get-CurrencyCode $_
			$pName = "${currency}_account"
			$_.$pName
		}},
		@{ Name = 'Account Name'; Expression = { $_.account_name }},
		@{ Name = 'Funds'; Expression = { Get-CurrencyCode $_ }},
		@{ Name = 'MM TO BUY'; Expression = {
			if ([decimal]$_.initial_cash_bal -ge 0) { Get-MMValue $_.initial_cash_bal } else { 'SELL' }
		}},
		@{ Name = 'Approved By'; Expression = {
			if ($alwaysApproveAccounts -contains $_.account_code.Trim()) {
				'APPROVAL REQUIRED'
			}
			elseif ([decimal]$_.initial_cash_bal -ge $thresholdValue) { 
				'APPROVAL REQUIRED' 
			} else { '' }
		}},
		@{ Name = 'Projected Balance'; Expression = { $_.initial_cash_bal }},
		@{ Name = 'Negative On Date'; Expression = {
			if ($_.FutureNegativeDate -ne '') { $_.FutureNegativeDate } else { '' }
		}},
		@{ Name = 'Negative Value'; Expression = {
			if ($_.FutureNegativeValue -ne '') { $_.FutureNegativeValue } else { '' }
		}},
		@{ Name = 'Notes'; Expression = { $_.notes }} |
	Sort-Object * -Unique # Remove all duplicate entries by comparing all properties.
	# Duplicate entries may happen if there are multiple transactions on a single day.
	# Transaction data is not kept at this point, this makes what looks like duplicate rows.


$formatted | Export-Csv -Path $filePathOutFullFormatted -NoTypeInformation
Invoke-Item $filePathOutFullFormatted # Open the file

<#
NOTES:
- The PM column can be filled in by an xlsx function (not within scope)

TODO: 
- Add more options to export:
	- export to .xlsx to allow colour and style formatting
	- Open when finished exporting
	- Dedicated file dialogue for export location instead of just the file name
	- More flags?
- Ensure that the targeted file for cleaning is actually a report.
- Should fixed comments be kept? (Comments are the reason why reports need to be cleaned)
- Do ten million tests to make sure it doesn't break.
- Add this script to the setup pipeline?
#>