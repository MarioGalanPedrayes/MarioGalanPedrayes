"""Motor de juego de BESTIARIO: Ecos de lo Salvaje."""
import json, random

# 70 especies originales: seis biomas, patrón único de cuatro tonos.
_RAW = [
("Musgario","Bosque","cauto","✿"),("Lúgora","Bosque","curiosa","❋"),("Trenzal","Bosque","sereno","♧"),("Brezaluz","Bosque","inquieta","✧"),("Nubrote","Bosque","cauto","❀"),("Hojalba","Bosque","serena","❈"),("Tiznillo","Bosque","juguetón","✺"),("Velaria","Bosque","reservada","❃"),("Raizonte","Bosque","sereno","♣"),("Péndula","Bosque","curiosa","❁"),("Brumel","Bosque","cauto","☼"),("Cendal","Bosque","inquieto","✼"),
("Rocíofer","Costa","sereno","◈"),("Salmuera","Costa","curiosa","❖"),("Nacarín","Costa","cauto","◇"),("Espumel","Costa","juguetón","✦"),("Mareta","Costa","inquieta","⌁"),("Alguario","Costa","reservado","♢"),("Coralba","Costa","serena","❂"),("Burbujón","Costa","juguetón","○"),("Litorna","Costa","curiosa","✧"),("Ventalga","Costa","inquieta","⌘"),("Crisalia","Costa","cauta","❉"),("Ondario","Costa","sereno","◉"),
("Pedernal","Cumbres","orgulloso","▲"),("Ventisca","Cumbres","inquieta","△"),("Cuarzón","Cumbres","cauto","◇"),("Altífero","Cumbres","sereno","✥"),("Nevaira","Cumbres","reservada","❄"),("Riscón","Cumbres","terco","◬"),("Auralta","Cumbres","curiosa","✦"),("Granizo","Cumbres","juguetón","❅"),("Picaluz","Cumbres","inquieto","✧"),("Umbrafín","Cumbres","cauto","◐"),("Crestal","Cumbres","orgulloso","♢"),("Nivaluz","Cumbres","serena","✣"),
("Cenizal","Volcán","temperamental","♨"),("Brasaul","Volcán","inquieto","✹"),("Obsidia","Volcán","reservada","⬖"),("Fumarol","Volcán","curioso","♨"),("Escoriel","Volcán","terco","✴"),("Lumbreta","Volcán","juguetona","✺"),("Azufral","Volcán","cauto","◉"),("Magmario","Volcán","orgulloso","⬟"),("Pavesa","Volcán","serena","✷"),("Calderín","Volcán","inquieto","♧"),("Ígnea","Volcán","curiosa","❖"),("Tizoria","Volcán","reservada","✹"),
("Dunario","Desierto","cauto","☼"),("Arenis","Desierto","curiosa","◇"),("Siroco","Desierto","inquieto","〰"),("Oasín","Desierto","sereno","❋"),("Miraluz","Desierto","reservada","✧"),("Dunavelo","Desierto","juguetón","◌"),("Cactilio","Desierto","terco","♧"),("Solmara","Desierto","serena","☀"),("Yesquín","Desierto","inquieto","✦"),("Salitral","Desierto","orgulloso","⬡"),("Calíope","Desierto","curiosa","❈"),("Vidrial","Desierto","cauto","◇"),
("Noctil","Umbral","reservado","☾"),("Eclipsa","Umbral","curiosa","◒"),("Susurial","Umbral","cauto","♬"),("Velumbría","Umbral","serena","✧"),("Ombrel","Umbral","juguetón","◍"),("Lunario","Umbral","inquieto","☽"),("Silencia","Umbral","reservada","❂"),("Eteria","Umbral","serena","✴"),("Parpadeo","Umbral","curioso","✺"),("Sombraciel","Umbral","orgulloso","◐")
]
TONES = ["Bruma", "Raíz", "Chispa"]
def _pattern(i):
    """Patrón único de 4 tonos: 70 de las 81 combinaciones posibles (3^4)."""
    n=(i*7+5)%81  # 7 y 81 son coprimos: no se repite ningún valor
    return [n//27%3, n//9%3, n//3%3, n%3]
CREATURES = []
for i, (name, biome, mood, glyph) in enumerate(_RAW):
    CREATURES.append({"id":i,"name":name,"biome":biome,"mood":mood,"glyph":glyph,
                      "pattern":_pattern(i)})
_state = {}

def _dump():
    c = _state.get("creature")
    return json.dumps({
      "collection":sorted(_state.get("collection",[])),"encounters":_state.get("encounters",0),
      "seals":_state.get("seals",0),
      "creature":({k:c[k] for k in ("id","name","biome","mood","glyph")} if c else None),
      "description":_state.get("description",""),"heard":_state.get("heard",False),
      "echo":([TONES[x] for x in c["pattern"]] if c and _state.get("heard") else []),
      "turn":_state.get("turn",0),"agitation":_state.get("agitation",0),
      "answers":_state.get("answers",[]),"feedback":_state.get("feedback",""),
      "result":_state.get("result"),"finished":_state.get("finished",False)
    },ensure_ascii=False)

def start():
    global _state
    _state={"collection":[],"encounters":0,"seals":0,"creature":None,"description":"",
      "heard":False,"turn":0,"agitation":0,"answers":[],"feedback":"El silencio también es una respuesta.",
      "result":None,"finished":False}
    return _dump()

def restore(raw):
    global _state
    try:
      d=json.loads(raw or "{}")
      ids=sorted(set(int(x) for x in d.get("collection",[]) if 0<=int(x)<70))
      _state={"collection":ids,"encounters":max(0,int(d.get("encounters",0))),
        "seals":max(0,int(d.get("seals",0))),"creature":None,"description":"",
        "heard":False,"turn":0,"agitation":0,"answers":[],
        "feedback":"Expedición recuperada. Busca un nuevo rastro.","result":None,"finished":False}
    except Exception:
      return start()
    return _dump()

def explore():
    if _state.get("creature") and not _state.get("finished"): return _dump()
    unseen=[c for c in CREATURES if c["id"] not in _state["collection"]]
    c=random.choice(unseen or CREATURES)
    _state.update({"creature":c,"encounters":_state["encounters"]+1,
      "description":"Entre el paisaje aparece una presencia. Su pulso cambia con cada respiración.",
      "heard":False,"turn":0,"agitation":0,"answers":[],"feedback":"Hay algo al otro lado del silencio.",
      "result":None,"finished":False})
    return _dump()

def listen():
    if _state.get("creature") and not _state.get("finished"):
      _state["heard"]=True
      _state["feedback"]="Memoriza el patrón y devuelve sus cuatro tonos en el mismo orden."
    return _dump()

def answer(tone):
    if not _state.get("creature") or not _state.get("heard") or _state.get("finished"): return _dump()
    tone=int(tone)
    if tone not in (0,1,2): return _dump()
    expected=_state["creature"]["pattern"][_state["turn"]]
    _state["answers"].append(tone)
    if tone==expected:
      _state["agitation"]=max(0,_state["agitation"]-8)
      _state["feedback"]="El tono encaja. La criatura se aproxima un poco."
    else:
      _state["agitation"]=min(100,_state["agitation"]+34)
      _state["feedback"]="El eco se quiebra. La presencia se inquieta."
    _state["turn"]+=1
    if _state["agitation"]>=100:
      _state["finished"]=True; _state["result"]="escaped"
      _state["feedback"]="La criatura se ha retirado. El encuentro termina sin captura."
    elif _state["turn"]>=4:
      _state["finished"]=True
      if _state["agitation"]<=55:
        cid=_state["creature"]["id"]
        if cid not in _state["collection"]:
          _state["collection"].append(cid); _state["seals"]+=1
        _state["result"]="captured"
        _state["feedback"]="Cuatro pulsos en armonía. La criatura acepta quedar registrada."
      else:
        _state["result"]="escaped"
        _state["feedback"]="La señal fue demasiado áspera. La criatura se marcha."
    return _dump()

def next_encounter():
    if _state.get("finished"):
      _state.update({"creature":None,"description":"","heard":False,"turn":0,"agitation":0,
        "answers":[],"feedback":"El sendero vuelve a abrirse.","result":None,"finished":False})
    return _dump()

def state(): return _dump()
