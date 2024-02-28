from flask import Flask
from flask.cli import with_appcontext
from typing import cast
from os import getenv, system, path, makedirs
from shutil import copyfile
from sqlalchemy_utils import database_exists
import click

from model.database         import db, DB_VER
from model.version_control  import verControl


def register_commands(app: Flask):
    @app.cli.command(help='Setup python')
    @with_appcontext
    def setup():
        system('pip install -r requirements.txt')
        if input('Do you want to change .env? [y/N] ').lower() == 'y':
            copyfile('.env', '.env.bak')
            copyfile('example.env', '.env')
        if input('Do you want to initialize the database? [y/N] ').lower() == 'y':
            db_init()
        print('Python setup complete')


    @app.cli.command(help='Initialize the database')
    @with_appcontext
    def db_init():
        if not database_exists(db.engine.url):
            db.create_all()

        verControl.update('db_ver', str(DB_VER))
        verControl.save()
        click.echo('Database initialized')


    @app.cli.command(help='Drop the database')
    @with_appcontext
    def db_drop():
        db.drop_all()

        verControl.update('db_ver', None)
        verControl.update('role_ver', None)
        verControl.save()
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

