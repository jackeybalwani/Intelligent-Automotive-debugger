module.exports = {
  extends: [
    'react-app',
    'react-app/jest',
  ],
  rules: {
    // General rules
    'no-console': 'warn',
    'no-debugger': 'error',
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
};