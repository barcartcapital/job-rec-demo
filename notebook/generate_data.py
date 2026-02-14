"""
Data pipeline script: Downloads XML feed, computes recommendations, exports JSON.
This mirrors the notebook logic but runs as a standalone script.
"""
import os
import re
import json
import sys
import requests
import numpy as np
import pandas as pd
from lxml import etree
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter

FEED_URL = 'https://www.workable.com/boards/workable.xml'
XML_PATH = 'data/workable_feed.xml'
OUTPUT_DIR = 'output'
SAMPLE_SIZE = 1000
TOP_N = 3

os.makedirs('data', exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def download_feed():
    if os.path.exists(XML_PATH):
        size_mb = os.path.getsize(XML_PATH) / (1024 * 1024)
        print(f'XML feed already cached ({size_mb:.1f} MB). Skipping download.')
        return True

    print(f'Downloading XML feed from {FEED_URL}...')
    try:
        response = requests.get(FEED_URL, stream=True, timeout=600)
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))
        downloaded = 0
        with open(XML_PATH, 'wb') as f:
            for chunk in response.iter_content(chunk_size=65536):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded / total * 100
                    print(f'\rDownloaded {downloaded / 1024 / 1024:.1f} MB ({pct:.0f}%)', end='', flush=True)
                else:
                    print(f'\rDownloaded {downloaded / 1024 / 1024:.1f} MB', end='', flush=True)
        print(f'\nDone! Saved to {XML_PATH}')
        return True
    except Exception as e:
        print(f'\nDownload failed: {e}')
        return False


def parse_feed(max_jobs=None):
    print('Parsing XML feed...')
    jobs = []
    context = etree.iterparse(XML_PATH, events=('end',), tag='job', recover=True)

    for event, elem in context:
        job = {
            'id': (elem.findtext('referencenumber') or '').strip(),
            'title': (elem.findtext('title') or '').strip(),
            'company': (elem.findtext('company') or '').strip(),
            'city': (elem.findtext('city') or '').strip(),
            'state': (elem.findtext('state') or '').strip(),
            'country': (elem.findtext('country') or '').strip(),
            'remote': (elem.findtext('remote') or '').strip().lower() == 'true',
            'description': (elem.findtext('description') or '').strip(),
            'education': (elem.findtext('education') or '').strip(),
            'job_type': (elem.findtext('jobtype') or '').strip(),
            'category': (elem.findtext('category') or '').strip(),
            'experience': (elem.findtext('experience') or '').strip(),
            'url': (elem.findtext('url') or '').strip(),
            'date': (elem.findtext('date') or '').strip(),
        }

        if job['id'] and job['title'] and job['description']:
            jobs.append(job)

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

        if max_jobs and len(jobs) >= max_jobs:
            break

        if len(jobs) % 10000 == 0 and len(jobs) > 0:
            print(f'  Parsed {len(jobs):,} jobs...', flush=True)

    print(f'Parsed {len(jobs):,} valid jobs.')
    return jobs


def clean_html(raw_html):
    if not raw_html or not isinstance(raw_html, str):
        return ''
    soup = BeautifulSoup(raw_html, 'html.parser')
    for tag in soup.find_all(['script', 'style']):
        tag.decompose()
    text = soup.get_text(separator=' ', strip=True)
    text = re.sub(r'http\S+|www\.\S+', '', text)
    text = re.sub(r'\S+@\S+\.\S+', '', text)
    text = re.sub(r'&\w+;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def preprocess_text(text):
    if not text:
        return ''
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def stratified_sample(df, n=1000, min_per_group=5):
    df_dedup = df.drop_duplicates(subset=['title', 'company', 'city'])
    print(f'After dedup: {len(df_dedup):,} (removed {len(df) - len(df_dedup):,} duplicates)')

    df_dedup = df_dedup.copy()
    df_dedup['category'] = df_dedup['category'].replace('', 'Other')

    cat_counts = df_dedup['category'].value_counts()
    cat_proportions = cat_counts / cat_counts.sum()
    cat_samples = (cat_proportions * n).apply(lambda x: max(int(x), min_per_group))

    while cat_samples.sum() > n:
        largest = cat_samples.idxmax()
        cat_samples[largest] -= 1
    while cat_samples.sum() < n:
        largest = cat_samples.idxmax()
        cat_samples[largest] += 1

    sampled = []
    for cat, count in cat_samples.items():
        cat_df = df_dedup[df_dedup['category'] == cat]
        sample_n = min(count, len(cat_df))
        sampled.append(cat_df.sample(n=sample_n, random_state=42))

    result = pd.concat(sampled).reset_index(drop=True)
    print(f'Sampled {len(result)} jobs across {result["category"].nunique()} categories')
    return result


def get_top_n_recs(sim_matrix, df, n=3):
    recs = {}
    for i in range(len(df)):
        scores = sim_matrix[i].copy()
        scores[i] = -1
        top_n = np.argsort(scores)[::-1][:n]
        recs[df.iloc[i]['id']] = [
            {'id': df.iloc[top_n[j]]['id'], 'score': round(float(scores[top_n[j]]), 4)}
            for j in range(n)
        ]
    return recs


def main():
    # Step 1: Download
    if not download_feed():
        print('Cannot proceed without XML feed.')
        sys.exit(1)

    # Step 2: Parse
    all_jobs = parse_feed()

    # Step 3: Load and sample
    df_all = pd.DataFrame(all_jobs)
    print(f'\nDataFrame: {df_all.shape[0]:,} jobs, {df_all.shape[1]} columns')
    print(f'Categories: {df_all["category"].nunique()}')

    df = stratified_sample(df_all, n=SAMPLE_SIZE)

    # Step 4: Clean and preprocess
    print('\nCleaning HTML descriptions...')
    df['description_clean'] = df['description'].apply(clean_html)
    df['title_clean'] = df['title'].apply(preprocess_text)
    df['desc_processed'] = df['description_clean'].apply(preprocess_text)

    # Fill missing
    df['category'] = df['category'].replace('', 'Other')
    df['experience'] = df['experience'].replace('', 'Not Specified')
    df['education'] = df['education'].replace('', 'Not Specified')
    df['job_type'] = df['job_type'].replace('', 'Not Specified')
    df['city'] = df['city'].replace('', 'Unknown')
    df['state'] = df['state'].replace('', 'Unknown')
    df['country'] = df['country'].replace('', 'Unknown')

    print(f'Description lengths: min={df["description_clean"].str.len().min()}, '
          f'median={df["description_clean"].str.len().median():.0f}, '
          f'max={df["description_clean"].str.len().max()}')

    # Step 5: Baseline model (title TF-IDF)
    print('\n--- Baseline Model (Title-Only Cosine Similarity) ---')
    title_vectorizer = TfidfVectorizer(
        ngram_range=(1, 2), max_features=5000,
        stop_words='english', sublinear_tf=True,
    )
    title_tfidf = title_vectorizer.fit_transform(df['title_clean'])
    print(f'Title TF-IDF shape: {title_tfidf.shape}')

    title_sim_matrix = cosine_similarity(title_tfidf)
    baseline_recs = get_top_n_recs(title_sim_matrix, df, n=TOP_N)
    print(f'Baseline recs generated for {len(baseline_recs)} jobs.')

    # Spot check
    for i in [0, 100, 500]:
        if i < len(df):
            job = df.iloc[i]
            print(f'\n  Source: {job["title"]} ({job["company"]})')
            for rec in baseline_recs[job['id']]:
                r = df[df['id'] == rec['id']].iloc[0]
                print(f'    -> {r["title"]} ({r["company"]}) score={rec["score"]:.4f}')

    # Step 6: Weighted model
    print('\n--- Enhanced Model (Weighted Multi-Feature) ---')
    desc_vectorizer = TfidfVectorizer(
        ngram_range=(1, 2), max_features=10000,
        max_df=0.85, min_df=2,
        stop_words='english', sublinear_tf=True,
        dtype=np.float32,
    )
    desc_tfidf = desc_vectorizer.fit_transform(df['desc_processed'])
    print(f'Description TF-IDF shape: {desc_tfidf.shape}')

    desc_sim = cosine_similarity(desc_tfidf)

    categories = df['category'].values
    cat_sim = (categories[:, None] == categories[None, :]).astype(np.float32)

    cities = df['city'].values
    states = df['state'].values
    countries = df['country'].values
    loc_sim = np.where(
        cities[:, None] == cities[None, :], 1.0,
        np.where(states[:, None] == states[None, :], 0.5,
                 np.where(countries[:, None] == countries[None, :], 0.2, 0.0))
    ).astype(np.float32)

    jobtypes = df['job_type'].values
    type_sim = (jobtypes[:, None] == jobtypes[None, :]).astype(np.float32)

    exp_map = {
        'Entry level': 0, 'Internship': 0, 'Associate': 1,
        'Mid-Senior level': 2, 'Not Specified': 2,
        'Director': 3, 'Executive': 4,
    }
    exp_vals = np.array([exp_map.get(e, 2) for e in df['experience'].values], dtype=np.float32)
    exp_dist = np.abs(exp_vals[:, None] - exp_vals[None, :])
    max_dist = exp_dist.max()
    exp_sim = (1.0 - exp_dist / max_dist).astype(np.float32) if max_dist > 0 else np.ones_like(exp_dist)

    WEIGHTS = {
        'description': 0.35, 'title': 0.25, 'category': 0.15,
        'location': 0.10, 'job_type': 0.08, 'experience': 0.07,
    }

    weighted_sim = (
        WEIGHTS['description'] * desc_sim +
        WEIGHTS['title'] * title_sim_matrix.astype(np.float32) +
        WEIGHTS['category'] * cat_sim +
        WEIGHTS['location'] * loc_sim +
        WEIGHTS['job_type'] * type_sim +
        WEIGHTS['experience'] * exp_sim
    )

    weighted_recs = get_top_n_recs(weighted_sim, df, n=TOP_N)
    print(f'Weighted recs generated for {len(weighted_recs)} jobs.')

    # Spot check comparison
    for i in [0, 100, 500]:
        if i < len(df):
            job = df.iloc[i]
            print(f'\n  Source: {job["title"]} ({job["company"]})')
            print(f'    Baseline:')
            for rec in baseline_recs[job['id']]:
                r = df[df['id'] == rec['id']].iloc[0]
                print(f'      -> {r["title"]} score={rec["score"]:.4f}')
            print(f'    Weighted:')
            for rec in weighted_recs[job['id']]:
                r = df[df['id'] == rec['id']].iloc[0]
                print(f'      -> {r["title"]} score={rec["score"]:.4f}')

    # Overlap analysis
    overlaps = []
    for job_id in baseline_recs:
        base_ids = {r['id'] for r in baseline_recs[job_id]}
        wtd_ids = {r['id'] for r in weighted_recs[job_id]}
        overlaps.append(len(base_ids & wtd_ids))
    overlap_counts = Counter(overlaps)
    print(f'\nOverlap: avg {np.mean(overlaps):.1f} shared recs per job')
    for k, v in sorted(overlap_counts.items()):
        print(f'  {k}/{TOP_N}: {v} jobs ({v/len(df)*100:.1f}%)')

    # Step 7: Export
    print('\n--- Exporting JSON ---')
    jobs_export = []
    for _, row in df.iterrows():
        jobs_export.append({
            'id': row['id'],
            'title': row['title'],
            'company': row['company'],
            'city': row['city'],
            'state': row['state'],
            'country': row['country'],
            'remote': bool(row['remote']),
            'description': row['description'],
            'category': row['category'],
            'jobType': row['job_type'],
            'experience': row['experience'],
            'education': row['education'],
            'url': row['url'],
        })

    jobs_path = os.path.join(OUTPUT_DIR, 'jobs.json')
    baseline_path = os.path.join(OUTPUT_DIR, 'recs_baseline.json')
    weighted_path = os.path.join(OUTPUT_DIR, 'recs_weighted.json')

    with open(jobs_path, 'w') as f:
        json.dump(jobs_export, f, separators=(',', ':'))
    with open(baseline_path, 'w') as f:
        json.dump(baseline_recs, f, separators=(',', ':'))
    with open(weighted_path, 'w') as f:
        json.dump(weighted_recs, f, separators=(',', ':'))

    for path in [jobs_path, baseline_path, weighted_path]:
        size_kb = os.path.getsize(path) / 1024
        label = f'{size_kb/1024:.1f} MB' if size_kb > 1024 else f'{size_kb:.0f} KB'
        print(f'  {path}: {label}')

    # Sanity check
    job_ids = {j['id'] for j in jobs_export}
    for recs in [baseline_recs, weighted_recs]:
        for job_id, rec_list in recs.items():
            assert job_id in job_ids
            assert len(rec_list) == TOP_N
            for r in rec_list:
                assert r['id'] in job_ids

    print('\nAll checks passed. Ready for web app!')


if __name__ == '__main__':
    main()
