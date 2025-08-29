#!/bin/bash

echo "🔍 Analyzing project dependencies..."

cd ./iam-frontend

echo ""
echo "📦 Package Manager:"
echo "Using: $(npm --version)"
echo "Package manager specified: $(grep 'packageManager' package.json | cut -d'"' -f4)"

echo ""
echo "📊 Dependencies Analysis:"
echo "Total dependencies: $(npm list --depth=0 --json | jq '.dependencies | keys | length')"
echo "Total devDependencies: $(npm list --depth=0 --json | jq '.devDependencies | keys | length')"

echo ""
echo "📈 Bundle Size Analysis:"
echo "Node modules size: $(du -sh node_modules | cut -f1)"
echo "Package-lock.json size: $(du -sh package-lock.json | cut -f1)"

echo ""
echo "🔍 Potential Issues:"

# Check for duplicate packages
echo "Checking for duplicate packages..."
npm ls | grep "UNMET PEER DEPENDENCY" || echo "✅ No unmet peer dependencies found"

# Check for outdated packages
echo ""
echo "Checking for outdated packages..."
npm outdated || echo "✅ All packages are up to date"

# Check for unused dependencies (requires depcheck)
echo ""
echo "💡 To check for unused dependencies, install and run:"
echo "npm install -g depcheck"
echo "depcheck"

echo ""
echo "💡 To optimize node_modules:"
echo "npm prune"
echo "npm dedupe"

echo ""
echo "💡 To clean install:"
echo "rm -rf node_modules package-lock.json"
echo "npm ci"

cd ..
