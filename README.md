# SQLite Workbench

SQLite Workbench is a lightweight desktop application for exploring and working with SQLite databases. It provides a clean graphical interface for opening database files, browsing tables, inspecting schemas, running SQL queries, editing records, importing CSV data, and exporting results. The current codebase is implemented in Python 3 with `customtkinter` for the UI and `pygments` for SQL syntax highlighting. :contentReference[oaicite:0]{index=0}

## Features

- Open and explore SQLite database files
- Browse tables and inspect table schemas
- Search and paginate table data
- Run custom SQL queries with syntax highlighting
- Keep query history and save favorite queries
- Insert, edit, and delete records
- Create, rename, and delete tables
- Import CSV files into new tables
- Export visible data to CSV or JSON
- Run `VACUUM` to compact the database
- Dark, light, and system theme modes
- English and Portuguese localization 

## Technology Stack

- Python 3
- customtkinter
- pygments
- sqlite3

## Project Structure

```text
app.py
database.py
localization.py
````

* `app.py` — main desktop UI and application flow
* `database.py` — SQLite access and database operations
* `localization.py` — UI translations and localized strings

## Requirements

Install the required packages:

```bash
pip install customtkinter pygments
```

## Run the Application

```bash
python app.py
```

Depending on how you organize the package, you may also run it as a module.

## Packaging

This project can be packaged for desktop distribution with tools such as PyInstaller. Since desktop binaries are platform-specific, builds should normally be generated separately for Windows, Linux, and macOS.

Example:

```bash
pyinstaller --onefile --windowed app.py
```

## Notes

* Settings are stored in `settings.json`
* Favorite SQL queries are stored in `favorites.json`
* The application currently supports Portuguese and English
* The UI title in the current source still contains the previous internal app name and can be updated to `SQLite Workbench` before release

## Intended Audience

SQLite Workbench is designed for developers, analysts, inspectors, and advanced users who need a practical desktop tool for inspecting and working with SQLite databases without unnecessary complexity.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Author

Carlos Canuto Costa
