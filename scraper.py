import asyncio
from playwright.async_api import async_playwright

async def scrape_company(website: str) -> dict:
    """Lightweight browser scraping optimized for 512MB RAM environments."""
    async with async_playwright() as p:
        # CRITICAL: These flags prevent OOM kills on Render free tier
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage',  # Use /tmp instead of /dev/shm
                '--single-process',         # Reduce memory footprint
                '--no-sandbox',
                '--disable-gpu',
                '--disable-extensions'
            ]
        )
        context = await browser.new_context(
            viewport={'width': 800, 'height': 600},  # Small viewport = less RAM
            user_agent='Mozilla/5.0 (compatible; LH2Bot/1.0)'
        )
        page = await context.new_page()

        try:
            await page.goto(website, timeout=20000, wait_until='domcontentloaded')
            title = await page.title()

            # Extract meta description OR first meaningful paragraph
            desc = await page.evaluate('''() => {
                const meta = document.querySelector("meta[name='description']");
                if (meta?.content) return meta.content;
                const p = document.querySelector("article p, main p, .about p, p");
                return p?.innerText || "";
            }''')

            return {"title": title, "description": desc[:600], "source": "browser"}
        except Exception as e:
            return {"error": str(e)[:200], "source": "browser"}
        finally:
            await context.close()
            await browser.close()
