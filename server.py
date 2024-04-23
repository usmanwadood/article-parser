import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup

app = FastAPI()

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Be sure to restrict origins in production for security reasons
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/fetch/")
async def fetch_url(url: str):
    logger.info(f"Fetching URL: {url}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.RequestError as e:
        logger.error(f"Request error for {url}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"An error occurred while requesting {url}.") from e
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP status error for {url}: {str(e)}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Error response {e.response.status_code} while requesting {url}.") from e

    # Parsing the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract title
    title = soup.title.string if soup.title else None

    # Extract headings
    headings = {f"h{level}": [h.get_text(strip=True) for h in soup.find_all(f"h{level}")]
                for level in range(1, 7)}

    # Extract author
    author = None
    # Typical places where author might be found
    if soup.find('meta', attrs={"name": "author"}):
        author = soup.find('meta', attrs={"name": "author"})['content']
    elif soup.find('meta', property="article:author"):
        author = soup.find('meta', property="article:author")['content']

    # Extract images
    images = [img['src'] for img in soup.find_all('img') if 'src' in img.attrs]

    text = soup.get_text(separator=' ', strip=True)
    
    # Include raw HTML in the response
    raw_html = response.text
    
    logger.info(f"Content fetched successfully for {url}")
    return {
        "url": url,
        "title": title,
        "headings": headings,
        "author": author,
        "images": images,
        "content": text,
        "html": raw_html  # Send raw HTML to client
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
