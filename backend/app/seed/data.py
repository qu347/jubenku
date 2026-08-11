from typing import Any


DEFAULT_GENRE_MODULES: list[dict[str, Any]] = [
    {"name": "西方奇幻", "slug": "western-fantasy", "icon": "MagicStick", "theme_color": "#8b5cf6"},
    {"name": "东方仙侠", "slug": "eastern-xianxia", "icon": "Sunrise", "theme_color": "#22c55e"},
    {"name": "科幻末世", "slug": "sci-fi-apocalypse", "icon": "Cpu", "theme_color": "#06b6d4"},
    {"name": "都市日常", "slug": "urban-daily", "icon": "OfficeBuilding", "theme_color": "#3b82f6"},
    {"name": "都市修真", "slug": "urban-cultivation", "icon": "Lightning", "theme_color": "#14b8a6"},
    {"name": "都市高武", "slug": "urban-martial", "icon": "Trophy", "theme_color": "#f97316"},
    {"name": "历史古代", "slug": "historical-ancient", "icon": "Reading", "theme_color": "#d97706"},
    {"name": "战神赘婿", "slug": "war-god-son-in-law", "icon": "Medal", "theme_color": "#ef4444"},
    {"name": "都市种田", "slug": "urban-farming", "icon": "Cherry", "theme_color": "#84cc16"},
    {"name": "传统玄幻", "slug": "classic-fantasy", "icon": "Moon", "theme_color": "#a855f7"},
    {"name": "历史脑洞", "slug": "historical-what-if", "icon": "Compass", "theme_color": "#eab308"},
    {"name": "悬疑脑洞", "slug": "mystery-what-if", "icon": "View", "theme_color": "#6366f1"},
    {"name": "都市脑洞", "slug": "urban-what-if", "icon": "Opportunity", "theme_color": "#0ea5e9"},
    {"name": "玄幻脑洞", "slug": "fantasy-what-if", "icon": "Connection", "theme_color": "#c026d3"},
    {"name": "悬疑灵异", "slug": "supernatural-mystery", "icon": "ColdDrink", "theme_color": "#64748b"},
]


DEFAULT_SECTIONS: list[dict[str, Any]] = [
    {"section_key": "title", "section_name": "标题", "icon": "Document", "field_schema": []},
]
