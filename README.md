# Bennett University LMS Downloader

A fast, reliable Python tool to download all course materials from Bennett University LMS. Uses direct authentication (no browser needed).

## Features

- ✅ **Direct Authentication** - Fast login without browser automation
- ✅ **Multi-Course** - Auto-downloads from all your courses
- ✅ **Smart Files** - Proper extensions, no re-downloading duplicates
- ✅ **Progress Bars** - Visual download progress for each file
- ✅ **Organized** - Files sorted by course and type (PDF, Docs, Videos, etc.)
- ✅ **Reliable** - Error recovery, continues on failures
- ✅ **Cross-platform** - Windows, Mac, Linux
- ✓ **Duplicate Handling** - Automatically renames files if duplicates exist
- ✓ **Large File Support** - Skips files > 500MB by default
- ✓ **Detailed Progress** - Shows download status and summary
- ✓ **Cross-platform** - Works on Windows, Mac, and Linux

## Installation

Install Python 3.7+ then run:
```bash
pip install -r requirements.txt
```

Or just double-click the batch file - it handles everything!


## Usage

### Method 1: Interactive Mode (Recommended)
```bash
python lms_downloader.py
```
The script will prompt you for:
- Course URL
- Username (optional)
- Password (optional - won't be echoed on screen)

### Method 2: Command-Line Arguments
```bash
python lms_downloader.py "https://lms.bennett.edu.in/course/view.php?id=13571" -u your_username -p your_password
```

### Method 3: With Custom Output Directory
```bash
python lms_downloader.py "https://lms.bennett.edu.in/course/view.php?id=13571" -u your_username -p your_password -o "my_downloads"
```

### Method 4: URL Only (Manual Login)
```bash
python lms_downloader.py "https://lms.bennett.edu.in/course/view.php?id=13571"
```
This will open a browser - log in manually if credentials aren't provided.

## Download Structure

Files are organized by course and type:

```
lms_downloads/
├── Course Name 1/
│   ├── PDFs/
│   │   ├── lecture.pdf
│   │   └── notes.pdf
│   ├── Documents/
│   │   └── syllabus.docx
│   ├── Spreadsheets/
│   │   └── data.xlsx
│   └── Other/
└── Course Name 2/
    ├── PDFs/
    ├── Videos/
    └── ...
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid Login" | Check username/password; try login manually first |
| "No courses found" | Verify you're enrolled; visit LMS dashboard |
| "No resources found" | Course may have no files; try another course |
| "Connection timeout" | Check internet; server may be down; try again |
| Files not downloading | Verify file permissions; check disk space |

**For more help:** Run `python lms_downloader_direct.py -h`

## Technical Details

- Uses `requests` library to fetch pages with browser cookies
- Parses HTML with `BeautifulSoup`
- Extracts links using multiple LMS-specific patterns
- Implements file type detection and organization

## Performance

- Downloads include 0.5-second delays between requests (respectful to server)
- Large files (>500MB) are skipped by default
- Failed downloads are logged and summarized

## Notes

- Always ensure you have the right to download course materials
- Respect copyright and intellectual property rights
- Check your institution's policies regarding course material distribution

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify your LMS login is still active
3. Try clearing browser cache if session issues persist
