# release_manager\__main__.py
import typer

from .release import main

app = typer.Typer(help="CLI for managing client GitHub releases.")


@app.command()
def release(
    tag_name: str = typer.Option(..., prompt=True),
    repo: str = typer.Option("tibia-oce/otclient"),
    repo_path: str = typer.Option("."),
) -> None:
    main(repo, tag_name, repo_path)


if __name__ == "__main__":
    app()
