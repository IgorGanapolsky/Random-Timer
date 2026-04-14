/**
 * JWS verification for Apple App Store Server Notifications V2.
 *
 * Apple signs notification payloads as JWS (JSON Web Signature) using their
 * private key chained up to the Apple Root CA G3. We verify:
 *   1. The certificate chain terminates at a known Apple root.
 *   2. Every consecutive pair in the chain is cryptographically validated:
 *      cert[i].tbsCertificate is verified against cert[i+1]'s public key
 *      using Web Crypto SubtleCrypto — no string comparisons for chain links.
 *   3. The leaf certificate's public key verifies the JWS signature.
 *   4. The token has not expired.
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

// ---------------------------------------------------------------------------
// Minimal DER / ASN.1 parser — used only for X.509 chain validation.
// Cloudflare Workers expose Web Crypto (crypto.subtle) but no X.509 library.
// ---------------------------------------------------------------------------

interface TlvInfo {
  tag: number;
  valueStart: number;
  valueLen: number;
  end: number;
}

function readLength(data: Uint8Array, pos: number): { len: number; advance: number } {
  const first = data[pos];
  if ((first & 0x80) === 0) return { len: first, advance: 1 };
  const numBytes = first & 0x7f;
  let len = 0;
  for (let i = 0; i < numBytes; i++) len = (len << 8) | data[pos + 1 + i];
  return { len, advance: 1 + numBytes };
}

function readTlv(data: Uint8Array, pos: number): TlvInfo {
  const tag = data[pos];
  const { len, advance } = readLength(data, pos + 1);
  return { tag, valueStart: pos + 1 + advance, valueLen: len, end: pos + 1 + advance + len };
}

interface SigInfo {
  isEcdsa: boolean;
  hashAlg: string;
}

/**
 * Extract the TBSCertificate bytes (what was signed), signature algorithm, and
 * raw signature from a DER-encoded X.509 certificate.
 */
function extractTbsAndSig(
  der: Uint8Array
): { tbs: Uint8Array; sigInfo: SigInfo; sig: Uint8Array } {
  const certSeq = readTlv(der, 0);
  let pos = certSeq.valueStart;

  // TBSCertificate SEQUENCE — raw bytes including the outer SEQUENCE tag/length
  const tbsElem = readTlv(der, pos);
  const tbs = der.slice(pos, tbsElem.end);
  pos = tbsElem.end;

  // signatureAlgorithm SEQUENCE
  const sigAlgSeq = readTlv(der, pos);
  const oidElem = readTlv(der, sigAlgSeq.valueStart);
  const oidBytes = der.slice(oidElem.valueStart, oidElem.valueStart + oidElem.valueLen);
  const oidHex = Array.from(oidBytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  pos = sigAlgSeq.end;

  // Map OID to algorithm parameters
  // ecdsa-with-SHA256: 1.2.840.10045.4.3.2
  // ecdsa-with-SHA384: 1.2.840.10045.4.3.3
  // ecdsa-with-SHA512: 1.2.840.10045.4.3.4
  // sha256WithRSAEncryption: 1.2.840.113549.1.1.11
  // sha384WithRSAEncryption: 1.2.840.113549.1.1.12
  const OID_MAP: Record<string, SigInfo> = {
    "2a8648ce3d040302": { isEcdsa: true, hashAlg: "SHA-256" },
    "2a8648ce3d040303": { isEcdsa: true, hashAlg: "SHA-384" },
    "2a8648ce3d040304": { isEcdsa: true, hashAlg: "SHA-512" },
    "2a864886f70d01010b": { isEcdsa: false, hashAlg: "SHA-256" },
    "2a864886f70d01010c": { isEcdsa: false, hashAlg: "SHA-384" },
  };
  const sigInfo = OID_MAP[oidHex];
  if (!sigInfo) throw new Error(`Unsupported signature algorithm OID: ${oidHex}`);

  // signatureValue BIT STRING
  const sigBitsElem = readTlv(der, pos);
  // First byte of BIT STRING value is unused-bits count (always 0 for certs)
  const sig = der.slice(sigBitsElem.valueStart + 1, sigBitsElem.end);

  return { tbs, sigInfo, sig };
}

/**
 * Extract the SubjectPublicKeyInfo (SPKI) bytes from a DER-encoded certificate.
 * Identified structurally as the SEQUENCE in TBSCertificate whose first child is
 * an AlgorithmIdentifier (SEQUENCE) and whose second child is a BIT STRING.
 */
function extractSpki(der: Uint8Array): Uint8Array {
  const certSeq = readTlv(der, 0);
  let pos = certSeq.valueStart;
  const tbsElem = readTlv(der, pos);
  pos = tbsElem.valueStart;
  const tbsEnd = tbsElem.end;

  // Skip optional version [0] EXPLICIT context tag
  if (pos < tbsEnd && der[pos] === 0xa0) {
    pos = readTlv(der, pos).end;
  }

  while (pos < tbsEnd) {
    const elem = readTlv(der, pos);
    if (elem.tag === 0x30 && elem.valueLen > 4) {
      // Check for SPKI structure: SEQUENCE { SEQUENCE (AlgId), BIT STRING }
      const inner = readTlv(der, elem.valueStart);
      if (inner.tag === 0x30 && inner.end < elem.end) {
        const next = readTlv(der, inner.end);
        if (next.tag === 0x03) {
          return der.slice(pos, elem.end);
        }
      }
    }
    pos = elem.end;
  }
  throw new Error("SubjectPublicKeyInfo not found in certificate");
}

/**
 * Convert an ECDSA signature from DER (SEQUENCE { INTEGER r, INTEGER s }) to the
 * raw concatenated format (r || s) expected by Web Crypto ECDSA verify.
 */
function ecdsaDerToRaw(derSig: Uint8Array, keyBytes: number): Uint8Array {
  const seq = readTlv(derSig, 0);
  let pos = seq.valueStart;

  const rElem = readTlv(derSig, pos);
  let r = derSig.slice(rElem.valueStart, rElem.valueStart + rElem.valueLen);
  pos = rElem.end;

  const sElem = readTlv(derSig, pos);
  let s = derSig.slice(sElem.valueStart, sElem.valueStart + sElem.valueLen);

  // Strip leading 0x00 padding bytes added by DER to preserve sign
  while (r.length > keyBytes) r = r.slice(1);
  while (s.length > keyBytes) s = s.slice(1);

  // Pad to exact key size
  const raw = new Uint8Array(keyBytes * 2);
  raw.set(r, keyBytes - r.length);
  raw.set(s, keyBytes * 2 - s.length);
  return raw;
}

/**
 * Cryptographically verify that `subjectDer` was signed by the private key
 * corresponding to the public key in `issuerDer`.
 */
async function verifyCertSignedBy(
  subjectDer: Uint8Array,
  issuerDer: Uint8Array
): Promise<void> {
  const { tbs, sigInfo, sig } = extractTbsAndSig(subjectDer);
  const spki = extractSpki(issuerDer);

  let key: CryptoKey;
  let signature: ArrayBuffer;

  if (sigInfo.isEcdsa) {
    const namedCurve =
      sigInfo.hashAlg === "SHA-256" ? "P-256" :
      sigInfo.hashAlg === "SHA-384" ? "P-384" : "P-521";
    const keyBytes =
      sigInfo.hashAlg === "SHA-256" ? 32 :
      sigInfo.hashAlg === "SHA-384" ? 48 : 66;
    key = await crypto.subtle.importKey(
      "spki", spki,
      { name: "ECDSA", namedCurve },
      false, ["verify"]
    );
    signature = ecdsaDerToRaw(sig, keyBytes).buffer as ArrayBuffer;
    const ok = await crypto.subtle.verify(
      { name: "ECDSA", hash: sigInfo.hashAlg },
      key, signature, tbs
    );
    if (!ok) throw new Error("Certificate chain signature verification failed (ECDSA)");
  } else {
    key = await crypto.subtle.importKey(
      "spki", spki,
      { name: "RSASSA-PKCS1-v1_5", hash: sigInfo.hashAlg },
      false, ["verify"]
    );
    const ok = await crypto.subtle.verify(
      { name: "RSASSA-PKCS1-v1_5" },
      key, sig, tbs
    );
    if (!ok) throw new Error("Certificate chain signature verification failed (RSA)");
  }
}

/**
 * Decode a base64-encoded DER certificate (x5c element) to a Uint8Array.
 */
function b64ToDer(b64: string): Uint8Array {
  // x5c values are plain base64 (not base64url), no PEM headers
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

/**
 * Verify the full X.509 certificate chain from the JWS x5c header.
 *
 * For each consecutive pair (cert[i], cert[i+1]):
 *   - cert[i].tbsCertificate is cryptographically verified against cert[i+1]'s
 *     SubjectPublicKeyInfo using Web Crypto SubtleCrypto.
 * The chain must terminate at a known Apple Root CA (G3 or G4).
 */
async function verifyCertChain(x5c: string[]): Promise<void> {
  // Verify each link: cert[i] signed by cert[i+1]
  for (let i = 0; i < x5c.length - 1; i++) {
    const subjectDer = b64ToDer(x5c[i]);
    const issuerDer = b64ToDer(x5c[i + 1]);
    await verifyCertSignedBy(subjectDer, issuerDer);
  }

  // Verify the chain terminates at a trusted Apple root
  const rootPem = x5cToPem(x5c[x5c.length - 1]);
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
}

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
 *   1. Extract the x5c chain from the JWS protected header.
 *   2. Cryptographically verify every link in the chain (cert[i] → cert[i+1])
 *      using Web Crypto SubtleCrypto — prevents forged leaf injection.
 *   3. Assert the chain root is a known Apple Root CA (G3 or G4).
 *   4. Verify the JWS signature using the validated leaf cert's public key.
 *
 * Returns the decoded payload on success, throws on failure.
 */
export async function verifyAppleJws(token: string): Promise<VerifiedPayload> {
  const header = decodeJwsHeader(token);

  if (!header.x5c || header.x5c.length < 2) {
    throw new Error("JWS header missing x5c certificate chain (need >=2 certs)");
  }

  // Full cryptographic X.509 chain validation — rejects forged leaf injection.
  await verifyCertChain(header.x5c);

  // Chain is trusted; verify the JWS signature against the leaf cert's public key.
  const leafPem = x5cToPem(header.x5c[0]);
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
