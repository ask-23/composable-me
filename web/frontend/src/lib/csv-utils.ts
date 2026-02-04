export type RoleEntry = {
    company: string;
    role: string;
    location: string;
    employmentType: string;
    salary: string;
    description: string;
    url?: string;
    source?: string;
};

const DEFAULT_ROLE: RoleEntry = {
    company: "Unknown",
    role: "Unknown Role",
    location: "",
    employmentType: "",
    salary: "Not specified",
    description: "",
};

function splitCsvLine(line: string): string[] {
    const result: string[] = [];
    let current = "";
    let inQuotes = false;

    for (let i = 0; i < line.length; i += 1) {
        const char = line[i];

        if (char === '"') {
            if (inQuotes && line[i + 1] === '"') {
                current += '"';
                i += 1;
            } else {
                inQuotes = !inQuotes;
            }
            continue;
        }

        if (char === "," && !inQuotes) {
            result.push(current.trim());
            current = "";
            continue;
        }

        current += char;
    }

    result.push(current.trim());
    return result;
}

function normalizeHeader(header: string): string {
    return header.toLowerCase().replace(/[^a-z0-9]+/g, "");
}

const HEADER_MAP: Record<string, keyof RoleEntry> = {
    company: "company",
    employer: "company",
    role: "role",
    title: "role",
    position: "role",
    location: "location",
    city: "location",
    state: "location",
    employmenttype: "employmentType",
    workmode: "employmentType",
    type: "employmentType",
    salary: "salary",
    salaryrange: "salary",
    compensation: "salary",
    description: "description",
    jd: "description",
    jobdescription: "description",
    url: "url",
    link: "url",
    source: "source",
};

export function parseRoleCSV(content: string): RoleEntry[] {
    const lines = content.split(/\r?\n/).filter((line) => line.trim().length > 0);
    if (lines.length === 0) {
        return [];
    }

    const headers = splitCsvLine(lines[0]).map(normalizeHeader);
    const headerKeys = headers.map((header) => HEADER_MAP[header]);

    const roles: RoleEntry[] = [];

    for (const line of lines.slice(1)) {
        const values = splitCsvLine(line);
        const entry: RoleEntry = { ...DEFAULT_ROLE };

        values.forEach((value, index) => {
            const key = headerKeys[index];
            if (!key) {
                return;
            }
            const trimmed = value.trim();
            if (trimmed.length === 0) {
                return;
            }
            if (key === "company" || key === "role") {
                (entry[key] as string) = trimmed;
            } else if (key === "employmentType") {
                entry.employmentType = trimmed;
            } else if (key === "salary") {
                entry.salary = trimmed;
            } else if (key === "description") {
                entry.description = trimmed;
            } else if (key === "location") {
                entry.location = trimmed;
            } else if (key === "url") {
                entry.url = trimmed;
            } else if (key === "source") {
                entry.source = trimmed;
            }
        });

        if (entry.company !== DEFAULT_ROLE.company || entry.role !== DEFAULT_ROLE.role) {
            roles.push(entry);
        }
    }

    return roles;
}

export function roleToJobDescription(role: RoleEntry): string {
    const lines: string[] = [
        `Company: ${role.company}`,
        `Role: ${role.role}`,
    ];

    if (role.location) {
        lines.push(`Location: ${role.location}`);
    }

    if (role.employmentType) {
        lines.push(`Employment Type: ${role.employmentType}`);
    }

    if (role.salary && role.salary !== "Not specified") {
        lines.push(`Compensation: ${role.salary}`);
    }

    if (role.source) {
        lines.push(`Source: ${role.source}`);
    }

    if (role.url) {
        lines.push(`URL: ${role.url}`);
    }

    if (role.description) {
        lines.push("", "Description:", role.description);
    }

    return lines.join("\n");
}
