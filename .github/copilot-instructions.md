# GitHub Copilot Instructions for SSADAN

## Project Overview
SSADAN (SSAFY 식단 알림 봇) is an automated meal schedule notification bot that:
- Uses Google Cloud Document AI to extract meal schedules from images via OCR
- Converts extracted data to Markdown format
- Sends notifications to Mattermost via webhooks
- Runs on GitHub Actions for daily and weekly automation

## Project Structure
```
.
├── .github/workflows/      # GitHub Actions automation
│   ├── daily_notify.yml    # Daily lunch notifications (9:10 AM KST)
│   └── weekly_notify.yml   # Weekly menu processing
├── db/                     # Extracted meal schedules (YYYY-MM-DD.md)
├── src/                    # Core Python modules
│   ├── main.py             # CLI entry point and orchestration
│   ├── ocr_processor.py    # OCR processing and Markdown conversion
│   └── mm_sender.py        # Mattermost webhook sender
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # Documentation (in Korean)
```

## Language and Localization
- **Primary Language**: Korean (한국어)
- **User-facing messages**: Use Korean (e.g., "✓ OCR 처리 완료")
- **Code comments**: Use Korean for docstrings and inline comments
- **Variable names**: Use English
- **CLI output**: Korean with emoji for better UX
- **Error messages**: Korean with helpful context

## Coding Conventions

### Python Style
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Use docstrings in Korean for all functions and classes
- Prefer explicit error handling with try-except blocks
- Use meaningful variable names in English

### Error Handling
- Always catch specific exceptions (ValueError, FileNotFoundError, etc.)
- Provide informative Korean error messages with context
- Print stack traces for unexpected errors (using `traceback.print_exc()`)
- Return boolean success indicators from main functions

### File Operations
- Always use UTF-8 encoding for file I/O
- Use `os.path.join()` for cross-platform path handling
- Check file existence before reading
- Handle encoding errors gracefully

### Date and Time
- Use Korea Standard Time (KST, UTC+9) via `timezone(timedelta(hours=9))`
- Format dates as YYYY-MM-DD for file names
- Format dates as MM월 DD일 for display (e.g., "01월 15일")
- Use Korean weekday names: ['월', '화', '수', '목', '금', '토', '일']

### CLI Design
- Use argparse with subcommands (process, ocr, notify, daily)
- Provide helpful examples in epilog text
- Support both required and optional arguments
- Use `--dry-run` flags for testing without side effects

### Output Formatting
- Use emoji for visual clarity (🔄, ✓, ✗, 🍽️, 📤, etc.)
- Use separator lines (60 "=" characters) for section headers
- Provide step-by-step progress indicators (1️⃣, 2️⃣, 3️⃣)
- Print helpful tips with 💡 emoji

## Key Dependencies

### Google Cloud Document AI
- Used for OCR processing of meal schedule images
- Requires: service account credentials, processor ID, project ID
- Configuration via environment variables
- Handles table extraction from images

### Mattermost
- Webhook-based integration for notifications
- Supports Markdown formatting in messages
- Webhook URL stored in environment variables

### Environment Variables
Required variables (stored in `.env` locally, GitHub Secrets in CI):
- `MATTERMOST_WEBHOOK_URL`: Mattermost webhook endpoint
- `GOOGLE_CLOUD_CREDENTIALS`: JSON service account key (full content)
- `GOOGLE_CLOUD_PROJECT_ID`: Google Cloud project ID
- `GOOGLE_CLOUD_PROCESSOR_ID`: Document AI processor ID
- `GOOGLE_CLOUD_LOCATION`: Processor location (us, eu, asia)

## Development Workflow

### Local Testing
1. Copy `.env.example` to `.env` and configure
2. Install dependencies: `pip install -r requirements.txt`
3. Test OCR only: `python main.py ocr --image <path> --db ../db`
4. Review and edit generated Markdown files in `db/`
5. Test notification: `python main.py notify --date YYYY-MM-DD --db ../db`
6. Test daily notification: `python main.py daily --dry-run --db ../db`

### GitHub Actions
- Daily notifications run at 9:10 AM KST (scheduled via cron)
- Weekly processing is manually triggered via workflow_dispatch
- OCR and notification steps are separated for human review
- Secrets validation happens before execution

### Testing Strategy
- Use `--dry-run` flag to test without sending webhooks
- Validate file parsing logic before sending notifications
- Check weekend detection logic (no notifications on Sat/Sun)
- Test with sample meal schedule images

## Architecture Patterns

### Two-Step Process
1. **OCR Step**: Extract data from image → save to Markdown file
2. **Notification Step**: Load Markdown file → send to Mattermost
3. **Rationale**: Allows human review and correction of OCR results

### Module Separation
- `ocr_processor.py`: Handles Google Cloud API and Markdown conversion
- `mm_sender.py`: Handles Mattermost webhook communication
- `main.py`: Orchestrates workflow and provides CLI interface

### Error Recovery
- OCR failures don't block manual file creation
- File-based storage allows retry without reprocessing
- Each step can be run independently

## Markdown Format
Generated meal schedules use this structure:
```markdown
## 🍴 SSAFY 주간메뉴표 (MM/DD ~ MM/DD)

| 구분 | MM월 DD일 (월) | MM월 DD일 (화) | ... |
| :--- | :--- | :--- | :--- |
| **20F 일반식 (A. 한식)** | 메뉴1<br>메뉴2 | ... | ... |
| **20F 일반식 (B. 일품)** | 메뉴1<br>메뉴2 | ... | ... |
| **도시락** | 메뉴1<br>메뉴2 | ... | ... |
```

## Common Tasks

### Adding New Commands
1. Add subparser in `main.py`
2. Create handler function following naming convention (`verb_noun`)
3. Add examples to parser epilog
4. Use consistent error handling pattern
5. Print progress with emoji and Korean messages

### Modifying OCR Logic
- Edit `_parse_ocr_text()` in `ocr_processor.py`
- Adjust table parsing logic to match actual meal schedule format
- Test with sample images before deployment

### Changing Notification Format
- Modify message formatting in `mm_sender.py`
- Test with `--dry-run` before sending to Mattermost
- Ensure Markdown rendering works correctly

## Security Considerations
- Never commit `.env` file (listed in `.gitignore`)
- Never print sensitive credentials in logs
- Use GitHub Secrets for CI/CD credentials
- Validate environment variables before use

## When Making Changes
1. Maintain backward compatibility with existing Markdown files
2. Test both local and CI/CD workflows
3. Update README.md if adding new features
4. Keep Korean language consistency in user messages
5. Preserve existing file encoding (UTF-8)
6. Don't modify working GitHub Actions unless necessary
