# Requirements Document

## Introduction

Job Discovery is an automated job search and filtering system that finds relevant job opportunities based on user preferences and presents a curated shortlist for review. The system integrates with the Composable Crew workflow, allowing users to approve opportunities and automatically trigger the application generation process.

## Glossary

- **Job Discovery Agent**: Agent that searches job boards and aggregates opportunities
- **Filter Criteria**: User-defined preferences for job search (seniority, location, tech stack, compensation)
- **Job Board**: External platform where jobs are posted (LinkedIn, Indeed, etc.)
- **Shortlist**: Curated list of job opportunities that match user criteria
- **Auto-Reject Criteria**: Filters that automatically exclude jobs (contract-to-hire, relocation required, etc.)
- **Job Metadata**: Structured data about a job (company, role, compensation, requirements, posting date)
- **Composable Crew**: The downstream system that generates tailored applications
- **Discovery Session**: A single execution of the job search process
- **Saved Search**: Persistent filter criteria that can be reused

## Requirements

### Requirement 1

**User Story:** As a job seeker, I want to define my job search criteria once, so that the system can find relevant opportunities automatically.

#### Acceptance Criteria

1. WHEN a user first runs the system THEN the Job Discovery Agent SHALL prompt for search criteria (role titles, seniority level, location preferences, tech stack, compensation range)
2. WHEN criteria are provided THEN the system SHALL save them as a reusable search profile
3. WHEN the user updates criteria THEN the system SHALL persist the changes for future searches
4. WHEN multiple search profiles exist THEN the system SHALL allow the user to select which profile to use
5. WHEN a search profile is selected THEN the system SHALL display the active criteria before executing the search

### Requirement 2

**User Story:** As a job seeker, I want the system to search multiple job boards, so that I don't miss opportunities posted on different platforms.

#### Acceptance Criteria

1. WHEN a discovery session starts THEN the Job Discovery Agent SHALL search LinkedIn, Indeed, and other configured job boards
2. WHEN searching job boards THEN the system SHALL apply the user's filter criteria to each platform
3. WHEN job board APIs are available THEN the system SHALL use official APIs with proper authentication
4. WHEN APIs are unavailable THEN the system SHALL use web scraping with rate limiting and respectful delays
5. WHEN a job board is unreachable THEN the system SHALL continue with other sources and report the failure

### Requirement 3

**User Story:** As a job seeker, I want the system to filter out jobs that don't meet my requirements, so that I only see relevant opportunities.

#### Acceptance Criteria

1. WHEN jobs are retrieved THEN the system SHALL apply auto-reject criteria (contract-to-hire, below specified seniority, no remote option when required, relocation required)
2. WHEN filtering by tech stack THEN the system SHALL match required technologies against user preferences
3. WHEN filtering by compensation THEN the system SHALL exclude jobs below the user's minimum threshold
4. WHEN filtering by location THEN the system SHALL respect remote/hybrid/onsite preferences
5. WHEN a job matches all criteria THEN the system SHALL include it in the shortlist

### Requirement 4

**User Story:** As a job seeker, I want to see a curated shortlist of opportunities, so that I can quickly review and approve the best matches.

#### Acceptance Criteria

1. WHEN filtering is complete THEN the system SHALL rank jobs by fit score (match percentage based on criteria)
2. WHEN ranking is complete THEN the system SHALL present the top 10-20 opportunities in the shortlist
3. WHEN displaying the shortlist THEN the system SHALL show company name, role title, location, compensation range, and fit score
4. WHEN displaying each job THEN the system SHALL include a brief summary of why it matched
5. WHEN the shortlist is empty THEN the system SHALL suggest relaxing filter criteria

### Requirement 5

**User Story:** As a job seeker, I want to approve jobs from the shortlist, so that the system can generate tailored applications automatically.

#### Acceptance Criteria

1. WHEN the shortlist is presented THEN the system SHALL allow the user to approve, reject, or save jobs for later
2. WHEN a user approves a job THEN the system SHALL fetch the full job description
3. WHEN the full job description is retrieved THEN the system SHALL pass it to the Composable Crew workflow
4. WHEN the Composable Crew workflow completes THEN the system SHALL mark the job as processed
5. WHEN a user rejects a job THEN the system SHALL exclude similar jobs in future searches

### Requirement 6

**User Story:** As a job seeker, I want the system to avoid showing me duplicate jobs, so that I don't waste time reviewing the same opportunity twice.

#### Acceptance Criteria

1. WHEN jobs are retrieved THEN the system SHALL deduplicate by company name and role title
2. WHEN a job has been previously shown THEN the system SHALL exclude it from the current shortlist
3. WHEN a job has been previously rejected THEN the system SHALL exclude it from future searches
4. WHEN a job has been previously approved THEN the system SHALL mark it as already processed
5. WHEN deduplication is uncertain THEN the system SHALL flag potential duplicates for user review

### Requirement 7

**User Story:** As a job seeker, I want the system to respect rate limits and terms of service, so that my account doesn't get blocked.

#### Acceptance Criteria

1. WHEN scraping job boards THEN the system SHALL implement rate limiting (maximum 1 request per 2 seconds per domain)
2. WHEN using APIs THEN the system SHALL respect API rate limits and retry with exponential backoff
3. WHEN a rate limit is hit THEN the system SHALL pause and resume after the required delay
4. WHEN scraping THEN the system SHALL include a user-agent string identifying the tool
5. WHEN terms of service prohibit scraping THEN the system SHALL use official APIs only

### Requirement 8

**User Story:** As a job seeker, I want the system to extract structured data from job postings, so that filtering and ranking are accurate.

#### Acceptance Criteria

1. WHEN a job posting is retrieved THEN the system SHALL extract company name, role title, location, and posting date
2. WHEN compensation information is present THEN the system SHALL extract salary range or hourly rate
3. WHEN job requirements are listed THEN the system SHALL extract required technologies, years of experience, and education
4. WHEN extraction fails THEN the system SHALL flag the job for manual review
5. WHEN structured data is extracted THEN the system SHALL validate it against expected formats

### Requirement 9

**User Story:** As a job seeker, I want the system to run searches on a schedule, so that I'm notified of new opportunities without manual intervention.

#### Acceptance Criteria

1. WHEN a user enables scheduled searches THEN the system SHALL run discovery sessions at the specified interval (daily, weekly)
2. WHEN a scheduled search completes THEN the system SHALL notify the user of new opportunities via email or console output
3. WHEN new jobs are found THEN the system SHALL add them to the shortlist for review
4. WHEN no new jobs are found THEN the system SHALL log the result without sending a notification
5. WHEN a scheduled search fails THEN the system SHALL retry once and report the error if it persists

### Requirement 10

**User Story:** As a job seeker, I want to see why a job was included or excluded, so that I can refine my search criteria.

#### Acceptance Criteria

1. WHEN a job is included in the shortlist THEN the system SHALL display which criteria it matched
2. WHEN a job is excluded THEN the system SHALL log the reason (which filter it failed)
3. WHEN the user requests details THEN the system SHALL show the full filtering decision tree
4. WHEN criteria are too restrictive THEN the system SHALL suggest which filters to relax
5. WHEN criteria are too broad THEN the system SHALL suggest additional filters to narrow results

### Requirement 11

**User Story:** As a job seeker, I want the system to learn from my preferences, so that future searches are more accurate.

#### Acceptance Criteria

1. WHEN a user approves a job THEN the system SHALL record which attributes made it appealing
2. WHEN a user rejects a job THEN the system SHALL record which attributes made it unappealing
3. WHEN sufficient feedback is collected THEN the system SHALL adjust fit scoring to prioritize preferred attributes
4. WHEN ranking jobs THEN the system SHALL apply learned preferences to boost or penalize scores
5. WHEN preferences conflict with explicit criteria THEN the system SHALL prioritize explicit criteria

### Requirement 12

**User Story:** As a job seeker, I want to export the shortlist, so that I can review it offline or share it with others.

#### Acceptance Criteria

1. WHEN the shortlist is generated THEN the system SHALL offer to export it as JSON, CSV, or Markdown
2. WHEN exporting THEN the system SHALL include all job metadata and fit scores
3. WHEN exporting THEN the system SHALL include links to original job postings
4. WHEN exporting THEN the system SHALL include timestamps and search criteria used
5. WHEN the export is complete THEN the system SHALL save the file to a specified location

### Requirement 13

**User Story:** As a developer, I want to configure job board integrations, so that I can add or remove sources easily.

#### Acceptance Criteria

1. WHEN the system initializes THEN the system SHALL read job board configurations from a config file
2. WHEN a new job board is added THEN the system SHALL validate the configuration (API keys, endpoints, rate limits)
3. WHEN a job board is disabled THEN the system SHALL skip it during discovery sessions
4. WHEN API credentials are missing THEN the system SHALL report which job boards cannot be accessed
5. WHEN configuration changes THEN the system SHALL reload without requiring a restart

### Requirement 14

**User Story:** As a developer, I want the system to log all discovery activities, so that I can debug issues and monitor performance.

#### Acceptance Criteria

1. WHEN a discovery session starts THEN the system SHALL log the search criteria and job boards being queried
2. WHEN jobs are retrieved THEN the system SHALL log the count from each source
3. WHEN filtering occurs THEN the system SHALL log how many jobs passed each filter
4. WHEN errors occur THEN the system SHALL log the error, source, and attempted resolution
5. WHEN a session completes THEN the system SHALL log the total jobs found, filtered, and shortlisted

### Requirement 15

**User Story:** As a job seeker, I want the system to integrate seamlessly with Composable Crew, so that approved jobs automatically trigger application generation.

#### Acceptance Criteria

1. WHEN a user approves a job from the shortlist THEN the system SHALL pass the job description to Composable Crew
2. WHEN passing to Composable Crew THEN the system SHALL include the user's resume and any saved interview notes
3. WHEN Composable Crew completes THEN the system SHALL receive the generated application materials
4. WHEN application materials are ready THEN the system SHALL notify the user and provide the output
5. WHEN Composable Crew fails THEN the system SHALL report the error and allow the user to retry or skip
