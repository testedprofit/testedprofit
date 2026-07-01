const PINATA_FILE_ENDPOINT = "https://api.pinata.cloud/pinning/pinFileToIPFS";
const TURNSTILE_VERIFY_ENDPOINT = "https://challenges.cloudflare.com/turnstile/v0/siteverify";
const DEFAULT_MAX_UPLOAD_BYTES = 25 * 1024 * 1024;
const ALLOWED_MEDIA_TYPES = [
  "image/gif",
  "image/jpeg",
  "image/png",
  "image/svg+xml",
  "image/webp",
  "video/mp4",
  "video/ogg",
  "video/quicktime",
  "video/webm"
];

function json(data, status, extraHeaders) {
  return new Response(JSON.stringify(data), {
    status: status || 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...(extraHeaders || {})
    }
  });
}

function allowedOrigins(env) {
  return String(env.ALLOWED_ORIGINS || "")
    .split(",")
    .map((origin) => origin.trim())
    .filter(Boolean);
}

function corsHeaders(request, env) {
  const origin = request.headers.get("origin") || "";
  const allowlist = allowedOrigins(env);
  const allowOrigin = allowlist.includes(origin) ? origin : allowlist[0] || "";
  return {
    ...(allowOrigin ? { "access-control-allow-origin": allowOrigin } : {}),
    "access-control-allow-methods": "GET,POST,OPTIONS",
    "access-control-allow-headers": "content-type,x-algoflow-upload-token",
    "access-control-max-age": "86400",
    vary: "origin"
  };
}

function isOriginAllowed(request, env) {
  const origin = request.headers.get("origin");
  const allowlist = allowedOrigins(env);
  if (!allowlist.length) return true;
  if (!origin) return false;
  return allowlist.includes(origin);
}

function maxUploadBytes(env) {
  const configured = Number(env.MAX_UPLOAD_BYTES || "");
  return Number.isFinite(configured) && configured > 0 ? configured : DEFAULT_MAX_UPLOAD_BYTES;
}

function safeName(value) {
  return String(value || "algoflow-nft")
    .replace(/[^\w.\- ]+/g, "")
    .trim()
    .slice(0, 80) || "algoflow-nft";
}

function isLikelyJwt(value) {
  return typeof value === "string" && value.trim().split(".").length >= 3 && value.trim().length > 40;
}

function isAcceptedContentType(type, kind) {
  if (kind === "metadata") return type === "application/json" || type === "text/json" || type === "";
  if (kind === "media") return ALLOWED_MEDIA_TYPES.includes(type);
  return false;
}

async function verifyTurnstileIfConfigured(request, env, token) {
  if (!env.TURNSTILE_SECRET_KEY) return;
  if (!token) throw new Error("turnstile_required");

  const form = new FormData();
  form.append("secret", env.TURNSTILE_SECRET_KEY);
  form.append("response", token);
  const ip = request.headers.get("cf-connecting-ip");
  if (ip) form.append("remoteip", ip);

  const response = await fetch(TURNSTILE_VERIFY_ENDPOINT, { method: "POST", body: form });
  if (!response.ok) throw new Error("turnstile_unavailable");
  const result = await response.json();
  if (!result || result.success !== true) throw new Error("turnstile_failed");
}

async function pinToPinata(file, pinName, env) {
  if (!isLikelyJwt(env.PINATA_JWT)) throw new Error("pinata_not_configured");

  const form = new FormData();
  form.append("file", file, safeName(pinName || file.name));
  form.append("pinataMetadata", JSON.stringify({ name: safeName(pinName || file.name) }));
  form.append("pinataOptions", JSON.stringify({ cidVersion: 1 }));

  const response = await fetch(PINATA_FILE_ENDPOINT, {
    method: "POST",
    headers: { authorization: `Bearer ${env.PINATA_JWT}` },
    body: form
  });

  if (!response.ok) throw new Error("pinata_upload_failed");
  const result = await response.json();
  if (!result || !result.IpfsHash) throw new Error("pinata_missing_cid");
  return result.IpfsHash;
}

async function handlePin(request, env) {
  if (!isOriginAllowed(request, env)) {
    return json({ ok: false, error: "origin_not_allowed" }, 403, corsHeaders(request, env));
  }

  const contentLength = Number(request.headers.get("content-length") || "0");
  const limit = maxUploadBytes(env);
  if (contentLength && contentLength > limit) {
    return json({ ok: false, error: "upload_too_large", maxBytes: limit }, 413, corsHeaders(request, env));
  }

  let form;
  try {
    form = await request.formData();
  } catch (_) {
    return json({ ok: false, error: "invalid_form_data" }, 400, corsHeaders(request, env));
  }

  const file = form.get("file");
  const kind = String(form.get("kind") || "").toLowerCase();
  const name = safeName(form.get("name") || (file && file.name));
  const turnstileToken = String(form.get("turnstileToken") || "");

  if (!(file instanceof File)) {
    return json({ ok: false, error: "file_required" }, 400, corsHeaders(request, env));
  }
  if (!["media", "metadata"].includes(kind)) {
    return json({ ok: false, error: "kind_required" }, 400, corsHeaders(request, env));
  }
  if (file.size <= 0) {
    return json({ ok: false, error: "empty_file" }, 400, corsHeaders(request, env));
  }
  if (file.size > limit) {
    return json({ ok: false, error: "upload_too_large", maxBytes: limit }, 413, corsHeaders(request, env));
  }
  if (!isAcceptedContentType(file.type, kind)) {
    return json({ ok: false, error: "unsupported_content_type" }, 415, corsHeaders(request, env));
  }

  try {
    await verifyTurnstileIfConfigured(request, env, turnstileToken);
    const cid = await pinToPinata(file, name, env);
    return json({
      ok: true,
      cid,
      uri: `ipfs://${cid}`,
      kind,
      bytes: file.size,
      contentType: file.type || (kind === "metadata" ? "application/json" : "application/octet-stream")
    }, 200, corsHeaders(request, env));
  } catch (error) {
    const safeError = error instanceof Error ? error.message : "upload_failed";
    const status = safeError === "turnstile_required" || safeError === "turnstile_failed" ? 403 : 502;
    return json({ ok: false, error: safeError }, status, corsHeaders(request, env));
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const cors = corsHeaders(request, env);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }

    if (request.method === "GET" && url.pathname === "/health") {
      return json({ ok: true, service: "algoflow-nft-ipfs-broker" }, 200, cors);
    }

    if (request.method === "POST" && (url.pathname === "/pin" || url.pathname === "/api/nft/pin")) {
      return handlePin(request, env);
    }

    return json({ ok: false, error: "not_found" }, 404, cors);
  }
};
