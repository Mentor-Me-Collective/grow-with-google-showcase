const { setGlobalOptions } = require("firebase-functions");
const { onRequest } = require("firebase-functions/https");
const logger = require("firebase-functions/logger");
const { initializeApp } = require("firebase-admin/app");
const { getAuth } = require("firebase-admin/auth");
const {
  getFirestore,
  FieldValue,
} = require("firebase-admin/firestore");

initializeApp();

setGlobalOptions({
  maxInstances: 10,
  region: "us-central1",
});

const db = getFirestore();

function setCors(response) {
  response.set("Access-Control-Allow-Origin", "*");
  response.set(
    "Access-Control-Allow-Headers",
    "Content-Type, Authorization"
  );
  response.set(
    "Access-Control-Allow-Methods",
    "GET, POST, PATCH, OPTIONS"
  );
}

function sendJson(response, status, body) {
  return response.status(status).json(body);
}

function cleanString(value) {
  return typeof value === "string" ? value.trim() : "";
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validateContactBody(body) {
  const name = cleanString(body?.name);
  const email = cleanString(body?.email);
  const reason = cleanString(body?.reason);
  const message = cleanString(body?.message);

  const errors = {};

  if (!name || name.length > 120) {
    errors.name = "Enter a valid name.";
  }

  if (!email || email.length > 254 || !isValidEmail(email)) {
    errors.email = "Enter a valid email address.";
  }

  if (!reason || reason.length > 120) {
    errors.reason = "Select a valid contact reason.";
  }

  if (!message || message.length > 5000) {
    errors.message = "Enter a message between 1 and 5000 characters.";
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors,
    data: {
      name,
      email,
      reason,
      message,
    },
  };
}

async function requireAdmin(request) {
  const authorization = request.get("Authorization") || "";

  if (!authorization.startsWith("Bearer ")) {
    return null;
  }

  const idToken = authorization.slice(7).trim();

  if (!idToken) {
    return null;
  }

  const decodedToken = await getAuth().verifyIdToken(idToken);

  const userSnapshot = await db
    .collection("users")
    .doc(decodedToken.uid)
    .get();

  if (!userSnapshot.exists) {
    return null;
  }

  const profile = userSnapshot.data();

  if (
    profile.role !== "admin" ||
    profile.accountStatus !== "active"
  ) {
    return null;
  }

  return {
    uid: decodedToken.uid,
    profile,
  };
}

async function createContactMessage(request, response) {
  const validation = validateContactBody(request.body);

  if (!validation.valid) {
    return sendJson(response, 400, {
      ok: false,
      error: "validation_error",
      fields: validation.errors,
    });
  }

  const now = FieldValue.serverTimestamp();

  const messageRef = await db.collection("contactMessages").add({
    ...validation.data,
    status: "unread",
    createdAt: now,
    updatedAt: now,
  });

  return sendJson(response, 201, {
    ok: true,
    message: "Your message has been received.",
    id: messageRef.id,
  });
}

async function getContactMessages(request, response) {
  const admin = await requireAdmin(request);

  if (!admin) {
    return sendJson(response, 403, {
      ok: false,
      error: "forbidden",
    });
  }

  const snapshot = await db
    .collection("contactMessages")
    .orderBy("createdAt", "desc")
    .limit(100)
    .get();

  const messages = snapshot.docs.map((doc) => ({
    id: doc.id,
    ...doc.data(),
  }));

  return sendJson(response, 200, {
    ok: true,
    messages,
  });
}

async function updateContactMessage(request, response, messageId) {
  const admin = await requireAdmin(request);

  if (!admin) {
    return sendJson(response, 403, {
      ok: false,
      error: "forbidden",
    });
  }

  const status = cleanString(request.body?.status);

  if (!["read", "resolved"].includes(status)) {
    return sendJson(response, 400, {
      ok: false,
      error: "invalid_status",
    });
  }

  const messageRef = db.collection("contactMessages").doc(messageId);
  const snapshot = await messageRef.get();

  if (!snapshot.exists) {
    return sendJson(response, 404, {
      ok: false,
      error: "not_found",
    });
  }

  await messageRef.update({
    status,
    updatedAt: FieldValue.serverTimestamp(),
  });

  return sendJson(response, 200, {
    ok: true,
    id: messageId,
    status,
  });
}

exports.api = onRequest(async (request, response) => {
  setCors(response);

  if (request.method === "OPTIONS") {
    return response.status(204).send("");
  }

  try {
    const path = request.path.replace(/\/+$/, "") || "/";

    if (
      request.method === "POST" &&
      path === "/contact"
    ) {
      return await createContactMessage(request, response);
    }

    if (
      request.method === "GET" &&
      path === "/admin/contact-messages"
    ) {
      return await getContactMessages(request, response);
    }

    const adminMessageMatch = path.match(
      /^\/admin\/contact-messages\/([^/]+)$/
    );

    if (
      request.method === "PATCH" &&
      adminMessageMatch
    ) {
      return await updateContactMessage(
        request,
        response,
        decodeURIComponent(adminMessageMatch[1])
      );
    }

    return sendJson(response, 404, {
      ok: false,
      error: "not_found",
    });
  } catch (error) {
    logger.error("Contact API request failed", error);

    return sendJson(response, 500, {
      ok: false,
      error: "server_error",
      message: "We could not complete that request right now.",
    });
  }
});
