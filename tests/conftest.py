"""Shared pytest setup — loads .env so live API tests can find their keys."""
try:
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv())
except ImportError:
    pass
