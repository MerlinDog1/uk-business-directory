#!/usr/bin/env python3
"""Generate a private customer-status overlay from an exported SUPATED list."""
import argparse
import csv
import difflib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

POSTCODE = re.compile(r'\b(?:GIR\s*0AA|[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b', re.I)
LEGAL_ENDING = re.compile(r'\b(?:limited|ltd|plc|llp)\s*$', re.I)


def name(value):
    value = unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode().lower()
    value = value.replace('&', ' and ')
    value = re.sub(r'[^a-z0-9]+', ' ', value).strip()
    while LEGAL_ENDING.search(value):
        value = LEGAL_ENDING.sub('', value).strip()
    return value


def postcode(value):
    found = POSTCODE.search(str(value or ''))
    return re.sub(r'\s+', '', found.group().upper()) if found else ''


def phone(value):
    digits = re.sub(r'\D', '', str(value or ''))
    if digits.startswith('0044'):
        digits = '0' + digits[4:]
    elif digits.startswith('44'):
        digits = '0' + digits[2:]
    return digits if 10 <= len(digits) <= 11 else ''


def field(row, *keys):
    # Header names from typical Supabase JSON and CSV exports.
    normalized = {str(k).strip().lower().replace(' ', '_'): v for k, v in row.items() if k is not None}
    return next((normalized[k] for k in keys if normalized.get(k)), '')


def values(row):
    return {
        'name': name(field(row, 'company', 'company_name', 'business', 'business_name')),
        'postcode': postcode(field(row, 'postcode', 'postal_code', 'address')),
        'phone': phone(field(row, 'phone_number', 'phone', 'telephone', 'tel')),
    }


def compare(directory, customers):
    """Return minimal overlay and private review details. No unmatched inference."""
    ds, cs = [values(x) for x in directory], [values(x) for x in customers]
    dc, cc = Counter(x['name'] for x in ds), Counter(x['name'] for x in cs)
    # Only equal names or names corroborated by a phone/postcode can match.
    # Index those fields to avoid fuzzy-comparing every pair of businesses.
    indexes = {key: defaultdict(list) for key in ('name', 'postcode', 'phone')}
    for index, customer_values in enumerate(cs):
        if not customer_values['name']:
            continue
        for key, index_map in indexes.items():
            if customer_values[key]:
                index_map[customer_values[key]].append(index)
    matches, review = [], []
    for business, d in zip(directory, ds):
        if not d['name']:
            continue
        candidates = []
        candidate_indexes = set()
        for key, index_map in indexes.items():
            if d[key]:
                candidate_indexes.update(index_map.get(d[key], ()))
        # Preserve source order for evidence and review reports.
        for index in sorted(candidate_indexes):
            customer, c = customers[index], cs[index]
            exact = d['name'] == c['name']
            post_match = bool(d['postcode'] and d['postcode'] == c['postcode'])
            phone_match = bool(d['phone'] and d['phone'] == c['phone'])
            conflict = bool(d['postcode'] and c['postcode'] and not post_match)
            if exact or ((post_match or phone_match) and
                         difflib.SequenceMatcher(None, d['name'], c['name']).ratio() >= 0.86):
                confirmed = (exact and dc[d['name']] == 1 and cc[c['name']] == 1
                             and (post_match or phone_match) and not conflict)
                candidates.append((confirmed, customer, exact, post_match, phone_match, conflict))
        if not candidates:
            continue
        # More than one candidate, even with one exact, should be checked by a person.
        status = 'confirmed' if len(candidates) == 1 and candidates[0][0] else 'possible'
        candidate_names = []
        reasons = []
        for _, customer, exact, post_match, phone_match, conflict in candidates:
            customer_name = str(field(customer, 'company', 'company_name', 'business', 'business_name'))
            candidate_names.append(customer_name)
            evidence = ['exact normalized name' if exact else 'similar name']
            if post_match:
                evidence.append('same postcode')
            if phone_match:
                evidence.append('same phone')
            if conflict:
                evidence.append('postcode differs')
            if not post_match and not phone_match:
                evidence.append('no matching postcode or phone')
            reasons.append(f"{customer_name}: {', '.join(evidence)}")
            review.append({'directory_id': business['id'], 'directory_company': field(business, 'company'),
                           'customer_company': customer_name,
                           'status': status, 'exact_name': exact, 'same_postcode': post_match,
                           'same_phone': phone_match, 'postcode_conflict': conflict})
        matches.append({'id': business['id'], 'status': status,
                        'customer': '; '.join(candidate_names), 'reason': '; '.join(reasons)})
    return {'matches': matches}, review


def load_records(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        if path.suffix.lower() == '.csv':
            rows = list(csv.DictReader(f))
        elif path.suffix.lower() == '.json':
            rows = json.load(f)
            if isinstance(rows, dict):
                rows = rows.get('customers', rows.get('data'))
        else:
            raise ValueError('Input must be a CSV or JSON file')
    if not isinstance(rows, list) or not rows or not all(isinstance(r, dict) for r in rows):
        raise ValueError(f'{path}: expected a non-empty array of records')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('customers', type=Path, help='SUPATED customer export, CSV or JSON')
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parent.parent / 'data/directory-data.json')
    parser.add_argument('--output', type=Path, required=True, help='Private overlay JSON output')
    parser.add_argument('--review', type=Path, help='Optional private report containing customer names')
    args = parser.parse_args()
    try:
        inputs = {args.customers.resolve(), args.directory.resolve()}
        outputs = [args.output.resolve()] + ([args.review.resolve()] if args.review else [])
        if len(set(outputs)) != len(outputs) or any(p in inputs for p in outputs):
            raise ValueError('Outputs must be distinct from each other and the inputs')
        directory = load_records(args.directory)
        customers = load_records(args.customers)
        ids = [row.get('id') for row in directory]
        if any(not isinstance(i, int) or isinstance(i, bool) for i in ids) or len(ids) != len(set(ids)):
            raise ValueError('Directory IDs must be unique integers')
        if not any(values(row)['name'] for row in customers):
            raise ValueError('No customer company names found; check the export headers')
        overlay, review = compare(directory, customers)
        args.output.write_text(json.dumps(overlay, indent=2) + '\n', encoding='utf-8')
        if args.review:
            args.review.write_text(json.dumps(review, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        counts = Counter(row['status'] for row in overlay['matches'])
        print(f"Compared {len(directory)} directory entries with {len(customers)} customer records: "
              f"{counts['confirmed']} confirmed, {counts['possible']} possible. Unmatched entries are unknown.")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f'Comparison failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
