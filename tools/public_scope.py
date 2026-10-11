"""Explicit public-input policy shared by search and preservation tooling."""
import json
from pathlib import Path, PurePosixPath

DENIED_PARTS = {'.git', 'reports', 'backups', 'research', 'raw', 'incoming_pdfs',
                'tmp', '__pycache__', 'tests', 'docs', '.github', 'tools', '_public'}
PUBLIC_EXTENSIONS = {'.htm', '.html', '.shtml', '.pdf', '.jpg', '.jpeg', '.png',
                     '.gif', '.svg', '.ico', '.css', '.js', '.json', '.xml',
                     '.mp3', '.mp4', '.wmv', '.wav', '.swf', '.txt', '.woff',
                     '.woff2', '.ttf', '.webp'}

def permitted(name):
    p = PurePosixPath(name)
    return (not p.is_absolute() and '\\' not in name and ':' not in name
            and not any(part.lower() in DENIED_PARTS or part in {'..', '.'}
                        for part in p.parts)
            and p.suffix.lower() in PUBLIC_EXTENSIONS
            and not any(part.startswith('.') for part in p.parts))

def load_public_files(site_dir, manifest):
    root = Path(site_dir).resolve()
    data = json.loads(Path(manifest).read_text(encoding='utf-8'))
    names = data['files']
    if len(names) != len(set(names)):
        raise ValueError('Duplicate public manifest paths')
    for name in names:
        path = (root / name).resolve()
        if not permitted(name) or not path.is_relative_to(root):
            raise ValueError(f'Unsafe/nonpublic manifest input: {name}')
        if not path.is_file():
            raise FileNotFoundError(f'Approved public input missing: {name}')
    return [root / name for name in names]
