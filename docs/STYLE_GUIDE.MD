# STYLE_GUIDE.MD — Anti-AI Language & Human Voice Standards

## Purpose

This guide ensures all Composable Me outputs:
1. Sound human-written
2. Pass AI detection tools
3. Reflect senior engineering voice
4. Avoid cliché corporate language

---

## The AI Detection Problem

AI detectors look for:
- Predictable sentence structures
- Overuse of certain phrases
- Unnatural consistency
- Perfect grammar throughout
- Robotic rhythm

We counter by deliberately introducing human patterns.

---

## Forbidden Patterns

### Phrases (Never Use)

```
BANNED:
- "proven track record"
- "passionate about"
- "leverage my expertise"
- "drive innovation"
- "in today's rapidly evolving"
- "best-in-class"
- "cutting-edge"
- "state-of-the-art"
- "synergy" / "synergize"
- "seamlessly"
- "spearheaded"
- "key stakeholders"
- "cross-functional collaboration"
- "robust solutions"
- "scalable architecture" (alone, without specifics)
- "dynamic environment"
- "fast-paced"
- "results-driven"
- "thought leader"
- "paradigm shift"
```

### Structures (Avoid)

```
BANNED PATTERNS:

1. Perfect Parallelism
   BAD:
   - Led the development of...
   - Led the implementation of...
   - Led the optimization of...
   
   GOOD:
   - Led development of the event pipeline
   - Built the deployment system from scratch
   - Cut response times by 60% through caching

2. Identical Openers
   BAD:
   - Responsible for managing...
   - Responsible for developing...
   - Responsible for deploying...
   
   GOOD:
   - Managed a fleet of 200 servers
   - Wrote the monitoring system in Go
   - Shipped 3x per day after rebuilding CI/CD

3. Adverb Stacking
   BAD: "Effectively and efficiently managed resources"
   GOOD: "Managed $2M AWS spend, cut 30% through right-sizing"

4. Generic Accomplishments
   BAD: "Improved system performance"
   GOOD: "Reduced API latency from 400ms to 50ms p99"
```

---

## Required Patterns

### Sentence Variation

Mix lengths deliberately:

```
EXAMPLE:
"Built the CI/CD pipeline. Took it from 45-minute deploys to 8 minutes. 
The team ships 5x more often now, and I'm not the bottleneck anymore. 
That last part was the actual goal—making myself unnecessary for deploys."

Analysis:
- Short: "Built the CI/CD pipeline."
- Medium: "Took it from 45-minute deploys to 8 minutes."
- Long: "The team ships 5x more often now..."
- Conversational: "That last part was the actual goal..."
```

### Specific Numbers

Use precise numbers, not rounded:

```
BAD:  "approximately 50 servers"
GOOD: "47 servers"

BAD:  "significantly reduced costs"
GOOD: "cut AWS bill by $340K annually"

BAD:  "improved performance"
GOOD: "dropped P99 latency from 380ms to 45ms"
```

### Active Voice Dominance

Active voice sounds more confident:

```
PASSIVE (avoid): "The migration was completed by the team"
ACTIVE (prefer): "I led the migration. We moved 200 services in 3 months."

PASSIVE: "Improvements were made to the deployment process"
ACTIVE: "Rebuilt the deployment process. Deploys now take 8 minutes, not 45."
```

### First-Person Confidence

For cover letters and recruiter replies:

```
WEAK: "I believe I would be a good fit..."
STRONG: "I've done this before. At T-Mobile, I built the system you're describing."

WEAK: "I am interested in the opportunity to..."
STRONG: "Your JD describes my last three years. Let's talk."
```

---

## Voice by Document Type

### Resume

**Register:** Crisp, dense, factual
**Style:** Action verb → what → scale → result
**Personality:** Confident but not boastful

```
EXAMPLE BULLETS:
- Architected multi-account AWS landing zone (40+ developers, 8 accounts)
- Cut deploy time from 45min to 8min; teams ship without ops approval
- Passed SOC2 audit on first attempt—auditor said cleanest startup controls they'd seen
```

### Cover Letter

**Register:** Personable but professional
**Style:** Direct, specific, connected to JD
**Personality:** Engaged human, not form letter

```
EXAMPLE OPENING:
At T-Mobile, I built the CI/CD system that let 200 developers ship 
without waiting for ops approval. Before that, deploys took days. 
After, they took minutes. 

Your JD mentions "developer velocity" three times. That's what I do.
```

### LinkedIn About

**Register:** Professional but human
**Style:** Narrative arc, perspective-driven
**Personality:** Experienced, reflective

```
EXAMPLE:
I build systems that make themselves unnecessary.

At every company, I find the bottleneck—usually it's ops. 
Teams waiting on deployments. Developers blocked on environments. 
Engineers afraid to ship on Friday.

My job is to fix that, then move on to the next constraint.

Currently: Platform engineering at [Company].
Previously: [Previous roles].
```

### Recruiter Reply

**Register:** Light, professional, selective
**Style:** Short, questions that signal standards
**Personality:** Confident, not desperate

```
EXAMPLE:
Thanks for reaching out about the Platform Lead role.

Quick questions before we go further:
- Is this W2 full-time? (I don't do CTH)
- What's the comp range?
- Remote, or do I need to be somewhere?

Happy to share more once I understand the basics.
```

---

## Human Signaling Techniques

### Technique 1: Imperfection

Allow minor imperfections that humans naturally make:

```
ROBOTIC: "I successfully implemented a comprehensive monitoring solution."
HUMAN: "Built the monitoring stack. Took a few iterations to get alerting right, 
        but now we actually trust the dashboards."
```

### Technique 2: Conversational Asides

Add occasional parentheticals:

```
ROBOTIC: "Reduced deployment time significantly."
HUMAN: "Cut deploy time by 80% (though the first version broke staging twice)."
```

### Technique 3: Contractions

Use contractions naturally:

```
ROBOTIC: "I would not recommend this approach."
HUMAN: "I wouldn't recommend that—we tried it, and it didn't scale."
```

### Technique 4: Sentence Fragments

Occasional fragments sound natural:

```
ROBOTIC: "This resulted in improved developer experience."
HUMAN: "Better developer experience. Way fewer 'waiting on ops' messages."
```

### Technique 5: Specificity Over Abstraction

Replace abstract claims with concrete details:

```
ABSTRACT: "Improved operational efficiency through automation"
CONCRETE: "Wrote scripts that turned 3-hour manual processes into 5-minute cron jobs"
```

---

## Tone Calibration by Context

### High Stakes (Resume, Cover Letter)

- Confident but grounded
- Specific and verifiable
- Senior, not junior
- No hedging ("I think," "I believe")

### Medium Stakes (LinkedIn)

- More reflective
- Can show perspective
- Slightly more casual
- Still professional

### Low Stakes (Recruiter DM)

- Direct and efficient
- Can show personality
- Clear questions
- Signal selectiveness

---

## Quality Checklist

Before finalizing any document:

```
[ ] No forbidden phrases used
[ ] Sentence lengths vary
[ ] Active voice dominant
[ ] Specific numbers, not approximations
[ ] At least one "human" element (aside, fragment, imperfection)
[ ] No perfect parallelism in bullets
[ ] Would a human actually write this?
[ ] Does it sound like the user, not a bot?
```

---

## Examples: Before and After

### Resume Bullet

```
BEFORE (AI-scented):
"Spearheaded cross-functional initiatives to implement robust, 
scalable CI/CD pipelines, resulting in significantly improved 
deployment velocity and enhanced developer experience."

AFTER (human):
"Built CI/CD from scratch. Deploy time: 45min → 8min. 
Teams ship daily now without waiting for ops approval."
```

### Cover Letter Opening

```
BEFORE:
"I am writing to express my strong interest in the Senior Platform 
Engineer position at TechCorp. With my proven track record in cloud 
infrastructure and passion for DevOps..."

AFTER:
"At my last job, developers waited 2-3 days for deploys. 
By the time I left, they shipped in 10 minutes without asking anyone. 
Your JD describes exactly that problem. Let's talk."
```

### LinkedIn Summary

```
BEFORE:
"Results-driven Platform Engineering leader with 10+ years of experience 
delivering scalable, robust cloud solutions. Proven track record of 
driving innovation and building high-performing teams."

AFTER:
"I build systems that make themselves unnecessary.

Find the bottleneck. Fix it. Move to the next one.
Usually the bottleneck is ops. Teams waiting. Developers blocked.

I fix that. Then I find the next constraint."
```
