/**
 * Astromorty Discord Interactions Cloudflare Worker
 *
 * This worker handles Discord HTTP interactions (slash commands, buttons, modals)
 * received via the Interactions Endpoint URL. It verifies request signatures and
 * either forwards interactions to the bot's backend API or handles them directly.
 */

import {
  InteractionResponseType,
  InteractionType,
  verifyKey,
} from "discord-interactions";

/**
 * Environment variables available to the worker
 */
interface Env {
  // Required: Discord application public key (Ed25519 hex)
  DISCORD_PUBLIC_KEY: string;

  // Optional: URL to forward interactions to bot backend
  // If not set, worker handles interactions directly (limited functionality)
  BOT_API_URL?: string;

  // Optional: KV namespace for storing interaction state
  // INTERACTION_STATE?: KVNamespace;
}

/**
 * Handle Discord interaction HTTP requests
 */
async function handleInteraction(
  request: Request,
  env: Env,
): Promise<Response> {
  // Only handle POST requests
  if (request.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  // Verify Discord signature
  const signature = request.headers.get("X-Signature-Ed25519");
  const timestamp = request.headers.get("X-Signature-Timestamp");

  if (!signature || !timestamp) {
    return new Response("Missing signature headers", { status: 401 });
  }

  // Clone request to read body without consuming it
  const body = await request.clone().arrayBuffer();

  // Verify signature
  const isValidRequest = verifyKey(
    body,
    signature,
    timestamp,
    env.DISCORD_PUBLIC_KEY,
  );

  if (!isValidRequest) {
    return new Response("Invalid signature", { status: 401 });
  }

  // Parse interaction payload
  const interaction = await request.json();

  // Handle PING (type 1) - Discord uses this to validate the endpoint
  if (interaction.type === InteractionType.PING) {
    return new Response(
      JSON.stringify({ type: InteractionResponseType.PONG }),
      {
        headers: { "Content-Type": "application/json" },
      },
    );
  }

  // Handle other interaction types
  // Option 1: Forward to bot backend API
  if (env.BOT_API_URL) {
    return forwardToBackend(request, env.BOT_API_URL, interaction);
  }

  // Option 2: Handle directly in worker (limited functionality)
  return handleDirectly(interaction);
}

/**
 * Forward interaction to bot backend API
 */
async function forwardToBackend(
  originalRequest: Request,
  backendUrl: string,
  interaction: any,
): Promise<Response> {
  try {
    // Get the original request body (already parsed, need to stringify)
    const body = JSON.stringify(interaction);

    // Forward the interaction to the bot's backend
    // The backend will verify signatures again, so we forward the headers
    const response = await fetch(`${backendUrl}/interactions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Forward signature headers for backend verification
        "X-Signature-Ed25519": originalRequest.headers.get(
          "X-Signature-Ed25519",
        ) || "",
        "X-Signature-Timestamp": originalRequest.headers.get(
          "X-Signature-Timestamp",
        ) || "",
        // Forward user agent for identification
        "User-Agent": originalRequest.headers.get("User-Agent") || "Cloudflare-Worker",
      },
      body: body,
    });

    // Return the backend's response
    // If backend returns an error, pass it through
    if (!response.ok) {
      console.error(
        `Backend returned error: ${response.status} ${response.statusText}`,
      );
    }

    return response;
  } catch (error) {
    console.error("Error forwarding to backend:", error);
    return new Response(
      JSON.stringify({
        type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        data: {
          content: "❌ Error connecting to bot backend",
          flags: 64, // EPHEMERAL
        },
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      },
    );
  }
}

/**
 * Handle interaction directly in worker (limited functionality)
 * This is a fallback when BOT_API_URL is not configured.
 */
function handleDirectly(interaction: any): Response {
  const interactionType = interaction.type;

  // Application command (slash command)
  if (interactionType === InteractionType.APPLICATION_COMMAND) {
    const commandName = interaction.data?.name;

    // Return deferred response - commands would need to be handled elsewhere
    return new Response(
      JSON.stringify({
        type: InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
      }),
      {
        headers: { "Content-Type": "application/json" },
      },
    );
  }

  // Message component (button, select menu)
  if (interactionType === InteractionType.MESSAGE_COMPONENT) {
    const customId = interaction.data?.custom_id;

    // Return deferred update
    return new Response(
      JSON.stringify({
        type: InteractionResponseType.DEFERRED_UPDATE_MESSAGE,
      }),
      {
        headers: { "Content-Type": "application/json" },
      },
    );
  }

  // Modal submit
  if (interactionType === InteractionType.MODAL_SUBMIT) {
    const customId = interaction.data?.custom_id;

    // Return deferred response
    return new Response(
      JSON.stringify({
        type: InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
        data: {
          flags: 64, // EPHEMERAL
        },
      }),
      {
        headers: { "Content-Type": "application/json" },
      },
    );
  }

  // Autocomplete
  if (interactionType === InteractionType.APPLICATION_COMMAND_AUTOCOMPLETE) {
    // Return empty choices (would need command implementation)
    return new Response(
      JSON.stringify({
        type: InteractionResponseType.APPLICATION_COMMAND_AUTOCOMPLETE_RESULT,
        data: {
          choices: [],
        },
      }),
      {
        headers: { "Content-Type": "application/json" },
      },
    );
  }

  // Unknown interaction type
  return new Response(
    JSON.stringify({
      type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
      data: {
        content: "❌ Unknown interaction type",
        flags: 64, // EPHEMERAL
      },
    }),
    {
      headers: { "Content-Type": "application/json" },
    },
  );
}

/**
 * Main worker entry point
 */
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    try {
      return await handleInteraction(request, env);
    } catch (error) {
      console.error("Worker error:", error);
      return new Response(
        JSON.stringify({
          type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
          data: {
            content: "❌ Internal server error",
            flags: 64, // EPHEMERAL
          },
        }),
        {
          status: 500,
          headers: { "Content-Type": "application/json" },
        },
      );
    }
  },
};

