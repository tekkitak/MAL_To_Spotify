from flask import Flask
from typing import cast
import click
from flask.cli import with_appcontext
from model.database import db, DB_VER
from model.version_control import VersionControl
from os import getenv, system, path, makedirs
from shutil import copyfile
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists

SQLEngine = create_engine(getenv('DATABASE_URL'))
ver_control = VersionControl()


def register_commands(app: Flask):
    @app.cli.command(help='Setup python')
    @with_appcontext
    def setup():
        system('pip install -r requirements.txt')
        if input('Do you want to change .env? [y/N] ').lower() == 'y':
            copyfile('.env', '.env.bak')
            copyfile('example.env', '.env')
        print('Python setup complete')

    @app.cli.command(help='Initialize the database')
    @with_appcontext
    def db_init():
        if not database_exists(SQLEngine.url):
            db.create_all()

        ver_control.update('db_ver', str(DB_VER))
        ver_control.save()
        click.echo('Database initialized')

    @app.cli.command(help='Drop the database')
    @with_appcontext
    def db_drop():
        db.drop_all()

        ver_control.update('db_ver', None)
        ver_control.save()
        click.echo('Database dropped')

    @app.cli.command(help='Archive the database')
    @with_appcontext
    @click.argument('archive_name')
    def db_archive(archive_name: str):
        if not path.exists('archive'):
            makedirs('archive')
        if not archive_name.endswith('.sqlite3'):
            archive_name += '.sqlite3'
        db_url: str = "instance/" + cast(str, getenv('DATABASE_URL'))[10:]
        copyfile(db_url, f'archive/{archive_name}')
        system(f"sqlite3 archive/{archive_name} 'VACUUM;'")
        system(f"sqlite3 archive/{archive_name} 'PRAGMA locking_mode=EXCLUSIVE;'")
        system(f"sqlite3 archive/{archive_name} 'BEGIN EXCLUSIVE;'")
        
        click.echo('Database archived')

