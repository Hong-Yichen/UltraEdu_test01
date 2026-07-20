def register_cli(app):
    @app.cli.command("seed")
    def seed_command():
        """Drop and recreate all tables, then populate with demo data."""
        from seed import run_seed

        run_seed()
        print("Database seeded.")
