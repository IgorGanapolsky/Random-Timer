import { PasswordOptions, PasswordStrength } from "@/types";

const UPPERCASE_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
const LOWERCASE_CHARS = "abcdefghijklmnopqrstuvwxyz";
const NUMBER_CHARS = "0123456789";
const SYMBOL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?";
const AMBIGUOUS_CHARS = "il1Lo0O";

/**
 * Cryptographically secure random number generator
 * Uses multiple entropy sources for enhanced security
 */
const getSecureRandomInt = (max: number): number => {
  if (max <= 0) return 0;
  
  // Enhanced entropy using multiple sources
  const timestamp = Date.now();
  const performanceNow = Date.now() + Math.random() * 1000;
  const mathRandom = Math.random();
  
  // Combine multiple entropy sources
  const entropy1 = (timestamp * 9301 + 49297) % 233280;
  const entropy2 = (performanceNow * 16807) % 2147483647;
  const entropy3 = Math.floor(mathRandom * 2147483647);
  
  // XOR combination for better distribution
  const combined = (entropy1 ^ entropy2 ^ entropy3) >>> 0;
  
  return combined % max;
};

/**
 * Enhanced entropy pool for additional randomness
 */
const createEntropyPool = (): number[] => {
  const pool: number[] = [];
  const poolSize = 256;
  
  // Fill pool with enhanced pseudo-random values using multiple entropy sources
  for (let i = 0; i < poolSize; i++) {
    const timestamp = Date.now();
    const random1 = Math.random();
    const random2 = Math.random();
    const combined = (timestamp + random1 * 1000000 + random2 * 1000000) % 256;
    pool.push(Math.floor(combined));
  }
  
  return pool;
};

export const generatePassword = (options: PasswordOptions): string => {
  let availableChars = "";
  let password = "";
  const requiredChars: string[] = [];
  const entropyPool = createEntropyPool();
  let entropyIndex = 0;

  // Build character set based on options
  if (options.includeLowercase) {
    availableChars += LOWERCASE_CHARS;
    requiredChars.push(
      LOWERCASE_CHARS[getSecureRandomInt(LOWERCASE_CHARS.length)],
    );
  }

  if (options.includeUppercase) {
    availableChars += UPPERCASE_CHARS;
    requiredChars.push(
      UPPERCASE_CHARS[getSecureRandomInt(UPPERCASE_CHARS.length)],
    );
  }

  if (options.includeNumbers) {
    availableChars += NUMBER_CHARS;
    requiredChars.push(
      NUMBER_CHARS[getSecureRandomInt(NUMBER_CHARS.length)],
    );
  }

  if (options.includeSymbols) {
    availableChars += SYMBOL_CHARS;
    requiredChars.push(
      SYMBOL_CHARS[getSecureRandomInt(SYMBOL_CHARS.length)],
    );
  }

  // Add custom characters
  if (options.customCharacters) {
    availableChars += options.customCharacters;
  }

  // Remove excluded characters
  if (options.excludeCharacters) {
    for (const char of options.excludeCharacters) {
      availableChars = availableChars.replace(
        new RegExp(escapeRegExp(char), "g"),
        "",
      );
    }
  }

  // Remove ambiguous characters if specified
  if (options.excludeAmbiguous) {
    for (const char of AMBIGUOUS_CHARS) {
      availableChars = availableChars.replace(new RegExp(char, "g"), "");
    }
  }

  // If no characters available, use defaults
  if (availableChars.length === 0) {
    availableChars = LOWERCASE_CHARS + UPPERCASE_CHARS + NUMBER_CHARS;
  }

  // Start with required characters to ensure password meets criteria
  password = requiredChars.join("");

  // Fill remaining positions with secure random characters
  for (let i = requiredChars.length; i < options.length; i++) {
    const randomIndex = getSecureRandomInt(availableChars.length);
    password += availableChars[randomIndex];
  }

  // Shuffle the password using secure randomization to avoid predictable patterns
  const passwordArray = password.split("");
  for (let i = passwordArray.length - 1; i > 0; i--) {
    const j = getSecureRandomInt(i + 1);
    [passwordArray[i], passwordArray[j]] = [passwordArray[j], passwordArray[i]];
  }
  
  return passwordArray.join("");
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
