# ashutosh0804k.github.io

[![site-tests](https://github.com/ashutosh0804k/ashutosh0804k.github.io/actions/workflows/site-tests.yml/badge.svg)](https://github.com/ashutosh0804k/ashutosh0804k.github.io/actions/workflows/site-tests.yml)

My portfolio site: **https://ashutosh0804k.github.io/**

It's a single static page, and like anything I ship, it's tested. A Playwright suite runs on every push and weekly:

- **Links:** every in-page link has a target, every local file the page references exists, and every external link resolves
- **Accessibility:** no serious or critical [axe](https://github.com/dequelabs/axe-core) violations. Its first run caught low-contrast text on the skill tags, badge, and footer, which are now fixed.
- **Mobile:** no horizontal scroll at phone, tablet, and desktop widths; the menu opens, navigates, and closes; the resume button is visible without scrolling on a phone
- **Content:** the resume downloads as a real PDF, local images render, share-preview tags point to real files, and the hero terminal replay finishes

```bash
pip install -r tests/requirements.txt
playwright install chromium
pytest                      # everything
pytest -m "not external"    # skip checks that need internet
```
