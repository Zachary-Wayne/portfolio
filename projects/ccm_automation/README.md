# Back-Office Automation Suite

During my co-op work term I automated the repetitive parts of an investment firm's daily operations. Each tool is an independent, double-click PowerShell script with a native Windows Forms GUI, so the people using them never touch a terminal. Every tool works on its own; TooKind can also launch the others and pass them its folders, which is how they're linked together.

<!-- TODO(Zach): add time saved or adoption, e.g. "Used daily by N people; replaced ~X minutes of manual work per report." -->

## The tools

| Tool | What it does |
|---|---|
| **MMParser** | Repairs broken CSV exports from the portfolio management system and builds the daily money-market allocation sheet. |
| **StatementSplitter** | Splits one large statement PDF into per-client PDFs, named from the text on each page. |
| **TooKind** (~1,300 lines) | A GUI hub for the firm's SFTP workflows: stored credentials, uploads and downloads, and launching the other scripts. |
| **Bloomberg Emailer** | Collects report data and emails it with attachments, logging each run and returning a distinct exit code for each failure mode. |
| **IconViewer** | A small utility for browsing built-in Windows icons, used to design the other GUIs. |

## Highlights

**Repairing malformed CSVs (MMParser).** Free-text notes in the source system contain commas and newlines, and the export doesn't escape them. Rows get split and their columns shifted. The cleaner detects broken rows by their missing fields, looks ahead up to 15 rows to collect the overflowing note text, and shifts the remaining values back into the right columns. It also handles a second corruption pattern where a bank name lands in the currency column. Cleaning results are cached, so re-exporting with different options is instant.

**Business rules as options.** The allocation export groups positions by account and currency, rounds purchases down to the nearest $1,000, and flags any account over an approval threshold or on a persistent "always approve" list. It also looks ahead for upcoming negative balances so they're caught before trading.

**PDF splitting by content (StatementSplitter).** Using iTextSharp, it finds the pages where each client's letter starts (a page beginning with a date), names each file from the recipient line, and resolves name collisions using the letter's "Re:" line.

**Credentials.** Scripts prompt once and store credentials with Windows DPAPI (`Export-Clixml`), so they're encrypted to the user's account.

*Source excerpts are shown with permission and redacted: system names, server addresses, and account identifiers have been removed.*

*The demo video and screenshots use made-up data on a simulated server. Every client name, address, account number, balance, file and server path in them is fictitious, and any resemblance to real people, companies or accounts is coincidental. No real firm's or client's data appears anywhere in this project.*
