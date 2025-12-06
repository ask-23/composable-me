#!/usr/bin/env node
/**
 * Sync Kiro Specs to Linear
 * 
 * Parses requirements from .kiro/specs/{feature}/requirements.md and creates
 * corresponding Linear stories in the configured project.
 * 
 * Usage:
 *   node scripts/sync-kiro-to-linear.js [--dry-run] [--feature <name>]
 * 
 * Configuration:
 *   Reads from .kiro/linear-project.json for project/team settings
 *   See .kiro/steering/linear-sync.md for full documentation
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

// Configuration
const KIRO_DIR = path.join(process.cwd(), '.kiro');
const SPECS_DIR = path.join(KIRO_DIR, 'specs');
const CONFIG_FILE = path.join(KIRO_DIR, 'linear-project.json');

// Parse command line arguments
const args = process.argv.slice(2);
const DRY_RUN = args.includes('--dry-run');
const featureIndex = args.indexOf('--feature');
const FEATURE_FILTER = featureIndex !== -1 ? args[featureIndex + 1] : null;

// Get Linear API key from environment
const LINEAR_API_KEY = process.env.LINEAR_API_KEY;

/**
 * Load project configuration (graceful if missing)
 */
function loadConfig() {
  if (!fs.existsSync(CONFIG_FILE)) {
    console.log('ℹ️  No Linear configuration found.');
    console.log('');
    console.log('To set up Linear sync:');
    console.log('  1. Copy .kiro/linear-project.json.example to .kiro/linear-project.json');
    console.log('  2. Fill in your Linear project and team IDs');
    console.log('  3. Run this script again');
    console.log('');
    console.log('See .kiro/steering/linear-sync.md for details.');
    return null;
  }
  return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
}

/**
 * Parse requirements from a requirements.md file
 */
function parseRequirements(content, featureName) {
  const requirements = [];
  const reqRegex = /### Requirement (\d+)\s*\n\n\*\*User Story:\*\*\s*(.+?)(?=\n\n####|\n\n### Requirement|\n\n##|$)/gs;
  
  let match;
  while ((match = reqRegex.exec(content)) !== null) {
    const reqNum = match[1];
    const userStory = match[2].trim();
    // Extract summary from user story
    const wantMatch = userStory.match(/I want (?:to )?(.+?)(?:,\s*so that|$)/i);
    const summary = wantMatch 
      ? wantMatch[1].trim().replace(/\.$/, '')
      : userStory.split(',')[0].trim();
    
    requirements.push({
      number: parseInt(reqNum),
      userStory,
      summary: summary.charAt(0).toUpperCase() + summary.slice(1),
      feature: featureName
    });
  }
  return requirements;
}

/**
 * Get display name for a feature from config or derive from directory name
 */
function getFeatureDisplayName(featureDir, config) {
  if (config.featureMapping && config.featureMapping[featureDir]) {
    return config.featureMapping[featureDir];
  }
  // Convert kebab-case to Title Case
  return featureDir.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

/**
 * Generate canonical title for a requirement
 */
function generateTitle(feature, reqNum, summary) {
  return `${feature} – Req ${reqNum}: ${summary}`;
}

/**
 * Make a GraphQL request to Linear API
 */
function linearRequest(query, variables = {}) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({ query, variables });
    
    const options = {
      hostname: 'api.linear.app',
      path: '/graphql',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': LINEAR_API_KEY,
        'Content-Length': Buffer.byteLength(data)
      }
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          const result = JSON.parse(body);
          if (result.errors) {
            reject(new Error(result.errors[0].message));
          } else {
            resolve(result.data);
          }
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

/**
 * Search for existing issues by title prefix
 */
async function findExistingIssues(projectId, titlePrefix) {
  const query = `
    query SearchIssues($filter: IssueFilter) {
      issues(filter: $filter, first: 100) {
        nodes { id title }
      }
    }
  `;
  
  const result = await linearRequest(query, {
    filter: {
      project: { id: { eq: projectId } },
      title: { contains: titlePrefix }
    }
  });
  
  return result.issues.nodes;
}

/**
 * Create a new Linear issue
 */
async function createIssue(teamId, projectId, title, description) {
  const mutation = `
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue { id identifier title }
      }
    }
  `;
  
  const result = await linearRequest(mutation, {
    input: { teamId, projectId, title, description }
  });

  return result.issueCreate;
}

/**
 * Main sync function
 */
async function main() {
  console.log('🔄 Kiro → Linear Sync');
  console.log('='.repeat(50));

  if (DRY_RUN) {
    console.log('🏃 DRY RUN MODE - No changes will be made\n');
  }

  // Graceful handling of missing API key
  if (!LINEAR_API_KEY) {
    console.log('ℹ️  LINEAR_API_KEY not set.');
    console.log('');
    console.log('To sync to Linear:');
    console.log('  export LINEAR_API_KEY=lin_api_xxx');
    console.log('  npm run sync:linear');
    console.log('');
    console.log('Get your API key from Linear Settings → API → Personal API Keys');
    return;
  }

  // Graceful handling of missing config
  const config = loadConfig();
  if (!config) return;

  console.log(`📁 Project: ${config.projectName}`);
  console.log(`🔗 Project ID: ${config.projectId}\n`);

  // Check if specs directory exists
  if (!fs.existsSync(SPECS_DIR)) {
    console.log('ℹ️  No specs directory found (.kiro/specs/)');
    console.log('   Create feature specs to sync them to Linear.');
    return;
  }

  // Find all feature specs
  const features = fs.readdirSync(SPECS_DIR).filter(f => {
    const stat = fs.statSync(path.join(SPECS_DIR, f));
    return stat.isDirectory() && (!FEATURE_FILTER || f === FEATURE_FILTER);
  });

  if (features.length === 0) {
    console.log('ℹ️  No feature specs found.');
    if (FEATURE_FILTER) {
      console.log(`   Feature "${FEATURE_FILTER}" not found in .kiro/specs/`);
    }
    return;
  }

  let totalFound = 0, totalCreated = 0, totalSkipped = 0, totalErrors = 0;

  for (const featureDir of features) {
    const reqFile = path.join(SPECS_DIR, featureDir, 'requirements.md');
    if (!fs.existsSync(reqFile)) continue;

    const featureName = getFeatureDisplayName(featureDir, config);
    console.log(`\n📋 Feature: ${featureName}`);
    console.log('-'.repeat(40));

    const content = fs.readFileSync(reqFile, 'utf8');
    const requirements = parseRequirements(content, featureName);
    totalFound += requirements.length;

    if (requirements.length === 0) {
      console.log('   No requirements found in this spec.');
      continue;
    }

    console.log(`   Found ${requirements.length} requirements`);

    for (const req of requirements) {
      const title = generateTitle(featureName, req.number, req.summary);
      const titlePrefix = `${featureName} – Req ${req.number}:`;

      // Check for existing issue
      const existing = await findExistingIssues(config.projectId, titlePrefix);
      const exists = existing.some(i => i.title.startsWith(titlePrefix));

      if (exists) {
        console.log(`   ⏭️  Req ${req.number}: Already exists`);
        totalSkipped++;
        continue;
      }

      const description = `**User Story:** ${req.userStory}\n\n---\n_Synced from Kiro spec: .kiro/specs/${featureDir}/requirements.md_`;

      if (DRY_RUN) {
        console.log(`   🆕 Req ${req.number}: Would create "${title}"`);
        totalCreated++;
      } else {
        try {
          const result = await createIssue(config.teamId, config.projectId, title, description);
          if (result.success) {
            console.log(`   ✅ Req ${req.number}: Created ${result.issue.identifier}`);
            totalCreated++;
          } else {
            console.log(`   ❌ Req ${req.number}: Failed to create`);
            totalErrors++;
          }
        } catch (err) {
          console.log(`   ❌ Req ${req.number}: ${err.message}`);
          totalErrors++;
        }
      }
    }
  }

  // Summary
  console.log('\n' + '='.repeat(50));
  console.log('📊 Summary');
  console.log(`   Requirements found: ${totalFound}`);
  console.log(`   Stories created: ${totalCreated}`);
  console.log(`   Stories skipped: ${totalSkipped}`);
  if (totalErrors > 0) console.log(`   Errors: ${totalErrors}`);
  if (DRY_RUN) console.log('\n🏃 This was a dry run. Run without --dry-run to create stories.');
}

// Run
main().catch(err => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});

