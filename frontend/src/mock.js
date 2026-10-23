export const navLinks = [
  {
    label: "Product",
    hasDropdown: true,
    items: [
      { title: "Student OS", desc: "DSA, aptitude, ATS, interviews, and applications" },
      { title: "Institution Intelligence", desc: "Department health, forecasts, and reports" },
      { title: "Recruiter Intelligence", desc: "Talent discovery and shortlist workflows" },
      { title: "Readiness Engine", desc: "Dynamic placement readiness scoring" },
    ],
  },
  {
    label: "Workspaces",
    hasDropdown: true,
    items: [
      { title: "TPO Command Center", desc: "Drive pipeline and placement mission control" },
      { title: "Faculty Studio", desc: "Weak student detection and coaching analytics" },
      { title: "Student Workspace", desc: "Practice, test, interview, and apply" },
      { title: "Recruiter Console", desc: "Find the next best candidate" },
    ],
  },
  {
    label: "Resources",
    hasDropdown: true,
    items: [
      { title: "Placement Reports", desc: "Board-ready exports and analytics" },
      { title: "DSA Intelligence", desc: "Question-level Striver A2Z tracking" },
      { title: "ATS Intelligence", desc: "Resume versions, keyword gaps, role fit" },
    ],
  },
  { label: "Customers", hasDropdown: false },
  { label: "Pricing", hasDropdown: false },
];

export const trustLogos = [
  { name: "KMIT", migrated: "Placement intelligence live" },
  { name: "Vasavi", migrated: "Department health tracked" },
  { name: "Google", migrated: "Recruiter pipeline connected" },
  { name: "Amazon", migrated: "Talent readiness matched" },
  { name: "Microsoft", migrated: "Interview scheduling ready" },
  { name: "Adobe", migrated: "ATS fit and skills mapped" },
  { name: "DE Shaw", migrated: "High-signal talent pool" },
  { name: "Deloitte", migrated: "Applications lifecycle tracked" },
];

export const signals = [
  "Rahul completed 7 DSA problems today",
  "CSE batch aptitude speed dropped 12%",
  "Google drive has 289 applied students",
  "ATS keyword gap detected for cloud role",
  "MOU renewal due in 18 days",
  "Faculty comment added on Dynamic Programming",
  "Recruiter shortlisted 24 high-fit profiles",
  "Interview confidence improved by 16 points",
  "Amazon role requires Python and system design",
  "Training attendance below threshold in ECE",
  "Aptitude revision due for Blood Relations",
  "Resume version 3 improved ATS by 11%",
  "Student readiness crossed 80",
  "Placement forecast changed for IT department",
  "Mock interview recording saved",
  "New board report generated",
  "Revenue share payout pending approval",
  "Weak topic cluster found in Graphs",
  "Recruiter conversion increased this week",
  "Drive deadline closes tomorrow",
  "Student applied to 3 matching roles",
  "Faculty batch comparison updated",
  "TPO broadcast delivered to all students",
  "Interview panel calendar synced",
  "DSA mastery improved in Arrays",
  "Aptitude accuracy rose to 74%",
  "Institution health score recalculated",
  "Final year risk queue updated",
  "ATS heatmap found missing keywords",
  "Offer trend exceeded last year",
  "Report export ready for board review",
  "Recruiter saved a new talent filter",
  "Communication score improved in mock interview",
  "Application moved to interview stage",
  "Training program completion crossed 90%",
  "Student consistency streak reached 14 days",
  "Department placement rate forecast updated",
  "High package opportunity opened",
  "Faculty review requested for 12 students",
];

export const pillars = [
  {
    eyebrow: "Student Preparation",
    title: "Practice, test, interview, and apply",
    desc: "CareerOS gives students a complete preparation loop across DSA, aptitude, ATS resumes, interviews, applications, and learning roadmaps.",
    tile: "blush",
  },
  {
    eyebrow: "Placement Operations",
    title: "Run every drive from one command center",
    desc: "TPOs can monitor recruiter drives, student eligibility, interview schedules, applications, offers, forecasts, and reports in one place.",
    tile: "mint",
  },
  {
    eyebrow: "Institution Intelligence",
    title: "Know department health before it becomes risk",
    desc: "Institution admins see batch readiness, training ROI, placement forecasts, MOU status, revenue context, and board-ready reports.",
    tile: "yellow",
  },
  {
    eyebrow: "Recruiter Matching",
    title: "Find the right student faster",
    desc: "Recruiters can discover talent by skill, readiness, ATS fit, CGPA, interview score, and role compatibility.",
    tile: "lilac",
  },
];

export const personas = [
  {
    key: "sellers",
    title: "Students",
    heading: "Your personal placement operating system",
    link: "Explore student workspace",
    points: [
      { h: "Prepare without leaving the platform", p: "Solve DSA, take timed aptitude tests, improve resumes, and complete mock interviews from one workspace." },
      { h: "Know exactly what to improve next", p: "Readiness is calculated from real activity, not hardcoded cards or generic dashboard metrics." },
    ],
  },
  {
    key: "leaders",
    title: "TPOs",
    heading: "Placement mission control for every drive",
    link: "Explore TPO console",
    points: [
      { h: "Forecast outcomes earlier", p: "Track offers, packages, department health, recruiter conversions, and student risk before drives close." },
      { h: "Replace manual reports", p: "Generate analytics exports and board reports directly from live placement data." },
    ],
  },
  {
    key: "founders",
    title: "Faculty",
    heading: "Coach the students who need you most",
    link: "Explore faculty studio",
    points: [
      { h: "Detect weak students", p: "See topic-level DSA and aptitude gaps, consistency problems, interview weaknesses, and revision due lists." },
      { h: "Close learning gaps faster", p: "Leave comments, compare batches, and track progress from practice to mastery." },
    ],
  },
  {
    key: "revops",
    title: "Institutions",
    heading: "A live intelligence layer for campus leadership",
    link: "Explore institution intelligence",
    points: [
      { h: "Understand institutional health", p: "Placement rates, training completion, MOU status, reports, and forecasts are connected." },
      { h: "Audit every decision", p: "Actions, approvals, broadcasts, reports, and pipeline movements create a traceable operating history." },
    ],
  },
  {
    key: "marketers",
    title: "Recruiters",
    heading: "Interview the best-fit students next",
    link: "Explore recruiter console",
    points: [
      { h: "Search with intelligence", p: "Filter talent by readiness, skills, department, ATS match, interview signals, and hiring intent." },
      { h: "Move candidates with clarity", p: "Shortlists, interview schedules, application stages, and conversion analytics stay in one workflow." },
    ],
  },
];

// Numbers describe the bundled demonstration dataset only. They are deliberately not
// phrased as customer outcomes, because no customer data exists yet.
export const customerStats = [
  { metric: "702", label: "offers in demo data", company: "Sample dataset" },
  { metric: "148", label: "recruiter names", company: "Sample dataset" },
  { metric: "474", label: "DSA problems tracked", company: "Curriculum catalog" },
  { metric: "80L", label: "highest demo package", company: "Sample dataset" },
  { metric: "5,450", label: "student profiles", company: "Sample dataset" },
  { metric: "13", label: "intelligence modules", company: "This build" },
];

export const featuredTestimonials = [
  {
    quote: "CareerOS turns placement data into decisions. We can see readiness, risk, and recruiter movement before the final week panic begins.",
    name: "Placement Officer",
    role: "Training and Placement Cell",
    company: "Engineering Institution",
  },
  {
    quote: "The student workspace finally connects practice to outcomes. DSA, aptitude, ATS, and mock interviews feel like one preparation system.",
    name: "Final Year Student",
    role: "CSE",
    company: "CareerOS Student OS",
  },
  {
    quote: "Instead of asking for spreadsheets, I can shortlist students by the signals that matter for the role.",
    name: "Recruiter Partner",
    role: "Talent Acquisition",
    company: "Hiring Network",
  },
];

export const heroQuote = {
  quote: "CareerOS shows what spreadsheets never could: who is ready, who is at risk, and which action should happen next.",
  name: "Placement Leader",
  role: "Director, Campus Placements",
  company: "CareerOS",
};

export const duoQuote = {
  quote: "Every morning the platform surfaces student risks, recruiter movement, expiring MOUs, and the next highest-value action for our team.",
  name: "TPO Team",
  role: "Placement Operations",
  company: "CareerOS",
};

export const cabifyQuote = {
  quote: "We moved from disconnected files and status calls to one operating layer for training, readiness, recruiters, applications, and reports.",
  name: "Institution Admin",
  role: "Placement Intelligence",
  company: "CareerOS",
};

export const blogPosts = [
  { tag: "Product", date: "June 20, 2026", title: "How CareerOS turns student preparation into placement intelligence", color: "#ffd7f0" },
  { tag: "Reports", date: "June 18, 2026", title: "Board-ready placement reports without spreadsheet cleanup", color: "#e2ddfd" },
  { tag: "Recruiters", date: "June 16, 2026", title: "Building candidate shortlists from readiness and skill signals", color: "#b7efb2" },
  { tag: "Training", date: "June 12, 2026", title: "Why topic-level aptitude and DSA tracking changes placement outcomes", color: "#ffef99" },
];

export const wallOfLove = [
  { name: "Akhil Reddy", role: "Student, CSE", text: "The readiness score makes preparation less confusing. I know whether to work on DSA, aptitude, ATS, or interviews next." },
  { name: "Priya Sharma", role: "Faculty Mentor", text: "Question-level DSA progress and aptitude weak topics help us coach students with much more precision." },
  { name: "Rohit Menon", role: "TPO", text: "Applications, recruiters, schedules, and reports finally live in one placement workflow." },
  { name: "Sneha Rao", role: "Institution Admin", text: "The product gives leadership a live view of placement health instead of waiting for monthly spreadsheet reports." },
  { name: "Karthik Jain", role: "Recruiter", text: "The talent pool helps me identify students who actually match the role before interviews start." },
  { name: "Nisha Kapoor", role: "Student, IT", text: "Mock interviews and ATS version history made the platform feel like a real preparation operating system." },
];

export const footerCols = [
  { title: "Product", links: ["Student OS", "TPO Command Center", "Faculty Studio", "Recruiter Console", "Reports Engine", "Readiness Engine"] },
  { title: "Modules", links: ["DSA Intelligence", "Aptitude Intelligence", "ATS Intelligence", "Interview Intelligence", "Placement Intelligence"] },
  { title: "Workflows", links: ["Applications", "Interview Scheduler", "Broadcasts", "MOU Tracking", "Audit Logs", "Exports"] },
  { title: "Company", links: ["About", "Contact", "Security", "Privacy", "Terms", "Status"] },
];
