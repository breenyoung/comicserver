from lxml import etree
from typing import Optional, Dict, Any


def parse_comicinfo(xml_content: bytes) -> Dict[str, Any]:
    """Parse ComicInfo.xml and return structured data"""
    try:
        root = etree.fromstring(xml_content)

        # Helper to get text or None
        def get_text(element_name: str) -> Optional[str]:
            elem = root.find(element_name)
            return elem.text if elem is not None else None

        return {
            'series': get_text('Series'),
            'number': get_text('Number'),
            'volume': get_text('Volume'),
            'title': get_text('Title'),
            'summary': get_text('Summary'),
            'year': get_text('Year'),
            'month': get_text('Month'),
            'writer': get_text('Writer'),
            'penciller': get_text('Penciller'),
            'publisher': get_text('Publisher'),
            'page_count': get_text('PageCount'),

            # For reading lists
            'alternate_series': get_text('AlternateSeries'),
            'alternate_number': get_text('AlternateNumber'),
            'story_arc': get_text('StoryArc'),

            # Store full XML for future use
            'raw_xml': xml_content.decode('utf-8')
        }
    except Exception as e:
        print(f"Error parsing ComicInfo.xml: {e}")
        return {}