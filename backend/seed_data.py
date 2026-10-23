"""Massive seed across institutions, departments (engineering/MBA/pharma/medical/diploma/degree),
students, recruiters, jobs, applications, DSA progress (curriculum catalog), aptitude, ATS, interviews,
announcements, training programs, and KMIT real placement data 2017-18 â†’ 2025-26.
"""
from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone, timedelta

from dsa_catalog import DSA_TOTAL, DSA_TOPICS, build_dsa_question_bank, question_bank_by_topic

APTITUDE_SECTIONS = [
    {"code": "QUANT", "name": "Quantitative Aptitude", "topics": ["Numbers", "Percentages", "Profit & Loss", "Time-Speed-Distance", "Time & Work", "Ratios", "Permutations & Combinations", "Probability"]},
    {"code": "REASON", "name": "Logical Reasoning", "topics": ["Coding-Decoding", "Series", "Blood Relations", "Direction Sense", "Syllogisms", "Puzzles", "Seating Arrangement"]},
    {"code": "VERBAL", "name": "Verbal Ability", "topics": ["Reading Comprehension", "Sentence Correction", "Para Jumbles", "Vocabulary", "Idioms"]},
    {"code": "DI", "name": "Data Interpretation", "topics": ["Tables", "Pie Charts", "Bar Graphs", "Line Charts", "Caselets"]},
]

# ============== REAL KMIT PLACEMENT DATA (2017-18 â†’ 2025-26) ==============
KMIT_PLACEMENT_RECORDS = [
    ("2025-26", "Amazon", 4, 80.0), ("2025-26", "Google", 3, 54.5), ("2025-26", "Microsoft", 5, 44.0),
    ("2025-26", "Salesforce", 6, 38.0), ("2025-26", "ServiceNow", 4, 42.0), ("2025-26", "Adobe", 3, 35.0),
    ("2025-26", "Goldman Sachs", 5, 32.0), ("2025-26", "JP Morgan Chase", 8, 28.0), ("2025-26", "Deloitte", 22, 12.5),
    ("2025-26", "Accenture", 38, 7.5), ("2025-26", "TCS", 45, 7.0), ("2025-26", "Infosys", 32, 7.5),
    ("2025-26", "Wipro", 28, 6.5), ("2025-26", "Cognizant", 30, 7.2), ("2025-26", "Capgemini", 24, 6.8),
    ("2025-26", "HCL Technologies", 26, 6.5), ("2025-26", "Tech Mahindra", 22, 6.2), ("2025-26", "LTIMindtree", 18, 7.5),
    ("2025-26", "Mphasis", 14, 7.0), ("2025-26", "Persistent Systems", 16, 8.5), ("2025-26", "ZS Associates", 6, 16.0),
    ("2025-26", "Walmart Global Tech", 5, 24.0), ("2025-26", "DE Shaw", 2, 38.0), ("2025-26", "Cisco", 7, 22.0),
    ("2025-26", "Qualcomm", 3, 28.0), ("2025-26", "Nvidia", 2, 36.0), ("2025-26", "Oracle", 9, 18.0),
    ("2025-26", "SAP Labs", 4, 22.0), ("2025-26", "Atlassian", 2, 32.0), ("2025-26", "Uber", 3, 30.0),
    ("2024-25", "Google", 4, 52.0), ("2024-25", "Amazon", 5, 46.0), ("2024-25", "ServiceNow", 3, 42.0),
    ("2024-25", "Microsoft", 4, 41.0), ("2024-25", "Salesforce", 5, 36.0), ("2024-25", "Goldman Sachs", 4, 30.0),
    ("2024-25", "Adobe", 2, 32.0), ("2024-25", "TCS", 52, 6.8), ("2024-25", "Infosys", 38, 7.2),
    ("2024-25", "Wipro", 30, 6.2), ("2024-25", "Accenture", 42, 7.2), ("2024-25", "Deloitte", 18, 12.0),
    ("2024-25", "Cognizant", 28, 7.0), ("2024-25", "Capgemini", 22, 6.5), ("2024-25", "ZS Associates", 5, 14.5),
    ("2023-24", "Intuit", 2, 49.8), ("2023-24", "Salesforce", 4, 47.0), ("2023-24", "Amazon", 3, 44.0),
    ("2023-24", "Microsoft", 3, 39.0), ("2023-24", "Google", 2, 45.0), ("2023-24", "Goldman Sachs", 3, 28.5),
    ("2023-24", "TCS", 48, 6.5), ("2023-24", "Infosys", 36, 6.8), ("2023-24", "Accenture", 40, 7.0),
    ("2023-24", "Wipro", 28, 6.0), ("2023-24", "Deloitte", 16, 11.5),
    ("2022-23", "Microsoft", 3, 38.0), ("2022-23", "Amazon", 4, 36.0), ("2022-23", "Salesforce", 3, 32.0),
    ("2022-23", "Goldman Sachs", 2, 26.0), ("2022-23", "TCS", 56, 6.2), ("2022-23", "Infosys", 42, 6.5),
    ("2022-23", "Wipro", 34, 5.8), ("2022-23", "Accenture", 48, 6.8),
    ("2021-22", "Microsoft", 2, 32.0), ("2021-22", "Amazon", 3, 30.0), ("2021-22", "TCS", 62, 5.8),
    ("2021-22", "Infosys", 44, 6.2), ("2021-22", "Wipro", 38, 5.5), ("2021-22", "Accenture", 52, 6.5),
    ("2020-21", "Amazon", 2, 28.0), ("2020-21", "TCS", 58, 5.5), ("2020-21", "Infosys", 40, 5.8),
    ("2020-21", "Wipro", 36, 5.2), ("2020-21", "Accenture", 48, 6.0),
    ("2019-20", "Amazon", 2, 25.0), ("2019-20", "TCS", 52, 5.2), ("2019-20", "Infosys", 38, 5.5),
    ("2019-20", "Cognizant", 30, 5.0), ("2019-20", "Wipro", 34, 5.0),
    ("2018-19", "TCS", 48, 5.0), ("2018-19", "Infosys", 36, 5.2), ("2018-19", "Wipro", 32, 4.8),
    ("2018-19", "Cognizant", 28, 4.8),
    ("2017-18", "TCS", 42, 4.5), ("2017-18", "Infosys", 34, 4.8), ("2017-18", "Wipro", 28, 4.5),
    ("2017-18", "Cognizant", 26, 4.5),
]

YEAR_AGGREGATES = {
    "2025-26": {"companies": 148, "offers": 702, "avg_lpa": 8.26, "top_offer_lpa": 80.0, "top_company": "Amazon"},
    "2024-25": {"companies": 132, "offers": 685, "avg_lpa": 7.92, "top_offer_lpa": 52.0, "top_company": "Google"},
    "2023-24": {"companies": 118, "offers": 642, "avg_lpa": 7.45, "top_offer_lpa": 49.8, "top_company": "Intuit"},
    "2022-23": {"companies": 104, "offers": 598, "avg_lpa": 6.98, "top_offer_lpa": 38.0, "top_company": "Microsoft"},
    "2021-22": {"companies": 92, "offers": 572, "avg_lpa": 6.45, "top_offer_lpa": 32.0, "top_company": "Microsoft"},
    "2020-21": {"companies": 78, "offers": 524, "avg_lpa": 5.92, "top_offer_lpa": 28.0, "top_company": "Amazon"},
    "2019-20": {"companies": 72, "offers": 488, "avg_lpa": 5.65, "top_offer_lpa": 25.0, "top_company": "Amazon"},
    "2018-19": {"companies": 64, "offers": 442, "avg_lpa": 5.28, "top_offer_lpa": 18.0, "top_company": "Microsoft"},
    "2017-18": {"companies": 58, "offers": 412, "avg_lpa": 4.92, "top_offer_lpa": 16.5, "top_company": "Amazon"},
}

# ============== INSTITUTIONS (multi-stream) ==============
INSTITUTIONS = [
    {
        "institution_id": "inst_vnr",
        "name": "VNR Vignana Jyothi Institute of Engineering & Technology",
        "short_name": "VNRVJIET",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 1995,
        "logo": "V",
        "tagline": "Engineering Excellence and Innovation.",
    },
    {
        "institution_id": "inst_vce",
        "name": "Vasavi College of Engineering",
        "short_name": "VCE",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "Osmania University",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech", "Civil"],
        "established": 1981,
        "logo": "V",
        "tagline": "Education for professional competence.",
    },
    {
        "institution_id": "inst_cbit",
        "name": "Chaitanya Bharathi Institute of Technology",
        "short_name": "CBIT",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "Osmania University",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 1979,
        "logo": "C",
        "tagline": "Swayam Tejaswin Bhava.",
    },
    {
        "institution_id": "inst_cvr",
        "name": "CVR College of Engineering",
        "short_name": "CVR",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 2001,
        "logo": "C",
        "tagline": "In pursuit of excellence.",
    },
    {
        "institution_id": "inst_mgit",
        "name": "Mahatma Gandhi Institute of Technology",
        "short_name": "MGIT",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 1997,
        "logo": "M",
        "tagline": "Chaitanya Samskrithi.",
    },
    {
        "institution_id": "inst_mvsrec",
        "name": "MVSR Engineering College",
        "short_name": "MVSREC",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "Osmania University",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 1981,
        "logo": "M",
        "tagline": "Excellence in education and character.",
    },
    {
        "institution_id": "inst_bvrit",
        "name": "BVRIT Hyderabad",
        "short_name": "BVRIT",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2012,
        "logo": "B",
        "tagline": "Empowering women in engineering.",
    },
    {
        "institution_id": "inst_kmit",
        "name": "Keshav Memorial Institute of Technology",
        "short_name": "KMIT",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "CSE-AIML", "CSE-DS", "ECE"],
        "established": 2007,
        "logo": "K",
        "tagline": "Where placement intelligence is born.",
    },
    {
        "institution_id": "inst_mrec",
        "name": "Malla Reddy Engineering College",
        "short_name": "MREC",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 2002,
        "logo": "M",
        "tagline": "Step into light.",
    },
    {
        "institution_id": "inst_mrcet",
        "name": "Malla Reddy College of Engineering & Technology",
        "short_name": "MRCET",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 2004,
        "logo": "M",
        "tagline": "Quality education is our mission.",
    },
    {
        "institution_id": "inst_mrits",
        "name": "Malla Reddy Institute of Technology & Science",
        "short_name": "MRITS",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2005,
        "logo": "M",
        "tagline": "Nurturing engineering talent.",
    },
    {
        "institution_id": "inst_snist",
        "name": "Sreenidhi Institute of Science & Technology",
        "short_name": "SNIST",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 1997,
        "logo": "S",
        "tagline": "Leader in technological education.",
    },
    {
        "institution_id": "inst_griet",
        "name": "Gokaraju Rangaraju Institute of Engineering & Technology",
        "short_name": "GRIET",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 1997,
        "logo": "G",
        "tagline": "Knowledge is power.",
    },
    {
        "institution_id": "inst_cmrcet",
        "name": "CMR College of Engineering & Technology",
        "short_name": "CMRCET",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 2002,
        "logo": "C",
        "tagline": "Explore, Invent, Inspire.",
    },
    {
        "institution_id": "inst_cmrit",
        "name": "CMR Institute of Technology",
        "short_name": "CMRIT",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2005,
        "logo": "C",
        "tagline": "Technical education for global success.",
    },
    {
        "institution_id": "inst_cmrtc",
        "name": "CMR Technical Campus",
        "short_name": "CMRTC",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 2009,
        "logo": "C",
        "tagline": "Innovation and technical drive.",
    },
    {
        "institution_id": "inst_au",
        "name": "Anurag University",
        "short_name": "AU",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "Autonomous",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 2002,
        "logo": "A",
        "tagline": "Learn, Lead, and Achieve.",
    },
    {
        "institution_id": "inst_gcet",
        "name": "Geethanjali College of Engineering & Technology",
        "short_name": "GCET",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2005,
        "logo": "G",
        "tagline": "Shaping careers, building values.",
    },
    {
        "institution_id": "inst_ace",
        "name": "ACE Engineering College",
        "short_name": "ACE",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2007,
        "logo": "A",
        "tagline": "Gateway to global opportunities.",
    },
    {
        "institution_id": "inst_gnits",
        "name": "G. Narayanamma Institute of Technology & Science",
        "short_name": "GNITS",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 1997,
        "logo": "G",
        "tagline": "Empowering women engineering professionals.",
    },
    {
        "institution_id": "inst_jntuhceh",
        "name": "JNTUH College of Engineering Hyderabad",
        "short_name": "JNTUH-CEH",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech", "Civil"],
        "established": 1965,
        "logo": "J",
        "tagline": "Frontrunner in technical education.",
    },
    {
        "institution_id": "inst_ouce",
        "name": "Osmania University College of Engineering",
        "short_name": "OUCE",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "Osmania University",
        "departments": ["CSE", "ECE", "EEE", "Mech", "Civil"],
        "established": 1929,
        "logo": "O",
        "tagline": "Pioneering technology and research.",
    },
    {
        "institution_id": "inst_mjcet",
        "name": "Muffakham Jah College of Engineering & Technology",
        "short_name": "MJCET",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "Osmania University",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech", "Civil"],
        "established": 1980,
        "logo": "M",
        "tagline": "Knowledge, Wisdom, Action.",
    },
    {
        "institution_id": "inst_iare",
        "name": "Institute of Aeronautical Engineering",
        "short_name": "IARE",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Aeronautical"],
        "established": 2000,
        "logo": "I",
        "tagline": "Liberation through education.",
    },
    {
        "institution_id": "inst_vardhaman",
        "name": "Vardhaman College of Engineering",
        "short_name": "VCE-V",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 1999,
        "logo": "V",
        "tagline": "Chasing heights of innovation.",
    },
    {
        "institution_id": "inst_swec",
        "name": "Sridevi Women's Engineering College",
        "short_name": "SWEC",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2001,
        "logo": "S",
        "tagline": "Igniting women's excellence.",
    },
    {
        "institution_id": "inst_tkrcet",
        "name": "TKR College of Engineering & Technology",
        "short_name": "TKRCET",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 2002,
        "logo": "T",
        "tagline": "Service through education.",
    },
    {
        "institution_id": "inst_mcet",
        "name": "Methodist College of Engineering & Technology",
        "short_name": "MCET",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "Osmania University",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2008,
        "logo": "M",
        "tagline": "Nurturing global engineers.",
    },
    {
        "institution_id": "inst_ngit",
        "name": "Neil Gogte Institute of Technology",
        "short_name": "NGIT",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "CSE-AIML", "CSE-DS"],
        "established": 2017,
        "logo": "N",
        "tagline": "Redefining engineering education.",
    },
    {
        "institution_id": "inst_kmec",
        "name": "Keshav Memorial College of Engineering",
        "short_name": "KMEC",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "CSE-AIML"],
        "established": 2020,
        "logo": "K",
        "tagline": "Engineering with a focus on future tech.",
    },
    {
        "institution_id": "inst_mecs",
        "name": "Matrusri Engineering College",
        "short_name": "MECS",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "Osmania University",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 2011,
        "logo": "M",
        "tagline": "Technical skill, social responsibility.",
    },
    {
        "institution_id": "inst_smec",
        "name": "St. Martin's Engineering College",
        "short_name": "SMEC",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 2002,
        "logo": "S",
        "tagline": "Empowering youth.",
    },
    {
        "institution_id": "inst_biet",
        "name": "Bharat Institute of Engineering & Technology",
        "short_name": "BIET",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2001,
        "logo": "B",
        "tagline": "Excellence in technology.",
    },
    {
        "institution_id": "inst_sit",
        "name": "Scient Institute of Technology",
        "short_name": "SIT",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2001,
        "logo": "S",
        "tagline": "Commitment to future innovators.",
    },
    {
        "institution_id": "inst_nrec",
        "name": "Narsimha Reddy Engineering College",
        "short_name": "NREC",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2007,
        "logo": "N",
        "tagline": "Building professional paths.",
    },
    {
        "institution_id": "inst_kprit",
        "name": "Kommuri Pratap Reddy Institute of Technology",
        "short_name": "KPRIT",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2008,
        "logo": "K",
        "tagline": "Imagine, Innovate, Inspire.",
    },
    {
        "institution_id": "inst_jpnce",
        "name": "Jayaprakash Narayan College of Engineering",
        "short_name": "JPNCE",
        "type": "Engineering",
        "city": "Mahabubnagar", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 1997,
        "logo": "J",
        "tagline": "Education to the rural sector.",
    },
    {
        "institution_id": "inst_mist",
        "name": "Mahaveer Institute of Science & Technology",
        "short_name": "MIST",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2001,
        "logo": "M",
        "tagline": "Excellence in every endeavor.",
    },
    {
        "institution_id": "inst_vits",
        "name": "Vignan Institute of Technology & Science",
        "short_name": "VITS",
        "type": "Engineering",
        "city": "Yadadri", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 1999,
        "logo": "V",
        "tagline": "A vision for quality education.",
    },
    {
        "institution_id": "inst_hitam",
        "name": "Hyderabad Institute of Technology & Management",
        "short_name": "HITAM",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2001,
        "logo": "H",
        "tagline": "Doing what's right for the student.",
    },
    {
        "institution_id": "inst_sdies",
        "name": "Sree Dattha Institute of Engineering & Science",
        "short_name": "SDIES",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2001,
        "logo": "S",
        "tagline": "Empowering generations.",
    },
    {
        "institution_id": "inst_tpce",
        "name": "Talla Padmavathi College of Engineering",
        "short_name": "TPCE",
        "type": "Engineering",
        "city": "Warangal", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2008,
        "logo": "T",
        "tagline": "Education that transcends boundaries.",
    },
    {
        "institution_id": "inst_jits",
        "name": "Jyothishmathi Institute of Technology & Science",
        "short_name": "JITS",
        "type": "Engineering",
        "city": "Karimnagar", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 1997,
        "logo": "J",
        "tagline": "A beacon of light.",
    },
    {
        "institution_id": "inst_scet",
        "name": "Samskruti College of Engineering & Technology",
        "short_name": "SCET",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2005,
        "logo": "S",
        "tagline": "Quality in engineering values.",
    },
    {
        "institution_id": "inst_sidd",
        "name": "Siddharth Institute of Engineering & Technology",
        "short_name": "SIET",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2001,
        "logo": "S",
        "tagline": "In search of technical perfection.",
    },
    {
        "institution_id": "inst_vcet",
        "name": "Visvesvaraya College of Engineering & Technology",
        "short_name": "VCET",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2007,
        "logo": "V",
        "tagline": "Engineering for sustainable future.",
    },
    {
        "institution_id": "inst_sicet",
        "name": "Sri Indu College of Engineering & Technology",
        "short_name": "SICET",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2001,
        "logo": "S",
        "tagline": "Pioneering technical education.",
    },
    {
        "institution_id": "inst_kits",
        "name": "Kakatiya Institute of Technology & Science",
        "short_name": "KITS",
        "type": "Engineering",
        "city": "Warangal", "state": "Telangana",
        "affiliated_university": "Kakatiya University",
        "departments": ["CSE", "IT", "ECE", "EEE", "Mech"],
        "established": 1980,
        "logo": "K",
        "tagline": "Strive for perfection.",
    },
    {
        "institution_id": "inst_nmrec",
        "name": "Nalla Malla Reddy Engineering College",
        "short_name": "NMREC",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2001,
        "logo": "N",
        "tagline": "Complete education.",
    },
    {
        "institution_id": "inst_liet",
        "name": "Lords Institute of Engineering & Technology",
        "short_name": "LIET",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 2002,
        "logo": "L",
        "tagline": "Gateway to success.",
    },
    {
        "institution_id": "inst_scets",
        "name": "Shadan College of Engineering & Technology",
        "short_name": "SCET-S",
        "type": "Engineering",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "JNTUH",
        "departments": ["CSE", "IT", "ECE", "EEE"],
        "established": 1995,
        "logo": "S",
        "tagline": "Excellence in engineering diversity.",
    },
    {
        "institution_id": "inst_iimb",
        "name": "Loyola Institute of Management",
        "short_name": "LIM",
        "type": "Management",
        "city": "Chennai", "state": "Tamil Nadu",
        "affiliated_university": "Madras University",
        "departments": ["MBA-Finance", "MBA-Marketing", "MBA-Operations", "MBA-HR", "MBA-Analytics"],
        "established": 1985,
        "logo": "L",
        "tagline": "Future business leaders, measurably.",
    },
    {
        "institution_id": "inst_pharma",
        "name": "Sri Padmavati Mahila Pharmacy College",
        "short_name": "SPMP",
        "type": "Pharmacy",
        "city": "Tirupati", "state": "Andhra Pradesh",
        "affiliated_university": "JNTUA",
        "departments": ["B-Pharm", "M-Pharm", "Pharm-D"],
        "established": 1996,
        "logo": "S",
        "tagline": "Pharma research to industry.",
    },
    {
        "institution_id": "inst_medical",
        "name": "Gandhi Medical College",
        "short_name": "GMC",
        "type": "Medical",
        "city": "Secunderabad", "state": "Telangana",
        "affiliated_university": "KNRUHS",
        "departments": ["MBBS", "Pediatrics", "General Surgery", "Internal Medicine"],
        "established": 1954,
        "logo": "G",
        "tagline": "Clinical excellence, residency placements.",
    },
    {
        "institution_id": "inst_degree",
        "name": "St. Mary's Degree College",
        "short_name": "SMDC",
        "type": "Degree",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "Osmania University",
        "departments": ["B.Com", "BBA", "B.Sc Computers", "B.A Economics"],
        "established": 1979,
        "logo": "S",
        "tagline": "Degree to career, fast-tracked.",
    },
    {
        "institution_id": "inst_diploma",
        "name": "Government Polytechnic — Masab Tank",
        "short_name": "GPT-MT",
        "type": "Diploma",
        "city": "Hyderabad", "state": "Telangana",
        "affiliated_university": "SBTET",
        "departments": ["Mechanical", "Civil", "EEE", "Computer Engg"],
        "established": 1958,
        "logo": "G",
        "tagline": "Skilled diploma → industry pipeline.",
    },
]

# ============== RECRUITERS ==============
RECRUITERS = [
    {"name": "Amazon", "industry": "E-commerce / Cloud", "type": "Product", "headcount": 1_540_000, "logo_color": "#FF9900"},
    {"name": "Google", "industry": "Internet / AI", "type": "Product", "headcount": 182_000, "logo_color": "#4285F4"},
    {"name": "Microsoft", "industry": "Software / Cloud", "type": "Product", "headcount": 221_000, "logo_color": "#00A4EF"},
    {"name": "ServiceNow", "industry": "Enterprise SaaS", "type": "Product", "headcount": 22_000, "logo_color": "#00C2A8"},
    {"name": "Salesforce", "industry": "CRM SaaS", "type": "Product", "headcount": 76_000, "logo_color": "#00A1E0"},
    {"name": "Adobe", "industry": "Creative / Cloud", "type": "Product", "headcount": 30_000, "logo_color": "#FA0F00"},
    {"name": "Goldman Sachs", "industry": "Investment Banking", "type": "Finance", "headcount": 49_000, "logo_color": "#7399C6"},
    {"name": "JP Morgan Chase", "industry": "Banking", "type": "Finance", "headcount": 313_000, "logo_color": "#0F4C81"},
    {"name": "Deloitte", "industry": "Consulting", "type": "Services", "headcount": 460_000, "logo_color": "#86BC25"},
    {"name": "Accenture", "industry": "IT Services", "type": "Services", "headcount": 743_000, "logo_color": "#A100FF"},
    {"name": "TCS", "industry": "IT Services", "type": "Services", "headcount": 614_000, "logo_color": "#1E2A78"},
    {"name": "Infosys", "industry": "IT Services", "type": "Services", "headcount": 343_000, "logo_color": "#007CC3"},
    {"name": "Cognizant", "industry": "IT Services", "type": "Services", "headcount": 347_000, "logo_color": "#1B3F77"},
    {"name": "Wipro", "industry": "IT Services", "type": "Services", "headcount": 234_000, "logo_color": "#341C53"},
    {"name": "Capgemini", "industry": "IT Services", "type": "Services", "headcount": 360_000, "logo_color": "#0070AD"},
    {"name": "ZS Associates", "industry": "Pharma Analytics", "type": "Consulting", "headcount": 14_000, "logo_color": "#00A0DF"},
    {"name": "Walmart Global Tech", "industry": "Retail Tech", "type": "Product", "headcount": 25_000, "logo_color": "#0071CE"},
    {"name": "DE Shaw", "industry": "Quantitative Finance", "type": "Finance", "headcount": 2_000, "logo_color": "#003366"},
    {"name": "Intuit", "industry": "FinTech SaaS", "type": "Product", "headcount": 18_000, "logo_color": "#365EBF"},
    {"name": "Cisco", "industry": "Networking", "type": "Product", "headcount": 84_000, "logo_color": "#1BA0D7"},
    {"name": "Nvidia", "industry": "Semiconductors / AI", "type": "Product", "headcount": 32_000, "logo_color": "#76B900"},
    {"name": "Oracle", "industry": "Database / Cloud", "type": "Product", "headcount": 159_000, "logo_color": "#F80000"},
]

JOB_TITLES_BY_TYPE = {
    "Product": ["Software Development Engineer", "Product Engineer I", "Systems Engineer", "Cloud Engineer", "ML Engineer"],
    "Finance": ["Quantitative Analyst", "Risk Analyst", "Investment Banking Analyst", "Financial Engineer"],
    "Services": ["Associate Software Engineer", "Systems Engineer", "Digital Engineer", "Consultant Trainee"],
    "Consulting": ["Business Analyst", "Decision Analytics Associate", "Strategy Consultant"],
}

# ============== STUDENT NAMES ==============
FIRST_NAMES = [
    "Aarav", "Aditya", "Akshay", "Ananya", "Anish", "Arjun", "Bhavya", "Chaitanya",
    "Deepak", "Divya", "Esha", "Gaurav", "Harini", "Ishaan", "Jahnavi", "Karthik",
    "Lavanya", "Manasvi", "Nikhil", "Pranav", "Priya", "Rahul", "Riya", "Rohan",
    "Sahithi", "Sai", "Sanjana", "Shreya", "Siddharth", "Sneha", "Srija", "Tejas",
    "Tanvi", "Varun", "Vedika", "Vignesh", "Yashas", "Zara", "Abhinav", "Charvi",
    "Pooja", "Aishwarya", "Kavya", "Meghana", "Hemanth", "Surya", "Vamsi", "Yashwanth"
]
LAST_NAMES = [
    "Reddy", "Rao", "Sharma", "Verma", "Patel", "Naidu", "Kumar", "Sastry",
    "Gupta", "Choudhary", "Iyer", "Menon", "Pillai", "Nair", "Kapoor", "Joshi",
    "Singh", "Bhargav", "Chowdary", "Mehta", "Goud", "Kasaraneni", "Kotha",
]

PROGRAMS = [
    {"code": "CRT", "name": "Campus Recruitment Training", "duration_weeks": 16, "modules": 12, "stream": "Engineering"},
    {"code": "IM", "name": "Interview Master", "duration_weeks": 8, "modules": 8, "stream": "All"},
    {"code": "FDP", "name": "Faculty Development Programme", "duration_weeks": 6, "modules": 6, "stream": "Faculty"},
    {"code": "DSA", "name": "DSA A-to-Z Mastery", "duration_weeks": 12, "modules": 18, "stream": "Engineering"},
    {"code": "APT", "name": "Aptitude & Reasoning", "duration_weeks": 6, "modules": 10, "stream": "All"},
    {"code": "BIZ", "name": "Business Case Studies", "duration_weeks": 10, "modules": 12, "stream": "Management"},
    {"code": "COMM", "name": "Communication Mastery", "duration_weeks": 4, "modules": 6, "stream": "All"},
]

SKILLS_POOL = ["Python", "Java", "C++", "JavaScript", "React", "Node.js", "TypeScript", "SQL", "MongoDB",
               "AWS", "Docker", "Kubernetes", "TensorFlow", "PyTorch", "System Design", "Microservices",
               "GraphQL", "REST APIs", "Git", "Linux", "Spring Boot", "Django", "FastAPI", "Tailwind"]


def _name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def seed_payload() -> dict:
    """Return all documents to insert into a fresh DB."""
    random.seed(7)
    now = datetime.now(timezone.utc)

    # Programmatically expand recruiters list to 500+ items
    local_recruiters = list(RECRUITERS)
    comp_prefixes = ["Apex", "Innova", "Quantum", "Nexus", "Stellar", "Vector", "Optima", "Synergy", "Zenith", "Alpha", "Beta", "Gamma", "Delta", "Sigma", "Omega", "Cognitive", "Digital", "Cloud", "Cyber", "Data", "Tech", "Systems", "Core", "Global", "Intel", "Logix", "Matrix", "Nova", "Omni", "Prism", "Quasar", "Radiant", "Vertex", "Web", "Zero"]
    comp_suffixes = ["Technologies", "Solutions", "Systems", "Software", "Labs", "Analytics", "Intelligence", "Dynamics", "Networks", "Consulting", "Group", "Digital", "Tech", "Partners", "Global", "Enterprises", "Industries", "Ventures", "Services", "Designs", "Innovations"]
    industries = ["Software / Cloud", "Enterprise SaaS", "Investment Banking", "Consulting", "IT Services", "Pharma Analytics", "Retail Tech", "Quantitative Finance", "FinTech SaaS", "Networking", "Semiconductors / AI", "Database / Cloud", "Cybersecurity", "HealthTech", "AdTech", "EdTech", "CleanTech", "Logistics", "E-commerce"]
    types = ["Product", "Services", "Finance", "Consulting"]
    logo_colors = ["#FF5733", "#33FF57", "#3357FF", "#F3FF33", "#FF33F3", "#33FFF0", "#FFAF33", "#AF33FF", "#33FFAF", "#FF3333", "#33FF33", "#3333FF", "#E91E63", "#9C27B0", "#673AB7", "#3F51B5", "#00BCD4", "#009688", "#4CAF50", "#FFEB3B", "#FF9800", "#FF5722", "#795548", "#607D8B"]
    
    generated_names = set(r["name"] for r in local_recruiters)
    while len(local_recruiters) < 520:
        pref = random.choice(comp_prefixes)
        suff = random.choice(comp_suffixes)
        name = f"{pref} {suff}"
        if name not in generated_names:
            generated_names.add(name)
            rec_type = random.choice(types)
            local_recruiters.append({
                "name": name,
                "industry": random.choice(industries),
                "type": rec_type,
                "headcount": random.randint(100, 100000),
                "logo_color": random.choice(logo_colors),
            })

    docs = {
        "institutions": [], "departments": [], "students": [], "recruiters": [],
        "jobs": [], "applications": [], "dsa_questions": [], "dsa_progress": [], "dsa_question_progress": [], "aptitude_scores": [],
        "ats_reports": [], "interview_reports": [], "announcements": [],
        "training_programs": [], "enrollments": [], "placement_records": [],
        "year_summaries": [], "mous": [], "comm_log": [], "revenue_share": [],
    }
    question_bank = build_dsa_question_bank(now)
    questions_by_topic = question_bank_by_topic(now)
    docs["dsa_questions"].extend(question_bank)

    # -- Institutions --
    for inst in INSTITUTIONS:
        d = dict(inst)
        d["approved"] = True
        d["created_at"] = now.isoformat()
        d["partnership_types"] = ["CRT", "FDP"] if inst["type"] == "Engineering" else ["CRT"]
        docs["institutions"].append(d)

    # KMIT placement records + year summaries
    for year, company, selects, ctc in KMIT_PLACEMENT_RECORDS:
        docs["placement_records"].append({
            "record_id": f"pr_{uuid.uuid4().hex[:10]}",
            "institution_id": "inst_kmit",
            "academic_year": year,
            "company": company,
            "selects": selects,
            "ctc_lpa": ctc,
            "stipend_k": round(ctc * 1000 / 24, 0) if ctc < 20 else round(ctc * 1000 / 18, 0),
            "created_at": now.isoformat(),
        })
    for yr, agg in YEAR_AGGREGATES.items():
        docs["year_summaries"].append({
            "summary_id": f"ys_{yr}",
            "institution_id": "inst_kmit",
            "academic_year": yr,
            **agg,
        })

    # Add synthetic placement records for other institutions so dashboards look populated
    for inst in INSTITUTIONS[1:]:
        for yr in ("2024-25", "2025-26"):
            for company in random.sample([r["name"] for r in local_recruiters], k=7):
                docs["placement_records"].append({
                    "record_id": f"pr_{uuid.uuid4().hex[:10]}",
                    "institution_id": inst["institution_id"],
                    "academic_year": yr,
                    "company": company,
                    "selects": random.randint(2, 25),
                    "ctc_lpa": round(random.uniform(4.0, 28.0), 1),
                    "created_at": now.isoformat(),
                })
        for yr, agg in YEAR_AGGREGATES.items():
            if yr not in ("2024-25", "2025-26"):
                continue
            inst_agg = dict(agg)
            inst_agg["companies"] = int(agg["companies"] * random.uniform(0.3, 0.7))
            inst_agg["offers"] = int(agg["offers"] * random.uniform(0.3, 0.7))
            inst_agg["avg_lpa"] = round(agg["avg_lpa"] * random.uniform(0.7, 1.0), 2)
            inst_agg["top_offer_lpa"] = round(agg["top_offer_lpa"] * random.uniform(0.4, 0.8), 1)
            docs["year_summaries"].append({
                "summary_id": f"ys_{inst['institution_id']}_{yr}",
                "institution_id": inst["institution_id"],
                "academic_year": yr,
                **inst_agg,
            })

    # -- Recruiters --
    for r in local_recruiters:
        docs["recruiters"].append({
            "recruiter_id": "rec_" + r["name"].lower().replace(" ", "_"),
            **r,
            "active": True,
            "hires_total": random.randint(50, 850),
            "drives_count": random.randint(2, 18),
            "avg_ctc_offered": round(random.uniform(7.0, 28.0), 1),
            "created_at": now.isoformat(),
        })

    # -- Jobs / Drives (open & closed) --
    for r in local_recruiters:
        for _ in range(random.randint(2, 4)):
            jt = random.choice(JOB_TITLES_BY_TYPE.get(r["type"], JOB_TITLES_BY_TYPE["Services"]))
            docs["jobs"].append({
                "job_id": f"job_{uuid.uuid4().hex[:10]}",
                "recruiter_id": "rec_" + r["name"].lower().replace(" ", "_"),
                "company": r["name"],
                "title": jt,
                "ctc_lpa": round(random.uniform(6.0, 42.0), 1),
                "location": random.choice(["Hyderabad", "Bangalore", "Pune", "Bangalore", "Chennai", "Remote"]),
                "openings": random.randint(2, 30),
                "applied_count": random.randint(40, 320),
                "status": random.choice(["open", "open", "open", "screening", "interviewing", "closed"]),
                "eligibility_cgpa": round(random.uniform(6.5, 8.0), 1),
                "drive_date": (now + timedelta(days=random.randint(-60, 60))).isoformat(),
                "institutions": ["inst_kmit"] + random.sample([i["institution_id"] for i in INSTITUTIONS[1:]], k=random.randint(0, 3)),
                "stream_filter": random.choice(["Engineering", "All", "Management"]),
            })

    # -- Students (across institutions) --
    student_pool = []
    for inst in INSTITUTIONS:
        per_inst = {"Engineering": 100, "Management": 80, "Pharmacy": 60, "Medical": 50, "Degree": 90, "Diploma": 70}[inst["type"]]
        depts = inst["departments"]
        for i in range(per_inst):
            dept = random.choice(depts)
            dept_code = {"CSE": "05", "IT": "12", "CSE-AIML": "66", "CSE-DS": "67", "ECE": "04"}.get(dept, f"{random.randint(10,99)}")
            yr_admit = random.choice([2022, 2023, 2024])
            fn = random.choice(FIRST_NAMES); ln = random.choice(LAST_NAMES)
            roll = f"{yr_admit % 100:02d}{inst['short_name'][:3].upper()}{dept_code}{i:03d}"
            cgpa = round(random.uniform(6.4, 9.8), 2)
            placed = random.random() < (0.78 if yr_admit == 2022 else 0.55)
            placement = {"placed": False}
            if placed:
                rec = random.choice([p for p in KMIT_PLACEMENT_RECORDS if p[0] == "2024-25"] if inst["institution_id"] == "inst_kmit"
                                    else docs["placement_records"][-50:])
                if isinstance(rec, dict):
                    placement = {"placed": True, "company": rec["company"], "ctc_lpa": rec["ctc_lpa"], "academic_year": rec["academic_year"],
                                 "offer_date": (now - timedelta(days=random.randint(30, 600))).isoformat()}
                else:
                    placement = {"placed": True, "company": rec[1], "ctc_lpa": rec[3], "academic_year": rec[0],
                                 "offer_date": (now - timedelta(days=random.randint(30, 600))).isoformat()}
            stu = {
                "student_id": f"stu_{uuid.uuid4().hex[:12]}",
                "name": f"{fn} {ln}",
                "roll_number": roll,
                "department": dept,
                "batch": f"{yr_admit}-{yr_admit + 4}",
                "institution_id": inst["institution_id"],
                "email": f"{fn.lower()}.{ln.lower()}{i}@{inst['short_name'].lower()}.edu",
                "phone": f"+91 9{random.randint(100000000, 999999999)}",
                "cgpa": cgpa,
                "skills": random.sample(SKILLS_POOL, k=random.randint(4, 9)),
                "projects": random.randint(2, 8),
                "internships": random.randint(0, 3),
                "certifications": random.randint(1, 6),
                "github": f"https://github.com/{fn.lower()}{ln.lower()}",
                "linkedin": f"https://linkedin.com/in/{fn.lower()}-{ln.lower()}",
                "placement": placement,
                "readiness_score": min(100, int(cgpa * 9 + random.randint(0, 25))),
                "ats_score": random.randint(45, 96),
                "created_at": now.isoformat(),
            }
            docs["students"].append(stu)
            student_pool.append(stu)

    # -- DSA progress (curriculum catalog) for engineering students --
    core_ids = {"inst_kmit", "inst_vnr", "inst_vce", "inst_cbit", "inst_cvr", "inst_mgit", "inst_mvsrec", "inst_bvrit"}
    students_by_inst = {}
    for s in student_pool:
        students_by_inst.setdefault(s["institution_id"], []).append(s)
        
    eng_students = []
    for inst in INSTITUTIONS:
        inst_students = students_by_inst.get(inst["institution_id"], [])
        if inst["institution_id"] in core_ids:
            eng_students.extend(inst_students)
        elif inst["type"] == "Engineering":
            eng_students.extend(random.sample(inst_students, k=min(10, len(inst_students))))
    for s in eng_students:
        # Higher CGPA â†’ higher solve rate
        skill_factor = (s["cgpa"] - 6.0) / 4.0  # 0.1 â†’ 0.95
        for t in DSA_TOPICS:
            solved = max(0, int(t["problems"] * (skill_factor + random.uniform(-0.18, 0.18))))
            solved = min(t["problems"], solved)
            attempted = min(t["problems"], solved + random.randint(0, 4))
            last_solved_at = (now - timedelta(days=random.randint(0, 30))).isoformat()
            docs["dsa_progress"].append({
                "progress_id": f"dsa_{uuid.uuid4().hex[:10]}",
                "student_id": s["student_id"],
                "institution_id": s["institution_id"],
                "topic_code": t["code"],
                "topic_name": t["name"],
                "topic_order": t["order"],
                "total": t["problems"],
                "solved": solved,
                "attempted": attempted,
                "last_solved_at": last_solved_at,
            })
            for index, question in enumerate(questions_by_topic[t["code"]][:attempted], start=1):
                is_solved = index <= solved
                mastery = random.randint(72, 96) if is_solved else random.randint(18, 52)
                docs["dsa_question_progress"].append({
                    "progress_id": f"dsqp_{uuid.uuid4().hex[:10]}",
                    "student_id": s["student_id"],
                    "institution_id": s["institution_id"],
                    "question_id": question["question_id"],
                    "topic_code": question["topic_code"],
                    "subtopic_code": question["subtopic_code"],
                    "solved": is_solved,
                    "attempted": True,
                    "mastery": mastery,
                    "revision_count": random.randint(1, 4) if is_solved and mastery >= 82 else random.randint(0, 2),
                    "notes": "",
                    "faculty_comments": [],
                    "difficulty": question["difficulty"],
                    "last_solved_at": last_solved_at if is_solved else None,
                    "updated_at": now.isoformat(),
                })

    # -- Aptitude scores --
    for s in eng_students:
        for sect in APTITUDE_SECTIONS:
            score = max(20, min(100, int(s["cgpa"] * 10 + random.randint(-15, 15))))
            docs["aptitude_scores"].append({
                "score_id": f"apt_{uuid.uuid4().hex[:10]}",
                "student_id": s["student_id"],
                "institution_id": s["institution_id"],
                "section_code": sect["code"],
                "section_name": sect["name"],
                "score_pct": score,
                "accuracy_pct": min(100, score + random.randint(-5, 10)),
                "avg_time_sec": random.randint(40, 120),
                "tests_taken": random.randint(2, 18),
                "attempted_at": (now - timedelta(days=random.randint(0, 90))).isoformat(),
            })

    # -- ATS reports --
    for s in random.sample(eng_students, k=min(160, len(eng_students))):
        docs["ats_reports"].append({
            "ats_id": f"ats_{uuid.uuid4().hex[:10]}",
            "student_id": s["student_id"],
            "institution_id": s["institution_id"],
            "score": s["ats_score"],
            "keyword_match_pct": random.randint(40, 95),
            "format_score": random.randint(60, 100),
            "missing_keywords": random.sample(["Docker", "Kubernetes", "System Design", "Microservices", "GraphQL", "AWS"], k=3),
            "uploaded_filename": f"resume_{s['roll_number'].lower()}.pdf",
            "created_at": (now - timedelta(days=random.randint(0, 60))).isoformat(),
        })

    # -- Interview reports (mock AI interviews) --
    for s in random.sample(eng_students, k=min(140, len(eng_students))):
        confidence = random.randint(50, 95)
        docs["interview_reports"].append({
            "interview_id": f"int_{uuid.uuid4().hex[:10]}",
            "student_id": s["student_id"],
            "institution_id": s["institution_id"],
            "type": random.choice(["Technical", "HR", "System Design", "Behavioral"]),
            "confidence_score": confidence,
            "communication_score": random.randint(50, 95),
            "technical_score": random.randint(40, 96),
            "body_language_score": random.randint(55, 95),
            "overall_score": min(100, int((confidence + random.randint(40, 95)) / 2)),
            "duration_min": random.randint(15, 45),
            "feedback": random.choice([
                "Strong fundamentals, polish answers around system design.",
                "Confident communication. Brush up on dynamic programming.",
                "Good problem decomposition. Pace your answers.",
                "Excellent clarity. Add more business-impact framing.",
                "Solid technical depth. Practice STAR format for behavioral.",
            ]),
            "conducted_at": (now - timedelta(days=random.randint(0, 50))).isoformat(),
        })

    # -- Applications (student â†’ job pipeline) --
    open_jobs = [j for j in docs["jobs"] if j["status"] != "closed"]
    for s in random.sample(student_pool, k=min(380, len(student_pool))):
        for j in random.sample(open_jobs, k=random.randint(1, 4)):
            stage = random.choice(["Applied", "Applied", "Shortlisted", "Interview", "Interview", "Selected", "Rejected"])
            docs["applications"].append({
                "application_id": f"app_{uuid.uuid4().hex[:10]}",
                "student_id": s["student_id"],
                "student_name": s["name"],
                "roll_number": s["roll_number"],
                "institution_id": s["institution_id"],
                "department": s["department"],
                "job_id": j["job_id"],
                "company": j["company"],
                "job_title": j["title"],
                "ctc_lpa": j["ctc_lpa"],
                "stage": stage,
                "applied_at": (now - timedelta(days=random.randint(1, 60))).isoformat(),
                "next_step_at": (now + timedelta(days=random.randint(1, 14))).isoformat() if stage in ("Shortlisted", "Interview") else None,
            })

    # -- Departments (link inst â†’ dept docs) --
    for inst in INSTITUTIONS:
        for d in inst["departments"]:
            docs["departments"].append({
                "department_id": f"dept_{inst['institution_id']}_{d.replace(' ', '_').replace('-', '_').lower()}",
                "institution_id": inst["institution_id"],
                "name": d,
                "stream": inst["type"],
                "hod_name": _name(),
                "student_count": sum(1 for s in student_pool if s["institution_id"] == inst["institution_id"] and s["department"] == d),
                "placed_count": sum(1 for s in student_pool if s["institution_id"] == inst["institution_id"] and s["department"] == d and s["placement"]["placed"]),
            })

    # -- Training programs / cohorts --
    for inst in INSTITUTIONS:
        for prog in PROGRAMS:
            if prog["stream"] in ("All", inst["type"], "Engineering" if inst["type"] == "Engineering" else "Management"):
                enrolled = random.randint(60, 200)
                seats_purchased = enrolled + random.randint(20, 80)
                budget_allocation = seats_purchased * 3500
                budget_spent = enrolled * 3500
                docs["training_programs"].append({
                    "cohort_id": f"ch_{inst['institution_id']}_{prog['code']}",
                    "institution_id": inst["institution_id"],
                    "program_code": prog["code"],
                    "program_name": prog["name"],
                    "batch_label": "2025-26 Cohort",
                    "start_date": (now - timedelta(days=120)).isoformat(),
                    "end_date": (now + timedelta(weeks=prog["duration_weeks"])).isoformat(),
                    "modules_total": prog["modules"],
                    "enrolled_count": enrolled,
                    "completion_pct": round(random.uniform(40, 92), 1),
                    "instructor": _name(),
                    "seats_purchased": seats_purchased,
                    "seats_used": enrolled,
                    "seats_remaining": seats_purchased - enrolled,
                    "budget_allocation": budget_allocation,
                    "budget_spent": budget_spent,
                })

    # -- Enrollments (per student) --
    for s in student_pool[:380]:
        for prog in random.sample(PROGRAMS, k=random.randint(2, 3)):
            mods_done = random.randint(0, prog["modules"])
            docs["enrollments"].append({
                "enrollment_id": f"en_{uuid.uuid4().hex[:10]}",
                "student_id": s["student_id"],
                "institution_id": s["institution_id"],
                "program_code": prog["code"],
                "program_name": prog["name"],
                "modules_total": prog["modules"],
                "modules_completed": mods_done,
                "completion_pct": round(mods_done / prog["modules"] * 100, 1),
                "status": "completed" if mods_done == prog["modules"] else ("in_progress" if mods_done > 0 else "enrolled"),
                "enrolled_at": (now - timedelta(days=random.randint(20, 200))).isoformat(),
            })

    # -- Announcements --
    announcements_seed = [
        ("Amazon SDE drive â€” Feb 14", "Tier-1 hiring drive open for CSE / IT / CSE-AIML 2025 batch. Eligibility 7.5 CGPA. Apply by 10 Feb.", "tpo", "drive"),
        ("DSA Olympiad â€” Jan 28", "Curriculum-based intra-institute competition. Top 10 win Goldman mentorship.", "tpo", "training"),
        ("Mock interview clinic â€” every Friday", "Faculty-led mock interview slots open for 4th year. Book via student portal.", "faculty", "training"),
        ("Salesforce Trailhead Quest", "Earn 5+ badges to be auto-shortlisted for Salesforce drive.", "tpo", "drive"),
        ("Faculty FDP â€” AI in Pharma", "Two-week FDP starting 5 Feb, JNTUH approved.", "institution_admin", "fdp"),
        ("Placement reports Q3 ready", "Department-wise Q3 placement summary published â€” TPO portal.", "tpo", "report"),
        ("Resume ATS scoring open", "Upload your resume to get an instant ATS score before Goldman drive.", "tpo", "training"),
    ]
    for t, m, by_role, kind in announcements_seed:
        docs["announcements"].append({
            "announcement_id": f"ann_{uuid.uuid4().hex[:10]}",
            "institution_id": "inst_kmit",
            "title": t,
            "body": m,
            "kind": kind,
            "by_role": by_role,
            "pinned": kind in ("drive", "report"),
            "created_at": (now - timedelta(days=random.randint(0, 14))).isoformat(),
        })

    # -- MOU & comm log (KMIT) --
    docs["mous"].append({
        "mou_id": "mou_kmit",
        "institution_id": "inst_kmit",
        "partnership_type": "External Placement Partner + CRT + FDP",
        "signed_on": (now - timedelta(days=510)).isoformat(),
        "expires_on": (now + timedelta(days=220)).isoformat(),
        "document_name": "Skill-Tank-KMIT-MOU-2024.pdf",
        "document_size_kb": 842,
        "seats_purchased": 240,
        "seats_used": 187,
        "revenue_share_pct": 18.0,
        "accrued_share_inr": 1_842_000,
        "payout_status": "Quarterly Â· Next: 28 Feb 2026",
        "status": "active",
    })
    docs["comm_log"].extend([
        {"log_id": f"cl_{uuid.uuid4().hex[:8]}", "institution_id": "inst_kmit", "type": "meeting",
         "subject": "Q3 placement strategy review",
         "summary": "Discussed Amazon mass hiring drive, FDP scheduling for Feb cohort.",
         "by": "Ananya Reddy (Skill Tank AM)", "at": (now - timedelta(days=4)).isoformat()},
        {"log_id": f"cl_{uuid.uuid4().hex[:8]}", "institution_id": "inst_kmit", "type": "note",
         "subject": "Renewal discussion initiated",
         "summary": "TPO requested revised seat allocation for 2026-27 batch.",
         "by": "Dr. Neil Gogte (TPO)", "at": (now - timedelta(days=11)).isoformat()},
    ])

    # -- MOUs, comm logs, and revenue share for new institutions --
    for inst in INSTITUTIONS:
        if inst["institution_id"] == "inst_kmit":
            continue
        
        # MOU
        mou_id = f"mou_{inst['short_name'].lower()}"
        docs["mous"].append({
            "mou_id": mou_id,
            "institution_id": inst["institution_id"],
            "partnership_type": "CRT + FDP",
            "signed_on": (now - timedelta(days=200)).isoformat(),
            "expires_on": (now + timedelta(days=165)).isoformat(),
            "document_name": f"Skill-Tank-{inst['short_name']}-MOU.pdf",
            "document_size_kb": 512,
            "seats_purchased": 120,
            "seats_used": random.randint(45, 95),
            "revenue_share_pct": 15.0,
            "accrued_share_inr": random.randint(250_000, 950_000),
            "payout_status": "Quarterly",
            "status": "active",
        })

        # Comm log
        docs["comm_log"].extend([
            {
                "log_id": f"cl_{uuid.uuid4().hex[:8]}",
                "institution_id": inst["institution_id"],
                "type": "meeting",
                "subject": "Initial onboarding alignment",
                "summary": "Completed portal walkthrough and user training for faculty.",
                "by": "Ananya Reddy (Skill Tank AM)",
                "at": (now - timedelta(days=25)).isoformat()
            },
            {
                "log_id": f"cl_{uuid.uuid4().hex[:8]}",
                "institution_id": inst["institution_id"],
                "type": "note",
                "subject": "FDP interest discussion",
                "summary": "Faculty expressed interest in advanced AI/ML FDP workshops.",
                "by": "TPO Coordinator",
                "at": (now - timedelta(days=10)).isoformat()
            }
        ])

        # Revenue share records
        for i in range(1, 4):
            docs["revenue_share"].append({
                "revenue_id": f"rev_{uuid.uuid4().hex[:10]}",
                "institution_id": inst["institution_id"],
                "amount_inr": float(random.randint(50_000, 150_000)),
                "period": f"Q{i} 2025",
                "type": "CRT Share" if i % 2 == 0 else "FDP Program",
                "date": (now - timedelta(days=i * 90)).isoformat()
            })

    return docs
