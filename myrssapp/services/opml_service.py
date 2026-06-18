"""OPML 2.0 import/export service."""

import xml.etree.ElementTree as ET
from pathlib import Path

from ..database.connection import DatabaseConnection
from ..services.feed_service import FeedService
from ..services.fetch_service import FetchService


class OPMLService:
    """Handles OPML 2.0 import and export of feed subscriptions."""

    OPML_VERSION = "2.0"

    def __init__(self, db: DatabaseConnection):
        self._db = db
        self._feed_service = FeedService(db)
        self._fetch_service = FetchService(db)

    def export_opml(self, file_path: str) -> None:
        """Export all feeds as an OPML 2.0 document."""
        feeds = self._feed_service.get_all_feeds(include_disabled=True)
        categories = self._feed_service.get_all_categories()

        root = ET.Element("opml", version=self.OPML_VERSION)
        head = ET.SubElement(root, "head")
        ET.SubElement(head, "title").text = "MyRssApp Subscriptions"
        ET.SubElement(head, "dateCreated").text = feeds[0].created_at if feeds else ""

        body = ET.SubElement(root, "body")

        # Category outlines
        for cat in categories:
            cat_outline = ET.SubElement(
                body, "outline",
                text=cat.name,
                title=cat.name,
            )
            cat_feeds = [f for f in feeds if f.category_id == cat.id]
            for feed in cat_feeds:
                ET.SubElement(
                    cat_outline, "outline",
                    type="rss",
                    text=feed.title,
                    title=feed.title,
                    xmlUrl=feed.url,
                    htmlUrl=feed.site_url,
                )

        # Uncategorized feeds
        for feed in feeds:
            if feed.category_id is None:
                ET.SubElement(
                    body, "outline",
                    type="rss",
                    text=feed.title,
                    title=feed.title,
                    xmlUrl=feed.url,
                    htmlUrl=feed.site_url,
                )

        # Write to file
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(file_path, encoding="utf-8", xml_declaration=True)

    def import_opml(self, file_path: str) -> int:
        """Import feeds from an OPML 2.0 file. Returns count of imported feeds."""
        tree = ET.parse(file_path)
        root = tree.getroot()
        body = root.find("body")
        if body is None:
            return 0

        count = 0

        def process_outline(outline_elem, category_id=None):
            nonlocal count
            xml_url = outline_elem.get("xmlUrl")
            if xml_url:
                # This is a feed
                title = outline_elem.get("title") or outline_elem.get("text") or xml_url
                existing = self._feed_service.get_feed_by_url(xml_url)
                if not existing:
                    feed = self._feed_service.add_feed(xml_url, category_id)
                    # Try to fetch metadata
                    try:
                        parsed = self._fetch_service.fetch_feed_only(xml_url)
                        if parsed:
                            self._feed_service.update_feed_info(
                                feed.id, parsed.title, parsed.site_url, parsed.description
                            )
                    except Exception:
                        pass
                    count += 1
            else:
                # This is a category folder
                cat_name = outline_elem.get("text") or outline_elem.get("title") or "Imported"
                categories = self._feed_service.get_all_categories()
                matching = [c for c in categories if c.name == cat_name]
                if matching:
                    cat_id = matching[0].id
                else:
                    cat = self._feed_service.add_category(cat_name)
                    cat_id = cat.id

                for child in outline_elem.findall("outline"):
                    process_outline(child, cat_id)

        for outline in body.findall("outline"):
            process_outline(outline)

        return count
