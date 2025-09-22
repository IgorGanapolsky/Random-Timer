import { PasswordOptions, PasswordStrength } from "@/types";

const UPPERCASE_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
const LOWERCASE_CHARS = "abcdefghijklmnopqrstuvwxyz";
const NUMBER_CHARS = "0123456789";
const SYMBOL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?";
const AMBIGUOUS_CHARS = "il1Lo0O";

/**
 * Cryptographically secure random number in [0, max)
 * Prefers Web Crypto / React Native polyfill, falls back to Node crypto, then Math.random.
 */
const getSecureRandomInt = (max: number): number => {
  if (max <= 0) return 0;

  // Prefer Web Crypto API (available in RN with react-native-get-random-values polyfill)
  const cryptoObj: any = (globalThis as any).crypto;
  if (cryptoObj && typeof cryptoObj.getRandomValues === 'function') {
    const arr = new Uint32Array(1);
    while (true) {
      cryptoObj.getRandomValues(arr);
      const random32 = arr[0];
      const buckets = Math.floor(0x100000000 / max) * max;
      if (random32 < buckets) return random32 % max;
    }
  }

  // Node.js fallback for test environment
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const nodeCrypto = require('crypto');
    if (typeof nodeCrypto.randomInt === 'function') {
      return nodeCrypto.randomInt(0, max);
    }
  } catch (_) {
    // ignore
  }

  // Final fallback (non-crypto) with rejection sampling
  while (true) {
    const random32 = Math.floor(Math.random() * 0x100000000) >>> 0;
    const buckets = Math.floor(0x100000000 / max) * max;
    if (random32 < buckets) return random32 % max;
  }
};

/**
 * Enhanced entropy pool for additional randomness
 */
const createEntropyPool = (): number[] => {
  const pool: number[] = [];
  const poolSize = 256;

  // Fill pool with secure random values
  for (let i = 0; i < poolSize; i++) {
    // Use our secure random generator for each byte
    pool.push(getSecureRandomInt(256));
  }

  // Fisher-Yates shuffle for additional mixing
  for (let i = poolSize - 1; i > 0; i--) {
    const j = getSecureRandomInt(i + 1);
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }

  return pool;
};

export const generatePassword = (options: PasswordOptions): string => {
  let availableChars = "";
  let password = "";
  const requiredChars: string[] = [];

  const excludeSet = new Set<string>(options.excludeCharacters ? options.excludeCharacters.split("") : []);
  const shouldExclude = (ch: string): boolean => excludeSet.has(ch) || (options.excludeAmbiguous ? AMBIGUOUS_CHARS.includes(ch) : false);
  const filterChars = (chars: string): string => chars.split("").filter((c) => !shouldExclude(c)).join("");

  const lower = options.includeLowercase ? filterChars(LOWERCASE_CHARS) : "";
  const upper = options.includeUppercase ? filterChars(UPPERCASE_CHARS) : "";
  const nums = options.includeNumbers ? filterChars(NUMBER_CHARS) : "";
  const syms = options.includeSymbols ? filterChars(SYMBOL_CHARS) : "";
  const custom = options.customCharacters ? filterChars(options.customCharacters) : "";

  availableChars = lower + upper + nums + syms + custom;

  // If no characters available, use defaults (filtered)
  if (availableChars.length === 0) {
    availableChars = filterChars(LOWERCASE_CHARS + UPPERCASE_CHARS + NUMBER_CHARS);
  }

  // Choose required characters from filtered category sets
  if (lower.length > 0) requiredChars.push(lower[getSecureRandomInt(lower.length)]);
  if (upper.length > 0) requiredChars.push(upper[getSecureRandomInt(upper.length)]);
  if (nums.length > 0) requiredChars.push(nums[getSecureRandomInt(nums.length)]);
  if (syms.length > 0) requiredChars.push(syms[getSecureRandomInt(syms.length)]);

  // Start with required characters (may be 0..4 chars)
  password = requiredChars.join("");

  // Fill remaining positions with secure random characters
  for (let i = password.length; i < options.length; i++) {
    const randomIndex = getSecureRandomInt(availableChars.length);
    password += availableChars[randomIndex];
  }

  // Shuffle the password using secure randomization to avoid predictable patterns
  const passwordArray = password.split("");
  const isPredictable = (pwd: string): boolean => {
    return (
      /^[a-z]{4}/.test(pwd) ||
      /^[A-Z]{4}/.test(pwd) ||
      /^[0-9]{4}/.test(pwd) ||
      /(.)\1{3,}/.test(pwd) ||
      /abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz/i.test(pwd) ||
      /123|234|345|456|567|678|789|890/.test(pwd)
    );
  };

  const shuffleInPlace = () => {
    for (let i = passwordArray.length - 1; i > 0; i--) {
      const j = getSecureRandomInt(i + 1);
      [passwordArray[i], passwordArray[j]] = [passwordArray[j], passwordArray[i]];
    }
  };

  shuffleInPlace();
  let candidate = passwordArray.join("");

  // If predictable patterns detected, reshuffle a few times
  let attempts = 0;
  while (isPredictable(candidate) && attempts < 10) {
    shuffleInPlace();
    candidate = passwordArray.join("");
    attempts++;
  }

  return candidate;
};

export const calculatePasswordStrength = (
  password: string,
): PasswordStrength => {
  if (!password) return PasswordStrength.VeryWeak;

  let strength = 0;
  const length = password.length;

  // Length criteria
  if (length >= 8) strength++;
  if (length >= 12) strength++;
  if (length >= 16) strength++;

  // Character diversity
  if (/[a-z]/.test(password)) strength++;
  if (/[A-Z]/.test(password)) strength++;
  if (/[0-9]/.test(password)) strength++;
  if (/[^a-zA-Z0-9]/.test(password)) strength++;

  // Pattern detection (reduce strength for common patterns)
  if (/(.)\1{2,}/.test(password)) strength--; // Repeated characters
  if (/^[a-zA-Z]+$/.test(password)) strength--; // Only letters
  if (/^[0-9]+$/.test(password)) strength--; // Only numbers
  if (/^(123|abc|qwerty|password)/i.test(password)) strength -= 2; // Common patterns

  // Calculate entropy-based score
  const charsetSize = getCharsetSize(password);
  const entropy = length * Math.log2(charsetSize);

  if (entropy >= 60) strength++;
  if (entropy >= 80) strength++;

  // Normalize to our scale (0-5)
  const normalizedStrength = Math.max(0, Math.min(5, Math.floor(strength / 2)));

  return normalizedStrength as PasswordStrength;
};

export const getPasswordStrengthLabel = (
  strength: PasswordStrength,
): string => {
  const labels = {
    [PasswordStrength.VeryWeak]: "Very Weak",
    [PasswordStrength.Weak]: "Weak",
    [PasswordStrength.Fair]: "Fair",
    [PasswordStrength.Good]: "Good",
    [PasswordStrength.Strong]: "Strong",
    [PasswordStrength.VeryStrong]: "Very Strong",
  };
  return labels[strength];
};

export const estimateCrackTime = (password: string): string => {
  const charsetSize = getCharsetSize(password);
  const possibilities = Math.pow(charsetSize, password.length);
  const guessesPerSecond = 1e9; // 1 billion guesses per second

  const seconds = possibilities / (2 * guessesPerSecond);

  if (seconds < 1) return "Instantly";
  if (seconds < 60) return `${Math.floor(seconds)} seconds`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours`;
  if (seconds < 31536000) return `${Math.floor(seconds / 86400)} days`;
  if (seconds < 3153600000) return `${Math.floor(seconds / 31536000)} years`;

  return "Centuries";
};

// Helper functions
function escapeRegExp(string: string): string {
  return string.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&");
}

function shuffleString(str: string): string {
  const arr = str.split("");
  for (let i = arr.length - 1; i > 0; i--) {
    const j = getSecureRandomInt(i + 1);
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr.join("");
}

function getCharsetSize(password: string): number {
  let size = 0;
  if (/[a-z]/.test(password)) size += 26;
  if (/[A-Z]/.test(password)) size += 26;
  if (/[0-9]/.test(password)) size += 10;
  if (/[^a-zA-Z0-9]/.test(password)) size += 32;
  return size || 26; // Default to lowercase if no patterns match
}

export const generateMultiplePasswords = (
  options: PasswordOptions,
  count: number,
): string[] => {
  const passwords: string[] = [];
  for (let i = 0; i < count; i++) {
    passwords.push(generatePassword(options));
  }
  return passwords;
};

export const validatePasswordOptions = (options: PasswordOptions): boolean => {
  // At least one character type must be selected
  const hasCharType =
    options.includeUppercase === true ||
    options.includeLowercase === true ||
    options.includeNumbers === true ||
    options.includeSymbols === true ||
    (typeof options.customCharacters === "string" &&
      options.customCharacters.length > 0);

  // Length must be reasonable
  const validLength = options.length >= 4 && options.length <= 128;

  return hasCharType && validLength;
};
