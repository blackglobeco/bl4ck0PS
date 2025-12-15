from dataclasses import dataclass
from typing import ClassVar, List, Dict, Any
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from .base import Transform
from entities.base import Entity
from entities.website import Website
from entities.username import Username
from ui.managers.status_manager import StatusManager

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5"
}

@dataclass
class UsernameSearch(Transform):
    name: ClassVar[str] = "Username Search"
    description: ClassVar[str] = "Search for websites and usernames using DuckDuckGo and social media platforms"
    input_types: ClassVar[List[str]] = ["Username"]
    output_types: ClassVar[List[str]] = ["Website", "Username"]
    
    async def run(self, entity: Username, graph) -> List[Entity]:
        """Async implementation"""
        if not isinstance(entity, Username):
            return []
        
        username = entity.properties.get("username", "")
        if not username:
            return []
        
        status = StatusManager.get()
        operation_id = status.start_loading("Username Search")
        
        try:
            status.set_text(f"Searching for username: {username}")
            
            # Run searches concurrently
            results = []
            
            # Search DuckDuckGo
            ddg_results = await self._search_duckduckgo(username)
            results.extend(ddg_results)
            
            # Check common social media platforms
            social_results = await self._check_social_platforms(username)
            results.extend(social_results)
            
            status.set_text(f"Found {len(results)} results for {username}")
            
            # Create entities from results
            entities = []
            for result in results:
                try:
                    entity_obj = self._create_entity(result)
                    if entity_obj:
                        entities.append(entity_obj)
                except Exception as e:
                    print(f"Error creating entity: {e}")
                    continue
            
            return entities
            
        except Exception as e:
            status.set_text(f"Username search failed: {str(e)}")
            return []
        finally:
            status.stop_loading(operation_id)

    async def _search_duckduckgo(self, username: str) -> List[Dict[str, Any]]:
        """Search DuckDuckGo for username (no API key needed)"""
        results = []
        search_url = f"https://html.duckduckgo.com/html/?q={username}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        
                        # Parse DuckDuckGo results
                        for result_div in soup.find_all("div", class_="result")[:10]:
                            try:
                                link = result_div.find("a", class_="result__a")
                                if link and link.get("href"):
                                    url = link["href"]
                                    title = link.get_text(strip=True)
                                    
                                    snippet_div = result_div.find("a", class_="result__snippet")
                                    description = snippet_div.get_text(strip=True) if snippet_div else ""
                                    
                                    results.append({
                                        "url": url,
                                        "title": title,
                                        "description": description,
                                        "source": "DuckDuckGo"
                                    })
                            except Exception as e:
                                print(f"Error parsing result: {e}")
                                continue
        except Exception as e:
            print(f"DuckDuckGo search failed: {str(e)}")
        
        return results

    async def _check_social_platforms(self, username: str) -> List[Dict[str, Any]]:
        """Check if username exists on common social platforms"""
        results = []
        
        # Common social media platforms
        platforms = [
            ("Instagram", f"https://www.instagram.com/{username}/"),
            ("Twitter/X", f"https://twitter.com/{username}"),
            ("GitHub", f"https://github.com/{username}"),
            ("Reddit", f"https://www.reddit.com/user/{username}"),
            ("TikTok", f"https://www.tiktok.com/@{username}"),
            ("LinkedIn", f"https://www.linkedin.com/in/{username}"),
            ("Facebook", f"https://www.facebook.com/{username}"),
            ("YouTube", f"https://www.youtube.com/@{username}"),
        ]
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for platform_name, url in platforms:
                tasks.append(self._check_url_exists(session, platform_name, url))
            
            platform_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in platform_results:
                if result and not isinstance(result, Exception):
                    results.append(result)
        
        return results

    async def _check_url_exists(self, session: aiohttp.ClientSession, platform: str, url: str) -> Dict[str, Any]:
        """Check if a URL exists and is accessible"""
        try:
            async with session.head(url, headers=headers, timeout=5, allow_redirects=True) as response:
                if response.status == 200:
                    return {
                        "url": url,
                        "title": f"{platform} Profile",
                        "description": f"Found profile on {platform}",
                        "source": "Platform Check"
                    }
        except Exception:
            pass
        
        return None

    def _create_entity(self, result: Dict[str, Any]) -> Entity:
        """Create appropriate entity from search result"""
        url = result["url"]
        
        try:
            # Parse domain from URL
            if "://" in url:
                domain = url.split("://")[1].split("/")[0]
            else:
                domain = url.split("/")[0]
            
            # Remove www. prefix
            domain = domain.replace("www.", "")
            
            # Detect social media platforms and create Username entities
            if "instagram.com" in domain:
                username = url.split("instagram.com/")[-1].split("/")[0].split("?")[0]
                if username and username not in ["p", "stories", "reel", "tv"]:
                    return Username(properties={
                        "username": username,
                        "platform": "Instagram",
                        "link": url,
                        "source": f"Username Search ({result['source']})"
                    })
            
            elif "twitter.com" in domain or "x.com" in domain:
                username = url.split("/")[-1].split("?")[0]
                if username and "/status/" not in url:
                    return Username(properties={
                        "username": username,
                        "platform": "Twitter/X",
                        "link": url,
                        "source": f"Username Search ({result['source']})"
                    })
            
            elif "github.com" in domain:
                username = url.split("github.com/")[-1].split("/")[0].split("?")[0]
                if username:
                    return Username(properties={
                        "username": username,
                        "platform": "GitHub",
                        "link": url,
                        "source": f"Username Search ({result['source']})"
                    })
            
            elif "reddit.com" in domain:
                if "/user/" in url:
                    username = url.split("/user/")[-1].split("/")[0].split("?")[0]
                    if username:
                        return Username(properties={
                            "username": username,
                            "platform": "Reddit",
                            "link": url,
                            "source": f"Username Search ({result['source']})"
                        })
            
            elif "tiktok.com" in domain:
                username = url.split("@")[-1].split("/")[0].split("?")[0]
                if username and username != "tiktok.com":
                    return Username(properties={
                        "username": username,
                        "platform": "TikTok",
                        "link": url,
                        "source": f"Username Search ({result['source']})"
                    })
            
            elif "linkedin.com" in domain:
                if "/in/" in url:
                    username = url.split("/in/")[-1].split("/")[0].split("?")[0]
                    if username:
                        return Username(properties={
                            "username": username,
                            "platform": "LinkedIn",
                            "link": url,
                            "source": f"Username Search ({result['source']})"
                        })
            
            elif "facebook.com" in domain:
                username = url.split("facebook.com/")[-1].split("/")[0].split("?")[0]
                if username and username not in ["pages", "groups", "events"]:
                    return Username(properties={
                        "username": username,
                        "platform": "Facebook",
                        "link": url,
                        "source": f"Username Search ({result['source']})"
                    })
            
            elif "youtube.com" in domain:
                if "/@" in url:
                    username = url.split("/@")[-1].split("/")[0].split("?")[0]
                    if username:
                        return Username(properties={
                            "username": username,
                            "platform": "YouTube",
                            "link": url,
                            "source": f"Username Search ({result['source']})"
                        })
            
            # Default: create Website entity
            return Website(properties={
                "url": url,
                "domain": domain,
                "title": result.get("title", domain),
                "description": result.get("description", ""),
                "source": f"Username Search ({result['source']})"
            })
            
        except Exception as e:
            print(f"Error creating entity for {url}: {e}")
            # Fallback to Website entity
            return Website(properties={
                "url": url,
                "domain": "unknown",
                "title": result.get("title", url),
                "description": result.get("description", ""),
                "source": f"Username Search ({result['source']})"
            })