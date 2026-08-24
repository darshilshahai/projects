ANALYSIS_TOOLS = [
    {
        "type": "function",
        "name": "execute_sql",
        "description": (
            "Execute a read-only DuckDB SQL query against the uploaded "
            "dataset when the user wants a textual or tabular analytical "
            "answer and does not need a chart."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "A single read-only DuckDB SQL query. "
                        "The uploaded dataset is available as table "
                        "'dataset'."
                    ),
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "create_chart",
        "description": (
            "Execute an analytical SQL query and create a visualization "
            "from the real query result. Use this when the user explicitly "
            "asks for a chart, graph, plot, visualization, trend, comparison "
            "chart, distribution chart, or relationship plot."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "A single read-only DuckDB query that returns the "
                        "data required for the chart."
                    ),
                },
                "chart_type": {
                    "type": "string",
                    "enum": [
                        "bar",
                        "line",
                        "pie",
                        "scatter",
                    ],
                    "description": ("The visualization type."),
                },
                "x": {
                    "type": "string",
                    "description": (
                        "The exact SQL result column to use as the chart "
                        "x-axis or category/name field."
                    ),
                },
                "y": {
                    "type": "string",
                    "description": (
                        "The exact SQL result column to use as the chart "
                        "y-axis or value field."
                    ),
                },
                "title": {
                    "type": "string",
                    "description": ("A concise descriptive chart title."),
                },
                "x_label": {
                    "type": [
                        "string",
                        "null",
                    ],
                    "description": ("Optional readable x-axis label."),
                },
                "y_label": {
                    "type": [
                        "string",
                        "null",
                    ],
                    "description": ("Optional readable y-axis label."),
                },
            },
            "required": [
                "query",
                "chart_type",
                "x",
                "y",
                "title",
                "x_label",
                "y_label",
            ],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "ask_clarification",
        "description": (
            "Ask for one missing piece of information when multiple "
            "reasonable interpretations could materially change the answer. "
            "Whenever possible provide 2 to 4 short choices based on the "
            "dataset schema."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": ("A short, user-friendly clarification question."),
                },
                "options": {
                    "type": "array",
                    "description": ("2 to 4 concise choices."),
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {
                                "type": "string",
                            },
                            "value": {
                                "type": "string",
                            },
                        },
                        "required": [
                            "label",
                            "value",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": [
                "question",
                "options",
            ],
            "additionalProperties": False,
        },
    },
]
