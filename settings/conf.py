from pathlib import Path

from decouple import Config, Csv, RepositoryEnv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = BASE_DIR / 'settings' / '.env'

config = Config(RepositoryEnv(str(ENV_FILE_PATH)))

ENV_ID_LOCAL = 'local'
ENV_ID_PROD = 'prod'
DEFAULT_ALLOWED_HOSTS = 'localhost,127.0.0.1'
DEFAULT_DB_PORT = '5432'

ENV_ID: str = config('BLOG_ENV_ID', default=ENV_ID_LOCAL)
SECRET_KEY: str = config('BLOG_SECRET_KEY')
ALLOWED_HOSTS: list[str] = config(
    'BLOG_ALLOWED_HOSTS', default=DEFAULT_ALLOWED_HOSTS, cast=Csv()
)

DB_NAME: str = config('BLOG_DB_NAME', default='')
DB_USER: str = config('BLOG_DB_USER', default='')
DB_PASSWORD: str = config('BLOG_DB_PASSWORD', default='')
DB_HOST: str = config('BLOG_DB_HOST', default='')
DB_PORT: str = config('BLOG_DB_PORT', default=DEFAULT_DB_PORT)