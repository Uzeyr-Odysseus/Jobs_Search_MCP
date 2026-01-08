# server.py
#------------------------------------------------------------------------------
from typing import List, Optional
from fastmcp import FastMCP
from jobspy import scrape_jobs

mcp = FastMCP(
    name="Job Search",
    instructions=(
        "Use this tool to discover recent job opportunities across major job boards. "
        "It is best suited for market research, role exploration, and job discovery "
        "based on role keywords, location, and recency."
    ),
)

@mcp.tool(
    description=(
        "Searches multiple job boards and returns recent job listings. "
        "Ideal for finding roles by title, function, or seniority within a specific "
        "location and time window."
    )
)
def scrape_jobs_tool(
    Boards: List[str] = [
    "Indeed",
    "LinkedIn",
    "Google",
    #"Glassdoor",
    #"ZipRecruiter",
    #"Bayt",
    #"Bdjobs",
    #"Naukri",
    ],
    RoleKeywords: Optional[str] = None,
    Location: Optional[str] = None,
    ResultCount: int = 20,
    PostedWithinDays: int = 7,
    Country: Optional[str] = None,
    # Country field is required when using Indeed. Must be a full country name (e.g. “united arab emirates”, not “uae”).
):
    """
    Parameters
    ----------
    Boards:
        Job boards to search. Options include Indeed, LinkedIn and Google (This looks up on multiple other platforms e.g., Glasdoor)

    RoleKeywords:
        Keywords describing the role, such as a job title or function
        (e.g. "Product Manager", "Backend Engineer").

    Location:
        City, region, or country where the job is located (e.g., "Hanoi", "Qatar", "Birmingham")

    ResultCount:
        Maximum number of job listings to return.

    PostedWithinDays:
        Only return jobs posted within this many days.

    Country:
        Country name required when searching Indeed
        (e.g. "Vietnam", "Qatar", "Pakistan"). Only "US" & "UK" supported as codes, rest require full names
    """

    # Normalize boards for JobSpy
    site_name = [b.lower() for b in Boards]

    # Convert days → hours (internal implementation detail)
    hours_old = PostedWithinDays * 24

    # Generate Google-style query if needed
    google_search_term = None
    if "google" in site_name and RoleKeywords:
        google_search_term = f"{RoleKeywords} jobs"
        if Location:
            google_search_term += f" in {Location}"

    scrape_kwargs = dict(
        site_name=site_name,
        search_term=RoleKeywords,
        google_search_term=google_search_term,
        location=Location,
        results_wanted=ResultCount,
        hours_old=hours_old,
    )

    if "indeed" in site_name:
        if not Country:
            raise ValueError(
                "Country is required when using Indeed. "
                "Examples: 'us', 'de', 'pk', 'uk'."
            )
        scrape_kwargs["country_indeed"] = Country.lower()

    jobs = scrape_jobs(**scrape_kwargs)


    results = []

    for _, row in jobs.iterrows():
        salary = (
            f"{row['min_amount']}–{row['max_amount']} {row['currency']} ({row['interval']})"
            if row["min_amount"] and row["max_amount"]
            else None
        )

        results.append({
            "Title": row["title"],
            "Company": row["company"],
            "Location": row["location"],
            "PostedDate": str(row["date_posted"]),
            "JobType": row["job_type"],
            "ExperienceRange": row["experience_range"],
            "Remote": row["is_remote"],
            "Salary": salary,
            "Board": row["site"],
            "JobURL": row["job_url"],
            "CompanyURL": row["company_url"],
        })

    return {
        "Count": len(results),
        "Jobs": results
    }

app = mcp.http_app(transport="streamable-http")
