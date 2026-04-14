/**
 * Apple App Store Server Notifications V2 — Cloudflare Worker
 *
 * Receives POST notifications from Apple, verifies the JWS signature,
 * parses the notification type, stores events in Cloudflare KV, and
 * returns the required 200 OK acknowledge response.
 *
 * Apple docs:
 *   https://developer.apple.com/documentation/appstoreservernotifications
 */

import { verifyAppleJws, decodeInnerJws, type VerifiedPayload } from "./verify";

export interface Env {
  /** Cloudflare KV namespace bound in wrangler.toml as REFUND_EVENTS */
  REFUND_EVENTS: KVNamespace;
}

// Notification types defined by Apple's V2 API.
const NOTIFICATION_TYPES = {
  REFUND: "REFUND",
  DID_RENEW: "DID_RENEW",
  EXPIRED: "EXPIRED",
  DID_FAIL_TO_RENEW: "DID_FAIL_TO_RENEW",
  SUBSCRIBED: "SUBSCRIBED",
  DID_CHANGE_RENEWAL_STATUS: "DID_CHANGE_RENEWAL_STATUS",
  DID_CHANGE_RENEWAL_PREF: "DID_CHANGE_RENEWAL_PREF",
  GRACE_PERIOD_EXPIRED: "GRACE_PERIOD_EXPIRED",
  OFFER_REDEEMED: "OFFER_REDEEMED",
  PRICE_INCREASE: "PRICE_INCREASE",
  REFUND_DECLINED: "REFUND_DECLINED",
  REFUND_REVERSED: "REFUND_REVERSED",
  CONSUMPTION_REQUEST: "CONSUMPTION_REQUEST",
  RENEWAL_EXTENDED: "RENEWAL_EXTENDED",
  RENEWAL_EXTENSION: "RENEWAL_EXTENSION",
  REVOKE: "REVOKE",
  TEST: "TEST",
  ONE_TIME_CHARGE: "ONE_TIME_CHARGE",
  EXTERNAL_PURCHASE_TOKEN: "EXTERNAL_PURCHASE_TOKEN",
} as const;

type NotificationType = (typeof NOTIFICATION_TYPES)[keyof typeof NOTIFICATION_TYPES];

interface RefundEvent {
  event_type: "refund";
  notification_uuid: string;
  notification_version: string;
  environment: string;
  original_transaction_id: string;
  product_id: string;
  refund_date: string | null;
  refund_reason: string | null;
  bundle_id: string;
  received_at: string;
  raw_transaction: Record<string, unknown>;
}

interface SubscriptionLifecycleEvent {
  event_type: "subscription_lifecycle";
  notification_type: string;
  subtype?: string;
  notification_uuid: string;
  notification_version: string;
  environment: string;
  original_transaction_id: string | null;
  product_id: string | null;
  bundle_id: string;
  renewal_date: string | null;
  expiry_date: string | null;
  received_at: string;
  raw_transaction: Record<string, unknown>;
  raw_renewal: Record<string, unknown>;
}

type StoredEvent = RefundEvent | SubscriptionLifecycleEvent;

/**
 * Convert Apple's epoch-milliseconds timestamp to ISO 8601.
 */
function epochMsToIso(ms: unknown): string | null {
  if (typeof ms !== "number" || ms <= 0) return null;
  try {
    return new Date(ms).toISOString();
  } catch {
    return null;
  }
}

/**
 * Store an event in Cloudflare KV.
 * Key format: <type>:<uuid>  (unique per notification)
 * TTL: 90 days (enough for refund dispute windows)
 */
async function storeEvent(kv: KVNamespace, event: StoredEvent): Promise<void> {
  const key = `${event.event_type}:${event.notification_uuid}`;
  // Also maintain a sorted-by-date index key for refunds only.
  await kv.put(key, JSON.stringify(event), {
    expirationTtl: 60 * 60 * 24 * 90, // 90 days in seconds
  });

  if (event.event_type === "refund") {
    // Maintain a secondary date-prefixed key for easy range queries via list().
    const datePrefix = (event.refund_date ?? event.received_at).slice(0, 10); // YYYY-MM-DD
    const indexKey = `refund_index:${datePrefix}:${event.notification_uuid}`;
    await kv.put(indexKey, event.notification_uuid, {
      expirationTtl: 60 * 60 * 24 * 90,
    });
  }
}

/**
 * Handle a REFUND notification.
 */
async function handleRefund(
  payload: VerifiedPayload,
  txInfo: Record<string, unknown>,
  env: Env
): Promise<void> {
  const originalTransactionId = String(txInfo.originalTransactionId ?? "unknown");
  const productId = String(txInfo.productId ?? "unknown");
  const refundDate = epochMsToIso(txInfo.revocationDate as number);
  const refundReason = txInfo.revocationReason != null ? String(txInfo.revocationReason) : null;
  const bundleId = String((payload.data as Record<string, unknown>)?.bundleId ?? "unknown");
  const environment = String((payload.data as Record<string, unknown>)?.environment ?? "unknown");

  const event: RefundEvent = {
    event_type: "refund",
    notification_uuid: payload.notificationUUID,
    notification_version: payload.notificationVersion,
    environment,
    original_transaction_id: originalTransactionId,
    product_id: productId,
    refund_date: refundDate,
    refund_reason: refundReason,
    bundle_id: bundleId,
    received_at: new Date().toISOString(),
    raw_transaction: txInfo,
  };

  console.log(
    JSON.stringify({
      level: "info",
      event: "apple_refund",
      original_transaction_id: originalTransactionId,
      product_id: productId,
      refund_date: refundDate,
      refund_reason: refundReason,
      environment,
      notification_uuid: payload.notificationUUID,
    })
  );

  await storeEvent(env.REFUND_EVENTS, event);
}

/**
 * Handle subscription lifecycle events (DID_RENEW, EXPIRED, DID_FAIL_TO_RENEW, etc.).
 */
async function handleSubscriptionLifecycle(
  payload: VerifiedPayload,
  notificationType: string,
  txInfo: Record<string, unknown>,
  renewalInfo: Record<string, unknown>,
  env: Env
): Promise<void> {
  const bundleId = String((payload.data as Record<string, unknown>)?.bundleId ?? "unknown");
  const environment = String((payload.data as Record<string, unknown>)?.environment ?? "unknown");

  const event: SubscriptionLifecycleEvent = {
    event_type: "subscription_lifecycle",
    notification_type: notificationType,
    subtype: payload.subtype,
    notification_uuid: payload.notificationUUID,
    notification_version: payload.notificationVersion,
    environment,
    original_transaction_id:
      txInfo.originalTransactionId != null ? String(txInfo.originalTransactionId) : null,
    product_id: txInfo.productId != null ? String(txInfo.productId) : null,
    bundle_id: bundleId,
    renewal_date: epochMsToIso(renewalInfo.renewalDate as number),
    expiry_date: epochMsToIso(txInfo.expiresDate as number),
    received_at: new Date().toISOString(),
    raw_transaction: txInfo,
    raw_renewal: renewalInfo,
  };

  console.log(
    JSON.stringify({
      level: "info",
      event: "apple_subscription_lifecycle",
      notification_type: notificationType,
      subtype: payload.subtype,
      original_transaction_id: event.original_transaction_id,
      product_id: event.product_id,
      environment,
      renewal_date: event.renewal_date,
      expiry_date: event.expiry_date,
      notification_uuid: payload.notificationUUID,
    })
  );

  await storeEvent(env.REFUND_EVENTS, event);
}

/**
 * Main fetch handler — entry point for the Cloudflare Worker.
 */
export default {
  async fetch(request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // Health check — GET /health
    if (request.method === "GET" && url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }

    // Only accept POST to /apple/notifications (or root path for flexibility).
    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    const allowedPaths = ["/", "/apple/notifications"];
    if (!allowedPaths.includes(url.pathname)) {
      return new Response("Not Found", { status: 404 });
    }

    let body: string;
    try {
      body = await request.text();
    } catch {
      return new Response("Bad Request: could not read body", { status: 400 });
    }

    if (!body) {
      return new Response("Bad Request: empty body", { status: 400 });
    }

    // The V2 notification body is a JSON object with a single `signedPayload` JWS field.
    let signedPayload: string | undefined;
    try {
      const parsed = JSON.parse(body) as Record<string, unknown>;
      signedPayload = parsed.signedPayload as string | undefined;
    } catch {
      return new Response("Bad Request: body is not valid JSON", { status: 400 });
    }

    if (!signedPayload || typeof signedPayload !== "string") {
      return new Response("Bad Request: missing signedPayload field", { status: 400 });
    }

    // Verify the JWS signature using Apple's certificate chain.
    let payload: VerifiedPayload;
    try {
      payload = await verifyAppleJws(signedPayload);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error(JSON.stringify({ level: "error", event: "jws_verification_failed", error: msg }));
      return new Response(`Forbidden: JWS verification failed — ${msg}`, { status: 403 });
    }

    const notificationType = String(payload.notificationType ?? "") as NotificationType;

    // Decode inner signed sub-payloads (transaction info and renewal info).
    const data = payload.data as Record<string, unknown> | undefined;
    let txInfo: Record<string, unknown> = {};
    let renewalInfo: Record<string, unknown> = {};
    try {
      txInfo = data?.signedTransactionInfo
        ? await decodeInnerJws(String(data.signedTransactionInfo))
        : {};
      renewalInfo = data?.signedRenewalInfo
        ? await decodeInnerJws(String(data.signedRenewalInfo))
        : {};
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error(
        JSON.stringify({ level: "error", event: "inner_jws_verification_failed", error: msg })
      );
      return new Response(`Forbidden: inner JWS verification failed — ${msg}`, { status: 403 });
    }

    try {
      switch (notificationType) {
        case NOTIFICATION_TYPES.REFUND:
          await handleRefund(payload, txInfo, env);
          break;

        case NOTIFICATION_TYPES.DID_RENEW:
        case NOTIFICATION_TYPES.EXPIRED:
        case NOTIFICATION_TYPES.DID_FAIL_TO_RENEW:
        case NOTIFICATION_TYPES.SUBSCRIBED:
        case NOTIFICATION_TYPES.DID_CHANGE_RENEWAL_STATUS:
        case NOTIFICATION_TYPES.GRACE_PERIOD_EXPIRED:
        case NOTIFICATION_TYPES.REFUND_DECLINED:
        case NOTIFICATION_TYPES.REFUND_REVERSED:
        case NOTIFICATION_TYPES.REVOKE:
          await handleSubscriptionLifecycle(payload, notificationType, txInfo, renewalInfo, env);
          break;

        case NOTIFICATION_TYPES.TEST:
          console.log(
            JSON.stringify({
              level: "info",
              event: "apple_test_notification",
              notification_uuid: payload.notificationUUID,
            })
          );
          break;

        default:
          // Log unknown types but still acknowledge to prevent Apple retries.
          console.log(
            JSON.stringify({
              level: "info",
              event: "apple_notification_unhandled_type",
              notification_type: notificationType,
              notification_uuid: payload.notificationUUID,
            })
          );
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error(
        JSON.stringify({
          level: "error",
          event: "notification_processing_error",
          notification_type: notificationType,
          error: msg,
        })
      );
      // Still return 200 — Apple will retry on non-2xx, and we don't want spam for storage errors.
      // The error is captured in Worker logs for investigation.
    }

    // Apple requires a 200 OK to acknowledge receipt.
    return new Response(null, { status: 200 });
  },
} satisfies ExportedHandler<Env>;
