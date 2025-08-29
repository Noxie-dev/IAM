#!/bin/bash

echo "🧹 Starting project cleanup..."

# Remove build artifacts
echo "📦 Removing build artifacts..."
rm -rf ./iam-frontend/dist
rm -rf ./iam-frontend/build
rm -rf ./.next
rm -rf ./out

# Remove Firebase cache
echo "🔥 Removing Firebase cache..."
rm -rf ./.firebase

# Remove test results
echo "🧪 Removing test results..."
rm -f ./TEST_RESULTS_SUMMARY.md
rm -rf ./test-results
rm -f ./test-report.html

# Remove temporary files
echo "🗑️ Removing temporary files..."
find . -name "*.tmp" -delete
find . -name "*.temp" -delete
find . -name "*.cache" -delete
find . -name "*.log" -delete

# Remove OS generated files
echo "💻 Removing OS generated files..."
find . -name ".DS_Store" -delete
find . -name "Thumbs.db" -delete

# Clean npm cache (optional - uncomment if needed)
# echo "🧹 Cleaning npm cache..."
# npm cache clean --force

# Remove node_modules and reinstall (optional - uncomment if needed)
# echo "📦 Removing and reinstalling node_modules..."
# rm -rf ./iam-frontend/node_modules
# cd ./iam-frontend && npm ci && cd ..

echo "✅ Cleanup completed!"
echo ""
echo "📊 Project size after cleanup:"
du -sh . --exclude=.git

echo ""
echo "💡 Recommendations:"
echo "1. Run 'npm ci' instead of 'npm install' for faster, cleaner installs"
echo "2. Consider using 'npm prune' to remove unused dependencies"
echo "3. Review package.json for unused dependencies"
echo "4. Consider implementing tree-shaking for smaller bundle sizes"
