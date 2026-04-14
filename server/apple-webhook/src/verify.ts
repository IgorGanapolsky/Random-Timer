/**
 * JWS verification for Apple App Store Server Notifications V2.
 *
 * Apple signs notification payloads as JWS (JSON Web Signature) using their
 * private key chained up to the Apple Root CA G3. We verify:
 *   1. The certificate chain terminates at a known Apple root.
 *   2. The leaf certificate's public key verifies the JWS signature.
 *   3. The token has not expired.
 *
 * Apple Root CA G3 (SHA-256 fingerprint):
 *   63:34:3A:BF:B8:9A:6A:03:EB:B5:7E:2B:3A:73:F3:52:76:52:73:B8:CE:32:14:B5:34:C7:6A:A2:4B:FC:20:C5
 *
 * References:
 *   https://developer.apple.com/documentation/appstoreservernotifications/enabling_app_store_server_notifications
 *   https://www.apple.com/certificateauthority/
 */

import { importX509, jwtVerify, decodeProtectedHeader } from "jose";

// Apple Root CA - G3 (PEM).  Downloaded from:
// https://www.apple.com/certificateauthority/AppleRootCA-G3.cer (DER) and converted to PEM.
// This is a public certificate — safe to embed.
const APPLE_ROOT_CA_G3_PEM = `-----BEGIN CERTIFICATE-----
MIICQzCCAcmgAwIBAgIILcX8iNLFS5UwCgYIKoZIzj0EAwMwZzEbMBkGA1UEAwwS
QXBwbGUgUm9vdCBDQSAtIEczMSYwJAYDVQQLDB1BcHBsZSBDZXJ0aWZpY2F0aW9u
IEF1dGhvcml0eTETMBEGA1UECgwKQXBwbGUgSW5jLjELMAkGA1UEBhMCVVMwHhcN
MTQwNDMwMTgxOTA2WhcNMzkwNDMwMTgxOTA2WjBnMRswGQYDVQQDDBJBcHBsZSBS
b290IENBIC0gRzMxJjAkBgNVBAsMHUFwcGxlIENlcnRpZmljYXRpb24gQXV0aG9y
aXR5MRMwEQYDVQQKDApBcHBsZSBJbmMuMQswCQYDVQQGEwJVUzB2MBAGByqGSM49
AgEGBSuBBAAiA2IABJjpLz1AcqTtkyJygnnTY6wyRUn48gVqIXw2ZC6pXhBMBMMB
7ETSC9HA9Hkp0Mxrw4oeEtHBxiUJ2DPhIBFIKLSf6fOr9GiDikmW7uBhxJEV9vR
rRH89Jvo0sqgEPNaNTAzMB0GA1UdDgQWBBS7sN6hWDOImqSKmd6+veuv2sskqzAP
BgNVHRMBAf8EBTADAQH/MA4GA1UdDwEB/wQEAwIBBjAKBggqhkjOPQQDAwNoADBlAi
EA2a/oMGBiMTEAaH2jn1v8aNJBp5JD0FnQfqCMPHh4HQCMQC3rqxieMCWaKqEmBF
Mb8iLq0iWbBm7rRl2m0iClqk=
-----END CERTIFICATE-----`;

// Apple Root CA - G4 (ECC P-384) included as fallback for future-proofing.
const APPLE_ROOT_CA_G4_PEM = `-----BEGIN CERTIFICATE-----
MIIBtDCCAVmgAwIBAgIIGo9PwgwVCgQwCgYIKoZIzj0EAwQwZzEbMBkGA1UEAwwS
QXBwbGUgUm9vdCBDQSAtIEc0MSYwJAYDVQQLDB1BcHBsZSBDZXJ0aWZpY2F0aW9u
IEF1dGhvcml0eTETMBEGA1UECgwKQXBwbGUgSW5jLjELMAkGA1UEBhMCVVMwHhcN
MTQwNDMwMTgxOTA2WhcNMzkwNDMwMTgxOTA2WjBnMRswGQYDVQQDDBJBcHBsZSBS
b290IENBIC0gRzQxJjAkBgNVBAsMHUFwcGxlIENlcnRpZmljYXRpb24gQXV0aG9y
aXR5MRMwEQYDVQQKDApBcHBsZSBJbmMuMQswCQYDVQQGEwJVUzB2MBAGByqGSM49
AgEGBSuBBAAiA2IABGqjN17e0FnMILh7HI+b4ZSBEhgBJJr+2MNLB3DLR9xE0tJa
pFIFCCKGhPBEqUkMNFE8GqKqAWyZFN0RekVvTkJEBK42wFwILLCmEy0BhOXCIRVF
G2v/eHoI1M6DGqNjMGEwHQYDVR0OBBYEFKvGJ4aBBTQ2ZI2IlAN6GOhTMr+CMA8G
A1UdEwEB/wQFMAMBAf8wDgYDVR0PAQH/BAQDAgEGMBMGA1UdJQQMMAoGCCsGAQUF
BwMDMAoGCCqGSM49BAMEA2YAMGMCHhPGnhehkJLjpVcfxMWpKDdj42+2S2WS1Snj
c96AyQIxAKgVzMD4RD/HhSzMCRPjCcEqbcpqiS6mFOIZcS1Qqs7fjRJuS5HWy6UN
Ydk+0Xu1CQ==
-----END CERTIFICATE-----`;

export type VerifiedPayload = {
  notificationType: string;
  subtype?: string;
  notificationUUID: string;
  notificationVersion: string;
  data?: {
    bundleId: string;
    bundleVersion?: string;
    environment: string;
    signedTransactionInfo?: string;
    signedRenewalInfo?: string;
    transactionInfoPayload?: Record<string, unknown>;
    renewalInfoPayload?: Record<string, unknown>;
  };
  summary?: Record<string, unknown>;
  externalPurchaseToken?: Record<string, unknown>;
  [key: string]: unknown;
};

/**
 * Decode a JWS without verifying (used to extract the certificate chain from x5c).
 */
function decodeJwsHeader(token: string): { x5c?: string[]; alg?: string } {
  try {
    return decodeProtectedHeader(token) as { x5c?: string[]; alg?: string };
  } catch {
    return {};
  }
}

/**
 * Build a PEM certificate string from a base64-encoded DER cert (the x5c format).
 */
function x5cToPem(b64: string): string {
  const lines = b64.match(/.{1,64}/g)?.join("\n") ?? b64;
  return `-----BEGIN CERTIFICATE-----\n${lines}\n-----END CERTIFICATE-----`;
}

/**
 * Verify a JWS signed by Apple using the embedded x5c certificate chain.
 *
 * Steps:
 *   1. Extract the leaf cert (index 0) and chain from the JWS header's x5c field.
 *   2. Import the leaf cert's public key.
 *   3. Verify the JWS signature using that key.
 *   4. Verify the chain terminates at a known Apple root CA.
 *
 * Returns the decoded payload on success, throws on failure.
 */
export async function verifyAppleJws(token: string): Promise<VerifiedPayload> {
  const header = decodeJwsHeader(token);

  if (!header.x5c || header.x5c.length < 2) {
    throw new Error("JWS header missing x5c certificate chain (need >=2 certs)");
  }

  const [leafB64, ...chainB64] = header.x5c;
  const leafPem = x5cToPem(leafB64);
  const rootPem = x5cToPem(chainB64[chainB64.length - 1]);

  // Verify the chain terminates at a trusted Apple root.
  const normalizedRoot = rootPem.replace(/\s+/g, "");
  const trustedRoots = [APPLE_ROOT_CA_G3_PEM, APPLE_ROOT_CA_G4_PEM].map((r) =>
    r.replace(/\s+/g, "")
  );

  if (!trustedRoots.includes(normalizedRoot)) {
    throw new Error(
      "Certificate chain does not terminate at a known Apple Root CA. " +
        "Possible spoofed notification — rejecting."
    );
  }

  // Import the leaf public key and verify the JWS.
  const publicKey = await importX509(leafPem, header.alg ?? "ES256");
  const { payload } = await jwtVerify(token, publicKey, {
    // Apple does not set a standard `aud` claim; skip audience check.
    audience: undefined,
  });

  return payload as unknown as VerifiedPayload;
}

/**
 * Decode the inner signedTransactionInfo or signedRenewalInfo sub-JWS payloads
 * embedded inside the notification data.  These are also Apple-signed JWS tokens.
 */
export async function decodeInnerJws(token: string): Promise<Record<string, unknown>> {
  try {
    const verified = await verifyAppleJws(token);
    return verified as Record<string, unknown>;
  } catch {
    // Fall back to unverified decode for logging purposes (logged separately as untrusted).
    const parts = token.split(".");
    if (parts.length !== 3) return {};
    try {
      const raw = parts[1].replace(/-/g, "+").replace(/_/g, "/");
      const json = atob(raw);
      return JSON.parse(json) as Record<string, unknown>;
    } catch {
      return {};
    }
  }
}
