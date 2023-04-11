from flask import Flask
import click
from flask.cli import with_appcontext
from database import db
from os import getenv
from shutil import copyfile
from os import system

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
        db.create_all()
        click.echo('Database initialized')
    
    @app.cli.command(help='Drop the database')
    @with_appcontext
    def db_drop():
        db.drop_all()
        click.echo('Database dropped')

    @app.cli.command(help='Archive the database')
    @with_appcontext
    @click.argument('archive_name')
    def db_archive(archive_name):
        if not archive_name.endswith('.sqlite3'):
            archive_name += '.sqlite3'
        db_url = "instance/" + getenv('DATABASE_URL')[10:]
        copyfile(db_url, f'archive/{archive_name}')
        system(f"sqlite3 archive/{archive_name} 'VACUUM;'")
        system(f"sqlite3 archive/{archive_name} 'PRAGMA locking_mode=EXCLUSIVE;'")
        system(f"sqlite3 archive/{archive_name} 'BEGIN EXCLUSIVE;'")
        
        click.echo('Database archived')

