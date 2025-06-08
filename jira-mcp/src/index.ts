import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import JiraClient from 'jira-client';
import { z } from 'zod';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config();
try {
  dotenv.config({ path: path.resolve(__dirname, '../.env') });
} catch (e) {
  console.error("Error loading .env file:", e);
  // Ignore errors
}

const app = express();
app.use(cors());
app.use(express.json());

const port = process.env.PORT || 5001;

// Setup Jira client
const jiraConfig = {
  protocol: process.env.JIRA_PROTOCOL || "https",
  host: process.env.JIRA_HOST || "jira.corp.adobe.com",
  username: process.env.JIRA_USERNAME || "",
  password: process.env.JIRA_PASSWORD || "",
  apiVersion: process.env.JIRA_API_VERSION || "2",
  strictSSL: process.env.JIRA_STRICT_SSL !== "false",
};
const jira = new JiraClient(jiraConfig);

// Helper to validate env
function validateJiraConfig() {
  if (!jiraConfig.host) return "JIRA_HOST not set";
  if (!jiraConfig.username) return "JIRA_USERNAME not set";
  if (!jiraConfig.password) return "JIRA_PASSWORD not set";
  return null;
}

// Route: Get issue description
app.get("/jira/:issueId/description", async (req, res) => {
  const issueKey = req.params.issueId;
  console.log('Got description request for issueKey:', issueKey);
  const configError = validateJiraConfig();
  if (configError) return res.status(500).json({ error: configError });

  try {
    const issue = await jira.findIssue(issueKey);
    if (!issue) return res.status(404).json({ error: "Issue not found" });

    const description = issue.fields.description || "No description";
    const summary = issue.fields.summary || "No summary";
    const status = issue.fields.status?.name || "Unknown";
    const issueType = issue.fields.issuetype?.name || "Unknown";
    console.log('Response sending for description request for issueKey:', issueKey);
    return res.json({
      issueKey,
      summary,
      type: issueType,
      status,
      description,
    });
  } catch (err) {
    console.error("Jira error:", err);
    return res.status(500).json({ error: err.message });
  }
});

// Route: Get issue comments
app.get("/jira/:issueId/comments", async (req, res) => {
  const issueKey = req.params.issueId;
  console.log('Got comments request for issueKey:', issueKey);
  const configError = validateJiraConfig();
  if (configError) return res.status(500).json({ error: configError });

  try {
    const comments = await jira.getComments(issueKey);
    if (!comments?.comments?.length)
      return res.json({ comments: [] });

    const formatted = comments.comments.map(c => ({
      author: c.author?.displayName || "Unknown",
      created: c.created,
      body: c.body || "",
    }));
    console.log('Response sending for comments request for issueKey:', issueKey);
    return res.json({ comments: formatted });
  } catch (err) {
    console.error("Jira comments error:", err);
    return res.status(500).json({ error: err.message });
  }
});

// Start server
app.listen(port, () => {
  console.log(`JIRA MCP HTTP server running at http://localhost:${port}`);
});
