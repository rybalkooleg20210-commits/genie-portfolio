# CSV leads cleanup (demo)

Small Python utility that cleans and merges lead CSVs:

- normalizes names, emails, phones
- drops empty rows
- dedupes by email (then phone, then name)
- merges non-empty fields from duplicates
- writes a cleaned CSV + a short Markdown report

> Demo with **fake** sample numbers and emails (`example.com`). Not production CRM data.

## Run

```bash
cd projects/csv-automation
python3 clean_leads.py sample_data/leads_a.csv sample_data/leads_b.csv \
  -o cleaned_leads.csv -r cleanup_report.md
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Stdlib only. Python 3.10+.
