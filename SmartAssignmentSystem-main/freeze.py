import shutil
from pathlib import Path

from app import create_app


# Simple static exporter (does NOT reproduce login/backend behavior).
# It uses Flask's test client to fetch a small set of public pages
# and copies the `static/` folder into `build/static` so assets are available.

APP = create_app()
BUILD_DIR = Path("build")


def clean_build():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)


def copy_static():
    src = Path("static")
    dst = BUILD_DIR / "static"
    if src.exists():
        shutil.copytree(src, dst)


def export_paths(paths):
    with APP.test_client() as client:
        for p in paths:
            resp = client.get(p, follow_redirects=True)
            if resp.status_code == 200:
                html = resp.get_data(as_text=True)
                if p == "/":
                    out = BUILD_DIR / "index.html"
                else:
                    name = p.strip("/").replace("/", "_") or "index"
                    out = BUILD_DIR / f"{name}.html"
                out.write_text(html, encoding="utf-8")
                print(f"Wrote {out}")
            else:
                print(f"Skipping {p} (status {resp.status_code})")


def main():
    # Pages to export. Add more public routes if you have them.
    paths = ["/", "/login", "/register"]
    clean_build()
    copy_static()
    export_paths(paths)
    print(f"Static export complete. See {BUILD_DIR.resolve()}")


if __name__ == "__main__":
    main()
