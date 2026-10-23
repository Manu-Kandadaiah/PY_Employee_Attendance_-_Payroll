"""Isolated dataset cleaning and report generation; never modifies payroll tables."""
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

MAX_ROWS = 50000
MAX_COLS = 100


def read_data(path):
    path = Path(path)
    if path.suffix.lower() == '.csv':
        with path.open('r', encoding='utf-8-sig', newline='') as f:
            rows = list(csv.reader(f))
    elif path.suffix.lower() == '.xlsx':
        from python_calamine import CalamineWorkbook
        book = CalamineWorkbook.from_path(str(path))
        if not book.sheets:
            raise ValueError('Workbook has no worksheets')
        rows = book.get_sheet_by_index(0).to_python()
    else:
        raise ValueError('Upload .csv or .xlsx only')
    if len(rows) > MAX_ROWS + 1 or any(len(r) > MAX_COLS for r in rows):
        raise ValueError('Dataset exceeds 50,000 rows or 100 columns')
    if len(rows) < 2:
        raise ValueError('Dataset must contain headers and at least one data row')
    return rows


def clean_data(rows):
    raw_headers = rows[0]
    headers, seen_headers = [], Counter()
    for i, name in enumerate(raw_headers):
        clean = re.sub(r'[^a-z0-9]+', '_', str(name or '').strip().lower()).strip('_') or f'column_{i+1}'
        seen_headers[clean] += 1
        headers.append(clean if seen_headers[clean] == 1 else f'{clean}_{seen_headers[clean]}')
    records, seen, duplicates, empty_rows, padded = [], set(), 0, 0, 0
    for original in rows[1:]:
        vals = ['' if v is None else str(v).strip() for v in original[:len(headers)]]
        if len(vals) < len(headers):
            padded += 1
            vals += [''] * (len(headers) - len(vals))
        if not any(vals):
            empty_rows += 1
            continue
        key = tuple(vals)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        records.append(vals)
    missing = {name: sum(not r[i] for r in records) for i, name in enumerate(headers)}
    stats = {'input_rows': len(rows)-1, 'cleaned_rows': len(records),
             'duplicate_rows_removed': duplicates, 'blank_rows_removed': empty_rows,
             'short_rows_padded': padded, 'missing_values_by_column': missing,
             'cleaning_rules': ['normalize column names', 'trim cell whitespace',
                                'remove fully empty rows', 'remove exact duplicate rows',
                                'preserve missing cells as blank (no invented values)']}
    return headers, records, stats


def write_report(headers, records, stats, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with (output/'cleaned_data.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(records)
    charts = []
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for i, column in enumerate(headers):
        values = [r[i] for r in records if r[i]]
        if not values:
            continue
        numeric = []
        for v in values:
            try:
                numeric.append(float(v.replace(',', '')))
            except ValueError:
                pass
        fig, ax = plt.subplots(figsize=(8, 4.5))
        if len(numeric) >= max(3, int(len(values)*0.85)) and len(set(numeric)) > 1:
            ax.hist(numeric, bins=min(20, max(5, int(len(numeric)**0.5))))
            ax.set_ylabel('Frequency')
        else:
            counts = Counter(values)
            if len(counts) > 25:
                plt.close(fig)
                continue
            top = counts.most_common(10)
            ax.barh([str(k)[:32] for k, _ in reversed(top)], [v for _, v in reversed(top)])
            ax.set_xlabel('Count')
        ax.set_title(column.replace('_', ' ').title())
        fig.tight_layout()
        filename = f'chart_{i+1:02d}.png'
        fig.savefig(output/filename, dpi=125)
        plt.close(fig)
        charts.append(filename)
        if len(charts) >= 8:
            break
    stats['charts'] = charts
    stats['generated_at_utc'] = datetime.now(timezone.utc).isoformat()
    (output/'cleaning_report.json').write_text(json.dumps(stats, indent=2), encoding='utf-8')
    import html
    body = '<h1>Dataset Cleaning & Chart Report</h1>'
    body += '<p>Rows received: {} | Rows retained: {} | Duplicates removed: {} | Blank rows removed: {}</p>'.format(
        stats['input_rows'], stats['cleaned_rows'], stats['duplicate_rows_removed'], stats['blank_rows_removed'])
    body += '<h2>Missing values</h2><table border="1" cellpadding="8"><tr><th>Column</th><th>Missing</th></tr>'
    body += ''.join(f'<tr><td>{html.escape(k)}</td><td>{v}</td></tr>' for k,v in stats['missing_values_by_column'].items()) + '</table>'
    body += '<h2>Charts</h2>' + ''.join(f'<div><img src="{name}" style="max-width:95%;height:auto"></div>' for name in charts)
    (output/'report.html').write_text('<!doctype html><html><head><meta charset="utf-8"><title>Dataset Report</title></head><body style="font-family:Arial;max-width:1000px;margin:auto">'+body+'</body></html>', encoding='utf-8')
    return stats
