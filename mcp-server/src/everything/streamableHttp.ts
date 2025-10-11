import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { InMemoryEventStore } from '@modelcontextprotocol/sdk/examples/shared/inMemoryEventStore.js';
import express, { Request, Response } from "express";
import { createServer } from "./everything.js";
import { randomUUID } from 'node:crypto';
import cors from 'cors';

import * as fs from 'fs/promises';
import * as path from 'path';
import { fileURLToPath } from 'url';

// At the top of your file (if using ES modules)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.error('Starting Streamable HTTP server...');

const app = express();
app.use(cors({
    "origin": "*", // use "*" with caution in production
    "methods": "GET,POST,DELETE",
    "preflightContinue": false,
    "optionsSuccessStatus": 204,
    "exposedHeaders": [
        'mcp-session-id',
        'last-event-id',
        'mcp-protocol-version'
    ]
})); // Enable CORS for all routes so Inspector can connect

const transports: Map<string, StreamableHTTPServerTransport> = new Map<string, StreamableHTTPServerTransport>();

app.post('/mcp', async (req: Request, res: Response) => {
  console.error('Received MCP POST request');
  try {
    // Check for existing session ID
    const sessionId = req.headers['mcp-session-id'] as string | undefined;

    let transport: StreamableHTTPServerTransport;

    if (sessionId && transports.has(sessionId)) {
      // Reuse existing transport
      transport = transports.get(sessionId)!;
    } else if (!sessionId) {

      const { server, cleanup, startNotificationIntervals } = createServer();

      // New initialization request
      const eventStore = new InMemoryEventStore();
      transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: () => randomUUID(),
        eventStore, // Enable resumability
        onsessioninitialized: (sessionId: string) => {
          // Store the transport by session ID when session is initialized
          // This avoids race conditions where requests might come in before the session is stored
          console.error(`Session initialized with ID: ${sessionId}`);
          transports.set(sessionId, transport);
        }
      });


      // Set up onclose handler to clean up transport when closed
      server.onclose = async () => {
        const sid = transport.sessionId;
        if (sid && transports.has(sid)) {
          console.error(`Transport closed for session ${sid}, removing from transports map`);
          transports.delete(sid);
          await cleanup();
        }
      };

      // Connect the transport to the MCP server BEFORE handling the request
      // so responses can flow back through the same transport
      await server.connect(transport);

      await transport.handleRequest(req, res);

      // Wait until initialize is complete and transport will have a sessionId
      startNotificationIntervals(transport.sessionId);

        return; // Already handled
    } else {
      // Invalid request - no session ID or not initialization request
      res.status(400).json({
        jsonrpc: '2.0',
        error: {
          code: -32000,
          message: 'Bad Request: No valid session ID provided',
        },
        id: req?.body?.id,
      });
      return;
    }

    // Handle the request with existing transport - no need to reconnect
    // The existing transport is already connected to the server
    await transport.handleRequest(req, res);
  } catch (error) {
    console.error('Error handling MCP request:', error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: '2.0',
        error: {
          code: -32603,
          message: 'Internal server error',
        },
        id: req?.body?.id,
      });
      return;
    }
  }
});

// Handle GET requests for SSE streams (using built-in support from StreamableHTTP)
app.get('/mcp', async (req: Request, res: Response) => {
  console.error('Received MCP GET request');
  const sessionId = req.headers['mcp-session-id'] as string | undefined;
  if (!sessionId || !transports.has(sessionId)) {
    res.status(400).json({
      jsonrpc: '2.0',
      error: {
        code: -32000,
        message: 'Bad Request: No valid session ID provided',
      },
      id: req?.body?.id,
    });
    return;
  }

  // Check for Last-Event-ID header for resumability
  const lastEventId = req.headers['last-event-id'] as string | undefined;
  if (lastEventId) {
    console.error(`Client reconnecting with Last-Event-ID: ${lastEventId}`);
  } else {
    console.error(`Establishing new SSE stream for session ${sessionId}`);
  }

  const transport = transports.get(sessionId);
  await transport!.handleRequest(req, res);
});

// Handle DELETE requests for session termination (according to MCP spec)
app.delete('/mcp', async (req: Request, res: Response) => {
  const sessionId = req.headers['mcp-session-id'] as string | undefined;
  if (!sessionId || !transports.has(sessionId)) {
    res.status(400).json({
      jsonrpc: '2.0',
      error: {
        code: -32000,
        message: 'Bad Request: No valid session ID provided',
      },
      id: req?.body?.id,
    });
    return;
  }

  console.error(`Received session termination request for session ${sessionId}`);

  try {
    const transport = transports.get(sessionId);
    await transport!.handleRequest(req, res);
  } catch (error) {
    console.error('Error handling session termination:', error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: '2.0',
        error: {
          code: -32603,
          message: 'Error handling session termination',
        },
        id: req?.body?.id,
      });
      return;
    }
  }
});

app.get('', async (req: Request, res:Response) => {

});
// Add this route handler
app.get('/sidenotes', async (req: Request, res: Response) => {
  try {
    const sidenotesDir = path.join(__dirname, 'sidenotes');
    
    // Check if sidenotes directory exists
    try {
      await fs.access(sidenotesDir);
    } catch {
      // Directory doesn't exist, return empty page
      res.send(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Sidenotes</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            p { color: #666; }
          </style>
        </head>
        <body>
          <h1>Sidenotes</h1>
          <p>No sidenotes found yet.</p>
        </body>
        </html>
      `);
    }

    // Read all files in the sidenotes directory
    const files = await fs.readdir(sidenotesDir);
    const sidenoteFiles = files.filter(f => f.startsWith('sidenote-') && f.endsWith('.txt'));

    // Read and parse all sidenotes
    const sidenotes = await Promise.all(
      sidenoteFiles.map(async (filename) => {
        const filepath = path.join(sidenotesDir, filename);
        const content = await fs.readFile(filepath, 'utf-8');
        
        // Extract timestamp from filename: sidenote-2025-01-15T10-30-45-123Z.txt
        const timestampMatch = filename.match(/sidenote-(.+)\.txt$/);
        const timestamp = timestampMatch 
          ? timestampMatch[1].replace(/-/g, (match, offset, string) => {
              // Replace hyphens back to colons and dots for time portion
              const beforeT = string.indexOf('T');
              if (offset > beforeT) {
                const char = string[offset - 1];
                if (!isNaN(parseInt(char))) {
                  return offset === beforeT + 3 || offset === beforeT + 6 ? ':' : 
                         offset === beforeT + 9 ? '.' : '-';
                }
              }
              return '-';
            })
          : 'Unknown';

        return {
          filename,
          timestamp,
          content,
          date: new Date(timestamp),
        };
      })
    );

    // Sort by timestamp (newest first)
    sidenotes.sort((a, b) => b.date.getTime() - a.date.getTime());

    // Generate HTML table
    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Sidenotes</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
          }
          h1 {
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-top: 20px;
          }
          th {
            background-color: #4CAF50;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
          }
          td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
          }
          tr:hover {
            background-color: #f9f9f9;
          }
          .timestamp {
            white-space: nowrap;
            font-family: monospace;
            color: #666;
          }
          .content {
            max-width: 600px;
            word-wrap: break-word;
            white-space: pre-wrap;
          }
          .filename {
            font-size: 0.9em;
            color: #999;
          }
          .count {
            color: #666;
            margin-top: 10px;
          }
        </style>
      </head>
      <body>
        <h1>Sidenotes</h1>
        <p class="count">Total sidenotes: ${sidenotes.length}</p>
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Content</th>
              <th>Filename</th>
            </tr>
          </thead>
          <tbody>
            ${sidenotes.map(note => `
              <tr>
                <td class="timestamp">${note.date.toLocaleString()}</td>
                <td class="content">${escapeHtml(note.content)}</td>
                <td class="filename">${escapeHtml(note.filename)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </body>
      </html>
    `;

    res.send(html);
  } catch (err:unknown) {
    console.error('Error reading sidenotes:', err);
    const error = err as Error;
    res.status(500).send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Error</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          .error { color: red; }
        </style>
      </head>
      <body>
        <h1 class="error">Error</h1>
        <p>Failed to load sidenotes: ${escapeHtml(error.message)}</p>
      </body>
      </html>
    `);
  }
});
// Helper function to escape HTML
function escapeHtml(text: string): string {
  const map: { [key: string]: string } = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}
// Start the server
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.error(`MCP Streamable HTTP Server listening on port ${PORT}`);
});

// Handle server shutdown
process.on('SIGINT', async () => {
  console.error('Shutting down server...');

  // Close all active transports to properly clean up resources
  for (const sessionId in transports) {
    try {
      console.error(`Closing transport for session ${sessionId}`);
      await transports.get(sessionId)!.close();
      transports.delete(sessionId);
    } catch (error) {
      console.error(`Error closing transport for session ${sessionId}:`, error);
    }
  }

  console.error('Server shutdown complete');
  process.exit(0);
});


