import tomllib
from dataclasses import dataclass, field
from typing import List, Optional

from tinyhtml import html, h, frag, raw


VALID_ALIGNMENTS = {"left", "center", "right"}


@dataclass
class Item:
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    icon: Optional[str] = None
    icon_align: Optional[str] = None
    embed_url: Optional[str] = None
    embed_height: str = "315"


@dataclass
class Section:
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None
    icon_size: str = "24px"
    direction: str = "column"
    item_style: str = "outline"
    items: List[Item] = field(default_factory=list)


@dataclass
class Data:
    name: str
    base_url: str
    sections: List[Section] = field(default_factory=list)
    description: Optional[str] = None
    keywords: Optional[str] = None
    image: Optional[str] = None
    theme: str = "dark"
    primary_color: str = "#546e7a"
    text_align: str = "center"
    icon_align: str = "center"
    gtag_id: Optional[str] = None


def normalize_alignment(
    value: Optional[str],
    default: str = "center",
) -> str:
    if not value:
        return default

    normalized_value = value.strip().lower()

    if normalized_value not in VALID_ALIGNMENTS:
        return default

    return normalized_value


def load_data(file_path):
    with open(file_path, "rb") as f:
        raw_data = tomllib.load(f)

    return Data(
        name=raw_data["name"],
        description=raw_data.get("description"),
        keywords=raw_data.get("keywords"),
        base_url=raw_data["base_url"],
        image=raw_data.get("image"),
        theme=raw_data.get("theme", "dark"),
        primary_color=raw_data.get("primary_color", "#546e7a"),
        text_align=normalize_alignment(
            raw_data.get("text_align"),
            default="center",
        ),
        icon_align=normalize_alignment(
            raw_data.get("icon_align"),
            default="center",
        ),
        gtag_id=raw_data.get("gtag_id"),
        sections=[
            Section(
                title=section.get("title"),
                description=section.get("description"),
                icon=section.get("icon"),
                icon_size=section.get("icon_size", "24px"),
                direction=section.get("direction", "column"),
                item_style=section.get("item_style", "outline"),
                items=[
                    Item(
                        title=item.get("title"),
                        description=item.get("description"),
                        url=item.get("url"),
                        icon=item.get("icon"),
                        icon_align=(
                            normalize_alignment(item.get("icon_align"))
                            if item.get("icon_align")
                            else None
                        ),
                        embed_url=item.get("embed_url"),
                        embed_height=item.get("embed_height", "315"),
                    )
                    for item in section.get("items", [])
                ],
            )
            for section in raw_data.get("sections", [])
        ],
    )


def create_section(
    section: Section,
    default_icon_align: str,
):
    items = frag(
        h(
            "div",
            klass="item",
            style=f"width: {'100%' if section.direction == 'column' else 'unset'}",
        )(
            h(
                "a",
                role="button",
                klass=f"{'outline' if section.item_style == 'outline' else ''}",
                href=item.url,
                target="_blank",
                data_icon_align=normalize_alignment(
                    item.icon_align or default_icon_align
                ),
            )(
                h(
                    "img",
                    klass="icon",
                    src=item.icon,
                    alt=item.title,
                    style=f"width: {section.icon_size};",
                )
                if item.icon
                else None,
                h("hgroup", klass="item-text")(
                    h("h4")(item.title),
                    h("h5")(item.description),
                ),
            )
            if item.url
            else raw(
                f"""
                    <iframe
                        src="{item.embed_url}"
                        height="{item.embed_height}"
                        frameborder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowfullscreen="true"
                    >
                    </iframe>
                """
            )
            if item.embed_url
            else None
        )
        for item in section.items
    )

    return h("div", klass="section")(
        h("hgroup")(
            h("h3")(section.title),
            h("p")(section.description),
        ),
        h(
            "div",
            klass="items",
            style=f"flex-direction: {section.direction}",
        )(items),
    )


def create_meta_tags(data: Data):
    return frag(
        h("title")(data.name),
        h("meta", name="description", content=data.description),
        h("meta", name="keywords", content=data.keywords),
        h(
            "meta",
            name="viewport",
            content="width=device-width, initial-scale=1",
        ),
        h("meta", charset="utf-8"),
        h("meta", property="og:title", content=data.name),
        h(
            "meta",
            property="og:description",
            content=data.description,
        ),
        h(
            "meta",
            property="og:image",
            content=f"{data.base_url}/img/{data.image}",
        ),
        h("meta", name="twitter:title", content=data.name),
        h(
            "meta",
            name="twitter:description",
            content=data.description,
        ),
        h(
            "meta",
            name="twitter:image",
            content=f"{data.base_url}/img/{data.image}",
        ),
        h(
            "meta",
            name="twitter:card",
            content="summary_large_image",
        ),
    )


def create_head(data: Data):
    return h("head")(
        create_meta_tags(data),
        h(
            "link",
            rel="stylesheet",
            href="css/pico.min.css",
        ),
        h(
            "link",
            rel="stylesheet",
            href="css/style.css",
        ),
        h("style", rel="stylesheet")(
            f"""
                [data-theme="dark"],
                [data-theme="light"] {{
                    --primary: {data.primary_color} !important;
                }}

                h1,
                h2,
                h3,
                h4,
                h5,
                h6,
                p,
                small {{
                    text-align: {data.text_align};
                }}

                /*
                 * Preserve Pico's existing button appearance and colors.
                 * Only change how content is positioned inside item buttons.
                 */
                .item > a[role="button"] {{
                    display: grid;
                    grid-template-columns: 1fr auto 1fr;
                    align-items: center;
                    column-gap: 1rem;
                    width: 100%;
                }}

                /*
                 * The text always occupies the true middle column.
                 */
                .item > a[role="button"] > .item-text {{
                    grid-column: 2;
                    grid-row: 1;
                    margin: 0;
                    text-align: {data.text_align};
                }}

                .item > a[role="button"] > .item-text h4,
                .item > a[role="button"] > .item-text h5 {{
                    margin-left: 0;
                    margin-right: 0;
                    text-align: {data.text_align};
                }}

                /*
                 * Image position is independent from text alignment.
                 */
                .item > a[role="button"][data-icon-align="right"] > .icon {{
                    grid-column: 3;
                    grid-row: 1;
                    justify-self: end;
                }}

                .item > a[role="button"][data-icon-align="left"] > .icon {{
                    grid-column: 1;
                    grid-row: 1;
                    justify-self: start;
                }}

                .item > a[role="button"][data-icon-align="center"] > .icon {{
                    grid-column: 2;
                    grid-row: 1;
                    justify-self: center;
                }}

                /*
                 * When the image is centred, move the text below it so the
                 * image and text do not overlap.
                 */
                .item > a[role="button"][data-icon-align="center"] {{
                    grid-template-rows: auto auto;
                    row-gap: 0.5rem;
                }}

                .item > a[role="button"][data-icon-align="center"] > .item-text {{
                    grid-column: 1 / -1;
                    grid-row: 2;
                    justify-self: stretch;
                }}

                .item > a[role="button"] > .icon {{
                    display: block;
                    margin: 0;
                }}
            """
        ),
        raw(
            f"""
                <script
                    defer
                    src="https://analytics.thewefactor.ca/script.js"
                    data-website-id="{data.gtag_id}">
                </script>

                <script>
                    window.dataLayer = window.dataLayer || [];

                    function gtag() {{
                        dataLayer.push(arguments);
                    }}

                    gtag('js', new Date());
                    gtag('config', '{data.gtag_id}');
                </script>
            """
        )
        if data.gtag_id
        else None,
    )


def create_header(data: Data):
    return h("header", klass="container")(
        h("hgroup")(
            h(
                "img",
                klass="avatar",
                src=f"img/{data.image}",
                alt="avatar",
            ),
            h("h1")(data.name),
            h("p")(data.description)
            if data.description
            else None,
        )
    )


def create_footer():
    return h("footer", klass="container")(
        h("small")("Generated with "),
        h(
            "a",
            klass="",
            href="https://github.com/thevahidal/jake/",
            target="_blank",
        )("Jake"),
    )


def generate_html(data: Data):
    sections = frag(
        create_section(
            section,
            default_icon_align=data.icon_align,
        )
        for section in data.sections
    )

    return html(
        lang="en",
        data_theme=data.theme,
    )(
        create_head(data),
        h("body")(
            create_header(data),
            h("main", klass="container")(sections),
            create_footer(),
        ),
    ).render()


def main():
    data = load_data("data.toml")
    output = generate_html(data)

    with open(
        "dist/index.html",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(output)


if __name__ == "__main__":
    main()
