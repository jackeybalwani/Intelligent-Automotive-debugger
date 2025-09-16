module.exports = {
  extends: [
    'react-app',
    'react-app/jest',
  ],
  rules: {
    // General rules
    'no-console': 'off',  // Disable for debugging
    'no-debugger': 'error',
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
};