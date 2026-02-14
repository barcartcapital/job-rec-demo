"""
Generate realistic sample job data for the web app demo.
Uses the Workable XML feed schema we already inspected.
When the feed is available, the notebook will use real data.
This generates realistic sample data for local web app development.
"""
import json
import os
import random
import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter

OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

SAMPLE_SIZE = 1000
TOP_N = 3

# Realistic job data pools
CATEGORIES = [
    ("Information Technology", 250),
    ("Sales", 100),
    ("Marketing", 80),
    ("Customer Service", 70),
    ("Healthcare", 60),
    ("Finance & Accounting", 55),
    ("Engineering", 50),
    ("Human Resources", 45),
    ("Operations", 40),
    ("Design", 35),
    ("Education", 30),
    ("Manufacturing", 25),
    ("Legal", 20),
    ("Construction", 15),
    ("Hospitality & Tourism", 15),
    ("Retail", 10),
    ("Other", 100),
]

TITLES_BY_CATEGORY = {
    "Information Technology": [
        "Software Engineer", "Senior Software Engineer", "Full Stack Developer",
        "Frontend Developer", "Backend Developer", "DevOps Engineer",
        "Data Engineer", "Data Scientist", "Machine Learning Engineer",
        "Cloud Architect", "System Administrator", "Network Engineer",
        "Security Analyst", "QA Engineer", "Technical Lead",
        "iOS Developer", "Android Developer", "React Developer",
        "Python Developer", "Java Developer", "Site Reliability Engineer",
        "Database Administrator", "Solutions Architect", "Product Manager (Tech)",
        "Scrum Master", "IT Support Specialist", "Systems Engineer",
        "Platform Engineer", "Infrastructure Engineer", "API Developer",
    ],
    "Sales": [
        "Sales Representative", "Account Executive", "Sales Manager",
        "Business Development Representative", "Sales Director",
        "Account Manager", "Regional Sales Manager", "Sales Engineer",
        "Inside Sales Representative", "Enterprise Account Executive",
        "Sales Operations Analyst", "Channel Partner Manager",
    ],
    "Marketing": [
        "Marketing Manager", "Digital Marketing Specialist", "Content Marketing Manager",
        "SEO Specialist", "Social Media Manager", "Brand Manager",
        "Marketing Analyst", "Growth Marketing Manager", "Email Marketing Specialist",
        "Product Marketing Manager", "Marketing Coordinator", "PPC Specialist",
    ],
    "Customer Service": [
        "Customer Service Representative", "Customer Success Manager",
        "Support Engineer", "Help Desk Technician", "Client Relations Manager",
        "Customer Experience Manager", "Technical Support Specialist",
        "Call Center Agent", "Customer Support Lead", "Account Support Specialist",
    ],
    "Healthcare": [
        "Registered Nurse", "Medical Assistant", "Physical Therapist",
        "Occupational Therapist", "Healthcare Administrator", "Clinical Research Associate",
        "Pharmacy Technician", "Medical Billing Specialist", "Health Information Technician",
        "Nurse Practitioner", "Physician Assistant", "Lab Technician",
    ],
    "Finance & Accounting": [
        "Financial Analyst", "Accountant", "Senior Accountant",
        "Controller", "Bookkeeper", "Tax Specialist",
        "Auditor", "Financial Planner", "Payroll Specialist",
        "Treasury Analyst", "Credit Analyst", "Compliance Officer",
    ],
    "Engineering": [
        "Mechanical Engineer", "Electrical Engineer", "Civil Engineer",
        "Chemical Engineer", "Industrial Engineer", "Structural Engineer",
        "Environmental Engineer", "Aerospace Engineer", "Biomedical Engineer",
        "Manufacturing Engineer", "Quality Engineer", "Process Engineer",
    ],
    "Human Resources": [
        "HR Manager", "HR Coordinator", "Recruiter",
        "Talent Acquisition Specialist", "HR Business Partner",
        "Compensation & Benefits Analyst", "Training Manager",
        "People Operations Manager", "HR Generalist", "Employee Relations Specialist",
    ],
    "Operations": [
        "Operations Manager", "Project Manager", "Supply Chain Manager",
        "Logistics Coordinator", "Warehouse Manager", "Procurement Specialist",
        "Business Analyst", "Operations Analyst", "Facilities Manager",
        "Program Manager",
    ],
    "Design": [
        "UX Designer", "UI Designer", "Product Designer",
        "Graphic Designer", "Visual Designer", "UX Researcher",
        "Interaction Designer", "Creative Director", "Web Designer",
        "Design Lead",
    ],
    "Education": [
        "Teacher", "Instructor", "Training Specialist",
        "Curriculum Developer", "Education Coordinator", "Tutor",
        "Academic Advisor", "Instructional Designer", "Professor",
    ],
    "Manufacturing": [
        "Production Manager", "Machine Operator", "Quality Control Inspector",
        "Assembly Technician", "Maintenance Technician", "Production Planner",
        "Plant Manager", "CNC Machinist",
    ],
    "Legal": [
        "Paralegal", "Legal Assistant", "Contract Specialist",
        "Compliance Analyst", "Legal Counsel", "Corporate Attorney",
        "Litigation Support Specialist",
    ],
    "Construction": [
        "Project Manager (Construction)", "Site Supervisor", "Estimator",
        "Construction Manager", "Safety Manager", "Superintendent",
    ],
    "Hospitality & Tourism": [
        "Hotel Manager", "Restaurant Manager", "Event Coordinator",
        "Chef", "Front Desk Agent", "Concierge",
    ],
    "Retail": [
        "Store Manager", "Retail Sales Associate", "Visual Merchandiser",
        "Inventory Specialist", "Retail Manager",
    ],
    "Other": [
        "Administrative Assistant", "Executive Assistant", "Office Manager",
        "Data Entry Clerk", "Receptionist", "Research Assistant",
        "Consultant", "Freelance Writer", "Translator", "Virtual Assistant",
        "Content Writer", "Copywriter", "Editor", "Photographer",
    ],
}

COMPANIES = [
    "TechCorp", "InnovateSoft", "DataDriven Inc.", "CloudFirst Solutions",
    "PixelPerfect Design", "GreenEnergy Co.", "HealthPlus Medical",
    "FinanceForward", "MarketBoost Agency", "BuildRight Construction",
    "EduLearn Academy", "RetailMax", "LogiTrans Shipping", "SafeGuard Security",
    "FoodieDelights", "TravelWise Tours", "LegalEagle LLP", "ManufactPro",
    "HRConnect", "SalesForce Pro", "AnalyticsMind", "CyberShield Inc.",
    "NetworX Solutions", "AppWorks Studio", "DesignHub Creative",
    "ConsultPro", "BioTech Labs", "RoboTech Industries", "SmartHome Systems",
    "AgriTech Solutions", "MediaPulse", "SportsFit Inc.", "PharmaCore",
    "AutoDrive Motors", "SpaceVentures", "EcoSolutions", "UrbanDev Group",
    "Quantum Computing Inc.", "BlockChain Dynamics", "NeuralNet AI",
    "Acme Corporation", "Globex Industries", "Initech", "Hooli",
    "Pied Piper", "Umbrella Corp", "Stark Industries", "Wayne Enterprises",
]

CITIES = [
    ("New York", "NY", "US"), ("San Francisco", "CA", "US"),
    ("Austin", "TX", "US"), ("Seattle", "WA", "US"),
    ("Chicago", "IL", "US"), ("Boston", "MA", "US"),
    ("Denver", "CO", "US"), ("Atlanta", "GA", "US"),
    ("Los Angeles", "CA", "US"), ("Miami", "FL", "US"),
    ("Portland", "OR", "US"), ("Nashville", "TN", "US"),
    ("Dallas", "TX", "US"), ("Phoenix", "AZ", "US"),
    ("Minneapolis", "MN", "US"), ("Raleigh", "NC", "US"),
    ("San Diego", "CA", "US"), ("Philadelphia", "PA", "US"),
    ("Detroit", "MI", "US"), ("Salt Lake City", "UT", "US"),
    ("London", "", "GB"), ("Berlin", "", "DE"),
    ("Toronto", "ON", "CA"), ("Vancouver", "BC", "CA"),
    ("Sydney", "NSW", "AU"), ("Singapore", "", "SG"),
    ("Amsterdam", "", "NL"), ("Paris", "", "FR"),
    ("Dublin", "", "IE"), ("Bangalore", "Karnataka", "IN"),
]

EXPERIENCE_LEVELS = ["Entry level", "Associate", "Mid-Senior level", "Director", "Executive"]
JOB_TYPES = ["Full-time", "Part-time", "Contract", "Temporary", "Internship"]
EDUCATION_LEVELS = ["High School or equivalent", "Associate's Degree", "Bachelor's Degree", "Master's Degree", "Doctorate"]

# Description templates per category
DESC_TEMPLATES = {
    "Information Technology": [
        "We are looking for a talented {title} to join our engineering team. You will work on building and maintaining {tech_area}. The ideal candidate has experience with {skills} and a passion for {passion}.",
        "Join our team as a {title}! In this role, you will be responsible for {responsibility}. We're looking for someone with {years}+ years of experience in {skills}. You'll work closely with {team} to deliver {deliverable}.",
        "As a {title} at {company}, you will {action} our {product}. We need someone who understands {domain} and can {capability}. This is a great opportunity to work with {tech_stack} in a {environment} environment.",
    ],
    "Sales": [
        "We're seeking an experienced {title} to drive revenue growth. You will manage {territory} and build relationships with {client_type}. The ideal candidate has {years}+ years of B2B sales experience and a proven track record of {achievement}.",
        "Join our sales team as a {title}. You'll be responsible for {responsibility} and achieving quarterly targets. Experience with {tools} and {industry} is preferred.",
    ],
    "default": [
        "We are hiring a {title} to join our growing team at {company}. In this role, you will {responsibility}. The ideal candidate has {years}+ years of experience and strong {skills}. We offer competitive compensation and benefits.",
        "{company} is looking for a motivated {title}. You will {action} and collaborate with cross-functional teams. Requirements include {requirements}. This is a {type} position based in {location}.",
    ],
}

TECH_AREAS = ["scalable web applications", "cloud infrastructure", "data pipelines", "mobile applications", "microservices architecture", "distributed systems", "machine learning models", "API platforms", "real-time analytics", "developer tools"]
SKILLS_IT = ["Python, JavaScript, and SQL", "React, Node.js, and TypeScript", "AWS, Docker, and Kubernetes", "Java, Spring Boot, and PostgreSQL", "Go, gRPC, and Kafka", "Ruby on Rails and Redis", "C++, Linux, and networking", "TensorFlow, PyTorch, and data analysis", "Swift, Objective-C, and UIKit", "Angular, .NET, and Azure"]
PASSIONS = ["clean code and best practices", "user experience and performance", "data-driven decision making", "open source and community", "innovation and problem solving", "security and reliability", "scalability and efficiency"]
RESPONSIBILITIES = ["designing and implementing new features", "leading technical architecture decisions", "optimizing system performance and reliability", "building CI/CD pipelines and automation", "developing RESTful APIs and microservices", "conducting code reviews and mentoring junior developers", "analyzing requirements and translating them into technical solutions"]
TEAMS = ["product managers, designers, and engineers", "a cross-functional agile team", "stakeholders across the organization", "our platform engineering team", "frontend and backend developers"]
DELIVERABLES = ["high-quality software products", "scalable and reliable systems", "innovative solutions for our customers", "data-driven insights and tools", "seamless user experiences"]
REQUIREMENTS_GENERAL = ["excellent communication skills", "strong analytical and problem-solving abilities", "ability to work independently and in teams", "attention to detail and organizational skills", "proficiency in relevant software tools"]


def generate_description(title, company, category, city, job_type):
    """Generate a realistic job description."""
    templates = DESC_TEMPLATES.get(category, DESC_TEMPLATES["default"])
    template = random.choice(templates)

    years = random.choice(["2", "3", "5", "7", "10"])

    desc = template.format(
        title=title,
        company=company,
        tech_area=random.choice(TECH_AREAS),
        skills=random.choice(SKILLS_IT if category == "Information Technology" else REQUIREMENTS_GENERAL),
        passion=random.choice(PASSIONS),
        responsibility=random.choice(RESPONSIBILITIES),
        years=years,
        team=random.choice(TEAMS),
        deliverable=random.choice(DELIVERABLES),
        action="develop and improve",
        product="core platform",
        domain="software development",
        capability="solve complex technical challenges",
        tech_stack="modern technologies",
        environment="fast-paced, collaborative",
        territory="key enterprise accounts",
        client_type="C-level executives",
        achievement="exceeding quota",
        tools="CRM platforms like Salesforce",
        industry="technology",
        requirements=random.choice(REQUIREMENTS_GENERAL),
        type=job_type,
        location=city,
    )

    # Build HTML description with requirements section
    requirements = random.sample(REQUIREMENTS_GENERAL, min(3, len(REQUIREMENTS_GENERAL)))
    skills_list = random.choice(SKILLS_IT if category == "Information Technology" else [REQUIREMENTS_GENERAL[0]])

    html = f"""<p>{desc}</p>
<h3>Responsibilities</h3>
<ul>
{"".join(f"<li>{r}</li>" for r in random.sample(RESPONSIBILITIES, min(4, len(RESPONSIBILITIES))))}
</ul>
<h3>Requirements</h3>
<ul>
<li>{years}+ years of relevant experience</li>
{"".join(f"<li>{r}</li>" for r in requirements)}
<li>Experience with {skills_list}</li>
</ul>
<h3>Benefits</h3>
<ul>
<li>Competitive salary and equity</li>
<li>Health, dental, and vision insurance</li>
<li>Flexible work arrangements</li>
<li>Professional development budget</li>
<li>{'Remote work options' if random.random() > 0.5 else 'Generous PTO'}</li>
</ul>"""
    return html


def generate_jobs(n=1000):
    """Generate n realistic job records."""
    jobs = []
    job_id = 0

    for category, count in CATEGORIES:
        actual_count = min(count, n - len(jobs))
        if actual_count <= 0:
            break

        titles = TITLES_BY_CATEGORY.get(category, TITLES_BY_CATEGORY["Other"])

        for _ in range(actual_count):
            title = random.choice(titles)
            # Occasionally add seniority prefix or location suffix
            if random.random() > 0.7:
                prefix = random.choice(["Senior ", "Junior ", "Lead ", "Staff ", "Principal "])
                title = prefix + title
            company = random.choice(COMPANIES)
            city, state, country = random.choice(CITIES)
            remote = random.random() > 0.7
            job_type = random.choices(JOB_TYPES, weights=[60, 10, 15, 5, 10])[0]
            experience = random.choices(
                EXPERIENCE_LEVELS,
                weights=[20, 15, 40, 15, 10]
            )[0]
            education = random.choices(
                EDUCATION_LEVELS + [""],
                weights=[10, 10, 40, 20, 10, 10]
            )[0]

            job_id += 1
            ref = f"{job_id:010X}"

            jobs.append({
                'id': ref,
                'title': title,
                'company': company,
                'city': city,
                'state': state,
                'country': country,
                'remote': remote,
                'description': generate_description(title, company, category, city, job_type),
                'education': education,
                'job_type': job_type,
                'category': category,
                'experience': experience,
                'url': f'https://apply.workable.com/j/{ref}',
            })

    random.shuffle(jobs)
    return jobs[:n]


def clean_html(raw_html):
    """Simple HTML to text."""
    if not raw_html:
        return ''
    text = re.sub(r'<[^>]+>', ' ', raw_html)
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
    print(f'Generating {SAMPLE_SIZE} sample jobs...')
    random.seed(42)
    np.random.seed(42)

    jobs = generate_jobs(SAMPLE_SIZE)
    df = pd.DataFrame(jobs)
    print(f'Generated {len(df)} jobs across {df["category"].nunique()} categories')

    # Clean and preprocess
    df['description_clean'] = df['description'].apply(clean_html)
    df['title_clean'] = df['title'].apply(preprocess_text)
    df['desc_processed'] = df['description_clean'].apply(preprocess_text)

    # Fill empties
    df['category'] = df['category'].replace('', 'Other')
    df['experience'] = df['experience'].replace('', 'Not Specified')
    df['education'] = df['education'].replace('', 'Not Specified')
    df['job_type'] = df['job_type'].replace('', 'Not Specified')

    print(f'\nCategory distribution:')
    print(df['category'].value_counts().head(10))

    # === BASELINE MODEL ===
    print('\n--- Baseline Model (Title-Only Cosine Similarity) ---')
    title_vectorizer = TfidfVectorizer(
        ngram_range=(1, 2), max_features=5000,
        stop_words='english', sublinear_tf=True,
    )
    title_tfidf = title_vectorizer.fit_transform(df['title_clean'])
    print(f'Title TF-IDF shape: {title_tfidf.shape}')

    title_sim_matrix = cosine_similarity(title_tfidf)
    baseline_recs = get_top_n_recs(title_sim_matrix, df, n=TOP_N)
    print(f'Baseline recs: {len(baseline_recs)} jobs')

    # === ENHANCED MODEL ===
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
    print(f'Weighted recs: {len(weighted_recs)} jobs')

    # Spot checks
    for i in [0, 50, 200, 500]:
        if i < len(df):
            job = df.iloc[i]
            print(f'\n  Source: {job["title"]} ({job["company"]}, {job["city"]}) [{job["category"]}]')
            b_ids = {r['id'] for r in baseline_recs[job['id']]}
            w_ids = {r['id'] for r in weighted_recs[job['id']]}
            overlap = len(b_ids & w_ids)
            print(f'    Baseline:')
            for rec in baseline_recs[job['id']]:
                r = df[df['id'] == rec['id']].iloc[0]
                print(f'      -> {r["title"]} ({r["company"]}, {r["city"]}) score={rec["score"]:.4f}')
            print(f'    Weighted:')
            for rec in weighted_recs[job['id']]:
                r = df[df['id'] == rec['id']].iloc[0]
                print(f'      -> {r["title"]} ({r["company"]}, {r["city"]}) score={rec["score"]:.4f}')
            print(f'    Overlap: {overlap}/{TOP_N}')

    # Overlap analysis
    overlaps = []
    for job_id in baseline_recs:
        b_ids = {r['id'] for r in baseline_recs[job_id]}
        w_ids = {r['id'] for r in weighted_recs[job_id]}
        overlaps.append(len(b_ids & w_ids))
    overlap_counts = Counter(overlaps)
    print(f'\nOverall overlap: avg {np.mean(overlaps):.1f} shared recs per job')
    for k, v in sorted(overlap_counts.items()):
        print(f'  {k}/{TOP_N}: {v} jobs ({v / len(df) * 100:.1f}%)')

    # === EXPORT ===
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
            'education': row['education'] if row['education'] else 'Not Specified',
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
        label = f'{size_kb / 1024:.1f} MB' if size_kb > 1024 else f'{size_kb:.0f} KB'
        print(f'  {path}: {label}')

    # Sanity check
    job_ids = {j['id'] for j in jobs_export}
    for recs in [baseline_recs, weighted_recs]:
        for job_id, rec_list in recs.items():
            assert job_id in job_ids
            assert len(rec_list) == TOP_N
            for r in rec_list:
                assert r['id'] in job_ids

    print('\nAll checks passed! JSON files ready for web app.')


if __name__ == '__main__':
    main()
