import typer

from .release import main

app = typer.Typer(help="CLI for managing GitHub releases.")


@app.command()
def release(
    tag_name: str = typer.Option(..., prompt=True, help="The tag name of the release."),
    repo: str = typer.Option(
        "tibia-oce/otclient", help="The GitHub repository in the format 'owner/repo'."
    ),
    repo_path: str = typer.Option(
        ".", help="The local path where the release assets will be extracted."
    ),
) -> None:
    main(repo, tag_name, repo_path)


if __name__ == "__main__":
    app()
