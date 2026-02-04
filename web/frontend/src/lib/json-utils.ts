import type { RoleEntry } from "./csv-utils";

const DEFAULT_ROLE: RoleEntry = {
    company: "Unknown",
    role: "Unknown Role",
    location: "",
    employmentType: "",
    salary: "Not specified",
    description: "",
};

function normalizeEntry(raw: Record<string, unknown>): RoleEntry {
    const company = String(raw.company ?? raw.employer ?? DEFAULT_ROLE.company).trim();
    const role = String(raw.title ?? raw.role ?? raw.position ?? DEFAULT_ROLE.role).trim();
    const location = String(raw.location ?? "").trim();
    const employmentType = String(raw.employmentType ?? raw.employment_type ?? raw.workMode ?? "").trim();
    const salary = String(raw.salaryRange ?? raw.salary ?? raw.compensation ?? DEFAULT_ROLE.salary).trim();
    const description = String(raw.description ?? raw.jd_text ?? "").trim();
    const url = String(raw.link ?? raw.url ?? "").trim();
    const source = String(raw.source ?? "").trim();

    return {
        company: company || DEFAULT_ROLE.company,
        role: role || DEFAULT_ROLE.role,
        location,
        employmentType,
        salary: salary || DEFAULT_ROLE.salary,
        description,
        url: url || undefined,
        source: source || undefined,
    };
}

export function parseJobFeedJSON(content: string): RoleEntry[] {
    const parsed = JSON.parse(content);
    const items: Record<string, unknown>[] = Array.isArray(parsed)
        ? parsed
        : Array.isArray(parsed.jobs)
        ? parsed.jobs
        : Array.isArray(parsed.items)
        ? parsed.items
        : [];

    return items
        .map((item) => normalizeEntry(item))
        .filter((entry) => entry.company !== "Unknown" || entry.role !== "Unknown Role");
}
