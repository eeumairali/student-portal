"""Learning plans shown on the home page.

Edit session ranges or topics here; the template renders whatever is listed.
"""

LEARNING_PLANS = [
    {
        "track": "Foundations",
        "slug": "foundations",
        "intro": "Start here if you are new to programming, at any age.",
        "plans": [
            {"name": "Basic Python", "sessions": "6–10", "level": "Beginner",
             "covers": "Variables, input/output, if/else, loops, lists, dictionaries, functions and small games."},
            {"name": "Python for kids", "sessions": "8–12", "level": "Ages 10+",
             "covers": "Turtle graphics, simple games and puzzles that teach logic one step at a time."},
            {"name": "OOP and problem solving", "sessions": "4–6", "level": "After basics",
             "covers": "Classes, objects, files, errors and breaking bigger problems into clean code."},
        ],
    },
    {
        "track": "Data science",
        "slug": "data",
        "intro": "Turn raw data into answers and clear charts.",
        "plans": [
            {"name": "NumPy", "sessions": "2–4", "level": "After basics",
             "covers": "Arrays, indexing, vectorised maths and the ideas behind fast numeric Python."},
            {"name": "Pandas", "sessions": "4–8", "level": "After NumPy",
             "covers": "DataFrames, cleaning messy data, grouping, merging and real dataset analysis."},
            {"name": "Matplotlib and Seaborn", "sessions": "2–4", "level": "With Pandas",
             "covers": "Line, bar and scatter plots, styling, and telling a story with charts."},
        ],
    },
    {
        "track": "Machine learning and AI",
        "slug": "ml",
        "intro": "Build models and understand why they work.",
        "plans": [
            {"name": "Scikit-learn", "sessions": "6–10", "level": "After Pandas",
             "covers": "Regression, classification, clustering, model evaluation and pipelines."},
            {"name": "PyTorch", "sessions": "8–12", "level": "After Scikit-learn",
             "covers": "Tensors, autograd, neural networks, training loops and CNNs."},
            {"name": "TensorFlow and Keras", "sessions": "6–10", "level": "After Scikit-learn",
             "covers": "Sequential and functional models, callbacks and deploying a trained model."},
            {"name": "Computer vision", "sessions": "6–10", "level": "After PyTorch",
             "covers": "OpenCV, image processing, object detection and real-world projects."},
        ],
    },
    {
        "track": "Web development",
        "slug": "web",
        "intro": "Ship real web apps and APIs with Python.",
        "plans": [
            {"name": "Flask", "sessions": "4–6", "level": "After basics",
             "covers": "Routes, templates, forms, a database and deploying a small app."},
            {"name": "FastAPI", "sessions": "4–6", "level": "After basics",
             "covers": "REST APIs, Pydantic validation, async endpoints and auto-generated docs."},
            {"name": "Django", "sessions": "8–12", "level": "After OOP",
             "covers": "Models, admin, authentication, views and templates, and a full deployed project."},
        ],
    },
]
