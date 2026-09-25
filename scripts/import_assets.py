from pathlib import Path
import re, shutil, zipfile, sys

GAMES={
 "Wuthering Waves picture":"wuthering-waves",
 "Punishing Gray Raven picture":"pgr",
 "Genshin Impact picture":"genshin",
 "Honkai Star Rail picture":"hsr",
 "Zenless Zone Zero picture":"zzz",
 "Arknights Endfield picture":"endfield",
 "Neverness to Everness picture":"nte",
}
root=Path(__file__).resolve().parents[1]
zip_path=Path(sys.argv[1] if len(sys.argv)>1 else "pictures.zip")
out=root/"web/assets/games"; out.mkdir(parents=True,exist_ok=True)
def slug(s):
    s=s.replace("×","x")
    return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")
with zipfile.ZipFile(zip_path) as z:
    for name in z.namelist():
        if name.endswith("/") or "/" not in name: continue
        folder,file=name.split("/",1); game=GAMES.get(folder)
        if not game: continue
        target_dir=out/game; target_dir.mkdir(parents=True,exist_ok=True)
        target=target_dir/(slug(Path(file).stem)+Path(file).suffix.lower())
        with z.open(name) as src, open(target,"wb") as dst: shutil.copyfileobj(src,dst)
print("Assets imported:", out)
