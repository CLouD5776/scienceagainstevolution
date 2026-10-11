"""Copy only approved public files to a fresh publishing directory."""
import argparse,hashlib,json,shutil
from pathlib import Path
from public_scope import load_public_files

def build(site_dir,manifest,output,max_file_bytes=None):
    root=Path(site_dir).resolve();dest=Path(output).resolve()
    if root==dest or root.is_relative_to(dest):raise ValueError('Output must not contain or replace source')
    if dest.exists() and any(dest.iterdir()):raise ValueError('Output must be new or empty; existing release preserved')
    inputs=load_public_files(root,manifest)
    if max_file_bytes is not None:
        oversized=[p.relative_to(root).as_posix() for p in inputs if p.stat().st_size>max_file_bytes]
        if oversized:raise ValueError(f'Public assets exceed host file limit: {oversized}')
    dest.mkdir(parents=True,exist_ok=True);records=[]
    for p in inputs:
        name=p.relative_to(root).as_posix();target=dest/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,target)
        with p.open('rb') as f:before=hashlib.file_digest(f,'sha256').hexdigest()
        with target.open('rb') as f:after=hashlib.file_digest(f,'sha256').hexdigest()
        if before!=after:raise RuntimeError(f'Copy mismatch {name}')
        records.append({'path':name,'bytes':target.stat().st_size,'sha256':after})
    # Pages otherwise treats a site without 404.html as an SPA and returns
    # homepage HTML for missing assets, hiding broken video links.
    if not (dest/'404.html').exists():
        missing=b'<!doctype html><html lang="en"><meta charset="utf-8"><title>Page not found - SAGE</title><h1>Page not found</h1><p>This page or file is unavailable.</p><p><a href="/">Return to SAGE</a></p></html>\n'
        (dest/'404.html').write_bytes(missing)
        records.append({'path':'404.html','bytes':len(missing),'sha256':hashlib.sha256(missing).hexdigest(),'generated':True})
    receipt=dest.with_name(dest.name+'-manifest.json')
    receipt.write_text(json.dumps({'public_files':records,'scope_manifest':str(Path(manifest).resolve())},indent=2))
    return records

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--site-dir',required=True);ap.add_argument('--public-manifest',required=True);ap.add_argument('--output',required=True);ap.add_argument('--max-file-bytes',type=int)
    args=ap.parse_args();rows=build(args.site_dir,args.public_manifest,args.output,args.max_file_bytes)
    print(f'Clean publishing directory: {args.output}; {len(rows)} verified public files')
