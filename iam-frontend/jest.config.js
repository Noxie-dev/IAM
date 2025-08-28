export default {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  transform: {
    '^.+\\.(js|jsx)$': ['babel-jest', { presets: ['@babel/preset-env', '@babel/preset-react'] }],
  },
  moduleFileExtensions: ['js', 'jsx'],
  testMatch: ['**/__tests__/**/*.(js|jsx)', '**/*.(test|spec).(js|jsx)'],
  collectCoverageFrom: [
    'src/**/*.(js|jsx)',
    '!src/main.jsx',
    '!src/setupTests.js',
  ],
  transformIgnorePatterns: [
    'node_modules/(?!(lucide-react)/)',
  ],
  testTimeout: 10000,
};
