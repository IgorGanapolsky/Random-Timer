/**
 * Simple Hello World Function
 * Created to test GitButler + Claude Code integration
 */

/**
 * Generates a personalized greeting message
 * @param {string} name - The name of the person to greet
 * @returns {string} A friendly greeting message
 */
function hello(name) {
    if (!name || typeof name !== 'string') {
        return 'Hello, World!';
    }
    
    return `Hello, ${name}! Welcome to the GitButler + Claude Code integration test.`;
}

/**
 * Example usage of the hello function
 */
function demonstrateHello() {
    console.log(hello());                    // "Hello, World!"
    console.log(hello('Alice'));             // "Hello, Alice! Welcome to..."
    console.log(hello('GitButler User'));    // "Hello, GitButler User! Welcome to..."
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { hello, demonstrateHello };
}

// Run demonstration if this file is executed directly
if (require.main === module) {
    demonstrateHello();
}
