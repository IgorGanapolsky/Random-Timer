import {
  generatePassword,
  calculatePasswordStrength,
  getPasswordStrengthLabel,
  estimateCrackTime,
  generateMultiplePasswords,
  validatePasswordOptions,
  PasswordStrength,
} from '../passwordGenerator';
import { PasswordOptions } from '../../types';

describe('passwordGenerator', () => {
  describe('generatePassword', () => {
    it('should generate password with default options', () => {
      const options: PasswordOptions = {
        length: 12,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: false,
      };

      const password = generatePassword(options);
      expect(password).toHaveLength(12);
      expect(password).toMatch(/[A-Z]/);
      expect(password).toMatch(/[a-z]/);
      expect(password).toMatch(/[0-9]/);
    });

    it('should generate password with all character types', () => {
      const options: PasswordOptions = {
        length: 16,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: true,
      };

      const password = generatePassword(options);
      expect(password).toHaveLength(16);
      expect(password).toMatch(/[A-Z]/);
      expect(password).toMatch(/[a-z]/);
      expect(password).toMatch(/[0-9]/);
      expect(password).toMatch(/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/);
    });

    it('should generate password with custom characters', () => {
      const options: PasswordOptions = {
        length: 10,
        includeUppercase: false,
        includeLowercase: false,
        includeNumbers: false,
        includeSymbols: false,
        customCharacters: 'ABC123',
      };

      const password = generatePassword(options);
      expect(password).toHaveLength(10);
      expect(password).toMatch(/^[ABC123]+$/);
    });

    it('should exclude specified characters', () => {
      const options: PasswordOptions = {
        length: 20,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: true,
        excludeCharacters: '0O1lI',
      };

      const password = generatePassword(options);
      expect(password).toHaveLength(20);
      expect(password).not.toMatch(/[0O1lI]/);
    });

    it('should exclude ambiguous characters when specified', () => {
      const options: PasswordOptions = {
        length: 15,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: false,
        excludeAmbiguous: true,
      };

      const password = generatePassword(options);
      expect(password).toHaveLength(15);
      expect(password).not.toMatch(/[il1Lo0O]/);
    });

    it('should handle minimum length requirement', () => {
      const options: PasswordOptions = {
        length: 4,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: true,
      };

      const password = generatePassword(options);
      expect(password).toHaveLength(4);
      expect(password).toMatch(/[A-Z]/);
      expect(password).toMatch(/[a-z]/);
      expect(password).toMatch(/[0-9]/);
      expect(password).toMatch(/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/);
    });

    it('should use default character set when none specified', () => {
      const options: PasswordOptions = {
        length: 8,
        includeUppercase: false,
        includeLowercase: false,
        includeNumbers: false,
        includeSymbols: false,
      };

      const password = generatePassword(options);
      expect(password).toHaveLength(8);
      expect(password).toMatch(/[a-zA-Z0-9]/);
    });
  });

  describe('calculatePasswordStrength', () => {
    it('should return VeryWeak for empty password', () => {
      const strength = calculatePasswordStrength('');
      expect(strength).toBe(PasswordStrength.VeryWeak);
    });

    it('should return VeryWeak for short password', () => {
      const strength = calculatePasswordStrength('abc');
      expect(strength).toBe(PasswordStrength.VeryWeak);
    });

    it('should return Weak for basic password', () => {
      const strength = calculatePasswordStrength('password');
      expect(strength).toBe(PasswordStrength.Weak);
    });

    it('should return Fair for password with numbers', () => {
      const strength = calculatePasswordStrength('password123');
      expect(strength).toBe(PasswordStrength.Fair);
    });

    it('should return Good for password with mixed case', () => {
      const strength = calculatePasswordStrength('Password123');
      expect(strength).toBe(PasswordStrength.Good);
    });

    it('should return Strong for password with symbols', () => {
      const strength = calculatePasswordStrength('Password123!');
      expect(strength).toBe(PasswordStrength.Strong);
    });

    it('should return VeryStrong for complex password', () => {
      const strength = calculatePasswordStrength('MyStr0ng!P@ssw0rd');
      expect(strength).toBe(PasswordStrength.VeryStrong);
    });

    it('should reduce strength for repeated characters', () => {
      const strength1 = calculatePasswordStrength('Password123!');
      const strength2 = calculatePasswordStrength('Password123!!!');
      expect(strength2).toBeLessThan(strength1);
    });

    it('should reduce strength for common patterns', () => {
      const strength1 = calculatePasswordStrength('Password123!');
      const strength2 = calculatePasswordStrength('password123');
      expect(strength2).toBeLessThan(strength1);
    });

    it('should reduce strength for only letters', () => {
      const strength = calculatePasswordStrength('abcdefghijklmnop');
      expect(strength).toBeLessThan(PasswordStrength.Strong);
    });

    it('should reduce strength for only numbers', () => {
      const strength = calculatePasswordStrength('1234567890123456');
      expect(strength).toBeLessThan(PasswordStrength.Strong);
    });
  });

  describe('getPasswordStrengthLabel', () => {
    it('should return correct labels for all strength levels', () => {
      expect(getPasswordStrengthLabel(PasswordStrength.VeryWeak)).toBe('Very Weak');
      expect(getPasswordStrengthLabel(PasswordStrength.Weak)).toBe('Weak');
      expect(getPasswordStrengthLabel(PasswordStrength.Fair)).toBe('Fair');
      expect(getPasswordStrengthLabel(PasswordStrength.Good)).toBe('Good');
      expect(getPasswordStrengthLabel(PasswordStrength.Strong)).toBe('Strong');
      expect(getPasswordStrengthLabel(PasswordStrength.VeryStrong)).toBe('Very Strong');
    });
  });

  describe('estimateCrackTime', () => {
    it('should return instantly for very weak passwords', () => {
      const time = estimateCrackTime('123');
      expect(time).toBe('Instantly');
    });

    it('should return seconds for weak passwords', () => {
      const time = estimateCrackTime('password');
      expect(time).toMatch(/seconds/);
    });

    it('should return minutes for moderate passwords', () => {
      const time = estimateCrackTime('Password123');
      expect(time).toMatch(/minutes/);
    });

    it('should return hours for strong passwords', () => {
      const time = estimateCrackTime('MyStr0ng!P@ssw0rd');
      expect(time).toMatch(/hours/);
    });

    it('should return days for very strong passwords', () => {
      const time = estimateCrackTime('MyStr0ng!P@ssw0rd123456789');
      expect(time).toMatch(/days/);
    });

    it('should return years for extremely strong passwords', () => {
      const time = estimateCrackTime('MyStr0ng!P@ssw0rd123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ');
      expect(time).toMatch(/years/);
    });

    it('should return centuries for maximum strength passwords', () => {
      const time = estimateCrackTime('MyStr0ng!P@ssw0rd123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+-=[]{}|;:,.<>?');
      expect(time).toBe('Centuries');
    });
  });

  describe('generateMultiplePasswords', () => {
    it('should generate multiple unique passwords', () => {
      const options: PasswordOptions = {
        length: 12,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: true,
      };

      const passwords = generateMultiplePasswords(options, 5);
      expect(passwords).toHaveLength(5);
      
      // All passwords should have correct length
      passwords.forEach(password => {
        expect(password).toHaveLength(12);
      });

      // Passwords should be different (very high probability)
      const uniquePasswords = new Set(passwords);
      expect(uniquePasswords.size).toBeGreaterThan(1);
    });

    it('should generate single password when count is 1', () => {
      const options: PasswordOptions = {
        length: 8,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: false,
        includeSymbols: false,
      };

      const passwords = generateMultiplePasswords(options, 1);
      expect(passwords).toHaveLength(1);
      expect(passwords[0]).toHaveLength(8);
    });

    it('should handle large count', () => {
      const options: PasswordOptions = {
        length: 10,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: false,
      };

      const passwords = generateMultiplePasswords(options, 100);
      expect(passwords).toHaveLength(100);
      
      passwords.forEach(password => {
        expect(password).toHaveLength(10);
      });
    });
  });

  describe('validatePasswordOptions', () => {
    it('should validate correct options', () => {
      const options: PasswordOptions = {
        length: 12,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: false,
      };

      expect(validatePasswordOptions(options)).toBe(true);
    });

    it('should validate options with custom characters', () => {
      const options: PasswordOptions = {
        length: 8,
        includeUppercase: false,
        includeLowercase: false,
        includeNumbers: false,
        includeSymbols: false,
        customCharacters: 'ABC123',
      };

      expect(validatePasswordOptions(options)).toBe(true);
    });

    it('should reject options with no character types', () => {
      const options: PasswordOptions = {
        length: 12,
        includeUppercase: false,
        includeLowercase: false,
        includeNumbers: false,
        includeSymbols: false,
      };

      expect(validatePasswordOptions(options)).toBe(false);
    });

    it('should reject options with invalid length', () => {
      const options: PasswordOptions = {
        length: 3,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: false,
      };

      expect(validatePasswordOptions(options)).toBe(false);
    });

    it('should reject options with excessive length', () => {
      const options: PasswordOptions = {
        length: 200,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: false,
      };

      expect(validatePasswordOptions(options)).toBe(false);
    });

    it('should reject options with empty custom characters', () => {
      const options: PasswordOptions = {
        length: 12,
        includeUppercase: false,
        includeLowercase: false,
        includeNumbers: false,
        includeSymbols: false,
        customCharacters: '',
      };

      expect(validatePasswordOptions(options)).toBe(false);
    });

    it('should accept minimum valid length', () => {
      const options: PasswordOptions = {
        length: 4,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: false,
      };

      expect(validatePasswordOptions(options)).toBe(true);
    });

    it('should accept maximum valid length', () => {
      const options: PasswordOptions = {
        length: 128,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: false,
      };

      expect(validatePasswordOptions(options)).toBe(true);
    });
  });

  describe('edge cases', () => {
    it('should handle very long passwords', () => {
      const options: PasswordOptions = {
        length: 50,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: true,
      };

      const password = generatePassword(options);
      expect(password).toHaveLength(50);
    });

    it('should handle minimum length with all character types', () => {
      const options: PasswordOptions = {
        length: 4,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: true,
      };

      const password = generatePassword(options);
      expect(password).toHaveLength(4);
      expect(password).toMatch(/[A-Z]/);
      expect(password).toMatch(/[a-z]/);
      expect(password).toMatch(/[0-9]/);
      expect(password).toMatch(/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/);
    });

    it('should handle special characters in exclude list', () => {
      const options: PasswordOptions = {
        length: 20,
        includeUppercase: true,
        includeLowercase: true,
        includeNumbers: true,
        includeSymbols: true,
        excludeCharacters: '!@#$%^&*()',
      };

      const password = generatePassword(options);
      expect(password).toHaveLength(20);
      expect(password).not.toMatch(/[!@#$%^&*()]/);
    });

    it('should handle unicode characters', () => {
      const options: PasswordOptions = {
        length: 10,
        includeUppercase: false,
        includeLowercase: false,
        includeNumbers: false,
        includeSymbols: false,
        customCharacters: 'αβγδεζηθικλμνξοπρστυφχψω',
      };

      const password = generatePassword(options);
      expect(password).toHaveLength(10);
      expect(password).toMatch(/^[αβγδεζηθικλμνξοπρστυφχψω]+$/);
    });
  });
});
