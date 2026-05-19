name: 🔧 Weekly Deep SEO & Maintenance

on:
  schedule:
    - cron: '0 23 * * 0'
  workflow_dispatch:

jobs:
  weekly-deep-maintenance:
    name: Weekly Deep SEO Audit & Fix
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: ⬇️ Checkout
        uses: actions/checkout@v4

      - name: 🐍 Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: 📦 Install dependencies
        run: pip install anthropic requests --quiet

      - name: 🔍 Deep SEO Audit + AI Fix
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python3 scripts/weekly_seo_audit.py

      - name: 📅 Update All Dates
        run: |
          TODAY=$(date +%Y-%m-%d)
          sed -i "s|<lastmod>[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}</lastmod>|<lastmod>$TODAY</lastmod>|g" sitemap.xml
          sed -i 's|"dateModified": "[0-9-]*"|"dateModified": "'"$TODAY"'"|g' index.html
          for f in blog/*.html kta.html; do [ -f "$f" ] && sed -i 's|"dateModified": "[0-9-]*"|"dateModified": "'"$TODAY"'"|g' "$f"; done
          echo "✅ All dates updated to $TODAY"

      - name: 📤 Commit Weekly Changes
        run: |
          git config user.name "🤖 Salut AI Bot"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          if ! git diff --staged --quiet; then
            git commit -m "🔧 Weekly Deep Maintenance [$(date +%Y-%m-%d)]"
            git push
          fi
