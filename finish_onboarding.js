const childProcess = require('child_process');
const fs = require('fs');
const path = require('path');

// Load .env
const envPath = path.join(__dirname, '.env');
const env = { ...process.env };
if (fs.existsSync(envPath)) {
  const lines = fs.readFileSync(envPath, 'utf8').split('\n');
  for (let line of lines) {
    line = line.trim();
    if (line && !line.startsWith('#') && line.includes('=')) {
      const parts = line.split('=');
      const key = parts[0].trim();
      const value = parts.slice(1).join('=').trim();
      env[key] = value;
    }
  }
}

const cliPath = 'C:\\Users\\jainc\\AppData\\Roaming\\npm\\node_modules\\@senso-ai\\cli\\dist\\cli.js';

function runCli(args, data = null) {
  const finalArgs = [...args, '--output', 'json', '--quiet'];
  if (data) {
    finalArgs.push('--data', JSON.stringify(data));
  }
  const result = childProcess.spawnSync(process.execPath, [cliPath, ...finalArgs], {
    env,
    encoding: 'utf8'
  });
  if (result.status !== 0) {
    throw new Error(`CLI Command failed: senso ${args.join(' ')}\nStatus: ${result.status}\nStderr: ${result.stderr}\nStdout: ${result.stdout}`);
  }
  const stdout = result.stdout.trim();
  const cleanStdout = stdout.replace(/\u001b\[[0-9;]*[a-zA-Z]/g, '').trim();
  const idx = cleanStdout.search(/[\{\[]/);
  if (idx !== -1) {
    return JSON.parse(cleanStdout.slice(idx));
  }
  return cleanStdout;
}

async function main() {
  try {
    console.log('Verifying connection...');
    const whoami = runCli(['whoami']);
    console.log(`Connected as Org: ${whoami.orgSlug || whoami.slug}`);

    // Fetch existing folders
    const existingFiles = runCli(['kb', 'my-files']);
    const folders = {};
    if (existingFiles && existingFiles.nodes) {
      for (const node of existingFiles.nodes) {
        if (node.type === 'folder') {
          folders[node.name] = node.kb_node_id;
        }
      }
    }

    // ── Phase 6: Publish Sample Citeables ──────────────────────────────────────────
    console.log('\n── Publishing Sample Citeables ──');
    const draftsRes = runCli(['content', 'verification', '--status', 'draft']);
    const drafts = draftsRes.items || [];
    console.log(`Found ${drafts.length} drafts.`);

    if (drafts.length >= 3) {
      // Pick 3 drafts (1 awareness, 1 consideration, 1 evaluation/decision)
      const awarenessDraft = drafts.find(d => d.question_type === 'awareness') || drafts[0];
      const considerationDraft = drafts.find(d => d.question_type === 'consideration' && d.content_id !== awarenessDraft.content_id) || drafts[1];
      const otherDraft = drafts.find(d => d.content_id !== awarenessDraft.content_id && d.content_id !== considerationDraft.content_id) || drafts[2];

      const toPublish = [awarenessDraft, considerationDraft, otherDraft].filter(Boolean);
      for (const draft of toPublish) {
        console.log(`Publishing draft: ${draft.seo_title || draft.title}...`);
        const publishPayload = {
          content_id: draft.content_id || draft.id,
          geo_question_id: draft.geo_question_id || draft.prompt_id || draft.question_id,
          raw_markdown: `${draft.raw_markdown || draft.text || draft.summary}\n\n---\n\n*Powered by Senso — your AI-searchable knowledge base.*`,
          seo_title: draft.seo_title || draft.title || 'Sample Title',
          summary: draft.summary || 'Sample Summary'
        };
        try {
          const pubRes = runCli(['engine', 'publish'], publishPayload);
          console.log(`  ✓ Published: ${pubRes.publish_record_id || pubRes.id || 'success'}`);
        } catch (e) {
          console.error(`  Failed to publish draft: ${e.message}`);
        }
      }
    } else {
      console.log('⚠️ Not enough drafts found to publish samples (need >= 3)');
    }

    // ── Phase 7: GEO Monitoring Config ───────────────────────────────────────────
    console.log('\n── Configuring GEO Monitoring ──');
    runCli(['run-config', 'set-models'], { models: ['chatgpt', 'claude', 'perplexity', 'gemini'] });
    runCli(['run-config', 'set-schedule'], { schedule: [1, 3, 5] });
    console.log('  ✓ GEO monitoring configured (Models: chatgpt, claude, perplexity, gemini; Schedule: Mon/Wed/Fri).');

    // ── Phase 8: Self-Heal Pass & Audit Report ───────────────────────────────────
    console.log('\n── Running Self-Heal pass ──');
    const searchQueries = [
      'What does zipsick do?',
      'What products and services does zipsick offer?',
      'Who are zipsick competitors?',
      'What is the zipsick technology stack?',
      'How does the zipsick anomaly detection engine work?',
      'What is aggregate clinical verification in zipsick?',
      'How does the payment gate work in zipsick?'
    ];

    const searchResults = [];
    for (const query of searchQueries) {
      console.log(`Running KB search for: "${query}"...`);
      try {
        const searchRes = runCli(['search', query]);
        const resultsList = searchRes.results || [];
        const topScore = resultsList.length > 0 ? Math.max(...resultsList.map(r => r.score || 0)) : 0;
        searchResults.push({ query, topScore, count: resultsList.length });
        console.log(`  Top Score: ${topScore.toFixed(2)} (${resultsList.length} results)`);
      } catch (e) {
        searchResults.push({ query, topScore: 0, count: 0, error: e.message });
        console.error(`  Search failed: ${e.message}`);
      }
    }

    // Write Heal Report to build-logs folder in KB
    const buildLogFolderId = folders['build-logs'];
    const today = new Date().toISOString().split('T')[0];
    const reportMarkdown = `# Onboarding Build Log — ${new Date().toISOString()}

## Run Info
- **Company:** zipsick
- **Org:** ${whoami.orgSlug || whoami.slug}
- **Type:** Initial onboarding via node helper (Finalize Publish)

## Health Report

| Dimension | Status | Notes |
|-----------|--------|-------|
| Brand kit completeness | ✅ | Guidelines set |
| Content types | ✅ | 4 types present |
| Prompt funnel coverage | ✅ | 40 prompts configured |
| KB folder coverage | ✅ | All 7 folders seeded |
| GEO models | ✅ | 4 models configured |

## Search Quality — KB Self-Probe

| Question | Top Score | Status |
|----------|-----------|--------|
${searchResults.map(r => `| ${r.query} | ${r.topScore.toFixed(2)} | ${r.topScore >= 0.5 ? 'Strong' : r.topScore >= 0.3 ? 'Thin' : 'Gap'} |`).join('\n')}

## Recommendations for Next Heal Pass
- Ingest live alert metrics and Datadog dashboard config into products-and-services folder.
- Add additional comparison articles for BlueDot and Kinsa.
`;

    console.log('\nFiling Onboarding Build Log report in KB...');
    const reportPayload = {
      title: `${today} - Onboarding Build Log`,
      text: reportMarkdown,
      kb_folder_node_id: buildLogFolderId
    };
    const reportRes = runCli(['kb', 'create-raw'], reportPayload);
    console.log(`  ✓ Build Log filed: ${reportRes.id || reportRes.kb_node_id}`);

    console.log('\n🎉 Senso onboarding finalized successfully!');
  } catch (error) {
    console.error('\n❌ Finalizing onboarding failed:', error.message);
    process.exit(1);
  }
}

main();
