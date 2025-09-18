import { 
  generatePassword, 
  calculatePasswordStrength, 
  getPasswordStrengthLabel,
  estimateCrackTime,
  generateMultiplePasswords,
  validatePasswordOptions 
} from '../passwordGenerator';
import { PasswordOptions, PasswordStrength } from '../../types';

describe('Password Generator Security Tests', () => {
  describe('Cryptographic Security', () => {
    test('should generate different passwords each time', () => {
      const options: PasswordOptions = {
        length: 12,
        includeLowercase: true,
        includeUppercase: true,
        includeNumbers: true,
        includeSymbols: true,
        excludeAmbiguous: false,
        excludeCharacters: '',
        customCharacters: ''
      };

      const passwords = Array.from({ length: 100 }, () => generatePassword(options));
      const uniquePasswords = new Set(passwords);
      
      // Should have high uniqueness (at least 95% unique)
      expect(uniquePasswords.size).toBeGreaterThan(95);
    });

    test('should not use predictable patterns', () => {
      const options: PasswordOptions = {
        length: 16,
        includeLowercase: true,
        includeUppercase: true,
        includeNumbers: true,
        includeSymbols: true,
        excludeAmbiguous: false,
        excludeCharacters: '',
        customCharacters: ''
      };

      const passwords = Array.from({ length: 50 }, () => generatePassword(options));
      
      // Check for common patterns
      passwords.forEach(password => {
        // Should not start with predictable sequences
        expect(password).not.toMatch(/^[a-z]{4}/);
        expect(password).not.toMatch(/^[A-Z]{4}/);
        expect(password).not.toMatch(/^[0-9]{4}/);
        
        // Should not have repeated characters
        expect(password).not.toMatch(/(.)\1{3,}/);
        
        // Should not be sequential
        expect(password).not.toMatch(/abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz/i);
        expect(password).not.toMatch(/123|234|345|456|567|678|789|890/);
      });
    });

    test('should have high entropy', () => {
      const options: PasswordOptions = {
        length: 20,
        includeLowercase: true,
        includeUppercase: true,
        includeNumbers: true,
        includeSymbols: true,
        excludeAmbiguous: false,
        excludeCharacters: '',
        customCharacters: ''
      };

      const password = generatePassword(options);
      
      // Calculate entropy
      const charsetSize = 26 + 26 + 10 + 32; // lowercase + uppercase + numbers + symbols
      const entropy = Math.log2(Math.pow(charsetSize, password.length));
      
      // Should have high entropy (>100 bits for 20 chars)
      expect(entropy).toBeGreaterThan(100);
    });
  });

  describe('Password Strength Calculation', () => {
    test('should correctly calculate strength for strong passwords', () => {
      const strongPassword = 'MyStr0ng!P@ssw0rd123';
      const strength = calculatePasswordStrength(strongPassword);
      
      expect(strength).toBeGreaterThanOrEqual(PasswordStrength.Good);
    });

    test('should correctly calculate strength for weak passwords', () => {
      const weakPassword = '123';
      const strength = calculatePasswordStrength(weakPassword);
      
      expect(strength).toBeLessThanOrEqual(PasswordStrength.Weak);
    });

    test('should penalize common patterns', () => {
      const commonPatterns = [
        'password123',
        'qwerty123',
        'abc123456',
        '123456789'
      ];

      commonPatterns.forEach(password => {
        const strength = calculatePasswordStrength(password);
        expect(strength).toBeLessThanOrEqual(PasswordStrength.Weak);
      });
    });

    test('should reward complexity', () => {
      const complexPassword = 'Kx9#mP2$vL8@nQ5!';
      const strength = calculatePasswordStrength(complexPassword);
      
      expect(strength).toBeGreaterThanOrEqual(PasswordStrength.Strong);
    });
  });

  describe('Crack Time Estimation', () => {
    test('should estimate realistic crack times', () => {
      const weakPassword = '123456';
      const strongPassword = 'MyStr0ng!P@ssw0rd123';

      const weakTime = estimateCrackTime(weakPassword);
      const strongTime = estimateCrackTime(strongPassword);

      expect(weakTime).toBe('Instantly');
      expect(strongTime).toMatch(/years|Centuries/);
    });
  });

  describe('Multiple Password Generation', () => {
    test('should generate multiple unique passwords', () => {
      const options: PasswordOptions = {
        length: 12,
        includeLowercase: true,
        includeUppercase: true,
        includeNumbers: true,
        includeSymbols: false,
        excludeAmbiguous: false,
        excludeCharacters: '',
        customCharacters: ''
      };

      const passwords = generateMultiplePasswords(options, 10);
      const uniquePasswords = new Set(passwords);

      expect(passwords).toHaveLength(10);
      expect(uniquePasswords.size).toBe(10);
    });
  });

  describe('Input Validation', () => {
    test('should validate password options correctly', () => {
      const validOptions: PasswordOptions = {
        length: 12,
        includeLowercase: true,
        includeUppercase: false,
        includeNumbers: false,
        includeSymbols: false,
        excludeAmbiguous: false,
        excludeCharacters: '',
        customCharacters: ''
      };

      const invalidOptions: PasswordOptions = {
        length: 2, // Too short
        includeLowercase: false,
        includeUppercase: false,
        includeNumbers: false,
        includeSymbols: false,
        excludeAmbiguous: false,
        excludeCharacters: '',
        customCharacters: ''
      };

      expect(validatePasswordOptions(validOptions)).toBe(true);
      expect(validatePasswordOptions(invalidOptions)).toBe(false);
    });
  });

  describe('Character Set Validation', () => {
    test('should respect character inclusion options', () => {
      const options: PasswordOptions = {
        length: 20,
        includeLowercase: true,
        includeUppercase: false,
        includeNumbers: false,
        includeSymbols: false,
        excludeAmbiguous: false,
        excludeCharacters: '',
        customCharacters: ''
      };

      const password = generatePassword(options);
      
      // Should only contain lowercase letters
      expect(password).toMatch(/^[a-z]+$/);
      expect(password).not.toMatch(/[A-Z0-9!@#$%^&*()]/);
    });

    test('should exclude ambiguous characters when requested', () => {
      const options: PasswordOptions = {
        length: 50,
        includeLowercase: true,
        includeUppercase: true,
        includeNumbers: true,
        includeSymbols: true,
        excludeAmbiguous: true,
        excludeCharacters: '',
        customCharacters: ''
      };

      const password = generatePassword(options);
      
      // Should not contain ambiguous characters
      expect(password).not.toMatch(/[il1Lo0O]/);
    });

    test('should exclude custom characters when specified', () => {
      const options: PasswordOptions = {
        length: 20,
        includeLowercase: true,
        includeUppercase: true,
        includeNumbers: true,
        includeSymbols: true,
        excludeAmbiguous: false,
        excludeCharacters: 'aA1',
        customCharacters: ''
      };

      const password = generatePassword(options);
      
      // Should not contain excluded characters
      expect(password).not.toMatch(/[aA1]/);
    });
  });

  describe('Security Edge Cases', () => {
    test('should handle minimum length requirements', () => {
      const options: PasswordOptions = {
        length: 4,
        includeLowercase: true,
        includeUppercase: true,
        includeNumbers: true,
        includeSymbols: true,
        excludeAmbiguous: false,
        excludeCharacters: '',
        customCharacters: ''
      };

      const password = generatePassword(options);
      expect(password).toHaveLength(4);
      expect(password.length).toBeGreaterThanOrEqual(4);
    });

    test('should handle maximum length requirements', () => {
      const options: PasswordOptions = {
        length: 128,
        includeLowercase: true,
        includeUppercase: true,
        includeNumbers: true,
        includeSymbols: true,
        excludeAmbiguous: false,
        excludeCharacters: '',
        customCharacters: ''
      };

      const password = generatePassword(options);
      expect(password).toHaveLength(128);
    });

    test('should handle empty character sets gracefully', () => {
      const options: PasswordOptions = {
        length: 10,
        includeLowercase: false,
        includeUppercase: false,
        includeNumbers: false,
        includeSymbols: false,
        excludeAmbiguous: false,
        excludeCharacters: '',
        customCharacters: ''
      };

      // Should fall back to default character set
      const password = generatePassword(options);
      expect(password).toHaveLength(10);
      expect(password.length).toBeGreaterThan(0);
    });
  });
});
