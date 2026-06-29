"""A minimal but realistic nyaa RSS document for tests."""


def make_rss(items):
    body = "".join(items)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:nyaa="https://nyaa.si/xmlns/nyaa">\n'
        "<channel>\n"
        "<title>Nyaa - test - Torrent File RSS</title>\n"
        "<link>https://nyaa.si/</link>\n" + body + "</channel>\n</rss>\n"
    )


def make_item(
    title="Example Release 1080p",
    tid="2126378",
    infohash="0123456789abcdef0123456789abcdef01234567",
    size="1.4 GiB",
    seeders="42",
    leechers="3",
    pubdate="Sun, 28 Jun 2026 12:34:56 -0000",
):
    return (
        "<item>\n"
        "<title>{title}</title>\n"
        "<link>https://nyaa.si/download/{tid}.torrent</link>\n"
        "<guid isPermaLink=\"true\">https://nyaa.si/view/{tid}</guid>\n"
        "<pubDate>{pubdate}</pubDate>\n"
        "<nyaa:seeders>{seeders}</nyaa:seeders>\n"
        "<nyaa:leechers>{leechers}</nyaa:leechers>\n"
        "<nyaa:downloads>100</nyaa:downloads>\n"
        "<nyaa:infoHash>{infohash}</nyaa:infoHash>\n"
        "<nyaa:categoryId>1_2</nyaa:categoryId>\n"
        "<nyaa:category>Anime - English-translated</nyaa:category>\n"
        "<nyaa:size>{size}</nyaa:size>\n"
        "</item>\n"
    ).format(
        title=title,
        tid=tid,
        infohash=infohash,
        size=size,
        seeders=seeders,
        leechers=leechers,
        pubdate=pubdate,
    )


# A two-result feed with deliberately out-of-order seeders to test sorting.
SAMPLE_RSS = make_rss(
    [
        make_item(title="Low Seeded Release", tid="1", seeders="5", leechers="1"),
        make_item(title="High Seeded Release", tid="2", seeders="99", leechers="7"),
    ]
)
